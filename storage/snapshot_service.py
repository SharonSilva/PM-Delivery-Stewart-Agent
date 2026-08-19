from datetime import datetime
from typing import Optional

from adapters.tracker_adapter import TrackerAdapter
from adapters.codehost_adapter import CodeHostAdapter
from adapters.chat_adapter import ChatAdapter
from models.snapshot import Snapshot
from storage.snapshot_store import save_snapshot


def take_snapshot(
    tracker: TrackerAdapter,
    codehost: CodeHostAdapter,
    chat: ChatAdapter,
    as_of: Optional[datetime] = None,
) -> Snapshot:
    """Reads through the three read-only adapters and persists a
    single normalized snapshot. Depends only on adapter interfaces,
    per the Adapter Contract.

    as_of lets callers pin the snapshot's timestamp explicitly —
    essential when testing against fictional seed-data dates rather
    than real wall-clock time. Defaults to datetime.now() for real
    scheduled runs.
    """
    taken_at = as_of if as_of is not None else datetime.now()
    snapshot = Snapshot(
        taken_at=taken_at,
        items=tracker.get_items(),
        transitions=tracker.get_transitions(),
        commits=codehost.get_commits(),
        messages=chat.get_messages(),
    )
    save_snapshot(snapshot)
    return snapshot