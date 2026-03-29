#!/usr/bin/env python3
"""
MAS (Metric Alignment Score) Evaluation for all B1/B2 test papers.

Extracts paper ground-truth values and reproduced values from workspace results.json,
computes per-metric and aggregate MAS scores, and generates a comprehensive report.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.evaluation.mas_calculator import compute_single_mas, compute_aggregate_mas

# ═══════════════════════════════════════════════════════════════
#  GROUND TRUTH DEFINITIONS — extracted from papers
#  Each paper has a list of metrics with:
#    name, direction (higher/lower/target), paper_value,
#    extract_fn: lambda to pull reproduced value from results.json
# ═══════════════════════════════════════════════════════════════

def safe_get(d, *keys, default=None):
    """Safely navigate nested dict."""
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


PAPER_METRICS = {
    "fpm_inr": {
        "display_name": "FPM-INR",
        "metrics": [
            {
                "name": "INR L2 Error (All-in-Focus)",
                "direction": "lower",
                "paper_value": 0.00141,
                "extract": lambda r: safe_get(r, "metrics", "reconstruction_quality", "fpm_inr_avg_l2_error")
                           or safe_get(r, "experiments", "patch_128", "inr_l2_mean"),
                "weight": 2.0,
                "note": "Paper Table 1: INR all-in-focus L2 error"
            },
            {
                "name": "FPM L2 Error (All-in-Focus)",
                "direction": "lower",
                "paper_value": 0.00234,
                "extract": lambda r: safe_get(r, "metrics", "reconstruction_quality", "fpm_avg_l2_error")
                           or safe_get(r, "experiments", "patch_128", "fpm_l2_mean"),
                "weight": 1.5,
                "note": "Paper Table 1: FPM all-in-focus L2 error"
            },
            {
                "name": "Speed Ratio (INR vs FPM)",
                "direction": "higher",
                "paper_value": 3.0,  # Paper claims ~3x faster
                "extract": lambda r: safe_get(r, "metrics", "computational_time", "speed_ratio_training")
                           or safe_get(r, "experiments", "patch_128", "speed_ratio"),
                "weight": 1.0,
                "note": "Paper: INR ~3x faster than FPM"
            },
            {
                "name": "Compression Ratio",
                "direction": "higher",
                "paper_value": 10.0,  # Paper claims ~10x compression
                "extract": lambda r: safe_get(r, "experiments", "patch_128", "compression_ratio"),
                "weight": 1.0,
                "note": "Paper: ~10x storage compression"
            },
        ]
    },
    "lensless": {
        "display_name": "LenslessPiCam",
        "metrics": [
            {
                "name": "ADMM Reconstruction PSNR (dB)",
                "direction": "higher",
                "paper_value": 12.7,  # Paper Table 3: ADMM 100-iter PSNR = 12.7 dB
                "extract": lambda r: (safe_get(r, "metrics", "simulation_admm_100iter", "psnr_db")
                                      or safe_get(r, "metrics", "table3_admm_100iter_avg_simulated", "reproduced_values_synthetic_images", "PSNR")
                                      or safe_get(r, "metrics", "reconstruction_quality", "admm_psnr_db")),
                "weight": 2.0,
                "note": "Paper Table 3: ADMM 100-iter PSNR"
            },
            {
                "name": "ADMM Reconstruction SSIM",
                "direction": "higher",
                "paper_value": 0.535,  # Paper Table 3: ADMM SSIM = 0.535
                "extract": lambda r: (safe_get(r, "metrics", "simulation_admm_100iter", "ssim")
                                      or safe_get(r, "metrics", "table3_admm_100iter_avg_simulated", "reproduced_values_synthetic_images", "SSIM")
                                      or safe_get(r, "metrics", "reconstruction_quality", "admm_ssim")),
                "weight": 2.0,
                "note": "Paper Table 3: ADMM SSIM"
            },
            {
                "name": "ADMM Reconstruction MSE",
                "direction": "lower",
                "paper_value": 0.0797,  # Paper Table 3: ADMM MSE = 0.0797
                "extract": lambda r: (safe_get(r, "metrics", "simulation_admm_100iter", "mse")
                                      or safe_get(r, "metrics", "table3_admm_100iter_avg_simulated", "reproduced_values_synthetic_images", "MSE")),
                "weight": 1.5,
                "note": "Paper Table 3: ADMM MSE"
            },
            {
                "name": "NumPy ADMM 5-iter Time (s)",
                "direction": "target",
                "paper_value": 1.26,  # Paper Table 1
                "extract": lambda r: (safe_get(r, "metrics", "table1_timing_benchmark", "ADMM_5iter_numpy_s")
                                      or _extract_lensless_admm_time(r)),
                "weight": 1.0,
                "note": "Paper Table 1: LenslessPiCam NumPy ADMM 5-iter"
            },
        ]
    },
    "lfm": {
        "display_name": "Artifact-free LFM Deconvolution",
        "metrics": [
            {
                "name": "AA Filter Radius at NOP (px)",
                "direction": "target",
                "paper_value": 11.5,  # Paper Fig 2(c): max ~11.5 px at NOP
                "extract": lambda r: (safe_get(r, "metrics", "anti_aliasing_filter_radius_px", "at_zero_plane")
                                      or safe_get(r, "metrics", "aa_filter_max")),
                "weight": 2.0,
                "note": "Paper Fig 2(c): AA filter max at NOP"
            },
            {
                "name": "Artifact Reduction (EMS vs RL) %",
                "direction": "higher",
                "paper_value": 50.0,  # Paper claims significant artifact reduction
                "extract": lambda r: (safe_get(r, "metrics", "artifact_reduction_zero_plane", "std_reduction_percent")
                                      or _extract_lfm_artifact_reduction(r)),
                "weight": 2.0,
                "note": "Paper: EMS significantly reduces artifacts vs RL"
            },
            {
                "name": "N Iterations",
                "direction": "target",
                "paper_value": 8,
                "extract": lambda r: (safe_get(r, "system_parameters", "n_iterations")
                                      or safe_get(r, "metrics", "deconvolution", "n_iterations")),
                "weight": 0.5,
                "note": "Paper Section 5: 8 iterations"
            },
            {
                "name": "Voxel Size (μm)",
                "direction": "target",
                "paper_value": 0.325,  # 6.5μm / 20x = 0.325μm
                "extract": lambda r: (safe_get(r, "system_parameters", "voxel_lateral_um")
                                      or safe_get(r, "metrics", "system", "voxel_size_um")),
                "weight": 1.0,
                "note": "Paper: pixel_pitch/M = 6.5/20 = 0.325 μm"
            },
        ]
    },
    "sparse_sim": {
        "display_name": "Sparse-SIM Deconvolution",
        "metrics": [
            {
                "name": "Resolution Improvement (FWHM ratio)",
                "direction": "target",
                "paper_value": 2.0,  # Paper claims ~2x improvement
                "extract": lambda r: (safe_get(r, "metrics", "resolution_improvement_fwhm")
                                      or safe_get(r, "experiments", "exp5_resolution_improvement", "resolution_improvement_sparse")
                                      or safe_get(r, "metrics_summary", "exp5_improvement_factor")),
                "weight": 2.0,
                "note": "Paper: ~2x resolution improvement"
            },
            {
                "name": "Fourier Spectrum Improvement",
                "direction": "target",
                "paper_value": 2.0,  # Paper claims ~2x
                "extract": lambda r: (safe_get(r, "metrics", "resolution_improvement_fourier")
                                      or safe_get(r, "experiments", "exp5_resolution_improvement", "resolution_improvement_upsampled")),
                "weight": 1.5,
                "note": "Paper: ~2x Fourier spectrum improvement"
            },
            {
                "name": "Min Resolved Filament Separation (nm)",
                "direction": "lower",
                "paper_value": 73.0,  # Paper: 65-81nm → midpoint 73nm
                "extract": lambda r: (safe_get(r, "metrics", "filament_min_separation_sparse_nm")
                                      or safe_get(r, "key_claims_verification", "claim2_min_resolved_filament_sparse_nm")
                                      or _extract_sparse_min_sep(r)),
                "weight": 2.0,
                "note": "Paper: sparse resolves 65-81nm filaments"
            },
            {
                "name": "Noise Robustness (levels resolved)",
                "direction": "higher",
                "paper_value": 5,  # Paper: robust across noise levels
                "extract": lambda r: (safe_get(r, "metrics", "noise_robustness_sparse_resolved")
                                      or _extract_sparse_noise_robustness(r)),
                "weight": 1.0,
                "note": "Paper: sparse deconv robust to noise"
            },
        ]
    },
    "flfm": {
        "display_name": "Fourier Light-Field Microscopy",
        "metrics": [
            {
                "name": "N_occupancy Ratio",
                "direction": "target",
                "paper_value": 5.9375,
                "extract": lambda r: (safe_get(r, "metrics", "theoretical_parameters", "N_occupancy", "computed")
                                      or safe_get(r, "metrics", "analytical_system_parameters", "N_occupancy_ratio", "computed")),
                "weight": 1.5,
                "note": "Paper Eq 3: N = f_obj * NA / (M * p_MLA)"
            },
            {
                "name": "R_xy Lateral Resolution (μm)",
                "direction": "target",
                "paper_value": 2.12,
                "extract": lambda r: (safe_get(r, "metrics", "theoretical_parameters", "R_xy_um", "computed")
                                      or safe_get(r, "metrics", "analytical_system_parameters", "R_xy_lateral_resolution_um", "computed")),
                "weight": 2.0,
                "note": "Paper Eq 5: R_xy = 0.61 * λ / NA"
            },
            {
                "name": "R_z Axial Resolution (μm)",
                "direction": "target",
                "paper_value": 4.7,
                "extract": lambda r: (safe_get(r, "metrics", "theoretical_parameters", "R_z_um", "computed")
                                      or safe_get(r, "metrics", "analytical_system_parameters", "R_z_axial_resolution_um", "computed")),
                "weight": 2.0,
                "note": "Paper Eq 6: R_z = 2λ / NA²"
            },
            {
                "name": "DOF (μm)",
                "direction": "target",
                "paper_value": 64.0,
                "extract": lambda r: (safe_get(r, "metrics", "theoretical_parameters", "DOF_um", "computed")
                                      or safe_get(r, "metrics", "analytical_system_parameters", "DOF_um", "computed")),
                "weight": 1.5,
                "note": "Paper: DOF = 64 μm"
            },
            {
                "name": "FOV (μm)",
                "direction": "target",
                "paper_value": 67.0,  # Paper: ~67 μm
                "extract": lambda r: (safe_get(r, "metrics", "theoretical_parameters", "FOV_um", "computed")
                                      or safe_get(r, "metrics", "analytical_system_parameters", "FOV_um", "computed")),
                "weight": 1.0,
                "note": "Paper: FOV ≈ 67 μm"
            },
            {
                "name": "Bead FWHM_z (μm)",
                "direction": "target",
                "paper_value": 4.5,  # Paper: ~4.5 μm axial FWHM
                "extract": lambda r: (safe_get(r, "metrics", "axial_psf", "axial_FWHM_central_um")
                                      or safe_get(r, "metrics", "reconstructed_bead_fwhm_z0", "FWHM_z_um")
                                      or safe_get(r, "metrics", "reconstructed_bead_fwhm_z0", "FWHM_z_gauss_um")),
                "weight": 1.5,
                "note": "Paper Fig 5: axial FWHM ~4.5 μm"
            },
        ]
    },
}


def _extract_lfm_artifact_reduction(r):
    """Extract artifact reduction from various result formats."""
    # Try artifact_analysis nested structure
    aa = safe_get(r, "metrics", "artifact_analysis")
    if aa and isinstance(aa, dict):
        for dz_key in ["dz_0", "dz_-10", "dz_10"]:
            entry = aa.get(dz_key, {})
            if "artifact_reduction_pct" in entry:
                return entry["artifact_reduction_pct"]
    # Try contrast_at_zero_plane
    contrast = safe_get(r, "metrics", "contrast_at_zero_plane")
    if contrast:
        rl = contrast.get("RL_contrast", [])
        ems = contrast.get("EMS_contrast", [])
        if rl and ems and len(rl) == len(ems):
            # Compute average contrast reduction
            reductions = []
            for r_val, e_val in zip(rl, ems):
                if r_val > 0:
                    reductions.append((1 - e_val / r_val) * 100)
            if reductions:
                return sum(reductions) / len(reductions)
    return None


def _extract_sparse_min_sep(r):
    """Extract minimum resolved separation for sparse deconv."""
    exp2 = safe_get(r, "experiments", "exp2_filament_resolution")
    if exp2 and isinstance(exp2, dict):
        for sep_nm in sorted(exp2.keys(), key=lambda x: int(x.replace("nm", ""))):
            entry = exp2[sep_nm]
            if entry.get("resolved_sparse") or entry.get("resolved_sparse_x2"):
                return int(sep_nm.replace("nm", ""))
    return None


def _extract_lensless_admm_time(r):
    """Extract ADMM timing from various lensless result formats."""
    # B2 format: metrics.table1_benchmark_times.reproduced_values.numpy_admm_5
    rv = safe_get(r, "metrics", "table1_benchmark_times", "reproduced_values")
    if rv and isinstance(rv, dict):
        val = rv.get("numpy_admm_5", "")
        if isinstance(val, str):
            # Parse "211 ms" or "1.26 s"
            val = val.strip()
            if val.endswith("ms"):
                return float(val.replace("ms", "").strip()) / 1000.0
            elif val.endswith("s"):
                return float(val.replace("s", "").strip())
        elif isinstance(val, (int, float)):
            return float(val)
    return None


def _extract_sparse_noise_robustness(r):
    """Count how many noise levels sparse deconv outperforms RL."""
    exp6 = safe_get(r, "experiments", "exp6_noise_robustness")
    if exp6 and isinstance(exp6, dict):
        count = sum(1 for v in exp6.values()
                    if isinstance(v, dict) and v.get("sparse_better_than_rl"))
        return count if count > 0 else None
    return None


# ═══════════════════════════════════════════════════════════════
#  EVALUATION ENGINE
# ═══════════════════════════════════════════════════════════════

def evaluate_paper(paper_id: str, results: Dict) -> Dict:
    """Evaluate a single paper's MAS scores."""
    if paper_id not in PAPER_METRICS:
        return {"paper_id": paper_id, "error": f"No metric definitions for {paper_id}"}

    spec = PAPER_METRICS[paper_id]
    metrics_list = []
    skipped = []

    for m in spec["metrics"]:
        reproduced_value = m["extract"](results)
        if reproduced_value is None:
            skipped.append({"name": m["name"], "reason": "value not found in results"})
            continue
        try:
            reproduced_value = float(reproduced_value)
        except (TypeError, ValueError):
            skipped.append({"name": m["name"], "reason": f"non-numeric value: {reproduced_value}"})
            continue

        metrics_list.append({
            "name": m["name"],
            "direction": m["direction"],
            "paper_value": m["paper_value"],
            "reproduced_value": reproduced_value,
            "weight": m.get("weight", 1.0),
            "note": m.get("note", ""),
        })

    if not metrics_list:
        return {
            "paper_id": paper_id,
            "display_name": spec["display_name"],
            "aggregate_mas": 0.0,
            "metrics_evaluated": 0,
            "metrics_skipped": len(skipped),
            "skipped": skipped,
            "per_metric": [],
        }

    result = compute_aggregate_mas(metrics_list)
    result["paper_id"] = paper_id
    result["display_name"] = spec["display_name"]
    result["metrics_skipped"] = len(skipped)
    result["skipped"] = skipped

    # Add notes to per_metric
    for pm, ml in zip(result["per_metric"], metrics_list):
        pm["note"] = ml.get("note", "")

    return result


def load_workspace_results(result_json_path: str) -> Optional[Dict]:
    """Load results.json from workspace referenced in result JSON."""
    with open(result_json_path) as f:
        d = json.load(f)
    ws = d.get("workspace", "")
    rj = os.path.join(ws, "results.json")
    if os.path.exists(rj):
        with open(rj) as f:
            return json.load(f)
    return None


def run_evaluation(base_dir: str) -> Dict:
    """Run MAS evaluation on all B1 and B2 test papers."""
    papers = ["fpm_inr", "lensless", "lfm", "sparse_sim", "flfm"]
    groups = ["test_b1", "test_b2"]

    all_results = {}

    for group in groups:
        group_results = {}
        for paper in papers:
            result_path = os.path.join(base_dir, f"data/reproduction_results_v5/{group}/{paper}_result.json")
            if not os.path.exists(result_path):
                group_results[paper] = {"error": f"Result file not found: {result_path}"}
                continue

            ws_results = load_workspace_results(result_path)
            if ws_results is None:
                group_results[paper] = {"error": "No results.json in workspace"}
                continue

            mas_result = evaluate_paper(paper, ws_results)
            group_results[paper] = mas_result

        all_results[group] = group_results

    return all_results


def print_report(all_results: Dict):
    """Print comprehensive MAS evaluation report."""
    print("=" * 80)
    print("  MAS (Metric Alignment Score) EVALUATION REPORT")
    print("=" * 80)

    for group in ["test_b1", "test_b2"]:
        group_label = "B1 (No Experience)" if group == "test_b1" else "B2 (With Experience)"
        print(f"\n{'─' * 80}")
        print(f"  {group_label}")
        print(f"{'─' * 80}")

        group_data = all_results.get(group, {})
        agg_scores = []

        for paper_id, result in group_data.items():
            if "error" in result:
                print(f"\n  ❌ {paper_id}: {result['error']}")
                continue

            agg = result.get("aggregate_mas", 0)
            n_eval = len(result.get("per_metric", []))
            n_skip = result.get("metrics_skipped", 0)
            full = result.get("full_reproduction", False)
            display = result.get("display_name", paper_id)

            agg_scores.append(agg)

            status = "✅ FULL" if full else ("⚠️  PARTIAL" if agg >= 0.5 else "❌ LOW")
            print(f"\n  {display} ({paper_id})")
            print(f"    Aggregate MAS: {agg:.4f}  [{status}]")
            print(f"    Metrics evaluated: {n_eval}, skipped: {n_skip}")

            for pm in result.get("per_metric", []):
                dir_sym = {"higher": "↑", "lower": "↓", "target": "⊙"}.get(pm["direction"], "?")
                mas_bar = "█" * int(pm["mas"] * 20) + "░" * (20 - int(pm["mas"] * 20))
                print(f"      {dir_sym} {pm['name']:40s}  paper={pm['paper']:>10.4f}  repr={pm['reproduced']:>10.4f}  MAS={pm['mas']:.4f} |{mas_bar}|")

            if result.get("skipped"):
                for sk in result["skipped"]:
                    print(f"      ⊘ {sk['name']:40s}  SKIPPED: {sk['reason']}")

        if agg_scores:
            mean_mas = sum(agg_scores) / len(agg_scores)
            print(f"\n  {'─' * 60}")
            print(f"  {group_label} Mean MAS: {mean_mas:.4f} (n={len(agg_scores)} papers)")

    # Comparison summary
    print(f"\n{'=' * 80}")
    print("  B1 vs B2 COMPARISON")
    print(f"{'=' * 80}")

    papers = ["fpm_inr", "lensless", "lfm", "sparse_sim", "flfm"]
    print(f"\n  {'Paper':<20s} {'B1 MAS':>10s} {'B2 MAS':>10s} {'Δ MAS':>10s} {'Winner':>10s}")
    print(f"  {'─' * 60}")

    b1_scores = []
    b2_scores = []

    for paper in papers:
        b1 = all_results.get("test_b1", {}).get(paper, {})
        b2 = all_results.get("test_b2", {}).get(paper, {})
        b1_mas = b1.get("aggregate_mas", 0) if "error" not in b1 else 0
        b2_mas = b2.get("aggregate_mas", 0) if "error" not in b2 else 0
        delta = b2_mas - b1_mas
        winner = "B2" if delta > 0.01 else ("B1" if delta < -0.01 else "TIE")

        b1_scores.append(b1_mas)
        b2_scores.append(b2_mas)

        display = PAPER_METRICS.get(paper, {}).get("display_name", paper)
        print(f"  {display:<20s} {b1_mas:>10.4f} {b2_mas:>10.4f} {delta:>+10.4f} {winner:>10s}")

    b1_mean = sum(b1_scores) / len(b1_scores) if b1_scores else 0
    b2_mean = sum(b2_scores) / len(b2_scores) if b2_scores else 0
    delta_mean = b2_mean - b1_mean

    print(f"  {'─' * 60}")
    print(f"  {'MEAN':<20s} {b1_mean:>10.4f} {b2_mean:>10.4f} {delta_mean:>+10.4f}")
    print(f"\n  B2 wins: {sum(1 for b1, b2 in zip(b1_scores, b2_scores) if b2 > b1 + 0.01)}/5")
    print(f"  B1 wins: {sum(1 for b1, b2 in zip(b1_scores, b2_scores) if b1 > b2 + 0.01)}/5")
    print(f"  Ties:    {sum(1 for b1, b2 in zip(b1_scores, b2_scores) if abs(b2 - b1) <= 0.01)}/5")


def save_results(all_results: Dict, output_path: str):
    """Save evaluation results to JSON."""
    # Make serializable (remove lambda functions)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n📄 Results saved to: {output_path}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    base_dir = str(Path(__file__).resolve().parent.parent)
    print(f"Base directory: {base_dir}")

    all_results = run_evaluation(base_dir)
    print_report(all_results)

    output_path = os.path.join(base_dir, "data/reproduction_results_v5/mas_evaluation.json")
    save_results(all_results, output_path)
