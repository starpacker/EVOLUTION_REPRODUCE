#!/usr/bin/env python3
"""
V4 Experience-Enhanced Re-run Script.

Re-runs failed/all Tier 1 papers with experience injection from the Experience DB.
This is the key experiment: V3 (no experience) vs V4 (with experience).

Usage:
  # Re-run only failed papers (bpm, diff)
  python scripts/run_v4_tier1.py --failed-only

  # Re-run all Tier 1 papers
  python scripts/run_v4_tier1.py --all

  # Dry run (print prompts, don't launch)
  python scripts/run_v4_tier1.py --failed-only --dry-run

  # Check status
  python scripts/run_v4_tier1.py --status
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
sys.path.insert(0, str(PROJECT_ROOT))

OPENHANDS_DIR = Path("/home/yjh/OpenHands")
OPENHANDS_PYTHON = "/home/yjh/local_openhands_env/bin/python3"
OPENHANDS_CONFIG = OPENHANDS_DIR / "config.toml"
OPENHANDS_LAUNCHER = OPENHANDS_DIR / "run_evolution_task.py"

RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v4"
PROMPTS_DIR = PROJECT_ROOT / "data" / "agent_prompts_v4"
LOGS_DIR = PROJECT_ROOT / "logs" / "sandbox_stdout"
WORKSPACE_BASE = Path("/home/yjh/openhands_workspace_v4")
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
CLEANUP_SCRIPT = PROJECT_ROOT / "code" / "utils" / "sandbox_cleanup.sh"

MAX_ITERATIONS = 100
MAX_WAIT_SECONDS = 5400  # 90 min

# Papers and their V3 status
TIER1_PAPERS = {
    "pyeit": {"domain": "biomedical_imaging", "v3_success": True},
    "pat": {"domain": "biomedical_imaging", "v3_success": True},
    "insar": {"domain": "remote_sensing", "v3_success": True},
    "bpm": {"domain": "computational_optics", "v3_success": False},
    "diff": {"domain": "computational_optics", "v3_success": False},
}

# Enhanced prompt template with experience injection
PROMPT_TEMPLATE = """You are a professional academic paper reproduction Agent. Your goal is to read the following academic paper and reproduce its key experimental results from scratch using Python.

You are working in a CLEAN EMPTY directory. There are NO pre-prepared datasets, NO starter code, NO reference implementations. You must do EVERYTHING from scratch based solely on the paper content below.

{experience_section}

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
RULE 8 — RESOLUTION MATCHING: When the paper specifies grid/image resolution, match it as closely as possible. Using lower resolution can cause catastrophic quality loss.
RULE 9 — AVOID IPYTHON: Write all code to .py files using bash heredoc, then run with python. This prevents tool call format errors.

=== BEGIN REPRODUCTION ===
Start by reading the paper carefully and creating your reproduction plan."""


def get_experience_section(paper_id: str, paper_content: str, domain: str) -> str:
    """Retrieve relevant experiences from the DB and format for injection."""
    try:
        from code.experience_db.experience_db import ExperienceDB
        db = ExperienceDB()

        if db.count() == 0:
            print(f"  Experience DB is empty, no injection")
            return ""

        # Build query from paper content
        snippet = paper_content[:2000]
        query = (
            f"[Domain]: {domain}\n"
            f"[Task Context]: Reproducing a paper from scratch. "
            f"Planning phase — looking for common pitfalls and strategies.\n"
            f"[Paper excerpt]: {snippet}\n"
        )

        # Retrieve with relaxed settings (early exploration)
        results = db.retrieve(query, max_inject=3, exploration_ratio=0.9)

        if not results:
            # Fallback: try stage1 only with lower threshold
            results = db.search_stage1(query, top_k=5, min_sim=0.5)
            if results:
                # Take top 3
                results = results[:3]

        if not results:
            print(f"  No relevant experiences found")
            return ""

        # Format experiences
        parts = []
        for i, item in enumerate(results, 1):
            exp = item.get("experience")
            if exp is None:
                continue

            relevance = item.get("relevance", "RELEVANT")
            block = f"Experience #{i}"
            if relevance == "PARTIAL":
                block += " (partial match — use as inspiration only)"

            if exp.type == "negative":
                block += f" ⚠️ KNOWN FAILURE"
                block += f"\n  WARNING: The following approach has been verified as INEFFECTIVE:"
                block += f"\n  Problem: {exp.condition.get('error_or_symptom', 'N/A')}"
                block += f"\n  Failed approach: {exp.action.get('solution', 'N/A')}"
            else:
                block += f"\n  Context: {exp.condition.get('task_context', 'N/A')}"
                block += f"\n  Strategy: {exp.action.get('solution', 'N/A')}"
                code = exp.action.get("code_implement")
                if code and len(code.strip()) > 0:
                    block += f"\n  Key code hint:\n    {code.strip()}"

            parts.append(block)
            print(f"  Injecting experience: {exp.id} ({exp.type})")

        if not parts:
            return ""

        return (
            "=== RELEVANT EXPERIENCE FROM PRIOR TASKS ===\n"
            "The following experience(s) were retrieved from solved problems in previous\n"
            "paper reproduction tasks. They MAY be relevant to your current task.\n"
            "Use them as hints, but verify their applicability before applying blindly.\n\n"
            + "\n\n".join(parts) +
            "\n\n=== END OF EXPERIENCE ===\n"
        )

    except Exception as e:
        print(f"  ⚠️ Experience retrieval failed: {e}")
        return ""


def generate_prompt(paper_id: str, domain: str) -> Path:
    """Generate experience-enhanced prompt for a paper."""
    md_path = PAPER_MARKDOWN_DIR / f"{paper_id}_full.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Paper markdown not found: {md_path}")

    paper_content = md_path.read_text(encoding="utf-8")
    print(f"  Paper: {md_path.name} ({len(paper_content)} chars)")

    # Get experience section
    print(f"  Querying Experience DB...")
    experience_section = get_experience_section(paper_id, paper_content, domain)

    prompt = PROMPT_TEMPLATE.format(
        paper_content=paper_content,
        max_iterations=MAX_ITERATIONS,
        experience_section=experience_section,
    )

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{paper_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"  Prompt: {prompt_file} ({len(prompt)} chars)")
    return prompt_file


def cleanup_sandbox():
    """Clean up sandbox processes before launching."""
    if CLEANUP_SCRIPT.exists():
        try:
            subprocess.run(["bash", str(CLEANUP_SCRIPT)],
                           capture_output=True, timeout=30)
        except Exception:
            pass
    time.sleep(3)


def launch_paper(paper_id: str, prompt_file: Path) -> dict:
    """Launch OpenHands for a single paper and wait for completion."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_name = f"v4_{paper_id}_{ts}"
    workspace = WORKSPACE_BASE / session_name
    output_file = RESULTS_DIR / f"{paper_id}_result.json"
    log_file = LOGS_DIR / f"v4_{paper_id}.log"

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        OPENHANDS_PYTHON, str(OPENHANDS_LAUNCHER),
        "--prompt-file", str(prompt_file),
        "--workspace", str(workspace),
        "--session-name", session_name,
        "--max-iterations", str(MAX_ITERATIONS),
        "--config", str(OPENHANDS_CONFIG),
        "--output-file", str(output_file),
    ]

    print(f"\n  Launching: {session_name}")
    print(f"  Workspace: {workspace}")
    print(f"  Log: {log_file}")

    with open(log_file, 'w') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)

    print(f"  PID: {proc.pid}")

    # Wait for completion
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time

        # Check if result file has final state
        if output_file.exists():
            try:
                data = json.loads(output_file.read_text())
                state = data.get("agent_state", "")
                if any(s in state for s in ["FINISHED", "ERROR", "STOPPED"]):
                    print(f"  ✅ Completed: state={state} ({elapsed:.0f}s)")
                    return data
            except Exception:
                pass

        # Check if process is still running
        if proc.poll() is not None and elapsed > 60:
            if output_file.exists():
                try:
                    return json.loads(output_file.read_text())
                except Exception:
                    pass
            print(f"  ❌ Process died without result ({elapsed:.0f}s)")
            return {"agent_state": "PROCESS_DIED", "error": "Process exited without result"}

        # Timeout
        if elapsed > MAX_WAIT_SECONDS:
            print(f"  ⏰ Timeout after {elapsed:.0f}s, killing...")
            proc.kill()
            time.sleep(5)
            return {"agent_state": "TIMEOUT", "error": f"Timed out after {elapsed:.0f}s"}

        # Progress report every 2 minutes
        if int(elapsed) % 120 == 0 and elapsed > 0:
            log_size = log_file.stat().st_size if log_file.exists() else 0
            print(f"  ⏳ {elapsed:.0f}s elapsed, log={log_size:,} bytes")

        time.sleep(15)


def check_status():
    """Check status of V4 results."""
    print(f"\n{'='*60}")
    print(f"V4 STATUS — {datetime.now().isoformat()}")
    print(f"{'='*60}")

    if not RESULTS_DIR.exists():
        print("No V4 results yet")
        return

    for rf in sorted(RESULTS_DIR.glob("*_result.json")):
        try:
            data = json.loads(rf.read_text())
            state = data.get("agent_state", "?")
            elapsed = data.get("elapsed_seconds", "?")
            has_results = data.get("has_results_json", False)
            pid = rf.stem.replace("_result", "")
            print(f"  {pid}: {state} | {elapsed}s | results.json={'✅' if has_results else '❌'}")
        except Exception as e:
            print(f"  {rf.name}: ⚠️ {e}")

    # Compare V3 vs V4
    v3_dir = PROJECT_ROOT / "data" / "reproduction_results_v3"
    if v3_dir.exists():
        print(f"\n  V3 vs V4 Comparison:")
        for paper_id in TIER1_PAPERS:
            v3_file = v3_dir / f"{paper_id}_result.json"
            v4_file = RESULTS_DIR / f"{paper_id}_result.json"
            v3_state = "N/A"
            v4_state = "N/A"
            if v3_file.exists():
                try:
                    v3_state = json.loads(v3_file.read_text()).get("agent_state", "?")
                except Exception:
                    pass
            if v4_file.exists():
                try:
                    v4_state = json.loads(v4_file.read_text()).get("agent_state", "?")
                except Exception:
                    pass
            v3_ok = "FINISHED" in str(v3_state)
            v4_ok = "FINISHED" in str(v4_state)
            print(f"    {paper_id}: V3={'✅' if v3_ok else '❌'} → V4={'✅' if v4_ok else '❌' if v4_state != 'N/A' else '⏳'}")


def main():
    parser = argparse.ArgumentParser(description="V4 Experience-Enhanced Re-run")
    parser.add_argument("--failed-only", action="store_true",
                        help="Only re-run papers that failed in V3")
    parser.add_argument("--all", action="store_true",
                        help="Re-run all Tier 1 papers")
    parser.add_argument("--papers", nargs="+",
                        help="Specific paper IDs to run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate prompts but don't launch")
    parser.add_argument("--status", action="store_true",
                        help="Check status of V4 runs")
    args = parser.parse_args()

    if args.status:
        check_status()
        return

    # Determine which papers to run
    if args.papers:
        papers_to_run = {p: TIER1_PAPERS[p] for p in args.papers if p in TIER1_PAPERS}
    elif args.failed_only:
        papers_to_run = {p: info for p, info in TIER1_PAPERS.items() if not info["v3_success"]}
    elif args.all:
        papers_to_run = TIER1_PAPERS
    else:
        # Default: failed only
        papers_to_run = {p: info for p, info in TIER1_PAPERS.items() if not info["v3_success"]}

    if not papers_to_run:
        print("No papers to run")
        return

    print(f"\n{'='*60}")
    print(f"  V4 Experience-Enhanced Tier 1 Launch")
    print(f"  Papers: {list(papers_to_run.keys())}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"{'='*60}")

    results = {}
    for paper_id, info in papers_to_run.items():
        print(f"\n{'='*60}")
        print(f"  Paper: {paper_id} (V3: {'✅' if info['v3_success'] else '❌'})")
        print(f"{'='*60}")

        # Generate prompt with experience injection
        try:
            prompt_file = generate_prompt(paper_id, info["domain"])
        except Exception as e:
            print(f"  ❌ Prompt generation failed: {e}")
            results[paper_id] = {"error": str(e)}
            continue

        if args.dry_run:
            print(f"  [DRY RUN] Would launch with prompt: {prompt_file}")
            results[paper_id] = {"status": "dry_run", "prompt_file": str(prompt_file)}
            continue

        # Cleanup before launch
        print(f"  Cleaning sandbox...")
        cleanup_sandbox()

        # Launch and wait
        result = launch_paper(paper_id, prompt_file)
        results[paper_id] = result

        # Copy outputs to local folder
        if result.get("workspace"):
            ws = Path(result["workspace"])
            local_dir = PROJECT_ROOT / "data" / "v4_outputs" / paper_id
            local_dir.mkdir(parents=True, exist_ok=True)
            for f in ws.glob("*"):
                if f.is_file() and f.suffix in (".py", ".json", ".png", ".jpg"):
                    try:
                        import shutil
                        shutil.copy2(str(f), str(local_dir / f.name))
                    except Exception:
                        pass

    # Save summary
    summary = {
        "version": "v4",
        "timestamp": datetime.now().isoformat(),
        "papers": {p: {"v3_success": TIER1_PAPERS[p]["v3_success"],
                        "v4_state": r.get("agent_state", "N/A")}
                   for p, r in results.items()},
    }
    summary_file = RESULTS_DIR / "v4_summary.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"V4 LAUNCH SUMMARY")
    print(f"{'='*60}")
    for paper_id, result in results.items():
        state = result.get("agent_state", result.get("status", "?"))
        v3 = "✅" if TIER1_PAPERS[paper_id]["v3_success"] else "❌"
        v4 = "✅" if "FINISHED" in str(state) else "❌" if state != "dry_run" else "⏳"
        print(f"  {paper_id}: V3={v3} → V4={v4} ({state})")


if __name__ == "__main__":
    main()
