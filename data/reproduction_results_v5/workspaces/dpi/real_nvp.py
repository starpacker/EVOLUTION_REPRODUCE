"""
Real-NVP flow-based generative model implementation for DPI.
Supports both 2D toy examples and image reconstruction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class AffineCouplingLayer(nn.Module):
    """Affine coupling layer for Real-NVP."""
    
    def __init__(self, dim, hidden_dim=256, n_hidden=2):
        super().__init__()
        self.dim = dim
        self.split = dim // 2
        
        # Build scale and translation networks
        layers_s = []
        layers_t = []
        in_dim = self.split
        for i in range(n_hidden):
            layers_s.append(nn.Linear(in_dim if i == 0 else hidden_dim, hidden_dim))
            layers_s.append(nn.LeakyReLU(0.01))
            layers_t.append(nn.Linear(in_dim if i == 0 else hidden_dim, hidden_dim))
            layers_t.append(nn.LeakyReLU(0.01))
        layers_s.append(nn.Linear(hidden_dim, dim - self.split))
        layers_t.append(nn.Linear(hidden_dim, dim - self.split))
        
        self.net_s = nn.Sequential(*layers_s)
        self.net_t = nn.Sequential(*layers_t)
    
    def forward(self, z):
        z1, z2 = z[:, :self.split], z[:, self.split:]
        s = self.net_s(z1)
        t = self.net_t(z1)
        # Clamp s for numerical stability
        s = torch.clamp(s, -5, 5)
        x2 = z2 * torch.exp(s) + t
        x = torch.cat([z1, x2], dim=1)
        log_det = s.sum(dim=1)
        return x, log_det
    
    def inverse(self, x):
        x1, x2 = x[:, :self.split], x[:, self.split:]
        s = self.net_s(x1)
        t = self.net_t(x1)
        s = torch.clamp(s, -5, 5)
        z2 = (x2 - t) * torch.exp(-s)
        z = torch.cat([x1, z2], dim=1)
        log_det = -s.sum(dim=1)
        return z, log_det


class RealNVP(nn.Module):
    """Real-NVP normalizing flow model."""
    
    def __init__(self, dim, n_layers=32, hidden_dim=256, n_hidden=2, 
                 use_softplus=False):
        super().__init__()
        self.dim = dim
        self.n_layers = n_layers
        self.use_softplus = use_softplus
        
        self.layers = nn.ModuleList()
        # Create random permutations for each layer
        self.permutations = []
        self.inv_permutations = []
        
        for i in range(n_layers):
            self.layers.append(AffineCouplingLayer(dim, hidden_dim, n_hidden))
            perm = torch.randperm(dim)
            inv_perm = torch.zeros_like(perm)
            inv_perm[perm] = torch.arange(dim)
            self.permutations.append(perm)
            self.inv_permutations.append(inv_perm)
    
    def forward(self, z):
        """Transform from latent z to data x."""
        log_det_total = torch.zeros(z.shape[0], device=z.device)
        x = z
        for i, layer in enumerate(self.layers):
            x, log_det = layer(x)
            log_det_total += log_det
            # Apply permutation
            x = x[:, self.permutations[i].to(x.device)]
        
        if self.use_softplus:
            # Softplus for non-negativity: x_out = log(1 + exp(x))
            # log_det of softplus: sum of log(sigmoid(x))
            log_det_softplus = torch.sum(F.logsigmoid(x), dim=1)
            x = F.softplus(x)
            log_det_total += log_det_softplus
        
        return x, log_det_total
    
    def log_prob(self, x, z, log_det):
        """Compute log probability of x given the transformation."""
        # log q(x) = log pi(z) - log|det dG/dz|
        log_pi_z = -0.5 * (z ** 2).sum(dim=1) - 0.5 * self.dim * np.log(2 * np.pi)
        log_qx = log_pi_z - log_det
        return log_qx
    
    def sample(self, n_samples):
        """Sample from the model."""
        z = torch.randn(n_samples, self.dim)
        x, log_det = self.forward(z)
        return x, z, log_det


class UNetCouplingLayer(nn.Module):
    """Affine coupling layer with UNet-style skip connections for image DPI."""
    
    def __init__(self, dim, hidden_dims=[512, 256, 128, 64, 32]):
        super().__init__()
        self.dim = dim
        self.split = dim // 2
        
        # Encoder
        enc_layers = []
        in_d = self.split
        for hd in hidden_dims:
            enc_layers.append(nn.Linear(in_d, hd))
            enc_layers.append(nn.LeakyReLU(0.01))
            enc_layers.append(nn.BatchNorm1d(hd))
            in_d = hd
        self.encoder = nn.ModuleList()
        idx = 0
        for hd in hidden_dims:
            block = nn.Sequential(
                nn.Linear(in_d if idx == 0 else hidden_dims[idx-1], hd),
                nn.LeakyReLU(0.01),
                nn.BatchNorm1d(hd)
            )
            if idx == 0:
                block = nn.Sequential(
                    nn.Linear(self.split, hd),
                    nn.LeakyReLU(0.01),
                    nn.BatchNorm1d(hd)
                )
            self.encoder.append(block)
            idx += 1
        
        # Decoder with skip connections
        self.decoder = nn.ModuleList()
        for i in range(len(hidden_dims) - 1, 0, -1):
            in_features = hidden_dims[i] + hidden_dims[i-1]  # skip connection
            out_features = hidden_dims[i-1]
            block = nn.Sequential(
                nn.Linear(in_features, out_features),
                nn.LeakyReLU(0.01),
                nn.BatchNorm1d(out_features)
            )
            self.decoder.append(block)
        
        # Output layers for scale and translation
        self.out_s = nn.Linear(hidden_dims[0], dim - self.split)
        self.out_t = nn.Linear(hidden_dims[0], dim - self.split)
    
    def _compute_st(self, z1):
        # Encoder
        enc_outputs = []
        h = z1
        for block in self.encoder:
            h = block(h)
            enc_outputs.append(h)
        
        # Decoder with skip connections
        h = enc_outputs[-1]
        for i, block in enumerate(self.decoder):
            skip_idx = len(enc_outputs) - 2 - i
            h = torch.cat([h, enc_outputs[skip_idx]], dim=1)
            h = block(h)
        
        s = self.out_s(h)
        t = self.out_t(h)
        s = torch.clamp(s, -5, 5)
        return s, t
    
    def forward(self, z):
        z1, z2 = z[:, :self.split], z[:, self.split:]
        s, t = self._compute_st(z1)
        x2 = z2 * torch.exp(s) + t
        x = torch.cat([z1, x2], dim=1)
        log_det = s.sum(dim=1)
        return x, log_det


class ImageRealNVP(nn.Module):
    """Real-NVP for image reconstruction with UNet-style coupling layers."""
    
    def __init__(self, dim, n_layers=48, hidden_dims=[512, 256, 128, 64, 32],
                 use_softplus=False):
        super().__init__()
        self.dim = dim
        self.n_layers = n_layers
        self.use_softplus = use_softplus
        
        self.layers = nn.ModuleList()
        self.permutations = []
        
        for i in range(n_layers):
            self.layers.append(UNetCouplingLayer(dim, hidden_dims))
            perm = torch.randperm(dim)
            self.permutations.append(perm)
    
    def forward(self, z):
        log_det_total = torch.zeros(z.shape[0], device=z.device)
        x = z
        for i, layer in enumerate(self.layers):
            x, log_det = layer(x)
            log_det_total += log_det
            x = x[:, self.permutations[i].to(x.device)]
        
        if self.use_softplus:
            log_det_softplus = torch.sum(F.logsigmoid(x), dim=1)
            x = F.softplus(x)
            log_det_total += log_det_softplus
        
        return x, log_det_total
    
    def sample(self, n_samples):
        z = torch.randn(n_samples, self.dim)
        x, log_det = self.forward(z)
        return x, z, log_det


if __name__ == "__main__":
    # Quick test
    model = RealNVP(dim=2, n_layers=4, hidden_dim=64, n_hidden=2)
    z = torch.randn(10, 2)
    x, log_det = model(z)
    print(f"Input shape: {z.shape}, Output shape: {x.shape}, Log det shape: {log_det.shape}")
    print(f"Log det values: {log_det[:3]}")
    print("Real-NVP basic test passed!")
