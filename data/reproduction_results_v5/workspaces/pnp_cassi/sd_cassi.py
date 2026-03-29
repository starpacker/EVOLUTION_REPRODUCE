"""
SD-CASSI Forward Model and Reconstruction Algorithms
Based on: "Deep plug-and-play priors for spectral snapshot compressive imaging"
"""

import numpy as np
from scipy.ndimage import gaussian_filter


def generate_binary_mask(H, W, seed=42):
    """Generate binary random mask {0,1} with equal probability."""
    rng = np.random.RandomState(seed)
    mask = rng.randint(0, 2, size=(H, W)).astype(np.float64)
    return mask


def sd_cassi_forward(X, mask):
    """
    SD-CASSI forward model.
    X: (H, W, B) spectral data cube, values in [0, 1]
    mask: (H, W) binary mask
    
    Returns:
        Y: (H, W+B-1) measurement
        masks_shifted: (H, W+B-1, B) the shifted masks
    """
    H, W, B = X.shape
    W_meas = W + B - 1

    Y = np.zeros((H, W_meas), dtype=np.float64)
    masks_shifted = np.zeros((H, W_meas, B), dtype=np.float64)

    for b in range(B):
        shifted_mask = np.zeros((H, W_meas), dtype=np.float64)
        shifted_mask[:, b:b+W] = mask
        masks_shifted[:, :, b] = shifted_mask

        modulated = np.zeros((H, W_meas), dtype=np.float64)
        modulated[:, b:b+W] = X[:, :, b] * mask
        Y += modulated

    return Y, masks_shifted


def sd_cassi_At(Y, masks_shifted):
    """Transpose operation A^T y."""
    H, W_meas, B = masks_shifted.shape
    W = W_meas - B + 1
    X_est = np.zeros((H, W, B), dtype=np.float64)
    for b in range(B):
        X_est[:, :, b] = (Y * masks_shifted[:, :, b])[:, b:b+W]
    return X_est


def sd_cassi_A(X, masks_shifted):
    """Forward operation A x."""
    H, W, B = X.shape
    W_meas = masks_shifted.shape[1]
    Y = np.zeros((H, W_meas), dtype=np.float64)
    for b in range(B):
        modulated = np.zeros((H, W_meas), dtype=np.float64)
        modulated[:, b:b+W] = X[:, :, b] * masks_shifted[:, b:b+W, b]
        Y += modulated
    return Y


def compute_diag_AAt(masks_shifted):
    """Compute Diag(AA^T) for image-plane coding."""
    return np.sum(masks_shifted ** 2, axis=2)


def tv_denoise_3d(X, weight, n_iter=20):
    """TV denoising for 3D spectral cube, band by band."""
    from skimage.restoration import denoise_tv_chambolle
    if weight <= 0:
        return X.copy()
    H, W, B = X.shape
    result = X.copy()
    for b in range(B):
        result[:, :, b] = denoise_tv_chambolle(X[:, :, b], weight=weight,
                                                 max_num_iter=n_iter)
    return result


def tv_denoise_2d(img, weight, n_iter=20):
    """TV denoising using skimage's Chambolle algorithm."""
    from skimage.restoration import denoise_tv_chambolle
    if weight <= 0:
        return img.copy()
    return denoise_tv_chambolle(img, weight=weight, max_num_iter=n_iter)


def gap_tv(Y, masks_shifted, n_iter=80, tv_weight=0.15, tv_iter=30, verbose=False):
    """
    GAP-TV: Generalized Alternating Projection with TV prior.
    x^{k+1} = z^k + A^T(y - A z^k) / Diag(AA^T)
    z^{k+1} = TV_denoise(x^{k+1})
    """
    H, W_meas, B = masks_shifted.shape
    W = W_meas - B + 1

    diag_AAt = compute_diag_AAt(masks_shifted)
    diag_AAt_safe = np.maximum(diag_AAt, 1e-10)

    # Initial estimate
    X = sd_cassi_At(Y / diag_AAt_safe, masks_shifted)
    X = np.clip(X, 0, 1)

    for k in range(n_iter):
        # Projection step
        residual = Y - sd_cassi_A(X, masks_shifted)
        X = X + sd_cassi_At(residual / diag_AAt_safe, masks_shifted)

        # TV denoising with decreasing weight
        tw = tv_weight * max(0.01, 1 - k / n_iter)
        X = tv_denoise_3d(X, tw, tv_iter)
        X = np.clip(X, 0, 1)

        if verbose and (k + 1) % 20 == 0:
            res_norm = np.linalg.norm(residual)
            print(f"  GAP-TV iter {k+1}: residual={res_norm:.4f}")

    return X


def twist_tv(Y, masks_shifted, n_iter=80, tv_weight=0.15, tv_iter=30, verbose=False):
    """
    TwIST with TV prior for SD-CASSI.
    """
    H, W_meas, B = masks_shifted.shape
    W = W_meas - B + 1

    diag_AAt = compute_diag_AAt(masks_shifted)
    diag_AAt_safe = np.maximum(diag_AAt, 1e-10)

    # Estimate eigenvalue bounds of A^T A
    xi_m = float(np.max(diag_AAt))
    xi_1 = 0.1
    xi_m_bar = max(1.0, xi_m)

    kappa = xi_1 / xi_m_bar
    gamma_hat = (1 - np.sqrt(kappa)) / (1 + np.sqrt(kappa))
    alpha = gamma_hat ** 2 + 1
    beta = 2 * alpha / (xi_1 + xi_m_bar)

    # Initialize
    z_prev = sd_cassi_At(Y / diag_AAt_safe, masks_shifted)
    z_prev = np.clip(z_prev, 0, 1)
    z_curr = z_prev.copy()

    for k in range(n_iter):
        # Gradient step with scaling
        residual = Y - sd_cassi_A(z_curr, masks_shifted)
        x_new = z_curr + (1.0 / xi_m_bar) * sd_cassi_At(residual, masks_shifted)

        # TV denoising
        tw = tv_weight * max(0.01, 1 - k / n_iter)
        theta = tv_denoise_3d(x_new, tw, tv_iter)
        theta = np.clip(theta, 0, 1)

        # TwIST correction step
        z_new = (1 - alpha) * z_prev + (alpha - beta) * z_curr + beta * theta
        z_new = np.clip(z_new, 0, 1)

        z_prev = z_curr
        z_curr = z_new

        if verbose and (k + 1) % 20 == 0:
            res_norm = np.linalg.norm(residual)
            print(f"  TwIST iter {k+1}: residual={res_norm:.4f}")

    return z_curr


def pnp_admm(Y, masks_shifted, denoiser, n_iter=50, rho=1.0,
             sigma_schedule=None, warm_start=None, verbose=False):
    """
    PnP-ADMM for SD-CASSI (image-plane coding).
    Eq. (13)-(15) from the paper.
    """
    H, W_meas, B = masks_shifted.shape
    W = W_meas - B + 1

    diag_AAt = compute_diag_AAt(masks_shifted)

    if sigma_schedule is None:
        sigma_schedule = [50/255]*20 + [25/255]*15 + [12/255]*10 + [6/255]*5

    n_iter = min(n_iter, len(sigma_schedule))

    if warm_start is not None:
        z = warm_start.copy()
    else:
        diag_safe = np.maximum(diag_AAt, 1e-10)
        z = sd_cassi_At(Y / diag_safe, masks_shifted)
        z = np.clip(z, 0, 1)

    u = np.zeros_like(z)

    for k in range(n_iter):
        # Step 1: Projection (Eq. 13)
        v = z - u
        residual = Y - sd_cassi_A(v, masks_shifted)
        x = v + sd_cassi_At(residual / (diag_AAt + rho), masks_shifted)

        # Step 2: Denoising (Eq. 14)
        sigma_k = sigma_schedule[k]
        z = denoiser(x + u, sigma_k)
        z = np.clip(z, 0, 1)

        # Step 3: Dual update (Eq. 15)
        u = u + (x - z)

        if verbose and (k + 1) % 10 == 0:
            res_norm = np.linalg.norm(Y - sd_cassi_A(z, masks_shifted))
            print(f"  PnP-ADMM iter {k+1}: sigma={sigma_k:.4f}, residual={res_norm:.4f}")

    return z


def compute_psnr(ref, rec):
    """Compute PSNR between reference and reconstruction."""
    from skimage.metrics import peak_signal_noise_ratio
    return peak_signal_noise_ratio(ref, rec, data_range=1.0)


def compute_ssim(ref, rec):
    """Compute average SSIM across spectral bands."""
    from skimage.metrics import structural_similarity
    if ref.ndim == 3:
        ssim_vals = []
        for b in range(ref.shape[2]):
            s = structural_similarity(ref[:, :, b], rec[:, :, b], data_range=1.0)
            ssim_vals.append(s)
        return np.mean(ssim_vals)
    else:
        return structural_similarity(ref, rec, data_range=1.0)
