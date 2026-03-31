"""
Win Condition Classifier + Analytical Solvers (H60)

Goal-first reasoning pipeline:
  classify win condition type → estimate state space → run type-specific solver

Instead of: actions → state transitions → (maybe) win
We do:      win_condition → enumerate valid final states → plan path to one

Win types:
  pixel_composition  - Brushes stamped onto canvas must match target (RE86)
  constraint_sat     - Toggle cells to satisfy boolean constraints (FT09)
  flow_spill         - Fluid source must reach target via spill (SP80)
  position_match     - Objects must reach target positions (AR25, VC33)
  sequence_collect   - Collect targets in correct config/order (SK48, LS20)
  path_clear         - Navigate/clear path between endpoints (DC22, WA30)
  unknown            - Fall back to MCTS

For each type, the analytical solver works backwards from the win condition:
  1. What are the free variables?
  2. What is the combinatorial size?
  3. Can we enumerate and directly test all valid final states?
  4. Once the final state is found, what action sequence reaches it?
"""

import itertools
import time
from collections import deque

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

WIN_PIXEL_COMPOSITION = "pixel_composition"
WIN_CONSTRAINT_SAT    = "constraint_sat"
WIN_FLOW_SPILL        = "flow_spill"
WIN_POSITION_MATCH    = "position_match"
WIN_SEQUENCE_COLLECT  = "sequence_collect"
WIN_PATH_CLEAR        = "path_clear"
WIN_UNKNOWN           = "unknown"

# Feasibility thresholds
MAX_DIRECT_COMBOS = 5_000_000   # brute-force enumeration ceiling
MAX_CONSTRAINT_BITS = 18        # 2^18 = 262K — max for bitmask SAT search


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_level(game):
    """Return current level object from game, or None."""
    level = getattr(game, "current_level", None)
    if level is not None:
        return level
    try:
        li = getattr(game, "_current_level_index", 0) or 0
        levels = getattr(game, "_levels", None)
        if levels and 0 <= li < len(levels):
            return levels[li]
    except Exception:
        pass
    return None


def _get_sprites(game, tag):
    """Return sprites with given tag from game's current level."""
    level = _get_level(game)
    if level is None:
        return []
    try:
        result = level.get_sprites_by_tag(tag)
        return result if result else []
    except Exception:
        return []


def _has_method(game, name):
    return callable(getattr(game, name, None))


# ─────────────────────────────────────────────
# CLASSIFIER
# ─────────────────────────────────────────────

def classify_win_condition(game):
    """
    Classify win condition type from a game object.

    Inspection priority:
      1. Specific win-check method presence (strongest signal)
      2. Sprite tag patterns (corroborating evidence)
      3. Available-action count heuristics

    Returns one of the WIN_* constants.
    """
    if game is None:
        return WIN_UNKNOWN

    # ── Pixel composition (RE86-style) ─────────────────────────
    # cdjxpfqest() composites brush sprites onto canvas and checks pixel match
    if _has_method(game, "cdjxpfqest") and _get_sprites(game, "vfaeucgcyr"):
        return WIN_PIXEL_COMPOSITION

    # ── Constraint satisfaction (FT09-style) ───────────────────
    # gvtmoopqgy() checks that all constraint cells are satisfied
    if _has_method(game, "gvtmoopqgy"):
        return WIN_CONSTRAINT_SAT

    # ── Flow / spill (SP80-style) ───────────────────────────────
    # Fluid source must flow to target; ACTION5 triggers spill
    if _get_sprites(game, "syaipsfndp"):
        return WIN_FLOW_SPILL

    # ── Sequence / collect (SK48 / LS20-style) ─────────────────
    # Collect color-coded targets in the correct configuration
    if _get_sprites(game, "elmjchdqcn") or _get_sprites(game, "vbelzuaian"):
        return WIN_SEQUENCE_COLLECT

    # ── Position match (AR25 / VC33-style) ─────────────────────
    # Objects must reach specific target positions
    if _get_sprites(game, "mldlhgjtqi"):
        return WIN_POSITION_MATCH

    return WIN_UNKNOWN


# ─────────────────────────────────────────────
# STATE SPACE ESTIMATOR
# ─────────────────────────────────────────────

def estimate_state_space(game, win_type):
    """
    Estimate the combinatorial size of the search space.

    Returns dict:
      type                  – WIN_* constant
      n_objects             – number of free objects
      total_combinations    – estimated total states to enumerate
      direct_feasible       – True if brute-force enumeration is feasible
      strategy_note         – human-readable explanation
    """
    if win_type == WIN_PIXEL_COMPOSITION:
        brushes = _get_sprites(game, "vfaeucgcyr")
        n = len(brushes) if brushes else 2
        step = 3
        pos_per_axis = len(range(0, 64, step))   # 22
        total = pos_per_axis ** (2 * n)
        return {
            "type": win_type,
            "n_objects": n,
            "positions_per_axis": pos_per_axis,
            "total_combinations": total,
            "direct_feasible": total <= MAX_DIRECT_COMBOS,
            "strategy_note": (
                f"{n} brushes × {pos_per_axis}² positions = {total:,} combos"
            ),
        }

    if win_type == WIN_CONSTRAINT_SAT:
        # Estimate from grid size; FT09 has 6 cells per row
        level = _get_level(game)
        grid_w = 6
        if level is not None:
            gs = getattr(level, "grid_size", None)
            if gs:
                grid_w = gs[0]
        n_cells = grid_w * grid_w
        n_bits = min(n_cells, MAX_CONSTRAINT_BITS)
        total = 2 ** n_bits
        return {
            "type": win_type,
            "n_objects": n_cells,
            "total_combinations": total,
            "direct_feasible": n_bits <= MAX_CONSTRAINT_BITS,
            "strategy_note": f"2^{n_bits} = {total:,} click-subsets",
        }

    if win_type == WIN_FLOW_SPILL:
        # BFS over piece positions; similar to pixel_composition
        # SP80 grid is 16×16, pieces moveable in 4 directions
        return {
            "type": win_type,
            "n_objects": -1,
            "total_combinations": -1,
            "direct_feasible": True,   # handled by targeted BFS, not brute-force
            "strategy_note": "BFS with spill-check at each state",
        }

    if win_type == WIN_POSITION_MATCH:
        # Pieces must reach target positions; use BFS with direct win-check
        return {
            "type": win_type,
            "n_objects": -1,
            "total_combinations": -1,
            "direct_feasible": True,
            "strategy_note": "BFS with position win-check",
        }

    return {
        "type": win_type,
        "n_objects": -1,
        "total_combinations": -1,
        "direct_feasible": False,
        "strategy_note": "unknown — fall back to MCTS",
    }


# ─────────────────────────────────────────────
# ANALYTICAL SOLVERS
# ─────────────────────────────────────────────

def solve_pixel_composition(cls, level_idx, make_game_fn, verbose=False):
    """
    Analytical solver for pixel_composition games (RE86).

    Steps:
      1. Probe all position combos by directly setting brush .x/.y
      2. Call cdjxpfqest() — O(1) check, no replay needed
      3. On match: convert target positions to directional action sequence

    Complexity: 22^(2n) — for 2 brushes = 234K checks ≈ 0.2s
    Returns list of (action_num, data_dict) or None.
    """
    g_probe = make_game_fn(cls, level_idx)
    brushes = _get_sprites(g_probe, "vfaeucgcyr")
    if not brushes:
        return None

    n = len(brushes)
    step = 3
    start_xy = [(b.x, b.y) for b in brushes]

    def _reachable(start_coord, size, step):
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

    brush_xr = [_reachable(b.x, b.width, step) for b in brushes]
    brush_yr = [_reachable(b.y, b.height, step) for b in brushes]
    total = 1
    for xr, yr in zip(brush_xr, brush_yr):
        total *= len(xr) * len(yr)

    if verbose:
        print(
            f"    [pixel_composition] {n} brushes, "
            f"{total:,} reachable combos", flush=True
        )

    target_xy = None

    if n == 1:
        b = brushes[0]
        for x in brush_xr[0]:
            for y in brush_yr[0]:
                b.set_position(x, y)
                if g_probe.cdjxpfqest():
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
                        if g_probe.cdjxpfqest():
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
        found = False
        for combo in itertools.product(*pos_ranges):
            for i, (x, y) in enumerate(combo):
                brushes[i].set_position(x, y)
            if g_probe.cdjxpfqest():
                target_xy = list(combo)
                found = True
                break

    if target_xy is None:
        if verbose:
            print("    [pixel_composition] No valid position found", flush=True)
        return None

    if verbose:
        print(f"    [pixel_composition] Target positions: {target_xy}", flush=True)

    # Build action sequence: move each brush from start to target
    # Actions: 1=up(y−), 2=down(y+), 3=left(x−), 4=right(x+), 5=cycle brush
    actions = []
    for brush_idx, (tx, ty) in enumerate(target_xy):
        sx, sy = start_xy[brush_idx]
        if brush_idx > 0:
            actions.append((5, {}))   # cycle to next brush
        dx = tx - sx
        dy = ty - sy
        # Horizontal
        if dx > 0:
            actions.extend([(4, {})] * (dx // step))
        elif dx < 0:
            actions.extend([(3, {})] * ((-dx) // step))
        # Vertical
        if dy > 0:
            actions.extend([(2, {})] * (dy // step))
        elif dy < 0:
            actions.extend([(1, {})] * ((-dy) // step))

    return actions


def solve_constraint_sat(cls, level_idx, make_game_fn, verbose=False):
    """
    Analytical solver for constraint satisfaction games (FT09-style).

    Strategy: enumerate click subsets ordered by size (shortest solution first).
    For FT09: ACTION6 = click with (x, y) data on a 6×6 grid.

    Click positions are discovered by probing the grid; positions that cause
    no state change are pruned from the search space.

    Returns list of (action_num, data_dict) or None.
    """
    try:
        from arcengine import ActionInput, GameAction
    except ImportError:
        return None

    g0 = make_game_fn(cls, level_idx)
    level = _get_level(g0)
    if level is None:
        return None

    grid_w = getattr(level, "grid_size", (6, 6))[0]
    scale = max(1, 64 // grid_w)

    # Build click grid — centre of each cell
    click_grid = []
    for gy in range(grid_w):
        for gx in range(grid_w):
            cx = gx * scale + scale // 2
            cy = gy * scale + scale // 2
            click_grid.append({"x": cx, "y": cy})

    # Prune: only keep positions that change game state when clicked
    def _state_hash(g):
        try:
            li = g._current_level_index
            lvl = g._levels[li]
            sprites = getattr(lvl, "_sprites", []) or []
            parts = []
            for s in sprites:
                if s is not None and hasattr(s, "x") and hasattr(s, "y"):
                    col = None
                    if hasattr(s, "pixels"):
                        try:
                            col = int(s.pixels[s.height // 2, s.width // 2])
                        except Exception:
                            pass
                    parts.append((int(s.x), int(s.y), col))
            return tuple(sorted(parts))
        except Exception:
            return None

    init_hash = _state_hash(g0)
    active_positions = []
    for cd in click_grid:
        g_try = make_game_fn(cls, level_idx)
        ai = ActionInput(id=GameAction.ACTION6, data=cd)
        try:
            g_try.perform_action(ai)
        except Exception:
            continue
        if _state_hash(g_try) != init_hash:
            active_positions.append(cd)

    n = len(active_positions)
    if verbose:
        print(
            f"    [constraint_sat] {n} active click positions "
            f"(pruned from {len(click_grid)})", flush=True
        )

    if n == 0 or n > MAX_CONSTRAINT_BITS:
        return None

    # Enumerate subsets by size (BFS over click-sequences)
    for r in range(1, min(n + 1, n + 1)):
        for combo in itertools.combinations(range(n), r):
            actions = [(6, active_positions[i]) for i in combo]
            g_try = make_game_fn(cls, level_idx)
            won = False
            for act_num, act_data in actions:
                ai = ActionInput(id=GameAction.ACTION6, data=act_data)
                prev_li = g_try._current_level_index
                try:
                    g_try.perform_action(ai)
                except Exception:
                    break
                if g_try._current_level_index > prev_li:
                    won = True
                    break
            if won:
                if verbose:
                    print(
                        f"    [constraint_sat] Solved: {len(actions)} clicks", flush=True
                    )
                return actions
    return None


# ─────────────────────────────────────────────
# UNIFIED ENTRY POINT
# ─────────────────────────────────────────────

def analytical_solve(cls, level_idx, make_game_fn, verbose=False, t_budget=30.0):
    """
    Goal-first analytical solver for a single level.

    Workflow:
      1. Create probe game and classify win condition
      2. Estimate state space feasibility
      3. Run appropriate analytical solver
      4. Return (action_sequence, win_type) or (None, win_type)

    action_sequence is a list of (action_num: int, data: dict) tuples.
    """
    t0 = time.time()

    try:
        game = make_game_fn(cls, level_idx)
    except Exception as e:
        if verbose:
            print(f"    [analytical_solve] make_game failed: {e}", flush=True)
        return None, WIN_UNKNOWN

    win_type = classify_win_condition(game)
    space = estimate_state_space(game, win_type)

    if verbose:
        print(f"    [analytical_solve] type={win_type}  {space['strategy_note']}", flush=True)

    if not space.get("direct_feasible", False):
        if verbose:
            print("    [analytical_solve] Not directly feasible, skipping", flush=True)
        return None, win_type

    if time.time() - t0 > t_budget:
        return None, win_type

    if win_type == WIN_PIXEL_COMPOSITION:
        seq = solve_pixel_composition(cls, level_idx, make_game_fn, verbose=verbose)
        return seq, win_type

    if win_type == WIN_CONSTRAINT_SAT:
        seq = solve_constraint_sat(cls, level_idx, make_game_fn, verbose=verbose)
        return seq, win_type

    return None, win_type


def analytical_solve_all_levels(cls, num_levels, make_game_fn,
                                verbose=False, t_budget=120.0):
    """
    Run analytical_solve for all levels.
    Returns {level_num: action_sequence} for solved levels.
    """
    t0 = time.time()
    results = {}

    for level_idx in range(num_levels):
        remaining = t_budget - (time.time() - t0)
        if remaining < 1.0:
            break
        level_num = level_idx + 1
        if verbose:
            print(f"  [analytical_solve] Level {level_num}...", flush=True)

        per_level_budget = min(remaining * 0.5, 30.0)
        seq, win_type = analytical_solve(
            cls, level_idx, make_game_fn,
            verbose=verbose, t_budget=per_level_budget
        )
        if seq is not None:
            if verbose:
                print(
                    f"  [analytical_solve] L{level_num} SOLVED ({len(seq)} actions)", flush=True
                )
            results[level_num] = seq

    return results
