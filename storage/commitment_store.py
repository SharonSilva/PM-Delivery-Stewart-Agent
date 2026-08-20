import json
from datetime import date, datetime
from pathlib import Path

from models.commitment import Commitment


def load_commitments(path: str = "seed_data/commitments.json") -> list[Commitment]:
    with open(Path(path)) as f:
        data = json.load(f)
    commitments = []
    for c in data["commitments"]:
        due = date.fromisoformat(c["due_date"]) if c.get("due_date") else None
        commitments.append(Commitment(
            id=c["id"],
            person=c["person"],
            description=c["description"],
            item_id=c.get("item_id"),
            due_date=due,
            due_date_text=c.get("due_date_text"),
            created_at=c["created_at"],
        ))
    return commitments
