# phasorpy: Phasor Analysis and Reconstruction of FLIM Data

## Overview
A deterministic signal processing pipeline that transforms time-resolved FLIM (Fluorescence Lifetime Imaging Microscopy) data into phasor space, applies spatial median filtering and intensity thresholding, and reconstructs the time-domain signal using harmonic modulation.

## Algorithm
1. Load input signal I(t) from input.npy (time-resolved FLIM data)
2. Forward DFT to compute phasor coordinates (g, s) at harmonics h:
   - X[k] = sum_n I[n] * exp(-j*2*pi*k*n/N)
   - g_h = Re(X[h]) / X[0],  s_h = Im(X[h]) / X[0]
   - M = X[0] (mean intensity / DC component)
3. Apply spatial median filter to phasor coordinates (kernel=3)
4. Apply intensity thresholding (mask low-intensity pixels)
5. Reconstruct signal via inverse phasor transform:
   - I_hat(t) = M_tilde * (1 + 2 * sum_h (g_tilde_h * cos(h*w*t) + s_tilde_h * sin(h*w*t)))
6. Save reconstruction as reconstruction.npy

## Source Code
Available at: /data/yjh/phasorpy-main/
You may inspect the source for implementation details, but write your own reproduce.py.

## Input/Output
- Input: /data/yjh/benchmark_dataset/phasorpy-main/input.npy
- Ground truth reference: /data/yjh/benchmark_dataset/phasorpy-main/gt_reference.npy
- Expected output: reconstruction.npy (same shape as gt_reference)
- Copy input.npy to your workspace before processing.

## Evaluation Metrics
- MSE (Mean Squared Error) -- lower is better
- PSNR (Peak Signal-to-Noise Ratio) -- higher is better
- SSIM (Structural Similarity) -- higher is better

## Key Dependencies
- numpy, scipy

## Required Output Files
- reproduce.py: Complete reproduction code
- reconstruction.npy: Reconstructed signal array
- results.json: {"MSE": val, "PSNR": val, "SSIM": val}
