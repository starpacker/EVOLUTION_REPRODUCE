#!/usr/bin/env python3
"""Launch Tier 1 Paper Reproductions — Phase 0 Restart (Proper Methodology)"""
import os, sys, json, time, subprocess, shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
OPENHANDS_DIR = Path("/home/yjh/OpenHands")
OPENHANDS_PYTHON = "/data/yjh/conda_envs/openhands/bin/python3"
OPENHANDS_CONFIG = OPENHANDS_DIR / "config.toml"
MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v2"
PROMPTS_DIR = PROJECT_ROOT / "data" / "agent_prompts_v2"
LOGS_DIR = PROJECT_ROOT / "logs" / "sandbox_stdout"
MAX_ITERATIONS = 100

TIER1_PAPERS = [
    {"paper_id": "pyeit", "title": "PyEIT: Electrical Impedance Tomography"},
    {"paper_id": "bpm", "title": "Beam Propagation Method"},
    {"paper_id": "pat", "title": "Photoacoustic Tomography"},
]

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

def generate_prompt(paper_id):
    task_md = MARKDOWN_DIR / f"{paper_id}_task.md"
    if not task_md.exists():
        raise FileNotFoundError(f"Task markdown not found: {task_md}")
    paper_content = task_md.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(paper_content=paper_content, max_iterations=MAX_ITERATIONS)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / f"{paper_id}_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"  Prompt generated: {prompt_file} ({len(prompt)} chars)")
    return str(prompt_file)

def launch_openhands(paper_id, prompt_file):
    session_name = f"tier1_v2_{paper_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    workspace = f"/data/yjh/openhands_workspace/{session_name}"
    output_file = RESULTS_DIR / f"{paper_id}_result.json"
    log_file = LOGS_DIR / f"{paper_id}.log"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        OPENHANDS_PYTHON, str(OPENHANDS_DIR / "run_evolution_task.py"),
        "--prompt-file", prompt_file,
        "--workspace", workspace,
        "--session-name", session_name,
        "--max-iterations", str(MAX_ITERATIONS),
        "--config", str(OPENHANDS_CONFIG),
        "--output-file", str(output_file),
    ]
    
    print(f"\n{'='*60}")
    print(f"Launching: {paper_id}")
    print(f"Session: {session_name}")
    print(f"Workspace: {workspace}")
    print(f"Log: {log_file}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    with open(log_file, 'w') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
        print(f"  PID: {proc.pid} — Running in background, log: {log_file}")
        return {"paper_id": paper_id, "pid": proc.pid, "log_file": str(log_file), "output_file": str(output_file)}

def main():
    print(f"{'='*60}")
    print(f"Phase 0 Restart: Tier 1 Paper Reproductions")
    print(f"Proper Methodology: Paper markdown only, clean empty sandbox")
    print(f"{'='*60}\n")
    
    launched = []
    for paper in TIER1_PAPERS:
        paper_id = paper["paper_id"]
        print(f"\n[{paper_id}] {paper['title']}")
        try:
            prompt_file = generate_prompt(paper_id)
            result = launch_openhands(paper_id, prompt_file)
            launched.append(result)
            time.sleep(5)  # Stagger launches
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Launched {len(launched)} reproductions:")
    for r in launched:
        print(f"  {r['paper_id']}: PID={r['pid']}, log={r['log_file']}")
    print(f"\nMonitor logs with: tail -f {LOGS_DIR}/*.log")
    print(f"Check results in: {RESULTS_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
