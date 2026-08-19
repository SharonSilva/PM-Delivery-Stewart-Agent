import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from adapters.chat_adapter import ChatAdapter
from models.chat import ChatMessage

class MockChatAdapter(ChatAdapter):
    def __init__(self, data_path: str= "seed_data/chat_messages.json"):
        self._data_path = Path(data_path)
        
    def get_messages(self, since: Optional[datetime] = None) -> list[ChatMessage]:
        with open(self._data_path) as f:
            data = json.load(f)
        messages = [ChatMessage(**m) for m in data["messages"]]
        if since is not None:
            messages = [m for m in messages if m.timestamp >= since]
        return messages