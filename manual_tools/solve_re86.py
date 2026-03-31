"""
RE86 Solver — analytical pixel-composition approach (H60).

Win condition: cdjxpfqest() composites brush sprites (tagged "vfaeucgcyr")
onto a canvas and checks if the result matches target sprites ("vzuwsebntu").
This is a PIXEL PAINTING game — brushes need to be at exact positions so
their pixel patterns, when overlaid, equal the target image.

Why BFS fails: 50K+ nodes explored with zero wins because BFS searches
action-space (move sequences) but win lives in pixel-canvas-space (final
brush positions). The two are decoupled — any sequence reaching the target
positions wins, regardless of the path taken.

Analytical approach:
  1. Enumerate all feasible brush position combos (22^(2n) where n=brushes)
     — for 2 brushes: 22^4 = 234K combinations, ~0.2s to test
  2. For each combo: set .x/.y directly, call cdjxpfqest() — O(1) win check
  3. On match: convert (x_start→x_target, y_start→y_target) to move actions
     via directional steps (3px per action) + brush-cycle (ACTION5)

State space: 22 positions per axis × 2 axes × n brushes
  n=1: 484   n=2: 234K   n=3: 113M (needs per-brush pruning at n≥3)
"""

import importlib.util
import itertools
import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from arcengine import ActionInput, GameAction

ROOT = Path(__file__).resolve().parent.parent
GAME_FILE = ROOT / "environment_files" / "re86" / "4e57566e" / "re86.py"
GAME_ID = "re86-4e57566e"
NUM_LEVELS = 8


# ─────────────────────────────────────────────
# Game utilities
# ─────────────────────────────────────────────

def load_mod():
    spec = importlib.util.spec_from_file_location("re86_mod", GAME_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_game(cls, level_idx):
    g = cls()
    g._current_level_index = level_idx
    g._levels = list(g._clean_levels)
    g.on_set_level(g._levels[level_idx])
    return g


def perform(g, act_id, data=None):
    if data is None:
        data = {}
    ai = ActionInput(id=getattr(GameAction, f"ACTION{act_id}"), data=data)
    prev = g._current_level_index
    try:
        g.perform_action(ai)
    except Exception:
        return False, True
    return g._current_level_index > prev, g._state.name == "GAME_OVER"


def replay_sequence(cls, level_idx, actions):
    """Replay (action_num, data) pairs on a fresh game."""
    g = make_game(cls, level_idx)
    for act_num, data in actions:
        won, over = perform(g, act_num, data)
        if won:
            return g, True
        if over:
            return g, False
    return g, False


# ─────────────────────────────────────────────
# Analytical solver — pixel composition
# ─────────────────────────────────────────────

def probe_target_positions(cls, level_idx, verbose=True):
    """
    Find brush positions where cdjxpfqest() returns True.

    Method: set brush .x/.y directly (no action replay), call win check.
    Step size is 3px (one action = 3px movement).

    Returns list of (x, y) target coords per brush, or None.
    """
    g = make_game(cls, level_idx)
    level = g.current_level

    brushes = level.get_sprites_by_tag("vfaeucgcyr")
    if not brushes:
        print(f"  L{level_idx+1}: no brush sprites found", flush=True)
        return None, None

    n = len(brushes)
    step = 3
    start_xy = [(b.x, b.y) for b in brushes]

    # Early exit: already solved?
    if g.cdjxpfqest():
        return [(b.x, b.y) for b in brushes], start_xy

    def _reachable(start_coord, size):
        """Positions reachable via 3px steps that overlap the 0..63 canvas."""
        res = start_coord % step
        result = []
        p = res
        while p >= -(size - 1):
            result.append(p)
            p -= step
        p = res + step
        while p <= 63:
            result.append(p)
            p += step
        return sorted(result)

    brush_xr = [_reachable(b.x, b.width) for b in brushes]
    brush_yr = [_reachable(b.y, b.height) for b in brushes]

    total = 1
    for xr, yr in zip(brush_xr, brush_yr):
        total *= len(xr) * len(yr)
    if verbose:
        print(
            f"  L{level_idx+1}: {n} brush(es), {total:,} reachable combos to probe",
            flush=True
        )

    target_xy = None

    if n == 1:
        b = brushes[0]
        for x in brush_xr[0]:
            for y in brush_yr[0]:
                b.set_position(x, y)
                if g.cdjxpfqest():
                    target_xy = [(x, y)]
                    break
            if target_xy:
                break

    elif n == 2:
        b0, b1 = brushes[0], brushes[1]
        found = False
        for x1 in brush_xr[0]:
            for y1 in brush_yr[0]:
                b0.set_position(x1, y1)
                for x2 in brush_xr[1]:
                    for y2 in brush_yr[1]:
                        b1.set_position(x2, y2)
                        if g.cdjxpfqest():
                            target_xy = [(x1, y1), (x2, y2)]
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break

    elif n >= 3:
        pos_ranges = [
            list(itertools.product(brush_xr[i], brush_yr[i]))
            for i in range(n)
        ]
        for combo in itertools.product(*pos_ranges):
            for i, (x, y) in enumerate(combo):
                brushes[i].set_position(x, y)
            if g.cdjxpfqest():
                target_xy = list(combo)
                break

    return target_xy, start_xy


def positions_to_actions(target_xy, start_xy, step=3):
    """
    Convert list of (x_target, y_target) per brush into action sequence.

    Actions: 1=up(y−3), 2=down(y+3), 3=left(x−3), 4=right(x+3), 5=cycle brush
    Returns list of (action_num, data_dict).
    """
    actions = []
    for idx, ((tx, ty), (sx, sy)) in enumerate(zip(target_xy, start_xy)):
        if idx > 0:
            actions.append((5, {}))   # cycle to next brush
        dx = tx - sx
        dy = ty - sy
        if dx > 0:
            actions.extend([(4, {})] * (dx // step))
        elif dx < 0:
            actions.extend([(3, {})] * ((-dx) // step))
        if dy > 0:
            actions.extend([(2, {})] * (dy // step))
        elif dy < 0:
            actions.extend([(1, {})] * ((-dy) // step))
    return actions


def verify_solution(cls, level_idx, actions, verbose=True):
    """Replay action sequence and confirm level advances."""
    g, won = replay_sequence(cls, level_idx, actions)
    if verbose:
        print(
            f"  L{level_idx+1}: verify {'PASS' if won else 'FAIL'} "
            f"({len(actions)} actions)", flush=True
        )
    return won


# ─────────────────────────────────────────────
# Persistence
# ─────────────────────────────────────────────

def save_to_db(level_num, actions):
    act_list = [{"action": a, "data": d} for a, d in actions]
    conn = sqlite3.connect(str(ROOT / "core_data.db"))
    conn.execute(
        """INSERT OR REPLACE INTO winning_sequences
        (sequence_id, game_id, game_type, level_number, action_sequence,
         total_actions, total_score, efficiency_score, agent_id, session_id,
         is_active, initial_frame, final_frame, discovered_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            str(uuid.uuid4()), GAME_ID, "re86", level_num,
            json.dumps(act_list), len(act_list), 1.0,
            1.0 / max(len(act_list), 1), "analytical", "manual",
            1, "[]", "[]", datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    print(f"  DB saved L{level_num}: {len(actions)} actions", flush=True)


def save_knowledge(results):
    winning_sequences = {}
    for level_num, actions in results.items():
        winning_sequences[str(level_num)] = [
            {"action": a, "data": d} for a, d in actions
        ]
    out = {"game_id": GAME_ID, "winning_sequences": winning_sequences}
    out_path = ROOT / "competition_knowledge_upload" / f"{GAME_ID}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Knowledge saved to {out_path}", flush=True)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    import gc
    print(f"Loading {GAME_FILE}...", flush=True)
    mod = load_mod()
    Re86 = mod.Re86

    results = {}

    for level_idx in range(NUM_LEVELS):
        level_num = level_idx + 1
        print(f"\n=== Level {level_num} ===", flush=True)

        # Step 1: probe for target positions
        target_xy, start_xy = probe_target_positions(Re86, level_idx, verbose=True)

        if target_xy is None:
            print(f"  L{level_num}: no valid target positions found", flush=True)
            gc.collect()
            continue

        print(f"  Target positions: {target_xy}", flush=True)
        print(f"  Start positions:  {start_xy}", flush=True)

        # Step 2: convert to action sequence
        actions = positions_to_actions(target_xy, start_xy)
        print(
            f"  Action sequence ({len(actions)} steps): "
            f"{[a for a, d in actions]}", flush=True
        )

        # Step 3: verify via replay
        if verify_solution(Re86, level_idx, actions, verbose=True):
            results[level_num] = actions
            save_to_db(level_num, actions)
        else:
            print(
                f"  WARNING: replay verify failed — "
                f"brush movement may not match position probe", flush=True
            )
            # Attempt: replay + check if positions match via debug
            g_dbg, _ = replay_sequence(Re86, level_idx, actions)
            dbg_brushes = g_dbg.current_level.get_sprites_by_tag("vfaeucgcyr")
            print(
                f"  Debug brush positions after replay: "
                f"{[(b.x, b.y) for b in dbg_brushes]}", flush=True
            )
            print(f"  Expected: {target_xy}", flush=True)

        gc.collect()

    print("\n=== Summary ===")
    for ln, actions in sorted(results.items()):
        print(f"  L{ln}: {len(actions)} actions — {[a for a, d in actions]}")

    if results:
        save_knowledge(results)

    print("\nDone.")


if __name__ == "__main__":
    main()
