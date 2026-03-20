#!/usr/bin/env python3
"""
run_baseline.py — OpenHands-Only Baseline Framework (B2) for Evolution-Reproduce.

This is the CLEAN, CONSOLIDATED launcher for the B2 baseline:
  Paper (arxiv ID or local PDF) → Markdown → OpenHands CodeActAgent → Results

Supports:
  - arxiv paper download + OCR (full pipeline)
  - Local PDF → OCR → launch
  - Pre-existing markdown → launch directly
  - Single paper or batch mode
  - Staggered launches to avoid API overload
  - Result collection and status monitoring

Usage:
  # From arxiv ID
  python run_baseline.py --arxiv-id 2301.10137

  # From local PDF
  python run_baseline.py --pdf /path/to/paper.pdf --paper-id my_paper

  # From existing markdown
  python run_baseline.py --markdown /path/to/paper.md --paper-id my_paper

  # Batch from registry
  python run_baseline.py --registry data/ReproduceBench/paper_registry_v2.json --tier 1

  # Monitor running tasks
  python run_baseline.py --status
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# === Configuration ===
PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
OPENHANDS_DIR = Path("/home/yjh/OpenHands")
OPENHANDS_PYTHON = "/data/yjh/conda_envs/openhands/bin/python3"
OPENHANDS_CONFIG = OPENHANDS_DIR / "config.toml"
OPENHANDS_LAUNCHER = OPENHANDS_DIR / "run_evolution_task.py"

# Output directories
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "reproduction_results_v2"
PROMPTS_DIR = DATA_DIR / "agent_prompts_v2"
LOGS_DIR = PROJECT_ROOT / "logs" / "sandbox_stdout"
WORKSPACE_BASE = Path("/data/yjh/openhands_workspace")

# Defaults
MAX_ITERATIONS = 100
LAUNCH_STAGGER_SECONDS = 60

# === Prompt Template ===
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
RULE 4 — FILE PERSISTENCE: Use `cat > file.py << 'PYEOF'` pattern for multi-line files.
RULE 5 — RESULTS FORMAT: Save results.json with {{paper_title, reproduction_status, metrics, notes, files_produced}}.
RULE 6 — BUDGET AWARENESS: You have ~{max_iterations} iterations. At 70% budget, wrap up and produce whatever results you have.
RULE 7 — NO CHEATING: Do NOT hardcode expected results. Your code must actually perform the algorithm.

=== BEGIN REPRODUCTION ===
Start by reading the paper carefully and creating your reproduction plan."""


def get_paper_markdown(paper_id: str = None, arxiv_id: str = None, 
                       pdf_path: str = None, markdown_path: str = None) -> tuple:
    """Resolve paper content to markdown string.
    
    Returns (paper_id, markdown_content, markdown_path)
    """
    if markdown_path:
        # Use existing markdown directly
        md_path = Path(markdown_path)
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown not found: {markdown_path}")
        content = md_path.read_text(encoding="utf-8")
        pid = paper_id or md_path.stem
        return pid, content, str(md_path)
    
    if arxiv_id:
        # Use arxiv pipeline
        sys.path.insert(0, str(PROJECT_ROOT))
        from code.utils.arxiv_to_markdown import arxiv_to_markdown
        
        result = arxiv_to_markdown(arxiv_id=arxiv_id)
        md_path = result["markdown_path"]
        content = Path(md_path).read_text(encoding="utf-8")
        pid = paper_id or arxiv_id.replace("/", "_").replace(".", "_")
        return pid, content, md_path
    
    if pdf_path:
        # Use OCR pipeline on local PDF
        sys.path.insert(0, str(PROJECT_ROOT))
        from code.utils.arxiv_to_markdown import arxiv_to_markdown
        
        result = arxiv_to_markdown(pdf_path=pdf_path)
        md_path = result["markdown_path"]
        content = Path(md_path).read_text(encoding="utf-8")
        pid = paper_id or Path(pdf_path).stem
        return pid, content, md_path
    
    raise ValueError("Must provide one of: --markdown, --arxiv-id, --pdf")


def generate_prompt(paper_id: str, paper_content: str, max_iterations: int = MAX_ITERATIONS) -> Path:
    """Generate the agent prompt and save to file."""
    prompt = PROMPT_TEMPLATE.format(
        paper_content=paper_content, 
        max_iterations=max_iterations
    )
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{paper_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file


def launch_openhands(paper_id: str, prompt_file: Path, max_iterations: int = MAX_ITERATIONS) -> dict:
    """Launch a single OpenHands reproduction task.
    
    Returns dict with launch info (pid, session, paths).
    """
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_name = f"b2_{paper_id}_{ts}"
    workspace = WORKSPACE_BASE / session_name
    output_file = RESULTS_DIR / f"{paper_id}_result.json"
    log_file = LOGS_DIR / f"{paper_id}.log"
    
    # Create directories
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        OPENHANDS_PYTHON, str(OPENHANDS_LAUNCHER),
        "--prompt-file", str(prompt_file),
        "--workspace", str(workspace),
        "--session-name", session_name,
        "--max-iterations", str(max_iterations),
        "--config", str(OPENHANDS_CONFIG),
        "--output-file", str(output_file),
    ]
    
    print(f"\n{'='*60}")
    print(f"Launching: {paper_id}")
    print(f"  Session: {session_name}")
    print(f"  Workspace: {workspace}")
    print(f"  Log: {log_file}")
    print(f"  Max iterations: {max_iterations}")
    print(f"{'='*60}")
    
    with open(log_file, 'w') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    
    info = {
        "paper_id": paper_id,
        "pid": proc.pid,
        "session": session_name,
        "workspace": str(workspace),
        "log_file": str(log_file),
        "output_file": str(output_file),
        "prompt_file": str(prompt_file),
        "launched_at": datetime.now().isoformat(),
        "max_iterations": max_iterations,
        "status": "running"
    }
    
    print(f"  PID: {proc.pid}")
    return info


def launch_single(paper_id: str = None, arxiv_id: str = None,
                   pdf_path: str = None, markdown_path: str = None,
                   max_iterations: int = MAX_ITERATIONS) -> dict:
    """Full pipeline: resolve paper → generate prompt → launch OpenHands."""
    
    # Step 1: Get markdown
    print(f"[Step 1] Resolving paper content...")
    pid, content, md_path = get_paper_markdown(
        paper_id=paper_id, arxiv_id=arxiv_id,
        pdf_path=pdf_path, markdown_path=markdown_path
    )
    print(f"  Paper ID: {pid}")
    print(f"  Markdown: {md_path} ({len(content)} chars)")
    
    # Step 2: Generate prompt
    print(f"[Step 2] Generating agent prompt...")
    prompt_file = generate_prompt(pid, content, max_iterations)
    print(f"  Prompt: {prompt_file} ({prompt_file.stat().st_size} chars)")
    
    # Step 3: Launch
    print(f"[Step 3] Launching OpenHands...")
    info = launch_openhands(pid, prompt_file, max_iterations)
    
    return info


def launch_from_registry(registry_path: str, tier: int = None, 
                         papers: list = None,
                         max_iterations: int = MAX_ITERATIONS,
                         stagger: int = LAUNCH_STAGGER_SECONDS) -> list:
    """Launch multiple papers from the registry.
    
    Args:
        registry_path: path to paper_registry_v2.json
        tier: launch all papers of this tier (1, 2, or 3)
        papers: specific paper IDs to launch
        max_iterations: max iterations per task
        stagger: seconds between launches
    """
    with open(registry_path) as f:
        registry = json.load(f)
    
    # Filter papers
    to_launch = []
    for pid, info in registry["papers"].items():
        if papers and pid not in papers:
            continue
        if tier is not None and info["tier"] != tier:
            continue
        to_launch.append((pid, info))
    
    if not to_launch:
        print("No papers match the filter criteria.")
        return []
    
    print(f"\n{'='*60}")
    print(f"Batch Launch: {len(to_launch)} papers")
    print(f"Tier filter: {tier}, Paper filter: {papers}")
    print(f"Stagger: {stagger}s between launches")
    print(f"{'='*60}")
    
    launched = []
    for i, (pid, info) in enumerate(to_launch):
        print(f"\n--- Paper {i+1}/{len(to_launch)}: {pid} ---")
        
        # Determine markdown source
        # IMPORTANT: Prioritize _full.md (actual paper) over _task.md (code script)
        # Using _task.md leads to artificially high success rates since agent
        # just rewrites visible code rather than truly reproducing from paper.
        md_task = info.get("markdown_task_path")
        md_full = info.get("markdown_full_path")
        md_path = md_full if md_full and Path(md_full).exists() else md_task
        
        if not md_path or not Path(md_path).exists():
            print(f"  ⚠️ No markdown found for {pid}, skipping")
            continue
        
        try:
            result = launch_single(
                paper_id=pid,
                markdown_path=md_path,
                max_iterations=max_iterations
            )
            launched.append(result)
        except Exception as e:
            print(f"  ❌ Launch failed: {e}")
            launched.append({"paper_id": pid, "error": str(e), "status": "failed"})
            continue
        
        # Stagger
        if i < len(to_launch) - 1:
            print(f"\n  ⏳ Waiting {stagger}s before next launch...")
            time.sleep(stagger)
    
    # Save launch manifest
    manifest = {
        "launched_at": datetime.now().isoformat(),
        "tier": tier,
        "stagger_seconds": stagger,
        "max_iterations": max_iterations,
        "papers": launched
    }
    manifest_path = PROJECT_ROOT / "logs" / f"launch_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\nLaunch manifest saved: {manifest_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"LAUNCH SUMMARY")
    print(f"{'='*60}")
    successes = sum(1 for r in launched if r.get("status") != "failed")
    print(f"  Launched: {successes}/{len(launched)}")
    for r in launched:
        status = "✅" if r.get("status") != "failed" else "❌"
        pid = r.get("paper_id", "?")
        if r.get("status") == "failed":
            print(f"  {status} {pid}: {r.get('error', 'unknown')}")
        else:
            print(f"  {status} {pid}: PID={r.get('pid')}")
    
    return launched


def check_status():
    """Check status of all running/completed tasks."""
    print(f"\n{'='*60}")
    print(f"TASK STATUS CHECK — {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    # Check running processes
    try:
        result = subprocess.run(
            ["pgrep", "-a", "-f", "run_evolution_task"],
            capture_output=True, text=True
        )
        running_pids = {}
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    pid = parts[0]
                    cmd = parts[1]
                    # Extract session name
                    import re
                    session_match = re.search(r'--session-name\s+(\S+)', cmd)
                    session = session_match.group(1) if session_match else "unknown"
                    running_pids[session] = pid
    except Exception:
        running_pids = {}
    
    print(f"\n  Running processes: {len(running_pids)}")
    for session, pid in running_pids.items():
        print(f"    PID {pid}: {session}")
    
    # Check result files
    print(f"\n  Result files:")
    if RESULTS_DIR.exists():
        for rf in sorted(RESULTS_DIR.glob("*_result.json")):
            try:
                data = json.loads(rf.read_text())
                state = data.get("agent_state", "?")
                error = data.get("error")
                iters = data.get("iterations_used", "?")
                elapsed = data.get("elapsed_seconds", "?")
                has_results = data.get("has_results_json", False)
                
                if error:
                    status = f"❌ ERROR: {error[:60]}"
                elif "FINISHED" in str(state):
                    status = f"✅ FINISHED ({elapsed:.0f}s)" if isinstance(elapsed, (int, float)) else f"✅ FINISHED"
                else:
                    status = f"🔄 {state}"
                
                pid = rf.stem.replace("_result", "")
                print(f"    {pid}: {status} | results.json={'✅' if has_results else '❌'}")
            except Exception as e:
                print(f"    {rf.name}: ⚠️ parse error: {e}")
    else:
        print(f"    No results directory yet")
    
    # Check log sizes
    print(f"\n  Log files:")
    if LOGS_DIR.exists():
        for lf in sorted(LOGS_DIR.glob("*.log")):
            size = lf.stat().st_size
            mtime = datetime.fromtimestamp(lf.stat().st_mtime).strftime('%H:%M:%S')
            print(f"    {lf.name}: {size:,} bytes (modified {mtime})")
    
    # Check workspaces
    print(f"\n  Workspaces:")
    if WORKSPACE_BASE.exists():
        for ws in sorted(WORKSPACE_BASE.glob("b2_*")):
            files = list(ws.iterdir()) if ws.is_dir() else []
            has_results = any(f.name == "results.json" for f in files)
            print(f"    {ws.name}: {len(files)} files | results.json={'✅' if has_results else '❌'}")


def main():
    parser = argparse.ArgumentParser(
        description="Evolution-Reproduce B2 Baseline Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--arxiv-id", type=str, help="Launch from arxiv paper ID")
    mode_group.add_argument("--pdf", type=str, help="Launch from local PDF")
    mode_group.add_argument("--markdown", type=str, help="Launch from existing markdown")
    mode_group.add_argument("--registry", type=str, help="Launch from paper registry JSON")
    mode_group.add_argument("--status", action="store_true", help="Check status of running tasks")
    
    # Options
    parser.add_argument("--paper-id", type=str, help="Paper ID (auto-derived if not given)")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Tier filter (with --registry)")
    parser.add_argument("--papers", nargs="+", type=str, help="Specific paper IDs (with --registry)")
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS, help=f"Max iterations (default: {MAX_ITERATIONS})")
    parser.add_argument("--stagger", type=int, default=LAUNCH_STAGGER_SECONDS, help=f"Seconds between launches (default: {LAUNCH_STAGGER_SECONDS})")
    
    args = parser.parse_args()
    
    if args.status:
        check_status()
        return
    
    if args.registry:
        launch_from_registry(
            args.registry, 
            tier=args.tier,
            papers=args.papers,
            max_iterations=args.max_iterations,
            stagger=args.stagger
        )
    else:
        launch_single(
            paper_id=args.paper_id,
            arxiv_id=args.arxiv_id,
            pdf_path=args.pdf,
            markdown_path=args.markdown,
            max_iterations=args.max_iterations
        )


if __name__ == "__main__":
    main()
