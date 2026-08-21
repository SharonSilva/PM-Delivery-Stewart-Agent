# MCP Tool Schema — Delivery Steward

Schema version: 1.0
Server entry point: mcp_server/server.py
Transport: streamable HTTP (mcp_app.streamable_http_app()), default port 8000

This is a bonus capability (per the toolkit doc: "Tool / integration
protocol... bonus marks, not required"). Every tool below is a thin
wrapper over an existing, already-tested function - no new business
logic lives in the MCP server itself.

## A note on human-in-the-loop gating via MCP

Exposing approve_proposal and reject_proposal over MCP does not weaken
the human-approval requirement. The approval gate itself
(approval/write_gate.py's execute_approved_write) enforces identically
regardless of what interface submitted the approve/reject call - it
checks the Proposal's stored status at the moment of writing, not which
interface was used to set that status. An MCP-connected agent calling
approve_proposal is only ever relaying a decision a human already made
(e.g. a delivery lead telling their own assistant "approve the T-004
one") - the same kind of explicit human authorization as typing the
command directly, just through a different interface.

## Tools

### get_morning_brief
- Input: none
- Output: string (the rendered morning brief)
- Side effects: none (read-only)
- Description: generates today's morning brief - per-person status and
  blockers ranked by age, using the shared clock's current time.

### get_eod_summary
- Input: none
- Output: string (the rendered end-of-day summary)
- Side effects: none (read-only)
- Description: generates today's end-of-day delta summary against this
  morning's snapshot.

### list_pending_proposals
- Input: none
- Output: string (formatted list of pending proposals, or a message if
  none are pending)
- Side effects: none (read-only)
- Description: lists every Proposal currently in PENDING status, with
  its id, type, and original payload.

### approve_proposal
- Input: proposal_id (string), approver (string)
- Output: string (confirmation message, or an error message if the
  write could not be executed)
- Side effects: WRITE. Sets the proposal's status to APPROVED, then
  executes the corresponding real write (currently wired for
  risk_gap_fill and blocker_promotion proposal types only - see
  WRITE_DISPATCH in mcp_server/server.py). Proposal types with no
  registered write function are refused explicitly, not silently
  no-op'd, and the approval is NOT recorded in that case.
- Requires human authorization behind the call, per the note above.

### reject_proposal
- Input: proposal_id (string), approver (string)
- Output: string (confirmation message)
- Side effects: WRITE (to the proposal's own status only - sets it to
  REJECTED). No downstream write to any other system occurs.

## Known gap, disclosed

approve_proposal only has a real write path for risk_gap_fill and
blocker_promotion proposals. Proposal types from P8 (meeting_tracker_update,
meeting_risk_entry) do not have a dedicated write-execution function in
this codebase at all yet (P8 was built and tested through the
approval/audit layer, not a full write path) - attempting to approve one
via this tool is refused with an explicit message rather than silently
doing nothing, consistent with this project's broader rule that absence
of a capability is always reported as absence.

## Versioning

Any breaking change to a tool's input/output shape should increment this
schema's version number and note the change here.
