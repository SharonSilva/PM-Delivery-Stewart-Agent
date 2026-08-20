from pydantic import BaseModel


class ItemDelta(BaseModel):
    """What happened to one item between the morning and EOD
    snapshots. flapped is True if the item passed through more
    than one transition in the window - the diff engine (not the
    model) is responsible for collapsing that into one accurate
    delta rather than reporting each transition separately."""
    item_id: str
    title: str
    morning_status: str
    eod_status: str
    flapped: bool
    transition_count: int


class EODDeltaFacts(BaseModel):
    """Pure, deterministic delta between two snapshots of the same
    day. Computed entirely in code - the model only narrates this,
    never derives it."""
    sprint_name: str
    sprint_day: int
    morning_taken_at: str
    eod_taken_at: str
    shipped: list[ItemDelta] = []
    newly_blocked: list[ItemDelta] = []
    changed_other: list[ItemDelta] = []
    still_pending: list[str] = []  # item IDs that were Open at both morning and EOD, no activity today
    item_titles: dict[str, str] = {}
