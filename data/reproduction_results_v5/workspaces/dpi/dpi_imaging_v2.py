"""
DPI Imaging Experiments - Improved version.
Uses 8x8 images with better model architecture and training.
"""
import torch
import torch.nn as nn
import torch.nn.functional as tF
import numpy as np
import json
import time
import sys


class AC(nn.Module):
    def __init__(self, dim, hd=48):
        super().__init__()
        sp = dim // 2
        self.sp = sp
        self.s = nn.Sequential(nn.Linear(sp, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, dim - sp))
        self.t = nn.Sequential(nn.Linear(sp, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, hd), nn.LeakyReLU(0.01),
                                nn.Linear(hd, dim - sp))

    def forward(self, z):
        z1, z2 = z[:, :self.sp], z[:, self.sp:]
        s = torch.tanh(self.s(z1)) * 3
        t = self.t(z1)
        return torch.cat([z1, z2 * torch.exp(s) + t], 1), s.sum(1)


class Flow(nn.Module):
    def __init__(self, dim, n_layers=4, hd=48, softplus=False):
        super().__init__()
        self.softplus = softplus
        self.layers = nn.ModuleList([AC(dim, hd) for _ in range(n_layers)])
        self.perms = [torch.randperm(dim) for _ in range(n_layers)]

    def forward(self, z):
        ld = torch.zeros(z.shape[0])
        for i, l in enumerate(self.layers):
            z, d = l(z)
            ld += d
            z = z[:, self.perms[i]]
        if self.softplus:
            ld += tF.logsigmoid(z).sum(1)
            z = tF.softplus(z)
        return z, ld


def create_crescent(M=8, total_flux=2.0):
    fov = 160
    x = np.linspace(-fov/2, fov/2, M)
    xx, yy = np.meshgrid(x, x)
    r = np.sqrt(xx**2 + yy**2)
    ring = np.exp(-0.5 * ((r - 22) / 10)**2)
    asym = 1.0 + 0.5 * np.sin(np.arctan2(yy, xx) - np.pi/3)
    dep = 1.0 - 0.7 * np.exp(-0.5 * (r/12)**2)
    img = ring * asym * dep
    img = img / img.sum() * total_flux
    return torch.tensor(img.flatten(), dtype=torch.float32)


def create_fourier_mat(M=8, n_uv=30):
    fov_rad = 160 * np.pi / (180 * 3600 * 1e6)
    pix_rad = fov_rad / M
    coords = (np.arange(M) - M/2 + 0.5) * pix_rad
    xx, yy = np.meshgrid(coords, coords)
    xf, yf = xx.flatten(), yy.flatten()
    np.random.seed(42)
    us = np.random.uniform(-4e9, 4e9, n_uv)
    vs = np.random.uniform(-4e9, 4e9, n_uv)
    Fc = np.zeros((n_uv, M*M), dtype=np.complex64)
    for k in range(n_uv):
        Fc[k] = np.exp(-2j * np.pi * (us[k]*xf + vs[k]*yf))
    Fr = np.vstack([Fc.real, Fc.imag]).astype(np.float32)
    return torch.tensor(Fr)


def create_phantom(M=8):
    x = np.linspace(-1, 1, M)
    xx, yy = np.meshgrid(x, x)
    outer = np.exp(-((xx/0.7)**2 + (yy/0.5)**2)**2 * 2)
    bone1 = 0.8 * np.exp(-((xx-0.1)**2 + (yy+0.1)**2) / 0.03)
    bone2 = 0.6 * np.exp(-((xx+0.15)**2 + (yy-0.05)**2) / 0.025)
    img = outer + bone1 + bone2
    img = img / img.max()
    return torch.tensor(img.flatten(), dtype=torch.float32)


def create_mri_mask_proper(M, accel):
    """Proper MRI undersampling - select random k-space lines."""
    np.random.seed(int(accel * 1000))
    n_lines = max(2, int(M / accel))
    # Always include DC line
    selected = [M//2]
    available = list(range(M))
    available.remove(M//2)
    extra = np.random.choice(available, min(n_lines-1, len(available)), replace=False)
    selected.extend(extra.tolist())

    mask = np.zeros((M, M), dtype=bool)
    for line in selected:
        mask[line, :] = True
    return mask, len(selected)


def create_mri_fmat(mask, M=8):
    dft1d = np.fft.fftshift(np.fft.fft(np.eye(M), axis=0), axes=0) / np.sqrt(M)
    dft2d = np.kron(dft1d, dft1d)
    mf = mask.flatten()
    Fc = dft2d[mf]
    Fr = np.vstack([Fc.real, Fc.imag]).astype(np.float32)
    return torch.tensor(Fr), mf.sum()


def tv(x, M):
    b = x.shape[0]
    img = x.view(b, M, M)
    return ((img[:, 1:, :] - img[:, :-1, :]).abs().sum((1,2)) +
            (img[:, :, 1:] - img[:, :, :-1]).abs().sum((1,2)))


def train_dpi(model, F_mat, y, sigma2_diag, prior_fn, beta, epochs=1000, bs=4, lr=5e-4):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    dim = F_mat.shape[1]

    for ep in range(epochs):
        z = torch.randn(bs, dim)
        x, ld = model(z)
        res = y.unsqueeze(0) - (F_mat @ x.T).T
        data_loss = 0.5 * (res**2 / sigma2_diag.unsqueeze(0)).sum(1)
        prior_loss = prior_fn(x)
        loss = (data_loss + prior_loss - beta * ld).mean()
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

        if (ep+1) % 200 == 0:
            print(f"    ep {ep+1}: loss={loss.item():.2f}", flush=True)

    return model


def sample_model(model, dim, n=512, bs=64):
    all_xs = []
    with torch.no_grad():
        for i in range(0, n, bs):
            b = min(bs, n - i)
            z = torch.randn(b, dim)
            x, _ = model(z)
            all_xs.append(x)
    return torch.cat(all_xs, 0)


def run_interferometric():
    print("\n" + "="*60)
    print("CONVEX INTERFEROMETRIC IMAGING (8x8)")
    print("="*60)

    M = 8
    dim = M * M
    x_true = create_crescent(M)
    F_mat = create_fourier_mat(M, n_uv=20)
    K = F_mat.shape[0]

    noise_std = 0.05
    sigma2 = torch.ones(K) * noise_std**2
    torch.manual_seed(123)
    y = F_mat @ x_true + torch.randn(K) * noise_std

    # Gaussian prior
    mu = torch.ones(dim) * x_true.mean()
    prior_var = 0.1**2
    Lambda = torch.eye(dim) * prior_var

    # Analytical posterior
    Sigma = torch.diag(sigma2)
    FLam = F_mat @ Lambda
    S = Sigma + FLam @ F_mat.T
    Kg = Lambda @ F_mat.T @ torch.linalg.inv(S)
    m_post = mu + Kg @ (y - F_mat @ mu)
    C_post = Lambda - Kg @ F_mat @ Lambda
    post_std = torch.sqrt(torch.clamp(torch.diag(C_post), min=1e-10))
    print(f"Analytical: mean [{m_post.min():.4f},{m_post.max():.4f}], "
          f"std [{post_std.min():.4f},{post_std.max():.4f}]")

    prior_fn = lambda x: 0.5 * ((x - mu)**2 / prior_var).sum(1)
    results = {}

    for beta in [0.5, 1.0, 2.0]:
        torch.manual_seed(42)
        model = Flow(dim, n_layers=4, hd=48)
        t0 = time.time()
        print(f"\n  Training beta={beta}...")
        train_dpi(model, F_mat, y, sigma2, prior_fn, beta, epochs=1000, bs=4, lr=5e-4)
        xs = sample_model(model, dim, n=512)
        dpi_mean = xs.mean(0)
        dpi_std = xs.std(0)

        mean_mse = ((dpi_mean - m_post)**2).mean().item()
        std_mse = ((dpi_std - post_std)**2).mean().item()
        mc = torch.corrcoef(torch.stack([dpi_mean, m_post]))[0,1].item()
        sc = torch.corrcoef(torch.stack([dpi_std, post_std]))[0,1].item()
        dt = time.time() - t0

        results[str(beta)] = {"mean_mse": mean_mse, "std_mse": std_mse,
                               "mean_corr": mc, "std_corr": sc}
        print(f"  beta={beta}: mean_MSE={mean_mse:.6f}, mean_corr={mc:.4f}, "
              f"std_corr={sc:.4f} ({dt:.0f}s)")
        sys.stdout.flush()

    best = min(results, key=lambda b: results[b]["mean_mse"])
    print(f"\n  Best beta (by mean MSE): {best}")
    return results


def run_mri():
    print("\n" + "="*60)
    print("COMPRESSED SENSING MRI (8x8)")
    print("="*60)

    M = 8
    dim = M * M
    x_true = create_phantom(M)
    print(f"Image: {M}x{M}, range [{x_true.min():.3f}, {x_true.max():.3f}]")

    # Use line-based undersampling for proper acceleration
    accel_configs = [
        (2.0, 4),   # 4 out of 8 lines
        (4.0, 2),   # 2 out of 8 lines
        (8.0, 1),   # 1 out of 8 lines
    ]
    results = {}

    for target_accel, n_lines in accel_configs:
        np.random.seed(int(target_accel * 100))
        # Create mask with specified number of lines
        mask = np.zeros((M, M), dtype=bool)
        selected = [M//2]  # Always include DC
        available = list(range(M))
        available.remove(M//2)
        if n_lines > 1:
            extra = np.random.choice(available, n_lines-1, replace=False)
            selected.extend(extra.tolist())
        for line in selected:
            mask[line, :] = True

        F_mat, ns = create_mri_fmat(mask, M)
        K = F_mat.shape[0]
        actual_accel = dim / ns
        print(f"\n  Target {target_accel}x: {len(selected)} lines, "
              f"sampled={ns}/{dim}, actual={actual_accel:.1f}x")

        dc = x_true.sum().item()
        noise_std = 0.001 * dc
        sigma2 = torch.ones(K) * noise_std**2
        torch.manual_seed(int(target_accel * 100))
        y = F_mat @ x_true + torch.randn(K) * noise_std

        lam_tv = 0.1
        prior_fn = lambda x: lam_tv * tv(x, M)

        torch.manual_seed(42)
        model = Flow(dim, n_layers=4, hd=48)
        t0 = time.time()
        print(f"  Training...")
        train_dpi(model, F_mat, y, sigma2, prior_fn, beta=1.0,
                  epochs=1000, bs=4, lr=5e-4)
        xs = sample_model(model, dim, n=512)
        dpi_mean = xs.mean(0)
        dpi_std = xs.std(0)

        ae = (dpi_mean - x_true).abs()
        w4s = (ae < 4 * dpi_std).float().mean().item() * 100
        w2s = (ae < 2 * dpi_std).float().mean().item() * 100
        rmse = ((dpi_mean - x_true)**2).mean().sqrt().item()
        ms = dpi_std.mean().item()
        # Handle constant std case
        if dpi_std.std() < 1e-8:
            ec = 0.0
        else:
            ec = torch.corrcoef(torch.stack([ae, dpi_std]))[0,1].item()
        dt = time.time() - t0

        results[str(target_accel)] = {
            "actual_acceleration": actual_accel,
            "n_lines_sampled": len(selected),
            "within_4sigma_pct": w4s, "within_2sigma_pct": w2s,
            "rmse": rmse, "mean_std": ms, "error_std_corr": ec
        }
        print(f"  {target_accel}x: RMSE={rmse:.4f}, std={ms:.4f}, "
              f"4σ={w4s:.1f}%, 2σ={w2s:.1f}% ({dt:.0f}s)")
        sys.stdout.flush()

    # Check key paper claim: std increases with acceleration
    stds = [results[str(a)]["mean_std"] for a in [2.0, 4.0, 8.0]]
    std_increases = all(stds[i] <= stds[i+1] for i in range(len(stds)-1))
    print(f"\n  Std increases with acceleration: {std_increases}")
    print(f"  Stds: {stds}")

    return results


if __name__ == "__main__":
    t0 = time.time()
    ir = run_interferometric()
    mr = run_mri()
    print(f"\nTotal: {(time.time()-t0)/60:.1f} min")

    res = {"interferometric": ir, "mri": mr}
    with open("imaging_results.json", "w") as f:
        json.dump(res, f, indent=2)
    print("Saved imaging_results.json")
