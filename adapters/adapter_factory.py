"""
Central adapter factory. Every job/script that needs an adapter
should call one of these functions instead of instantiating a
Mock*Adapter class directly - this is what the brief's worked
example shows ("one factory function chooses the implementation
from configuration. Agent code imports the interface type and
never the mock").

The test this proves: to add a real integration, add one new
implementation class and one new branch below. Nothing in any
job, service, or scheduler file changes.
"""
from config.scheduler_config import ADAPTER_MODE

from adapters.tracker_adapter import TrackerAdapter
from adapters.codehost_adapter import CodeHostAdapter
from adapters.chat_adapter import ChatAdapter
from adapters.notification_adapter import NotificationAdapter
from adapters.risk_log_adapter import RiskLogAdapter
from adapters.proposal_store_adapter import ProposalStoreAdapter

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from mocks.notification_mock import MockNotificationAdapter
from mocks.risk_log_mock import MockRiskLogAdapter
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter


def get_tracker_adapter() -> TrackerAdapter:
    if ADAPTER_MODE == "mock":
        return MockTrackerAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")


def get_codehost_adapter() -> CodeHostAdapter:
    if ADAPTER_MODE == "mock":
        return MockCodeHostAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")


def get_chat_adapter() -> ChatAdapter:
    if ADAPTER_MODE == "mock":
        return MockChatAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")


def get_notification_adapter() -> NotificationAdapter:
    if ADAPTER_MODE == "mock":
        return MockNotificationAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")


def get_risk_log_adapter() -> RiskLogAdapter:
    if ADAPTER_MODE == "mock":
        return MockRiskLogAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")


def get_proposal_store_adapter() -> ProposalStoreAdapter:
    # SQLite is genuinely our local state store, not a stand-in for
    # something else - "mock" and "real" aren't meaningfully
    # different for our own state, but this stays consistent with
    # the same factory pattern as every other adapter.
    if ADAPTER_MODE == "mock":
        return SqliteProposalStoreAdapter()
    raise ValueError(f"Unknown ADAPTER_MODE: {ADAPTER_MODE}")
