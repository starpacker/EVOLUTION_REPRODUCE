#!/usr/bin/env python3
"""
Paper PDF → Markdown Parser using PaddleOCR PPStructureV3.
Part of Project Evolution-Reproduce.

Usage:
    python ocr_paper_parser.py --pdf <path_to_pdf> --output_dir <output_directory>
    
This script calls PaddleOCR via the paddle_env conda environment.
"""

import argparse
import subprocess
import os
import sys
import json
from pathlib import Path


# Path to the paddle_env Python interpreter
PADDLE_PYTHON = "/home/yjh/.conda/envs/paddle_env/bin/python"


def parse_paper_via_subprocess(pdf_path: str, output_dir: str) -> dict:
    """
    Parse a paper PDF to Markdown by calling PaddleOCR in the paddle_env.
    Uses subprocess to ensure the correct conda environment is used.
    
    Returns:
        dict with keys: 'markdown_path', 'images_dir', 'success', 'error'
    """
    pdf_path = os.path.abspath(pdf_path)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_path):
        return {"success": False, "error": f"PDF not found: {pdf_path}"}
    
    if not os.path.exists(PADDLE_PYTHON):
        return {"success": False, "error": f"paddle_env not found at {PADDLE_PYTHON}"}
    
    # Create the inline OCR script to run in paddle_env
    ocr_script = f'''
import sys
import os
import json
from pathlib import Path

try:
    from paddleocr import PPStructureV3
    
    pdf_path = "{pdf_path}"
    output_dir = "{output_dir}"
    
    pipeline = PPStructureV3()
    output = pipeline.predict(input=pdf_path)
    
    # Collect markdown pages and images
    markdown_pages = []
    all_images = []
    
    for result in output:
        if hasattr(result, 'text') and result.text:
            markdown_pages.append(result.text)
        # Handle different output formats
        if isinstance(result, dict):
            if 'text' in result:
                markdown_pages.append(result['text'])
    
    # Try the concatenate method if available
    try:
        markdown_text = pipeline.concatenate_markdown_pages(markdown_pages)
    except (AttributeError, TypeError):
        markdown_text = "\\n\\n---\\n\\n".join(markdown_pages) if markdown_pages else ""
    
    # If output is iterable of results with different structure
    if not markdown_text:
        collected = []
        for res in output:
            if isinstance(res, str):
                collected.append(res)
            elif hasattr(res, '__iter__'):
                for item in res:
                    if isinstance(item, str):
                        collected.append(item)
                    elif isinstance(item, dict) and 'text' in item:
                        collected.append(item['text'])
        markdown_text = "\\n\\n".join(collected)
    
    # Save markdown
    paper_name = Path(pdf_path).stem
    md_path = os.path.join(output_dir, f"{{paper_name}}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    
    # Save images if any
    images_dir = os.path.join(output_dir, f"{{paper_name}}_images")
    os.makedirs(images_dir, exist_ok=True)
    
    result_info = {{
        "success": True,
        "markdown_path": md_path,
        "images_dir": images_dir,
        "num_pages": len(markdown_pages),
        "markdown_length": len(markdown_text)
    }}
    print("OCR_RESULT:" + json.dumps(result_info))
    
except Exception as e:
    import traceback
    result_info = {{
        "success": False,
        "error": f"{{type(e).__name__}}: {{str(e)}}",
        "traceback": traceback.format_exc()
    }}
    print("OCR_RESULT:" + json.dumps(result_info))
    sys.exit(1)
'''
    
    try:
        result = subprocess.run(
            [PADDLE_PYTHON, "-c", ocr_script],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout for long PDFs
        )
        
        # Parse the result from stdout
        for line in result.stdout.split('\n'):
            if line.startswith("OCR_RESULT:"):
                return json.loads(line[len("OCR_RESULT:"):])
        
        # If no result line found
        return {
            "success": False,
            "error": "No OCR result found in output",
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "OCR timed out after 300 seconds"}
    except Exception as e:
        return {"success": False, "error": f"Subprocess error: {type(e).__name__}: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="Parse paper PDF to Markdown using PaddleOCR")
    parser.add_argument("--pdf", required=True, help="Path to the paper PDF file")
    parser.add_argument("--output_dir", required=True, help="Directory to save the output Markdown and images")
    args = parser.parse_args()
    
    print(f"[INFO] Parsing: {args.pdf}")
    print(f"[INFO] Output dir: {args.output_dir}")
    
    result = parse_paper_via_subprocess(args.pdf, args.output_dir)
    
    if result["success"]:
        print(f"[SUCCESS] Markdown saved to: {result['markdown_path']}")
        print(f"[SUCCESS] Pages processed: {result.get('num_pages', '?')}")
        print(f"[SUCCESS] Markdown length: {result.get('markdown_length', '?')} chars")
    else:
        print(f"[FAILED] {result['error']}")
        if 'traceback' in result:
            print(f"[TRACEBACK]\n{result['traceback']}")
    
    return result


if __name__ == "__main__":
    main()
