"""
DPI Toy Examples: 2D distribution learning with Real-NVP.
Reproduces Figure 1 from the paper.
Key result: beta=1 minimizes KL divergence between learned and true distributions.
"""
import torch
import torch.nn as nn
import numpy as np
import json
import time
import sys


class AffineCoupling(nn.Module):
    def __init__(self, hd=64):
        super().__init__()
        self.s = nn.Sequential(nn.Linear(1, hd), nn.LeakyReLU(0.01), nn.Linear(hd, 1))
        self.t = nn.Sequential(nn.Linear(1, hd), nn.LeakyReLU(0.01), nn.Linear(hd, 1))

    def forward(self, z):
        z1, z2 = z[:, :1], z[:, 1:]
        s = torch.tanh(self.s(z1)) * 3.0
        t = self.t(z1)
        return torch.cat([z1, z2 * torch.exp(s) + t], 1), s.sum(1)


class RealNVP2D(nn.Module):
    def __init__(self, n_layers=8, hd=64):
        super().__init__()
        self.layers = nn.ModuleList([AffineCoupling(hd) for _ in range(n_layers)])
        self.perms = [torch.randperm(2) for _ in range(n_layers)]

    def forward(self, z):
        ld = torch.zeros(z.shape[0])
        for i, layer in enumerate(self.layers):
            z, d = layer(z)
            ld += d
            z = z[:, self.perms[i]]
        return z, ld


def gaussian_mixture_potential(x):
    mu1, mu2 = torch.tensor([2.0, 0.0]), torch.tensor([-2.0, 0.0])
    sigma = 0.5
    lp1 = -0.5 * ((x - mu1)**2).sum(1) / sigma**2
    lp2 = -0.5 * ((x - mu2)**2).sum(1) / sigma**2
    return -torch.logsumexp(torch.stack([lp1, lp2], 1), 1)


def bowtie_potential(x):
    r2 = (x**2).sum(1)
    angle = torch.atan2(x[:, 1], x[:, 0])
    return 0.5 * r2 / 4.0 - 2.0 * torch.cos(2 * angle)


def sinusoidal_potential(x):
    w1 = torch.sin(2 * np.pi * x[:, 0] / 4.0)
    return 0.5 * (x[:, 1] - w1)**2 / 0.3**2 + 0.5 * x[:, 0]**2 / 4.0


def estimate_log_Z(pot_fn, rng=6.0, n=300):
    lin = torch.linspace(-rng, rng, n)
    xx, yy = torch.meshgrid(lin, lin, indexing='ij')
    pts = torch.stack([xx.flatten(), yy.flatten()], 1)
    dx = (2 * rng / n)**2
    return (torch.logsumexp(-pot_fn(pts), 0) + np.log(dx)).item()


def compute_kl(model, pot_fn, log_Z, ns=10000):
    with torch.no_grad():
        z = torch.randn(ns, 2)
        x, ld = model(z)
        log_qx = -0.5 * (z**2).sum(1) - np.log(2*np.pi) - ld
        log_px = -pot_fn(x) - log_Z
        return (log_qx - log_px).mean().item()


def train_dpi(pot_fn, log_Z, beta=1.0, n_layers=8, hd=64,
              epochs=2000, bs=256, lr=1e-3, seed=42):
    torch.manual_seed(seed)
    model = RealNVP2D(n_layers, hd)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)

    for ep in range(epochs):
        z = torch.randn(bs, 2)
        x, ld = model(z)
        loss = (pot_fn(x) - beta * ld).mean()
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

    return model, compute_kl(model, pot_fn, log_Z, 20000)


def main():
    pots = {
        "gaussian_mixture": gaussian_mixture_potential,
        "bowtie": bowtie_potential,
        "sinusoidal": sinusoidal_potential,
    }

    log_Zs = {n: estimate_log_Z(f) for n, f in pots.items()}
    for n, lz in log_Zs.items():
        print(f"log Z({n}) = {lz:.4f}")

    betas = [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    results = {}

    for dname, pfn in pots.items():
        print(f"\n{'='*50}\n{dname}\n{'='*50}")
        sys.stdout.flush()
        kls = {}
        for beta in betas:
            t0 = time.time()
            _, kl = train_dpi(pfn, log_Zs[dname], beta=beta,
                              n_layers=8, hd=64, epochs=2000, bs=256, lr=1e-3)
            dt = time.time() - t0
            kls[str(beta)] = kl
            print(f"  beta={beta:5.1f}: KL={kl:.4f} ({dt:.1f}s)")
            sys.stdout.flush()

        results[dname] = kls
        best = min(kls, key=kls.get)
        print(f"  BEST beta={best} (KL={kls[best]:.4f})")

    print("\n\nSUMMARY")
    print("="*50)
    for dname, kls in results.items():
        print(f"\n{dname}:")
        for b, kl in sorted(kls.items(), key=lambda x: float(x[0])):
            m = " <-- BEST" if kl == min(kls.values()) else ""
            print(f"  beta={float(b):5.1f}: KL={kl:.4f}{m}")

    with open("toy_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved toy_results.json")
    return results


if __name__ == "__main__":
    main()
