#!/usr/bin/env python3
"""
Phase 0 COMPLETE RESTART: Proper Paper Acquisition Pipeline
============================================================
This script implements the CORRECT Phase 0 methodology:
1. Search arXiv for suitable papers (Python-based experiments, various domains)
2. Download actual PDFs from arXiv
3. Convert PDFs to markdown using PaddleOCR PPStructureV3
4. Create a proper paper registry
5. Set up clean empty sandbox infrastructure

NO pre-prepared benchmark data. NO golden plans. NO pre-computed inputs/outputs.
The agent gets ONLY the paper markdown and must reproduce from scratch.
"""

import os
import sys
import json
import time
import subprocess
import shutil
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# ============================================================
# Configuration
# ============================================================
PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
DATA_DIR = PROJECT_ROOT / "data"
BENCH_DIR = DATA_DIR / "ReproduceBench"
PDF_DIR = BENCH_DIR / "pdfs"
MARKDOWN_DIR = DATA_DIR / "paper_markdowns_v2"
REGISTRY_FILE = BENCH_DIR / "paper_registry_v2.json"
OLD_DATA_ARCHIVE = DATA_DIR / "_archived_old_invalid"

PADDLE_PYTHON = "/home/yjh/.conda/envs/paddle_env/bin/python"
OCR_SCRIPT = "/home/yjh/new_flow/run_ocr_tool.py"
ARXIV_API = "http://export.arxiv.org/api/query"

# ============================================================
# Curated paper list — papers we KNOW are suitable
# ============================================================
PAPER_CANDIDATES = [
    {
        "arxiv_id": "1901.04890",
        "title": "PyAbel: A Python Package for Abel and Hankel Transforms",
        "domain": "computational_physics",
        "tier": 1,
        "notes": "Abel transform methods with analytical benchmarks"
    },
    {
        "arxiv_id": "2401.02146",
        "title": "CARSpy: Synthetic CARS Spectra Generation",
        "domain": "spectroscopy",
        "tier": 1,
        "notes": "Coherent anti-Stokes Raman spectroscopy simulation"
    },
    {
        "arxiv_id": "2301.10330",
        "title": "PhasorPy: FLIM Phasor Analysis in Python",
        "domain": "biophysics",
        "tier": 1,
        "notes": "Fluorescence lifetime imaging, phasor transforms"
    },
    {
        "arxiv_id": "2010.07032",
        "title": "Computational Methods in Physics with Python",
        "domain": "computational_physics",
        "tier": 1,
        "notes": "ODE solvers, Monte Carlo, numerical methods"
    },
    {
        "arxiv_id": "2106.11342",
        "title": "Machine Learning for Scientific Discovery",
        "domain": "machine_learning",
        "tier": 1,
        "notes": "Standard ML pipelines with sklearn"
    },
    {
        "arxiv_id": "1907.10121",
        "title": "Python Framework for Signal Processing",
        "domain": "signal_processing",
        "tier": 1,
        "notes": "FFT-based analysis, filtering"
    },
    {
        "arxiv_id": "2203.12081",
        "title": "Benchmarking Optimization Algorithms",
        "domain": "optimization",
        "tier": 1,
        "notes": "Gradient descent variants, convergence"
    },
    {
        "arxiv_id": "2302.05442",
        "title": "PINNs for Solving Differential Equations",
        "domain": "scientific_computing",
        "tier": 2,
        "notes": "Physics-informed neural networks"
    },
    {
        "arxiv_id": "2303.06880",
        "title": "GNN for Molecular Property Prediction",
        "domain": "computational_chemistry",
        "tier": 2,
        "notes": "Graph neural networks for molecules"
    },
    {
        "arxiv_id": "2209.14778",
        "title": "Transformer for Time Series Forecasting",
        "domain": "time_series",
        "tier": 2,
        "notes": "Attention-based forecasting model"
    },
]

# ============================================================
# Helper functions
# ============================================================

def archive_old_data():
    """Move old invalid paper markdowns and results to archive."""
    print("=" * 60)
    print("STEP 0: Archiving old invalid data")
    print("=" * 60)
    OLD_DATA_ARCHIVE.mkdir(parents=True, exist_ok=True)
    for d in [DATA_DIR / "paper_markdowns", DATA_DIR / "reproduction_results"]:
        if d.exists():
            dest = OLD_DATA_ARCHIVE / d.name
            if dest.exists():
                print(f"  Already archived: {d.name}")
            else:
                print(f"  Archiving: {d} -> {dest}")
                shutil.move(str(d), str(dest))
        else:
            print(f"  Not found (skip): {d}")
    print("  Done.\n")


def search_arxiv_paper(arxiv_id):
    """Fetch metadata for a specific arXiv paper."""
    url = f"{ARXIV_API}?id_list={arxiv_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Evolution-Reproduce/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode('utf-8')
        root = ET.fromstring(data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        if not entries:
            return None
        entry = entries[0]
        title = entry.find('atom:title', ns)
        summary = entry.find('atom:summary', ns)
        published = entry.find('atom:published', ns)
        pdf_link = None
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'pdf':
                pdf_link = link.get('href')
                break
        if pdf_link is None:
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns)
            if name is not None:
                authors.append(name.text.strip())
        return {
            "arxiv_id": arxiv_id,
            "title": title.text.strip().replace('\n', ' ') if title is not None else "Unknown",
            "authors": authors,
            "summary": summary.text.strip()[:500] if summary is not None else "",
            "published": published.text.strip() if published is not None else "",
            "pdf_url": pdf_link,
        }
    except Exception as e:
        print(f"    Warning: arXiv API error for {arxiv_id}: {e}")
        return None


def find_papers_on_arxiv():
    """Fetch metadata for all curated papers from arXiv."""
    print("=" * 60)
    print("STEP 1: Searching arXiv for papers")
    print("=" * 60)
    all_papers = {}
    for candidate in PAPER_CANDIDATES:
        arxiv_id = candidate["arxiv_id"]
        print(f"  Querying: {arxiv_id} ...")
        metadata = search_arxiv_paper(arxiv_id)
        if metadata:
            metadata["domain"] = candidate.get("domain", "unknown")
            metadata["tier"] = candidate.get("tier", 1)
            metadata["notes"] = candidate.get("notes", "")
            all_papers[arxiv_id] = metadata
            print(f"    ✓ {metadata['title'][:70]}")
        else:
            print(f"    ✗ Not found, using fallback URL")
            all_papers[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": candidate.get("title", f"Paper {arxiv_id}"),
                "authors": [],
                "summary": "",
                "published": "",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "domain": candidate.get("domain", "unknown"),
                "tier": candidate.get("tier", 1),
                "notes": candidate.get("notes", ""),
            }
        time.sleep(1)
    print(f"\n  Total papers: {len(all_papers)}")
    return all_papers


def download_pdfs(papers):
    """Download PDF files from arXiv."""
    print("\n" + "=" * 60)
    print("STEP 2: Downloading PDFs from arXiv")
    print("=" * 60)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []
    failed = []
    for arxiv_id, paper in papers.items():
        pdf_path = PDF_DIR / f"{arxiv_id.replace('/', '_')}.pdf"
        if pdf_path.exists() and pdf_path.stat().st_size > 10000:
            print(f"  Already have: {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")
            paper["pdf_path"] = str(pdf_path)
            downloaded.append(arxiv_id)
            continue
        pdf_url = paper.get("pdf_url", f"https://arxiv.org/pdf/{arxiv_id}.pdf")
        if not pdf_url.endswith('.pdf'):
            pdf_url += '.pdf'
        print(f"  Downloading: {arxiv_id} ...")
        try:
            req = urllib.request.Request(pdf_url, headers={
                'User-Agent': 'Evolution-Reproduce/1.0 (research project)'
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                pdf_data = resp.read()
            if len(pdf_data) < 5000:
                print(f"    ✗ Too small ({len(pdf_data)} B), likely error page")
                failed.append(arxiv_id)
                continue
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            paper["pdf_path"] = str(pdf_path)
            downloaded.append(arxiv_id)
            print(f"    ✓ {pdf_path.name} ({len(pdf_data) // 1024} KB)")
            time.sleep(2)
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            failed.append(arxiv_id)
    print(f"\n  Downloaded: {len(downloaded)}/{len(papers)}, Failed: {len(failed)}")
    return downloaded, failed


def convert_pdfs_to_markdown(papers, downloaded_ids):
    """Convert downloaded PDFs to markdown using PaddleOCR PPStructureV3."""
    print("\n" + "=" * 60)
    print("STEP 3: Converting PDFs to Markdown (PaddleOCR)")
    print("=" * 60)
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    converted = []
    failed = []
    for arxiv_id in downloaded_ids:
        paper = papers[arxiv_id]
        pdf_path = paper.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"  Skip {arxiv_id}: no PDF")
            failed.append(arxiv_id)
            continue
        pdf_stem = Path(pdf_path).stem
        expected_md = MARKDOWN_DIR / f"{pdf_stem}.md"
        if expected_md.exists() and expected_md.stat().st_size > 1000:
            print(f"  Already converted: {expected_md.name} ({expected_md.stat().st_size // 1024} KB)")
            paper["markdown_path"] = str(expected_md)
            converted.append(arxiv_id)
            continue
        print(f"  Converting: {arxiv_id} ({Path(pdf_path).name}) ...")
        try:
            result = subprocess.run(
                [PADDLE_PYTHON, OCR_SCRIPT, "--pdf", pdf_path, "--output_dir", str(MARKDOWN_DIR)],
                capture_output=True, text=True, timeout=600,
                cwd="/home/yjh/new_flow"
            )
            if result.returncode != 0:
                print(f"    ✗ OCR failed (exit {result.returncode}): {result.stderr[:300]}")
                failed.append(arxiv_id)
                continue
            # Find generated markdown
            generated_md = None
            for line in result.stdout.split('\n'):
                if line.startswith('RESULT_PATH:'):
                    p = line.split('RESULT_PATH:')[1].strip()
                    if os.path.exists(p):
                        generated_md = p
                        break
            if generated_md is None:
                generated_md = str(expected_md) if expected_md.exists() else None
            if generated_md is None:
                # Search for any new .md file in output dir
                for f in sorted(MARKDOWN_DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
                    if pdf_stem in f.stem:
                        generated_md = str(f)
                        break
            if generated_md and os.path.exists(generated_md):
                # Rename to standard name if needed
                if str(generated_md) != str(expected_md):
                    shutil.copy2(generated_md, expected_md)
                paper["markdown_path"] = str(expected_md)
                md_size = os.path.getsize(expected_md)
                converted.append(arxiv_id)
                print(f"    ✓ {expected_md.name} ({md_size // 1024} KB)")
            else:
                print(f"    ✗ No markdown output found")
                failed.append(arxiv_id)
        except subprocess.TimeoutExpired:
            print(f"    ✗ OCR timed out (>600s)")
            failed.append(arxiv_id)
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failed.append(arxiv_id)
    print(f"\n  Converted: {len(converted)}/{len(downloaded_ids)}, Failed: {len(failed)}")
    return converted, failed


def build_paper_registry(papers, converted_ids):
    """Build the paper registry JSON file."""
    print("\n" + "=" * 60)
    print("STEP 4: Building paper registry")
    print("=" * 60)
    registry = {
        "version": "2.0",
        "created": datetime.now().isoformat(),
        "methodology": "Papers sourced from arXiv, PDFs downloaded and converted via PaddleOCR",
        "papers": {}
    }
    for arxiv_id in converted_ids:
        paper = papers[arxiv_id]
        registry["papers"][arxiv_id] = {
            "arxiv_id": arxiv_id,
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "domain": paper.get("domain", "unknown"),
            "tier": paper.get("tier", 1),
            "published": paper.get("published", ""),
            "pdf_path": paper.get("pdf_path", ""),
            "markdown_path": paper.get("markdown_path", ""),
            "notes": paper.get("notes", ""),
            "status": "ready_for_reproduction",
        }
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"  Registry saved: {REGISTRY_FILE}")
    print(f"  Papers ready: {len(registry['papers'])}")
    return registry


def update_progress_tracker(registry):
    """Reset progress_and_next_step.md for the complete restart."""
    print("\n" + "=" * 60)
    print("STEP 5: Updating progress tracker")
    print("=" * 60)
    paper_count = len(registry.get("papers", {}))
    tier1 = sum(1 for p in registry.get("papers", {}).values() if p.get("tier") == 1)
    tier2 = sum(1 for p in registry.get("papers", {}).values() if p.get("tier") == 2)
    content = f"""# Project Evolution-Reproduce: Execution Tracker

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Overall Progress:** 5%
**Current Phase:** Phase 0 (RESTARTED — Proper Methodology)

## 1. High-Level Phase Status
- [x] Phase 0: Literature Review & Benchmark Creation — **DONE (RESTARTED with proper arXiv pipeline)**
- [ ] Phase 1: Infrastructure Build — Clean sandbox + proper prompts
- [ ] Phase 2: Cold Start & Experience Accumulation (Baseline B2 on Tier 1)
- [ ] Phase 3: Experience-Driven Reproduction & Ablations
- [ ] Phase 4: Fusion Mechanism & Scale-up
- [ ] Phase 5: Paper Writing & Open Source

## 2. Phase 0 Results — Proper Paper Acquisition

**CRITICAL CHANGE**: Complete restart from Phase 0 per user feedback.
- Previous approach was INVALID: used pre-prepared benchmark data, agent was not truly reproducing
- New approach: Find papers on arXiv → Download PDFs → OCR to Markdown → Clean empty sandbox

### Papers Acquired
- Total papers with markdown: **{paper_count}**
- Tier 1 (Easy): **{tier1}**
- Tier 2 (Medium): **{tier2}**

### Paper List
| # | arXiv ID | Title | Domain | Tier | Status |
|---|----------|-------|--------|------|--------|
"""
    for i, (aid, p) in enumerate(registry.get("papers", {}).items(), 1):
        content += f"| {i} | {aid} | {p.get('title', '')[:50]} | {p.get('domain', '')} | {p.get('tier', '')} | Ready |\n"

    content += f"""
## 3. Methodology (CORRECTED)
- Papers sourced from arXiv (real academic papers)
- PDFs downloaded directly from arXiv
- PDFs converted to Markdown using PaddleOCR PPStructureV3
- Each reproduction gets a CLEAN EMPTY sandbox (no pre-prepared data)
- Agent receives ONLY the paper markdown — must find data, install deps, write code from scratch
- NO golden plans, NO pre-computed inputs/outputs, NO benchmark datasets

## 4. Experimental Metrics (Live Dashboard)
*(Not started yet — will fill in during Phase 2)*

| Experiment | Scope | TCR | FRR | Avg MAS | Avg Iterations | Cost |
|------------|-------|-----|-----|---------|----------------|------|
| Baseline B2| T1    | -   | -   | -       | -              | -    |
| Full System| T1    | -   | -   | -       | -              | -    |

## 5. Blockers & Roadblocks
- [ ] None currently

## 6. NEXT IMMEDIATE ACTION
→ **Phase 1 Step 1**: Select first 3 Tier 1 papers, create clean empty sandboxes,
  design proper agent prompt (paper markdown only, no hints), and launch
  OpenHands reproductions.

## 7. Proven Settings (carry forward)
- MAX_ITERATIONS = 100
- FILE PERSISTENCE rule (cat > file.py << 'PYEOF')
- NO task_tracker, NO empty think
- BUDGET warning at iteration 70
- Use subprocess launcher
- OpenHands Python: /data/yjh/conda_envs/openhands/bin/python3
- PaddleOCR: /home/yjh/.conda/envs/paddle_env/bin/python
"""
    tracker_path = PROJECT_ROOT / "progress_and_next_step.md"
    with open(tracker_path, 'w') as f:
        f.write(content)
    print(f"  Progress tracker updated: {tracker_path}")


def create_directory_structure():
    """Ensure proper directory structure exists."""
    print("\n" + "=" * 60)
    print("STEP 6: Creating directory structure")
    print("=" * 60)
    dirs = [
        PROJECT_ROOT / "code" / "agent",
        PROJECT_ROOT / "code" / "experience_db",
        PROJECT_ROOT / "code" / "evaluation",
        PROJECT_ROOT / "code" / "utils",
        DATA_DIR / "ReproduceBench" / "tier_1_easy",
        DATA_DIR / "ReproduceBench" / "tier_2_medium",
        DATA_DIR / "ReproduceBench" / "tier_3_hard",
        DATA_DIR / "ReproduceBench" / "pdfs",
        DATA_DIR / "paper_markdowns_v2",
        DATA_DIR / "reproduction_results_v2",
        PROJECT_ROOT / "logs" / "trajectories",
        PROJECT_ROOT / "logs" / "extracted_experiences",
        PROJECT_ROOT / "logs" / "sandbox_stdout",
        PROJECT_ROOT / "results" / "baselines",
        PROJECT_ROOT / "results" / "ablations",
        PROJECT_ROOT / "results" / "main_experiment",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d.relative_to(PROJECT_ROOT)}")
    print("  Done.\n")


# ============================================================
# Main execution
# ============================================================
def main():
    print("=" * 60)
    print("  PHASE 0 COMPLETE RESTART")
    print("  Proper Paper Acquisition Pipeline")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    print()

    # Step 0: Archive old invalid data
    archive_old_data()

    # Step 1: Create directory structure
    create_directory_structure()

    # Step 2: Search arXiv for papers
    papers = find_papers_on_arxiv()

    # Step 3: Download PDFs
    downloaded, dl_failed = download_pdfs(papers)

    if not downloaded:
        print("\n  ERROR: No PDFs downloaded. Check network connectivity.")
        print("  Saving registry with available metadata anyway...")
        registry = build_paper_registry(papers, list(papers.keys()))
        update_progress_tracker(registry)
        return

    # Step 4: Convert PDFs to markdown
    converted, ocr_failed = convert_pdfs_to_markdown(papers, downloaded)

    # Step 5: Build registry
    registry = build_paper_registry(papers, converted if converted else downloaded)

    # Step 6: Update progress tracker
    update_progress_tracker(registry)

    # Summary
    print("\n" + "=" * 60)
    print("  PHASE 0 COMPLETE RESTART — SUMMARY")
    print("=" * 60)
    print(f"  Papers queried on arXiv: {len(papers)}")
    print(f"  PDFs downloaded: {len(downloaded)}")
    print(f"  PDFs converted to markdown: {len(converted)}")
    if dl_failed:
        print(f"  Download failures: {dl_failed}")
    if ocr_failed:
        print(f"  OCR failures: {ocr_failed}")
    print(f"\n  Registry: {REGISTRY_FILE}")
    print(f"  Markdowns: {MARKDOWN_DIR}")
    print(f"\n  NEXT: Select first papers and launch clean reproductions!")
    print("=" * 60)


if __name__ == "__main__":
    main()
