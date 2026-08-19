from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    """A single chat message from a channel"""
    
    id: str
    channel: str
    author: str
    text: str
    timestamp: datetime
    item_id: Optional[str] = None