import json
from pathlib import Path

from adapters.risk_log_adapter import RiskLogAdapter


class MockRiskLogAdapter(RiskLogAdapter):
    def __init__(self, data_path: str = "seed_data/risk_log.json"):
        self._data_path = Path(data_path)

    def load_risks(self) -> list[dict]:
        with open(self._data_path) as f:
            data = json.load(f)
        return data["risks"]

    def append_risk(self, entry: dict) -> None:
        with open(self._data_path) as f:
            data = json.load(f)
        data["risks"].append(entry)
        with open(self._data_path, "w") as f:
            json.dump(data, f, indent=2)
