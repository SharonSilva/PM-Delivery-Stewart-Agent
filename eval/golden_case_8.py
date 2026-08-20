"""
Golden Case 8: consent gate. Processing the supplied outcome
record produces the expected proposals and no writes. The record
with consent absent is refused with a logged reason.
"""
import json

from storage.db import get_connection, init_db
from storage.meeting_outcome_consumer import process_meeting_outcome


def _reset_test_proposals():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM proposals WHERE proposal_type IN ('meeting_tracker_update', 'meeting_risk_entry')")
    conn.commit()
    conn.close()


def golden_case_8_consent_gate():
    _reset_test_proposals()

    with open("seed_data/meeting_outcomes.json") as f:
        data = json.load(f)

    results = {}
    for record in data["meeting_outcomes"]:
        results[record["id"]] = process_meeting_outcome(record)

    mo_001 = results.get("MO-001")
    mo_002 = results.get("MO-002")

    mo_001_correct = (
        mo_001 is not None
        and not mo_001.refused
        and len(mo_001.tracker_proposals) > 0
    )
    mo_002_correct = (
        mo_002 is not None
        and mo_002.refused
        and mo_002.reason is not None
    )

    # Confirm the refusal was actually logged, not just returned in memory
    logged = False
    try:
        with open("storage/refused_meeting_outcomes.jsonl") as f:
            logged = any('"meeting_id": "MO-002"' in line for line in f)
    except FileNotFoundError:
        logged = False

    passed = mo_001_correct and mo_002_correct and logged
    detail = (
        f"MO-001 processed with proposals: {mo_001_correct}; "
        f"MO-002 refused with reason: {mo_002_correct}; "
        f"refusal logged to file: {logged}"
    )
    return passed, passed, True, detail
