#!/usr/bin/env python3
"""
Experience Database for Project Evolution-Reproduce.
Implements the Experience Memory System (§4.4, §4.5 of reproduce_readme.md).

Uses numpy for vector storage + SQLite for metadata/scoring.
Embedding via aliyun/text-embedding-v4 (1024-dim) through OpenAI-compatible API.
"""

import json
import os
import time
import uuid
import sqlite3
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# API configuration
API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
EMBEDDING_MODEL = "aliyun/text-embedding-v4"
RERANKER_MODEL = "cds/GPT-5-mini"  # Cost-efficient model for reranking (gpt-4o unavailable)
EMBEDDING_DIM = 1024

# Score update hyperparams (§4.6.3)
ALPHA = 0.3
BETA_1 = 2.0   # success reward multiplier
BETA_2 = 0.5   # partial reward multiplier
GAMMA = 3.0    # failure penalty

# DB paths
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "experience_db")


@dataclass
class Experience:
    """Experience data structure per §4.4.2 schema."""
    id: str
    type: str              # "positive" | "negative"
    domain_hint: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    rationale: str
    metadata: Dict[str, Any]
    status: str = "verified"  # "verified" | "hypothesis"


class ExperienceDB:
    """Experience Database with vector search + metadata + scoring."""

    def __init__(self, db_dir: str = None):
        self.db_dir = db_dir or DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self.sqlite_path = os.path.join(self.db_dir, "experience_meta.db")
        self.vectors_path = os.path.join(self.db_dir, "vectors.json")

        from openai import OpenAI
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

        self._init_sqlite()
        self._load_vectors()

    # ──────────────── init helpers ────────────────

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY, type TEXT NOT NULL, domain_hint TEXT,
            condition_json TEXT NOT NULL, action_json TEXT NOT NULL,
            rationale TEXT, source_paper TEXT, creation_time TEXT,
            score REAL DEFAULT 5.0, call_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0, last_used TEXT,
            lineage TEXT, status TEXT DEFAULT 'verified',
            tier TEXT DEFAULT 'silver')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS gap_markers (
            id TEXT PRIMARY KEY, query_snapshot TEXT NOT NULL,
            task_id TEXT, iteration INTEGER, timestamp TEXT,
            resolved INTEGER DEFAULT 0)""")
        conn.commit()
        conn.close()

    def _load_vectors(self):
        self.vectors: Dict[str, np.ndarray] = {}
        if os.path.exists(self.vectors_path):
            with open(self.vectors_path) as f:
                data = json.load(f)
            self.vectors = {k: np.array(v) for k, v in data.items()}

    def _save_vectors(self):
        with open(self.vectors_path, "w") as f:
            json.dump({k: v.tolist() for k, v in self.vectors.items()}, f)

    # ──────────────── embedding ────────────────

    def _embed(self, text: str) -> np.ndarray:
        text = text[:8000]
        resp = self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return np.array(resp.data[0].embedding)

    @staticmethod
    def _search_text(exp: Experience) -> str:
        parts = [
            f"Error/Symptom: {exp.condition.get('error_or_symptom', '')}",
            f"Context: {exp.condition.get('task_context', '')}",
            f"Solution: {exp.action.get('solution', '')}",
        ]
        env = exp.condition.get("environment")
        if env:
            parts.append(f"Environment: {env}")
        return "\n".join(parts)

    # ──────────────── tier logic (§4.7.3) ────────────────

    @staticmethod
    def _compute_tier(score: float, success_count: int) -> str:
        if score > 8.0 and success_count >= 5:
            return "gold"
        if score > 3.0:
            return "silver"
        return "bronze"

    # ══════════════════ CRUD ══════════════════

    def add(self, exp: Experience) -> str:
        if not exp.id:
            exp.id = f"exp_{time.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        self.vectors[exp.id] = self._embed(self._search_text(exp))
        self._save_vectors()

        conn = sqlite3.connect(self.sqlite_path)
        conn.execute(
            """INSERT OR REPLACE INTO experiences
            (id,type,domain_hint,condition_json,action_json,rationale,
             source_paper,creation_time,score,call_count,success_count,
             last_used,lineage,status,tier)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (exp.id, exp.type, exp.domain_hint,
             json.dumps(exp.condition), json.dumps(exp.action), exp.rationale,
             exp.metadata.get("source_paper", ""),
             exp.metadata.get("creation_time", time.strftime("%Y-%m-%dT%H:%M:%S")),
             exp.metadata.get("score", 5.0),
             exp.metadata.get("call_count", 0),
             exp.metadata.get("success_count", 0),
             exp.metadata.get("last_used"),
             json.dumps(exp.metadata.get("lineage")) if exp.metadata.get("lineage") else None,
             exp.status,
             self._compute_tier(exp.metadata.get("score", 5.0),
                                exp.metadata.get("success_count", 0))))
        conn.commit()
        conn.close()
        return exp.id

    def get(self, exp_id: str) -> Optional[Experience]:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM experiences WHERE id=?", (exp_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return Experience(
            id=row["id"], type=row["type"], domain_hint=row["domain_hint"],
            condition=json.loads(row["condition_json"]),
            action=json.loads(row["action_json"]),
            rationale=row["rationale"],
            metadata=dict(source_paper=row["source_paper"],
                          creation_time=row["creation_time"],
                          score=row["score"], call_count=row["call_count"],
                          success_count=row["success_count"],
                          last_used=row["last_used"],
                          lineage=json.loads(row["lineage"]) if row["lineage"] else None),
            status=row["status"])

    def count(self) -> int:
        conn = sqlite3.connect(self.sqlite_path)
        n = conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        conn.close()
        return n

    def all_ids(self) -> List[str]:
        conn = sqlite3.connect(self.sqlite_path)
        rows = conn.execute("SELECT id FROM experiences").fetchall()
        conn.close()
        return [r[0] for r in rows]

    # ══════════════════ SEARCH (§4.5) ══════════════════

    def search_stage1(self, query: str, top_k: int = 10,
                      min_sim: float = 0.7) -> List[Dict]:
        """Stage 1: Dense retrieval via cosine similarity."""
        if not self.vectors:
            return []
        qvec = self._embed(query)
        results = []
        for eid, vec in self.vectors.items():
            sim = float(np.dot(qvec, vec) / (np.linalg.norm(qvec) * np.linalg.norm(vec) + 1e-9))
            if sim >= min_sim:
                results.append({"id": eid, "similarity": sim})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]
        # attach full experience objects
        for r in results:
            r["experience"] = self.get(r["id"])
        return results

    def search_stage2_rerank(self, query: str, candidates: List[Dict],
                             strict: bool = False) -> List[Dict]:
        """
        Stage 2: LLM Reranker (§4.5.2).
        Returns filtered list with relevance judgments.
        """
        if not candidates:
            return []

        # Build candidate descriptions
        cand_texts = []
        for i, c in enumerate(candidates):
            exp = c["experience"]
            cand_texts.append(
                f"[{i}] Condition: {exp.condition.get('error_or_symptom','')}\n"
                f"    Context: {exp.condition.get('task_context','')}\n"
                f"    Solution: {exp.action.get('solution','')}\n"
                f"    Type: {exp.type}")

        prompt = f"""You are an experience relevance judge. Given the current problem and candidate experiences, judge each.

【Current Problem】
{query}

【Candidates】
{chr(10).join(cand_texts)}

For each candidate [i], output EXACTLY one line:
[i] RELEVANT | PARTIAL | IRRELEVANT

Rules:
1. RELEVANT = condition root cause matches AND solution directly applies
2. PARTIAL = some reference value but not exact match
3. IRRELEVANT = not applicable
If ALL are irrelevant, add a final line: NONE
Be strict — prefer NONE over uncertain injection."""

        resp = self.client.chat.completions.create(
            model=RERANKER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.0)
        text = resp.choices[0].message.content

        # Parse results
        ranked = []
        for i, c in enumerate(candidates):
            tag = "IRRELEVANT"
            for line in text.strip().split("\n"):
                if line.strip().startswith(f"[{i}]"):
                    if "RELEVANT" in line and "IRRELEVANT" not in line:
                        tag = "RELEVANT"
                    elif "PARTIAL" in line:
                        tag = "PARTIAL"
            if strict and tag != "RELEVANT":
                continue
            if tag == "IRRELEVANT":
                continue
            ranked.append({**c, "relevance": tag})
        return ranked

    def retrieve(self, query: str, max_inject: int = 3,
                 exploration_ratio: float = 0.5) -> List[Dict]:
        """
        Full two-stage retrieval with exploration-aware control (§4.5).
        exploration_ratio: 1.0 = early (relaxed), 0.0 = late (strict).
        """
        # Adjust params based on exploration ratio
        if exploration_ratio > 0.66:
            min_sim, top_k, strict = 0.7, 10, False
        elif exploration_ratio > 0.33:
            min_sim, top_k, strict = 0.8, 10, False
        else:
            min_sim, top_k, strict = 0.9, 10, True
            max_inject = min(max_inject, 1)

        stage1 = self.search_stage1(query, top_k=top_k, min_sim=min_sim)
        if not stage1:
            return []

        # Cost control: if top-1 similarity > 0.95, skip Reranker
        if stage1[0]["similarity"] > 0.95:
            return [stage1[0]]

        stage2 = self.search_stage2_rerank(query, stage1, strict=strict)
        return stage2[:max_inject]

    # ══════════════════ SCORING (§4.6) ══════════════════

    def update_score(self, exp_id: str, outcome: str, difficulty: float = 3.0):
        """
        Update experience score after usage.
        outcome: "success" | "partial" | "failure"
        difficulty: task difficulty d ∈ [1.0, 5.0]
        """
        if outcome == "success":
            reward = BETA_1 * difficulty
        elif outcome == "partial":
            reward = BETA_2 * difficulty
        else:
            reward = -GAMMA / max(difficulty, 0.5)

        conn = sqlite3.connect(self.sqlite_path)
        row = conn.execute(
            "SELECT score, call_count, success_count FROM experiences WHERE id=?",
            (exp_id,)).fetchone()
        if not row:
            conn.close()
            return

        new_score = row[0] + ALPHA * reward
        new_calls = row[1] + 1
        new_success = row[2] + (1 if outcome == "success" else 0)
        new_tier = self._compute_tier(new_score, new_success)

        conn.execute(
            """UPDATE experiences SET score=?, call_count=?, success_count=?,
               last_used=?, tier=? WHERE id=?""",
            (new_score, new_calls, new_success,
             time.strftime("%Y-%m-%dT%H:%M:%S"), new_tier, exp_id))
        conn.commit()
        conn.close()

    # ══════════════════ GAP MARKERS (§4.5.4) ══════════════════

    def add_gap_marker(self, query_snapshot: Dict, task_id: str, iteration: int):
        gid = f"gap_{uuid.uuid4().hex[:8]}"
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute(
            "INSERT INTO gap_markers (id,query_snapshot,task_id,iteration,timestamp) VALUES (?,?,?,?,?)",
            (gid, json.dumps(query_snapshot), task_id, iteration,
             time.strftime("%Y-%m-%dT%H:%M:%S")))
        conn.commit()
        conn.close()

    # ══════════════════ STATS ══════════════════

    def stats(self) -> Dict:
        conn = sqlite3.connect(self.sqlite_path)
        total = conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        gold = conn.execute("SELECT COUNT(*) FROM experiences WHERE tier='gold'").fetchone()[0]
        silver = conn.execute("SELECT COUNT(*) FROM experiences WHERE tier='silver'").fetchone()[0]
        bronze = conn.execute("SELECT COUNT(*) FROM experiences WHERE tier='bronze'").fetchone()[0]
        hypo = conn.execute("SELECT COUNT(*) FROM experiences WHERE status='hypothesis'").fetchone()[0]
        gaps = conn.execute("SELECT COUNT(*) FROM gap_markers WHERE resolved=0").fetchone()[0]
        conn.close()
        return dict(total=total, gold=gold, silver=silver, bronze=bronze,
                    hypothesis=hypo, unresolved_gaps=gaps)


# ══════════════════ Quick test ══════════════════
if __name__ == "__main__":
    db = ExperienceDB()
    print(f"DB initialized at: {db.db_dir}")
    print(f"Stats: {db.stats()}")

    # Add a test experience
    test_exp = Experience(
        id="exp_test_001",
        type="positive",
        domain_hint="computational_physics",
        condition={
            "error_or_symptom": "RuntimeError: singular matrix in np.linalg.solve",
            "task_context": "Implementing FEM solver for 2D heat equation",
            "environment": "Python 3.10, NumPy 1.24, SciPy 1.11",
            "failed_attempts_summary": [
                "Tried direct inversion — singular matrix",
                "Tried adding epsilon to diagonal — results diverged"
            ]
        },
        action={
            "solution": "Use scipy.sparse.linalg.spsolve with sparse CSR matrix; apply Dirichlet BC before assembly",
            "code_implement": "from scipy.sparse.linalg import spsolve\nx = spsolve(K_sparse, F)",
            "verification": "Solver converges, L2 error < 1e-6 vs analytical solution"
        },
        rationale="Dense solver fails because stiffness matrix is singular without proper BCs",
        metadata={
            "source_paper": "test_paper",
            "score": 5.0, "call_count": 0, "success_count": 0
        }
    )
    eid = db.add(test_exp)
    print(f"Added experience: {eid}")
    print(f"Stats after add: {db.stats()}")

    # Test search
    results = db.search_stage1(
        "singular matrix error when solving linear system in finite element code",
        top_k=3)
    for r in results:
        print(f"  Found: {r['id']} sim={r['similarity']:.3f}")

    print("\n✅ Experience DB working correctly!")
