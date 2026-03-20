#!/usr/bin/env python3
"""
arxiv_to_markdown.py — Download paper from arxiv and convert to markdown.

This is the core pipeline for Project Evolution-Reproduce:
  arxiv ID → PDF download → PaddleOCR PPStructureV3 → Markdown

Usage:
  python arxiv_to_markdown.py --arxiv-id 2301.10137 --output-dir ./output
  python arxiv_to_markdown.py --arxiv-id 2301.10137  # defaults to data/arxiv_papers/
  python arxiv_to_markdown.py --arxiv-url https://arxiv.org/abs/2301.10137 --output-dir ./output
  python arxiv_to_markdown.py --pdf /path/to/local.pdf --output-dir ./output  # skip download, just OCR

Outputs:
  {output_dir}/{arxiv_id}.pdf       — downloaded PDF
  {output_dir}/{arxiv_id}.md        — converted markdown
  {output_dir}/{arxiv_id}_images/   — extracted images (if any)
"""

import argparse
import os
import re
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# === Configuration ===
PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "arxiv_papers"
PADDLE_PYTHON = "/home/yjh/.conda/envs/paddle_env/bin/python"
OCR_SCRIPT = "/home/yjh/new_flow/run_ocr_tool.py"

# arxiv PDF URL patterns
ARXIV_PDF_URL = "https://arxiv.org/pdf/{arxiv_id}.pdf"
ARXIV_ABS_URL = "https://arxiv.org/abs/{arxiv_id}"

# Retry settings
MAX_DOWNLOAD_RETRIES = 3
RETRY_DELAY = 5  # seconds


def normalize_arxiv_id(input_str: str) -> str:
    """Extract arxiv ID from various input formats.
    
    Handles:
      - Pure ID: "2301.10137"
      - With version: "2301.10137v2"  
      - Full URL: "https://arxiv.org/abs/2301.10137"
      - PDF URL: "https://arxiv.org/pdf/2301.10137.pdf"
    """
    input_str = input_str.strip()
    
    # Match arxiv ID pattern (YYMM.NNNNN or YYMM.NNNNNvN)
    pattern = r'(\d{4}\.\d{4,5}(?:v\d+)?)'
    match = re.search(pattern, input_str)
    if match:
        return match.group(1)
    
    # Also handle old-style IDs like "hep-ph/0301001"
    old_pattern = r'([a-z-]+/\d{7}(?:v\d+)?)'
    match = re.search(old_pattern, input_str)
    if match:
        return match.group(1)
    
    raise ValueError(f"Cannot extract arxiv ID from: {input_str}")


def download_pdf(arxiv_id: str, output_dir: Path) -> Path:
    """Download PDF from arxiv.org.
    
    Returns the path to the downloaded PDF file.
    """
    pdf_url = ARXIV_PDF_URL.format(arxiv_id=arxiv_id)
    # Clean ID for filename (replace / with _)
    safe_id = arxiv_id.replace("/", "_")
    pdf_path = output_dir / f"{safe_id}.pdf"
    
    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        print(f"  PDF already exists: {pdf_path} ({pdf_path.stat().st_size} bytes)")
        return pdf_path
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
        print(f"  Downloading (attempt {attempt}/{MAX_DOWNLOAD_RETRIES}): {pdf_url}")
        try:
            result = subprocess.run(
                [
                    "curl", "-L", "-f", "-s", "-S",
                    "--connect-timeout", "30",
                    "--max-time", "120",
                    "-o", str(pdf_path),
                    "-H", "User-Agent: Evolution-Reproduce/1.0 (Academic Research)",
                    pdf_url
                ],
                capture_output=True, text=True, timeout=150
            )
            
            if result.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 1000:
                print(f"  ✅ Downloaded: {pdf_path} ({pdf_path.stat().st_size} bytes)")
                return pdf_path
            else:
                stderr = result.stderr.strip() if result.stderr else "unknown error"
                size = pdf_path.stat().st_size if pdf_path.exists() else 0
                print(f"  ⚠️ Download issue: returncode={result.returncode}, size={size}, stderr={stderr}")
                if pdf_path.exists() and pdf_path.stat().st_size < 1000:
                    pdf_path.unlink()
                    
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Download timed out")
        except Exception as e:
            print(f"  ⚠️ Download error: {e}")
        
        if attempt < MAX_DOWNLOAD_RETRIES:
            print(f"  Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    
    raise RuntimeError(f"Failed to download PDF after {MAX_DOWNLOAD_RETRIES} attempts: {pdf_url}")


def get_paper_metadata(arxiv_id: str) -> dict:
    """Fetch basic metadata from arxiv (title, authors, abstract).
    
    Uses the arxiv API (Atom XML feed).
    """
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "15", "--max-time", "30", api_url],
            capture_output=True, text=True, timeout=45
        )
        if result.returncode != 0:
            return {"arxiv_id": arxiv_id, "title": "Unknown", "authors": [], "abstract": ""}
        
        xml = result.stdout
        
        # Simple XML parsing (avoid dependency on lxml)
        title = ""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', xml, re.DOTALL)
        if title_match:
            # Skip the feed title, get the entry title
            titles = re.findall(r'<title[^>]*>(.*?)</title>', xml, re.DOTALL)
            if len(titles) >= 2:
                title = titles[1].strip().replace('\n', ' ')
            elif titles:
                title = titles[0].strip().replace('\n', ' ')
        
        authors = re.findall(r'<name>(.*?)</name>', xml)
        
        abstract = ""
        summary_match = re.search(r'<summary[^>]*>(.*?)</summary>', xml, re.DOTALL)
        if summary_match:
            abstract = summary_match.group(1).strip().replace('\n', ' ')
        
        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract[:500]  # truncate long abstracts
        }
    except Exception as e:
        print(f"  ⚠️ Could not fetch metadata: {e}")
        return {"arxiv_id": arxiv_id, "title": "Unknown", "authors": [], "abstract": ""}


def run_ocr(pdf_path: Path, output_dir: Path) -> Path:
    """Run PaddleOCR PPStructureV3 to convert PDF to Markdown.
    
    Returns the path to the generated markdown file.
    """
    print(f"  Running PaddleOCR on: {pdf_path}")
    print(f"  Output dir: {output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = subprocess.run(
        [PADDLE_PYTHON, OCR_SCRIPT, "--pdf", str(pdf_path), "--output_dir", str(output_dir)],
        capture_output=True, text=True, timeout=600  # 10 min timeout for OCR
    )
    
    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "unknown"
        raise RuntimeError(f"PaddleOCR failed (exit code {result.returncode}): {stderr}")
    
    # Parse the RESULT_PATH from stdout
    md_path = None
    for line in result.stdout.split('\n'):
        if line.startswith("RESULT_PATH:"):
            md_path = Path(line.replace("RESULT_PATH:", "").strip())
            break
    
    # Fallback: look for .md file in output dir
    if md_path is None or not md_path.exists():
        stem = pdf_path.stem
        candidates = list(output_dir.glob(f"{stem}*.md"))
        if candidates:
            md_path = candidates[0]
        else:
            # Check recursively
            candidates = list(output_dir.rglob("*.md"))
            if candidates:
                md_path = candidates[0]
    
    if md_path is None or not md_path.exists():
        raise RuntimeError(f"OCR completed but no markdown file found in {output_dir}")
    
    print(f"  ✅ Markdown generated: {md_path} ({md_path.stat().st_size} bytes)")
    return md_path


def arxiv_to_markdown(
    arxiv_id: str = None,
    arxiv_url: str = None, 
    pdf_path: str = None,
    output_dir: str = None
) -> dict:
    """Main pipeline: arxiv → PDF → Markdown.
    
    Args:
        arxiv_id: arxiv paper ID (e.g., "2301.10137")
        arxiv_url: arxiv URL (alternative to arxiv_id)
        pdf_path: local PDF path (skip download)
        output_dir: output directory
    
    Returns:
        dict with paths and metadata
    """
    # Resolve output dir
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = DEFAULT_OUTPUT_DIR
    
    # Step 1: Resolve arxiv ID and download PDF
    if pdf_path:
        pdf = Path(pdf_path)
        if not pdf.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        safe_id = pdf.stem
        metadata = {"arxiv_id": "local", "title": safe_id}
        print(f"[1/3] Using local PDF: {pdf}")
    else:
        if arxiv_url:
            arxiv_id = normalize_arxiv_id(arxiv_url)
        elif arxiv_id:
            arxiv_id = normalize_arxiv_id(arxiv_id)
        else:
            raise ValueError("Must provide either arxiv_id, arxiv_url, or pdf_path")
        
        safe_id = arxiv_id.replace("/", "_")
        print(f"[1/3] Downloading PDF for arxiv:{arxiv_id}")
        metadata = get_paper_metadata(arxiv_id)
        print(f"  Title: {metadata.get('title', 'Unknown')}")
        
        pdf_dir = out_dir / "pdfs"
        pdf = download_pdf(arxiv_id, pdf_dir)
    
    # Step 2: Run OCR
    print(f"[2/3] Converting PDF to Markdown via PaddleOCR")
    md_dir = out_dir / "markdowns"
    md_path = run_ocr(pdf, md_dir)
    
    # Step 3: Verify output quality
    print(f"[3/3] Verifying output quality")
    md_content = md_path.read_text(encoding="utf-8")
    md_size = len(md_content)
    md_lines = md_content.count('\n')
    md_words = len(md_content.split())
    
    quality_ok = True
    quality_notes = []
    
    if md_size < 1000:
        quality_ok = False
        quality_notes.append(f"WARNING: Markdown too small ({md_size} bytes)")
    if md_lines < 20:
        quality_ok = False
        quality_notes.append(f"WARNING: Too few lines ({md_lines})")
    if md_words < 200:
        quality_ok = False
        quality_notes.append(f"WARNING: Too few words ({md_words})")
    
    if quality_ok:
        print(f"  ✅ Quality OK: {md_size} bytes, {md_lines} lines, {md_words} words")
    else:
        for note in quality_notes:
            print(f"  ⚠️ {note}")
    
    # Build result
    result = {
        "arxiv_id": arxiv_id or "local",
        "metadata": metadata,
        "pdf_path": str(pdf),
        "markdown_path": str(md_path),
        "markdown_stats": {
            "size_bytes": md_size,
            "lines": md_lines,
            "words": md_words
        },
        "quality_ok": quality_ok,
        "quality_notes": quality_notes,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save result metadata
    result_json_path = out_dir / f"{safe_id}_pipeline_result.json"
    with open(result_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Pipeline result saved: {result_json_path}")
    
    return result


def batch_download(arxiv_ids: list, output_dir: str = None) -> list:
    """Download and convert multiple papers.
    
    Args:
        arxiv_ids: list of arxiv IDs
        output_dir: output directory
    
    Returns:
        list of results
    """
    results = []
    for i, aid in enumerate(arxiv_ids):
        print(f"\n{'='*60}")
        print(f"Paper {i+1}/{len(arxiv_ids)}: {aid}")
        print(f"{'='*60}")
        try:
            result = arxiv_to_markdown(arxiv_id=aid, output_dir=output_dir)
            results.append(result)
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            results.append({"arxiv_id": aid, "error": str(e)})
        
        # Rate limiting: be nice to arxiv
        if i < len(arxiv_ids) - 1:
            print(f"  Waiting 3s (rate limit)...")
            time.sleep(3)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY: {len(results)} papers")
    successes = sum(1 for r in results if "error" not in r)
    print(f"  ✅ Success: {successes}")
    print(f"  ❌ Failed: {len(results) - successes}")
    for r in results:
        status = "✅" if "error" not in r else "❌"
        aid = r.get("arxiv_id", "?")
        if "error" in r:
            print(f"  {status} {aid}: {r['error']}")
        else:
            print(f"  {status} {aid}: {r['markdown_stats']['words']} words")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download arxiv paper and convert to markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single paper by ID
  python arxiv_to_markdown.py --arxiv-id 2301.10137
  
  # Single paper by URL
  python arxiv_to_markdown.py --arxiv-url https://arxiv.org/abs/2301.10137
  
  # Local PDF (skip download)
  python arxiv_to_markdown.py --pdf /path/to/paper.pdf --output-dir ./output
  
  # Batch mode
  python arxiv_to_markdown.py --batch 2301.10137 2302.00001 2303.12345
  
  # Custom output dir
  python arxiv_to_markdown.py --arxiv-id 2301.10137 --output-dir /tmp/papers
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--arxiv-id", type=str, help="arxiv paper ID (e.g., 2301.10137)")
    group.add_argument("--arxiv-url", type=str, help="arxiv URL")
    group.add_argument("--pdf", type=str, help="Local PDF path (skip download)")
    group.add_argument("--batch", nargs="+", type=str, help="Multiple arxiv IDs for batch processing")
    
    parser.add_argument("--output-dir", type=str, default=None,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    
    args = parser.parse_args()
    
    try:
        if args.batch:
            results = batch_download(args.batch, args.output_dir)
            sys.exit(0 if all("error" not in r for r in results) else 1)
        else:
            result = arxiv_to_markdown(
                arxiv_id=args.arxiv_id,
                arxiv_url=args.arxiv_url,
                pdf_path=args.pdf,
                output_dir=args.output_dir
            )
            sys.exit(0 if result.get("quality_ok") else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
