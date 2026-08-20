import json
from storage.meeting_outcome_consumer import process_meeting_outcome
from storage.db import get_connection, init_db

# Clean slate for meeting-outcome proposals specifically
init_db()
conn = get_connection()
conn.execute("DELETE FROM proposals WHERE proposal_type IN ('meeting_tracker_update', 'meeting_risk_entry')")
conn.commit()
conn.close()

with open("seed_data/meeting_outcomes.json") as f:
    data = json.load(f)

for record in data["meeting_outcomes"]:
    print(f"=== Processing {record['id']} (consent={record['consent']}) ===")
    result = process_meeting_outcome(record)
    if result.refused:
        print(f"  REFUSED: {result.reason}")
    else:
        print(f"  Tracker proposals: {len(result.tracker_proposals)}")
        for p in result.tracker_proposals:
            print(f"    {p.id}: {p.original_payload['text']}")
        print(f"  Risk proposals: {len(result.risk_proposals)}")
        for p in result.risk_proposals:
            print(f"    {p.id}: {p.original_payload['text']}")
    print()

print("=== Refusal log ===")
with open("storage/refused_meeting_outcomes.jsonl") as f:
    for line in f:
        print(line.strip())
