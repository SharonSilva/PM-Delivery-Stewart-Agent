from datetime import datetime
from typing import Optional 
from pydantic import BaseModel

class   WorkItem(BaseModel):                                                      
    """ A single tracker item that is normalized. Status is kept as the raw
        string from the source system and normalization into a clean enum happens
        in the deterministic engine, not here, so this model can represent messy real world
        data (including free-text statuses).
    """
    
    id: str
    title: str
    status: str
    assignee: Optional[str] = None
    priority: Optional[str] = None
    blocked: bool = False
    created_at: datetime
    
class Transition(BaseModel):
    """A single state change for a work item, with a timestamp. 
       from_status is None for an item's creation event.    
    """
    
    item_id: str
    from_status: Optional[str] = None
    to_status: str
    timestamp: datetime