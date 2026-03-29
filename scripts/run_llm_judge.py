#!/usr/bin/env python3
"""
Run LLM Judge (Code Faithfulness Evaluation) on all B1/B2 test papers.

Uses the LLM Judge to evaluate how faithfully the reproduced code implements
the paper's method. Evaluates both B1 (no experience) and B2 (with experience).
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.evaluation.llm_judge import (
    evaluate_workspace, print_report, save_report, FaithfulnessReport
)

BASE_DIR = Path(__file__).resolve().parent.parent
PAPERS = ["fpm_inr", "lensless", "lfm", "sparse_sim", "flfm"]
GROUPS = ["test_b1", "test_b2"]


def run_judge_all():
    """Run LLM Judge on all test papers for B1 and B2."""
    all_reports = {}

    for group in GROUPS:
        group_label = "B1 (No Experience)" if group == "test_b1" else "B2 (With Experience)"
        print(f"\n{'='*70}")
        print(f"  LLM JUDGE: {group_label}")
        print(f"{'='*70}")

        group_reports = {}

        for paper_id in PAPERS:
            print(f"\n--- Evaluating {paper_id} ({group}) ---")

            # Skip if already evaluated
            report_path = BASE_DIR / f"data/reproduction_results_v5/{group}/{paper_id}_judge.json"
            if report_path.exists():
                with open(report_path) as f:
                    existing = json.load(f)
                if existing.get("overall_score", 0) > 0:
                    print(f"  ✅ Already evaluated (score={existing['overall_score']}), skipping")
                    group_reports[paper_id] = {
                        "overall_score": existing["overall_score"],
                        "n_components": len(existing.get("components", [])),
                        "full_count": sum(1 for c in existing.get("components", []) if c.get("score") == "full"),
                        "partial_count": sum(1 for c in existing.get("components", []) if c.get("score") == "partial"),
                        "missing_count": sum(1 for c in existing.get("components", []) if c.get("score") == "missing"),
                        "summary": existing.get("summary", ""),
                        "strengths": existing.get("strengths", []),
                        "weaknesses": existing.get("weaknesses", []),
                    }
                    continue

            # Load paper markdown
            paper_md = BASE_DIR / f"data/paper_markdowns_v2/{paper_id}_full.md"
            if not paper_md.exists():
                paper_md = BASE_DIR / f"data/paper_markdowns_v2/{paper_id}_task.md"
            if not paper_md.exists():
                print(f"  ⚠️  No paper markdown found for {paper_id}")
                continue

            paper_text = paper_md.read_text(encoding="utf-8", errors="ignore")

            # Load workspace path
            result_path = BASE_DIR / f"data/reproduction_results_v5/{group}/{paper_id}_result.json"
            if not result_path.exists():
                print(f"  ⚠️  No result file for {paper_id}")
                continue

            with open(result_path) as f:
                result_data = json.load(f)
            workspace = result_data.get("workspace", "")

            if not os.path.isdir(workspace):
                print(f"  ⚠️  Workspace not found: {workspace}")
                continue

            # Run evaluation
            try:
                report = evaluate_workspace(
                    paper_text=paper_text,
                    workspace=workspace,
                    paper_id=paper_id,
                    task_id=f"{group}_{paper_id}",
                )
                print_report(report)

                # Save individual report
                report_path = BASE_DIR / f"data/reproduction_results_v5/{group}/{paper_id}_judge.json"
                save_report(report, str(report_path))

                group_reports[paper_id] = {
                    "overall_score": report.overall_score,
                    "n_components": len(report.components),
                    "full_count": sum(1 for c in report.components if c.score == "full"),
                    "partial_count": sum(1 for c in report.components if c.score == "partial"),
                    "missing_count": sum(1 for c in report.components if c.score == "missing"),
                    "summary": report.summary,
                    "strengths": report.strengths,
                    "weaknesses": report.weaknesses,
                }

            except Exception as e:
                print(f"  ❌ Error evaluating {paper_id}: {e}")
                import traceback
                traceback.print_exc()
                group_reports[paper_id] = {"error": str(e)}

            # Rate limiting
            time.sleep(2)

        all_reports[group] = group_reports

    # Print comparison summary
    print(f"\n{'='*70}")
    print(f"  LLM JUDGE COMPARISON: B1 vs B2")
    print(f"{'='*70}")

    print(f"\n  {'Paper':<20s} {'B1 Score':>10s} {'B2 Score':>10s} {'Δ':>8s} {'B1 ○/△/×':>12s} {'B2 ○/△/×':>12s}")
    print(f"  {'─'*62}")

    b1_scores = []
    b2_scores = []

    for paper_id in PAPERS:
        b1 = all_reports.get("test_b1", {}).get(paper_id, {})
        b2 = all_reports.get("test_b2", {}).get(paper_id, {})

        b1_score = b1.get("overall_score", 0)
        b2_score = b2.get("overall_score", 0)
        delta = b2_score - b1_score

        b1_comp = f"{b1.get('full_count',0)}/{b1.get('partial_count',0)}/{b1.get('missing_count',0)}"
        b2_comp = f"{b2.get('full_count',0)}/{b2.get('partial_count',0)}/{b2.get('missing_count',0)}"

        b1_scores.append(b1_score)
        b2_scores.append(b2_score)

        print(f"  {paper_id:<20s} {b1_score:>10.1f} {b2_score:>10.1f} {delta:>+8.1f} {b1_comp:>12s} {b2_comp:>12s}")

    b1_mean = sum(b1_scores) / len(b1_scores) if b1_scores else 0
    b2_mean = sum(b2_scores) / len(b2_scores) if b2_scores else 0

    print(f"  {'─'*62}")
    print(f"  {'MEAN':<20s} {b1_mean:>10.2f} {b2_mean:>10.2f} {b2_mean-b1_mean:>+8.2f}")

    # Save summary
    summary = {
        "b1_mean_score": round(b1_mean, 2),
        "b2_mean_score": round(b2_mean, 2),
        "delta": round(b2_mean - b1_mean, 2),
        "per_paper": all_reports,
    }
    summary_path = BASE_DIR / "data/reproduction_results_v5/judge_evaluation.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n📄 Summary saved to: {summary_path}")


if __name__ == "__main__":
    run_judge_all()
