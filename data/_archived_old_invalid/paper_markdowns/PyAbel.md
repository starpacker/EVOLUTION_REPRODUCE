# PyAbel: A Python Tool for Forward and Inverse Abel Transforms

## Abstract
PyAbel is a Python package for computing forward and inverse Abel transforms. The Abel transform is encountered in many areas of physics, chemistry, and engineering. PyAbel implements several transform methods including the BASEX method, Hansen-Law method, and direct integration, along with tools for centering, symmetrizing, and analyzing transformed images.

## 1. Introduction
The Abel transform arises when a 3D cylindrically-symmetric object is projected onto a 2D plane (e.g., in photoelectron/photoion imaging experiments). The inverse Abel transform recovers the original 3D distribution from the 2D projection.

## 2. Methods
PyAbel implements the following inverse Abel transform methods:
- **BASEX** (BAsis Set EXpansion): Expands the projection in a basis of known Abel transforms
- **Hansen-Law**: Recursive algorithm based on the work of Hansen & Law (1985)
- **Direct integration**: Numerical integration of the Abel integral
- **Three-point**: A three-point Abel deconvolution method
- **Two-point**: A two-point deconvolution method
- **OnionPeeling**: Onion-peeling (back-projection) method
- **LinBASEX**: Linearized BASEX method

## 3. Key Implementation Details
- Input: 2D image (numpy array), assumed to be cylindrically symmetric
- Image centering via center_image() function
- Angular integration via angular_integration() for extracting radial distributions
- Speed distribution from radial distribution

## 4. Experimental Validation
The package is validated using:
1. **Analytical test functions**: Known functions with analytical Abel transforms (e.g., Gaussian peaks)
2. **Benchmark timing**: Comparing execution speed of different methods
3. **Accuracy metrics**: RMS error between computed and analytical transforms

### Key Results:
- For a sample image of size 501x501:
  - BASEX method: RMS error ≈ 0.002, execution time ≈ 0.15s
  - Hansen-Law: RMS error ≈ 0.005, execution time ≈ 0.8s
  - Direct method: RMS error ≈ 0.01, execution time ≈ 2.5s
- All methods correctly recover the known analytical inverse for Gaussian test functions
- The package handles images up to 2001x2001 within reasonable time (<30s for BASEX)

## 5. Dependencies
- numpy
- scipy
- matplotlib (for visualization)

## 6. Metrics to Reproduce
| Metric | Method | Value | Direction |
|--------|--------|-------|-----------|
| RMS Error | BASEX | 0.002 | ↓ |
| RMS Error | Hansen-Law | 0.005 | ↓ |
| Execution Time (501x501) | BASEX | 0.15s | ↓ |
