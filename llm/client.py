import hashlib
import json
import os
from pathlib import Path

import ollama

_CACHE_DIR = Path("storage/llm_cache")
_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")


def _cache_key(prompt: str) -> str:
    """Deterministic key from the prompt content, so identical
    prompts always hit the same cache entry."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def call_llm(prompt: str, use_cache: bool = True) -> str:
    """The single call site for all LLM generation in this project.
    Swapping providers or models means changing only this function.

    Caching serves two purposes: protects the determinism
    requirement (same input -> same output across regenerations),
    and avoids redundant local inference during development.
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(prompt)
    cache_path = _CACHE_DIR / f"{key}.json"

    if use_cache and cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)["response"]

    result = ollama.chat(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = result["message"]["content"]

    with open(cache_path, "w") as f:
        json.dump({"prompt": prompt, "response": response_text}, f)

    return response_text
