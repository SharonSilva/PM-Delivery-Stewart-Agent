from datetime import datetime
from pydantic import BaseModel

from models.tracker import WorkItem, Transition
from models.codehost import Commit
from models.chat import ChatMessage


class Snapshot(BaseModel):
    """A normalized, timestamped view of project state across all
    adapters. Two snapshots can be diffed to compute what changed
    between them  that diffing happens in code , never by
    asking the model to compare two snapshots."""
    
    taken_at: datetime
    items: list[WorkItem]
    transitions: list[Transition]
    commits: list[Commit]
    messages: list[ChatMessage]
