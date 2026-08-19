import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from adapters.tracker_adapter import TrackerAdapter
from models.tracker import WorkItem, Transition

class MockTrackerAdapter(TrackerAdapter):
    """Reads tracker state from a local JSON files. Satisfies 
        TrackerAdapter where agent code never import this class directly,
        only ever depends on the TrackerAdapter type.
    """
    
    def __init__(self, data_path: str = "seed_data/tracker_items.json"):
        self._data_path = Path(data_path)
        
    
    def _load(self) -> dict:
        with open(self._data_path) as f:
            return json.load(f)
        
    def get_items(self) -> list[WorkItem]:
        data = self._load()
        return [WorkItem(**item) for item in data["items"]]
    
    def get_transitions(self, since : Optional[datetime] = None) -> list[Transition]:
        data = self._load()
        transitions = [Transition(**t) for t in data["transitions"]]
        if since is not None:
            transitions = [t for t in transitions if t.timestamp >= since]
        return transitions