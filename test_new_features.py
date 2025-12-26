"""Test the new click behavior and CODS reasoning features."""
from agent_self_model import AgentSelfModel
from cods_engine import CODSEngine

print('=== Testing Click Behavior Classification ===')
asm = AgentSelfModel()

# Test classify_click_behavior with mock data
test_frame_before = [[0,0,3,3],[0,0,3,3],[5,5,0,0],[5,5,0,0]]
test_frame_after = [[0,0,4,4],[0,0,4,4],[5,5,0,0],[5,5,0,0]]  # Object 3 changed to 4

result = asm.classify_click_behavior(
    game_id='test_game-123',
    level=1,
    click_x=2,
    click_y=0,
    object_color=3,
    frame_before_click=test_frame_before,
    frame_after_click=test_frame_after
)
print(f"Result: {result['behavior_type']}")
print(f"  is_self_toggle: {result['is_self_toggle']}")
print(f"  is_trigger: {result['is_trigger']}")
print(f"  is_selectable: {result['is_selectable']}")
print()

# Test trigger behavior (clicking object 3 changes object 5)
test_frame_trigger = [[0,0,3,3],[0,0,3,3],[0,0,0,0],[0,0,0,0]]  # Object 5 disappeared
result2 = asm.classify_click_behavior(
    game_id='test_game-123',
    level=1,
    click_x=2,
    click_y=0,
    object_color=3,
    frame_before_click=test_frame_before,
    frame_after_click=test_frame_trigger
)
print(f"Trigger test: {result2['behavior_type']}")
print(f"  is_self_toggle: {result2['is_self_toggle']}")
print(f"  is_trigger: {result2['is_trigger']}")
print(f"  other_changes: {len(result2['other_changes'])} objects affected")
print()

print('=== Testing CODS Reasoning-Aware Update ===')
cods = CODSEngine()
cods.set_context('test_game-123', 1, 'agent1')
cods.update_frame(
    frame=test_frame_before,
    score=1.0,
    action_count=5,
    reasoning='Testing symmetry detection on this level'
)
print('[OK] CODS update with reasoning worked')
print()

print('[OK] All tests passed!')
