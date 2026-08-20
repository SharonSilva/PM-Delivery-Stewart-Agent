# Rate-limit handling — disclosure

This project uses a local model (Qwen2.5 7B via Ollama), which has
no rate limit in the way a hosted API would — every call runs
locally, so there is no external quota, no 429 response, and no
per-minute/per-day cap to hit. As a result, we have not built or
demonstrated real rate-limit-error handling, because there is no
real rate-limit condition to trigger it against.

**If this project used a hosted free-tier API instead** (e.g. a
free tier of a commercial LLM provider), the same discipline we
already apply to malformed output would extend naturally to
rate-limit errors:

- `llm/client.py` is the single call site for all LLM generation in
  the project — a hosted provider's rate-limit exception would be
  caught at exactly this one point, not scattered across callers.
- The existing `_call_with_retry` pattern in each narration service
  already retries on malformed/unparseable output with a hard cap
  (`MAX_RETRIES`). The same shape — retry with a cap, then fail
  loudly and safely rather than silently — would apply to a
  rate-limit error, most likely with an exponential backoff between
  attempts (e.g. 1s, 2s, 4s) rather than an immediate retry, since a
  rate limit is a "try again shortly" condition rather than a
  transient parsing failure.
- After exhausting retries, the failure should surface exactly like
  our current malformed-output failure: a clear, typed exception
  (not a silently wrong answer), so the calling job can report "the
  brief could not be generated this run" rather than fabricate one.

This is disclosed here explicitly rather than left unaddressed,
since the ground rules ask for a stated approach even when the
condition wasn't actually hit during development.
