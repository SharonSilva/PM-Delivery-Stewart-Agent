from datetime import datetime
from adapters.tracker_adapter import TrackerAdapter
from adapters.codehost_adapter import CodeHostAdapter
from adapters.chat_adapter import ChatAdapter
from models.snapshot import Snapshot
from storage.snapshot_store import save_snapshot

def take_snapshot(
    tracker: TrackerAdapter,
    codehost: CodeHostAdapter,
    chat: ChatAdapter,
) -> Snapshot:
    """Reads through the 3 readonly adapter and finds 
    a single normalised snapshot. Depends only on adapter interface,
    per the adapter contract"""
    
    snapshot = Snapshot(
        taken_at=datetime.now(),
        items=tracker.get_items(),
        transitions=tracker.get_transitions(),
        commits=codehost.get_commits(),
        messages=chat.get_messages(),
    )
    save_snapshot(snapshot)
    return snapshot