from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class NotificationRecord(BaseModel):
    """A single logged notification (nudge/escalation)
    or Never actually sent written to an inspectable log only,
    per the brief's out of scope rule on real messaging"""
    
    id: str
    kind: Literal["nudge", "escalation"]
    recipient: str
    commitment_id: str
    message: str
    timestamp: datetime