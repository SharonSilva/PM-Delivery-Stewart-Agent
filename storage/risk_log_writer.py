import json
from pathlib import Path


def write_risk_entry(payload: dict) -> None:
    """The actual write function for an approved risk-gap-fill
    proposal. Only ever called through execute_approved_write,
    which refuses to invoke it unless the proposal is APPROVED -
    this function itself trusts its caller because that check
    already happened at the gate."""
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
        "created_at": None,  # set by caller if needed; None is honest when not tracked
    }

    data["risks"].append(new_entry)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
