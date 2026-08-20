from pydantic import BaseModel


class ItemDelta(BaseModel):
    """What happened to one item between the morning and EOD
    snapshots, plus the supporting evidence (commits, messages)
    that grounds the narration - not just the bare status change."""
    item_id: str
    title: str
    morning_status: str
    eod_status: str
    flapped: bool
    transition_count: int
    commit_messages: list[str] = []   # real commit messages referencing this item in the window
    chat_excerpts: list[str] = []     # real chat message texts referencing this item in the window


class MeetingOutcomeNote(BaseModel):
    """A meeting outcome relevant to today, surfaced as context -
    not automatically applied (that's P8's job), just referenced
    here so the EOD summary can mention it happened."""
    meeting_id: str
    consent: bool
    decision_texts: list[str] = []


class EODDeltaFacts(BaseModel):
    """Pure, deterministic delta between two snapshots of the same
    day, enriched with real supporting evidence. Computed entirely
    in code - the model only narrates this, never derives it."""
    sprint_name: str
    sprint_day: int
    morning_taken_at: str
    eod_taken_at: str
    shipped: list[ItemDelta] = []
    newly_blocked: list[ItemDelta] = []
    changed_other: list[ItemDelta] = []
    still_pending: list[str] = []
    item_titles: dict[str, str] = {}
    meeting_outcomes_today: list[MeetingOutcomeNote] = []
