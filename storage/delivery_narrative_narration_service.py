import json
import re

from pydantic import ValidationError

from llm.client import call_llm
from models.delivery_narrative import TemporalAssociation
from models.brief_output import NarratedBrief

MAX_RETRIES = 3

# Language that asserts definitive causation - if the model's
# output contains any of these, its text is discarded and the
# original code-generated hedged sentence is used instead.
_CAUSAL_ASSERTION_PATTERNS = [
    r"\bcaused\b", r"\bcausing\b", r"\bcause of\b",
    r"\bled to\b", r"\bresulted in\b", r"\bresulting in\b",
    r"\bdue to\b", r"\bbecause of\b", r"\bthe reason\b",
    r"\bwas responsible for\b",
]


def _parse_narrated_brief(raw_response: str) -> NarratedBrief:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    parsed = json.loads(cleaned)
    return NarratedBrief.model_validate(parsed)


def _call_with_retry(prompt: str) -> NarratedBrief:
    last_error = None
    for attempt in range(MAX_RETRIES):
        # Only use the cache on the first attempt - a retry that
        # replays the same cached malformed response is not a real
        # retry at all. Force a fresh generation on every subsequent attempt.
        raw = call_llm(prompt, use_cache=(attempt == 0))
        try:
            return _parse_narrated_brief(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue
    raise RuntimeError(f"LLM failed after {MAX_RETRIES} attempts: {last_error}")


def _contains_causal_assertion(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in _CAUSAL_ASSERTION_PATTERNS)


def narrate_association(association: TemporalAssociation) -> str:
    """Rephrases the already-correct, hedged, code-generated
    description into more natural prose. The model is NOT asked to
    reason about causation - it's only asked to reword a sentence
    that already states the facts and the hedge. Output is
    validated: if it contains any causal-assertion language, it's
    discarded entirely and the original code-generated sentence is
    used as-is. This is reference-or-drop applied to epistemic
    honesty, not just factual grounding."""

    prompt = f"""Reword the following sentence to be more natural and readable, for a
delivery status narrative. Return ONLY valid JSON:
{{"lines": [{{"text": "...", "source_ref": "association"}}]}}

STRICT RULES:
- Do NOT change the meaning. Do NOT claim anything is a proven cause.
- Do NOT use words like "caused", "led to", "resulted in", "due to", "because of".
- Keep the hedge ("coincidence", "not a proven cause") explicit in your rewording.
- Do NOT invent any detail, item, or reason beyond what is in the sentence below.

Sentence to reword: {association.description}"""

    result = _call_with_retry(prompt)
    if not result.lines:
        return association.description

    text = result.lines[0].text

    # Validate: reject anything with causal-assertion language, and
    # also reject if the item IDs originally cited no longer all
    # appear (a sign the model dropped or altered the citations).
    if _contains_causal_assertion(text):
        return association.description
    for item_id in association.cited_item_ids:
        if item_id not in text:
            return association.description

    return text
