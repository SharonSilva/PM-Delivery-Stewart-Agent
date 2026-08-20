from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.sprint_planning_service import extract_sprint_planning_facts
from storage.sprint_planning_assembly_service import generate_sprint_planning_pack

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

print("############ AT CONFIGURED CAPACITY (12) ############")
facts = extract_sprint_planning_facts(snapshot)
pack = generate_sprint_planning_pack(facts)
print(pack.render())

print("\n\n############ AT HIGHER CAPACITY (25), proving the mechanism ############")
import storage.sprint_planning_service as sps
original = sps.TEAM_CAPACITY_ITEMS_PER_SPRINT
sps.TEAM_CAPACITY_ITEMS_PER_SPRINT = 25
facts2 = sps.extract_sprint_planning_facts(snapshot)
sps.TEAM_CAPACITY_ITEMS_PER_SPRINT = original
pack2 = generate_sprint_planning_pack(facts2)
print(pack2.render())
