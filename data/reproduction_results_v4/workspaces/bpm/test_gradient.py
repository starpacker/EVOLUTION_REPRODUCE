"""Test gradient direction and step size."""
import numpy as np
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

# Generate measurement
y0 = np.ones((Nx, Ny), dtype=np.complex128)
y_K = bpm_forward(phantom, y0, H, k0, dz)

# Compute gradient at zero
x0 = np.zeros_like(phantom)
grad, cost0 = bpm_gradient(x0, y0, y_K, H, k0, dz)
print(f"Cost at zero: {cost0:.6f}")
print(f"Gradient norm: {np.linalg.norm(grad):.6f}")
print(f"Gradient max: {grad.max():.6f}, min: {grad.min():.6f}")

# Line search: x = -alpha * grad
for alpha in [1e-6, 1e-5, 1e-4, 1e-3, 0.01, 0.1, 0.5, 1.0]:
    x_test = x0 - alpha * grad
    y_test = bpm_forward(x_test, y0, H, k0, dz)
    cost_test = 0.5 * np.sum(np.abs(y_test - y_K)**2)
    print(f"  alpha={alpha:.1e}: cost={cost_test:.6f}, delta_cost={cost_test - cost0:.6f}")

# Also test gradient at a point closer to solution
print("\nGradient check at non-trivial point (half of phantom):")
x_half = phantom * 0.5
grad_half, cost_half = bpm_gradient(x_half, y0, y_K, H, k0, dz)
print(f"Cost at half: {cost_half:.6f}")

# Numerical check at non-trivial point
eps = 1e-6
idx = (Nx//2, Ny//2, K//2)
x_p = x_half.copy(); x_p[idx] += eps
x_m = x_half.copy(); x_m[idx] -= eps
y_p = bpm_forward(x_p, y0, H, k0, dz)
y_m = bpm_forward(x_m, y0, H, k0, dz)
c_p = 0.5 * np.sum(np.abs(y_p - y_K)**2)
c_m = 0.5 * np.sum(np.abs(y_m - y_K)**2)
num = (c_p - c_m) / (2 * eps)
ana = grad_half[idx]
print(f"Numerical grad: {num:.6e}, Analytical grad: {ana:.6e}")
if abs(num) > 1e-10:
    print(f"Relative error: {abs(num - ana)/abs(num):.6e}")

# Check multiple random points
print("\nGradient check at 5 random points:")
rng = np.random.RandomState(123)
for _ in range(5):
    i, j, k = rng.randint(0, Nx), rng.randint(0, Ny), rng.randint(0, K)
    x_p = x_half.copy(); x_p[i,j,k] += eps
    x_m = x_half.copy(); x_m[i,j,k] -= eps
    y_p = bpm_forward(x_p, y0, H, k0, dz)
    y_m = bpm_forward(x_m, y0, H, k0, dz)
    c_p = 0.5 * np.sum(np.abs(y_p - y_K)**2)
    c_m = 0.5 * np.sum(np.abs(y_m - y_K)**2)
    num = (c_p - c_m) / (2 * eps)
    ana = grad_half[i,j,k]
    if abs(num) > 1e-10:
        rel = abs(num - ana)/abs(num)
        print(f"  [{i},{j},{k}] num={num:.6e}, ana={ana:.6e}, rel_err={rel:.6e}")
    else:
        print(f"  [{i},{j},{k}] num={num:.6e}, ana={ana:.6e} (num~0)")
