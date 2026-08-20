from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Proposal(BaseModel):
    """
    The core abstraction where any capability that wants to write to the tracker
    or risk log produces a Proposal instead of writing 
    directly. Nothing executes until this record's sttus is 
    APPROVED, and that check happens at the erite  boundary itself,
    not just in whatever UI happens to call it
    """
    
    id: str
    proposal_type: str  # "risk_gap_fill", "blocker_promotion"
    source_ref: str     # what evidence grounds this proposal (an item_id, etc..)
    original_payload: dict[str, Any]
    final_payload: Optional[dict[str, Any]] = None  #set on approve or edit-then-approve
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: datetime
    decided_at: Optional[datetime] = None
    approver: Optional[str] = None