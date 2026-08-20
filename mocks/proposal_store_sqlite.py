import json
from datetime import datetime
from typing import Optional

from adapters.proposal_store_adapter import ProposalStoreAdapter
from storage.db import get_connection, init_db
from models.proposal import Proposal, ProposalStatus


class SqliteProposalStoreAdapter(ProposalStoreAdapter):
    """Local-file-backed implementation (SQLite is our local state
    store, standing in for wherever proposal records would live in
    a real system). Wraps the exact logic already proven correct
    throughout P4/P5/P6/P8, just behind the interface now."""

    def __init__(self):
        self._init_table()

    def _init_table(self) -> None:
        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                proposal_type TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                original_payload TEXT NOT NULL,
                final_payload TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                approver TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save(self, proposal: Proposal) -> None:
        conn = get_connection()
        conn.execute("""
            INSERT INTO proposals
                (id, proposal_type, source_ref, original_payload, final_payload,
                 status, created_at, decided_at, approver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                final_payload=excluded.final_payload,
                status=excluded.status,
                decided_at=excluded.decided_at,
                approver=excluded.approver
        """, (
            proposal.id,
            proposal.proposal_type,
            proposal.source_ref,
            json.dumps(proposal.original_payload),
            json.dumps(proposal.final_payload) if proposal.final_payload is not None else None,
            proposal.status.value,
            proposal.created_at.isoformat(),
            proposal.decided_at.isoformat() if proposal.decided_at else None,
            proposal.approver,
        ))
        conn.commit()
        conn.close()

    def _row_to_proposal(self, row) -> Proposal:
        return Proposal(
            id=row["id"],
            proposal_type=row["proposal_type"],
            source_ref=row["source_ref"],
            original_payload=json.loads(row["original_payload"]),
            final_payload=json.loads(row["final_payload"]) if row["final_payload"] else None,
            status=ProposalStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            decided_at=datetime.fromisoformat(row["decided_at"]) if row["decided_at"] else None,
            approver=row["approver"],
        )

    def get(self, proposal_id: str) -> Optional[Proposal]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        conn.close()
        return self._row_to_proposal(row) if row else None

    def get_all(self) -> list[Proposal]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM proposals ORDER BY created_at ASC").fetchall()
        conn.close()
        return [self._row_to_proposal(row) for row in rows]
