"""Test reconstruction with better step size on toy problem."""
import numpy as np
import time
from bpm_tomo import *

Nx, Ny, K = 64, 64, 32
lam = 561e-9
n0 = 1.518
k0 = 2 * np.pi / lam
Lx = Ly = 9.216e-6
Lz = 4.608e-6
dx = Lx / Nx
dy = Ly / Ny
dz = Lz / K

H = build_diffraction_kernel(Nx, Ny, dx, dy, dz, k0, n0)
phantom = create_bead_phantom(Nx, Ny, K, dx, dy, dz, 2.5e-6, 0.03)

# Generate multiple views
L = 21  # fewer views for toy
angles = np.linspace(-np.pi/8, np.pi/8, L)
measurements = []
for angle in angles:
    y0 = make_input_field(Nx, Ny, dx, dy, k0, n0, angle)
    y_K = bpm_forward(phantom, y0, H, k0, dz)
    measurements.append((y0, y_K))
print(f"Generated {L} measurements")

# Test reconstruction with different step sizes
def reconstruct_v2(measurements, H, k0, dz, dx, dy, dz_step,
                   tau, x_bounds, L_tilde, max_iter, Nx, Ny, K,
                   gamma0=0.01, use_momentum=True, verbose=True):
    """Improved reconstruction with better step size."""
    L = len(measurements)
    x_hat = np.zeros((Nx, Ny, K), dtype=np.float64)
    s = x_hat.copy()
    q = 1.0
    x_prev = x_hat.copy()
    rng = np.random.RandomState(42)
    
    for t in range(1, max_iter + 1):
        gamma_t = gamma0 / np.sqrt(t)
        indices = rng.choice(L, size=min(L_tilde, L), replace=False)
        
        total_grad = np.zeros((Nx, Ny, K), dtype=np.float64)
        total_cost = 0.0
        for idx in indices:
            y0, y_K = measurements[idx]
            grad, cost = bpm_gradient(s, y0, y_K, H, k0, dz)
            total_grad += grad
            total_cost += cost
        total_grad /= len(indices)
        total_cost /= len(indices)
        
        z_t = s - gamma_t * total_grad
        x_hat = tv_prox_fgp(z_t, tau * gamma_t, dx, dy, dz_step,
                            a=x_bounds[0], b=x_bounds[1], max_iter=10)
        
        if use_momentum:
            q_new = (1 + np.sqrt(1 + 4 * q**2)) / 2
            ratio = (q - 1) / q_new
            s = x_hat + ratio * (x_hat - x_prev)
            s = np.clip(s, x_bounds[0], x_bounds[1])
            q = q_new
        else:
            s = x_hat.copy()
        
        diff = np.linalg.norm(x_hat.ravel() - x_prev.ravel())
        norm_prev = np.linalg.norm(x_prev.ravel())
        rel_change = diff / max(norm_prev, 1e-10)
        x_prev = x_hat.copy()
        
        if verbose and t % 50 == 0:
            snr = compute_snr(phantom, x_hat)
            print(f"  Iter {t:4d}: cost={total_cost:.4e}, SNR={snr:.2f}dB, rel={rel_change:.4e}")
    
    return x_hat

# Test different gamma0 values without momentum
print("\n--- No momentum, tau=0.01 ---")
for g0 in [0.005, 0.01, 0.02]:
    t0 = time.time()
    x_r = reconstruct_v2(measurements, H, k0, dz, dx, dy, dz,
                         tau=0.01, x_bounds=(0, 0.1), L_tilde=4,
                         max_iter=200, Nx=Nx, Ny=Ny, K=K,
                         gamma0=g0, use_momentum=False, verbose=False)
    snr = compute_snr(phantom, x_r)
    print(f"  gamma0={g0}: SNR={snr:.2f}dB, time={time.time()-t0:.1f}s")

# Test with momentum
print("\n--- With momentum, tau=0.01 ---")
for g0 in [0.005, 0.01, 0.02]:
    t0 = time.time()
    x_r = reconstruct_v2(measurements, H, k0, dz, dx, dy, dz,
                         tau=0.01, x_bounds=(0, 0.1), L_tilde=4,
                         max_iter=200, Nx=Nx, Ny=Ny, K=K,
                         gamma0=g0, use_momentum=True, verbose=False)
    snr = compute_snr(phantom, x_r)
    print(f"  gamma0={g0}: SNR={snr:.2f}dB, time={time.time()-t0:.1f}s")

# Best config with more iterations
print("\n--- Best config, 500 iterations ---")
t0 = time.time()
x_r = reconstruct_v2(measurements, H, k0, dz, dx, dy, dz,
                     tau=0.01, x_bounds=(0, 0.1), L_tilde=4,
                     max_iter=500, Nx=Nx, Ny=Ny, K=K,
                     gamma0=0.01, use_momentum=False, verbose=True)
snr = compute_snr(phantom, x_r)
print(f"Final SNR: {snr:.2f}dB, time={time.time()-t0:.1f}s")
print(f"Recon range: [{x_r.min():.4f}, {x_r.max():.4f}]")
