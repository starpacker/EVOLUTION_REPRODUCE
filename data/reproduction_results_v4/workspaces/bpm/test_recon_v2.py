"""Test reconstruction with unit-spacing TV and debugging."""
import numpy as np
import time
from bpm_tomo import *


def gradient_3d_unit(x):
    """Discrete gradient with unit spacing."""
    gx = np.zeros_like(x)
    gy = np.zeros_like(x)
    gz = np.zeros_like(x)
    gx[:-1, :, :] = x[1:, :, :] - x[:-1, :, :]
    gy[:, :-1, :] = x[:, 1:, :] - x[:, :-1, :]
    gz[:, :, :-1] = x[:, :, 1:] - x[:, :, :-1]
    return gx, gy, gz


def divergence_3d_unit(gx, gy, gz):
    """D^T with unit spacing."""
    div = np.zeros_like(gx)
    div[0, :, :] = gx[0, :, :]
    div[1:-1, :, :] = gx[1:-1, :, :] - gx[:-2, :, :]
    div[-1, :, :] = -gx[-2, :, :]
    div[:, 0, :] += gy[:, 0, :]
    div[:, 1:-1, :] += gy[:, 1:-1, :] - gy[:, :-2, :]
    div[:, -1, :] += -gy[:, -2, :]
    div[:, :, 0] += gz[:, :, 0]
    div[:, :, 1:-1] += gz[:, :, 1:-1] - gz[:, :, :-2]
    div[:, :, -1] += -gz[:, :, -2]
    return div


def tv_prox_unit(z, tau, a=0.0, b=0.1, max_iter=10):
    """FGP with unit spacing."""
    gamma = 1.0 / (12.0 * tau)  # Lipschitz = 12 for 3D unit spacing
    gx = np.zeros_like(z)
    gy = np.zeros_like(z)
    gz = np.zeros_like(z)
    dx_d, dy_d, dz_d = gx.copy(), gy.copy(), gz.copy()
    q_old = 1.0
    
    for t in range(max_iter):
        div_d = divergence_3d_unit(dx_d, dy_d, dz_d)
        x_t = np.clip(z - tau * div_d, a, b)
        grad_x, grad_y, grad_z = gradient_3d_unit(x_t)
        gx_new = dx_d + gamma * grad_x
        gy_new = dy_d + gamma * grad_y
        gz_new = dz_d + gamma * grad_z
        # Project onto unit ball (isotropic)
        norm = np.sqrt(gx_new**2 + gy_new**2 + gz_new**2)
        norm = np.maximum(norm, 1.0)
        gx_new /= norm; gy_new /= norm; gz_new /= norm
        
        q_new = (1 + np.sqrt(1 + 4 * q_old**2)) / 2
        ratio = (q_old - 1) / q_new
        dx_d = gx_new + ratio * (gx_new - gx)
        dy_d = gy_new + ratio * (gy_new - gy)
        dz_d = gz_new + ratio * (gz_new - gz)
        gx, gy, gz = gx_new, gy_new, gz_new
        q_old = q_new
    
    div_g = divergence_3d_unit(gx, gy, gz)
    return np.clip(z - tau * div_g, a, b)


def reconstruct_v3(measurements, H, k0, dz, tau, x_bounds, L_tilde,
                   max_iter, Nx, Ny, K, phantom=None, gamma0=0.01,
                   verbose=True):
    """Reconstruction with unit-spacing TV."""
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
        
        if tau > 0:
            x_hat = tv_prox_unit(z_t, tau * gamma_t,
                                 a=x_bounds[0], b=x_bounds[1], max_iter=10)
        else:
            x_hat = np.clip(z_t, x_bounds[0], x_bounds[1])
        
        # FISTA momentum
        q_new = (1 + np.sqrt(1 + 4 * q**2)) / 2
        ratio = (q - 1) / q_new
        s = x_hat + ratio * (x_hat - x_prev)
        s = np.clip(s, x_bounds[0], x_bounds[1])
        q = q_new
        
        diff = np.linalg.norm(x_hat.ravel() - x_prev.ravel())
        norm_prev = max(np.linalg.norm(x_prev.ravel()), 1e-10)
        rel_change = diff / norm_prev
        x_prev = x_hat.copy()
        
        if verbose and (t <= 10 or t % 50 == 0):
            snr_val = compute_snr(phantom, x_hat) if phantom is not None else 0
            gn = np.linalg.norm(total_grad)
            print(f"  t={t:4d}: cost={total_cost:.4e}, SNR={snr_val:.2f}dB, "
                  f"|grad|={gn:.2e}, gamma={gamma_t:.4e}, rel={rel_change:.4e}, "
                  f"x:[{x_hat.min():.4f},{x_hat.max():.4f}]")
    
    return x_hat


# Setup
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

L = 21
angles = np.linspace(-np.pi/8, np.pi/8, L)
measurements = []
for angle in angles:
    y0 = make_input_field(Nx, Ny, dx, dy, k0, n0, angle)
    y_K = bpm_forward(phantom, y0, H, k0, dz)
    measurements.append((y0, y_K))
print(f"Generated {L} measurements")

# Test 1: No TV, just box constraint
print("\n=== No TV (tau=0), gamma0=0.01 ===")
t0 = time.time()
x_r = reconstruct_v3(measurements, H, k0, dz, tau=0, x_bounds=(0, 0.1),
                     L_tilde=4, max_iter=300, Nx=Nx, Ny=Ny, K=K,
                     phantom=phantom, gamma0=0.01)
print(f"Time: {time.time()-t0:.1f}s, Final SNR: {compute_snr(phantom, x_r):.2f}dB")

# Test 2: With TV
print("\n=== TV tau=0.01, gamma0=0.01 ===")
t0 = time.time()
x_r = reconstruct_v3(measurements, H, k0, dz, tau=0.01, x_bounds=(0, 0.1),
                     L_tilde=4, max_iter=300, Nx=Nx, Ny=Ny, K=K,
                     phantom=phantom, gamma0=0.01)
print(f"Time: {time.time()-t0:.1f}s, Final SNR: {compute_snr(phantom, x_r):.2f}dB")
