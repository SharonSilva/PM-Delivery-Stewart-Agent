from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from models.chat import ChatMessage

class ChatAdapter(ABC):
    """Interface for reading recent chat messages across channels"""
    
    @abstractmethod
    def get_messages(self, since: Optional[datetime] = None) -> list[ChatMessage]:
        """Return messages, optionally filtered to at/after `since`"""
        raise NotImplementedError