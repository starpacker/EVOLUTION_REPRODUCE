#!/usr/bin/env python3
"""
Extract experiences from V3 Tier 1 trajectories and seed the Experience DB.

This script:
1. Parses V3 trajectory files (from successful + failed runs)
2. Extracts structured experiences via LLM
3. Also creates "meta-experiences" from the V3 results analysis
4. Stores everything in the Experience DB

Usage:
  python scripts/extract_v3_experiences.py
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
sys.path.insert(0, str(PROJECT_ROOT))

from code.experience_db.trajectory_parser import process_trajectory
from code.experience_db.experience_db import ExperienceDB, Experience

# V3 trajectory files
TRAJ_DIR = Path("/data/yjh/openhands_results_v2/trajectories")
V3_TRAJECTORIES = {
    "pyeit": {
        "file": "b2_pyeit_2026032-d61cb80a594c9fa.json",
        "domain": "biomedical_imaging",
        "success": True,
        "notes": "EIT: mesh+forward+sensitivity+reconstruction, all verified"
    },
    "pat": {
        "file": "b2_pat_20260326_-9fa7afd001b7f9b.json",
        "domain": "biomedical_imaging",
        "success": True,
        "notes": "PAT: backprojection+spectral unmixing+enhancement detection"
    },
    "insar": {
        "file": "b2_insar_2026032-22e0ff42b172091.json",
        "domain": "remote_sensing",
        "success": True,
        "notes": "InSAR: ADMM sparse phase unwrapping, 4 claims verified"
    },
    "bpm": {
        "file": "b2_bpm_20260326_-079544e3f3bad5e.json",
        "domain": "computational_optics",
        "success": False,
        "notes": "BPM: tool call loop, SNR=-24dB vs paper 22.74dB, resolution too low"
    },
    "diff": {
        "file": "b2_diff_20260327-ecfc5684d1c3be1.json",
        "domain": "computational_optics",
        "success": False,
        "notes": "Diff: BadRequestError, tool call format errors, never completed"
    },
}

# Meta-experiences derived from V3 analysis (not from trajectory parsing)
META_EXPERIENCES = [
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
            "code_implement": "# Toy-first: test with small mesh (e.g., 16 elements) before scaling to 512+\n# Verify forward solver produces reasonable voltage ranges\n# Check Jacobian shape matches [n_measurements, n_elements]",
            "verification": "Compare mesh node/element counts, voltage ranges, and reconstruction localization error against paper values"
        },
        "rationale": "Structured decomposition into mesh→forward→sensitivity→inverse stages with toy-first testing prevents cascading errors. Verified on pyEIT paper reproduction.",
        "metadata": {"source_paper": "pyeit_v3", "score": 8.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to implement ADMM-based optimization algorithm from paper equations",
            "task_context": "Reproducing optimization paper with ADMM/proximal gradient methods, need to implement from mathematical formulation",
            "environment": "Python with numpy, scipy",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Implement ADMM step-by-step from paper equations: (1) Identify the splitting variables, (2) Implement each sub-problem solver (often FFT-based for image problems), (3) Design multiple experiments covering all paper claims. Use DCT/FFT for efficient sub-problem solving.",
            "code_implement": "# ADMM template:\n# while not converged:\n#   x = argmin_x f(x) + rho/2 ||x - z + u||^2  (often FFT/DCT based)\n#   z = prox_{g/rho}(x + u)  (proximal operator)\n#   u = u + x - z  (dual update)",
            "verification": "Check convergence in ~10 iterations, compare RMSE improvement ratio, verify reliability across multiple random seeds"
        },
        "rationale": "ADMM decomposition into FFT-solvable subproblems is the standard approach for image reconstruction. Verified on InSAR phase unwrapping with 1.75x improvement over L2.",
        "metadata": {"source_paper": "insar_v3", "score": 9.0, "success_count": 1}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to reproduce software toolkit paper (JOSS-style) with multiple algorithms",
            "task_context": "Reproducing a software package paper that demonstrates multiple algorithms (reconstruction, spectral analysis, enhancement detection)",
            "environment": "Python with numpy, scipy, matplotlib",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Create synthetic phantom data that matches paper's test setup. Implement each algorithm as a separate function. Use ground truth comparison for validation. Focus on: (1) reconstruction quality (RMSE, SSIM), (2) spectral unmixing accuracy, (3) enhancement detection sensitivity.",
            "code_implement": "# Create phantom with known ground truth\n# phantom = create_phantom(size, structures=[tumor1, tumor2, spine])\n# For each algorithm: implement, run on phantom, compare to ground truth\n# Save all metrics to results.json",
            "verification": "sO2 estimation error < 0.003, structure detection all True, RMSE reasonable"
        },
        "rationale": "Synthetic phantom with known ground truth enables precise validation of each algorithm independently. Verified on PATATO paper.",
        "metadata": {"source_paper": "pat_v3", "score": 7.0, "success_count": 1}
    },
    {
        "type": "negative",
        "domain_hint": "computational_optics",
        "condition": {
            "error_or_symptom": "BPM optical tomography reconstruction produces very low SNR (-24dB vs paper's 22.74dB)",
            "task_context": "Implementing beam propagation method for optical diffraction tomography with TV regularization",
            "environment": "Python with numpy, scipy",
            "failed_attempts_summary": [
                "Used 64x64x32 grid instead of paper's 256x256x128 — 4x coarser voxels",
                "Agent got stuck in tool call loop (execute_ipython_cell missing 'code' param)"
            ]
        },
        "action": {
            "solution": "CRITICAL: Use grid resolution matching the paper (256x256x128 at 144nm voxels). Low resolution (64x64x32 at 576nm) causes severe aliasing in BPM forward model, making reconstruction impossible. Also: use bash file writing (cat > file.py << 'PYEOF') instead of IPython cells to avoid tool call format errors.",
            "code_implement": "# MUST match paper resolution:\n# Nx, Ny, Nz = 256, 256, 128\n# voxel_size = 144e-9  # meters\n# Use cat > file.py << 'PYEOF' for file creation, NOT execute_ipython_cell",
            "verification": "SNR should be > 20 dB for 10um bead reconstruction"
        },
        "rationale": "BPM forward model requires sufficient spatial sampling to accurately propagate wavefronts. 4x coarser voxels cause phase wrapping artifacts that destroy reconstruction quality.",
        "metadata": {"source_paper": "bpm_v3", "score": 5.0, "success_count": 0}
    },
    {
        "type": "negative",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Agent enters infinite loop of tool call format errors (Missing required parameters)",
            "task_context": "Using execute_ipython_cell or execute_bash tools in OpenHands agent",
            "environment": "OpenHands CodeActAgent with Claude LLM",
            "failed_attempts_summary": [
                "execute_ipython_cell called without 'code' parameter repeatedly",
                "execute_bash called without 'command' parameter repeatedly"
            ]
        },
        "action": {
            "solution": "ALWAYS use bash file writing pattern instead of IPython cells: cat > filename.py << 'PYEOF' ... PYEOF && python filename.py. This avoids the tool call format error that causes infinite loops. Never use execute_ipython_cell for important code.",
            "code_implement": "# SAFE pattern:\ncat > script.py << 'PYEOF'\nimport numpy as np\n# ... your code ...\nPYEOF\npython script.py",
            "verification": "Code executes without 'Missing required parameters' errors"
        },
        "rationale": "LLM sometimes generates malformed tool calls for execute_ipython_cell. The bash heredoc pattern is more robust and avoids this failure mode entirely.",
        "metadata": {"source_paper": "bpm_v3_failure", "score": 7.0, "success_count": 0}
    },
    {
        "type": "positive",
        "domain_hint": "general_reproduction",
        "condition": {
            "error_or_symptom": "Need to design comprehensive experiments to validate paper claims",
            "task_context": "Paper makes multiple claims (algorithm superiority, convergence speed, reliability, scalability) that need independent verification",
            "environment": "Python",
            "failed_attempts_summary": []
        },
        "action": {
            "solution": "Design one experiment per paper claim: (1) Comparison experiment for superiority claims, (2) Convergence curve for speed claims, (3) Multi-seed reliability test, (4) Scaling test for efficiency claims. Use 20+ random seeds for reliability. Extrapolate timing to paper's scale.",
            "code_implement": "# For each claim, design targeted experiment:\n# Claim 1 (superiority): run both methods, compare RMSE\n# Claim 2 (convergence): track metric per iteration\n# Claim 3 (reliability): 20 random seeds, count successes\n# Claim 4 (efficiency): time at smaller scale, extrapolate",
            "verification": "Each claim has quantitative evidence (ratio, iteration count, success rate, timing)"
        },
        "rationale": "Systematic claim-by-claim verification ensures comprehensive reproduction. The InSAR paper achieved 4/4 claims verified using this approach.",
        "metadata": {"source_paper": "insar_v3", "score": 9.0, "success_count": 1}
    },
]


def extract_from_trajectories(db: ExperienceDB) -> int:
    """Extract experiences from V3 trajectory files."""
    total = 0
    for paper_id, info in V3_TRAJECTORIES.items():
        traj_path = TRAJ_DIR / info["file"]
        if not traj_path.exists():
            print(f"⚠️  Trajectory not found for {paper_id}: {traj_path}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing trajectory: {paper_id} ({'✅' if info['success'] else '❌'})")
        print(f"{'='*60}")

        try:
            raw_experiences = process_trajectory(
                filepath=str(traj_path),
                project_name=paper_id,
                domain=info["domain"]
            )
        except Exception as e:
            print(f"  ❌ Trajectory parsing failed: {e}")
            continue

        if not raw_experiences:
            print(f"  No experiences extracted from trajectory")
            continue

        for exp_data in raw_experiences:
            try:
                exp = Experience(
                    id=f"exp_v3_{paper_id}_{time.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                    type=exp_data.get("type", "positive"),
                    domain_hint=exp_data.get("domain_hint", info["domain"]),
                    condition=exp_data.get("condition", {}),
                    action=exp_data.get("action", {}),
                    rationale=exp_data.get("rationale", ""),
                    metadata={
                        "source_paper": f"{paper_id}_v3",
                        "creation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "score": 7.0 if info["success"] else 4.0,
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
    """Add curated meta-experiences from V3 analysis."""
    total = 0
    for exp_data in META_EXPERIENCES:
        try:
            meta = exp_data.get("metadata", {})
            exp = Experience(
                id=f"exp_meta_v3_{uuid.uuid4().hex[:8]}",
                type=exp_data["type"],
                domain_hint=exp_data["domain_hint"],
                condition=exp_data["condition"],
                action=exp_data["action"],
                rationale=exp_data["rationale"],
                metadata={
                    "source_paper": meta.get("source_paper", "v3_analysis"),
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
            print(f"  ✅ Meta-experience: {eid} — {symptom}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

    return total


def main():
    print("=" * 60)
    print("  V3 Experience Extraction Pipeline")
    print("=" * 60)

    db = ExperienceDB()
    print(f"\nExisting DB stats: {db.stats()}")

    # Step 1: Extract from trajectories
    print(f"\n{'='*60}")
    print("Step 1: Extracting from V3 trajectories...")
    print(f"{'='*60}")
    traj_count = extract_from_trajectories(db)
    print(f"\nExtracted {traj_count} experiences from trajectories")

    # Step 2: Add meta-experiences
    print(f"\n{'='*60}")
    print("Step 2: Adding meta-experiences from V3 analysis...")
    print(f"{'='*60}")
    meta_count = add_meta_experiences(db)
    print(f"\nAdded {meta_count} meta-experiences")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Trajectory experiences: {traj_count}")
    print(f"  Meta-experiences: {meta_count}")
    print(f"  Total new: {traj_count + meta_count}")
    print(f"  DB stats: {db.stats()}")


if __name__ == "__main__":
    main()
