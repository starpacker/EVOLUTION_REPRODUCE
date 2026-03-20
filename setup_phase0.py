#!/usr/bin/env python3
"""Phase 0 Setup: Copy local papers + build registry"""
import os, json, shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("/home/yjh/Evolution_reproduce")
MARKDOWN_DIR = PROJECT_ROOT / "data" / "paper_markdowns_v2"
PDF_DIR = PROJECT_ROOT / "data" / "ReproduceBench" / "pdfs"
REGISTRY_FILE = PROJECT_ROOT / "data" / "ReproduceBench" / "paper_registry_v2.json"
INPUT_DIR = Path("/home/yjh/new_flow/input")

MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

PAPERS = {
    "pyeit": {"title": "PyEIT: A Python-based Framework for Electrical Impedance Tomography", "domain": "biomedical_imaging", "tier": 1, "pdf": "pyeit.pdf", "md_full": "output_2/pyeit.md", "md_task": "input/pyeit.md", "notes": "EIT reconstruction, FEM mesh, JAC/GREIT/BP algorithms"},
    "bpm": {"title": "Beam Propagation Method for Optical Waveguide Simulation", "domain": "computational_optics", "tier": 1, "pdf": "bpm.pdf", "md_full": "output_2/bpm.md", "md_task": "input/bpm.md", "notes": "Beam propagation in waveguides, FFT-based simulation"},
    "pat": {"title": "Photoacoustic Tomography Image Reconstruction", "domain": "biomedical_imaging", "tier": 1, "pdf": "pat.pdf", "md_full": "output_2/pat.md", "md_task": "input/pat.md", "notes": "PAT reconstruction, time-reversal, k-Wave"},
    "insar": {"title": "InSAR Phase Unwrapping and Deformation Analysis", "domain": "remote_sensing", "tier": 1, "pdf": "insar.pdf", "md_full": "output_2/insar.md", "md_task": "input/insar.md", "notes": "Interferometric SAR, phase unwrapping algorithms"},
    "diff": {"title": "Diffraction Pattern Simulation and Analysis", "domain": "computational_optics", "tier": 1, "pdf": "diff.pdf", "md_full": "output_2/diff.md", "md_task": "input/diff.md", "notes": "Diffraction simulation, Fresnel/Fraunhofer"},
    "fpm_inr": {"title": "Fourier Ptychographic Microscopy with Implicit Neural Representations", "domain": "computational_imaging", "tier": 2, "pdf": "fpm_inr.pdf", "md_full": "output_2/fpm_inr.md", "md_task": "input/fpm_inr.md", "notes": "FPM + INR, neural network-based phase retrieval"},
    "lensless": {"title": "Lensless Imaging via ADMM-based Reconstruction", "domain": "computational_imaging", "tier": 2, "pdf": "lenseless.pdf", "md_full": "output_2/lenseless.md", "md_task": "input/lensless_admm.md", "notes": "Lensless camera, PSF deconvolution, ADMM optimization"},
    "pnp_cassi": {"title": "Plug-and-Play CASSI: Coded Aperture Snapshot Spectral Imaging", "domain": "computational_imaging", "tier": 2, "pdf": "pnp_cassi.pdf", "md_full": "output_2/pnp_cassi.md", "md_task": "input/pnp_cassi.md", "notes": "CASSI hyperspectral imaging, PnP-ADMM reconstruction"},
    "oopao": {"title": "OOPAO: Object-Oriented Python Adaptive Optics Simulation", "domain": "adaptive_optics", "tier": 2, "pdf": "oopao.pdf", "md_full": "output_2/oopao.md", "md_task": "input/oopao_sh_wfs.md", "notes": "Adaptive optics, Shack-Hartmann WFS, Zernike modes"},
    "lenstronomy": {"title": "Lenstronomy: Gravitational Lens Modeling in Python", "domain": "astrophysics", "tier": 2, "pdf": "lenstronomy.pdf", "md_full": "output_2/lenstronomy.md", "md_task": "input/lenstronomy_simple_ring.md", "notes": "Gravitational lensing simulation and modeling"},
    "lfm": {"title": "Light Field Microscopy: Computational Reconstruction", "domain": "computational_imaging", "tier": 2, "pdf": "lfm.pdf", "md_full": "output_2/lfm.md", "md_task": "input/lfm.md", "notes": "Light field microscopy, 3D deconvolution"},
    "dpi": {"title": "Differentiable Programming for Inverse Problems", "domain": "scientific_computing", "tier": 3, "pdf": "dpi.pdf", "md_full": "output_2/dpi.md", "md_task": "input/dpi_task1.md", "notes": "Auto-diff for physics inverse problems"},
    "ptyrad": {"title": "PtyRAD: Ptychographic Reconstruction with Automatic Differentiation", "domain": "computational_imaging", "tier": 3, "pdf": "PtyRAD.pdf", "md_full": "output_2/PtyRAD.md", "md_task": "input/ptyrad.md", "notes": "Ptychography, auto-diff reconstruction, GPU-accelerated"},
    "sparse_sim": {"title": "Sparse Structured Illumination Microscopy", "domain": "computational_imaging", "tier": 3, "pdf": "sparse_sim.pdf", "md_full": "output_2/sparse_sim.md", "md_task": "input/sim.md", "notes": "SIM super-resolution, sparse reconstruction"},
    "flfm": {"title": "Fourier Light Field Microscopy", "domain": "computational_imaging", "tier": 3, "pdf": "flfm.pdf", "md_full": "output_2/flfm.md", "md_task": "input/flfm.md", "notes": "Fourier LFM, 3D reconstruction"},
}

for paper_id, meta in PAPERS.items():
    task_src = Path("/home/yjh/new_flow") / meta["md_task"]
    full_src = Path("/home/yjh/new_flow") / meta["md_full"]
    task_dst = MARKDOWN_DIR / f"{paper_id}_task.md"
    full_dst = MARKDOWN_DIR / f"{paper_id}_full.md"
    pdf_src = INPUT_DIR / meta["pdf"]
    pdf_dst = PDF_DIR / meta["pdf"]
    if task_src.exists(): shutil.copy2(str(task_src), str(task_dst))
    if full_src.exists(): shutil.copy2(str(full_src), str(full_dst))
    if pdf_src.exists() and not pdf_dst.exists(): shutil.copy2(str(pdf_src), str(pdf_dst))
    print(f"  {paper_id}: task={'OK' if task_dst.exists() else 'X'} full={'OK' if full_dst.exists() else 'X'} pdf={'OK' if pdf_dst.exists() else 'X'}")

registry = {
    "version": "2.0-local", "created": datetime.now().isoformat(),
    "methodology": "Papers from local PDF collection, OCR'd via PaddleOCR. Clean empty sandbox per task.",
    "total_papers": len(PAPERS),
    "tier_counts": {"tier_1": sum(1 for p in PAPERS.values() if p["tier"]==1), "tier_2": sum(1 for p in PAPERS.values() if p["tier"]==2), "tier_3": sum(1 for p in PAPERS.values() if p["tier"]==3)},
    "papers": {}
}
for pid, m in PAPERS.items():
    t = MARKDOWN_DIR / f"{pid}_task.md"
    f = MARKDOWN_DIR / f"{pid}_full.md"
    registry["papers"][pid] = {"paper_id": pid, "title": m["title"], "domain": m["domain"], "tier": m["tier"],
        "pdf_path": str(PDF_DIR / m["pdf"]), "markdown_task_path": str(t) if t.exists() else None,
        "markdown_full_path": str(f) if f.exists() else None, "notes": m["notes"], "status": "ready_for_reproduction"}

with open(REGISTRY_FILE, 'w') as fh:
    json.dump(registry, fh, indent=2)

print(f"\nRegistry: {REGISTRY_FILE}")
print(f"Papers: {len(PAPERS)} (T1:{registry['tier_counts']['tier_1']} T2:{registry['tier_counts']['tier_2']} T3:{registry['tier_counts']['tier_3']})")
print(f"MDs: {len(list(MARKDOWN_DIR.glob('*.md')))} | PDFs: {len(list(PDF_DIR.glob('*.pdf')))}")
print("DONE")
