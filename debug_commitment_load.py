from storage.commitment_store import load_commitments

commitments = load_commitments()
print(f"{len(commitments)} commitments loaded")
for c in commitments:
    status = f"due={c.due_date}" if c.due_date else f"AMBIGUOUS (text='{c.due_date_text}')"
    print(f"  {c.id} ({c.person}): {status}")
