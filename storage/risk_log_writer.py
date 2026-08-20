import json
from pathlib import Path


def write_risk_entry(payload: dict) -> None:
    """Writes a NEW risk entry (used by P4's gap-fill)."""
    path = Path("seed_data/risk_log.json")
    with open(path) as f:
        data = json.load(f)

    existing_ids = {r["id"] for r in data["risks"]}
    next_num = len(data["risks"]) + 1
    new_id = f"R-{next_num:03d}"
    while new_id in existing_ids:
        next_num += 1
        new_id = f"R-{next_num:03d}"

    new_entry = {
        "id": new_id,
        "description": payload["description"],
        "impact": payload["impact"],
        "item_id": payload["item_id"],
        "owner": payload.get("suggested_owner"),
        "created_at": None,
    }
    data["risks"].append(new_entry)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_promotion_entry(payload: dict) -> None:
    """Writes a NEW risk entry from an approved blocker-promotion
    proposal - the item is being escalated into a formal risk."""
    path = Path("seed_data/risk_log.json")
    with open(path) as f:
        data = json.load(f)

    existing_ids = {r["id"] for r in data["risks"]}
    next_num = len(data["risks"]) + 1
    new_id = f"R-{next_num:03d}"
    while new_id in existing_ids:
        next_num += 1
        new_id = f"R-{next_num:03d}"

    new_entry = {
        "id": new_id,
        "description": payload["mitigation_draft"],
        "impact": "High",  # a blocker that aged past threshold defaults to High
        "item_id": payload["item_id"],
        "owner": None,  # promotion doesn't evidence an owner - human assigns on approval
        "created_at": None,
    }
    data["risks"].append(new_entry)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
