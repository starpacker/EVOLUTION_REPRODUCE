# CT-and-MR-Perfusion: Perfusion Parameter Estimation via Truncated SVD Deconvolution

## Overview
Transforms dynamic contrast-enhanced medical images (CTP/MRP) into perfusion parameter maps (CBF, CBV, MTT, Tmax) using Truncated SVD Deconvolution.

## Algorithm
1. Load NIfTI medical image time-series (4D: T x Z x Y x X)
2. Downsample spatially/temporally if needed
3. Gaussian smoothing (sigma=1.0) per frame
4. Generate brain mask (bone threshold=300 HU + fast marching)
5. Detect bolus arrival, compute baseline S0
6. Convert signal to concentration:
   - CTP: C(t) = S(t) - S0
   - MRP: C(t) = -(1/TE) * ln(S(t)/(S0+eps))
7. Compute TTP map = argmax_t(C(t))
8. Determine AIF via percentile search + gamma-variate fitting
9. Build Toeplitz convolution matrix from AIF
10. Truncated SVD deconvolution (threshold=0.1*max(sigma))
11. Compute: CBF = max_t(R(t)) * 60 * 100 * 0.73 / 1.05
             CBV = AUC_total / AUC_aif * 100 * 0.73 / 1.05
             MTT = CBV / CBF * 60
             Tmax = time_index[argmax_t(R(t))]

## Source Code
Available at: /data/yjh/CT-and-MR-Perfusion-Tool-main/
You may inspect the source for implementation details.

## Input/Output
- Benchmark data: /data/yjh/benchmark_dataset/CT-and-MR-Perfusion-Tool-main/
  (Note: This task may have NIfTI input files - check the benchmark directory)
- Output: Perfusion maps (CBF, CBV, MTT, Tmax, TTP)

## Evaluation Metrics
- RMSE (Root Mean Square Error) -- lower is better
- MAE (Mean Absolute Error) -- lower is better
- SSIM (Structural Similarity Index) -- higher is better

## Key Dependencies
- numpy, scipy (SVD, curve_fit, gaussian_filter, toeplitz)
- SimpleITK or nibabel (NIfTI I/O)
- scikit-image (morphology, SSIM)

## Key Constants
- Blood density rho = 1.05 g/mL
- Hematocrit factor = 0.73
- SVD truncation threshold = 0.1
- Gaussian smoothing sigma = 1.0

## Required Output Files
- reproduce.py: Complete reproduction code
- results.json: {"RMSE_CBF": val, "RMSE_CBV": val, "SSIM_CBF": val, ...}
