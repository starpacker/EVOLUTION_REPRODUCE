#!/usr/bin/env python3
"""
Agent Planner for Project Evolution-Reproduce.
Orchestrates paper reproduction tasks via OpenHands CodeActAgent.

Responsibilities:
  1. Build System Prompt per §5.1 (Dynamic Scaffolding, Toy-First, Sanity Check)
  2. Launch OpenHands CodeActAgent with paper markdown + experience injection
  3. Integrate Experience DB retrieval before/during execution
  4. Collect trajectories for post-hoc experience extraction

Usage:
  python -m code.agent.planner --paper_id <id> [--no-experience] [--dry-run]
"""

import asyncio
import json
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

# ─── Project paths ───
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, "/home/yjh/OpenHands")

# ─── API / Model config (shared with experience_db) ───
API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
LLM_MODEL = "cds/Claude-4.6-opus"

# ─── OpenHands paths ───
OPENHANDS_ROOT = Path("/home/yjh/OpenHands")
OPENHANDS_PYTHON = "/data/yjh/conda_envs/openhands/bin/python3"
WORKSPACE_BASE = Path("/data/yjh/openhands_workspace")
TRAJECTORY_DIR = Path("/data/yjh/openhands_results_v2/trajectories")
ARCHIVE_BASE = Path("/data/yjh/openhands_archive")

# ─── Project data paths ───
PAPER_REGISTRY = PROJECT_ROOT / "data" / "ReproduceBench" / "paper_registry_v2.json"
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v2"

# ─── Defaults ───
MAX_ITERATIONS = 100
SANDBOX_PYTHON = "3.10"


# ═══════════════════════════════════════════════════════════════
#  SYSTEM PROMPT (§5.1)
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT_TEMPLATE = """You are a paper reproduction agent. Reproduce the experiments from the paper below.

[Paper Content]:
{paper_markdown}

[Working Directory]: {workspace_path}
{experience_section}

=== RULES (READ CAREFULLY) ===

1. BRIEF PLAN FIRST: Write a short checklist (5-8 items max) of what to do, then start coding immediately.

2. FILE PERSISTENCE: ALL code MUST be written to .py files using bash:
   cat > filename.py << 'PYEOF'
   <code>
   PYEOF
   python filename.py
   Do NOT use IPython cells for anything important. The working directory is {workspace_path}.

3. TOY-FIRST: Test with tiny data/parameters first (e.g., small grid, few samples).
   Only run full-scale after toy version works.

4. SANITY CHECK: After every execution, verify outputs are reasonable (no NaN, correct magnitude).

5. DO NOT use the task_tracker tool — it wastes iterations. Just work directly.

6. DO NOT use empty think actions. Always take concrete action.

7. BUDGET: You have limited iterations. Be efficient. Start saving final files by iteration 70.

=== FINAL DELIVERABLE (MUST DO) ===
Save these two files using bash BEFORE calling finish:

cat > reproduce.py << 'PYEOF'
<your complete reproduction code>
PYEOF

cat > results.json << 'JSONEOF'
{{"metric_name": value, ...}}
JSONEOF

ls -la reproduce.py results.json
# Then call finish
"""

EXPERIENCE_INJECTION_TEMPLATE = """=== RELEVANT EXPERIENCE FROM PRIOR TASKS ===
The following experience(s) were retrieved from solved problems in previous
paper reproduction tasks. They MAY be relevant to your current task.
Use them as hints, but verify their applicability before applying blindly.

{experiences_text}

=== END OF EXPERIENCE ===
"""

NEGATIVE_EXPERIENCE_TEMPLATE = """WARNING — KNOWN INEFFECTIVE APPROACH:
The following approach has been verified as INEFFECTIVE for a similar problem.
Avoid this path:
  Problem: {condition}
  Failed approach: {solution}
"""


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ReproductionTask:
    """Represents a single paper reproduction task."""
    task_id: str
    paper_id: str
    paper_title: str
    paper_domain: str
    paper_markdown_path: str
    workspace: str
    conda_env: str
    max_iterations: int = MAX_ITERATIONS
    use_experience: bool = True
    status: str = "pending"       # pending | running | finished | failed
    start_time: str = ""
    end_time: str = ""
    trajectory_path: str = ""
    result: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReproductionResult:
    """Results from a reproduction attempt."""
    task_id: str
    paper_id: str
    agent_state: str              # FINISHED | STOPPED | ERROR
    iterations_used: int
    metrics_reproduced: Dict[str, float]
    trajectory_path: str
    experiences_injected: List[str]
    duration_seconds: float
    success: bool


# ═══════════════════════════════════════════════════════════════
#  EXPERIENCE INTEGRATION
# ═══════════════════════════════════════════════════════════════

def format_experience_for_injection(retrieved: List[Dict]) -> str:
    """Format retrieved experiences into prompt-injectable text.

    Per §4.5.2: RELEVANT gets full injection, PARTIAL gets disclaimer,
    Negative experiences get WARNING format.
    """
    if not retrieved:
        return ""

    parts = []
    for i, item in enumerate(retrieved, 1):
        exp = item.get("experience")
        if exp is None:
            continue
        relevance = item.get("relevance", "RELEVANT")

        if exp.type == "negative":
            parts.append(NEGATIVE_EXPERIENCE_TEMPLATE.format(
                condition=exp.condition.get("error_or_symptom", ""),
                solution=exp.action.get("solution", "")
            ))
            continue

        cond = exp.condition
        act = exp.action
        block = f"Experience #{i}"
        if relevance == "PARTIAL":
            block += " (partial match — use as inspiration only, may not directly apply)"
        block += f"""
  Symptom: {cond.get('error_or_symptom', 'N/A')}
  Context: {cond.get('task_context', 'N/A')}
  Solution: {act.get('solution', 'N/A')}"""
        code = act.get("code_implement")
        if code and len(code.strip()) > 0:
            block += f"\n  Key code: {code.strip()}"
        parts.append(block)

    if not parts:
        return ""
    return EXPERIENCE_INJECTION_TEMPLATE.format(experiences_text="\n\n".join(parts))


def retrieve_initial_experiences(paper_markdown: str, paper_domain: str) -> List[Dict]:
    """Retrieve potentially useful experiences before the task starts.

    Query the Experience DB with the paper's domain and key challenges.
    This provides 'meta-experiences' (recommended reproduction strategies).
    """
    from code.experience_db.experience_db import ExperienceDB

    db = ExperienceDB()
    if db.count() == 0:
        return []

    # Build a broad query from paper content (first 2000 chars + domain)
    snippet = paper_markdown[:2000]
    query = (
        f"[Domain]: {paper_domain}\n"
        f"[Task Context]: Reproducing a paper from scratch. "
        f"Planning phase — looking for common pitfalls and strategies.\n"
        f"[Paper excerpt]: {snippet}\n"
    )

    # Use relaxed retrieval (early-stage exploration ratio)
    results = db.retrieve(query, max_inject=2, exploration_ratio=0.9)
    return results


# ═══════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════

def build_task_prompt(
    paper_markdown: str,
    workspace_path: str,
    experiences: Optional[List[Dict]] = None,
) -> str:
    """Build the full system prompt for the CodeActAgent."""
    exp_section = ""
    if experiences:
        exp_section = format_experience_for_injection(experiences)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        paper_markdown=paper_markdown,
        workspace_path=workspace_path,
        experience_section=exp_section,
    )
    return prompt


# ═══════════════════════════════════════════════════════════════
#  SANDBOX MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def prepare_workspace(task: ReproductionTask, paper_markdown: str) -> str:
    """Prepare the isolated workspace for a reproduction task.

    Creates workspace directory and places paper markdown inside.
    Returns the workspace path.
    """
    ws = Path(task.workspace)
    ws.mkdir(parents=True, exist_ok=True)

    # Save paper markdown for agent reference
    paper_file = ws / "paper.md"
    paper_file.write_text(paper_markdown, encoding="utf-8")

    # Create standard subdirectories
    (ws / "code").mkdir(exist_ok=True)
    (ws / "data").mkdir(exist_ok=True)
    (ws / "results").mkdir(exist_ok=True)

    return str(ws)


# ═══════════════════════════════════════════════════════════════
#  OPENHANDS LAUNCHER
# ═══════════════════════════════════════════════════════════════

async def launch_openhands_agent(task: ReproductionTask, prompt: str) -> Dict:
    """Launch OpenHands CodeActAgent for a reproduction task.

    Uses the OpenHands run_controller API directly.
    Returns dict with agent_state, iterations, trajectory_path.
    """
    from openhands.core.config import OpenHandsConfig
    from openhands.core.main import run_controller, auto_continue_response
    from openhands.events.action import MessageAction
    from openhands.core.schema import AgentState

    # Build OpenHands config programmatically
    config = OpenHandsConfig()
    config.runtime = "local"
    config.workspace_base = task.workspace
    config.save_trajectory_path = str(TRAJECTORY_DIR)
    config.enable_browser = False
    config.file_store = "memory"
    config.max_iterations = task.max_iterations
    config.default_agent = "CodeActAgent"

    # LLM config
    config.llm.model = LLM_MODEL
    config.llm.api_key = API_KEY
    config.llm.base_url = BASE_URL
    config.llm.temperature = 0.7
    config.llm.max_message_chars = 30000
    config.llm.num_retries = 5
    config.llm.retry_multiplier = 2
    config.llm.retry_min_wait = 10
    config.llm.retry_max_wait = 120

    # Sandbox config
    config.sandbox.timeout = 600
    config.sandbox.enable_gpu = True
    config.sandbox.user_id = 1000

    # Session ID for this task
    sid = f"evo_{task.task_id}"

    # Create the initial message action
    initial_action = MessageAction(content=prompt)

    print(f"[Planner] Launching OpenHands agent for task {task.task_id}")
    print(f"[Planner] Workspace: {task.workspace}")
    print(f"[Planner] Max iterations: {task.max_iterations}")

    # Run the agent
    state = await run_controller(
        config=config,
        initial_user_action=initial_action,
        sid=sid,
        fake_user_response_fn=auto_continue_response,
        headless_mode=True,
    )

    # Extract results
    agent_state = "UNKNOWN"
    iterations = 0
    if state is not None:
        agent_state = str(state.agent_state) if hasattr(state, 'agent_state') else "UNKNOWN"
        iterations = state.iteration if hasattr(state, 'iteration') else 0

    # Find trajectory file
    traj_path = str(TRAJECTORY_DIR / f"{sid}.json")
    if not os.path.exists(traj_path):
        # Try searching for it
        for f in TRAJECTORY_DIR.glob(f"*{task.task_id}*"):
            traj_path = str(f)
            break

    return {
        "agent_state": agent_state,
        "iterations_used": iterations,
        "trajectory_path": traj_path,
        "state": state,
    }


def launch_openhands_subprocess(task: ReproductionTask, prompt: str) -> Dict:
    """Launch OpenHands via the standalone run_evolution_task.py script.

    This runs in the OpenHands directory using the proven benchmark_v2 pattern:
    load_openhands_config -> generate_sid -> run_controller.
    """
    # Save prompt to workspace
    prompt_file = Path(task.workspace) / ".task_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    session_name = f"evo_{task.task_id}"
    output_file = str(RESULTS_DIR / task.paper_id / f"{task.task_id}_oh_result.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    launcher = str(OPENHANDS_ROOT / "run_evolution_task.py")
    # Use OPENHANDS_PYTHON if it exists, otherwise fall back to sys.executable
    python_bin = OPENHANDS_PYTHON if os.path.isfile(OPENHANDS_PYTHON) else sys.executable

    # Log files for stdout/stderr (capture FULL output, not truncated)
    log_dir = RESULTS_DIR / task.paper_id
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = str(log_dir / f"{task.task_id}_stdout.log")
    stderr_log = str(log_dir / f"{task.task_id}_stderr.log")

    cmd = [
        python_bin, launcher,
        "--prompt-file", str(prompt_file),
        "--workspace", task.workspace,
        "--session-name", session_name,
        "--max-iterations", str(task.max_iterations),
        "--config", str(OPENHANDS_ROOT / "config.toml"),
        "--output-file", output_file,
    ]

    print(f"[Planner] Launching OpenHands subprocess for task {task.task_id}")
    print(f"[Planner] Command: {' '.join(cmd)}")
    print(f"[Planner] Stdout log: {stdout_log}")
    print(f"[Planner] Stderr log: {stderr_log}")

    start = time.time()
    try:
        with open(stdout_log, "w") as f_out, open(stderr_log, "w") as f_err:
            result = subprocess.run(
                cmd,
                cwd=str(OPENHANDS_ROOT),
                stdout=f_out,
                stderr=f_err,
                text=True,
                timeout=7200,  # 2 hour max
            )
        duration = time.time() - start

        # Read back logs for the return dict
        stdout_text = ""
        stderr_text = ""
        try:
            with open(stdout_log) as f:
                stdout_text = f.read()
        except:
            pass
        try:
            with open(stderr_log) as f:
                stderr_text = f.read()
        except:
            pass

        # Parse result from output file
        if os.path.exists(output_file):
            with open(output_file) as f:
                oh_result = json.load(f)
            return {
                "agent_state": oh_result.get("agent_state", "UNKNOWN"),
                "iterations_used": oh_result.get("iterations_used", -1),
                "trajectory_path": oh_result.get("trajectory_path", ""),
                "duration": duration,
                "stdout": stdout_text[-5000:] if stdout_text else "",
                "stderr": stderr_text[-5000:] if stderr_text else "",
                "stdout_log": stdout_log,
                "stderr_log": stderr_log,
            }

        # Fallback: no output file
        return {
            "agent_state": "FINISHED" if result.returncode == 0 else "ERROR",
            "iterations_used": -1,
            "trajectory_path": "",
            "duration": duration,
            "stdout": stdout_text[-5000:] if stdout_text else "",
            "stderr": stderr_text[-5000:] if stderr_text else "",
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
        }
    except subprocess.TimeoutExpired:
        return {
            "agent_state": "TIMEOUT",
            "iterations_used": -1,
            "trajectory_path": "",
            "duration": 7200,
            "stdout": "",
            "stderr": "Task timed out after 7200s",
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
        }


# ═══════════════════════════════════════════════════════════════
#  POST-TASK PROCESSING
# ═══════════════════════════════════════════════════════════════

def extract_reproduced_metrics(workspace: str) -> Dict[str, float]:
    """Extract reproduced metrics from the agent's output.

    Looks for results.json or parses METRIC: lines from stdout.
    """
    ws = Path(workspace)

    # Try results.json first
    results_file = ws / "results.json"
    if results_file.exists():
        try:
            with open(results_file) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {k: float(v) for k, v in data.items()
                        if isinstance(v, (int, float))}
        except Exception:
            pass

    # Try parsing METRIC: lines from any .log or output file
    metrics = {}
    for log_file in ws.glob("*.log"):
        try:
            text = log_file.read_text()
            for line in text.split("\n"):
                if line.strip().startswith("METRIC:"):
                    parts = line.split("=")
                    if len(parts) == 2:
                        name = parts[0].replace("METRIC:", "").strip()
                        val = float(parts[1].strip())
                        metrics[name] = val
        except Exception:
            continue

    return metrics


def process_post_task(task: ReproductionTask, launch_result: Dict) -> ReproductionResult:
    """Post-task processing: extract metrics, package sandbox, trigger experience extraction."""
    metrics = extract_reproduced_metrics(task.workspace)

    # Determine success
    success = (
        launch_result["agent_state"] in ("FINISHED", "AgentState.FINISHED")
        and len(metrics) > 0
    )

    result = ReproductionResult(
        task_id=task.task_id,
        paper_id=task.paper_id,
        agent_state=launch_result["agent_state"],
        iterations_used=launch_result.get("iterations_used", -1),
        metrics_reproduced=metrics,
        trajectory_path=launch_result.get("trajectory_path", ""),
        experiences_injected=[],
        duration_seconds=launch_result.get("duration", 0),
        success=success,
    )

    # Save result
    results_dir = RESULTS_DIR / task.paper_id
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{task.task_id}_result.json"
    with open(result_file, "w") as f:
        json.dump(asdict(result), f, indent=2)

    print(f"[Planner] Task {task.task_id} completed: state={result.agent_state}, "
          f"success={result.success}, metrics={result.metrics_reproduced}")

    # Log subprocess output for debugging if task failed
    if not result.success:
        stderr = launch_result.get("stderr", "")
        stdout = launch_result.get("stdout", "")
        if stderr:
            print(f"[Planner] STDERR (last 500 chars): {stderr[-500:]}")
        if stdout and not stderr:
            print(f"[Planner] STDOUT (last 500 chars): {stdout[-500:]}")

        # Save debug log
        debug_file = results_dir / f"{task.task_id}_debug.txt"
        with open(debug_file, "w") as f:
            f.write(f"=== STDOUT ===\n{stdout}\n\n=== STDERR ===\n{stderr}\n")

    # ── Package sandbox (collect all artifacts into structured directory) ──
    try:
        from code.utils.sandbox_packager import package_sandbox
        sandbox_path = package_sandbox(
            paper_id=task.paper_id,
            workspace=task.workspace,
            markdown_path=task.paper_markdown_path,
            task_id=task.task_id,
            extra_metadata={
                "agent_state": result.agent_state,
                "success": result.success,
                "iterations_used": result.iterations_used,
                "duration_seconds": result.duration_seconds,
                "metrics": result.metrics_reproduced,
            },
        )
        print(f"[Planner] Sandbox packaged: {sandbox_path}")
    except Exception as e:
        print(f"[Planner] Sandbox packaging failed (non-fatal): {e}")

    # ── Extract experiences from trajectory and store in Experience DB ──
    traj_path = launch_result.get("trajectory_path", "")
    if traj_path and os.path.exists(traj_path):
        try:
            _extract_and_store_experiences(
                trajectory_path=traj_path,
                paper_id=task.paper_id,
                paper_title=task.paper_title,
                paper_domain=task.paper_domain,
                task_success=result.success,
            )
        except Exception as e:
            print(f"[Planner] Experience extraction failed (non-fatal): {e}")

    return result


def _extract_and_store_experiences(
    trajectory_path: str,
    paper_id: str,
    paper_title: str,
    paper_domain: str,
    task_success: bool,
) -> int:
    """Extract experiences from a trajectory and store them in the Experience DB.

    This is the automatic post-run experience accumulation pipeline:
    1. Parse trajectory → segment episodes → denoise → LLM extract
    2. For each extracted experience, create an Experience object
    3. Store in Experience DB with proper metadata

    Returns number of experiences stored.
    """
    from code.experience_db.trajectory_parser import process_trajectory
    from code.experience_db.experience_db import ExperienceDB, Experience

    print(f"\n[Planner] Extracting experiences from trajectory: {trajectory_path}")

    # Step 1: Extract raw experience dicts from trajectory
    raw_experiences = process_trajectory(
        filepath=trajectory_path,
        project_name=paper_title or paper_id,
        domain=paper_domain,
    )

    if not raw_experiences:
        print(f"[Planner] No experiences extracted from trajectory")
        return 0

    # Step 2: Store in Experience DB
    db = ExperienceDB()
    stored_count = 0
    import time as _time
    import uuid as _uuid

    for i, exp_data in enumerate(raw_experiences):
        try:
            exp = Experience(
                id=f"exp_{paper_id}_{_time.strftime('%Y%m%d')}_{_uuid.uuid4().hex[:8]}",
                type=exp_data.get("type", "positive"),
                domain_hint=exp_data.get("domain_hint", paper_domain),
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
                    "task_success": task_success,
                },
                status="verified" if task_success else "hypothesis",
            )
            eid = db.add(exp)
            stored_count += 1
            symptom = exp.condition.get("error_or_symptom", "")[:80]
            print(f"  ✅ Stored experience {eid}: {symptom}")
        except Exception as e:
            print(f"  ❌ Failed to store experience #{i}: {e}")

    print(f"[Planner] Stored {stored_count}/{len(raw_experiences)} experiences in DB")
    print(f"[Planner] Experience DB stats: {db.stats()}")
    return stored_count


# ═══════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

def load_paper_markdown(paper_id: str) -> str:
    """Load paper markdown from the paper_markdowns_v2 directory or parse from PDF.
    
    Prioritizes _full.md (actual paper) over _task.md (code script).
    Using _task.md leads to artificially high success rates.
    """
    # Priority: _full.md > _task.md > {paper_id}.md
    full_md = PAPER_MARKDOWN_DIR / f"{paper_id}_full.md"
    task_md = PAPER_MARKDOWN_DIR / f"{paper_id}_task.md"
    plain_md = PAPER_MARKDOWN_DIR / f"{paper_id}.md"
    
    for md_path in [full_md, task_md, plain_md]:
        if md_path.exists():
            print(f"[Planner] Using markdown: {md_path.name}")
            return md_path.read_text(encoding="utf-8")

    # Check if we have a PDF to parse
    pdf_dir = PROJECT_ROOT / "data" / "papers_pdf"
    pdf_path = pdf_dir / f"{paper_id}.pdf"
    if pdf_path.exists():
        print(f"[Planner] Parsing PDF for {paper_id} via PaddleOCR...")
        from code.utils.ocr_paper_parser import parse_paper_pdf
        result = parse_paper_pdf(str(pdf_path), str(PAPER_MARKDOWN_DIR))
        if result and result.get("markdown_path"):
            return Path(result["markdown_path"]).read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"No markdown or PDF found for paper_id={paper_id}. "
        f"Searched: {full_md}, {task_md}, {plain_md}"
    )


def load_paper_info(paper_id: str) -> Dict:
    """Load paper metadata from the registry (v2 format)."""
    with open(PAPER_REGISTRY) as f:
        registry = json.load(f)

    # v2 registry format: registry["papers"] is a dict keyed by paper_id
    papers = registry.get("papers", {})
    if paper_id in papers:
        return papers[paper_id]
    
    # Case-insensitive fallback
    for pid, info in papers.items():
        if pid.lower() == paper_id.lower():
            return info

    # Legacy format fallback
    candidates = registry.get("papers_from_existing_trajectories", {}).get("candidates", [])
    for paper in candidates:
        if paper.get("project_name", "").lower() == paper_id.lower():
            return paper

    raise ValueError(f"Paper '{paper_id}' not found in registry: {PAPER_REGISTRY}")


def run_reproduction(
    paper_id: str,
    use_experience: bool = True,
    max_iterations: int = MAX_ITERATIONS,
    use_subprocess: bool = True,
    dry_run: bool = False,
) -> Optional[ReproductionResult]:
    """
    Main entry point: run a full paper reproduction task.

    Steps:
      1. Load paper markdown + metadata
      2. Create isolated workspace
      3. Retrieve relevant experiences (if enabled)
      4. Build system prompt
      5. Launch OpenHands agent
      6. Collect results + trajectory
      7. Trigger experience extraction (if applicable)

    Args:
        paper_id: Identifier matching paper_registry.json
        use_experience: Whether to inject experiences from the DB
        max_iterations: Max OpenHands iterations
        use_subprocess: Use subprocess launcher (more robust) vs async API
        dry_run: If True, print prompt but don't launch agent

    Returns:
        ReproductionResult or None if dry_run
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 1. Load paper info
    print(f"\n{'='*60}")
    print(f"[Planner] Starting reproduction for: {paper_id}")
    print(f"{'='*60}")

    paper_info = load_paper_info(paper_id)
    paper_domain = paper_info.get("domain", "unknown")
    paper_title = paper_info.get("project_name", paper_id)
    print(f"[Planner] Paper: {paper_title} | Domain: {paper_domain}")

    # Load markdown
    try:
        paper_markdown = load_paper_markdown(paper_id)
        print(f"[Planner] Paper markdown loaded: {len(paper_markdown)} chars")
    except FileNotFoundError as e:
        print(f"[Planner] ERROR: {e}")
        print(f"[Planner] Please place the paper markdown at: "
              f"{PAPER_MARKDOWN_DIR / f'{paper_id}.md'}")
        return None

    # 2. Create task and workspace
    task_id = f"{paper_id}_{timestamp}"
    workspace = str(WORKSPACE_BASE / f"task_{task_id}")

    task = ReproductionTask(
        task_id=task_id,
        paper_id=paper_id,
        paper_title=paper_title,
        paper_domain=paper_domain,
        paper_markdown_path=str(PAPER_MARKDOWN_DIR / f"{paper_id}.md"),
        workspace=workspace,
        conda_env=f"task_{task_id}",
        max_iterations=max_iterations,
        use_experience=use_experience,
    )

    prepare_workspace(task, paper_markdown)
    print(f"[Planner] Workspace prepared: {workspace}")

    # 3. Retrieve experiences
    experiences = []
    if use_experience:
        print(f"[Planner] Querying Experience DB for relevant experiences...")
        try:
            experiences = retrieve_initial_experiences(paper_markdown, paper_domain)
            if experiences:
                print(f"[Planner] Found {len(experiences)} relevant experience(s)")
                for exp in experiences:
                    e = exp.get("experience")
                    if e:
                        print(f"  - {e.id}: {e.condition.get('error_or_symptom', '')[:80]}")
            else:
                print(f"[Planner] No relevant experiences found (cold start)")
        except Exception as e:
            print(f"[Planner] Experience retrieval error (non-fatal): {e}")
            experiences = []

    # 4. Build prompt
    prompt = build_task_prompt(paper_markdown, workspace, experiences)
    task.start_time = time.strftime("%Y-%m-%dT%H:%M:%S")
    task.status = "running"

    print(f"[Planner] Prompt built: {len(prompt)} chars")

    if dry_run:
        print(f"\n{'='*60}")
        print("[DRY RUN] Prompt preview (first 3000 chars):")
        print(f"{'='*60}")
        print(prompt[:3000])
        print(f"\n... ({len(prompt) - 3000} more chars)")
        print(f"{'='*60}")
        # Save full prompt for inspection
        prompt_save = RESULTS_DIR / task.paper_id / f"{task_id}_prompt.txt"
        prompt_save.parent.mkdir(parents=True, exist_ok=True)
        prompt_save.write_text(prompt, encoding="utf-8")
        print(f"[DRY RUN] Full prompt saved to: {prompt_save}")
        return None

    # 5. Launch OpenHands
    start = time.time()
    if use_subprocess:
        launch_result = launch_openhands_subprocess(task, prompt)
    else:
        launch_result = asyncio.run(launch_openhands_agent(task, prompt))
    launch_result["duration"] = time.time() - start

    task.end_time = time.strftime("%Y-%m-%dT%H:%M:%S")
    task.trajectory_path = launch_result.get("trajectory_path", "")

    # 6. Post-task processing
    result = process_post_task(task, launch_result)

    # 7. Trigger experience extraction from trajectory (if applicable)
    if result.trajectory_path and os.path.exists(result.trajectory_path):
        print(f"[Planner] Trajectory saved: {result.trajectory_path}")
        print(f"[Planner] Run trajectory_parser to extract experiences from this trajectory.")
        # Auto-extraction can be done here in the future:
        # from code.experience_db.trajectory_parser import process_trajectory
        # process_trajectory(result.trajectory_path, paper_title, paper_domain)

    return result


# ═══════════════════════════════════════════════════════════════
#  BATCH RUNNER
# ═══════════════════════════════════════════════════════════════

def run_batch(
    paper_ids: List[str],
    use_experience: bool = True,
    max_iterations: int = MAX_ITERATIONS,
    dry_run: bool = False,
) -> List[ReproductionResult]:
    """Run reproduction on multiple papers sequentially."""
    results = []
    for i, pid in enumerate(paper_ids, 1):
        print(f"\n[Batch] Paper {i}/{len(paper_ids)}: {pid}")
        try:
            r = run_reproduction(pid, use_experience=use_experience,
                                 max_iterations=max_iterations, dry_run=dry_run)
            if r:
                results.append(r)
        except Exception as e:
            print(f"[Batch] ERROR on {pid}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    if results:
        print(f"\n{'='*60}")
        print(f"[Batch] Summary: {len(results)} tasks completed")
        successes = sum(1 for r in results if r.success)
        print(f"[Batch] Success: {successes}/{len(results)}")
        print(f"{'='*60}")

    return results


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evolution-Reproduce Agent Planner — Orchestrate paper reproduction")
    parser.add_argument("--paper_id", type=str, help="Paper ID from registry")
    parser.add_argument("--no-experience", action="store_true",
                        help="Disable experience injection (baseline B2)")
    parser.add_argument("--max-iter", type=int, default=MAX_ITERATIONS,
                        help="Max OpenHands iterations")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build prompt only, don't launch agent")
    parser.add_argument("--list-papers", action="store_true",
                        help="List available papers in registry")
    parser.add_argument("--batch", nargs="+", type=str,
                        help="Run batch reproduction on multiple paper IDs")

    args = parser.parse_args()

    if args.list_papers:
        with open(PAPER_REGISTRY) as f:
            reg = json.load(f)
        papers = reg.get("papers_from_existing_trajectories", {}).get("candidates", [])
        print(f"\nAvailable papers ({len(papers)}):")
        print(f"{'Name':<25} {'Domain':<30} {'Tier':<15} {'Trajectories'}")
        print("-" * 85)
        for p in papers:
            print(f"{p['project_name']:<25} {p.get('domain','?'):<30} "
                  f"{p.get('estimated_tier','?'):<15} {p.get('trajectory_count', 0)}")
        sys.exit(0)

    if args.batch:
        run_batch(args.batch, use_experience=not args.no_experience,
                  max_iterations=args.max_iter, dry_run=args.dry_run)
    elif args.paper_id:
        run_reproduction(args.paper_id, use_experience=not args.no_experience,
                         max_iterations=args.max_iter, dry_run=args.dry_run)
    else:
        parser.print_help()
