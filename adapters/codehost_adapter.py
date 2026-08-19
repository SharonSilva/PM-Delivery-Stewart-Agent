from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from models.codehost import Commit

class CodeHostAdapter(ABC):
    """Interface for reading recent chat messages across channels."""
    
    @abstractmethod
    def get_commits(self, since: Optional[datetime] = None) -> list[Commit]:
        """Return commits, optionally to at/after `since`"""
        raise NotImplementedError