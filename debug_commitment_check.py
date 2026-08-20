from datetime import date
from storage.commitment_tracking_service import run_commitment_check

result = run_commitment_check(as_of_date=date(2026, 8, 18))

print("=== Ageing view ===")
for entry in result["ageing_view"]:
    print(f"  {entry['id']} ({entry['person']}): {entry['classification']}")

print(f"\n=== Nudges sent ({len(result['nudges_sent'])}) ===")
for n in result["nudges_sent"]:
    print(f"  {n.recipient}: {n.message}")

print(f"\n=== Escalations ({len(result['escalations'])}) ===")
for e in result["escalations"]:
    print(f"  {e.message}")

print(f"\n=== Capped (skipped due to daily cap) ===")
print(result["capped_skips"])
