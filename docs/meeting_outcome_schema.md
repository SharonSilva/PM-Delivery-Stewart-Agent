# Meeting Outcome Schema — v1

This is the schema P8 (Consume a meeting outcome) expects for each
supplied meeting-outcome record. Version: 1.0 (2026-08-18).

```json
{
  "id": "string, unique meeting outcome ID",
  "meeting_date": "ISO 8601 datetime",
  "attendees": ["list of person names"],
  "consent": "boolean - required. false or absent means the record is REFUSED outright.",
  "decisions": [
    {"text": "string", "source_ref": "item ID or other reference this decision relates to"}
  ],
  "actions": [
    {"text": "string", "person": "string", "due_date": "ISO 8601 date, optional", "source_ref": "item ID"}
  ],
  "risks": [
    {"text": "string", "source_ref": "item ID"}
  ]
}
```

## Consent gate

`consent` must be exactly `true` for a record to be processed. Any
other value (`false`, missing, `null`) causes the record to be
refused before any proposal is generated. The refusal is logged
with a reason (see `storage/refusal_log.py`), not silently dropped.

## Output mapping

- `decisions` + `actions` → proposals in the **tracker batch**
  (P8's "tracker updates or creations" set)
- `risks` → proposals in the **risk-log batch**
- Every proposal carries the meeting outcome's `id` as its
  grounding reference, per the spec's "carrying the meeting
  reference that justifies it."
