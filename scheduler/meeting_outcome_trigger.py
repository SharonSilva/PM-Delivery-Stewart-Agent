from storage.meeting_outcome_consumer import process_meeting_outcome


def on_new_meeting_outcome(record: dict):
    """P8's trigger is event-based ('a new outcome record appears'),
    not time-based - this is the entry point a real file-watcher,
    endpoint handler, or table-poll would call when a new record
    shows up. For this mocked build, it's called directly with the
    record dict."""
    result = process_meeting_outcome(record)
    if result.refused:
        print(f"[Meeting outcome] Refused: {result.reason}")
    else:
        total = len(result.tracker_proposals) + len(result.risk_proposals)
        print(f"[Meeting outcome] Processed - {total} new proposal(s) awaiting approval.")
    return result
