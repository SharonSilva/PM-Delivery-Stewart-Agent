from typing import Optional
from pydantic import BaseModel


class CarryOverItem(BaseModel):
    item_id: str
    title: str
    status_at_sprint_end: str
    assignee: Optional[str] = None


class CandidateItem(BaseModel):
    item_id: str
    title: str
    priority: Optional[str] = None
    reasoning: str


class SprintPlanningFacts(BaseModel):
    """Pure, deterministic facts for the sprint planning pack.
    Reference sprint is the most recently CLOSED sprint (Sprint 1,
    Aug 3-14) - Sprint 2 is still open, so it cannot honestly be
    used as 'historical completion' data.
    """
    reference_sprint_name: str
    reference_sprint_start: str
    reference_sprint_end: str

    carry_over: list[CarryOverItem] = []

    stated_capacity: int
    capacity_is_assumption_note: str  # the disclosed assumption text, always populated

    ready_backlog: list[CandidateItem] = []  # candidates NOT yet selected
    candidate_slice: list[CandidateItem] = []  # candidates proposed for the next sprint

    item_titles: dict[str, str] = {}
