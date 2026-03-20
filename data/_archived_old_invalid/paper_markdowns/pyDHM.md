# pyDHM: 4-Step Phase-Shifting Digital Holography Reconstruction

## Overview
A deterministic reconstruction algorithm that recovers the complex optical field from four phase-shifted intensity holograms using a linear combination formula followed by angular spectrum back-propagation.

## Algorithm
1. Load input data from input.npy (contains 4 phase-shifted holograms with shifts 0, pi/2, pi, 3pi/2)
2. Recover complex field at z=0 using 4-step formula:
   - U(x,y) = (I_0 - I_2) + j*(I_1 - I_3)
3. Angular Spectrum Back-Propagation to focus plane at distance z:
   - FFT of U(x,y)
   - Multiply by transfer function H(fx,fy) = exp(j*2*pi*z/lambda * sqrt(1 - (lambda*fx)^2 - (lambda*fy)^2))
   - IFFT to get U_rec(x,y,z)
4. Extract amplitude: A = |U_rec|, clip to [0,1]
5. Extract phase: phi = angle(U_rec)
6. Save reconstruction as reconstruction.npy

## Source Code
Available at: /data/yjh/pyDHM-master/
You may inspect the source for implementation details and parameters (wavelength, pixel size, propagation distance).

## Input/Output
- Input: /data/yjh/benchmark_dataset/pyDHM-master/input.npy
- Ground truth reference: /data/yjh/benchmark_dataset/pyDHM-master/gt_reference.npy
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
