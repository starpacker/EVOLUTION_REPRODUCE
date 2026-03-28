#!/usr/bin/env python3
"""
Sandbox Packager — Post-run artifact collector for Evolution-Reproduce.

After each paper reproduction run, this module:
1. Collects artifacts from the OpenHands workspace (code, results, visualizations)
2. Copies the input paper markdown
3. Packages everything into a structured sandbox directory
4. Generates a manifest.json summarizing the sandbox contents

Sandbox structure:
  data/sandboxes/{paper_id}/{timestamp}/
  ├── manifest.json           # Sandbox metadata and file inventory
  ├── input/
  │   └── paper.md            # Input paper markdown
  ├── code/
  │   ├── reproduce.py        # Main reproduction code (if produced)
  │   └── *.py                # Other generated Python files
  ├── data/
  │   └── *.{csv,npy,npz,json,pkl}  # Generated/downloaded data files
  ├── results/
  │   ├── results.json        # Agent's results output
  │   └── oh_result.json      # OpenHands run metadata
  └── visualizations/
      └── *.{png,jpg,svg,pdf} # Generated plots and images

Usage:
  from code.utils.sandbox_packager import package_sandbox
  sandbox_path = package_sandbox(
      paper_id="pyeit",
      workspace="/data/yjh/openhands_workspace/tier1_v2_pyeit_...",
      markdown_path="data/paper_markdowns_v2/pyeit_full.md",
      oh_result_path="data/reproduction_results_v2/pyeit_result.json",
  )
"""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

# ─── Project paths ───
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SANDBOXES_DIR = PROJECT_ROOT / "data" / "sandboxes"
PAPER_MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
RESULTS_DIR = PROJECT_ROOT / "data" / "reproduction_results_v2"

# File categories for collection
CODE_EXTENSIONS = {".py", ".sh", ".m", ".jl"}
DATA_EXTENSIONS = {".csv", ".npy", ".npz", ".json", ".pkl", ".h5", ".hdf5",
                   ".mat", ".dat", ".txt", ".tsv", ".parquet"}
VIZ_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".gif", ".bmp",
                  ".tif", ".tiff", ".eps"}
LOG_EXTENSIONS = {".log", ".out", ".err"}

# Files to skip (internal OpenHands artifacts)
SKIP_FILES = {
    ".task_prompt.txt",  # Internal prompt file
    ".bashrc",
    ".bash_history",
    ".profile",
}

# Max file size to copy (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def _classify_file(filepath: Path) -> str:
    """Classify a file into a sandbox subdirectory based on extension."""
    ext = filepath.suffix.lower()
    name = filepath.name.lower()

    # Special files
    if name == "results.json":
        return "results"
    if name == "reproduce.py":
        return "code"
    if name == "paper.md":
        return "input"

    # By extension
    if ext in CODE_EXTENSIONS:
        return "code"
    if ext in VIZ_EXTENSIONS:
        return "visualizations"
    if ext in DATA_EXTENSIONS:
        return "data"
    if ext in LOG_EXTENSIONS:
        return "logs"

    # Unknown — put in data
    return "data"


def _safe_copy(src: Path, dst: Path) -> bool:
    """Copy a file safely, skipping oversized or unreadable files."""
    try:
        if src.stat().st_size > MAX_FILE_SIZE:
            print(f"  ⚠️ Skipping (too large: {src.stat().st_size / 1024 / 1024:.1f}MB): {src.name}")
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except (OSError, shutil.Error) as e:
        print(f"  ⚠️ Failed to copy {src.name}: {e}")
        return False


def collect_workspace_files(workspace: str) -> Dict[str, List[Dict]]:
    """Scan workspace and classify all files into categories.

    Returns dict of category -> list of file info dicts.
    """
    ws = Path(workspace)
    if not ws.exists():
        return {}

    categories: Dict[str, List[Dict]] = {
        "code": [],
        "data": [],
        "results": [],
        "visualizations": [],
        "logs": [],
        "input": [],
    }

    for f in ws.rglob("*"):
        if not f.is_file():
            continue
        if f.name in SKIP_FILES:
            continue
        # Skip hidden files and __pycache__
        rel = f.relative_to(ws)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue

        category = _classify_file(f)
        file_info = {
            "name": f.name,
            "relative_path": str(rel),
            "absolute_path": str(f),
            "size_bytes": f.stat().st_size,
            "category": category,
        }
        categories[category].append(file_info)

    return categories


def package_sandbox(
    paper_id: str,
    workspace: str,
    markdown_path: Optional[str] = None,
    oh_result_path: Optional[str] = None,
    task_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    extra_metadata: Optional[Dict] = None,
) -> str:
    """Package all artifacts from a reproduction run into a structured sandbox.

    Args:
        paper_id: Paper identifier (e.g., "pyeit")
        workspace: Path to the OpenHands workspace directory
        markdown_path: Path to the input paper markdown (auto-detected if None)
        oh_result_path: Path to OpenHands result JSON (auto-detected if None)
        task_id: Task identifier for naming
        timestamp: Override timestamp for sandbox directory name
        extra_metadata: Additional metadata to include in manifest

    Returns:
        Absolute path to the created sandbox directory.
    """
    ts = timestamp or time.strftime("%Y%m%d_%H%M%S")
    sandbox_dir = SANDBOXES_DIR / paper_id / ts
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[Sandbox] Packaging sandbox for: {paper_id}")
    print(f"[Sandbox] Workspace: {workspace}")
    print(f"[Sandbox] Sandbox dir: {sandbox_dir}")
    print(f"{'='*60}")

    # Create subdirectories
    subdirs = ["input", "code", "data", "results", "visualizations", "logs"]
    for sd in subdirs:
        (sandbox_dir / sd).mkdir(exist_ok=True)

    file_manifest = []
    stats = {cat: 0 for cat in subdirs}

    # ── 1. Copy input paper markdown ──
    if markdown_path is None:
        # Auto-detect from paper_markdowns_v2
        for suffix in [f"{paper_id}_full.md", f"{paper_id}_task.md", f"{paper_id}.md"]:
            candidate = PAPER_MARKDOWN_DIR / suffix
            if candidate.exists():
                markdown_path = str(candidate)
                break

    if markdown_path and Path(markdown_path).exists():
        dst = sandbox_dir / "input" / "paper.md"
        if _safe_copy(Path(markdown_path), dst):
            file_manifest.append({
                "name": "paper.md",
                "category": "input",
                "source": markdown_path,
                "size_bytes": dst.stat().st_size,
            })
            stats["input"] += 1
            print(f"  ✅ Input: paper.md ({Path(markdown_path).name})")
    else:
        print(f"  ⚠️ No input markdown found for {paper_id}")

    # ── 2. Collect workspace files ──
    categories = collect_workspace_files(workspace)

    for category, files in categories.items():
        if category == "input":
            continue  # Already handled above
        for finfo in files:
            src = Path(finfo["absolute_path"])
            # For results.json, also put in results/
            dst = sandbox_dir / category / finfo["name"]

            # Handle name conflicts (add counter)
            if dst.exists():
                stem = dst.stem
                ext = dst.suffix
                counter = 1
                while dst.exists():
                    dst = sandbox_dir / category / f"{stem}_{counter}{ext}"
                    counter += 1

            if _safe_copy(src, dst):
                file_manifest.append({
                    "name": dst.name,
                    "category": category,
                    "source": finfo["relative_path"],
                    "size_bytes": src.stat().st_size,
                })
                stats[category] += 1

    # ── 3. Copy OH result JSON ──
    if oh_result_path is None:
        # Auto-detect
        candidate = RESULTS_DIR / f"{paper_id}_result.json"
        if candidate.exists():
            oh_result_path = str(candidate)
        else:
            # Try subdirectory pattern
            paper_results_dir = RESULTS_DIR / paper_id
            if paper_results_dir.exists():
                oh_files = sorted(paper_results_dir.glob(f"{paper_id}_*_oh_result.json"),
                                  key=os.path.getmtime, reverse=True)
                if oh_files:
                    oh_result_path = str(oh_files[0])

    if oh_result_path and Path(oh_result_path).exists():
        dst = sandbox_dir / "results" / "oh_result.json"
        if _safe_copy(Path(oh_result_path), dst):
            file_manifest.append({
                "name": "oh_result.json",
                "category": "results",
                "source": oh_result_path,
                "size_bytes": dst.stat().st_size,
            })
            stats["results"] += 1
            print(f"  ✅ Results: oh_result.json")

    # ── 4. Generate manifest ──
    manifest = {
        "paper_id": paper_id,
        "task_id": task_id or f"{paper_id}_{ts}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "workspace_source": workspace,
        "markdown_source": markdown_path,
        "sandbox_path": str(sandbox_dir),
        "file_stats": stats,
        "total_files": sum(stats.values()),
        "files": file_manifest,
    }
    if extra_metadata:
        manifest["extra"] = extra_metadata

    manifest_path = sandbox_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ── 5. Print summary ──
    print(f"\n[Sandbox] Summary:")
    for cat, count in stats.items():
        if count > 0:
            print(f"  {cat}: {count} file(s)")
    print(f"  Total: {sum(stats.values())} files")
    print(f"  Manifest: {manifest_path}")
    print(f"[Sandbox] ✅ Sandbox packaged: {sandbox_dir}")

    return str(sandbox_dir)


def package_from_result_json(result_path: str) -> str:
    """Convenience: package sandbox from an existing result JSON file.

    Extracts paper_id, workspace, etc. from the result JSON.
    """
    with open(result_path) as f:
        result = json.load(f)

    paper_id = result.get("paper_id", "")
    workspace = result.get("workspace", "")
    task_id = result.get("task_id", "")

    if not paper_id:
        paper_id = Path(result_path).stem.replace("_result", "").replace("_oh_result", "")

    if not workspace:
        # Try to reconstruct
        if task_id:
            workspace = f"/data/yjh/openhands_workspace/task_{task_id}"

    return package_sandbox(
        paper_id=paper_id,
        workspace=workspace,
        task_id=task_id,
        extra_metadata={"source_result": result_path},
    )


def package_all_existing(results_dir: Optional[str] = None) -> List[str]:
    """Package sandboxes for all existing reproduction results.

    Scans the results directory and packages any that don't have sandboxes yet.
    """
    rdir = Path(results_dir) if results_dir else RESULTS_DIR
    if not rdir.exists():
        print(f"Results directory not found: {rdir}")
        return []

    packaged = []

    # Scan for result JSON files (flat pattern: {paper_id}_result.json)
    for rf in sorted(rdir.glob("*_result.json")):
        paper_id = rf.stem.replace("_result", "")
        try:
            with open(rf) as f:
                data = json.load(f)
            workspace = data.get("workspace", "")
            if not workspace:
                # Try to find workspace from session info
                session = data.get("session", "")
                if session:
                    workspace = f"/data/yjh/openhands_workspace/{session}"

            if workspace and Path(workspace).exists():
                sandbox_path = package_sandbox(
                    paper_id=paper_id,
                    workspace=workspace,
                    oh_result_path=str(rf),
                    extra_metadata={"source_result": str(rf)},
                )
                packaged.append(sandbox_path)
            else:
                print(f"  ⚠️ Workspace not found for {paper_id}: {workspace}")
        except Exception as e:
            print(f"  ❌ Error packaging {paper_id}: {e}")

    # Scan for result JSON files (nested pattern: {paper_id}/{task_id}_result.json)
    for paper_dir in sorted(rdir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        result_files = sorted(paper_dir.glob(f"{paper_id}_*_result.json"),
                              key=os.path.getmtime, reverse=True)
        if not result_files:
            continue

        rf = result_files[0]  # Latest result
        try:
            with open(rf) as f:
                data = json.load(f)
            workspace = data.get("workspace", "")
            task_id = data.get("task_id", "")

            if not workspace and task_id:
                workspace = f"/data/yjh/openhands_workspace/task_{task_id}"

            if workspace and Path(workspace).exists():
                sandbox_path = package_sandbox(
                    paper_id=paper_id,
                    workspace=workspace,
                    task_id=task_id,
                    oh_result_path=str(rf),
                    extra_metadata={"source_result": str(rf)},
                )
                packaged.append(sandbox_path)
            else:
                print(f"  ⚠️ Workspace not found for {paper_id}: {workspace}")
        except Exception as e:
            print(f"  ❌ Error packaging {paper_id}: {e}")

    print(f"\n{'='*60}")
    print(f"[Sandbox] Packaged {len(packaged)} sandboxes total")
    print(f"{'='*60}")
    return packaged


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Package reproduction artifacts into structured sandboxes")
    parser.add_argument("--paper-id", type=str,
                        help="Paper ID to package")
    parser.add_argument("--workspace", type=str,
                        help="Path to OpenHands workspace")
    parser.add_argument("--markdown", type=str,
                        help="Path to input paper markdown")
    parser.add_argument("--result", type=str,
                        help="Path to result JSON file (auto-package)")
    parser.add_argument("--all", action="store_true",
                        help="Package all existing results")

    args = parser.parse_args()

    if args.all:
        package_all_existing()
    elif args.result:
        package_from_result_json(args.result)
    elif args.paper_id and args.workspace:
        package_sandbox(
            paper_id=args.paper_id,
            workspace=args.workspace,
            markdown_path=args.markdown,
        )
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Package a specific run:")
        print("  python -m code.utils.sandbox_packager --paper-id pyeit \\")
        print("    --workspace /data/yjh/openhands_workspace/tier1_v2_pyeit_...")
        print("")
        print("  # Package from result JSON:")
        print("  python -m code.utils.sandbox_packager --result data/reproduction_results_v2/pyeit_result.json")
        print("")
        print("  # Package all existing results:")
        print("  python -m code.utils.sandbox_packager --all")
