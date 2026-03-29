#!/usr/bin/env python3
"""
Extract experiences from ALL Training Set trajectories (V3 + V5) and build
a clean Experience DB for the B2 (experience-enhanced) test runs.

Training Set (10 papers):
  Tier 1 (V3): pyeit✅, pat✅, insar✅, bpm❌, diff✅(V4)
  Tier 2 (V5): oopao✅, lenstronomy✅, pnp_cassi✅
  Tier 3 (V5): dpi❌, ptyrad✅

Usage:
  python scripts/extract_all_training_experiences.py [--fresh]
  
  --fresh: Wipe existing DB and rebuild from scratch
"""

import json
import os
import sys
import time
import uuid
import shutil
from pathlib import Path

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
sys.path.insert(0, str(PROJECT_ROOT))

from code.experience_db.trajectory_parser import process_trajectory
from code.experience_db.experience_db import ExperienceDB, Experience

TRAJ_DIR = Path("/data/yjh/openhands_results_v2/trajectories")

# ═══════════════════════════════════════════════════════════════
# Training Set: best trajectory per paper
# ═══════════════════════════════════════════════════════════════
TRAINING_TRAJECTORIES = {
    # ── Tier 1 (V3 runs, b2_ prefix = best V3 runs) ──
    "pyeit": {
        "file": "b2_pyeit_2026032-d61cb80a594c9fa.json",
        "domain": "biomedical_imaging",
        "success": True,
        "notes": "EIT: mesh+forward+sensitivity+reconstruction, all verified",
    },
    "pat": {
        "file": "b2_pat_20260326_-9fa7afd001b7f9b.json",
        "domain": "biomedical_imaging",
        "success": True,
        "notes": "PAT: backprojection+spectral unmixing+enhancement detection",
    },
    "insar": {
        "file": "b2_insar_2026032-22e0ff42b172091.json",
        "domain": "remote_sensing",
        "success": True,
        "notes": "InSAR: ADMM sparse phase unwrapping, 4 claims verified",
    },
    "bpm": {
        "file": "v4_bpm_20260328_-0f1d48beece8505.json",  # V4 run (larger, more attempts)
        "domain": "computational_optics",
        "success": False,
        "notes": "BPM: optical diffraction tomography, SNR too low, resolution issues",
    },
    "diff": {
        "file": "v4_diff_20260328-1957f7cfcb74a04.json",  # V4 run (successful)
        "domain": "computational_optics",
        "success": True,
        "notes": "Diff: diffraction simulation, 201x cost improvement reproduced",
    },
    # ── Tier 2 (V5 runs) ──
    "oopao": {
        "file": "v5_oopao_2026032-06d32fdbc3050da.json",
        "domain": "adaptive_optics",
        "success": True,
        "notes": "OOPAO: adaptive optics simulation, Strehl ratio 0.8159",
    },
    "lenstronomy": {
        "file": "v5_lenstronomy_2-ba80ae97c18012e.json",  # larger file = more complete run
        "domain": "gravitational_lensing",
        "success": True,
        "notes": "Lenstronomy: gravitational lens modeling, SIE+Sersic profiles",
    },
    "pnp_cassi": {
        "file": "v5_pnp_cassi_202-45212cf5786dcd3.json",  # larger = successful run
        "domain": "computational_imaging",
        "success": True,
        "notes": "PnP-CASSI: compressive spectral imaging, PnP-CNN 36.88dB",
    },
    # ── Tier 3 (V5 runs) ──
    "dpi": {
        "file": "v5_dpi_20260328_-49b899029b59f32.json",
        "domain": "computational_imaging",
        "success": False,
        "notes": "DPI: deep probabilistic imaging, timeout but partial results",
    },
    "ptyrad": {
        "file": "v5_ptyrad_202603-365902b236729a2.json",
        "domain": "ptychography",
        "success": True,
        "notes": "Ptyrad: ptychographic reconstruction, 6 experiments reproduced",
    },
}

# ═══════════════════════════════════════════════════════════════
# Meta-experiences: curated high-level lessons from Training Set
# ═══════════════════════════════════════════════════════════════
META_EXPERIENCES = [
    # ── From successful papers ──
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to reproduce paper with FEM/numerical methods from scratch",
            "task_context": "Reproducing computational physics paper involving mesh generation, forward problem solving, and inverse reconstruction",
            "environment": "Python with numpy, scipy, matplotlib",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Follow structured approach: (1) Create mesh with appropriate resolution, (2) Implement forward solver with FEM, (3) Compute Jacobian via adjoint method, (4) Implement reconstruction (BP/GN). Test each stage independently with toy examples before full-scale.",
            "code_implement": "# Toy-first: test with small mesh (e.g., 16 elements) before scaling to 512+\n# Verify forward solver produces reasonable ranges\n# Check Jacobian shape matches [n_measurements, n_elements]",
            "verification": "Compare mesh node/element counts, voltage ranges, and reconstruction localization error against paper values"
        },
        "rationale": "Structured decomposition into mesh→forward→sensitivity→inverse stages with toy-first testing prevents cascading errors. Verified on pyEIT paper.",
        "metadata": {"source_paper": "pyeit_training", "score": 8.5, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to implement ADMM-based optimization algorithm from paper equations",
            "task_context": "Reproducing optimization paper with ADMM/proximal gradient methods",
            "environment": "Python with numpy, scipy",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Implement ADMM step-by-step from paper equations: (1) Identify splitting variables, (2) Implement each sub-problem solver (often FFT-based), (3) Design multiple experiments covering all paper claims. Use DCT/FFT for efficient sub-problem solving.",
            "code_implement": "# ADMM template:\n# while not converged:\n#   x = argmin_x f(x) + rho/2 ||x - z + u||^2  (FFT/DCT based)\n#   z = prox_{g/rho}(x + u)  (proximal operator)\n#   u = u + x - z  (dual update)",
            "verification": "Check convergence in ~10 iterations, compare RMSE improvement ratio, verify reliability across multiple random seeds"
        },
        "rationale": "ADMM decomposition into FFT-solvable subproblems is the standard approach for image reconstruction. Verified on InSAR phase unwrapping.",
        "metadata": {"source_paper": "insar_training", "score": 9.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to reproduce software toolkit paper with multiple algorithms",
            "task_context": "Reproducing a software package paper that demonstrates multiple algorithms",
            "environment": "Python with numpy, scipy, matplotlib",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Create synthetic phantom data matching paper's test setup. Implement each algorithm as separate function. Use ground truth comparison for validation. Focus on: (1) reconstruction quality (RMSE, SSIM), (2) spectral analysis accuracy, (3) detection sensitivity.",
            "code_implement": "# Create phantom with known ground truth\n# For each algorithm: implement, run on phantom, compare to ground truth\n# Save all metrics to results.json",
            "verification": "Estimation error < threshold, structure detection all True, RMSE reasonable"
        },
        "rationale": "Synthetic phantom with known ground truth enables precise validation of each algorithm independently. Verified on PATATO paper.",
        "metadata": {"source_paper": "pat_training", "score": 7.5, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "adaptive_optics",
        "condition": {
            "error_or_symptom": "Need to reproduce adaptive optics simulation with wavefront correction",
            "task_context": "Reproducing AO paper with atmosphere simulation, wavefront sensing, and deformable mirror correction",
            "environment": "Python with numpy, scipy, OOPAO or similar AO toolkit",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Use the paper's toolkit directly if available. Set up atmosphere model (Kolmogorov turbulence), telescope, wavefront sensor (Shack-Hartmann), and deformable mirror. Run closed-loop correction and measure Strehl ratio. Key: match paper's r0, wavelength, and telescope diameter exactly.",
            "code_implement": "# 1. Create atmosphere with correct r0, L0\n# 2. Set up telescope with correct D, obstruction\n# 3. Configure WFS (nSubap, wavelength)\n# 4. Run closed-loop: sense → reconstruct → correct\n# 5. Measure Strehl = max(PSF_corrected) / max(PSF_diffraction)",
            "verification": "Strehl ratio within 10% of paper value, residual wavefront RMS decreasing over iterations"
        },
        "rationale": "AO simulations are sensitive to parameter matching. Using the paper's own toolkit ensures consistent physics. Verified on OOPAO paper (Strehl 0.8159).",
        "metadata": {"source_paper": "oopao_training", "score": 8.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "gravitational_lensing",
        "condition": {
            "error_or_symptom": "Need to reproduce gravitational lensing simulation or modeling",
            "task_context": "Reproducing paper on gravitational lens modeling with mass profiles and source reconstruction",
            "environment": "Python with lenstronomy, astropy, numpy",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Use lenstronomy library for lens modeling. Define lens model (SIE/NFW), source model (Sersic), and PSF. Generate mock data with known parameters, then fit using lenstronomy's fitting module. Compare recovered parameters to input.",
            "code_implement": "# 1. Define lens model: SIE with theta_E, e1, e2, center\n# 2. Define source: Sersic with R_sersic, n_sersic, magnitude\n# 3. Generate mock image with noise\n# 4. Fit with PSO + MCMC\n# 5. Compare recovered vs input parameters",
            "verification": "Parameter recovery within 5% for Einstein radius, source position, ellipticity"
        },
        "rationale": "Lenstronomy provides validated implementations of lens models. Mock data with known truth enables precise parameter recovery testing. Verified on lenstronomy paper.",
        "metadata": {"source_paper": "lenstronomy_training", "score": 8.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "computational_imaging",
        "condition": {
            "error_or_symptom": "Need to reproduce compressive sensing / plug-and-play reconstruction",
            "task_context": "Reproducing paper on PnP (Plug-and-Play) algorithms for image reconstruction with learned denoisers",
            "environment": "Python with numpy, scipy, torch (for CNN denoiser)",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Implement ADMM/HQS framework with denoiser as proximal operator. For PnP-CNN: use pre-trained DnCNN or similar. For PnP-BM3D: use BM3D library. Key: tune regularization parameter (lambda/sigma) carefully. Start with paper's suggested values.",
            "code_implement": "# PnP-ADMM:\n# while not converged:\n#   x = (H^T H + rho I)^{-1} (H^T y + rho(z - u))  # data fidelity\n#   z = Denoiser(x + u, sigma=sqrt(lambda/rho))  # PnP step\n#   u = u + x - z  # dual update",
            "verification": "PSNR within 1-2dB of paper values, visual quality comparable, convergence in <50 iterations"
        },
        "rationale": "PnP algorithms replace proximal operators with learned denoisers. The key is matching the denoiser's noise level parameter to the regularization strength. Verified on PnP-CASSI (36.88dB).",
        "metadata": {"source_paper": "pnp_cassi_training", "score": 8.5, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "ptychography",
        "condition": {
            "error_or_symptom": "Need to reproduce ptychographic reconstruction from diffraction patterns",
            "task_context": "Reproducing paper on ptychography with iterative phase retrieval algorithms",
            "environment": "Python with numpy, scipy, or specialized ptychography toolkit",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Use the paper's toolkit if available (e.g., ptyrad, PtyLab). Set up probe, object, and scanning positions. Generate synthetic diffraction patterns, then reconstruct using ePIE/rPIE/gradient descent. Key: match overlap ratio (>60%), probe size, and scanning grid.",
            "code_implement": "# 1. Define probe (focused beam) and object (complex transmission)\n# 2. Generate scanning positions with sufficient overlap\n# 3. Simulate diffraction patterns: I = |FFT(probe * object_patch)|^2\n# 4. Reconstruct with ePIE: update object and probe alternately\n# 5. Measure reconstruction error (SSIM, phase RMSE)",
            "verification": "Reconstruction SSIM > 0.9, phase error < 0.1 rad, convergence within 100 iterations"
        },
        "rationale": "Ptychography requires sufficient overlap between scanning positions for unique reconstruction. Using the paper's toolkit ensures consistent forward model. Verified on ptyrad paper (6 experiments).",
        "metadata": {"source_paper": "ptyrad_training", "score": 8.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "computational_optics",
        "condition": {
            "error_or_symptom": "Need to reproduce optical diffraction simulation with significant speedup claims",
            "task_context": "Reproducing paper comparing different diffraction simulation methods (BPM, angular spectrum, Rayleigh-Sommerfeld)",
            "environment": "Python with numpy, scipy",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Implement both the baseline method and the proposed method. Use identical optical parameters (wavelength, aperture, propagation distance). Measure both accuracy (field comparison) and timing. For speedup claims: use timeit with multiple runs, extrapolate to paper's grid size if needed.",
            "code_implement": "# 1. Define optical setup: wavelength, aperture, grid size\n# 2. Implement baseline (e.g., full BPM) and proposed method\n# 3. Compare fields: correlation, MSE, phase error\n# 4. Time both methods: timeit.timeit(method, number=10)\n# 5. Compute speedup ratio",
            "verification": "Field correlation > 0.99, speedup ratio within order of magnitude of paper claim"
        },
        "rationale": "Diffraction simulations are deterministic given same parameters. Speedup claims need careful timing methodology. Verified on Diff paper (201x improvement).",
        "metadata": {"source_paper": "diff_training", "score": 8.0, "success_count": 1}
    },
    # ── Negative experiences (from failures) ──
    {
        "type": "negative",
        "domain_hint": "computational_optics",
        "condition": {
            "error_or_symptom": "Optical tomography reconstruction produces very low SNR compared to paper",
            "task_context": "Implementing beam propagation method for optical diffraction tomography with TV regularization",
            "environment": "Python with numpy, scipy",
            "failed_attempts_summary": [
                "Used coarse grid (64x64x32) instead of paper's fine grid (256x256x128)",
                "Agent got stuck in tool call loop"
            ]
        },
        "action": {
            "solution": "CRITICAL: Use grid resolution matching the paper. Low resolution causes severe aliasing in BPM forward model, making reconstruction impossible. Also: write code to files (cat > file.py << 'PYEOF') instead of inline execution to avoid tool call format errors.",
            "code_implement": "# MUST match paper resolution for BPM:\n# Nx, Ny, Nz = 256, 256, 128\n# voxel_size = 144e-9  # meters\n# Use file-based execution for complex code",
            "verification": "SNR should be > 20 dB for standard test objects"
        },
        "rationale": "BPM forward model requires sufficient spatial sampling to accurately propagate wavefronts. Coarser voxels cause phase wrapping artifacts that destroy reconstruction quality.",
        "metadata": {"source_paper": "bpm_training", "score": 6.0, "success_count": 0}
    },
    {
        "type": "negative",
        "domain_hint": "computational_imaging",
        "condition": {
            "error_or_symptom": "Deep learning based imaging reconstruction times out or runs out of memory",
            "task_context": "Reproducing paper using normalizing flows, VAEs, or other deep generative models for image reconstruction",
            "environment": "Python with PyTorch, heavy GPU computation",
            "failed_attempts_summary": [
                "Training took too long (>5400s timeout)",
                "Model too large for available GPU memory"
            ]
        },
        "action": {
            "solution": "For deep learning papers: (1) Reduce model size (fewer layers/channels) for feasibility check, (2) Use smaller dataset/image size for initial validation, (3) Set aggressive early stopping, (4) If full training infeasible, validate architecture correctness with toy data and extrapolate.",
            "code_implement": "# Feasibility-first approach:\n# 1. Reduce image size: 64x64 instead of 256x256\n# 2. Reduce model: 2 layers instead of 8\n# 3. Train for 10 epochs, check loss decreasing\n# 4. If architecture works, report extrapolated results",
            "verification": "Loss decreasing, gradients not exploding, architecture matches paper description"
        },
        "rationale": "Deep learning reproductions often hit compute limits. Validating architecture correctness at small scale is more valuable than failing at full scale.",
        "metadata": {"source_paper": "dpi_training", "score": 5.0, "success_count": 0}
    },
    # ── General workflow experiences ──
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to design comprehensive experiments to validate paper claims",
            "task_context": "Paper makes multiple claims that need independent verification",
            "environment": "Python",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Design one experiment per paper claim: (1) Comparison experiment for superiority claims, (2) Convergence curve for speed claims, (3) Multi-seed reliability test, (4) Scaling test for efficiency claims. Use 20+ random seeds for reliability.",
            "code_implement": "# For each claim, design targeted experiment:\n# Claim 1 (superiority): run both methods, compare metric\n# Claim 2 (convergence): track metric per iteration\n# Claim 3 (reliability): 20 random seeds, count successes\n# Claim 4 (efficiency): time at smaller scale, extrapolate",
            "verification": "Each claim has quantitative evidence (ratio, iteration count, success rate, timing)"
        },
        "rationale": "Systematic claim-by-claim verification ensures comprehensive reproduction. Verified on InSAR (4/4 claims) and ptyrad (6 experiments).",
        "metadata": {"source_paper": "general_training", "score": 9.0, "success_count": 2}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Paper provides a software library/toolkit that should be used",
            "task_context": "Reproducing paper where the authors provide their own code/library",
            "environment": "Python",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "ALWAYS prefer using the paper's own library when available. Install it first (pip install or clone repo). Read the library's examples/tutorials. Adapt examples to match paper's specific experiments. This is faster and more accurate than reimplementing from scratch.",
            "code_implement": "# 1. pip install <library> or git clone <repo>\n# 2. Read library docs/examples\n# 3. Adapt example to paper's parameters\n# 4. Run and compare results",
            "verification": "Results match paper within expected tolerance"
        },
        "rationale": "Using the paper's own library eliminates implementation bugs and ensures consistent physics/math. Verified on oopao, lenstronomy, ptyrad, pyeit papers.",
        "metadata": {"source_paper": "general_training", "score": 9.0, "success_count": 4}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to save results in structured format for evaluation",
            "task_context": "Completing paper reproduction and saving results",
            "environment": "Python",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Always save results to results.json in the workspace root with: (1) paper_id, (2) claims dict mapping claim names to {reproduced: bool, evidence: str, metric_name: str, metric_value: float, paper_value: float}, (3) figures saved as PNG files, (4) summary string.",
            "code_implement": "results = {\n  'paper_id': 'paper_name',\n  'claims': {\n    'claim_1': {'reproduced': True, 'evidence': '...', 'metric_value': 0.95, 'paper_value': 0.93},\n  },\n  'summary': 'Successfully reproduced X/Y claims'\n}\njson.dump(results, open('results.json','w'), indent=2)",
            "verification": "results.json exists, contains all claims, metrics are numeric"
        },
        "rationale": "Structured results enable automated evaluation. The results.json format is expected by the evaluation pipeline.",
        "metadata": {"source_paper": "general_training", "score": 7.0, "success_count": 8}
    },
]


def extract_from_trajectories(db: ExperienceDB) -> int:
    """Extract experiences from all training trajectory files via LLM."""
    total = 0
    for paper_id, info in TRAINING_TRAJECTORIES.items():
        traj_path = TRAJ_DIR / info["file"]
        if not traj_path.exists():
            print(f"⚠️  Trajectory not found for {paper_id}: {traj_path}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing trajectory: {paper_id} ({'✅' if info['success'] else '❌'})")
        print(f"  File: {info['file']} ({traj_path.stat().st_size/1024:.0f} KB)")
        print(f"{'='*60}")

        try:
            raw_experiences = process_trajectory(
                filepath=str(traj_path),
                project_name=paper_id,
                domain=info["domain"]
            )
        except Exception as e:
            print(f"  ❌ Trajectory parsing failed: {e}")
            import traceback; traceback.print_exc()
            continue

        if not raw_experiences:
            print(f"  No experiences extracted from trajectory")
            continue

        for exp_data in raw_experiences:
            try:
                exp = Experience(
                    id=f"exp_train_{paper_id}_{time.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                    type=exp_data.get("type", "positive"),
                    domain_hint=exp_data.get("domain_hint", info["domain"]),
                    condition=exp_data.get("condition", {}),
                    action=exp_data.get("action", {}),
                    rationale=exp_data.get("rationale", ""),
                    metadata={
                        "source_paper": f"{paper_id}_training",
                        "creation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "score": 7.5 if info["success"] else 4.0,
                        "call_count": 0,
                        "success_count": 1 if info["success"] else 0,
                    },
                    status="verified" if info["success"] else "hypothesis",
                )
                eid = db.add(exp)
                total += 1
                symptom = exp.condition.get("error_or_symptom", "")[:80]
                print(f"  ✅ Stored: {eid} — {symptom}")
            except Exception as e:
                print(f"  ❌ Failed to store: {e}")

    return total


def add_meta_experiences(db: ExperienceDB) -> int:
    """Add curated meta-experiences from Training Set analysis."""
    total = 0
    for exp_data in META_EXPERIENCES:
        try:
            meta = exp_data.get("metadata", {})
            exp = Experience(
                id=f"exp_meta_train_{uuid.uuid4().hex[:8]}",
                type=exp_data["type"],
                domain_hint=exp_data["domain_hint"],
                condition=exp_data["condition"],
                action=exp_data["action"],
                rationale=exp_data["rationale"],
                metadata={
                    "source_paper": meta.get("source_paper", "training_analysis"),
                    "creation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "score": meta.get("score", 5.0),
                    "call_count": 0,
                    "success_count": meta.get("success_count", 0),
                },
                status="verified",
            )
            eid = db.add(exp)
            total += 1
            symptom = exp.condition.get("error_or_symptom", "")[:80]
            print(f"  ✅ Meta: {eid} — {symptom}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

    return total


def main():
    fresh = "--fresh" in sys.argv

    print("=" * 60)
    print("  Training Set Experience Extraction Pipeline")
    print(f"  Mode: {'FRESH (wipe & rebuild)' if fresh else 'APPEND'}")
    print("=" * 60)

    db_dir = str(PROJECT_ROOT / "data" / "experience_db")

    if fresh:
        # Backup existing DB
        backup_dir = str(PROJECT_ROOT / "data" / "experience_db_backup")
        if os.path.exists(db_dir):
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(db_dir, backup_dir)
            print(f"  Backed up existing DB to {backup_dir}")
            # Remove old DB files
            for f in ["experience_meta.db", "vectors.json"]:
                fp = os.path.join(db_dir, f)
                if os.path.exists(fp):
                    os.remove(fp)
            print("  Wiped existing DB")

    db = ExperienceDB(db_dir)
    print(f"\nExisting DB stats: {db.stats()}")

    # Step 1: Extract from trajectories (LLM-based)
    print(f"\n{'='*60}")
    print("Step 1: Extracting from Training Set trajectories...")
    print(f"  Papers: {list(TRAINING_TRAJECTORIES.keys())}")
    print(f"{'='*60}")
    traj_count = extract_from_trajectories(db)
    print(f"\n  Extracted {traj_count} experiences from trajectories")

    # Step 2: Add meta-experiences
    print(f"\n{'='*60}")
    print("Step 2: Adding curated meta-experiences...")
    print(f"{'='*60}")
    meta_count = add_meta_experiences(db)
    print(f"\n  Added {meta_count} meta-experiences")

    # Summary
    final_stats = db.stats()
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Trajectory experiences: {traj_count}")
    print(f"  Meta-experiences: {meta_count}")
    print(f"  Total new: {traj_count + meta_count}")
    print(f"  DB stats: {final_stats}")
    print(f"\n  DB location: {db_dir}")
    print(f"  Ready for B2 test runs!")


if __name__ == "__main__":
    main()
