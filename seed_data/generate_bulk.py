"""
Generate bullk 'background noise' items, commits, and chat messages to 
bring the seed dataset upto the brief's required columne of 25-40 items
, 30-60 commits , 60-120 messages. Uses a fixed random seed so the output 
is reproducible.Run once; output is committed as static json, not regenrated at runtime
"""

import json
import random
from datetime import datetime, timedelta

random.seed(42)

ASSIGNEES = ["Alice Chen", "Bob Martinez", "Priya Sharma", "Priya Nair", "Jordan Lee", "Sam Okafor"]
STATUSES = ["Open", "In Progress", "Done"]
TITLES = [
    "Improve error logging", "Add input validation", "Refactor test helpers",
    "Update API documentation", "Fix flaky integration test", "Optimize query performance",
    "Add retry logic to webhook handler", "Clean up unused imports", "Improve loading state UI",
    "Add pagination to list endpoint", "Fix timezone bug in scheduler", "Update dependency lockfile",
    "Add health check endpoint", "Improve form validation messages", "Refactor auth middleware",
    "Add caching layer for lookups", "Fix memory leak in worker process", "Improve accessibility on forms",
    "Add export-to-CSV feature", "Fix broken link in footer",
]
CHANNELS = ["general", "dev"]
MSG_TEMPLATES = [
    "Making good progress on {title_lower}", "Ran into a small issue with {title_lower}, investigating",
    "PR up for {title_lower}, could use a review", "{title_lower} is done, moving to next task",
    "Quick question about {title_lower} - anyone free to sync?", "Deployed {title_lower} to staging",
]

#  Bulk items T-021 onward 
bulk_items = []
bulk_transitions = []
start = datetime(2026, 8, 4)
for i, title in enumerate(TITLES, start=21):
    item_id = f"T-{i:03d}"
    created = start + timedelta(days=random.randint(0, 20), hours=random.randint(8, 17))
    sprint = "Sprint 1" if created < datetime(2026, 8, 17) else "Sprint 2"
    status = random.choice(STATUSES)
    assignee = random.choice(ASSIGNEES)
    bulk_items.append({
        "id": item_id, "title": title, "status": status, "assignee": assignee,
        "priority": random.choice(["Low", "Medium", "High"]), "sprint": sprint,
        "blocked": False, "created_at": created.isoformat(),
    })
    bulk_transitions.append({
        "item_id": item_id, "from_status": None, "to_status": "Open",
        "timestamp": created.isoformat(),
    })
    if status != "Open":
        bulk_transitions.append({
            "item_id": item_id, "from_status": "Open", "to_status": status,
            "timestamp": (created + timedelta(days=random.randint(1, 3))).isoformat(),
        })

# Bulk commits, referencing bulk items
bulk_commits = []
for i in range(25):
    item = random.choice(bulk_items)
    ts = datetime.fromisoformat(item["created_at"]) + timedelta(hours=random.randint(1, 48))
    bulk_commits.append({
        "hash": f"bulk{i:03d}x", "item_id": item["id"], "author": item["assignee"],
        "message": f"Work on {item['title'].lower()}", "timestamp": ts.isoformat(),
        "branch": item["title"].lower().replace(" ", "-")[:20],
        "pr_state": random.choice(["open", "merged"]),
    })

# Bulk chat messages, referencing bulk items (Sam excluded Aug 17-18) 
bulk_messages = []
for i in range(60):
    item = random.choice(bulk_items)
    ts = datetime.fromisoformat(item["created_at"]) + timedelta(hours=random.randint(1, 72))
    # keep Sam silent in the Aug 17-18 anchor window
    if item["assignee"] == "Sam Okafor" and datetime(2026, 8, 17) <= ts <= datetime(2026, 8, 19):
        ts = ts - timedelta(days=3)
    template = random.choice(MSG_TEMPLATES).format(title_lower=item["title"].lower())
    bulk_messages.append({
        "id": f"M-BULK-{i:03d}", "channel": random.choice(CHANNELS), "author": item["assignee"],
        "text": template, "timestamp": ts.isoformat(), "item_id": item["id"],
    })

#  Merge with hand-crafted files 
with open("seed_data/tracker_items.json") as f:
    tracker = json.load(f)
tracker["items"].extend(bulk_items)
tracker["transitions"].extend(bulk_transitions)
with open("seed_data/tracker_items.json", "w") as f:
    json.dump(tracker, f, indent=2)

with open("seed_data/commits.json") as f:
    commits = json.load(f)
commits["commits"].extend(bulk_commits)
with open("seed_data/commits.json", "w") as f:
    json.dump(commits, f, indent=2)

with open("seed_data/chat_messages.json") as f:
    messages = json.load(f)
messages["messages"].extend(bulk_messages)
with open("seed_data/chat_messages.json", "w") as f:
    json.dump(messages, f, indent=2)

print(f"Items now: {len(tracker['items'])}")
print(f"Commits now: {len(commits['commits'])}")
print(f"Messages now: {len(messages['messages'])}")