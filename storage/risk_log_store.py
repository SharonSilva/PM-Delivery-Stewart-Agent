import json
from pathlib import Path

def load_risk_log(path: str= "seed_data/risk_log.json") -> list[dict]:
    with open(Path(path)) as f:
        data = json.load(f)
    return data["risks"]
