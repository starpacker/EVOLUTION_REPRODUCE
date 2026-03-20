# Evolution-Reproduce

**An Autonomous Paper Reproduction System with Failure-Driven Learning and Evolutionary Experience Memory**

> Given only a scientific paper (PDF or arXiv ID), an LLM-powered agent autonomously reproduces its key experimental results from scratch — no starter code, no pre-prepared data, no human intervention.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [ReproduceBench](#reproducebench)
- [Evaluation](#evaluation)
- [License](#license)

---

## Overview

**Evolution-Reproduce** is a research framework that investigates whether LLM coding agents can autonomously reproduce experiments described in academic papers. The system is built on three core research hypotheses:

1. **Failure-Driven Learning (H1):** Recording *only failure episodes* (and their fixes) yields higher-quality experience than logging all trajectories.
2. **Anti-Pollution Retrieval (H2):** Cosine similarity gating prevents experience entries from the *same* paper from leaking into the agent's context, ensuring true zero-shot generalization.
3. **Evolutionary Fusion (H3):** When multiple experience entries for the same error pattern exist, an LLM-as-judge selects the best fix via competitive evaluation, distilling stronger experience over time.

The system uses [OpenHands](https://github.com/All-Hands-AI/OpenHands) as the underlying AI coding agent runtime.

## Key Features

| Feature | Description |
|---|---|
| **End-to-End Reproduction** | Paper PDF/arXiv → Markdown → Agent Prompt → Code → Reproduced Metrics |
| **ReproduceBench** | 15 curated papers across computational imaging, optics, signal processing, medical imaging |
| **Experience Database** | Vector-indexed SQLite store of failure-fix episodes for cross-task transfer |
| **LLM-as-Judge** | Multi-dimensional evaluation (data processing, method, metrics) |
| **MAS Calculator** | Metric Accuracy Score with directional awareness (↑/↓) |
| **Sandbox Isolation** | Conda-based environments prevent cross-contamination |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Evolution-Reproduce                 │
│                                                       │
│  ┌──────────┐    ┌────────────┐    ┌──────────────┐  │
│  │  Paper    │───▸│  Planner   │───▸│  OpenHands   │  │
│  │  (PDF/MD) │    │  Agent     │    │  CodeAct     │  │
│  └──────────┘    └─────┬──────┘    └──────┬───────┘  │
│                        │                   │          │
│                        ▼                   ▼          │
│               ┌────────────────┐   ┌──────────────┐  │
│               │  Experience DB │   │   Sandbox    │  │
│               │  (Vector+SQL)  │   │  (Conda env) │  │
│               └────────────────┘   └──────────────┘  │
│                        │                   │          │
│                        ▼                   ▼          │
│               ┌──────────────────────────────────┐   │
│               │      Evaluation Pipeline          │   │
│               │   LLM Judge  +  MAS Calculator    │   │
│               └──────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Project Structure

```
Evolution_reproduce/
├── README.md                          # This file
├── requirements.txt                   # Core Python dependencies
├── requirements-ocr.txt               # Extra deps for PDF parsing (PaddleOCR)
├── .gitignore
├── reproduce_readme.md                # Full research plan & design document
├── prompt.md                          # AI execution engine prompt specification
├── progress_and_next_step.md          # Project progress tracker
│
├── code/                              # Source code
│   ├── agent/
│   │   └── planner.py                 # Reproduction orchestrator (experience-augmented)
│   ├── baseline/
│   │   └── run_baseline.py            # B2 baseline (OpenHands-only, no experience)
│   ├── evaluation/
│   │   ├── evaluate_run.py            # Post-run evaluation pipeline
│   │   ├── llm_judge.py              # LLM-as-Judge scoring
│   │   └── mas_calculator.py          # Metric Accuracy Score calculator
│   ├── experience_db/
│   │   ├── experience_db.py           # Vector-indexed experience store (SQLite + numpy)
│   │   ├── trajectory_parser.py       # Extract failure-fix episodes from trajectories
│   │   └── seed_from_trajectories.py  # Batch-seed DB from trajectory files
│   └── utils/
│       ├── arxiv_to_markdown.py       # arXiv paper download & MD conversion
│       ├── ocr_paper_parser.py        # PDF → Markdown via PaddleOCR
│       ├── sandbox_manager.py         # Conda sandbox lifecycle management
│       ├── sandbox_cleanup.sh         # Kill orphan sandbox processes
│       └── verify_llm_api.py          # LLM API connectivity check
│
├── data/
│   ├── ReproduceBench/                # Benchmark dataset
│   │   ├── paper_registry.json        # Paper metadata registry
│   │   ├── paper_registry_v2.json     # Extended registry (15 papers)
│   │   ├── benchmark_metadata_template.json
│   │   ├── pdfs/                      # Paper PDFs (15 papers, ~110MB)
│   │   └── tier_{1,2,3}_*/           # Tier-specific configs
│   ├── paper_markdowns_v2/            # Pre-converted paper markdowns (30 files)
│   ├── agent_prompts_v2/             # Generated agent prompts
│   ├── arxiv_papers/                  # Downloaded arXiv papers
│   ├── experience_db/                # Experience DB data files
│   ├── reproduction_results_v2/      # Reproduction run results (JSON)
│   └── _archived_old_invalid/        # Archived early-stage results
│
├── logs/                              # Runtime logs
│   ├── sandbox_stdout/               # Per-paper sandbox output logs
│   └── trajectories/                 # Agent trajectory recordings
│
└── results/                           # Final experiment results
    ├── main_experiment/              # Evolution agent results
    ├── baselines/                    # Baseline comparison results
    └── ablations/                    # Ablation study results
```

## Installation

### Prerequisites

- **Python 3.10+**
- **Conda** (for sandbox isolation)
- **OpenHands** (AI coding agent runtime)
- An LLM API key (e.g., OpenAI, Anthropic, or compatible gateway)

### Step 1: Clone the Repository

```bash
git clone https://github.com/starpacker/EVOLUTION_REPRODUCE.git
cd EVOLUTION_REPRODUCE
```

### Step 2: Install Core Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install OpenHands

```bash
pip install openhands-ai
```

Or follow the [OpenHands installation guide](https://docs.all-hands.dev/modules/usage/installation) for Docker-based setup.

### Step 4 (Optional): Install OCR Dependencies

Only needed if you want to convert PDFs to Markdown locally:

```bash
pip install -r requirements-ocr.txt
```

## Configuration

### LLM API Setup

The system requires access to an LLM API. Set the following environment variables:

```bash
export LLM_API_KEY="your-api-key-here"
export LLM_BASE_URL="https://api.openai.com/v1"   # or your gateway URL
export LLM_MODEL="gpt-4o"                          # or claude-sonnet-4, etc.
```

You can verify your API connection:

```bash
python code/utils/verify_llm_api.py
```

### OpenHands Configuration

OpenHands reads from `~/.openhands/config.toml`. See the [OpenHands docs](https://docs.all-hands.dev/) for configuration details.

## Usage

### Baseline Reproduction (B2)

Run the baseline agent (OpenHands-only, no experience injection) on a single paper:

```bash
# From a pre-existing markdown
python code/baseline/run_baseline.py --markdown data/paper_markdowns_v2/pyeit_full.md

# From an arXiv ID
python code/baseline/run_baseline.py --arxiv-id 2301.10137

# From a local PDF
python code/baseline/run_baseline.py --pdf data/ReproduceBench/pdfs/pyeit.pdf

# Batch mode from the paper registry
python code/baseline/run_baseline.py --registry data/ReproduceBench/paper_registry_v2.json
```

### Evolution Agent with Experience

Run the full Evolution agent with experience retrieval:

```bash
python code/agent/planner.py \
    --paper_id pyeit \
    --use_experience \
    --experience_db data/experience_db/experience_meta.db
```

### Evaluation

Evaluate a completed reproduction run:

```bash
# Full evaluation pipeline (LLM Judge + MAS)
python code/evaluation/evaluate_run.py --run_dir data/reproduction_results_v2/ --paper_id pyeit

# LLM Judge only
python code/evaluation/llm_judge.py \
    --paper data/paper_markdowns_v2/pyeit_full.md \
    --workspace /path/to/agent/workspace
```

### Experience Database Management

```bash
# Seed the experience DB from existing trajectories
cd code/experience_db
python seed_from_trajectories.py --trajectory_dir ../../logs/trajectories/

# Query the experience DB
python experience_db.py --query "scipy sparse matrix solver error" --top_k 3
```

## ReproduceBench

ReproduceBench is a curated benchmark of 15 scientific computing papers organized into three difficulty tiers:

| Tier | Difficulty | Papers | Characteristics |
|------|-----------|--------|-----------------|
| **Tier 1** | Easy | 5 | Well-documented, standard libraries, clear metrics |
| **Tier 2** | Medium | 5 | Custom algorithms, moderate data processing |
| **Tier 3** | Hard | 5 | Complex pipelines, domain-specific knowledge required |

**Domains covered:** Computational Imaging, Signal Processing, Optics, Medical Imaging, Electrical Impedance Tomography, Interferometry, Photoacoustic Tomography, and more.

Each paper includes:
- Original PDF in `data/ReproduceBench/pdfs/`
- Pre-converted Markdown in `data/paper_markdowns_v2/` (both `*_full.md` for the complete paper and `*_task.md` for task-focused extraction)
- Metadata in `data/ReproduceBench/paper_registry_v2.json`

## Evaluation Metrics

### Metric Accuracy Score (MAS)

Quantitative comparison of reproduced vs. paper-reported metrics:

```
MAS(m) = max(0, 1 - |reproduced - reference| / |reference|)
```

With directional awareness: metrics marked ↑ (higher-is-better) or ↓ (lower-is-better) are scored accordingly.

### LLM Judge Score

Multi-dimensional code quality evaluation across:
- **Data Processing:** Data loading, preprocessing, augmentation
- **Method Implementation:** Core algorithm, model architecture, training loop
- **Evaluation:** Metric computation, visualization, result reporting

Each component scored as `full` / `partial` / `missing` with evidence-backed justification.

## Development Notes

- **Root-level `.py` scripts** (`launch_tier1_v2.py`, `relaunch_crashed_tier1.py`, etc.) are operational launch scripts used during experiments. They are included for reproducibility of the experimental workflow.
- **`reproduce_readme.md`** contains the complete research plan with 12 detailed sections covering design, architecture, and evaluation methodology.
- **`prompt.md`** is the AI execution engine prompt that drives the autonomous research workflow.

## License

This project is released for research purposes. Please cite appropriately if you use this work.
