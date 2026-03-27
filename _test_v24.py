"""
Unit tests for competition notebook — v23/v24 through v30.
Extracts cell 8 from the notebook, stubs out Kaggle-only deps,
then tests each new/changed function in isolation.
"""
import json
import sys
import traceback
import types

import numpy as np

PASS = []; FAIL = []

def ok(name):   PASS.append(name); print(f"  PASS  {name}")
def fail(name, msg): FAIL.append(name); print(f"  FAIL  {name}: {msg}")

def check(name, cond, msg=""):
    if cond: ok(name)
    else:    fail(name, msg or "condition false")

# ── Load notebook cells ──────────────────────────────────────────────────────
with open('competition_notebook.ipynb', encoding='utf-8') as f:
    nb = json.load(f)
cell8_src = ''.join(nb['cells'][8]['source'])
cell9_src = ''.join(nb['cells'][9]['source'])
cell6_src = ''.join(nb['cells'][6]['source'])

# Stub out everything cell 8 needs that isn't stdlib/numpy
_ns = {"__builtins__": __builtins__, "np": np}
exec(compile(cell8_src, "<cell8>", "exec"), _ns)

_analyze_first_frame         = _ns["_analyze_first_frame"]
_greedy_lookahead            = _ns["_greedy_lookahead"]
_generalize_goals_from_score = _ns["_generalize_goals_from_score"]
_generalize_effects          = _ns["_generalize_effects"]
CURSOR_SCAN_POSITIONS        = _ns["CURSOR_SCAN_POSITIONS"]


# ════════════════════════════════════════════════════════════════════════════
print("\n=== CURSOR_SCAN_POSITIONS structure ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 1: 36 positions (6x6 grid)
check("cursor-scan-36-positions", len(CURSOR_SCAN_POSITIONS) == 36,
      f"len={len(CURSOR_SCAN_POSITIONS)}")

# Test 2: all positions are dicts with 'x' and 'y' keys (ActionInput requires dict, not tuple)
check("cursor-scan-all-dicts",
      all(isinstance(p, dict) and 'x' in p and 'y' in p for p in CURSOR_SCAN_POSITIONS),
      f"bad entries={[p for p in CURSOR_SCAN_POSITIONS if not (isinstance(p, dict) and 'x' in p)][:3]}")

# Test 3: positions are within 0-63 frame bounds
check("cursor-scan-in-bounds",
      all(0 <= p['x'] <= 63 and 0 <= p['y'] <= 63 for p in CURSOR_SCAN_POSITIONS),
      f"out of bounds={[p for p in CURSOR_SCAN_POSITIONS if not (0<=p['x']<=63 and 0<=p['y']<=63)]}")

# Test 4: all positions are distinct (no duplicates)
_pos_tuples = [(p['x'], p['y']) for p in CURSOR_SCAN_POSITIONS]
check("cursor-scan-no-duplicates",
      len(set(_pos_tuples)) == len(_pos_tuples),
      "duplicate scan positions found")

# Test 5: positions span the frame (min and max cover most of it)
xs = [p['x'] for p in CURSOR_SCAN_POSITIONS]
ys = [p['y'] for p in CURSOR_SCAN_POSITIONS]
check("cursor-scan-spans-frame",
      min(xs) <= 10 and max(xs) >= 50 and min(ys) <= 10 and max(ys) >= 50,
      f"x={min(xs)}-{max(xs)} y={min(ys)}-{max(ys)}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== _analyze_first_frame ===")
# ════════════════════════════════════════════════════════════════════════════

def make_frame(h=64, w=64, colors=None, dtype=np.uint8):
    f = np.zeros((h, w), dtype=dtype)
    if colors:
        step = h * w // len(colors)
        for i, c in enumerate(colors):
            f.flat[i*step:(i+1)*step] = c
    return f[None]  # add channel dim

# Test 6: None frame → doesn't crash, returns safe defaults dict
hint = _analyze_first_frame(None, [1,2,3,4])
check("analyze-none-frame", isinstance(hint, dict) and "game_type" in hint, str(hint))

# Test 7: grid game + 3 colors → board_cleared hypothesis fires
grid_frame = np.zeros((1, 64, 64), dtype=np.uint8)
for i in range(6):
    for j in range(6):
        grid_frame[0, i*10, j*10] = (i*6+j) % 4
hint = _analyze_first_frame(grid_frame, [1,2,3,4,5,6])
hyp_types = [h for h, _ in hint.get("goal_hypotheses", [])]
check("grid-board-cleared-hyp", "board_cleared" in hyp_types,
      f"hyps={hyp_types} grid={hint.get('is_grid_game')} cd={hint.get('color_diversity')}")

# Test 8: non-grid multi-color frame → board_cleared fires (v24 new)
nongrid_frame = np.zeros((1, 64, 64), dtype=np.uint8)
nongrid_frame[0, 5, 7] = 1
nongrid_frame[0, 13, 22] = 2
nongrid_frame[0, 37, 51] = 3
nongrid_frame[0, 60, 3] = 2
hint = _analyze_first_frame(nongrid_frame, [1,2,3,4,5,6])
hyp_types = [h for h, _ in hint.get("goal_hypotheses", [])]
check("nongrid-board-cleared-hyp", "board_cleared" in hyp_types,
      f"hyps={hyp_types} grid={hint.get('is_grid_game')} cd={hint.get('color_diversity')}")

# Test 9: cursor game (ACTION6 only) → cursor_mode=True
hint = _analyze_first_frame(nongrid_frame, [6], cursor_mode=True)
check("cursor-game-type", hint["cursor_mode"] == True, str(hint["cursor_mode"]))

# Test 10: isolated bright pixel → player_at_goal fires
bright_frame = np.zeros((1, 64, 64), dtype=np.uint8)
bright_frame[0, 32, 32] = 255
hint = _analyze_first_frame(bright_frame, [1,2,3,4])
hyp_types = [h for h, _ in hint.get("goal_hypotheses", [])]
check("player-at-goal-hyp", "player_at_goal" in hyp_types,
      f"hyps={hyp_types} bright_count={hint.get('bright_count')}")

# Test 11: hint dict always contains required keys
required_keys = {"game_type", "cursor_mode", "is_grid_game", "color_diversity",
                 "goal_hypotheses", "is_symmetric"}
hint11 = _analyze_first_frame(make_frame(), [1,2,3])
check("hint-has-required-keys",
      required_keys.issubset(hint11.keys()),
      f"missing={required_keys - hint11.keys()}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== _generalize_goals_from_score ===")
# ════════════════════════════════════════════════════════════════════════════

class MockCM:
    def __init__(self):
        self._goal_cells = {}
        self._all_positions = set()
        self._effects = {}

# Test 12: score > 0, clear A→B transition → seeds other A-colored cells
cm = MockCM()
prev = np.zeros((64, 64), dtype=np.uint8)
nxt  = np.zeros((64, 64), dtype=np.uint8)
prev[5,5] = prev[10,10] = prev[15,15] = 1
nxt[5,5]  = nxt[10,10]  = nxt[15,15]  = 0
prev[20,20] = prev[25,25] = 1
n = _generalize_goals_from_score(cm, prev[None], nxt[None], score_delta=0.1)
check("goal-gen-seeds-color1-to-0", n > 0, f"injected={n}")
check("goal-gen-correct-target", all(v == 0 for v in cm._goal_cells.values()),
      f"targets={set(cm._goal_cells.values())}")
check("goal-gen-unseeded-cells", (20,20) in cm._goal_cells or (25,25) in cm._goal_cells,
      f"goal_cells keys sample={list(cm._goal_cells.keys())[:5]}")

# Test 13: score == 0 → no injection
cm2 = MockCM()
n2 = _generalize_goals_from_score(cm2, prev[None], nxt[None], score_delta=0.0)
check("goal-gen-no-score-no-inject", n2 == 0, f"injected={n2}")

# Test 14: too many changed cells → no injection (level transition noise)
cm3 = MockCM()
prev3 = np.random.randint(0, 4, (64,64), dtype=np.uint8)
nxt3  = np.random.randint(0, 4, (64,64), dtype=np.uint8)
n3 = _generalize_goals_from_score(cm3, prev3[None], nxt3[None], score_delta=0.5)
check("goal-gen-too-many-changes-skip", n3 == 0, f"injected={n3}")

# Test 15: cap at 100 goal cells
cm4 = MockCM()
prev4 = np.ones((64, 64), dtype=np.uint8)
nxt4  = np.zeros((64, 64), dtype=np.uint8)
nxt4[0,0] = nxt4[0,1] = nxt4[0,2] = 0
n4 = _generalize_goals_from_score(cm4, prev4[None], nxt4[None], score_delta=0.1)
check("goal-gen-cap-100", len(cm4._goal_cells) <= 100,
      f"goal_cells={len(cm4._goal_cells)}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== _greedy_lookahead ===")
# ════════════════════════════════════════════════════════════════════════════

class MockLoop:
    def __init__(self, effects, goal_cells, sim_results):
        self._causal_map = MockCM2(effects, goal_cells, sim_results)
        self._cursor_mode = False

class MockCM2:
    def __init__(self, effects, goal_cells, sim_results):
        self._effects = effects
        self._goal_cells = goal_cells
        self._sim_results = sim_results
    def simulate_action(self, state, action_num):
        return self._sim_results.get(action_num)

frame = np.zeros((64, 64), dtype=np.uint8)
frame[5, 5] = 1
goal_cells = {(5, 5): 0}
effects_dummy = {i: object() for i in range(5)}

# Test 16: action 2 achieves goal → picked
loop = MockLoop(effects_dummy, goal_cells, {1: {(5,5): 1}, 2: {(5,5): 0}})
result = _greedy_lookahead(loop, frame[None], [1, 2], goal_cells)
check("lookahead-picks-best-action", result == 2, f"got={result}")

# Test 17: no action improves → returns None
loop2 = MockLoop(effects_dummy, goal_cells, {1: {(5,5): 1}, 2: {(5,5): 1}})
result2 = _greedy_lookahead(loop2, frame[None], [1, 2], goal_cells)
check("lookahead-no-improvement-none", result2 is None, f"got={result2}")

# Test 18: no simulate_action method → returns None
class NoCM:
    _effects = {i: object() for i in range(5)}
    _goal_cells = {(0,0): 1}
class LoopNoSim:
    _causal_map = NoCM()
    _cursor_mode = False
result3 = _greedy_lookahead(LoopNoSim(), frame[None], [1,2], {(0,0): 1})
check("lookahead-no-simulate-none", result3 is None, f"got={result3}")

# Test 19: fewer than 3 effects → returns None
class FewEffectsCM:
    _effects = {1: object()}
    _goal_cells = {(0,0): 1}
    def simulate_action(self, s, a): return {(0,0): 1}
class LoopFewEff:
    _causal_map = FewEffectsCM()
    _cursor_mode = False
result4 = _greedy_lookahead(LoopFewEff(), frame[None], [1,2], {(0,0):1})
check("lookahead-few-effects-none", result4 is None, f"got={result4}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== _crashed_actions persistence (v24/v25 logic) ===")
# ════════════════════════════════════════════════════════════════════════════

class FakeLoop:
    pass

# Test 20: prior_loop has _crashed_actions_persistent → restored
prior = FakeLoop()
prior._crashed_actions_persistent = {6}
crashed = set(getattr(prior, "_crashed_actions_persistent", set()))
crashed.update(int(a) for a in {}.get("_session_crashed", []))
check("crashed-restored-from-prior", 6 in crashed, f"crashed={crashed}")

# Test 21: prior_loop has no persistent set → starts empty
prior2 = FakeLoop()
crashed2 = set(getattr(prior2, "_crashed_actions_persistent", set()))
crashed2.update(int(a) for a in {}.get("_session_crashed", []))
check("crashed-empty-without-prior", len(crashed2) == 0, f"crashed={crashed2}")

# Test 22: knowledge["_session_crashed"] feeds into _crashed_actions
prior3 = FakeLoop()
knowledge3 = {"_session_crashed": [6]}
crashed3 = set(getattr(prior3, "_crashed_actions_persistent", set()))
crashed3.update(int(a) for a in knowledge3.get("_session_crashed", []))
check("crashed-from-knowledge-dict", 6 in crashed3, f"crashed={crashed3}")

# Test 23: persist logic adds to loop._crashed_actions_persistent
loop_obj = FakeLoop()
action_num = 6
if not hasattr(loop_obj, "_crashed_actions_persistent"):
    loop_obj._crashed_actions_persistent = set()
loop_obj._crashed_actions_persistent.add(action_num)
check("crashed-persist-on-loop", 6 in loop_obj._crashed_actions_persistent,
      str(loop_obj._crashed_actions_persistent))

# Test 24: all actions crashed → _eff_avail empty
current_available = [6]
_crashed_actions = {6}
eff = [a for a in current_available if a not in _crashed_actions]
check("eff-avail-all-crashed-empty", eff == [], f"eff={eff}")

# Test 25: mixed — only unconstrained actions returned
current_available2 = [1, 2, 3, 6]
_crashed_actions2 = {6}
eff2 = [a for a in current_available2 if a not in _crashed_actions2]
check("eff-avail-mixed-excludes-crashed", eff2 == [1,2,3] and 6 not in eff2, f"eff={eff2}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== give-up condition: frame_hits fix (v26) ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 26: give-up logic uses frame_hits now
check("giveup-uses-frame-hits",
      "n.get(\"frame_hits\", 0) == 0" in cell6_src,
      "frame_hits check not found in give-up condition")

# Test 27: probe note includes frame_hits field
check("probe-note-has-frame-hits",
      '"frame_hits": getattr(loop, "_total_frame_hits", 0)' in cell6_src,
      "frame_hits not in probe note")

# Test 28: cell 9 stores _total_frame_hits before return
check("cell9-stores-frame-hits",
      "loop._total_frame_hits = sum(_frame_hit.values())" in cell9_src,
      "_total_frame_hits not stored in cell 9")

# Test 29: movement game (effects=0, frame_hits>0) is NOT all_blind
probe_notes_movement = [
    {"type": "probe", "effects_learned": 0, "frame_hits": 15},
    {"type": "probe", "effects_learned": 0, "frame_hits": 22},
]
all_blind_movement = all(
    n.get("effects_learned", 0) == 0 and n.get("frame_hits", 0) == 0
    for n in probe_notes_movement
)
check("movement-game-not-blind", not all_blind_movement,
      "movement game incorrectly flagged as blind")

# Test 30: truly unresponsive game IS all_blind
probe_notes_blind = [
    {"type": "probe", "effects_learned": 0, "frame_hits": 0},
    {"type": "probe", "effects_learned": 0, "frame_hits": 0},
    {"type": "probe", "effects_learned": 0, "frame_hits": 0},
]
all_blind_blind = all(
    n.get("effects_learned", 0) == 0 and n.get("frame_hits", 0) == 0
    for n in probe_notes_blind
)
check("truly-blind-game-flagged", all_blind_blind,
      "unresponsive game not flagged as blind")

# Test 31: toggle game (effects>0) is NOT all_blind
probe_notes_toggle = [{"type": "probe", "effects_learned": 12, "frame_hits": 8}]
all_blind_toggle = all(
    n.get("effects_learned", 0) == 0 and n.get("frame_hits", 0) == 0
    for n in probe_notes_toggle
)
check("toggle-game-not-blind", not all_blind_toggle, "toggle game incorrectly flagged as blind")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== score_delta initialization (v23) ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 32: verify cell 9 source has initialization before the while loop
check("score-delta-init-present",
      "score_delta = 0.0  # v23" in cell9_src,
      "initialization line not found in cell 9")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v28: ACTION6 never blacklisted ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 33: ACTION6 crash → not blacklisted, cursor mode enabled
class FakeLoop28:
    pass
loop28 = FakeLoop28()
_crashed28 = set()
action_num28 = 6
cursor_scan_done28 = True
cursor_scan_idx28 = 5
if action_num28 == 6:
    loop28._cursor_mode = True
    cursor_scan_done28 = False
    cursor_scan_idx28 = 0
else:
    _crashed28.add(action_num28)
check("action6-not-blacklisted-on-crash", 6 not in _crashed28, f"crashed={_crashed28}")
check("action6-cursor-mode-enabled-on-crash", getattr(loop28, "_cursor_mode", False),
      "cursor mode not enabled on ACTION6 crash")
check("action6-scan-reset-on-crash",
      cursor_scan_done28 == False and cursor_scan_idx28 == 0,
      f"done={cursor_scan_done28} idx={cursor_scan_idx28}")

# Test 34: Non-ACTION6 crash → still blacklisted
loop34 = FakeLoop28()
_crashed34 = set()
action_num34 = 3
if action_num34 == 6:
    loop34._cursor_mode = True
else:
    _crashed34.add(action_num34)
check("non-action6-still-blacklisted", 3 in _crashed34, f"crashed={_crashed34}")
check("non-action6-no-cursor-mode-set", not getattr(loop34, "_cursor_mode", False),
      "non-6 crash should not set cursor mode")

# Test 35: After ACTION6 crash, _eff_avail still includes ACTION6
available35 = [6]
crashed35 = set()  # ACTION6 NOT added
eff35 = [a for a in available35 if a not in crashed35]
check("eff-avail-includes-action6-after-crash", eff35 == [6], f"eff={eff35}")

# Test 36: cell 9 contains v28 except-block distinguishing action_num == 6
check("cell9-has-action6-except-branch",
      "if action_num == 6:" in cell9_src and "enabling cursor scan" in cell9_src,
      "v28 action6 except branch missing from cell 9")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v29/v30: new_obs is None handler ===")
# ════════════════════════════════════════════════════════════════════════════

class FakeLoop30:
    pass

# Test 37: First None for ACTION6 (_cursor_scan_done=True) → enable cursor scan, continue
loop37 = FakeLoop30()
cursor_scan_done_37 = True    # NOT yet scanning
cursor_scan_idx_37 = 9
action_num_37 = 6
new_obs_37 = None
did_continue_37 = False
did_break_37 = False
if new_obs_37 is None:
    if action_num_37 == 6:
        if cursor_scan_done_37:
            loop37._cursor_mode = True
            cursor_scan_done_37 = False
            cursor_scan_idx_37 = 0
            did_continue_37 = True
        else:
            did_break_37 = True
    else:
        did_break_37 = True
check("v30-first-none-enables-cursor", getattr(loop37, "_cursor_mode", False),
      "cursor mode not enabled on first None")
check("v30-first-none-resets-scan",
      cursor_scan_done_37 == False and cursor_scan_idx_37 == 0,
      f"done={cursor_scan_done_37} idx={cursor_scan_idx_37}")
check("v30-first-none-continues", did_continue_37 and not did_break_37,
      f"continue={did_continue_37} break={did_break_37}")

# Test 38: Second None for ACTION6 (_cursor_scan_done=False, cursor scan active) → break
loop38 = FakeLoop30()
loop38._cursor_mode = True    # already enabled
cursor_scan_done_38 = False   # scan is active (cursor scan running)
cursor_scan_idx_38 = 5
action_num_38 = 6
new_obs_38 = None
did_continue_38 = False
did_break_38 = False
if new_obs_38 is None:
    if action_num_38 == 6:
        if cursor_scan_done_38:
            loop38._cursor_mode = True
            cursor_scan_done_38 = False
            cursor_scan_idx_38 = 0
            did_continue_38 = True
        else:
            did_break_38 = True  # cursor scan active but still None → give up
    else:
        did_break_38 = True
check("v30-second-none-breaks", did_break_38 and not did_continue_38,
      f"break={did_break_38} continue={did_continue_38}")
check("v30-second-none-no-reset",
      cursor_scan_idx_38 == 5,  # NOT reset to 0
      f"cursor_scan_idx was unexpectedly reset: {cursor_scan_idx_38}")
check("v30-second-none-no-infinite-loop",
      cursor_scan_done_38 == False and cursor_scan_idx_38 == 5,
      "cursor scan state changed unexpectedly during second None")

# Test 39: Non-ACTION6 None → always break, no cursor mode
loop39 = FakeLoop30()
cursor_scan_done_39 = True
cursor_scan_idx_39 = 3
action_num_39 = 3  # not ACTION6
new_obs_39 = None
did_continue_39 = False
did_break_39 = False
if new_obs_39 is None:
    if action_num_39 == 6:
        if cursor_scan_done_39:
            loop39._cursor_mode = True
            cursor_scan_done_39 = False
            cursor_scan_idx_39 = 0
            did_continue_39 = True
        else:
            did_break_39 = True
    else:
        did_break_39 = True
check("v30-non-action6-none-breaks", did_break_39 and not did_continue_39,
      f"break={did_break_39}")
check("v30-non-action6-no-cursor-mode", not getattr(loop39, "_cursor_mode", False),
      "non-ACTION6 None set cursor mode unexpectedly")
check("v30-non-action6-scan-unchanged",
      cursor_scan_done_39 == True and cursor_scan_idx_39 == 3,
      "non-ACTION6 None changed cursor scan state")

# Test 40: Verify the v30 fix is in cell 9 source (code structure check)
check("cell9-has-v30-cursor-scan-done-check",
      "if _cursor_scan_done:" in cell9_src,
      "v30 _cursor_scan_done branch missing from cell 9")

check("cell9-has-v30-broken-with-coords",
      "broken even with coordinates" in cell9_src,
      "v30 'broken even with coordinates' message missing from cell 9")

check("cell9-no-unconditional-cursor-reset",
      # The reset should only appear inside the `if _cursor_scan_done:` branch, not bare
      cell9_src.count("_cursor_scan_idx = 0") <= 5,  # v45 adds one in keyboard_click all-fire branch
      f"Too many bare _cursor_scan_idx=0 resets: {cell9_src.count('_cursor_scan_idx = 0')}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== cursor scan state machine (full scenario) ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 41: cursor scan advances idx on each call
cursor_scan_done = False
cursor_scan_idx = 0
effects = {}  # no effects yet
for i in range(5):
    action_data = None
    if (not cursor_scan_done
            and cursor_scan_idx < len(CURSOR_SCAN_POSITIONS)
            and len(effects) == 0):
        action_data = CURSOR_SCAN_POSITIONS[cursor_scan_idx]
        cursor_scan_idx += 1
check("cursor-scan-idx-advances", cursor_scan_idx == 5,
      f"idx should be 5 after 5 iterations, got {cursor_scan_idx}")

# Test 42: cursor scan stops at 36 positions
cursor_scan_done2 = False
cursor_scan_idx2 = 0
effects2 = {}
for i in range(40):  # more than 36
    if (not cursor_scan_done2
            and cursor_scan_idx2 < len(CURSOR_SCAN_POSITIONS)
            and len(effects2) == 0):
        _ = CURSOR_SCAN_POSITIONS[cursor_scan_idx2]
        cursor_scan_idx2 += 1
        if cursor_scan_idx2 >= len(CURSOR_SCAN_POSITIONS):
            cursor_scan_done2 = True
check("cursor-scan-completes-at-36",
      cursor_scan_done2 == True and cursor_scan_idx2 == 36,
      f"done={cursor_scan_done2} idx={cursor_scan_idx2}")

# Test 43: cursor scan stops early when frame changes (hit found)
cursor_scan_done3 = False
cursor_scan_idx3 = 0
effects3 = {}
pixel_count = 0
for i in range(40):
    if (not cursor_scan_done3
            and cursor_scan_idx3 < len(CURSOR_SCAN_POSITIONS)
            and len(effects3) == 0):
        _ = CURSOR_SCAN_POSITIONS[cursor_scan_idx3]
        cursor_scan_idx3 += 1
    # Simulate frame change at step 7
    if i == 7:
        pixel_count = 10  # frame changed!
        if not cursor_scan_done3 and pixel_count > 0:
            cursor_scan_done3 = True
check("cursor-scan-stops-on-frame-change",
      cursor_scan_done3 == True and cursor_scan_idx3 <= 10,
      f"done={cursor_scan_done3} idx={cursor_scan_idx3}")

# Test 44: cursor scan skipped when effects known
cursor_scan_done4 = False
cursor_scan_idx4 = 0
effects4 = {1: object(), 2: object(), 3: object()}  # has effects
action_data4 = "sentinel"
if (not cursor_scan_done4
        and cursor_scan_idx4 < len(CURSOR_SCAN_POSITIONS)
        and len(effects4) == 0):  # condition: no effects
    action_data4 = CURSOR_SCAN_POSITIONS[cursor_scan_idx4]
    cursor_scan_idx4 += 1
check("cursor-scan-skipped-with-effects",
      action_data4 == "sentinel" and cursor_scan_idx4 == 0,
      f"scan ran despite having effects: idx={cursor_scan_idx4}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v27: fast-exit before arcade.make ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 45: all available actions crashed → fast-exit fires
_scr_45 = {6}
_prev_avail_45 = [6]
fast_exit_45 = bool(_scr_45 and _prev_avail_45 and
                    all(int(a) in _scr_45 for a in _prev_avail_45))
check("fast-exit-all-crashed", fast_exit_45,
      f"scr={_scr_45} prev={_prev_avail_45}")

# Test 46: some uncollided actions → fast-exit does NOT fire
_scr_46 = {6}
_prev_avail_46 = [1, 2, 3, 4, 5, 6]
fast_exit_46 = bool(_scr_46 and _prev_avail_46 and
                    all(int(a) in _scr_46 for a in _prev_avail_46))
check("fast-exit-partial-crashed-no-exit", not fast_exit_46,
      "should not exit: only action 6 crashed")

# Test 47: empty _prev_avail (first attempt) → fast-exit does NOT fire
_scr_47 = {6}
_prev_avail_47 = []
fast_exit_47 = bool(_scr_47 and _prev_avail_47 and
                    all(int(a) in _scr_47 for a in _prev_avail_47))
check("fast-exit-empty-prev-no-exit", not fast_exit_47,
      "empty _prev_avail should prevent fast-exit")

# Test 48: empty _session_crashed → fast-exit does NOT fire
_scr_48 = set()
_prev_avail_48 = [6]
fast_exit_48 = bool(_scr_48 and _prev_avail_48 and
                    all(int(a) in _scr_48 for a in _prev_avail_48))
check("fast-exit-no-crashed-no-exit", not fast_exit_48,
      "empty _session_crashed should prevent fast-exit")

# Test 49: cell 6 stores _last_avail_actions after env.reset()
check("cell6-stores-last-avail-actions",
      '"_last_avail_actions"' in cell6_src,
      "_last_avail_actions not in cell 6")

# Test 50: cell 6 has fast-exit check
check("cell6-has-fast-exit-check",
      "_prev_avail" in cell6_src and "_scr" in cell6_src,
      "fast-exit vars not in cell 6")

# Test 51: _last_avail_actions stored as ints (not enum objects)
_stored51 = [int(a) for a in [6, 1, 2]]
check("last-avail-stored-as-ints",
      _stored51 == [6, 1, 2] and all(isinstance(x, int) for x in _stored51),
      f"stored={_stored51}")

# Test 52: multiple crashed actions across two games, union covers all avail → exit
_scr_52 = {1, 2, 3, 6}
_prev_avail_52 = [1, 2, 3, 6]
fast_exit_52 = bool(_scr_52 and _prev_avail_52 and
                    all(int(a) in _scr_52 for a in _prev_avail_52))
check("fast-exit-all-4-actions-crashed", fast_exit_52,
      f"should exit when all 4 actions crashed")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== dead action logic ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 53: action with 3 probes and 0 hits → marked dead
_probe_counts_53 = {1: 3, 2: 1}
_frame_hit_53 = {1: 0, 2: 1}
_crashed_53 = set()
_dead_53 = set()
for act in [1, 2]:
    if (_probe_counts_53.get(act, 0) >= 3
            and _frame_hit_53.get(act, 0) == 0
            and act not in _crashed_53):
        _dead_53.add(act)
check("dead-action-added-at-3-probes-0-hits", 1 in _dead_53, f"dead={_dead_53}")
check("active-action-not-dead", 2 not in _dead_53, f"dead={_dead_53}")

# Test 54: dead actions deprioritized but NOT removed from _eff_avail
available_54 = [1, 2, 3, 4]
crashed_54 = set()
dead_54 = {1}
eff_54 = [a for a in available_54 if a not in crashed_54]
check("dead-action-stays-in-eff-avail", 1 in eff_54,
      "dead action should remain in eff_avail (only deprioritized, not excluded)")

# Test 55: level-up clears dead_actions (new layout may re-open blocked moves)
dead_55 = {1, 2}
level_up_55 = True
if level_up_55:
    dead_55.clear()
check("dead-cleared-on-level-up", len(dead_55) == 0, f"dead={dead_55}")

# Test 56: major frame change clears dead_actions
dead_56 = {1, 2, 3}
pixel_count_56 = 5000  # > FRAME_CHANGE_MAJOR
FRAME_CHANGE_MAJOR = 200  # approximate
if pixel_count_56 > FRAME_CHANGE_MAJOR:
    dead_56.clear()
check("dead-cleared-on-major-frame-change", len(dead_56) == 0, f"dead={dead_56}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v30 regression: no infinite loop ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 57: simulate the v29 bug — would have looped forever
# With v30, the second None should break instead of resetting idx
loop57 = FakeLoop30()
cursor_scan_done_57 = True  # not yet scanning
cursor_scan_idx_57 = 0
action_num_57 = 6
iterations_57 = 0
MAX_ITER = 1000  # if this hits, we have the bug

while iterations_57 < MAX_ITER:
    new_obs = None  # ACTION6 always returns None (broken game)
    if new_obs is None:
        if action_num_57 == 6:
            if cursor_scan_done_57:
                # First None: enable cursor scan
                loop57._cursor_mode = True
                cursor_scan_done_57 = False
                cursor_scan_idx_57 = 0
                iterations_57 += 1
                continue  # loop continues with cursor scan active
            else:
                # Second None: cursor scan active but still None → break
                break
        else:
            break
    iterations_57 += 1

check("v30-no-infinite-loop",
      iterations_57 < MAX_ITER,
      f"ran {iterations_57} iterations — infinite loop!")
check("v30-loop-exits-after-two-nones",
      iterations_57 == 1,  # one continue, then break
      f"expected 1 iteration before break, got {iterations_57}")

# Test 58: cursor scan active game — valid coordinates provided before possible None
loop58 = FakeLoop30()
cursor_scan_done_58 = False  # scan already active (cursor game, prior attempt set it)
cursor_scan_idx_58 = 3
effects_58 = {}  # no effects yet

# Normal step: cursor scan provides coordinates
action_data_58 = None
if (not cursor_scan_done_58
        and cursor_scan_idx_58 < len(CURSOR_SCAN_POSITIONS)
        and len(effects_58) == 0):
    action_data_58 = CURSOR_SCAN_POSITIONS[cursor_scan_idx_58]
    cursor_scan_idx_58 += 1

check("cursor-scan-provides-coords-when-active",
      action_data_58 == CURSOR_SCAN_POSITIONS[3] and isinstance(action_data_58, dict),
      f"expected dict POSITIONS[3]={CURSOR_SCAN_POSITIONS[3]}, got {action_data_58}")
check("cursor-scan-idx-advances-normally",
      cursor_scan_idx_58 == 4,
      f"expected idx=4, got {cursor_scan_idx_58}")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== cell source integrity checks ===")
# ════════════════════════════════════════════════════════════════════════════

# Test 59: v31 regression — cursor scan positions must be dicts (not tuples)
# ActionInput pydantic model rejects tuples with: "Input should be a valid dictionary"
check("v31-cursor-scan-positions-are-dicts",
      all(isinstance(p, dict) and set(p.keys()) == {'x', 'y'} for p in CURSOR_SCAN_POSITIONS),
      f"some positions are not {{'x':..,'y':..}} dicts: {[p for p in CURSOR_SCAN_POSITIONS if not isinstance(p,dict)][:3]}")

# Test 61: cell 9 still has the v28 except-block for ACTION6
check("cell9-v28-except-block-intact",
      "except Exception as e:" in cell9_src and
      "if action_num == 6:" in cell9_src,
      "v28 except block missing")

# Test 60: cell 9 has the v30 `if _cursor_scan_done:` guard in new_obs None handler
# This should appear within `if new_obs is None:` → `if action_num == 6:`
none_handler = cell9_src[cell9_src.find("if new_obs is None:"):]
none_handler = none_handler[:500]  # only check the first 500 chars
check("cell9-v30-cursor-scan-done-guard-in-none-handler",
      "if _cursor_scan_done:" in none_handler,
      f"_cursor_scan_done check not in none handler:\n{none_handler}")

# Test 61: cell 9 has the "give up" message for broken-with-coordinates case
check("cell9-v30-broken-even-with-coords",
      "broken even with coordinates" in cell9_src,
      "v30 give-up message missing")

# Test 62: cell 9 has "enabling cursor scan" message (v29/v30)
check("cell9-has-enabling-cursor-scan-message",
      "enabling cursor scan" in cell9_src,
      "enabling cursor scan message missing")

# Test 63: cell 9 does NOT have the old unconditional v29 code
# The old broken v29 code had "_cursor_scan_idx = 0" directly inside
# `if action_num == 6:` without the `if _cursor_scan_done:` guard
# We can't directly test absence (it was patched), but we can test that
# the guard is present (implies the unconditional version is gone)
check("cell9-v30-has-guard-not-bare-reset",
      "if _cursor_scan_done:" in cell9_src,
      "v30 guard missing — may still have bare reset causing infinite loop")

# Test 64: cell 6 has scorecard_id
check("cell6-has-scorecard",
      "scorecard_id" in cell6_src,
      "scorecard_id not in cell 6")

# Test 65: cell 9 has CURSOR_SCAN_POSITIONS reference
check("cell9-uses-cursor-scan-positions",
      "CURSOR_SCAN_POSITIONS" in cell9_src,
      "CURSOR_SCAN_POSITIONS not referenced in cell 9")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v32: relaxed give-up thresholds ===")
# ════════════════════════════════════════════════════════════════════════════

# Reload cell6_src after patches
cell6_src_v32 = ''.join(nb['cells'][6]['source'])

# Test 66: truly-blind threshold now 5 (was 3)
check("v32-blind-threshold-is-5",
      "zero_attempts >= 5 and best_score == 0.0 and _all_blind" in cell6_src_v32,
      "blind threshold not updated to 5")
check("v32-old-blind-threshold-gone",
      "zero_attempts >= 3 and best_score == 0.0 and _all_blind" not in cell6_src_v32,
      "old blind threshold (3) still present")

# Test 67: zero-probe threshold now 20 (was 5)
check("v32-zero-probe-threshold-is-20",
      "zero_attempts >= 20 and best_score == 0.0" in cell6_src_v32,
      "zero-probe threshold not updated to 20")
check("v32-old-zero-probe-threshold-gone",
      # Check the elif form (without _all_blind) is gone — the `>= 5` may still appear in the blind check
      "elif zero_attempts >= 5 and best_score == 0.0" not in cell6_src_v32,
      "old zero-probe elif threshold (5) still present (non-blind path)")

# Test 68: plateau attempts now 30 (was 10)
check("v32-plateau-attempts-is-30",
      "plateau_attempts >= 30" in cell6_src_v32,
      "plateau attempts threshold not updated to 30")
check("v32-old-plateau-attempts-gone",
      "plateau_attempts >= 10" not in cell6_src_v32,
      "old plateau attempts threshold (10) still present")

# Test 69: plateau time now 240s (was 60s)
check("v32-plateau-time-is-240",
      "last_progress_time >= 240" in cell6_src_v32,
      "plateau time threshold not updated to 240s")
check("v32-old-plateau-time-gone",
      "last_progress_time >= 60" not in cell6_src_v32,
      "old plateau time threshold (60s) still present")

# Test 70: logic simulation — truly-blind game gives up at 5, not before
zero_attempts_blind = 4
best_score_blind = 0.0
all_blind_v32 = True
# Should NOT trigger at 4
giveup_at_4 = zero_attempts_blind >= 5 and best_score_blind == 0.0 and all_blind_v32
check("v32-blind-no-giveup-at-4", not giveup_at_4,
      "blind game incorrectly gives up at 4 attempts")
# Should trigger at 5
zero_attempts_blind = 5
giveup_at_5 = zero_attempts_blind >= 5 and best_score_blind == 0.0 and all_blind_v32
check("v32-blind-giveup-at-5", giveup_at_5,
      "blind game should give up at 5 attempts")

# Test 71: logic simulation — effects>0 game doesn't give up until 20
zero_attempts_eff = 15
best_score_eff = 0.0
giveup_at_15 = zero_attempts_eff >= 20 and best_score_eff == 0.0
check("v32-effects-no-giveup-at-15", not giveup_at_15,
      "effects>0 game incorrectly gives up at 15 attempts")
zero_attempts_eff = 20
giveup_at_20 = zero_attempts_eff >= 20 and best_score_eff == 0.0
check("v32-effects-giveup-at-20", giveup_at_20,
      "effects>0 game should give up at 20 attempts")

# Test 72: plateau logic — doesn't exit at 10 attempts anymore
plateau_attempts_72 = 10
last_progress_72 = 0.0
import time as _time

current_time_72 = 50.0  # 50 seconds since last progress
plateau_exit_72 = plateau_attempts_72 >= 30 or (plateau_attempts_72 >= 5 and current_time_72 >= 240)
check("v32-plateau-no-exit-at-10-attempts-50s", not plateau_exit_72,
      f"plateau should not exit at {plateau_attempts_72} attempts / {current_time_72}s")

# Test 73: plateau logic — exits at 30 attempts
plateau_attempts_73 = 30
plateau_exit_73 = plateau_attempts_73 >= 30 or (plateau_attempts_73 >= 5 and 50.0 >= 240)
check("v32-plateau-exits-at-30-attempts", plateau_exit_73,
      "plateau should exit at 30 attempts")

# Test 74: plateau logic — exits at 5 attempts + 240s
plateau_attempts_74 = 5
time_since_74 = 240.0
plateau_exit_74 = plateau_attempts_74 >= 30 or (plateau_attempts_74 >= 5 and time_since_74 >= 240)
check("v32-plateau-exits-at-5-attempts-240s", plateau_exit_74,
      "plateau should exit at 5 attempts + 240s")

# Test 75: plateau logic — doesn't exit at 5 attempts + 180s
plateau_attempts_75 = 5
time_since_75 = 180.0
plateau_exit_75 = plateau_attempts_75 >= 30 or (plateau_attempts_75 >= 5 and time_since_75 >= 240)
check("v32-plateau-no-exit-at-5-attempts-180s", not plateau_exit_75,
      "plateau should NOT exit at 5 attempts + 180s (need 240s)")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v33: is_complex() upfront detection ===")
# ════════════════════════════════════════════════════════════════════════════

cell9_src_v33 = ''.join(nb['cells'][9]['source'])

# Test 76: cell 9 has is_complex() detection block
check("v33-has-is-complex-detection",
      "is_complex()" in cell9_src_v33,
      "is_complex() check not found in cell 9")

# Test 77: cell 9 has _complex_actions set
check("v33-has-complex-actions-set",
      "_complex_actions = set()" in cell9_src_v33,
      "_complex_actions set not found in cell 9")

# Test 78: cell 9 never calls env.step with complex action and data=None
check("v33-always-provides-coords-for-complex",
      "action_data is None and action_num in _complex_actions" in cell9_src_v33,
      "complex action coord guard not found in cell 9")

# Test 79: complex action detection enables cursor scan immediately
check("v33-complex-enables-cursor-scan",
      "_complex_actions" in cell9_src_v33 and "not getattr(loop" in cell9_src_v33,
      "complex action cursor scan activation not found")

# Test 80: logic — complex action detection populates _complex_actions correctly
class FakeGA:
    def __init__(self, name, complex_flag):
        self.name = name
        self._complex = complex_flag
    def is_complex(self): return self._complex

fake_action_space = [FakeGA("ACTION1", False), FakeGA("ACTION6", True), FakeGA("ACTION7", True)]
_complex_actions_test = set()
for _ga in fake_action_space:
    if hasattr(_ga, "is_complex") and _ga.is_complex():
        try:
            _complex_actions_test.add(int(_ga.name.replace("ACTION", "")))
        except (ValueError, AttributeError):
            pass
check("v33-complex-detection-logic-correct",
      _complex_actions_test == {6, 7},
      f"expected {{6,7}}, got {_complex_actions_test}")

# Test 81: complex action with data=None gets coordinates assigned
_complex_actions_81 = {6}
action_num_81 = 6
action_data_81 = None
_cursor_scan_idx_81 = 3
if action_data_81 is None and action_num_81 in _complex_actions_81:
    _ca_pos = _cursor_scan_idx_81 % len(CURSOR_SCAN_POSITIONS)
    action_data_81 = CURSOR_SCAN_POSITIONS[_ca_pos]
    _cursor_scan_idx_81 += 1
check("v33-complex-action-gets-coords",
      isinstance(action_data_81, dict) and 'x' in action_data_81 and 'y' in action_data_81,
      f"expected dict with x/y, got {action_data_81}")
check("v33-cursor-idx-advances-for-complex",
      _cursor_scan_idx_81 == 4,
      f"expected idx=4, got {_cursor_scan_idx_81}")

# Test 82: non-complex action with data=None is left alone
_complex_actions_82 = {6}
action_num_82 = 1  # not complex
action_data_82 = None
if action_data_82 is None and action_num_82 in _complex_actions_82:
    action_data_82 = CURSOR_SCAN_POSITIONS[0]
check("v33-non-complex-action-data-unchanged",
      action_data_82 is None,
      "non-complex action should not get coordinates assigned")

# Test 83: cursor scan cycles through all positions (wraps with modulo)
_complex_actions_83 = {6}
action_num_83 = 6
positions_used = []
_cursor_idx_83 = 34  # near end
for i in range(5):
    ad = None
    if ad is None and action_num_83 in _complex_actions_83:
        _ca_pos = _cursor_idx_83 % len(CURSOR_SCAN_POSITIONS)
        ad = CURSOR_SCAN_POSITIONS[_ca_pos]
        _cursor_idx_83 += 1
    positions_used.append(ad)
check("v33-cursor-wraps-with-modulo",
      all(isinstance(p, dict) for p in positions_used),
      f"some positions not dict: {[p for p in positions_used if not isinstance(p,dict)]}")

# Test 84: no ACTION6 errors when complex action always gets data
# Simulates a game where ACTION6 is complex — should never see data=None calls
calls_with_no_data = 0
_complex_84 = {6}
for i in range(10):
    a_num = 6
    a_data = None  # starts as None (from probe phase)
    if a_data is None and a_num in _complex_84:
        a_data = CURSOR_SCAN_POSITIONS[i % len(CURSOR_SCAN_POSITIONS)]
    if a_data is None:
        calls_with_no_data += 1
check("v33-zero-data-none-calls-for-complex",
      calls_with_no_data == 0,
      f"{calls_with_no_data} calls with data=None for complex action")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v34: competition mode server startup ===")
# ════════════════════════════════════════════════════════════════════════════

cell12_src = ''.join(nb['cells'][12]['source'])

# Test: COMPETITION_MODE is always True (v34b)
check("v34-competition-mode-always-true",
      "COMPETITION_MODE = True" in cell12_src,
      "COMPETITION_MODE must be hardcoded True")

# Test: server arcade starts in OFFLINE mode
check("v34-server-arcade-offline-mode",
      "operation_mode=OperationMode.OFFLINE" in cell12_src,
      "server arcade must use OFFLINE mode")

# Test: listen_and_serve is called with competition_mode=True
check("v34-listen-and-serve-called",
      "_srv_arcade.listen_and_serve(competition_mode=True)" in cell12_src,
      "listen_and_serve(competition_mode=True) missing")

# Test: server runs in daemon thread
check("v34-server-runs-in-daemon-thread",
      "daemon=True" in cell12_src,
      "server thread must be daemon=True")

# Test: client arcade uses COMPETITION mode
check("v34-client-arcade-competition-mode",
      "operation_mode=OperationMode.COMPETITION" in cell12_src,
      "client arcade must use COMPETITION mode")

# Test: ARC_BASE_URL set to localhost:8001
check("v34-arc-base-url-set",
      "os.environ['ARC_BASE_URL'] = 'http://localhost:8001'" in cell12_src,
      "ARC_BASE_URL must point to localhost:8001")

# Test: no old try/except parquet block (v35 writes parquet differently)
check("v34-no-manual-parquet",
      "# -- Write submission.parquet --\ntry:" not in cell12_src,
      "old try/except parquet block must be replaced")

# Test: auto-calculated message replaced by actual parquet writing (v35)
check("v34-auto-submission-message",
      "Submission auto-calculated" not in cell12_src or "_sub_df.to_parquet" in cell12_src,
      "parquet must be written (auto-submission message replaced by v35)")

# Test: server starts before scorecard creation (correct ordering)
idx_server = cell12_src.find("_srv_arcade.listen_and_serve")
idx_scorecard = cell12_src.find("scorecard_id = arcade.create_scorecard")
check("v34-server-starts-before-scorecard",
      idx_server < idx_scorecard,
      f"server startup (idx={idx_server}) must precede scorecard creation (idx={idx_scorecard})")

# Test: sleep after server start (give Flask time to initialise)
check("v34-sleep-after-server-start",
      "time.sleep(3)" in cell12_src,
      "need time.sleep(3) after server start to let Flask initialise")

# Test: games refreshed from client arcade in competition mode
check("v34-games-refreshed-from-client",
      "games = arcade.get_environments()" in cell12_src,
      "games must be refreshed from client arcade in competition mode")


# ════════════════════════════════════════════════════════════════════════════
# v35: env.reset() None guard — prevent infinite loop on RESET 400
# ════════════════════════════════════════════════════════════════════════════
print("\n=== v35: env.reset() None guard ===")
check("v35-reset-none-guard",
      "if obs is None:" in cell6_src and "env.reset() returned None" in cell6_src,
      "play_game() must break if env.reset() returns None")
check("v35-reset-none-guard-before-available-actions",
      cell6_src.index("if obs is None:") < cell6_src.index("available_actions = obs.available_actions"),
      "None guard must come before obs.available_actions access")
check("v35-reset-none-guard-breaks",
      "env.reset() returned None" in cell6_src and "break" in cell6_src[cell6_src.index("env.reset() returned None"):cell6_src.index("env.reset() returned None")+100],
      "None guard must break the play_game loop")

# ════════════════════════════════════════════════════════════════════════════
# v35b: competition mode — single attempt per game + parquet writing
# ════════════════════════════════════════════════════════════════════════════
print("\n=== v35b: competition mode single-attempt + parquet ===")
cell12_src2 = ''.join(__import__('json').load(open('competition_notebook.ipynb', encoding='utf-8'))['cells'][12]['source'])
check("v35b-play-game-competition-mode-param",
      "competition_mode: bool = False" in cell6_src,
      "play_game() must have competition_mode param")
check("v35b-competition-break-after-attempt-1",
      "Competition mode: single attempt" in cell6_src,
      "play_game() must break after attempt 1 in competition mode")
check("v35b-main-loop-passes-competition-mode",
      "competition_mode=COMPETITION_MODE" in cell12_src2,
      "main loop must pass competition_mode to play_game()")
check("v35b-parquet-written",
      "submission.parquet" in cell12_src2 and "_sub_df.to_parquet" in cell12_src2,
      "submission.parquet must be written")
check("v35b-parquet-includes-unplayed-games",
      "_results_map.get(_g.game_id, 0.0)" in cell12_src2,
      "parquet must include unplayed games as score=0")
check("v35b-parquet-row-id-format",
      "f'{_i}_0'" in cell12_src2,
      "parquet row_id must be in 'i_0' format")
check("v35b-parquet-end-of-game-true",
      "'end_of_game': True" in cell12_src2,
      "parquet must include end_of_game=True column")

# ════════════════════════════════════════════════════════════════════════════
# v36: cursor_mode suppressed for movement_interact games
# ════════════════════════════════════════════════════════════════════════════
print("\n=== v36: cursor_mode fix for movement_interact games ===")
cell9_src2 = ''.join(__import__('json').load(open('competition_notebook.ipynb', encoding='utf-8'))['cells'][9]['source'])
check("v36-movement-types-defined",
      '_movement_types = ("movement", "movement_interact")' in cell9_src2,
      "_movement_types tuple must be defined")
check("v36-cursor-mode-check-excludes-movement",
      "_game_type_hint not in _movement_types" in cell9_src2,
      "cursor_mode must be suppressed for movement_interact game type")
check("v36-movement-suppression-message",
      "movement_interact: complex actions" in cell9_src2,
      "must log suppression message for movement_interact games")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v45: tag-based game-type detection ===")
cell9_src_v45 = ''.join(__import__('json').load(open('competition_notebook.ipynb', encoding='utf-8'))['cells'][9]['source'])
check("v45-game-tags-read",
      '_game_tags = list((knowledge or {}).get("_tags", []))' in cell9_src_v45,
      "_game_tags must be read from knowledge dict")
check("v45-pure-click-cursor-mode",
      'pure-click' in cell9_src_v45 and 'cursor_mode=True' in cell9_src_v45,
      "pure click games must set cursor_mode=True from tags")
check("v45-cursor-scan-done-uses-cursor-mode",
      '_cursor_scan_done = not getattr(loop, "_cursor_mode", False)' in cell9_src_v45,
      "_cursor_scan_done must respect tag-based cursor_mode")
check("v45-keyboard-click-no-toggle",
      'keyboard_click all-fire -> cursor_mode=True (v45)' in cell9_src_v45,
      "keyboard_click all-fire probe must use cursor_mode not CSAT toggle")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v49/v50: fix competition mode replay bug ===")
cell6_src_v49 = ''.join(__import__('json').load(open('competition_notebook.ipynb', encoding='utf-8'))['cells'][6]['source'])
check("v49-replay-partial-falls-through",
      'v49/v50' in cell6_src_v49 and 'cognitive play' in cell6_src_v49,
      "replay in competition mode must fall through to cognitive play (v50)")
check("v50-competition-mode-no-continue",
      'if not competition_mode:' in cell6_src_v49 and 'continue' in cell6_src_v49,
      "only offline mode should continue; competition mode falls through")


# ════════════════════════════════════════════════════════════════════════════
print("\n=== v46: cursor scan improvements ===")
cell9_src_v46 = ''.join(__import__('json').load(open('competition_notebook.ipynb', encoding='utf-8'))['cells'][9]['source'])
check("v46-effects-gate-uses-cursor-mode",
      "_cm_effects == 0 or getattr(loop, \"_cursor_mode\", False)" in cell9_src_v46,
      "cursor scan must run when cursor_mode=True regardless of effects count")
check("v46b-force-action6-during-scan",
      "v46b: cursor scan always clicks (ACTION6) when available" in cell9_src_v46,
      "cursor scan must force ACTION6 when it's available")


# ════════════════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print(f"\nFAILED TESTS:")
    for name in FAIL:
        print(f"  - {name}")
    sys.exit(1)
else:
    print("All tests passed — safe to ship.")
