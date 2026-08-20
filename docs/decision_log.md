# Decision & assumption log

Each entry: the ambiguity or open question, the decision made, and why.

## P7 - Commitment nudges: seeded commitments only

The catalog does not specify whether commitments auto-created from an approved P8 meeting-outcome action should feed into P7 nudge tracking. This was left deliberately unbuilt: auto-creating a commitment from an approved write is a real design question (what due date? what cadence? does it need its own approval step?), not a small wiring task. P7 was built and tested purely against the seeded commitment store. If asked in Q&A: this is a genuine gap, not an oversight, and the reason it is not closed is that closing it properly would have meant designing a second approval-adjacent flow under time pressure rather than getting it right.

## P7 - Daily cap is per-day, not total-chases-before-escalation

The spec says nudges never exceed a configured per-person daily cap. It does not say a person can only ever be nudged some fixed number of times in total before escalation. Read literally, the cap governs a single day, so a person can be nudged once a day, every day, indefinitely, without ever escalating - the seeded data actually demonstrates this (Jordan Lee gets 5 consecutive daily nudges before an escalation eventually fires from the underlying overdue threshold, not from exhausting a chase count). This is a defensible literal reading of the stated rule, disclosed here in case a stricter interpretation was intended.

## P9 - the week is sprint-to-date, not a fixed 7-day window

The seeded project data does not span a full calendar week from Sprint 2 start to the snapshot date used in testing. Fabricating a fixed 7-day window would mean reporting on days that have no real data. Instead, the week is defined as sprint-start-to-latest-snapshot, and this is disclosed explicitly in the rendered report itself, not just in this log.

## P9 - Velocity compared as a rate, not a raw count

Sprint 1 (a full, closed sprint) and Sprint 2-to-date (a partial, still-open sprint) have very different elapsed-day counts. Comparing raw completed-item counts between them would be misleading. Velocity is compared as items-completed-per-elapsed-day instead. The prior-period basis is: the last persisted weekly report if one exists, else Sprint 1 (a real, complete comparison basis), else no comparison is offered at all - never a fabricated baseline.

## P9 - Decisions needed from client mapped to owner-less risks

The catalog asks for a decisions needed from client section without specifying what counts as one. This was interpreted as: any top risk with no owner assigned. This is a disclosed interpretive choice, not a literal requirement from the seed data schema.

## P10 - No Proposal/approval-gate machinery

The spec states the sprint-planning pack is never applied to the tracker automatically. Since there is no write this capability ever performs, there is nothing to gate - building Proposal machinery here anyway would imply a write action that does not exist.

## P10 - Reference sprint is Sprint 1, not Sprint 2

Sprint 2 is still open at the point the pack is generated, so it cannot honestly serve as historical completion data for capacity planning - a still-open sprint has an artificially low completion count simply because it is not finished. Sprint 1, real and closed, is used as the comparison basis instead.

## P10 - Capacity-to-candidate-slice conversion is a stated assumption

TEAM_CAPACITY_ITEMS_PER_SPRINT is a real, human-provided config value, not computed. Converting it directly into a candidate-slice size (capacity minus carry-over) is an assumption about how capacity should be spent, and is labeled explicitly as an assumption in the packs own output, not just asserted as fact.

## P10 - The empty candidate slice was kept, not adjusted away

At the real configured capacity (12), carry-over from Sprint 1 already exceeds capacity, so the candidate slice for new work is correctly zero. Rather than raising the capacity value to produce a more demo-friendly non-empty result, the real value was kept, and a second capacity value (25) was run separately to prove the mechanism responds correctly when there is room.

## P11 - Correlation only, never cause

The seed data contains no causal-mechanism information - nothing states that a blocker or a scope change caused a change in throughput. Any causal claim would therefore be invented. P11 only ever reports temporal coincidence, explicitly hedged, and validated by a hard-coded guard that discards any narrated line containing causal-assertion language in favor of the original, already-hedged, code-generated sentence.

## P11 - No Proposal/approval-gate machinery

Same reasoning as P10: this capability performs no write, so there is nothing to gate.

## Architecture - adapters required as parameters, not defaulted to a mock

Early in the build, several service functions accepted an adapter as an optional parameter and constructed a mock internally if none was given. This technically still imported a concrete mock class inside business-logic files, which conflicts with the adapter contract read strictly. This was corrected during the build: every such default was removed, and every adapter is now a required parameter, constructed only at composition points.

## Rate-limit handling - not demonstrated, disclosed instead

Local Ollama has no rate limit, so no real rate-limit-error condition was ever triggered during development. The disclosed approach that would apply against a hosted API is documented in docs/rate_limit_disclosure.md.
