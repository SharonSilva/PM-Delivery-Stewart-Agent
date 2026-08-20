from adapters.risk_log_adapter import RiskLogAdapter


class InMemoryRiskLogAdapter(RiskLogAdapter):
    """A second, deliberately different implementation of
    RiskLogAdapter - NOT the real system, just proof that the
    interface can be satisfied by something other than the file-
    backed mock. This is the concrete swap-test: agent logic never
    changes, only the factory's returned instance does."""

    def __init__(self, initial_risks: list[dict] = None):
        self._risks = initial_risks or []

    def load_risks(self) -> list[dict]:
        return self._risks

    def append_risk(self, entry: dict) -> None:
        self._risks.append(entry)
