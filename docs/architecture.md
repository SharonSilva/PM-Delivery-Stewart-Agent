# Architecture note

## Component overview

Every capability depends only on these six adapter interfaces, never on a concrete mock class directly:

- TrackerAdapter
- CodeHostAdapter
- ChatAdapter
- NotificationAdapter
- RiskLogAdapter
- ProposalStoreAdapter

All six are constructed in exactly one place: adapters/adapter_factory.py, which reads ADAPTER_MODE from config and returns the matching concrete implementation (currently only "mock" implementations exist). Adding a real integration means writing one new class that satisfies the interface, plus one new branch in the factory - zero changes anywhere else.

No capability business-logic file imports a concrete Mock* class directly. Only adapter_factory.py and the files inside mocks/ do.

## Data flow (the shape every capability follows)

The pipeline is the same shape for every capability:

1. seed_data/*.json is read via the relevant Adapter, producing a Snapshot (models/snapshot.py) - a normalized, point-in-time view of the whole project.
2. Pure-code fact extraction (e.g. storage/brief_facts_service.py) computes every fact needed - who did what, how long something has been blocked, whether velocity went up or down. No LLM call happens at this step.
3. Schema-constrained LLM narration (e.g. storage/brief_narration_service.py) turns those computed facts into readable English. The model is only ever asked to phrase a fact, never to compute one.
4. Reference-or-drop validation (storage/reference_validation_service.py) checks every narrated line against the real data. A line that cannot be traced back to something real is dropped or replaced with a plain, code-generated fallback sentence - never shown unverified.
5. Assembly/render produces the final output (e.g. storage/morning_brief_service.py).

Where the model is given a fact and asked only to phrase it (for example, whether weekly velocity increased or decreased), its output is still validated against the computed value afterward. If it contradicts the fact it was given, its output is discarded in favor of a deterministic fallback sentence - this caught a real bug during development where the model said velocity had "stayed similar" despite a computed 2.4x increase.

## Where the approval gate sits

When a capability detects something that needs a real write (a blocker missing from the risk log, a decision from an approved meeting outcome, a blocker old enough to promote), it never writes directly. It calls approval.approval_service.submit_proposal(), creating a Proposal record with status PENDING.

A human then reviews the pending queue and calls one of three functions, all in approval/approval_service.py:

- approve() - final_payload is set equal to original_payload.
- reject() - status becomes REJECTED, nothing further happens.
- edit_then_approve() - final_payload is set to the edited version; original_payload is retained unchanged for the audit trail.

Only after one of those calls can a write actually happen, and only through one function: approval.write_gate.execute_approved_write(). This function re-checks proposal.status itself, at the moment of writing - it does not trust that whatever called it already checked. If the status is not APPROVED, it raises WriteBlockedError and performs no write. This is what makes the gate enforced in the data model rather than by convention: even a caller that bypasses every other part of the system and calls execute_approved_write() directly is still blocked on a pending or rejected proposal.

Golden Case 6 (eval/golden_case_6.py) proves this directly: it attempts a write against a pending proposal (must fail), a rejected proposal (must fail), an approved proposal (must succeed, using final_payload), and an edited-then-approved proposal (must succeed using the edited payload, while the audit record still retains the original for comparison).

## Adapters - what is built and what each one mocks

| Adapter | Mocks | Backing data |
|---|---|---|
| TrackerAdapter | An issue tracker (read-only - nothing in scope writes to the tracker directly) | seed_data/tracker_items.json |
| CodeHostAdapter | A git host commit API | seed_data/commits.json |
| ChatAdapter | A chat workspace | seed_data/chat_messages.json |
| NotificationAdapter | An outbound notification channel | writes to storage/notifications.jsonl (inspectable) |
| RiskLogAdapter | A risk-log store | seed_data/risk_log.json |
| ProposalStoreAdapter | The agent own proposal/audit state | SQLite (storage/db.py) |

Every adapter interface lists only the operations its capabilities actually call - none expose a generic "do anything" method.

## Scheduling

scheduler/clock.py provides one shared Clock instance every job reads "now" from, with set_override() for demos so the whole system can be pinned to a specific date in the seed data without touching any capability code. scheduler/scheduler_app.py wires 6 jobs to real APScheduler cron triggers, each configured via config/scheduler_config.py.

## Storage

- SQLite (storage/db.py): the proposals table - every Proposal ever created, in every status, forming the audit trail.
- Local JSON (seed_data/): the committed sample project - never written to by the running system, only read.
- Local JSONL (storage/): inspectable write logs - notifications.jsonl (every nudge/escalation sent), refused_meeting_outcomes.jsonl (every meeting outcome refused for missing consent), weekly_reports.jsonl (persisted history used for prior-period velocity comparison).
