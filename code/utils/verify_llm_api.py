#!/usr/bin/env python3
"""
Verify LLM API connectivity for Project Evolution-Reproduce.
Tests the Claude 4.6 Opus endpoint via OpenAI-compatible gateway.
"""

import os
import sys
import time
import json

def verify_api():
    """Test LLM API connectivity with a simple prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        print("[ERROR] openai package not installed. Run: pip install openai")
        sys.exit(1)
    
    # Configuration from OpenHands config.toml
    API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
    BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
    MODEL = "cds/Claude-4.6-opus"
    
    print(f"[INFO] Testing LLM API...")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Model: {MODEL}")
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
                {"role": "user", "content": "Say 'API connection successful' and nothing else."}
            ],
            max_tokens=50,
            temperature=0.0
        )
        elapsed = time.time() - start_time
        
        content = response.choices[0].message.content
        print(f"[SUCCESS] API responded in {elapsed:.2f}s")
        print(f"  Response: {content}")
        print(f"  Model: {response.model}")
        print(f"  Usage: {response.usage}")
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[FAILED] API error after {elapsed:.2f}s: {type(e).__name__}: {e}")
        return False


def verify_embedding_api():
    """Test embedding API for experience DB vector search."""
    try:
        from openai import OpenAI
    except ImportError:
        print("[SKIP] openai package not installed")
        return False
    
    API_KEY = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
    BASE_URL = "https://ai-gateway-internal.dp.tech/v1"
    
    print(f"\n[INFO] Testing Embedding API...")
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input="Test embedding for experience retrieval"
        )
        dim = len(response.data[0].embedding)
        print(f"[SUCCESS] Embedding API works. Dimension: {dim}")
        return True
    except Exception as e:
        print(f"[INFO] Embedding API test: {type(e).__name__}: {e}")
        print("[INFO] Will fall back to local embedding model (bge-large-en-v1.5) if needed")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Project Evolution-Reproduce: API Verification")
    print("=" * 60)
    
    llm_ok = verify_api()
    emb_ok = verify_embedding_api()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  LLM API (Claude 4.6 Opus): {'✅ OK' if llm_ok else '❌ FAILED'}")
    print(f"  Embedding API: {'✅ OK' if emb_ok else '⚠️  Will use local model'}")
    print("=" * 60)
