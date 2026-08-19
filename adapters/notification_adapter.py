from abc import ABC, abstractmethod

from models.notification import NotificationRecord

class NotificationAdapter(ABC):
    """Interface for writing notification records (
        nudges, escalations). Write only and never sends 
        anything externally, persists to an inspectable log instead."""
        
    @abstractmethod
    def write(self, record: NotificationRecord) -> None:
        """Persist a notification record to the inspectable log"""
        raise NotImplementedError