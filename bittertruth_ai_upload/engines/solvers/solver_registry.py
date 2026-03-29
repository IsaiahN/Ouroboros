"""Parameterized solver registry and _parameterized_solve() entry point.

Call `_parameterized_solve(env, game_id, win_levels, envs_dir, t_budget)`
from play_game().  It:

  1. Checks for a registered game-type-specific solver (ft09, sc25).
  2. Falls back to GENERIC composition: MechanicDetector → PlanComposer.
     This handles novel games the system has never seen before.
  3. Replays the resulting action sequence through the live env.
  4. Returns (score, levels_completed, actions_taken, flat_action_list) or None.

Sheet music (action sequences) is what comes OUT.
Chords (primitives) + methods (plan) are what go IN.
"""

import time
from typing import Optional

from .composer import build_plan, execute_plan
from .config import get_config
from .context import SolverContext
from .detector import MechanicDetector
from .ft09_solver import solve_ft09
from .game_loader import load_game_module
from .primitives.bfs_pathfinder import detect_player_pos, detect_step_size
from .primitives.constraint_grid import get_cell_grid
from .sc25_solver import solve_sc25

# ---------------------------------------------------------------------------
# Registry: game_type[:4] → solver callable
#
# Signature: solver(game_class, ActionInput_cls, win_levels, verbose)
#            → {level_str: [action_entry, ...]} or None
#
# Add entries here for games with well-tested specific solvers.
# All OTHER game types use the generic composition path.
# ---------------------------------------------------------------------------

_SOLVER_MAP: dict = {
    'ft09': solve_ft09,
    'sc25': solve_sc25,
}


def register_solver(game_type: str, solver_fn):
    """Register a solver callable for a game type prefix (first 4 chars)."""
    _SOLVER_MAP[game_type[:4]] = solver_fn


def get_solver(game_type: str):
    """Return registered solver callable for this game type, or None."""
    return _SOLVER_MAP.get(game_type[:4])


# ---------------------------------------------------------------------------
# Generic composition solver (handles any game type)
# ---------------------------------------------------------------------------

def _generic_solve(game_class, ActionInput_cls, game_id: str,
                   win_levels: int, verbose: bool = False) -> Optional[dict]:
    """Auto-detect mechanics and compose a plan for any game type.

    This is the 'novel game' path — no pre-registered solver required.
    Returns {level_str: [action_entry, ...]} or None.
    """
    game_type = game_id[:4]
    cfg = get_config(game_type)
    detector = MechanicDetector()
    sequences = {}

    for level_idx in range(win_levels):
        game = game_class()
        game.full_reset()
        try:
            game.set_level(level_idx)
        except Exception:
            pass

        # Detect mechanics
        avail = cfg.get('metadata', {}).get('available_actions', [1, 2, 3, 4, 6])
        mechanics = detector.detect(
            game,
            game_type=game_type,
            available_actions=avail,
            config_hints=cfg.get('hint_mechanics', []),
        )

        if verbose:
            print(f'  [generic] L{level_idx + 1} mechanics: {sorted(mechanics)}',
                  flush=True)

        # Build context
        board_cells = get_cell_grid(game) if 'constraint_grid' in mechanics else []
        palette = list(getattr(game, 'gqb', []))
        metadata = dict(cfg.get('metadata', {}))

        ctx = SolverContext(
            game=game,
            game_class=game_class,
            ActionInput_cls=ActionInput_cls,
            level_idx=level_idx,
            win_levels=win_levels,
            board_cells=board_cells,
            palette=palette,
            player_pos=detect_player_pos(game),
            step_size=detect_step_size(game, ActionInput_cls),
            metadata=metadata,
        )

        plan = build_plan(mechanics, config_order=cfg.get('solver_order', []))
        execute_plan(plan, ctx, verbose=verbose)

        if ctx.actions:
            sequences[str(level_idx + 1)] = list(ctx.actions)

    return sequences if sequences else None


# ---------------------------------------------------------------------------
# Replay helper
# ---------------------------------------------------------------------------

def _replay_via_env(env, sequences_by_level: dict, win_levels: int):
    """Replay a {level_str: [action_entry]} dict through the live env.

    Returns (score, levels_completed, actions_taken).

    Handles intermediate WIN states: some games (e.g. sc25) complete a level
    via an exit animation that may not finish until the first action of the
    next level is processed.  When WIN fires with levels_completed < win_levels,
    we restart the next level's sequence from scratch rather than returning.
    """
    try:
        from arcengine import GameAction  # noqa: PLC0415
        from arcengine.enums import GameState  # noqa: PLC0415
    except ImportError:
        return 0.0, 0, 0

    actions_taken = 0
    obs = None
    level_num = 1
    _restarts: dict = {}  # guard against infinite level restarts

    while level_num <= win_levels:
        seq = sequences_by_level.get(str(level_num), [])
        if not seq:
            break

        level_advanced = False
        for entry in seq:
            if isinstance(entry, dict):
                action_num = entry.get('action', 6)
                action_data = entry.get('data') or None
            elif isinstance(entry, int):
                action_num = entry
                action_data = None
            else:
                continue

            try:
                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION6)
                obs = env.step(action, data=action_data)
                actions_taken += 1
            except Exception:
                continue

            state = getattr(obs, 'state', None)
            if state == GameState.WIN:
                lc = getattr(obs, 'levels_completed', win_levels)
                if lc >= win_levels:
                    return lc / win_levels if win_levels > 0 else 1.0, lc, actions_taken
                # Intermediate WIN: a level finished during this loop iteration.
                # Advance level_num to lc+1 and replay that level from scratch.
                # The current action was a level-transition flush consumed by the
                # engine; the game is now at level lc+1 initial state.
                next_lv = lc + 1
                restarts = _restarts.get(next_lv, 0)
                if restarts >= 2:
                    # Safety: don't loop forever on the same level
                    return lc / win_levels if win_levels > 0 else 0.0, lc, actions_taken
                _restarts[next_lv] = restarts + 1
                level_num = next_lv
                level_advanced = True
                break
            if state == GameState.GAME_OVER:
                lc = getattr(obs, 'levels_completed', 0) or 0
                return lc / win_levels if win_levels > 0 else 0.0, lc, actions_taken

        if not level_advanced:
            level_num += 1

    lc = getattr(obs, 'levels_completed', 0) or 0 if obs else 0
    return lc / win_levels if win_levels > 0 else 0.0, lc, actions_taken


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _parameterized_solve(
    env,
    game_id: str,
    win_levels: int,
    envs_dir: Optional[str] = None,
    t_budget: float = 60.0,
    verbose: bool = False,
) -> Optional[tuple]:
    """Attempt a parameterized solve for game_id.

    Priority:
      1. Registered type-specific solver (ft09, sc25) — proven, fast.
      2. Generic composition solver (detector → composer) — any game type.

    Returns (score, levels_completed, actions_taken, flat_action_list) or None.
    """
    if envs_dir is None:
        return None

    t_start = time.time()
    game_type = game_id[:4]

    if verbose:
        print(f'[parameterized_solve] {game_id} type={game_type}', flush=True)

    # --- Load game module ---
    try:
        game_class, _module, ActionInput_cls = load_game_module(game_id, envs_dir)
    except Exception as e:
        if verbose:
            print(f'  load_game_module error: {e}', flush=True)
        return None

    if game_class is None or ActionInput_cls is None:
        return None

    if time.time() - t_start > t_budget * 0.4:
        if verbose:
            print(f'  time budget exceeded before solve', flush=True)
        return None

    # --- Choose solver path ---
    solver_fn = get_solver(game_type)

    try:
        if solver_fn is not None:
            if verbose:
                print(f'  using registered solver: {solver_fn.__name__}', flush=True)
            sequences = solver_fn(
                game_class=game_class,
                ActionInput_cls=ActionInput_cls,
                win_levels=win_levels,
                verbose=verbose,
            )
        else:
            if verbose:
                print(f'  no registered solver — using generic composition',
                      flush=True)
            sequences = _generic_solve(
                game_class=game_class,
                ActionInput_cls=ActionInput_cls,
                game_id=game_id,
                win_levels=win_levels,
                verbose=verbose,
            )
    except Exception as e:
        if verbose:
            print(f'  solver error: {e}', flush=True)
            import traceback
            traceback.print_exc()
        return None

    if not sequences:
        if verbose:
            print(f'  solver returned no sequences', flush=True)
        return None

    if verbose:
        elapsed = time.time() - t_start
        print(f'  solver done in {elapsed:.1f}s — levels: {sorted(sequences.keys())}',
              flush=True)

    # --- Replay through live env ---
    try:
        score, levels_completed, actions_taken = _replay_via_env(
            env, sequences, win_levels
        )
    except Exception as e:
        if verbose:
            print(f'  replay error: {e}', flush=True)
        return None

    if verbose:
        print(f'  result: score={score:.3f} levels={levels_completed}/{win_levels} '
              f'acts={actions_taken}', flush=True)

    # Flat action list for knowledge storage
    flat_seq = []
    for lvl in range(1, win_levels + 1):
        for entry in sequences.get(str(lvl), []):
            if isinstance(entry, dict):
                flat_seq.append(entry.get('action', 1))
            elif isinstance(entry, int):
                flat_seq.append(entry)

    return score, levels_completed, actions_taken, flat_seq
