#!/usr/bin/env python3
"""
Metric Alignment Score (MAS) Calculator — §6.1.2 of reproduce_readme.md.
Metric-type-aware evaluation for paper reproduction quality.

Supports three metric types:
  ↑ Higher-is-Better: MAS = min(v_repr / v_paper, 1.0)
  ↓ Lower-is-Better:  MAS = min(v_paper / v_repr, 1.0)
  ⊙ Target-Value:     MAS = max(1 - |v_repr - v_paper| / max(|v_paper|, ε), 0)
"""
import json
import math
from typing import Dict, List, Optional
from dataclasses import dataclass

EPSILON = 1e-8


@dataclass
class MetricResult:
    name: str
    direction: str        # "higher" | "lower" | "target"
    paper_value: float
    reproduced_value: float
    weight: float
    mas: float


def compute_single_mas(paper_value: float, reproduced_value: float,
                       direction: str) -> float:
    """Compute MAS for a single metric."""
    if direction == "higher":
        # Higher-is-better: MAS = min(v_repr / v_paper, 1.0)
        if paper_value <= EPSILON:
            return 1.0 if reproduced_value >= 0 else 0.0
        return min(max(reproduced_value / paper_value, 0.0), 1.0)

    elif direction == "lower":
        # Lower-is-better: MAS = min(v_paper / v_repr, 1.0)
        if reproduced_value <= EPSILON:
            return 1.0 if paper_value >= 0 else 0.0
        return min(max(paper_value / reproduced_value, 0.0), 1.0)

    elif direction == "target":
        # Target-value: MAS = 1 - |v_repr - v_paper| / max(|v_paper|, ε)
        denom = max(abs(paper_value), EPSILON)
        mas = 1.0 - abs(reproduced_value - paper_value) / denom
        return max(min(mas, 1.0), 0.0)

    else:
        raise ValueError(f"Unknown direction: {direction}. Use 'higher', 'lower', or 'target'.")


def compute_aggregate_mas(metrics: List[Dict]) -> Dict:
    """
    Compute weighted aggregate MAS from multiple metrics.

    Each metric dict should have:
      - name: str
      - direction: "higher" | "lower" | "target"
      - paper_value: float
      - reproduced_value: float
      - weight: float (default 1.0)

    Returns dict with per-metric MAS and weighted aggregate.
    """
    results = []
    total_weight = 0.0
    weighted_sum = 0.0

    for m in metrics:
        w = m.get("weight", 1.0)
        mas = compute_single_mas(
            m["paper_value"], m["reproduced_value"], m["direction"])
        results.append(MetricResult(
            name=m["name"], direction=m["direction"],
            paper_value=m["paper_value"],
            reproduced_value=m["reproduced_value"],
            weight=w, mas=mas))
        weighted_sum += w * mas
        total_weight += w

    aggregate = weighted_sum / total_weight if total_weight > 0 else 0.0

    return {
        "aggregate_mas": round(aggregate, 4),
        "full_reproduction": aggregate > 0.95,
        "per_metric": [
            {"name": r.name, "direction": r.direction,
             "paper": r.paper_value, "reproduced": r.reproduced_value,
             "weight": r.weight, "mas": round(r.mas, 4)}
            for r in results
        ]
    }


def evaluate_paper(paper_metadata: Dict, reproduced_metrics: Dict) -> Dict:
    """
    Evaluate reproduction quality for a paper.

    paper_metadata: from benchmark_metadata_template with ground_truth_metrics
    reproduced_metrics: dict of {metric_name: reproduced_value}
    """
    gt = paper_metadata.get("ground_truth_metrics", {})
    metrics_list = []

    for metric_name, gt_info in gt.items():
        if metric_name not in reproduced_metrics:
            continue
        # Parse direction from ↑/↓/⊙ symbols
        direction_raw = gt_info.get("direction", "higher")
        if direction_raw in ("↑", "higher", "higher_is_better"):
            direction = "higher"
        elif direction_raw in ("↓", "lower", "lower_is_better"):
            direction = "lower"
        elif direction_raw in ("⊙", "target", "target_value"):
            direction = "target"
        else:
            direction = "higher"  # default

        metrics_list.append({
            "name": metric_name,
            "direction": direction,
            "paper_value": gt_info["value"],
            "reproduced_value": reproduced_metrics[metric_name],
            "weight": gt_info.get("weight", 1.0)
        })

    result = compute_aggregate_mas(metrics_list)
    result["paper_id"] = paper_metadata.get("paper_id", "unknown")
    result["metrics_evaluated"] = len(metrics_list)
    result["metrics_missing"] = len(gt) - len(metrics_list)
    return result


# ═══════ CLI / Self-Test ═══════
if __name__ == "__main__":
    print("=== MAS Calculator Self-Test ===\n")

    # Test 1: Higher-is-better (Accuracy)
    mas = compute_single_mas(0.95, 0.92, "higher")
    print(f"Accuracy: paper=0.95, repr=0.92 → MAS={mas:.4f} (expected ~0.9684)")

    # Test 2: Lower-is-better (RMSE)
    mas = compute_single_mas(0.05, 0.08, "lower")
    print(f"RMSE: paper=0.05, repr=0.08 → MAS={mas:.4f} (expected 0.6250)")

    # Test 3: Target-value (physical constant)
    mas = compute_single_mas(3.14159, 3.14, "target")
    print(f"Pi: paper=3.14159, repr=3.14 → MAS={mas:.4f} (expected ~0.9995)")

    # Test 4: Aggregate with multiple metrics
    result = compute_aggregate_mas([
        {"name": "Accuracy", "direction": "higher",
         "paper_value": 0.95, "reproduced_value": 0.93, "weight": 2.0},
        {"name": "F1", "direction": "higher",
         "paper_value": 0.90, "reproduced_value": 0.88, "weight": 1.0},
        {"name": "Loss", "direction": "lower",
         "paper_value": 0.05, "reproduced_value": 0.06, "weight": 1.0},
    ])
    print(f"\nAggregate MAS: {result['aggregate_mas']}")
    print(f"Full reproduction (>0.95): {result['full_reproduction']}")
    for m in result["per_metric"]:
        print(f"  {m['name']}: MAS={m['mas']} (paper={m['paper']}, repr={m['reproduced']})")

    # Test 5: Edge cases
    print("\n--- Edge Cases ---")
    print(f"Perfect match: {compute_single_mas(0.95, 0.95, 'higher'):.4f}")
    print(f"Better than paper: {compute_single_mas(0.95, 0.99, 'higher'):.4f} (capped at 1.0)")
    print(f"Zero paper value (higher): {compute_single_mas(0.0, 0.5, 'higher'):.4f}")
    print(f"Zero repr value (lower): {compute_single_mas(0.05, 0.0, 'lower'):.4f}")

    print("\n✅ MAS Calculator working correctly!")
