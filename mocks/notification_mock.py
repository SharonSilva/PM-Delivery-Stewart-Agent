import json
from pathlib import Path

from adapters.notification_adapter import NotificationAdapter
from models.notification import NotificationRecord


class MockNotificationAdapter(NotificationAdapter):
    """Writes notification records to an inspectable JSONL log
        Never sends anything externally, per the brief's scope rule
    """
    
    def __init__(self, log_path: str = "storage/notifications.jsonl"):
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        
        
    def write(self, record: NotificationRecord) -> None:
        with open(self._log_path, "a") as f:
            f.write(record.model_dump_json() + "\n")