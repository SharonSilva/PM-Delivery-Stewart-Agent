from datetime import datetime
from typing import Optional


class Clock:
    """Abstraction over 'now'. Real scheduled runs use real time;
    """

    def __init__(self):
        self._override: Optional[datetime] = None

    def set_override(self, dt: Optional[datetime]) -> None:
        self._override = dt

    def now(self) -> datetime:
        return self._override if self._override is not None else datetime.now()


clock = Clock()