#!/usr/bin/env python3
"""
Phase B1: Test Set Baseline Runner (NO experience injection).

Runs baseline on Test Set papers using the SAME prompt template and config
as the Training Set. This is the CONTROL GROUP for the experience experiment.

Usage:
  python scripts/run_test_baseline.py                    # Run all 5 test papers
  python scripts/run_test_baseline.py --paper fpm_inr    # Run specific paper
  python scripts/run_test_baseline.py --dry-run           # Check config only
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

RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v5" / "test_b1"
PROMPTS_DIR = PROJECT_ROOT / "data" / "agent_prompts_v5" / "test_b1"
LOGS_DIR = PROJECT_ROOT / "logs" / "run_logs"
WORKSPACE_BASE = Path("/home/yjh/openhands_workspace_v5")
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
CLEANUP_SCRIPT = PROJECT_ROOT / "code" / "utils" / "sandbox_cleanup.sh"

MAX_ITERATIONS = 100
MAX_WAIT_SECONDS = 5400  # 90 min per paper

# Test Set papers (NEVER seen during training)
TEST_PAPERS = {
    "fpm_inr":    {"tier": 2, "domain": "computational_imaging"},
    "lensless":   {"tier": 2, "domain": "computational_imaging"},
    "lfm":        {"tier": 2, "domain": "computational_imaging"},
    "sparse_sim": {"tier": 3, "domain": "computational_imaging"},
    "flfm":       {"tier": 3, "domain": "computational_imaging"},
}

# Same prompt template as training (NO experience)
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
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **data
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cleanup_sandbox():
    if CLEANUP_SCRIPT.exists():
        subprocess.run(["bash", str(CLEANUP_SCRIPT)],
                       capture_output=True, timeout=30)
    # Also kill stale processes
    subprocess.run("pkill -f jupyter-kernelgateway 2>/dev/null; tmux kill-server 2>/dev/null",
                   shell=True, capture_output=True)
    time.sleep(3)


def generate_prompt(paper_id: str) -> Path:
    md_path = PAPER_MARKDOWN_DIR / f"{paper_id}_full.md"
    paper_content = md_path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(
        paper_content=paper_content,
        max_iterations=MAX_ITERATIONS,
    )
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{paper_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file


def run_paper(paper_id: str, info: dict, log_file: Path) -> dict:
    print(f"\n{'='*60}")
    print(f"  RUNNING: {paper_id} (Tier {info['tier']}, {info['domain']})")
    print(f"  Phase: B1 (Test Set, NO experience)")
    print(f"{'='*60}")

    # Generate prompt
    prompt_file = generate_prompt(paper_id)
    print(f"  Prompt: {prompt_file} ({prompt_file.stat().st_size} bytes)")

    # Setup workspace
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"test_b1_{paper_id}_{ts}"
    workspace = WORKSPACE_BASE / session_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Setup result file
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_file = RESULTS_DIR / f"{paper_id}_result.json"

    # Setup stdout log
    stdout_dir = PROJECT_ROOT / "logs" / "run_logs"
    stdout_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = stdout_dir / f"test_b1_{paper_id}_{ts}.log"

    log_event(log_file, "launch", {
        "paper": paper_id, "session": session_name,
        "workspace": str(workspace), "prompt_file": str(prompt_file)
    })

    # Launch OpenHands
    cmd = [
        OPENHANDS_PYTHON, str(OPENHANDS_LAUNCHER),
        "--prompt-file", str(prompt_file),
        "--workspace", str(workspace),
        "--session-name", session_name,
        "--max-iterations", str(MAX_ITERATIONS),
        "--config", str(OPENHANDS_CONFIG),
        "--output-file", str(result_file),
    ]

    print(f"  Launching: {' '.join(cmd[:4])}...")
    print(f"  Log: {stdout_log}")

    log_f = open(stdout_log, "w")
    start_time = time.time()
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    # Monitor
    last_check = time.time()
    while proc.poll() is None:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_SECONDS:
            print(f"  ⏰ Timeout after {MAX_WAIT_SECONDS}s, killing...")
            proc.kill()
            proc.wait(timeout=30)
            break

        if time.time() - last_check > 120:
            files = [f.name for f in workspace.iterdir() if f.is_file()] if workspace.exists() else []
            print(f"  [{int(elapsed/60)}m] Workspace: {', '.join(files[:8])}")
            last_check = time.time()

        time.sleep(5)

    log_f.close()
    elapsed = time.time() - start_time

    # Count LLM calls
    llm_dir = PROJECT_ROOT / "logs" / "llm_completions"
    llm_calls = len(list(llm_dir.glob("*.json"))) if llm_dir.exists() else 0

    # Read result
    result = {"agent_state": "UNKNOWN", "has_results_json": False}
    if result_file.exists():
        try:
            with open(result_file) as f:
                result = json.load(f)
        except:
            pass

    # Check workspace for results.json
    ws_results = workspace / "results.json"
    has_results = ws_results.exists()

    state = result.get("agent_state", "UNKNOWN")
    print(f"\n  Result: {state} ({elapsed:.0f}s)")
    print(f"  LLM calls: {llm_calls}")
    print(f"  Has results.json: {has_results}")

    # Update result file
    result.update({
        "session_name": session_name,
        "elapsed_seconds": elapsed,
        "llm_calls": llm_calls,
        "workspace": str(workspace),
        "has_results_json": has_results,
        "phase": "B1_test_no_experience",
    })
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    log_event(log_file, "complete", {
        "paper": paper_id, "state": state,
        "elapsed": elapsed, "llm_calls": llm_calls,
        "has_results": has_results
    })

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", nargs="*", help="Specific paper(s) to run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    papers = {}
    if args.paper:
        for p in args.paper:
            if p in TEST_PAPERS:
                papers[p] = TEST_PAPERS[p]
            else:
                print(f"Unknown test paper: {p}")
                sys.exit(1)
    else:
        papers = TEST_PAPERS

    print(f"Phase B1: Test Set Baseline (NO experience)")
    print(f"Papers: {list(papers.keys())}")
    print(f"Config: {OPENHANDS_CONFIG}")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print(f"Max wait: {MAX_WAIT_SECONDS}s")

    if args.dry_run:
        for pid in papers:
            prompt = generate_prompt(pid)
            print(f"  {pid}: prompt={prompt.stat().st_size} bytes")
        return

    # Run log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"test_b1_{ts}.jsonl"

    results = {}
    for pid, info in papers.items():
        cleanup_sandbox()
        time.sleep(5)
        result = run_paper(pid, info, log_file)
        results[pid] = result.get("agent_state", "UNKNOWN")

    # Summary
    print(f"\n{'='*60}")
    print(f"PHASE B1 SUMMARY (Test Set, NO experience)")
    print(f"{'='*60}")
    for pid, state in results.items():
        s = "✅" if "FINISHED" in state else "❌"
        print(f"  {pid:15s} {state:30s} {s}")

    success = sum(1 for s in results.values() if "FINISHED" in s)
    print(f"\nSuccess: {success}/{len(results)} ({100*success/len(results):.0f}%)")

    # Save summary
    summary = {
        "phase": "B1_test_no_experience",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "success_rate": f"{success}/{len(results)}"
    }
    summary_file = RESULTS_DIR / "b1_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    main()
