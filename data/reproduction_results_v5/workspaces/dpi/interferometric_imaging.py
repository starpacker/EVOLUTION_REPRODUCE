"""
DPI Convex Interferometric Imaging with Visibilities.
Reproduces Figure 4 from the paper.

Key setup:
- 32x32 pixel image, 160 uas FOV
- Synthetic black hole image
- Gaussian image prior with known mean and covariance
- Linear forward model (complex visibilities)
- Analytical posterior is Gaussian (can verify DPI against it)
- Test beta=1 minimizes KL divergence
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import time
import sys

torch.manual_seed(42)
np.random.seed(42)

# ---- Synthetic Black Hole Image ----
def create_crescent_image(M=32, fov_uas=160, total_flux=2.0):
    """Create a synthetic crescent (black hole shadow) image."""
    pix = fov_uas / M  # uas per pixel
    x = np.linspace(-fov_uas/2, fov_uas/2, M)
    xx, yy = np.meshgrid(x, x)
    r = np.sqrt(xx**2 + yy**2)

    # Ring parameters
    r_ring = 22.0  # ring radius in uas
    width = 8.0    # ring width
    ring = np.exp(-0.5 * ((r - r_ring) / width)**2)

    # Asymmetric brightness (brighter on bottom)
    asym = 1.0 + 0.5 * np.sin(np.arctan2(yy, xx) - np.pi/3)
    img = ring * asym

    # Central depression
    depression = 1.0 - 0.8 * np.exp(-0.5 * (r / 10.0)**2)
    img = img * depression

    # Normalize to total flux
    img = img / img.sum() * total_flux
    return img.astype(np.float32)


# ---- EHT-like UV Coverage ----
def create_eht_uv_coverage(n_baselines=50, max_uv=4e9):
    """Create synthetic EHT-like UV coverage."""
    np.random.seed(42)
    # Simulate sparse UV coverage
    # EHT has ~9 telescopes, giving ~36 baselines
    # Over a night, Earth rotation gives arcs in UV plane
    n_times = 20
    n_tel = 8
    n_bl = n_tel * (n_tel - 1) // 2

    us, vs = [], []
    for t in range(n_times):
        hour_angle = -6 + 12 * t / n_times  # hours
        ha_rad = hour_angle * np.pi / 12
        for i in range(n_tel):
            for j in range(i+1, n_tel):
                # Random baseline with rotation
                bl_len = np.random.uniform(0.3, 1.0) * max_uv
                bl_angle = np.random.uniform(0, 2*np.pi) + ha_rad * 0.3
                u = bl_len * np.cos(bl_angle)
                v = bl_len * np.sin(bl_angle)
                us.append(u)
                vs.append(v)

    us, vs = np.array(us), np.array(vs)
    # Add conjugates
    us = np.concatenate([us, -us])
    vs = np.concatenate([vs, -vs])
    return us.astype(np.float32), vs.astype(np.float32)


def build_fourier_matrix(us, vs, M=32, fov_uas=160):
    """Build the discrete Fourier transform matrix for given UV points."""
    fov_rad = fov_uas * np.pi / (180 * 3600 * 1e6)  # convert uas to radians
    pix_rad = fov_rad / M

    # Pixel positions
    x = np.arange(M) - M/2 + 0.5
    y = np.arange(M) - M/2 + 0.5
    xx, yy = np.meshgrid(x, y)
    xx_rad = xx.flatten() * pix_rad
    yy_rad = yy.flatten() * pix_rad

    # DFT matrix: V(u,v) = sum_pixels I(x,y) * exp(-2pi*i*(u*x + v*y))
    K = len(us)
    N = M * M
    F_complex = np.zeros((K, N), dtype=np.complex64)
    for k in range(K):
        phase = -2 * np.pi * (us[k] * xx_rad + vs[k] * yy_rad)
        F_complex[k] = np.exp(1j * phase)

    # Split into real and imaginary parts
    F_real = np.vstack([F_complex.real, F_complex.imag])
    return torch.tensor(F_real, dtype=torch.float32), F_complex


def create_measurement_covariance(us, vs, base_noise=0.01):
    """Create measurement noise covariance based on baseline properties."""
    K = len(us)
    # Noise proportional to baseline length (longer baselines = more noise)
    bl_len = np.sqrt(us**2 + vs**2)
    bl_len_norm = bl_len / bl_len.max()
    noise_std = base_noise * (1 + bl_len_norm)
    # Stack for real and imaginary parts
    sigma = np.concatenate([noise_std, noise_std])
    Sigma = np.diag(sigma**2).astype(np.float32)
    return torch.tensor(Sigma, dtype=torch.float32), torch.tensor(sigma, dtype=torch.float32)


# ---- Affine Coupling for Image DPI ----
class AffineCoupling(nn.Module):
    def __init__(self, dim, hd=128):
        super().__init__()
        self.split = dim // 2
        out = dim - self.split
        self.s = nn.Sequential(nn.Linear(self.split, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, out))
        self.t = nn.Sequential(nn.Linear(self.split, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, out))

    def forward(self, z):
        z1, z2 = z[:, :self.split], z[:, self.split:]
        s = torch.tanh(self.s(z1)) * 3.0
        t = self.t(z1)
        return torch.cat([z1, z2 * torch.exp(s) + t], 1), s.sum(1)


class ImageRealNVP(nn.Module):
    def __init__(self, dim, n_layers=16, hd=128, use_softplus=False):
        super().__init__()
        self.dim = dim
        self.use_softplus = use_softplus
        self.layers = nn.ModuleList([AffineCoupling(dim, hd) for _ in range(n_layers)])
        self.perms = [torch.randperm(dim) for _ in range(n_layers)]

    def forward(self, z):
        ld = torch.zeros(z.shape[0])
        for i, layer in enumerate(self.layers):
            z, d = layer(z)
            ld += d
            z = z[:, self.perms[i]]
        if self.use_softplus:
            ld += F.logsigmoid(z).sum(1)
            z = F.softplus(z)
        return z, ld


def analytical_posterior(F_mat, y, Sigma, mu, Lambda):
    """Compute analytical Gaussian posterior: p(x|y) = N(m, C)."""
    # m = mu + Lambda @ F^T @ (Sigma + F @ Lambda @ F^T)^{-1} @ (y - F @ mu)
    # C = Lambda - Lambda @ F^T @ (Sigma + F @ Lambda @ F^T)^{-1} @ F @ Lambda
    FLambda = F_mat @ Lambda
    S = Sigma + FLambda @ F_mat.T
    S_inv = torch.linalg.inv(S)
    K = Lambda @ F_mat.T @ S_inv

    m = mu + K @ (y - F_mat @ mu)
    C = Lambda - K @ F_mat @ Lambda
    return m, C


def compute_kl_gaussian(mean_q, cov_q, mean_p, cov_p):
    """Compute KL(q||p) between two Gaussians."""
    d = mean_q.shape[0]
    cov_p_inv = torch.linalg.inv(cov_p)
    diff = mean_p - mean_q
    kl = 0.5 * (torch.trace(cov_p_inv @ cov_q) +
                diff @ cov_p_inv @ diff - d +
                torch.logdet(cov_p) - torch.logdet(cov_q))
    return kl.item()


def run_convex_imaging():
    M = 32
    dim = M * M  # 1024

    # Create synthetic image
    img = create_crescent_image(M)
    x_true = torch.tensor(img.flatten(), dtype=torch.float32)
    print(f"Image: {M}x{M}, total flux: {x_true.sum():.2f}")

    # Create UV coverage and forward model
    us, vs = create_eht_uv_coverage()
    F_mat, _ = build_fourier_matrix(us, vs, M)
    print(f"UV points: {len(us)}, F matrix: {F_mat.shape}")

    # Measurement noise
    Sigma, sigma = create_measurement_covariance(us, vs, base_noise=0.02)

    # Generate noisy measurements
    y_clean = F_mat @ x_true
    noise = torch.randn_like(y_clean) * sigma
    y = y_clean + noise
    print(f"Measurements: {y.shape}, SNR: {(y_clean.norm() / noise.norm()).item():.1f}")

    # Gaussian image prior
    mu = torch.ones(dim) * x_true.mean()
    prior_std = 0.1
    Lambda = torch.eye(dim) * prior_std**2

    # Analytical posterior
    print("Computing analytical posterior...")
    m_post, C_post = analytical_posterior(F_mat, y, Sigma, mu, Lambda)
    post_std = torch.sqrt(torch.diag(C_post))
    print(f"Posterior mean range: [{m_post.min():.4f}, {m_post.max():.4f}]")
    print(f"Posterior std range: [{post_std.min():.4f}, {post_std.max():.4f}]")

    # ---- Train DPI ----
    results = {"analytical": {
        "mean_min": m_post.min().item(),
        "mean_max": m_post.max().item(),
        "std_min": post_std.min().item(),
        "std_max": post_std.max().item(),
    }}

    # Precompute Sigma_inv for data fitting loss
    Sigma_inv = torch.diag(1.0 / torch.diag(Sigma))
    lambda_reg = 1.0  # prior weight

    # Architecture A: no softplus
    for arch_name, use_sp in [("arch_A", False), ("arch_B", True)]:
        print(f"\nTraining DPI {arch_name}...")
        sys.stdout.flush()

        beta_kls = {}
        for beta in [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]:
            torch.manual_seed(42)
            model = ImageRealNVP(dim, n_layers=8, hd=128, use_softplus=use_sp)
            opt = torch.optim.Adam(model.parameters(), lr=5e-4)
            sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 2000)

            t0 = time.time()
            for ep in range(2000):
                z = torch.randn(8, dim)
                x, log_det = model(z)

                # Data fitting loss: 0.5 * (y - Fx)^T Sigma^{-1} (y - Fx)
                residual = y.unsqueeze(0) - (F_mat @ x.T).T  # (batch, K)
                data_loss = 0.5 * (residual ** 2 / torch.diag(Sigma).unsqueeze(0)).sum(1)

                # Prior loss: 0.5 * (x - mu)^T Lambda^{-1} (x - mu)
                prior_loss = 0.5 * ((x - mu.unsqueeze(0))**2 / prior_std**2).sum(1)

                # Total loss
                loss = (data_loss + lambda_reg * prior_loss - beta * log_det).mean()

                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                sched.step()

                if (ep + 1) % 500 == 0:
                    print(f"  [{arch_name} b={beta}] Ep {ep+1}: loss={loss.item():.2f}")
                    sys.stdout.flush()

            # Evaluate
            with torch.no_grad():
                zs = torch.randn(512, dim)
                xs, lds = model(zs)
                dpi_mean = xs.mean(0)
                dpi_std = xs.std(0)
                dpi_cov = torch.zeros(dim, dim)
                centered = xs - dpi_mean.unsqueeze(0)
                dpi_cov = (centered.T @ centered) / (512 - 1)

            # Compute KL with analytical posterior
            kl = compute_kl_gaussian(dpi_mean, dpi_cov, m_post, C_post)
            dt = time.time() - t0
            beta_kls[str(beta)] = kl
            print(f"  [{arch_name}] beta={beta}: KL={kl:.4f} ({dt:.1f}s)")
            sys.stdout.flush()

        results[arch_name] = {
            "kl_vs_beta": beta_kls,
            "best_beta": min(beta_kls, key=beta_kls.get),
            "best_kl": min(beta_kls.values()),
            "dpi_mean_range": [dpi_mean.min().item(), dpi_mean.max().item()],
            "dpi_std_range": [dpi_std.min().item(), dpi_std.max().item()],
        }

    return results


if __name__ == "__main__":
    results = run_convex_imaging()
    print("\n\nSUMMARY")
    print("="*50)
    print(json.dumps(results, indent=2))
    with open("interferometric_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved interferometric_results.json")
