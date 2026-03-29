#!/usr/bin/env python3
"""
Trajectory-to-Experience Extraction Pipeline (§4.4.4).
Parses OpenHands trajectories, segments into episodes, denoises, and extracts experiences.
"""
import json, os, re, time, hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from openai import OpenAI

API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
LLM_MODEL = "gpt-4o"
FAILURE_THRESHOLD_K = 1
TRAJ_DIR = "/data/yjh/openhands_results_v2/trajectories"

@dataclass
class TrajectoryStep:
    step_id: int
    action_type: str  # "run"|"think"|"write"|"browse"|"system"|"message"|"recall"
    action_content: str
    observation: str
    has_error: bool
    error_type: Optional[str] = None
    timestamp: str = ""

@dataclass
class Episode:
    steps: List[TrajectoryStep]
    start_idx: int
    end_idx: int
    has_failure: bool = False
    failure_count: int = 0
    resolved: bool = False
    summary: str = ""

# ═══════ Step 1: Structural Parsing ═══════

def parse_trajectory(filepath: str) -> List[TrajectoryStep]:
    """Parse raw OpenHands trajectory JSON into TrajectoryStep list."""
    with open(filepath) as f:
        raw = json.load(f)
    steps = []
    i = 0
    while i < len(raw):
        item = raw[i]
        src = item.get("source", "")
        act = item.get("action", "")
        msg = item.get("message", "")
        ts = item.get("timestamp", "")
        # Skip system/user/recall items
        if act in ("system", "message", "recall") or src == "user":
            i += 1; continue
        # Agent action (run/think/write) followed by observation
        if src == "agent" and act in ("run", "think", "write", "browse"):
            obs = ""
            if i + 1 < len(raw) and raw[i+1].get("observation") == act:
                obs = raw[i+1].get("content", raw[i+1].get("message", ""))[:3000]
                i += 1
            action_content = ""
            if act == "run":
                action_content = item.get("args", {}).get("command", msg[:500])
            elif act == "think":
                action_content = item.get("args", {}).get("thought", msg[:500])
            else:
                action_content = msg[:500]
            has_err, err_type = _detect_error(obs)
            steps.append(TrajectoryStep(
                step_id=len(steps), action_type=act,
                action_content=action_content[:1500],
                observation=obs[:2000], has_error=has_err,
                error_type=err_type, timestamp=ts))
        # Observation-only item (command result without explicit action)
        elif src == "agent" and act == "" and "observation" in item:
            obs_type = item.get("observation", "")
            obs = item.get("content", item.get("message", ""))[:3000]
            has_err, err_type = _detect_error(obs)
            if steps and steps[-1].observation == "":
                steps[-1].observation = obs[:2000]
                steps[-1].has_error = has_err
                steps[-1].error_type = err_type
        i += 1
    return steps

ERROR_PATTERNS = [
    (r"Traceback \(most recent call last\)", "Traceback"),
    (r"ModuleNotFoundError", "ModuleNotFoundError"),
    (r"ImportError", "ImportError"),
    (r"RuntimeError", "RuntimeError"),
    (r"ValueError", "ValueError"),
    (r"TypeError", "TypeError"),
    (r"FileNotFoundError", "FileNotFoundError"),
    (r"KeyError", "KeyError"),
    (r"IndexError", "IndexError"),
    (r"AttributeError", "AttributeError"),
    (r"MemoryError|OOM|CUDA out of memory", "MemoryError"),
    (r"SyntaxError", "SyntaxError"),
    (r"NameError", "NameError"),
    (r"ZeroDivisionError", "ZeroDivisionError"),
    (r"OSError|PermissionError", "OSError"),
]

def _detect_error(text: str) -> tuple:
    if not text:
        return False, None
    for pat, etype in ERROR_PATTERNS:
        if re.search(pat, text):
            return True, etype
    return False, None

# ═══════ Step 2: Episode Segmentation ═══════

GOAL_SWITCH_PATTERNS = [
    r"(?i)now let me (move on|try|switch|work on|implement|focus)",
    r"(?i)next,?\s+I (need|will|should|want) to",
    r"(?i)let'?s (now|move|try|start|switch)",
    r"(?i)moving on to",
    r"(?i)the next step is",
]

def segment_episodes(steps: List[TrajectoryStep]) -> List[Episode]:
    """Segment steps into episodes based on intent/error changes."""
    if not steps:
        return []
    boundaries = [0]
    for i in range(1, len(steps)):
        s = steps[i]
        prev = steps[i-1]
        # Signal 1: Agent declares new goal in think step
        if s.action_type == "think":
            for pat in GOAL_SWITCH_PATTERNS:
                if re.search(pat, s.action_content):
                    boundaries.append(i); break
            continue
        # Signal 2: Error type changes abruptly
        if (s.has_error and prev.has_error and
            s.error_type and prev.error_type and
            s.error_type != prev.error_type):
            boundaries.append(i); continue
        # Signal 3: Long gap between steps (>60s think pause)
        if s.action_type == "think" and len(s.action_content) > 500:
            boundaries.append(i)
    boundaries = sorted(set(boundaries))
    episodes = []
    for j in range(len(boundaries)):
        start = boundaries[j]
        end = boundaries[j+1] if j+1 < len(boundaries) else len(steps)
        ep_steps = steps[start:end]
        fail_count = sum(1 for s in ep_steps if s.has_error)
        resolved = len(ep_steps) > 0 and not ep_steps[-1].has_error
        episodes.append(Episode(
            steps=ep_steps, start_idx=start, end_idx=end,
            has_failure=fail_count > 0, failure_count=fail_count,
            resolved=resolved))
    return episodes

# ═══════ Step 3: Episode Denoising ═══════

def denoise_episode(ep: Episode) -> str:
    """Compress episode into clean narrative < 3000 tokens."""
    lines = []
    prev_err = None
    repeat_count = 0
    for s in ep.steps:
        if s.action_type == "think":
            lines.append(f"[Think] {s.action_content[:200]}")
            continue
        if s.action_type == "run":
            cmd = s.action_content[:300]
            if s.has_error:
                if s.error_type == prev_err:
                    repeat_count += 1
                    continue  # skip repeated errors
                else:
                    if repeat_count > 0:
                        lines.append(f"  (repeated similar error {repeat_count} more times)")
                        repeat_count = 0
                    obs_tail = s.observation[-500:] if s.observation else ""
                    lines.append(f"[Run] {cmd}")
                    lines.append(f"  ❌ {s.error_type}: {obs_tail[:300]}")
                    prev_err = s.error_type
            else:
                if repeat_count > 0:
                    lines.append(f"  (repeated similar error {repeat_count} more times)")
                    repeat_count = 0
                obs_snip = s.observation[:300] if s.observation else "(no output)"
                lines.append(f"[Run] {cmd}")
                lines.append(f"  ✓ {obs_snip}")
                prev_err = None
    if repeat_count > 0:
        lines.append(f"  (repeated similar error {repeat_count} more times)")
    return "\n".join(lines)[:6000]


# ═══════ Step 4: LLM Experience Extraction ═══════

EXTRACT_PROMPT = """You are an experience extraction expert. Below is a denoised operation log
from an AI coding Agent solving a problem during paper reproduction.

【Episode Log】
{episode_text}

【Paper/Project Info】
Project: {project_name}, Domain: {domain}

Extract ONE structured experience in JSON:
{{
  "condition": {{
    "error_or_symptom": "one-line core error description",
    "task_context": "what the agent was doing",
    "environment": "key libs and versions if mentioned",
    "failed_attempts_summary": ["attempt 1 summary", "attempt 2 summary"]
  }},
  "action": {{
    "solution": "2-3 sentences on what finally worked",
    "code_implement": "key code if <=5 lines, else pseudocode",
    "verification": "how success was verified"
  }},
  "rationale": "why this solution works (1-2 sentences)",
  "domain_hint": "best matching domain label",
  "type": "positive or negative"
}}

RULES:
- If the episode is too trivial (typo, simple syntax error) or not generalizable, output: {{"SKIP": "reason"}}
- Use generic descriptions, not project-specific variable names
- condition+action must fit in 500 tokens"""


def extract_experience_from_episode(episode_text: str, project_name: str,
                                     domain: str, client: OpenAI) -> Optional[Dict]:
    """Use LLM to extract structured experience from denoised episode."""
    prompt = EXTRACT_PROMPT.format(
        episode_text=episode_text[:4000],
        project_name=project_name, domain=domain)
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800, temperature=0.0)
        text = resp.choices[0].message.content.strip()
        # Find JSON in response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            if "SKIP" in data:
                print(f"  SKIP: {data['SKIP']}")
                return None
            return data
    except Exception as e:
        print(f"  Extraction error: {e}")
    return None


# ═══════ Step 5: Quality Gate ═══════

def quality_check(exp_data: Dict) -> bool:
    """Validate extracted experience meets minimum quality."""
    cond = exp_data.get("condition", {})
    act = exp_data.get("action", {})
    # Check required fields exist and are non-empty
    if not cond.get("error_or_symptom") or len(cond["error_or_symptom"]) < 10:
        return False
    if not act.get("solution") or len(act["solution"]) < 20:
        return False
    # Reject overly generic solutions
    generic = ["check the code", "try again", "fix the error", "debug"]
    sol_lower = act["solution"].lower()
    if any(g in sol_lower and len(sol_lower) < 30 for g in generic):
        return False
    return True


# ═══════ Full Pipeline ═══════

def process_trajectory(filepath: str, project_name: str = "",
                       domain: str = "unknown") -> List[Dict]:
    """Full pipeline: parse → segment → filter → denoise → extract → validate."""
    if not project_name:
        project_name = os.path.basename(filepath).replace(".json", "")

    print(f"\n{'='*60}")
    print(f"Processing: {project_name}")

    # Step 1: Parse
    steps = parse_trajectory(filepath)
    print(f"  Parsed {len(steps)} steps")

    # Step 2: Segment
    episodes = segment_episodes(steps)
    print(f"  Segmented into {len(episodes)} episodes")

    # Filter: only episodes with failures >= K that were resolved (Type A)
    # or unresolved failures (Type C for negative constraints)
    candidates = []
    for ep in episodes:
        if ep.failure_count >= FAILURE_THRESHOLD_K and ep.resolved:
            candidates.append(("positive", ep))
        elif ep.failure_count >= FAILURE_THRESHOLD_K and not ep.resolved:
            candidates.append(("negative", ep))
    print(f"  {len(candidates)} episodes meet failure threshold (k={FAILURE_THRESHOLD_K})")

    if not candidates:
        print("  No extractable episodes found.")
        return []

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    extracted = []

    for exp_type, ep in candidates:
        # Step 3: Denoise
        denoised = denoise_episode(ep)
        print(f"\n  Episode [{ep.start_idx}:{ep.end_idx}] "
              f"failures={ep.failure_count} resolved={ep.resolved}")

        # Step 4: LLM Extract
        exp_data = extract_experience_from_episode(
            denoised, project_name, domain, client)
        if not exp_data:
            continue

        # Override type based on resolution
        exp_data["type"] = exp_type

        # Step 5: Quality gate
        if quality_check(exp_data):
            extracted.append(exp_data)
            print(f"  ✅ Extracted: {exp_data['condition']['error_or_symptom'][:80]}")
        else:
            print(f"  ❌ Failed quality check")

    print(f"\nTotal extracted: {len(extracted)} experiences")
    return extracted


def scan_all_trajectories(traj_dir: str = TRAJ_DIR) -> Dict[str, List[Dict]]:
    """Scan all trajectory files and extract experiences."""
    results = {}
    files = sorted(f for f in os.listdir(traj_dir) if f.endswith(".json"))
    print(f"Found {len(files)} trajectory files")

    for fname in files:
        project = fname.split("-")[0].replace("oh_", "")
        domain = "unknown"  # Could be enriched from paper_registry
        fpath = os.path.join(traj_dir, fname)
        exps = process_trajectory(fpath, project, domain)
        if exps:
            results[fname] = exps
    return results


# ═══════ CLI ═══════
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fp = sys.argv[1]
        exps = process_trajectory(fp)
        print(json.dumps(exps, indent=2, ensure_ascii=False))
    else:
        # Quick test on one trajectory
        test_file = os.path.join(TRAJ_DIR,
            "oh_PyAbel-master-476b74fcac1395f.json")
        if os.path.exists(test_file):
            exps = process_trajectory(test_file, "PyAbel", "computational_physics")
            if exps:
                print("\n--- Extracted Experience ---")
                print(json.dumps(exps[0], indent=2, ensure_ascii=False))
        else:
            print(f"Test file not found: {test_file}")
