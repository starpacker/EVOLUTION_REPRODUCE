#!/usr/bin/env python3
"""
LLM Judge for Code Faithfulness Evaluation — §6.1.2 Layer 2 of reproduce_readme.md.

Evaluates whether reproduced code faithfully implements the paper's method.
Two modes:
  - Reference-Free: Compares generated code against paper description only
  - Reference-Based: Compares generated code against ground truth implementation

Evaluation dimensions (from paper):
  - Data Processing: data acquisition, preprocessing, augmentation, splits
  - Method: core algorithm/model implementation, key formulas, special modules
  - Evaluation: metric computation, evaluation protocol (k-fold, etc.)

Each component scored as: ○ (full), △ (partial), × (missing)
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import re

# API configuration
API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
JUDGE_MODEL = "global.anthropic.claude-opus-4-6-v1"


@dataclass
class ComponentScore:
    """Score for a single implementation component."""
    dimension: str       # "data_processing" | "method" | "evaluation"
    component: str       # description of the component
    importance: str      # "high" | "medium" | "low"
    score: str           # "full" | "partial" | "missing"
    evidence: str        # quote from code or explanation
    notes: str = ""


@dataclass
class FaithfulnessReport:
    """Full faithfulness evaluation report."""
    paper_id: str
    task_id: str
    mode: str            # "reference_free" | "reference_based"
    components: List[ComponentScore]
    overall_score: float  # 1-5 scale
    summary: str
    strengths: List[str]
    weaknesses: List[str]


def _get_client():
    from openai import OpenAI
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _call_llm(prompt: str, max_tokens: int = 4000) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
        timeout=120,
    )
    return resp.choices[0].message.content


def _extract_json(text: str, expect_type: str = "auto"):
    """Robustly extract JSON from LLM response text.
    
    Args:
        text: Raw LLM response
        expect_type: "array", "object", or "auto"
    Returns:
        Parsed JSON object/array, or None on failure
    """
    text = text.strip()
    
    # Try 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try 2: Extract from markdown code block
    code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Try 3: Find first [ or { and match to last ] or }
    if expect_type in ("array", "auto"):
        arr_start = text.find('[')
        arr_end = text.rfind(']')
        if arr_start >= 0 and arr_end > arr_start:
            try:
                return json.loads(text[arr_start:arr_end+1])
            except json.JSONDecodeError:
                pass
    
    if expect_type in ("object", "auto"):
        obj_start = text.find('{')
        obj_end = text.rfind('}')
        if obj_start >= 0 and obj_end > obj_start:
            try:
                return json.loads(text[obj_start:obj_end+1])
            except json.JSONDecodeError:
                pass
    
    return None


# ═══════════════════════════════════════════════════════════════
#  STEP 1: Extract Key Components from Paper
# ═══════════════════════════════════════════════════════════════

EXTRACT_COMPONENTS_PROMPT = """You are an expert at analyzing academic papers to identify key implementation components needed for reproduction.

Given the following paper content, identify the KEY IMPLEMENTATION COMPONENTS that a correct reproduction must include. Organize them into three dimensions:

1. **Data Processing**: How data is obtained, preprocessed, augmented, and split
2. **Method**: Core algorithm/model implementation — the essential logic
3. **Evaluation**: How results are evaluated — metrics, protocols, baselines

For each component, specify:
- A clear description
- Importance: "high" (essential for correct results), "medium" (important but results may be close without it), "low" (nice to have)

Output as JSON array:
[
  {{"dimension": "data_processing"|"method"|"evaluation", "component": "...", "importance": "high"|"medium"|"low"}}
]

Paper content:
{paper_text}

Output ONLY the JSON array, no other text."""


EVALUATE_CODE_PROMPT = """You are an expert code reviewer evaluating whether reproduced code faithfully implements an academic paper's method.

Paper content:
{paper_text}

Key implementation components to check:
{components_json}

Reproduced code:
{code_text}

For EACH component listed above, evaluate:
- score: "full" (correctly implemented), "partial" (attempted but incomplete/incorrect), "missing" (not found)
- evidence: brief quote or explanation from the code supporting your judgment
- notes: any additional observations

Then provide:
- overall_score: 1-5 (1=completely wrong, 2=major issues, 3=partially correct, 4=mostly correct, 5=faithful)
- summary: 2-3 sentence overall assessment
- strengths: list of things done well
- weaknesses: list of issues found

Output as JSON:
{{
  "component_scores": [
    {{"dimension": "...", "component": "...", "importance": "...", "score": "full|partial|missing", "evidence": "...", "notes": "..."}}
  ],
  "overall_score": <float>,
  "summary": "...",
  "strengths": ["..."],
  "weaknesses": ["..."]
}}

Output ONLY the JSON, no other text."""


# ═══════════════════════════════════════════════════════════════
#  CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def extract_components(paper_text: str) -> List[Dict]:
    """Extract key implementation components from paper text."""
    prompt = EXTRACT_COMPONENTS_PROMPT.format(paper_text=paper_text[:15000])
    response = _call_llm(prompt, max_tokens=2000)

    # Parse JSON from response
    components = _extract_json(response, expect_type="array")
    if components and isinstance(components, list):
        return components
    
    print(f"[LLM Judge] Warning: Could not parse components JSON, using fallback")
    return [
        {"dimension": "method", "component": "Core algorithm implementation", "importance": "high"},
        {"dimension": "evaluation", "component": "Metric computation", "importance": "high"},
        {"dimension": "data_processing", "component": "Data loading and preprocessing", "importance": "medium"},
    ]


def collect_code_from_workspace(workspace: str) -> str:
    """Collect all Python code from a workspace directory."""
    ws = Path(workspace)
    code_parts = []

    # Priority order: reproduce.py first, then other .py files
    priority_files = ["reproduce.py", "main.py", "solver.py", "run.py"]
    seen = set()

    for pf in priority_files:
        for match in ws.rglob(pf):
            if match.is_file() and str(match) not in seen:
                seen.add(str(match))
                content = match.read_text(errors="ignore")
                code_parts.append(f"# === {match.relative_to(ws)} ===\n{content}")

    # Then all other .py files
    for py_file in sorted(ws.rglob("*.py")):
        if py_file.is_file() and str(py_file) not in seen:
            seen.add(str(py_file))
            content = py_file.read_text(errors="ignore")
            if len(content) > 50:  # skip trivial files
                code_parts.append(f"# === {py_file.relative_to(ws)} ===\n{content}")

    combined = "\n\n".join(code_parts)
    # Truncate if too long
    if len(combined) > 20000:
        combined = combined[:20000] + "\n\n# ... (truncated)"
    return combined


def evaluate_faithfulness(
    paper_text: str,
    code_text: str,
    paper_id: str = "unknown",
    task_id: str = "unknown",
    components: Optional[List[Dict]] = None,
) -> FaithfulnessReport:
    """Evaluate code faithfulness against paper description (Reference-Free mode).

    Args:
        paper_text: Paper markdown content
        code_text: Reproduced code (concatenated)
        paper_id: Paper identifier
        task_id: Task identifier
        components: Pre-extracted components (if None, will extract from paper)

    Returns:
        FaithfulnessReport with per-component scores and overall assessment
    """
    # Step 1: Extract components if not provided
    if components is None:
        print("[LLM Judge] Extracting key components from paper...")
        components = extract_components(paper_text)
        print(f"[LLM Judge] Found {len(components)} components to evaluate")

    # Step 2: Evaluate code against components
    print("[LLM Judge] Evaluating code faithfulness...")
    prompt = EVALUATE_CODE_PROMPT.format(
        paper_text=paper_text[:12000],
        components_json=json.dumps(components, indent=2),
        code_text=code_text[:18000],
    )
    response = _call_llm(prompt, max_tokens=6000)

    # Parse response with robust JSON extraction
    result = _extract_json(response, expect_type="object")
    if result is None or not isinstance(result, dict):
        print(f"[LLM Judge] Warning: Could not parse evaluation JSON")
        result = {
            "component_scores": [],
            "overall_score": 0.0,
            "summary": "Evaluation failed — could not parse LLM response",
            "strengths": [],
            "weaknesses": ["Evaluation parsing failed"],
        }

    # Build report
    comp_scores = []
    for cs in result.get("component_scores", []):
        comp_scores.append(ComponentScore(
            dimension=cs.get("dimension", "method"),
            component=cs.get("component", "unknown"),
            importance=cs.get("importance", "medium"),
            score=cs.get("score", "missing"),
            evidence=cs.get("evidence", ""),
            notes=cs.get("notes", ""),
        ))

    report = FaithfulnessReport(
        paper_id=paper_id,
        task_id=task_id,
        mode="reference_free",
        components=comp_scores,
        overall_score=float(result.get("overall_score", 0)),
        summary=result.get("summary", ""),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
    )

    return report


def evaluate_workspace(
    paper_text: str,
    workspace: str,
    paper_id: str = "unknown",
    task_id: str = "unknown",
) -> FaithfulnessReport:
    """Convenience function: evaluate all code in a workspace."""
    code_text = collect_code_from_workspace(workspace)
    if not code_text.strip():
        return FaithfulnessReport(
            paper_id=paper_id, task_id=task_id, mode="reference_free",
            components=[], overall_score=0.0,
            summary="No Python code found in workspace",
            strengths=[], weaknesses=["No code produced"],
        )
    return evaluate_faithfulness(paper_text, code_text, paper_id, task_id)


def print_report(report: FaithfulnessReport):
    """Pretty-print a faithfulness report."""
    print(f"\n{'='*60}")
    print(f"Code Faithfulness Report: {report.paper_id} / {report.task_id}")
    print(f"Mode: {report.mode} | Overall Score: {report.overall_score}/5.0")
    print(f"{'='*60}")
    print(f"\nSummary: {report.summary}")

    score_symbols = {"full": "○", "partial": "△", "missing": "×"}

    print(f"\nComponent Scores:")
    for cs in report.components:
        sym = score_symbols.get(cs.score, "?")
        print(f"  {sym} [{cs.dimension}] {cs.component} ({cs.importance})")
        if cs.evidence:
            print(f"      Evidence: {cs.evidence[:120]}")

    if report.strengths:
        print(f"\nStrengths:")
        for s in report.strengths:
            print(f"  + {s}")
    if report.weaknesses:
        print(f"\nWeaknesses:")
        for w in report.weaknesses:
            print(f"  - {w}")
    print()


def save_report(report: FaithfulnessReport, output_path: str):
    """Save report to JSON file."""
    data = asdict(report)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[LLM Judge] Report saved to: {output_path}")


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Judge — Code Faithfulness Evaluation")
    parser.add_argument("--paper", type=str, required=True, help="Path to paper markdown")
    parser.add_argument("--workspace", type=str, help="Path to workspace with reproduced code")
    parser.add_argument("--code", type=str, help="Path to a single code file to evaluate")
    parser.add_argument("--output", type=str, help="Path to save JSON report")
    parser.add_argument("--paper-id", type=str, default="unknown")
    parser.add_argument("--task-id", type=str, default="unknown")

    args = parser.parse_args()

    paper_text = Path(args.paper).read_text(encoding="utf-8")

    if args.workspace:
        report = evaluate_workspace(paper_text, args.workspace, args.paper_id, args.task_id)
    elif args.code:
        code_text = Path(args.code).read_text(encoding="utf-8")
        report = evaluate_faithfulness(paper_text, code_text, args.paper_id, args.task_id)
    else:
        # Just extract components (useful for debugging)
        print("[LLM Judge] No code provided — extracting components only")
        components = extract_components(paper_text)
        print(json.dumps(components, indent=2))
        exit(0)

    print_report(report)

    if args.output:
        save_report(report, args.output)
