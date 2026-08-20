import json
from datetime import datetime
from typing import Optional

from storage.db import get_connection, init_db
from models.proposal import Proposal, ProposalStatus


def init_proposal_table() -> None:
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


def save_proposal(proposal: Proposal) -> None:
    init_proposal_table()
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


def _row_to_proposal(row) -> Proposal:
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


def get_proposal(proposal_id: str) -> Optional[Proposal]:
    init_proposal_table()
    conn = get_connection()
    row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
    conn.close()
    return _row_to_proposal(row) if row else None


def get_all_proposals() -> list[Proposal]:
    init_proposal_table()
    conn = get_connection()
    rows = conn.execute("SELECT * FROM proposals ORDER BY created_at ASC").fetchall()
    conn.close()
    return [_row_to_proposal(row) for row in rows]
