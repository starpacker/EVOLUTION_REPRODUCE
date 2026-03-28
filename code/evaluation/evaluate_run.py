#!/usr/bin/env python3
"""
Post-Run Evaluation Pipeline for Evolution-Reproduce.

Combines:
  1. Result collection from workspace
  2. MAS calculation (metric alignment)
  3. LLM Judge (code faithfulness)
  4. Experience extraction from trajectory
  5. Summary report generation

Usage:
  python -m code.evaluation.evaluate_run --paper_id PyAbel --task_id PyAbel_20260319_011856
  python -m code.evaluation.evaluate_run --scan  # Auto-find latest results
"""

import json
import os
import sys
import glob
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Paths ───
RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v2"
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
WORKSPACE_BASE = Path("/data/yjh/openhands_workspace")
TRAJECTORY_DIR = Path("/data/yjh/openhands_results_v2/trajectories")


def find_latest_result(paper_id: str) -> Optional[Dict]:
    """Find the most recent result JSON for a paper_id."""
    results_dir = RESULTS_DIR / paper_id
    if not results_dir.exists():
        return None
    
    result_files = sorted(results_dir.glob(f"{paper_id}_*_result.json"), 
                          key=os.path.getmtime, reverse=True)
    if not result_files:
        return None
    
    with open(result_files[0]) as f:
        data = json.load(f)
    data["_result_file"] = str(result_files[0])
    return data


def find_latest_oh_result(paper_id: str) -> Optional[Dict]:
    """Find the most recent OpenHands output result."""
    results_dir = RESULTS_DIR / paper_id
    if not results_dir.exists():
        return None
    
    oh_files = sorted(results_dir.glob(f"{paper_id}_*_oh_result.json"),
                      key=os.path.getmtime, reverse=True)
    if not oh_files:
        return None
    
    with open(oh_files[0]) as f:
        data = json.load(f)
    data["_file"] = str(oh_files[0])
    return data


def collect_workspace_artifacts(workspace: str) -> Dict[str, Any]:
    """Scan workspace for produced artifacts."""
    ws = Path(workspace)
    artifacts = {
        "has_reproduce_py": False,
        "has_results_json": False,
        "python_files": [],
        "data_files": [],
        "log_files": [],
        "total_files": 0,
    }
    
    if not ws.exists():
        artifacts["error"] = f"Workspace not found: {workspace}"
        return artifacts
    
    for f in ws.rglob("*"):
        if f.is_file():
            artifacts["total_files"] += 1
            rel = str(f.relative_to(ws))
            
            if f.name == "reproduce.py":
                artifacts["has_reproduce_py"] = True
                artifacts["reproduce_py_path"] = str(f)
                artifacts["reproduce_py_size"] = f.stat().st_size
            elif f.name == "results.json":
                artifacts["has_results_json"] = True
                try:
                    with open(f) as fh:
                        artifacts["results_json"] = json.load(fh)
                except:
                    artifacts["results_json_error"] = "Failed to parse"
            elif f.suffix == ".py":
                artifacts["python_files"].append(rel)
            elif f.suffix in (".json", ".csv", ".npy", ".npz"):
                artifacts["data_files"].append(rel)
            elif f.suffix in (".log", ".txt"):
                artifacts["log_files"].append(rel)
    
    return artifacts


def extract_metrics_from_workspace(workspace: str) -> Dict[str, float]:
    """Extract metrics from results.json or METRIC: lines in output."""
    ws = Path(workspace)
    metrics = {}
    
    # Try results.json
    results_file = ws / "results.json"
    if results_file.exists():
        try:
            with open(results_file) as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    try:
                        metrics[k] = float(v)
                    except (ValueError, TypeError):
                        pass
        except:
            pass
    
    # Also scan for METRIC: lines in any text file
    for log_file in list(ws.glob("*.log")) + list(ws.glob("*.txt")):
        try:
            text = log_file.read_text(errors="ignore")
            for line in text.split("\n"):
                if "METRIC:" in line and "=" in line:
                    parts = line.split("=", 1)
                    name = parts[0].split("METRIC:")[-1].strip()
                    try:
                        val = float(parts[1].strip())
                        metrics[name] = val
                    except:
                        pass
        except:
            continue
    
    return metrics


def run_mas_evaluation(paper_id: str, reproduced_metrics: Dict[str, float]) -> Optional[Dict]:
    """Run MAS Calculator on reproduced metrics vs paper metrics."""
    if not reproduced_metrics:
        return {"error": "No metrics to evaluate", "mas_score": 0.0}
    
    try:
        from code.evaluation.mas_calculator import MASCalculator
        calc = MASCalculator()
        
        # For now, we need paper metrics defined — this would come from benchmark metadata
        # Placeholder: just report what metrics were reproduced
        return {
            "reproduced_metrics": reproduced_metrics,
            "num_metrics": len(reproduced_metrics),
            "note": "Full MAS evaluation requires paper benchmark metrics definition"
        }
    except Exception as e:
        return {"error": str(e)}


def run_llm_judge(paper_id: str, workspace: str) -> Optional[Dict]:
    """Run LLM Judge on the reproduced code."""
    ws = Path(workspace)
    reproduce_py = ws / "reproduce.py"
    
    if not reproduce_py.exists():
        # Try to find any main Python file
        py_files = list(ws.glob("*.py"))
        if py_files:
            reproduce_py = py_files[0]
        else:
            return {"error": "No Python code found in workspace"}
    
    # Prioritize _full.md > _task.md > plain .md
    paper_md = None
    for suffix in [f"{paper_id}_full.md", f"{paper_id}_task.md", f"{paper_id}.md"]:
        candidate = PAPER_MARKDOWN_DIR / suffix
        if candidate.exists():
            paper_md = candidate
            break
    if paper_md is None:
        return {"error": f"Paper markdown not found in {PAPER_MARKDOWN_DIR} for {paper_id}"}
    
    try:
        from code.evaluation.llm_judge import LLMJudge
        judge = LLMJudge()
        
        code_text = reproduce_py.read_text(encoding="utf-8")
        paper_text = paper_md.read_text(encoding="utf-8")
        
        print(f"[Eval] Running LLM Judge on {reproduce_py.name} ({len(code_text)} chars)...")
        result = judge.evaluate(paper_text, code_text)
        return result
    except Exception as e:
        return {"error": f"LLM Judge failed: {str(e)}"}


def trigger_experience_extraction(trajectory_path: str, paper_id: str,
                                   task_success: bool = False) -> Optional[Dict]:
    """Extract experiences from the task trajectory and store in Experience DB.
    
    This combines trajectory parsing + Experience DB storage into one step.
    """
    if not trajectory_path or not os.path.exists(trajectory_path):
        return {"error": f"Trajectory not found: {trajectory_path}"}
    
    try:
        from code.experience_db.trajectory_parser import process_trajectory
        
        print(f"[Eval] Extracting experiences from trajectory: {trajectory_path}")
        raw_experiences = process_trajectory(
            trajectory_path, 
            project_name=paper_id,
            domain="unknown"
        )
        
        if not raw_experiences:
            return {"num_extracted": 0, "num_stored": 0, "experiences": []}
        
        # Store extracted experiences in the Experience DB
        stored_count = 0
        try:
            from code.experience_db.experience_db import ExperienceDB, Experience
            import time as _time
            import uuid as _uuid
            
            db = ExperienceDB()
            for exp_data in raw_experiences:
                try:
                    exp = Experience(
                        id=f"exp_{paper_id}_{_time.strftime('%Y%m%d')}_{_uuid.uuid4().hex[:8]}",
                        type=exp_data.get("type", "positive"),
                        domain_hint=exp_data.get("domain_hint", "unknown"),
                        condition=exp_data.get("condition", {}),
                        action=exp_data.get("action", {}),
                        rationale=exp_data.get("rationale", ""),
                        metadata={
                            "source_paper": paper_id,
                            "source_trajectory": trajectory_path,
                            "creation_time": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "score": 5.0,
                            "call_count": 0,
                            "success_count": 1 if task_success else 0,
                        },
                        status="verified" if task_success else "hypothesis",
                    )
                    db.add(exp)
                    stored_count += 1
                except Exception as e:
                    print(f"  ⚠️ Failed to store experience: {e}")
            
            print(f"[Eval] Stored {stored_count}/{len(raw_experiences)} experiences in DB")
            print(f"[Eval] DB stats: {db.stats()}")
        except Exception as e:
            print(f"[Eval] Experience DB storage failed: {e}")
        
        return {
            "num_extracted": len(raw_experiences),
            "num_stored": stored_count,
            "experiences": [
                exp.get("condition", {}).get("error_or_symptom", "")[:100]
                for exp in (raw_experiences or [])
            ][:5]
        }
    except Exception as e:
        return {"error": f"Experience extraction failed: {str(e)}"}


def generate_report(
    paper_id: str,
    task_result: Dict,
    oh_result: Optional[Dict],
    artifacts: Dict,
    metrics: Dict,
    mas_result: Optional[Dict],
    judge_result: Optional[Dict],
    experience_result: Optional[Dict],
) -> str:
    """Generate a human-readable evaluation report."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  EVALUATION REPORT: {paper_id}")
    lines.append(f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    
    # 1. Task Summary
    lines.append("\n## 1. Task Summary")
    lines.append(f"  Task ID: {task_result.get('task_id', 'N/A')}")
    lines.append(f"  Agent State: {task_result.get('agent_state', 'N/A')}")
    lines.append(f"  Success: {task_result.get('success', False)}")
    lines.append(f"  Iterations: {task_result.get('iterations_used', -1)}")
    lines.append(f"  Duration: {task_result.get('duration_seconds', 0):.1f}s")
    
    if oh_result:
        lines.append(f"  OH State: {oh_result.get('agent_state', 'N/A')}")
        lines.append(f"  OH Elapsed: {oh_result.get('elapsed_seconds', 0):.1f}s")
        lines.append(f"  Has reproduce.py: {oh_result.get('has_reproduce_py', False)}")
        lines.append(f"  Has results.json: {oh_result.get('has_results_json', False)}")
    
    # 2. Workspace Artifacts
    lines.append("\n## 2. Workspace Artifacts")
    lines.append(f"  Total files: {artifacts.get('total_files', 0)}")
    lines.append(f"  reproduce.py: {'✅' if artifacts.get('has_reproduce_py') else '❌'}")
    lines.append(f"  results.json: {'✅' if artifacts.get('has_results_json') else '❌'}")
    if artifacts.get("python_files"):
        lines.append(f"  Python files: {', '.join(artifacts['python_files'][:10])}")
    
    # 3. Reproduced Metrics
    lines.append("\n## 3. Reproduced Metrics")
    if metrics:
        for k, v in metrics.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  No metrics found")
    
    # 4. MAS Evaluation
    lines.append("\n## 4. MAS (Metric Alignment Score)")
    if mas_result:
        if "error" in mas_result:
            lines.append(f"  Error: {mas_result['error']}")
        else:
            lines.append(f"  Metrics found: {mas_result.get('num_metrics', 0)}")
            if "mas_score" in mas_result:
                lines.append(f"  MAS Score: {mas_result['mas_score']:.4f}")
    
    # 5. LLM Judge
    lines.append("\n## 5. LLM Judge (Code Faithfulness)")
    if judge_result:
        if "error" in judge_result:
            lines.append(f"  Error: {judge_result['error']}")
        else:
            lines.append(f"  Score: {judge_result.get('overall_score', 'N/A')}")
            if "dimensions" in judge_result:
                for dim, score in judge_result["dimensions"].items():
                    lines.append(f"    {dim}: {score}")
    
    # 6. Experience Extraction
    lines.append("\n## 6. Experience Extraction")
    if experience_result:
        if "error" in experience_result:
            lines.append(f"  Error: {experience_result['error']}")
        else:
            lines.append(f"  Experiences extracted: {experience_result.get('num_extracted', 0)}")
    
    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def evaluate_paper(paper_id: str, task_id: Optional[str] = None, 
                   skip_judge: bool = False, skip_experience: bool = False) -> Dict:
    """
    Full evaluation pipeline for a paper reproduction attempt.
    
    Args:
        paper_id: Paper identifier
        task_id: Specific task ID (if None, uses latest)
        skip_judge: Skip LLM Judge (saves API calls)
        skip_experience: Skip experience extraction
    """
    print(f"\n{'='*60}")
    print(f"[Eval] Starting evaluation for: {paper_id}")
    print(f"{'='*60}")
    
    # 1. Find result
    task_result = find_latest_result(paper_id)
    if not task_result:
        print(f"[Eval] No result found for {paper_id}")
        return {"error": "No result found"}
    
    print(f"[Eval] Found result: {task_result.get('_result_file')}")
    print(f"[Eval] Agent state: {task_result.get('agent_state')}, Success: {task_result.get('success')}")
    
    oh_result = find_latest_oh_result(paper_id)
    if oh_result:
        print(f"[Eval] OH result: {oh_result.get('_file')}")
    
    # 2. Determine workspace
    workspace = task_result.get("workspace", "")
    if oh_result and not workspace:
        workspace = oh_result.get("workspace", "")
    
    if not workspace:
        # Try to reconstruct from task_id
        tid = task_result.get("task_id", "")
        workspace = str(WORKSPACE_BASE / f"task_{tid}")
    
    print(f"[Eval] Workspace: {workspace}")
    
    # 3. Collect artifacts
    artifacts = collect_workspace_artifacts(workspace)
    print(f"[Eval] Artifacts: {artifacts.get('total_files', 0)} files, "
          f"reproduce.py={'✅' if artifacts.get('has_reproduce_py') else '❌'}, "
          f"results.json={'✅' if artifacts.get('has_results_json') else '❌'}")
    
    # 4. Extract metrics
    metrics = extract_metrics_from_workspace(workspace)
    if not metrics and artifacts.get("results_json"):
        metrics = {k: float(v) for k, v in artifacts["results_json"].items() 
                   if isinstance(v, (int, float))}
    print(f"[Eval] Metrics found: {len(metrics)}")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    # 5. MAS evaluation
    mas_result = run_mas_evaluation(paper_id, metrics)
    
    # 6. LLM Judge
    judge_result = None
    if not skip_judge and artifacts.get("has_reproduce_py"):
        judge_result = run_llm_judge(paper_id, workspace)
    elif not artifacts.get("has_reproduce_py"):
        judge_result = {"error": "No reproduce.py found - skipping judge"}
    
    # 7. Experience extraction
    experience_result = None
    traj_path = task_result.get("trajectory_path", "")
    task_success = task_result.get("success", False)
    if not skip_experience and traj_path:
        experience_result = trigger_experience_extraction(
            traj_path, paper_id, task_success=task_success)
    
    # 7b. Package sandbox (collect all artifacts into structured directory)
    try:
        from code.utils.sandbox_packager import package_sandbox
        sandbox_path = package_sandbox(
            paper_id=paper_id,
            workspace=workspace,
            task_id=task_result.get("task_id"),
            extra_metadata={
                "agent_state": task_result.get("agent_state"),
                "success": task_success,
                "metrics": metrics,
            },
        )
        print(f"[Eval] Sandbox packaged: {sandbox_path}")
    except Exception as e:
        print(f"[Eval] Sandbox packaging failed (non-fatal): {e}")
    
    # 8. Generate report
    report = generate_report(
        paper_id, task_result, oh_result, artifacts, 
        metrics, mas_result, judge_result, experience_result
    )
    print(report)
    
    # Save report
    report_file = RESULTS_DIR / paper_id / f"evaluation_report.txt"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report, encoding="utf-8")
    print(f"\n[Eval] Report saved: {report_file}")
    
    # Save structured results
    eval_data = {
        "paper_id": paper_id,
        "task_result": task_result,
        "oh_result": oh_result,
        "artifacts": artifacts,
        "metrics": metrics,
        "mas_result": mas_result,
        "judge_result": judge_result,
        "experience_result": experience_result,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    eval_file = RESULTS_DIR / paper_id / f"evaluation_data.json"
    with open(eval_file, "w") as f:
        json.dump(eval_data, f, indent=2, default=str)
    
    return eval_data


def scan_all_results():
    """Scan and report on all reproduction results."""
    if not RESULTS_DIR.exists():
        print("No results directory found")
        return
    
    papers = [d.name for d in RESULTS_DIR.iterdir() if d.is_dir()]
    if not papers:
        print("No results found")
        return
    
    print(f"\n{'='*70}")
    print(f"  ALL REPRODUCTION RESULTS")
    print(f"{'='*70}")
    print(f"{'Paper':<20} {'State':<15} {'Success':<10} {'Iters':<8} {'Duration':<10} {'Metrics'}")
    print("-" * 80)
    
    for paper_id in sorted(papers):
        result = find_latest_result(paper_id)
        if result:
            state = result.get("agent_state", "?")[:12]
            success = "✅" if result.get("success") else "❌"
            iters = result.get("iterations_used", -1)
            dur = f"{result.get('duration_seconds', 0):.0f}s"
            metrics = result.get("metrics_reproduced", {})
            metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items()) if metrics else "none"
            print(f"{paper_id:<20} {state:<15} {success:<10} {iters:<8} {dur:<10} {metric_str}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate reproduction results")
    parser.add_argument("--paper_id", type=str, help="Paper ID to evaluate")
    parser.add_argument("--task_id", type=str, help="Specific task ID")
    parser.add_argument("--scan", action="store_true", help="Scan all results")
    parser.add_argument("--skip-judge", action="store_true", help="Skip LLM Judge")
    parser.add_argument("--skip-experience", action="store_true", help="Skip experience extraction")
    
    args = parser.parse_args()
    
    if args.scan:
        scan_all_results()
    elif args.paper_id:
        evaluate_paper(args.paper_id, args.task_id, 
                      skip_judge=args.skip_judge,
                      skip_experience=args.skip_experience)
    else:
        parser.print_help()
