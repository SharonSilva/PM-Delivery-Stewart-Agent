"""
Live demonstration of the malformed-output retry path (Tier 3
hardening requirement). Not a golden case with a pass/fail target -
this is a demo script proving the retry loop genuinely engages and
recovers, or fails safely, under real malformed-JSON conditions.
Run with: python3.11 eval/demo_malformed_output_handling.py
"""
import storage.brief_narration_service as bns

_call_count = {"n": 0}


def _fake_call_llm_recovers_on_retry(prompt, use_cache=True):
    """Simulates the model returning malformed JSON on the first
    attempt, then valid JSON on the second - proves the retry loop
    genuinely re-invokes the model and recovers."""
    _call_count["n"] += 1
    if _call_count["n"] == 1:
        return "{not valid json at all, missing quotes and brackets"
    return '{"lines": [{"text": "Alice Chen delivered T-001.", "source_ref": "T-001"}]}'


def _fake_call_llm_always_malformed(prompt, use_cache=True):
    """Simulates the model failing every single attempt - proves
    the retry loop gives up after MAX_RETRIES and raises a clear,
    safe error rather than silently returning something wrong."""
    return "this is not json, not even close"


def demo_recovers_after_one_bad_attempt():
    print("=== Demo 1: malformed first attempt, valid second attempt ===")
    _call_count["n"] = 0
    original = bns.call_llm
    bns.call_llm = _fake_call_llm_recovers_on_retry
    try:
        result = bns._call_with_retry("irrelevant prompt for this demo")
        print(f"Recovered successfully after {_call_count['n']} attempt(s).")
        print(f"Parsed result: {result.lines[0].text!r}")
    finally:
        bns.call_llm = original
    print()


def demo_fails_safely_after_max_retries():
    print("=== Demo 2: every attempt malformed - must fail safely, not silently ===")
    original = bns.call_llm
    bns.call_llm = _fake_call_llm_always_malformed
    try:
        bns._call_with_retry("irrelevant prompt for this demo")
        print("FAIL: expected a RuntimeError, but none was raised.")
    except RuntimeError as e:
        print(f"Correctly raised RuntimeError after {bns.MAX_RETRIES} attempts: {e}")
    finally:
        bns.call_llm = original
    print()


if __name__ == "__main__":
    demo_recovers_after_one_bad_attempt()
    demo_fails_safely_after_max_retries()
