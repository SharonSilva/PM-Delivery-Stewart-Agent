from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Commit(BaseModel):
    """A single commit for item_id is optional
    and some commits reference no tracker item."""
    
    
    hash: str
    item_id: Optional[str] = None
    author: str
    message: str
    timestamp: datetime
    
    