#!/usr/bin/env python3
"""
Phase A: Training Set Baseline Runner with Comprehensive Logging.

Runs baseline (no experience) on Training Set papers.
Saves structured logs: per-iteration actions, LLM calls, results.

Usage:
  # Run all new Training papers (Tier 2/3)
  python scripts/run_training_baseline.py

  # Run specific paper
  python scripts/run_training_baseline.py --paper oopao

  # Dry run (check config, don't launch)
  python scripts/run_training_baseline.py --dry-run

  # Check status of all runs
  python scripts/run_training_baseline.py --status
"""

import argparse
import json
import os
import subprocess
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
sys.path.insert(0, str(PROJECT_ROOT))

OPENHANDS_DIR = Path("/home/yjh/OpenHands")
OPENHANDS_PYTHON = "/home/yjh/local_openhands_env/bin/python3"
OPENHANDS_CONFIG = OPENHANDS_DIR / "config.toml"
OPENHANDS_LAUNCHER = OPENHANDS_DIR / "run_evolution_task.py"

RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v5"
PROMPTS_DIR = PROJECT_ROOT / "data" / "agent_prompts_v5"
LOGS_DIR = PROJECT_ROOT / "logs"
RUN_LOGS_DIR = LOGS_DIR / "run_logs"
LLM_LOGS_DIR = LOGS_DIR / "llm_completions"
WORKSPACE_BASE = Path("/home/yjh/openhands_workspace_v5")
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
CLEANUP_SCRIPT = PROJECT_ROOT / "code" / "utils" / "sandbox_cleanup.sh"
TRAJECTORY_DIR = Path("/data/yjh/openhands_results_v2/trajectories")

MAX_ITERATIONS = 100
MAX_WAIT_SECONDS = 5400  # 90 min per paper

# Training Set papers to run (new ones that don't have baseline data yet)
TRAINING_NEW = {
    "oopao":       {"tier": 2, "domain": "adaptive_optics"},
    "lenstronomy": {"tier": 2, "domain": "astrophysics"},
    "pnp_cassi":   {"tier": 2, "domain": "computational_imaging"},
    "dpi":         {"tier": 3, "domain": "scientific_computing"},
    "ptyrad":      {"tier": 3, "domain": "computational_imaging"},
}

# Already have baseline data from V3
TRAINING_EXISTING = {
    "pyeit": {"tier": 1, "domain": "biomedical_imaging", "status": "success"},
    "pat":   {"tier": 1, "domain": "biomedical_imaging", "status": "success"},
    "insar": {"tier": 1, "domain": "remote_sensing", "status": "success"},
    "bpm":   {"tier": 1, "domain": "computational_optics", "status": "failed"},
    "diff":  {"tier": 1, "domain": "computational_optics", "status": "failed_v3_success_v4"},
}

# Baseline prompt template (NO experience injection)
PROMPT_TEMPLATE = """You are a professional academic paper reproduction Agent. Your goal is to read the following academic paper and reproduce its key experimental results from scratch using Python.

You are working in a CLEAN EMPTY directory. There are NO pre-prepared datasets, NO starter code, NO reference implementations. You must do EVERYTHING from scratch based solely on the paper content below.

=== PAPER CONTENT START ===
{paper_content}
=== PAPER CONTENT END ===

=== YOUR MISSION ===
1. Read and understand the paper's methodology, algorithms, and experimental setup
2. Write a structured Reproduction Plan (checklist) BEFORE writing any code
3. Implement the necessary code from scratch
4. Generate or simulate the required input data (since you have no pre-existing datasets)
5. Run the experiment and produce quantitative results
6. Compare your results against the paper's reported values
7. Save all results to results.json in the working directory

=== MANDATORY RULES ===
RULE 1 — REPRODUCTION PLAN FIRST: Before writing ANY code, output a structured reproduction plan with verifiable steps.
RULE 2 — TOY-FIRST PRINCIPLE: Always create a MINIMAL toy test first to verify code correctness before running full-scale experiments.
RULE 3 — SANITY CHECK: After every execution, verify no NaN/Inf, reasonable shapes/ranges. If metric deviates >10x from paper, treat as SILENT BUG.
RULE 4 — FILE PERSISTENCE: Use `cat > file.py << 'PYEOF'` pattern for multi-line files. Do NOT use execute_ipython_cell for important code.
RULE 5 — RESULTS FORMAT: Save results.json with {{paper_title, reproduction_status, metrics, notes, files_produced}}.
RULE 6 — BUDGET AWARENESS: You have ~{max_iterations} iterations. At 70% budget, wrap up and produce whatever results you have.
RULE 7 — NO CHEATING: Do NOT hardcode expected results. Your code must actually perform the algorithm.
RULE 8 — RESOLUTION MATCHING: When the paper specifies grid/image resolution, match it as closely as possible.
RULE 9 — AVOID IPYTHON: Write all code to .py files using bash heredoc, then run with python.

=== BEGIN REPRODUCTION ===
Start by reading the paper carefully and creating your reproduction plan."""


def log_event(log_file: Path, event_type: str, data: dict):
    """Append a structured event to the run log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **data
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def generate_prompt(paper_id: str) -> Path:
    """Generate baseline prompt (no experience) for a paper."""
    md_path = PAPER_MARKDOWN_DIR / f"{paper_id}_full.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Paper markdown not found: {md_path}")

    paper_content = md_path.read_text(encoding="utf-8")

    prompt = PROMPT_TEMPLATE.format(
        paper_content=paper_content,
        max_iterations=MAX_ITERATIONS,
    )

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{paper_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file, len(paper_content), len(prompt)


def cleanup_sandbox():
    """Clean up sandbox processes before launching."""
    if CLEANUP_SCRIPT.exists():
        try:
            subprocess.run(["bash", str(CLEANUP_SCRIPT)],
                           capture_output=True, timeout=30)
        except Exception:
            pass
    # Also kill stale processes
    for cmd in ["pkill -f jupyter-kernelgateway",
                "pkill -f action_execution_server",
                "tmux kill-server"]:
        try:
            subprocess.run(cmd.split(), capture_output=True, timeout=5)
        except Exception:
            pass
    time.sleep(3)


def launch_paper(paper_id: str, info: dict, run_log: Path) -> dict:
    """Launch a single paper reproduction and wait for completion."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"v5_{paper_id}_{timestamp}"

    # Create workspace
    workspace = WORKSPACE_BASE / session_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Generate prompt
    prompt_file, paper_chars, prompt_chars = generate_prompt(paper_id)

    # Output file
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f"{paper_id}_result.json"

    log_event(run_log, "LAUNCH", {
        "paper_id": paper_id,
        "session": session_name,
        "tier": info["tier"],
        "domain": info["domain"],
        "paper_chars": paper_chars,
        "prompt_chars": prompt_chars,
        "prompt_file": str(prompt_file),
        "workspace": str(workspace),
        "output_file": str(output_file),
        "max_iterations": MAX_ITERATIONS,
    })

    # Build command
    cmd = [
        OPENHANDS_PYTHON,
        str(OPENHANDS_LAUNCHER),
        "--prompt-file", str(prompt_file),
        "--workspace", str(workspace),
        "--session-name", session_name,
        "--max-iterations", str(MAX_ITERATIONS),
        "--config", str(OPENHANDS_CONFIG),
        "--output-file", str(output_file),
    ]

    # Launch with stdout/stderr capture
    stdout_log = RUN_LOGS_DIR / f"{session_name}.log"
    RUN_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Launching: {' '.join(str(c) for c in cmd[:4])}...")
    print(f"  Log: {stdout_log}")

    log_f = open(stdout_log, "w")
    proc = subprocess.Popen(
        [str(c) for c in cmd],
        stdout=log_f,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(OPENHANDS_DIR),
    )

    log_event(run_log, "PROCESS_STARTED", {
        "paper_id": paper_id,
        "pid": proc.pid,
        "stdout_log": str(stdout_log),
    })

    # Wait for completion with heartbeat monitoring
    start_time = time.time()
    last_workspace_check = ""

    while True:
        elapsed = time.time() - start_time

        # Check if process ended
        ret = proc.poll()
        if ret is not None:
            log_event(run_log, "PROCESS_ENDED", {
                "paper_id": paper_id,
                "exit_code": ret,
                "elapsed_seconds": elapsed,
            })
            break

        # Timeout check
        if elapsed > MAX_WAIT_SECONDS:
            print(f"  ⏰ Timeout after {elapsed:.0f}s, killing...")
            proc.kill()
            proc.wait(timeout=10)
            log_event(run_log, "TIMEOUT", {
                "paper_id": paper_id,
                "elapsed_seconds": elapsed,
            })
            break

        # Heartbeat every 2 minutes
        if int(elapsed) % 120 < 5:
            ws_files = list(workspace.glob("*")) if workspace.exists() else []
            ws_summary = ", ".join(f.name for f in ws_files if not f.name.startswith("."))
            if ws_summary != last_workspace_check:
                print(f"  [{elapsed/60:.0f}m] Workspace: {ws_summary or '(empty)'}")
                log_event(run_log, "HEARTBEAT", {
                    "paper_id": paper_id,
                    "elapsed_minutes": elapsed / 60,
                    "workspace_files": ws_summary,
                })
                last_workspace_check = ws_summary

        time.sleep(5)

    # Close log file handle
    try:
        log_f.close()
    except Exception:
        pass

    # Collect results
    elapsed = time.time() - start_time
    result = {
        "paper_id": paper_id,
        "session": session_name,
        "elapsed_seconds": elapsed,
        "workspace": str(workspace),
    }

    # Read output file if it exists
    if output_file.exists():
        try:
            with open(output_file) as f:
                oh_result = json.load(f)
            result["agent_state"] = oh_result.get("agent_state", "unknown")
            result["has_results_json"] = oh_result.get("has_results_json", False)
            result["iterations_used"] = oh_result.get("iterations_used", 0)
            result["error"] = oh_result.get("error")
        except Exception as e:
            result["agent_state"] = "PARSE_ERROR"
            result["error"] = str(e)
    else:
        result["agent_state"] = "NO_OUTPUT"
        result["error"] = "Output file not created"

    # Check workspace for results.json
    ws_results = workspace / "results.json"
    if ws_results.exists():
        try:
            with open(ws_results) as f:
                ws_data = json.load(f)
            result["reproduction_status"] = ws_data.get("reproduction_status", "unknown")
            result["metrics"] = ws_data.get("metrics", {})
        except Exception:
            pass

    # Find trajectory
    traj_files = sorted(TRAJECTORY_DIR.glob(f"{session_name}*"))
    if traj_files:
        result["trajectory_file"] = str(traj_files[-1])
        # Count events in trajectory
        try:
            with open(traj_files[-1]) as f:
                traj = json.load(f)
            result["trajectory_events"] = len(traj)
        except Exception:
            pass

    # Count LLM completion logs for this session
    llm_logs = list(LLM_LOGS_DIR.glob("*.json"))
    # Filter by timestamp (approximate)
    result["llm_completion_logs"] = len(llm_logs)

    log_event(run_log, "RESULT", result)

    return result


def show_status():
    """Show status of all runs."""
    print("\n=== Training Set Baseline Status ===\n")

    all_papers = {**TRAINING_EXISTING, **TRAINING_NEW}

    for paper_id, info in sorted(all_papers.items()):
        result_file = RESULTS_DIR / f"{paper_id}_result.json"
        if result_file.exists():
            try:
                with open(result_file) as f:
                    r = json.load(f)
                state = r.get("agent_state", "?")
                has_results = r.get("has_results_json", False)
                elapsed = r.get("elapsed_seconds", 0)
                print(f"  {paper_id:<15} Tier {info['tier']}  {state:<25} results={has_results}  {elapsed:.0f}s")
            except Exception:
                print(f"  {paper_id:<15} Tier {info['tier']}  (parse error)")
        else:
            existing = info.get("status", "not_run")
            print(f"  {paper_id:<15} Tier {info['tier']}  {existing}")


def main():
    parser = argparse.ArgumentParser(description="Phase A: Training Set Baseline Runner")
    parser.add_argument("--paper", type=str, nargs="+", help="Run specific paper(s)")
    parser.add_argument("--dry-run", action="store_true", help="Check config, don't launch")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--all-new", action="store_true", help="Run all new Training papers")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Determine which papers to run
    if args.paper:
        papers_to_run = {}
        for p in args.paper:
            info = TRAINING_NEW.get(p, TRAINING_EXISTING.get(p))
            if info is None:
                print(f"Unknown paper: {p}")
                print(f"Available: {list(TRAINING_NEW.keys()) + list(TRAINING_EXISTING.keys())}")
                sys.exit(1)
            papers_to_run[p] = info
    else:
        papers_to_run = TRAINING_NEW

    # Create run log
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log = RUN_LOGS_DIR / f"training_baseline_{run_timestamp}.jsonl"
    RUN_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Phase A: Training Set Baseline Runner")
    print(f"{'='*60}")
    print(f"Papers to run: {list(papers_to_run.keys())}")
    print(f"Model: global.anthropic.claude-opus-4-6-v1")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print(f"Run log: {run_log}")
    print(f"Results dir: {RESULTS_DIR}")
    print(f"LLM logs: {LLM_LOGS_DIR}")
    print(f"{'='*60}\n")

    log_event(run_log, "RUN_START", {
        "papers": list(papers_to_run.keys()),
        "model": "global.anthropic.claude-opus-4-6-v1",
        "max_iterations": MAX_ITERATIONS,
    })

    if args.dry_run:
        print("DRY RUN — checking prompts only:\n")
        for paper_id, info in papers_to_run.items():
            try:
                prompt_file, paper_chars, prompt_chars = generate_prompt(paper_id)
                print(f"  {paper_id}: paper={paper_chars} chars, prompt={prompt_chars} chars → {prompt_file}")
            except Exception as e:
                print(f"  {paper_id}: ERROR — {e}")
        return

    # Run papers sequentially
    results = {}
    for i, (paper_id, info) in enumerate(papers_to_run.items(), 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(papers_to_run)}] Running: {paper_id} (Tier {info['tier']}, {info['domain']})")
        print(f"{'='*60}")

        # Cleanup before each run
        print("  Cleaning up sandbox...")
        cleanup_sandbox()

        # Clear LLM completion logs for this run (to count per-paper)
        llm_before = set(LLM_LOGS_DIR.glob("*.json")) if LLM_LOGS_DIR.exists() else set()

        try:
            result = launch_paper(paper_id, info, run_log)
            results[paper_id] = result

            # Count new LLM logs
            llm_after = set(LLM_LOGS_DIR.glob("*.json")) if LLM_LOGS_DIR.exists() else set()
            new_llm_logs = llm_after - llm_before
            result["llm_calls_this_paper"] = len(new_llm_logs)

            # Move LLM logs to per-paper directory
            paper_llm_dir = LLM_LOGS_DIR / paper_id
            paper_llm_dir.mkdir(exist_ok=True)
            for log_file in new_llm_logs:
                try:
                    shutil.move(str(log_file), str(paper_llm_dir / log_file.name))
                except Exception:
                    pass

            state = result.get("agent_state", "?")
            elapsed = result.get("elapsed_seconds", 0)
            print(f"\n  Result: {state} ({elapsed:.0f}s)")
            print(f"  LLM calls: {len(new_llm_logs)}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[paper_id] = {"error": str(e)}
            log_event(run_log, "ERROR", {"paper_id": paper_id, "error": str(e)})

        # Brief pause between papers
        if i < len(papers_to_run):
            print(f"\n  Waiting 10s before next paper...")
            time.sleep(10)

    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")

    summary = {
        "version": "v5_training_baseline",
        "timestamp": datetime.now().isoformat(),
        "model": "global.anthropic.claude-opus-4-6-v1",
        "papers": {}
    }

    for paper_id, result in results.items():
        state = result.get("agent_state", "?")
        has_results = result.get("has_results_json", False)
        elapsed = result.get("elapsed_seconds", 0)
        llm_calls = result.get("llm_calls_this_paper", 0)
        print(f"  {paper_id:<15} {state:<25} results={has_results}  {elapsed:.0f}s  llm_calls={llm_calls}")
        summary["papers"][paper_id] = {
            "state": state,
            "has_results": has_results,
            "elapsed_seconds": elapsed,
            "llm_calls": llm_calls,
        }

    # Save summary
    summary_file = RESULTS_DIR / "v5_training_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to: {summary_file}")
    print(f"Run log: {run_log}")

    log_event(run_log, "RUN_COMPLETE", {"summary": summary})


if __name__ == "__main__":
    main()
