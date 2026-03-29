"""
Deep Spectral Denoiser for PnP-CASSI
Based on FFDNet-style architecture adapted for spectral images.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class SpectralDenoiser(nn.Module):
    """
    FFDNet-style denoiser for spectral images.
    Takes K+1 adjacent spectral bands + noise level map as input.
    Processes at half resolution using pixel shuffle.
    """
    def __init__(self, K=6, n_layers=14, n_channels=64):
        super().__init__()
        self.K = K
        # Input: 4*(K+1) subimages + 1 noise map = 4K+5 channels
        in_channels = 4 * (K + 1) + 1
        
        layers = []
        # First layer
        layers.append(nn.Conv2d(in_channels, n_channels, 3, padding=1))
        layers.append(nn.ReLU(inplace=True))
        
        # Middle layers
        for _ in range(n_layers - 2):
            layers.append(nn.Conv2d(n_channels, n_channels, 3, padding=1))
            layers.append(nn.ReLU(inplace=True))
        
        # Last layer: output 4 channels for pixel shuffle
        layers.append(nn.Conv2d(n_channels, 4, 3, padding=1))
        
        self.net = nn.Sequential(*layers)
    
    def pixel_unshuffle(self, x):
        """Downsample by factor 2 using pixel unshuffle."""
        B, C, H, W = x.shape
        assert H % 2 == 0 and W % 2 == 0
        x = x.reshape(B, C, H//2, 2, W//2, 2)
        x = x.permute(0, 1, 3, 5, 2, 4).reshape(B, C*4, H//2, W//2)
        return x
    
    def pixel_shuffle(self, x):
        """Upsample by factor 2 using pixel shuffle."""
        return F.pixel_shuffle(x, 2)
    
    def forward(self, frames, sigma):
        """
        frames: (B, K+1, H, W) - K+1 adjacent spectral bands
        sigma: noise level (scalar or per-sample)
        Returns: (B, 1, H, W) - denoised center band
        """
        B, C, H, W = frames.shape
        
        # Pad to even dimensions if needed
        pad_h = H % 2
        pad_w = W % 2
        if pad_h or pad_w:
            frames = F.pad(frames, (0, pad_w, 0, pad_h), mode='reflect')
            _, _, H_pad, W_pad = frames.shape
        else:
            H_pad, W_pad = H, W
        
        # Pixel unshuffle each band
        unshuffled = self.pixel_unshuffle(frames)  # (B, 4*(K+1), H/2, W/2)
        
        # Create noise level map
        if isinstance(sigma, (int, float)):
            noise_map = torch.full((B, 1, H_pad//2, W_pad//2), sigma,
                                   device=frames.device, dtype=frames.dtype)
        else:
            noise_map = sigma.view(B, 1, 1, 1).expand(B, 1, H_pad//2, W_pad//2)
        
        # Concatenate
        inp = torch.cat([unshuffled, noise_map], dim=1)
        
        # Process
        out = self.net(inp)  # (B, 4, H/2, W/2)
        
        # Pixel shuffle back
        out = self.pixel_shuffle(out)  # (B, 1, H_pad, W_pad)
        
        # Remove padding
        if pad_h or pad_w:
            out = out[:, :, :H, :W]
        
        return out


class SimpleDenoiser(nn.Module):
    """
    Simpler denoiser that processes single bands with noise level conditioning.
    More efficient for CPU training.
    """
    def __init__(self, n_layers=8, n_channels=32):
        super().__init__()
        
        # Input: 1 image channel + 1 noise level map = 2
        layers = []
        layers.append(nn.Conv2d(2, n_channels, 3, padding=1))
        layers.append(nn.ReLU(inplace=True))
        
        for _ in range(n_layers - 2):
            layers.append(nn.Conv2d(n_channels, n_channels, 3, padding=1))
            layers.append(nn.ReLU(inplace=True))
        
        layers.append(nn.Conv2d(n_channels, 1, 3, padding=1))
        
        self.net = nn.Sequential(*layers)
    
    def forward(self, x, sigma):
        """
        x: (B, 1, H, W) - noisy image
        sigma: noise level
        Returns: (B, 1, H, W) - denoised image
        """
        B, C, H, W = x.shape
        if isinstance(sigma, (int, float)):
            noise_map = torch.full((B, 1, H, W), sigma, device=x.device, dtype=x.dtype)
        else:
            noise_map = sigma.view(B, 1, 1, 1).expand(B, 1, H, W)
        
        inp = torch.cat([x, noise_map], dim=1)
        residual = self.net(inp)
        return x - residual  # residual learning


class SpectralDenoiserWrapper:
    """Wrapper to use the trained denoiser in the PnP framework.
    Batches all bands together for efficiency."""
    
    def __init__(self, model, K=6, device='cpu'):
        self.model = model
        self.K = K
        self.device = device
        self.model.eval()
    
    def __call__(self, X, sigma):
        """
        X: (H, W, B) numpy array - spectral cube
        sigma: noise standard deviation
        Returns: (H, W, B) numpy array - denoised cube
        """
        H, W, B = X.shape
        half_K = self.K // 2
        
        # Prepare all band inputs at once
        all_frames = []
        for b in range(B):
            indices = []
            for i in range(b - half_K, b + half_K + 1):
                idx = i
                if idx < 0:
                    idx = -idx
                if idx >= B:
                    idx = 2 * B - 2 - idx
                indices.append(max(0, min(B-1, idx)))
            all_frames.append(X[:, :, indices])  # (H, W, K+1)
        
        # Stack into batch: (B, K+1, H, W)
        batch = np.stack(all_frames)  # (B, H, W, K+1)
        batch = np.transpose(batch, (0, 3, 1, 2))  # (B, K+1, H, W)
        batch_t = torch.from_numpy(batch).float().to(self.device)
        
        with torch.no_grad():
            denoised = self.model(batch_t, sigma)  # (B, 1, H, W)
        
        result = denoised[:, 0, :, :].cpu().numpy()  # (B, H, W)
        result = np.transpose(result, (1, 2, 0))  # (H, W, B)
        
        return result


class SimpleDenoiserWrapper:
    """Wrapper for the simple band-by-band denoiser."""
    
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.eval()
    
    def __call__(self, X, sigma):
        """
        X: (H, W, B) numpy array
        sigma: noise standard deviation
        Returns: (H, W, B) numpy array
        """
        H, W, B = X.shape
        result = np.zeros_like(X)
        
        with torch.no_grad():
            for b in range(B):
                band = torch.from_numpy(X[:, :, b:b+1]).float()
                band = band.permute(2, 0, 1).unsqueeze(0).to(self.device)
                denoised = self.model(band, sigma)
                result[:, :, b] = denoised[0, 0].cpu().numpy()
        
        return result


def generate_training_data(n_samples=500, patch_size=64, n_bands=7):
    """Generate synthetic spectral image patches for training."""
    patches = []
    
    for i in range(n_samples):
        np.random.seed(i * 137 + 42)
        patch = np.zeros((patch_size, patch_size, n_bands))
        
        # Base: smooth random field
        base = np.random.rand(patch_size // 4, patch_size // 4)
        from scipy.ndimage import zoom
        base = zoom(base, patch_size / (patch_size // 4), order=3)
        base = base[:patch_size, :patch_size]
        
        # Spectral profiles: smooth Gaussian-like curves
        wavelengths = np.linspace(0, 1, n_bands)
        n_materials = np.random.randint(2, 6)
        
        for m in range(n_materials):
            # Spatial region
            cx, cy = np.random.rand(2) * patch_size
            radius = np.random.rand() * patch_size * 0.4 + patch_size * 0.1
            xx, yy = np.meshgrid(np.arange(patch_size), np.arange(patch_size))
            spatial = np.exp(-((xx - cx)**2 + (yy - cy)**2) / (2 * radius**2))
            
            # Spectral profile
            center = np.random.rand()
            width = np.random.rand() * 0.3 + 0.1
            amplitude = np.random.rand() * 0.5 + 0.2
            spectral = amplitude * np.exp(-(wavelengths - center)**2 / (2 * width**2))
            
            for b in range(n_bands):
                patch[:, :, b] += spatial * spectral[b]
        
        # Add base
        for b in range(n_bands):
            patch[:, :, b] += base * 0.2
        
        # Smooth and normalize
        from scipy.ndimage import gaussian_filter
        patch = gaussian_filter(patch, sigma=[1.5, 1.5, 0.5])
        patch = np.clip(patch, 0, 1)
        if patch.max() > 0:
            patch = patch / max(patch.max(), 1.0)
        
        patches.append(patch)
    
    return patches


def train_simple_denoiser(model, patches, n_epochs=50, batch_size=16, 
                          lr=1e-3, max_sigma=25/255, device='cpu'):
    """Train the simple denoiser on spectral patches."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
    
    model.train()
    model.to(device)
    
    n_patches = len(patches)
    
    for epoch in range(n_epochs):
        total_loss = 0
        n_batches = 0
        
        # Shuffle
        indices = np.random.permutation(n_patches)
        
        for start in range(0, n_patches - batch_size + 1, batch_size):
            batch_idx = indices[start:start+batch_size]
            
            # Random band from each patch
            clean_bands = []
            for idx in batch_idx:
                patch = patches[idx]
                b = np.random.randint(patch.shape[2])
                clean_bands.append(patch[:, :, b])
            
            clean = np.stack(clean_bands)[:, np.newaxis, :, :]  # (B, 1, H, W)
            clean_t = torch.from_numpy(clean).float().to(device)
            
            # Random noise level
            sigma = np.random.uniform(0, max_sigma)
            noise = torch.randn_like(clean_t) * sigma
            noisy_t = clean_t + noise
            
            # Forward
            denoised = model(noisy_t, sigma)
            loss = F.mse_loss(denoised, clean_t)
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
        
        scheduler.step()
        avg_loss = total_loss / max(n_batches, 1)
        
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{n_epochs}: loss={avg_loss:.6f}")
    
    return model


def train_spectral_denoiser(model, patches, n_epochs=50, batch_size=8,
                            lr=1e-3, max_sigma=25/255, K=6, device='cpu'):
    """Train the spectral denoiser on spectral patches."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
    
    model.train()
    model.to(device)
    
    n_patches = len(patches)
    half_K = K // 2
    
    for epoch in range(n_epochs):
        total_loss = 0
        n_batches = 0
        
        indices = np.random.permutation(n_patches)
        
        for start in range(0, n_patches - batch_size + 1, batch_size):
            batch_idx = indices[start:start+batch_size]
            
            clean_frames_list = []
            clean_center_list = []
            
            for idx in batch_idx:
                patch = patches[idx]  # (H, W, n_bands)
                n_bands = patch.shape[2]
                # Random center band
                b = np.random.randint(n_bands)
                
                # Get K+1 adjacent bands with mirror padding
                band_indices = []
                for i in range(b - half_K, b + half_K + 1):
                    bi = i
                    if bi < 0:
                        bi = -bi
                    if bi >= n_bands:
                        bi = 2 * n_bands - 2 - bi
                    band_indices.append(max(0, min(n_bands - 1, bi)))
                
                frames = patch[:, :, band_indices]  # (H, W, K+1)
                clean_frames_list.append(frames)
                clean_center_list.append(patch[:, :, b])
            
            clean_frames = np.stack(clean_frames_list)  # (B, H, W, K+1)
            clean_frames = np.transpose(clean_frames, (0, 3, 1, 2))  # (B, K+1, H, W)
            clean_center = np.stack(clean_center_list)[:, np.newaxis, :, :]  # (B, 1, H, W)
            
            clean_frames_t = torch.from_numpy(clean_frames).float().to(device)
            clean_center_t = torch.from_numpy(clean_center).float().to(device)
            
            # Random noise level
            sigma = np.random.uniform(0, max_sigma)
            noise = torch.randn_like(clean_frames_t) * sigma
            noisy_frames_t = clean_frames_t + noise
            
            # Forward
            denoised = model(noisy_frames_t, sigma)
            loss = F.mse_loss(denoised, clean_center_t)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
        
        scheduler.step()
        avg_loss = total_loss / max(n_batches, 1)
        
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{n_epochs}: loss={avg_loss:.6f}")
    
    return model


if __name__ == "__main__":
    print("Testing denoiser architectures...")
    
    # Test SimpleDenoiser
    model = SimpleDenoiser(n_layers=6, n_channels=16)
    x = torch.randn(2, 1, 32, 32)
    out = model(x, 0.1)
    print(f"SimpleDenoiser: input {x.shape} -> output {out.shape}")
    
    # Test SpectralDenoiser
    K = 6
    model2 = SpectralDenoiser(K=K, n_layers=8, n_channels=32)
    x2 = torch.randn(2, K+1, 32, 32)
    out2 = model2(x2, 0.1)
    print(f"SpectralDenoiser: input {x2.shape} -> output {out2.shape}")
    
    print("Architecture tests passed!")
