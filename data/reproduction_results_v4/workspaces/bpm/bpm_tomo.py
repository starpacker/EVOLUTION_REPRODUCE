"""
BPM-based Optical Tomographic Reconstruction
Reproducing: "Optical tomographic image reconstruction based on beam propagation and sparse regularization"
Key experiment: Figure 4 - 10um bead reconstruction, target SNR = 22.74 dB
"""
import numpy as np
from numpy.fft import fft2, ifft2, fftfreq
import json
import time
import sys


def build_diffraction_kernel(Nx, Ny, dx, dy, dz, k0, n0):
    """Build the frequency-domain diffraction phase mask H (nonparaxial)."""
    fx = fftfreq(Nx, d=dx)
    fy = fftfreq(Ny, d=dy)
    FX, FY = np.meshgrid(fx, fy, indexing='ij')
    wx = 2 * np.pi * FX
    wy = 2 * np.pi * FY
    w2 = wx**2 + wy**2
    k0n0 = k0 * n0
    k0n0_sq = k0n0**2
    sqrt_arg = np.maximum(k0n0_sq - w2, 0.0)
    sqrt_val = np.sqrt(sqrt_arg)
    denom = k0n0 + sqrt_val
    denom = np.maximum(denom, 1e-10)
    phase = -(w2 / denom) * dz
    H = np.exp(-1j * phase)
    H[w2 > k0n0_sq] = 0.0
    return H


def bpm_forward(x_3d, y0, H, k0, dz, return_all=False):
    """BPM forward propagation."""
    Nx, Ny, K = x_3d.shape
    if return_all:
        y_all = np.zeros((Nx, Ny, K + 1), dtype=np.complex128)
        y_all[:, :, 0] = y0
    y_k = y0.copy()
    for k in range(K):
        y_diff = ifft2(fft2(y_k) * H)
        p_k = np.exp(1j * k0 * dz * x_3d[:, :, k])
        y_k = p_k * y_diff
        if return_all:
            y_all[:, :, k + 1] = y_k
    if return_all:
        return y_k, y_all
    return y_k


def bpm_gradient(x_3d, y0, y_meas, H, k0, dz):
    """Time-reversal gradient computation (Algorithm 1)."""
    Nx, Ny, K = x_3d.shape
    y_K, y_all = bpm_forward(x_3d, y0, H, k0, dz, return_all=True)
    r_K = y_K - y_meas
    cost = 0.5 * np.sum(np.abs(r_K)**2)
    HH = np.conj(H)
    grad = np.zeros((Nx, Ny, K), dtype=np.float64)
    s_m = r_K.copy()
    for m in range(K, 0, -1):
        p_m = np.exp(1j * k0 * dz * x_3d[:, :, m - 1])
        y_diff = ifft2(fft2(y_all[:, :, m - 1]) * H)
        grad[:, :, m - 1] = np.real((-1j * k0 * dz) * np.conj(p_m) * np.conj(y_diff) * s_m)
        s_m = ifft2(fft2(np.conj(p_m) * s_m) * HH)
    return grad, cost


def gradient_3d(x, dx, dy, dz_step):
    """Compute discrete gradient of 3D volume."""
    gx = np.zeros_like(x)
    gy = np.zeros_like(x)
    gz = np.zeros_like(x)
    gx[:-1, :, :] = (x[1:, :, :] - x[:-1, :, :]) / dx
    gy[:, :-1, :] = (x[:, 1:, :] - x[:, :-1, :]) / dy
    gz[:, :, :-1] = (x[:, :, 1:] - x[:, :, :-1]) / dz_step
    return gx, gy, gz


def divergence_3d(gx, gy, gz, dx, dy, dz_step):
    """Compute D^T g (negative divergence)."""
    div = np.zeros_like(gx)
    div[0, :, :] = gx[0, :, :] / dx
    div[1:-1, :, :] = (gx[1:-1, :, :] - gx[:-2, :, :]) / dx
    div[-1, :, :] = -gx[-2, :, :] / dx
    div[:, 0, :] += gy[:, 0, :] / dy
    div[:, 1:-1, :] += (gy[:, 1:-1, :] - gy[:, :-2, :]) / dy
    div[:, -1, :] += -gy[:, -2, :] / dy
    div[:, :, 0] += gz[:, :, 0] / dz_step
    div[:, :, 1:-1] += (gz[:, :, 1:-1] - gz[:, :, :-2]) / dz_step
    div[:, :, -1] += -gz[:, :, -2] / dz_step
    return div


def proj_X(x, a=0.0, b=0.1):
    """Project onto box constraint [a, b]."""
    return np.clip(x, a, b)


def proj_G_iso(gx, gy, gz):
    """Project onto unit ball for isotropic TV."""
    norm = np.sqrt(gx**2 + gy**2 + gz**2)
    norm = np.maximum(norm, 1.0)
    return gx / norm, gy / norm, gz / norm


def tv_prox_fgp(z, tau, dx, dy, dz_step, a=0.0, b=0.1, max_iter=10, tol=1e-4):
    """FGP for computing prox_R(z, tau) - Algorithm 4."""
    L_lip = 2.0 / dx**2 + 2.0 / dy**2 + 2.0 / dz_step**2
    gamma = 1.0 / (L_lip * tau)
    
    gx = np.zeros_like(z)
    gy = np.zeros_like(z)
    gz = np.zeros_like(z)
    dx_d, dy_d, dz_d = gx.copy(), gy.copy(), gz.copy()
    q_old = 1.0
    
    for t in range(max_iter):
        div_d = divergence_3d(dx_d, dy_d, dz_d, dx, dy, dz_step)
        x_t = proj_X(z - tau * div_d, a, b)
        grad_x, grad_y, grad_z = gradient_3d(x_t, dx, dy, dz_step)
        gx_new = dx_d + gamma * grad_x
        gy_new = dy_d + gamma * grad_y
        gz_new = dz_d + gamma * grad_z
        gx_new, gy_new, gz_new = proj_G_iso(gx_new, gy_new, gz_new)
        
        q_new = (1 + np.sqrt(1 + 4 * q_old**2)) / 2
        ratio = (q_old - 1) / q_new
        dx_d = gx_new + ratio * (gx_new - gx)
        dy_d = gy_new + ratio * (gy_new - gy)
        dz_d = gz_new + ratio * (gz_new - gz)
        
        gx, gy, gz = gx_new, gy_new, gz_new
        q_old = q_new
    
    div_g = divergence_3d(gx, gy, gz, dx, dy, dz_step)
    x_t = proj_X(z - tau * div_g, a, b)
    return x_t


def make_input_field(Nx, Ny, dx, dy, k0, n0, angle_rad):
    """Create input field for a tilted plane wave."""
    x = (np.arange(Nx) - Nx // 2) * dx
    y = (np.arange(Ny) - Ny // 2) * dy
    X, Y = np.meshgrid(x, y, indexing='ij')
    kx = k0 * n0 * np.sin(angle_rad)
    a0 = np.exp(1j * kx * X)
    return a0


def compute_snr(x_true, x_recon):
    """SNR in dB."""
    num = np.sum(x_true**2)
    den = np.sum((x_true - x_recon)**2)
    if den < 1e-30:
        return float('inf')
    return 10 * np.log10(num / den)


def create_bead_phantom(Nx, Ny, K, dx, dy, dz, diameter, delta_n):
    """Create a spherical bead phantom."""
    x = (np.arange(Nx) - Nx // 2) * dx
    y = (np.arange(Ny) - Ny // 2) * dy
    z = (np.arange(K) - K // 2) * dz
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2)
    phantom = np.zeros((Nx, Ny, K), dtype=np.float64)
    phantom[R <= diameter / 2] = delta_n
    return phantom


def reconstruct(measurements, H, k0, dz, dx, dy, dz_step,
                tau, x_bounds, L_tilde, max_iter, Nx, Ny, K,
                verbose=True):
    """Algorithm 2: Stochastic proximal-gradient with TV regularization."""
    L = len(measurements)
    x_hat = np.zeros((Nx, Ny, K), dtype=np.float64)
    s = x_hat.copy()
    q = 1.0
    x_prev = x_hat.copy()
    rng = np.random.RandomState(42)
    
    for t in range(1, max_iter + 1):
        gamma_t = 0.5 / np.sqrt(t)
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
        
        q_new = (1 + np.sqrt(1 + 4 * q**2)) / 2
        ratio = (q - 1) / q_new
        s = x_hat + ratio * (x_hat - x_prev)
        s = np.clip(s, x_bounds[0], x_bounds[1])
        
        diff = np.linalg.norm(x_hat.ravel() - x_prev.ravel())
        norm_prev = np.linalg.norm(x_prev.ravel())
        rel_change = diff / max(norm_prev, 1e-10)
        
        x_prev = x_hat.copy()
        q = q_new
        
        if verbose and t % 25 == 0:
            print(f"  Iter {t:4d}: cost={total_cost:.6e}, rel_change={rel_change:.6e}")
            sys.stdout.flush()
        
        if t > 10 and rel_change < 1e-4:
            if verbose:
                print(f"  Converged at iteration {t}")
            break
    
    return x_hat


def toy_test():
    """Small-scale test to verify BPM forward/backward correctness."""
    print("=" * 60)
    print("TOY TEST: Verifying BPM forward/backward")
    print("=" * 60)
    
    Nx, Ny, K = 64, 64, 32
    lam = 561e-9
    n0 = 1.518
    k0 = 2 * np.pi / lam
    Lx = Ly = 9.216e-6
    Lz = 4.608e-6
    dx = Lx / Nx
    dy = Ly / Ny
    dz = Lz / K
    
    print(f"  Grid: {Nx}x{Ny}x{K}, dx={dx*1e9:.1f}nm, dz={dz*1e9:.1f}nm")
    
    H = build_diffraction_kernel(Nx, Ny, dx, dy, dz, k0, n0)
    phantom = create_bead_phantom(Nx, Ny, K, dx, dy, dz, 2.5e-6, 0.03)
    print(f"  Phantom: max={phantom.max():.4f}, nonzero={np.sum(phantom > 0)}")
    
    y0 = np.ones((Nx, Ny), dtype=np.complex128)
    y_K = bpm_forward(phantom, y0, H, k0, dz)
    print(f"  Forward: |y_K| range=[{np.abs(y_K).min():.4f}, {np.abs(y_K).max():.4f}]")
    
    grad, cost = bpm_gradient(phantom, y0, y_K, H, k0, dz)
    print(f"  Grad at true: cost={cost:.6e}, |grad|max={np.abs(grad).max():.6e}")
    
    x_zero = np.zeros_like(phantom)
    grad_zero, cost_zero = bpm_gradient(x_zero, y0, y_K, H, k0, dz)
    print(f"  Grad at zero: cost={cost_zero:.6e}, |grad|max={np.abs(grad_zero).max():.6e}")
    
    # Numerical gradient check
    print("  Numerical gradient check...")
    eps = 1e-6
    idx = (Nx // 2, Ny // 2, K // 2)
    x_plus = phantom.copy()
    x_plus[idx] += eps
    x_minus = phantom.copy()
    x_minus[idx] -= eps
    y_plus = bpm_forward(x_plus, y0, H, k0, dz)
    y_minus = bpm_forward(x_minus, y0, H, k0, dz)
    cost_plus = 0.5 * np.sum(np.abs(y_plus - y_K)**2)
    cost_minus = 0.5 * np.sum(np.abs(y_minus - y_K)**2)
    num_grad = (cost_plus - cost_minus) / (2 * eps)
    ana_grad = grad[idx]
    print(f"  Numerical: {num_grad:.6e}, Analytical: {ana_grad:.6e}")
    if abs(num_grad) > 1e-10:
        rel_err = abs(num_grad - ana_grad) / max(abs(num_grad), 1e-10)
        print(f"  Relative error: {rel_err:.6e}")
        if rel_err < 0.05:
            print("  Gradient check PASSED!")
        else:
            print("  WARNING: Gradient check has large error!")
    
    # Quick reconstruction
    print("\n  Quick reconstruction (30 iters, 1 view)...")
    measurements = [(y0, y_K)]
    x_recon = reconstruct(measurements, H, k0, dz, dx, dy, dz,
                         tau=0.001, x_bounds=(0, 0.1), L_tilde=1,
                         max_iter=30, Nx=Nx, Ny=Ny, K=K, verbose=True)
    snr = compute_snr(phantom, x_recon)
    print(f"  SNR after 30 iters: {snr:.2f} dB")
    print(f"  Recon range: [{x_recon.min():.4f}, {x_recon.max():.4f}]")
    print("  Toy test COMPLETE!\n")
    return True


if __name__ == "__main__":
    toy_test()
