#!/usr/bin/env python3
"""
Batch seed Experience DB from qualifying trajectories.
Run: python3 code/experience_db/seed_from_trajectories.py
"""
from trajectory_parser import process_trajectory
from experience_db import ExperienceDB, Experience
import json, time, uuid, os, sys

TRAJ_DIR = "/data/yjh/openhands_results_v2/trajectories"

# All trajectories with max_fail >= 3
CANDIDATES = [
    ("p2e_a2caa5bd-506b857c363bc566d2a.json", "p2e_a2caa5bd", "unknown"),
    ("p2e_64a38422-43f726e0d4b8594f249.json", "p2e_64a38422", "unknown"),
    ("p2e_ebcbef3e-3d5f9aef5164b66aa08.json", "p2e_ebcbef3e", "unknown"),
    ("oh_carspy-main_a-a7f0f72fd067a63.json", "carspy", "spectroscopy"),
    ("p2e_ceef5980-48705d28ab6fad586be.json", "p2e_ceef5980", "unknown"),
    ("p2e_d7987c03-1623a23ca08dd7c06b1.json", "p2e_d7987c03", "unknown"),
    ("p2e_3b4a23d1-65df16de61bbe8dc74d.json", "p2e_3b4a23d1", "unknown"),
    ("p2e_bc961f2e-e9738de5b7497522188.json", "p2e_bc961f2e", "unknown"),
]

def main():
    db = ExperienceDB()
    total = 0
    for fname, name, domain in CANDIDATES:
        fpath = os.path.join(TRAJ_DIR, fname)
        if not os.path.exists(fpath):
            print(f"SKIP (not found): {fname}")
            continue
        exps = process_trajectory(fpath, name, domain)
        for exp_data in exps:
            cond = exp_data.get("condition", {})
            act = exp_data.get("action", {})
            exp = Experience(
                id=f"exp_{time.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                type=exp_data.get("type", "positive"),
                domain_hint=exp_data.get("domain_hint", "unknown"),
                condition=cond, action=act,
                rationale=exp_data.get("rationale", ""),
                metadata={"source_paper": name,
                           "creation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "score": 5.0, "call_count": 0, "success_count": 0},
                status="verified")
            eid = db.add(exp)
            total += 1
            print(f"  Added: {eid}")
    print(f"\n{'='*40}")
    print(f"Seeding complete. Added {total} experiences.")
    print(f"DB stats: {db.stats()}")

if __name__ == "__main__":
    main()
