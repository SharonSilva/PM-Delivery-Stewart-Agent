import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from adapters.codehost_adapter import CodeHostAdapter
from models.codehost import Commit

class MockCodeHostAdapter(CodeHostAdapter):
    def __init__(self,data_path: str="seed_data/commits.json"):
        self._data_path = Path(data_path)
        
    def get_commits(self, since: Optional[datetime] = None) -> list[Commit]:
        with open(self._data_path) as f:
            data = json.load(f)
        commits = [Commit(**c) for c in data[("commits")]]
        if since is not None:
            commits = [c for c in commits if c.timestamp >= since]
        return commits