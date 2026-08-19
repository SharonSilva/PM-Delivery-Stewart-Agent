from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from models.tracker import WorkItem, Transition

class TrackerAdapter(ABC):
    """Interface for reading project-tracker state(items and their
        transition history). Agent logic should depend only on this interface,
        interface, never on a concrete implementation
    """
    
    @abstractmethod
    def get_items(self) -> list[WorkItem]:
        """Return all curent work items."""
        raise NotImplementedError
    
    @abstractmethod
    def get_transitions(self, since: Optional[datetime] = None) -> list[Transition]:
        """Return transition history optionlly filtered to transition at or after `since`."""
        raise NotImplementedError