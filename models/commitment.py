from datetime import date
from typing import Optional
from pydantic import BaseModel


class Commitment(BaseModel):
    """A tracked promise. due_date is None when the source only
    gave a relative/ambiguous phrase (due_date_text) - this must
    stay unresolved rather than being guessed, per the brief's
    anti-pattern on silent guessing."""
    id: str
    person: str
    description: str
    item_id: Optional[str] = None
    due_date: Optional[date] = None
    due_date_text: Optional[str] = None
    created_at: str
