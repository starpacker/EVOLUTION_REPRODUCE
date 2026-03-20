# us-beamform: Delay-and-Sum Ultrasound Beamforming

## Overview
A direct reconstruction algorithm that forms an ultrasound image by applying time-gain compensation, bandpass filtering, and summing sensor data across channels with dynamically calculated time-of-flight delays, followed by envelope detection and scan conversion.

## Algorithm
1. Load input data from input.npy (raw ultrasound RF channel data)
2. Apply Time-Gain Compensation (TGC) to compensate for attenuation
3. Apply bandpass filter (center frequency ~5MHz, bandwidth ~60%)
4. For each beam q and depth z, compute Delay-and-Sum:
   - I(q,z) = sum_r Data_preproc(q, r, tau(z,r))
   where tau(z,r) is the round-trip time delay for channel r
5. Envelope detection via Hilbert transform
6. Log compression: dB = 20*log10(envelope/max_val)
7. Scan conversion to Cartesian grid
8. Save reconstruction as reconstruction.npy

## Source Code
Available at: /data/yjh/us-beamform-linarray-master/
You may inspect the source for implementation details (transducer parameters, speed of sound, etc).

## Input/Output
- Input: /data/yjh/benchmark_dataset/us-beamform-linarray-master/input.npy
- Ground truth reference: /data/yjh/benchmark_dataset/us-beamform-linarray-master/gt_reference.npy (shape: 512x96)
- Ground truth output: /data/yjh/benchmark_dataset/us-beamform-linarray-master/gt_output.npy (shape: 4, scalar metrics)
- Expected output: reconstruction.npy
- Copy input.npy to your workspace before processing.

## Evaluation Metrics
- MSE (Mean Squared Error) -- lower is better
- PSNR (Peak Signal-to-Noise Ratio) -- higher is better
- SSIM (Structural Similarity) -- higher is better

## Key Dependencies
- numpy, scipy (signal processing, Hilbert transform, filtering)

## Required Output Files
- reproduce.py: Complete reproduction code
- reconstruction.npy: Beamformed image array
- results.json: {"MSE": val, "PSNR": val, "SSIM": val}
