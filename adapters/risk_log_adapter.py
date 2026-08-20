from abc import ABC, abstractmethod


class RiskLogAdapter(ABC):
    """Interface for reading and writing the risk log. Agent logic
    depends only on this interface, never on a concrete
    implementation - this closes a gap where risk-log access was
    previously direct file I/O scattered across multiple services
    with no abstraction layer."""

    @abstractmethod
    def load_risks(self) -> list[dict]:
        """Return all current risk-log entries."""
        raise NotImplementedError

    @abstractmethod
    def append_risk(self, entry: dict) -> None:
        """Append one new risk entry."""
        raise NotImplementedError
