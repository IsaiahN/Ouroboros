"""SC25 solver — direct game-specific solver with BFS and spell mechanics.

Works on any sc25 variant by reading level mechanics from the live game instance:
  - Playable spells:   game.wdsxxkugj
  - Boss sprites:      [s for s in game.all_sprites if 'edusagitv' in s.name]
  - Teleport targets:  game.small_teleport_targets / game.teleport_targets
  - Doors:             game.doors / game.second_doors
  - Exit:              [s for s in game.all_sprites if 'pcohqadae' in s.name]

Strategy (auto-detected per level):
  1. detect_level_mechanics() — catalog bosses, spells, doors, teleports
  2. For each boss (in order of how they must die):
     a. BFS navigate to fireball shot position
     b. Cast fireball → boss dies → doors removed
  3. BFS navigate to exit (pcohqadae sprite)

Size-change (fpokrvgln) and teleport (jzukcpajs) are cast when needed to
reach otherwise-inaccessible zones. The solver auto-detects when growing
is blocked and navigates to open space first.

Spell click coordinates live in _SPELL_CLICKS — all game-specific knowledge
stays in this file so primitives remain generic.
"""

import copy
from collections import deque
from typing import Optional

# Spell slot click coordinates (center of 3×3 sprite in spell UI)
_SPELL_CLICKS = {
    'aprnrzeyj': [(30, 50), (30, 55), (30, 60)],        # fireball: center col
    'fpokrvgln':  [(30, 50), (25, 55), (35, 55), (30, 60)],  # size change: diamond
    'jzukcpajs': [(25, 50), (30, 50), (30, 55)],         # teleport: top-L
}

_MOVE_TO_DIR = {1: 0, 2: 1, 3: 2, 4: 3}   # action_num → direction int (U/D/L/R)
_MOVES = [1, 2, 3, 4]  # action nums for U/D/L/R


# ---------------------------------------------------------------------------
# Low-level game interaction helpers
# ---------------------------------------------------------------------------

def _do_action(game, ActionInput_cls, action_num, data=None):
    prev_score = game._score
    inp = ActionInput_cls(id=action_num, data=data) if data else ActionInput_cls(id=action_num)
    game.perform_action(inp)
    won = game._score > prev_score
    try:
        from arcengine.enums import GameState  # noqa: PLC0415
        lost = game._state == GameState.GAME_OVER
    except Exception:
        lost = False
    return won, lost


def _any_animation_active(game):
    checks = [
        game.fireball_animation.get('active', False),
        game.auto_cast_animation.get('active', False),
        game.size_change_animation.get('active', False),
        game.teleport_animation.get('active', False),
        game.spell_slots_flash_animation.get('active', False),
        getattr(game, 'entering_exit', False),
    ]
    return any(checks)


def _advance_animation(game, ActionInput_cls, max_ticks=50):
    for _ in range(max_ticks):
        if not _any_animation_active(game):
            return 'ok'
        won, lost = _do_action(game, ActionInput_cls, 1)
        if won:
            return 'won'
        if lost:
            return 'lost'
    return 'ok'


def _cast_spell(game, ActionInput_cls, spell_name):
    """Click spell slots and advance animation. Returns 'won', 'lost', or 'ok'."""
    clicks = _SPELL_CLICKS.get(spell_name, [])
    for x, y in clicks:
        won, lost = _do_action(game, ActionInput_cls, 6, {'x': x, 'y': y})
        if won:
            return 'won'
        if lost:
            return 'lost'
    return _advance_animation(game, ActionInput_cls)


def _get_player(game):
    return getattr(game, 'cflwkfoggh', None)


def _can_hit_boss(game, ActionInput_cls, boss_name):
    """Simulate fireball from current state — return True if named boss would be hit."""
    gc = copy.deepcopy(game)
    gc.mvgdxgobhf()
    hit = gc.fireball_animation.get('hit_sprite')
    return hit is not None and hit.name == boss_name


def _can_grow(game, ActionInput_cls):
    """Return True if fpokrvgln will successfully grow the player (scale 1→2)."""
    p = _get_player(game)
    if p is None or p.scale != 1:
        return False
    # Use game's own blocked-growth check
    check_fn = getattr(game, 'gckzrsqwde', None)
    if check_fn:
        return not check_fn(p, 2)
    # Fallback: try in deepcopy
    gc = copy.deepcopy(game)
    r = _cast_spell(gc, ActionInput_cls, 'fpokrvgln')
    pp = _get_player(gc)
    return pp is not None and pp.scale == 2


# ---------------------------------------------------------------------------
# BFS helpers
# ---------------------------------------------------------------------------

def _bfs_find_fireball_shot(game, ActionInput_cls, boss_name, max_steps=30):
    """BFS navigate to find a position+direction from which fireball hits boss.

    Returns list of action_nums (1-4), or None if unreachable.
    """
    # Check from each direction at current position first
    for a in _MOVES:
        gc = copy.deepcopy(game)
        _do_action(gc, ActionInput_cls, a)
        if _can_hit_boss(gc, ActionInput_cls, boss_name):
            return [a]

    p0 = _get_player(game)
    if p0 is None:
        return None

    visited = {(p0.x, p0.y, game.player_direction)}
    queue = deque([([], copy.deepcopy(game))])

    while queue:
        nav, g = queue.popleft()
        if len(nav) >= max_steps:
            continue
        for a in _MOVES:
            gc = copy.deepcopy(g)
            won, lost = _do_action(gc, ActionInput_cls, a)
            if lost:
                continue
            p = _get_player(gc)
            k = (p.x, p.y, gc.player_direction)
            if k in visited:
                continue
            visited.add(k)
            new_nav = nav + [a]
            if _can_hit_boss(gc, ActionInput_cls, boss_name):
                return new_nav
            queue.append((new_nav, gc))

    return None


def _bfs_nav_to_position(game, ActionInput_cls, target_x, target_y, max_steps=40):
    """BFS navigate to a specific pixel position. Returns action list or None."""
    p0 = _get_player(game)
    if p0 is None:
        return None
    if p0.x == target_x and p0.y == target_y:
        return []

    visited = {(p0.x, p0.y)}
    queue = deque([([], copy.deepcopy(game))])

    while queue:
        nav, g = queue.popleft()
        if len(nav) >= max_steps:
            continue
        for a in _MOVES:
            gc = copy.deepcopy(g)
            won, lost = _do_action(gc, ActionInput_cls, a)
            if lost:
                continue
            p = _get_player(gc)
            k = (p.x, p.y)
            if k in visited:
                continue
            visited.add(k)
            if p.x == target_x and p.y == target_y:
                return nav + [a]
            queue.append((nav + [a], gc))

    return None


def _bfs_find_grow_position(game, ActionInput_cls, max_steps=20):
    """BFS to find a nearby position where fpokrvgln grow will succeed."""
    p0 = _get_player(game)
    if p0 is None:
        return None

    # Check current position
    if _can_grow(game, ActionInput_cls):
        return []

    visited = {(p0.x, p0.y)}
    queue = deque([([], copy.deepcopy(game))])

    while queue:
        nav, g = queue.popleft()
        if len(nav) >= max_steps:
            continue
        for a in _MOVES:
            gc = copy.deepcopy(g)
            won, lost = _do_action(gc, ActionInput_cls, a)
            if lost:
                continue
            p = _get_player(gc)
            k = (p.x, p.y)
            if k in visited:
                continue
            visited.add(k)
            if _can_grow(gc, ActionInput_cls):
                return nav + [a]
            queue.append((nav + [a], gc))

    return None


def _bfs_nav_to_win(game, ActionInput_cls, max_steps=60):
    """BFS using only movement to reach win condition (score increases).

    Returns action list or None.
    """
    p0 = _get_player(game)
    if p0 is None:
        return None

    visited = {(p0.x, p0.y)}
    queue = deque([([], copy.deepcopy(game))])

    while queue:
        nav, g = queue.popleft()
        if len(nav) >= max_steps:
            continue
        for a in _MOVES:
            gc = copy.deepcopy(g)
            won, lost = _do_action(gc, ActionInput_cls, a)
            if won:
                return nav + [a]
            if lost:
                continue
            p = _get_player(gc)
            if p is None:
                continue
            k = (p.x, p.y)
            if k in visited:
                continue
            visited.add(k)
            queue.append((nav + [a], gc))

    return None


# ---------------------------------------------------------------------------
# Action sequence builder
# ---------------------------------------------------------------------------

def _seq_entry(action_num, data=None):
    return {'action': action_num, 'data': data or {}}


def _nav_entries(action_list):
    return [_seq_entry(a) for a in action_list]


def _spell_entries(spell_name, include_anim=True):
    clicks = _SPELL_CLICKS.get(spell_name, [])
    entries = [_seq_entry(6, {'x': x, 'y': y}) for x, y in clicks]
    if include_anim:
        entries.append(_seq_entry(1))  # animation placeholder
    return entries


# ---------------------------------------------------------------------------
# Level mechanics detection
# ---------------------------------------------------------------------------

def _detect_bosses(game):
    """Return list of boss sprite names present in the level, in kill order."""
    bosses = []
    for s in game.all_sprites:
        if 'edusagitv' in s.name:
            bosses.append(s.name)
    # Kill edusagitv (primary) before ckmqitdgq (secondary) since ckmqitdgq
    # depends on edusagitv doors being removed first.
    bosses.sort(key=lambda n: (0 if n == 'edusagitv' else 1))
    return bosses


def _available_spells(game):
    return list(getattr(game, 'wdsxxkugj', []) or [])


def _has_spell(game, spell_name):
    return spell_name in _available_spells(game)


# ---------------------------------------------------------------------------
# Core level solver
# ---------------------------------------------------------------------------

def _solve_level(game_class, ActionInput_cls, level_idx: int,
                 verbose: bool = False) -> Optional[list]:
    """Auto-solve a single sc25 level. Returns action sequence or None."""
    try:
        game = game_class()
        game.full_reset()
        game.set_level(level_idx)
    except Exception as e:
        if verbose:
            print(f'  sc25 L{level_idx + 1}: init error: {e}', flush=True)
        return None

    p = _get_player(game)
    if p is None:
        return None

    spells = _available_spells(game)
    bosses = _detect_bosses(game)
    has_teleport = 'jzukcpajs' in spells
    has_size = 'fpokrvgln' in spells

    if verbose:
        print(f'  sc25 L{level_idx + 1}: player=({p.x},{p.y}) scale={p.scale} '
              f'budget={game.sykpecmoq} spells={spells} bosses={bosses}', flush=True)
        print(f'    small_tp: {[(s.x,s.y) for s in game.small_teleport_targets]}', flush=True)
        print(f'    large_tp: {[(s.x,s.y) for s in game.teleport_targets]}', flush=True)
        print(f'    doors: {[(s.x,s.y) for s in game.doors]}', flush=True)
        print(f'    second_doors: {[(s.x,s.y) for s in game.second_doors]}', flush=True)

    all_actions = []

    # --- Handle levels with demo animation (L1 is_first_input) ---
    if getattr(game, 'is_first_input_on_level_1', False):
        # Trigger demo with first click, then continue
        won, lost = _do_action(game, ActionInput_cls, 6, {'x': 30, 'y': 50})
        all_actions.append(_seq_entry(6, {'x': 30, 'y': 50}))
        r = _advance_animation(game, ActionInput_cls)
        all_actions.append(_seq_entry(1))
        if r == 'won':
            return all_actions
        if r == 'lost':
            return None

    # --- Strategy: for each boss, navigate + fireball ---
    for boss_name in bosses:
        if verbose:
            print(f'  sc25 L{level_idx + 1}: targeting {boss_name}', flush=True)

        # Direct fireball shot BFS — secondary bosses get a larger range
        # since they may require navigating across the full map after doors open.
        is_secondary = boss_name != 'edusagitv'
        bfs_range = (60 if is_secondary else 25) if has_teleport else (80 if is_secondary else 40)
        nav = _bfs_find_fireball_shot(game, ActionInput_cls, boss_name,
                                      max_steps=bfs_range)

        # If unreachable directly, try shrink-only first (no teleport needed)
        if nav is None and has_size:
            p_cur = _get_player(game)
            if p_cur.scale == 2:
                if verbose:
                    print(f'    direct shot failed, trying shrink', flush=True)
                # Test shrink on a deepcopy to see if it helps
                gc_shrink = copy.deepcopy(game)
                r_s = _cast_spell(gc_shrink, ActionInput_cls, 'fpokrvgln')
                if r_s != 'lost':
                    nav_s = _bfs_find_fireball_shot(gc_shrink, ActionInput_cls,
                                                    boss_name, max_steps=40)
                    if nav_s is not None or r_s == 'won':
                        # Commit shrink on live game
                        r_live = _cast_spell(game, ActionInput_cls, 'fpokrvgln')
                        all_actions.extend(_spell_entries('fpokrvgln'))
                        if r_live == 'won':
                            return all_actions
                        if r_live != 'lost':
                            nav = nav_s

        # If still unreachable, try shrink + teleport
        if nav is None and has_size and has_teleport:
            if verbose:
                print(f'    trying shrink+teleport', flush=True)

            p_cur = _get_player(game)
            if p_cur.scale == 2:
                r = _cast_spell(game, ActionInput_cls, 'fpokrvgln')
                all_actions.extend(_spell_entries('fpokrvgln'))
                if r == 'won':
                    return all_actions
                if r == 'lost':
                    return None

            r = _cast_spell(game, ActionInput_cls, 'jzukcpajs')
            all_actions.extend(_spell_entries('jzukcpajs'))
            if r == 'won':
                return all_actions
            if r == 'lost':
                return None

            nav = _bfs_find_fireball_shot(game, ActionInput_cls, boss_name, max_steps=80)

        # If still unreachable, try teleport-only (no shrink needed) then wide BFS
        if nav is None and has_teleport:
            if verbose:
                print(f'    trying teleport-only wide BFS', flush=True)
            r = _cast_spell(game, ActionInput_cls, 'jzukcpajs')
            all_actions.extend(_spell_entries('jzukcpajs'))
            if r == 'won':
                return all_actions
            if r == 'lost':
                return None
            nav = _bfs_find_fireball_shot(game, ActionInput_cls, boss_name, max_steps=80)

        # Last resort: second teleport + wide BFS
        if nav is None and has_teleport:
            if verbose:
                print(f'    trying second teleport wide BFS', flush=True)
            r = _cast_spell(game, ActionInput_cls, 'jzukcpajs')
            all_actions.extend(_spell_entries('jzukcpajs'))
            if r == 'won':
                return all_actions
            if r == 'lost':
                return None
            nav = _bfs_find_fireball_shot(game, ActionInput_cls, boss_name, max_steps=80)

        if nav is None:
            if verbose:
                print(f'    all strategies failed for {boss_name}', flush=True)
            return None

        # Execute navigation
        for a in nav:
            won, lost = _do_action(game, ActionInput_cls, a)
            all_actions.append(_seq_entry(a))
            if won:
                return all_actions
            if lost:
                return None

        if verbose:
            p2 = _get_player(game)
            print(f'    nav done: ({p2.x},{p2.y}) dir={game.player_direction}', flush=True)

        # Cast fireball
        r = _cast_spell(game, ActionInput_cls, 'aprnrzeyj')
        all_actions.extend(_spell_entries('aprnrzeyj'))
        if r == 'won':
            return all_actions
        if r == 'lost':
            return None

        if verbose:
            print(f'    fireball: doors={len(game.doors)} second_doors={len(game.second_doors)}',
                  flush=True)

    # --- All bosses dead, navigate to exit ---
    if verbose:
        p3 = _get_player(game)
        print(f'  sc25 L{level_idx + 1}: all bosses dead, player=({p3.x},{p3.y})', flush=True)

    # Try direct nav to exit
    exit_nav = _bfs_nav_to_win(game, ActionInput_cls, max_steps=50)

    if exit_nav is None and has_size:
        p_cur = _get_player(game)
        if p_cur.scale == 1:
            # Try grow to scale=2 to reach exit area
            grow_nav = _bfs_find_grow_position(game, ActionInput_cls)
            if grow_nav is not None:
                for a in grow_nav:
                    _do_action(game, ActionInput_cls, a)
                    all_actions.append(_seq_entry(a))
                r = _cast_spell(game, ActionInput_cls, 'fpokrvgln')
                all_actions.extend(_spell_entries('fpokrvgln'))
                if r == 'won':
                    return all_actions
                exit_nav = _bfs_nav_to_win(game, ActionInput_cls, max_steps=60)
        elif p_cur.scale == 2:
            # Try shrink to scale=1 — exit may only be reachable when small
            r = _cast_spell(game, ActionInput_cls, 'fpokrvgln')
            all_actions.extend(_spell_entries('fpokrvgln'))
            if r == 'won':
                return all_actions
            if r != 'lost':
                exit_nav = _bfs_nav_to_win(game, ActionInput_cls, max_steps=60)
                if exit_nav is None:
                    # Undo shrink attempt — grow back
                    r2 = _cast_spell(game, ActionInput_cls, 'fpokrvgln')
                    all_actions.extend(_spell_entries('fpokrvgln'))
                    if r2 == 'won':
                        return all_actions

    if exit_nav is None and has_teleport:
        # Try teleport to get closer to exit
        r = _cast_spell(game, ActionInput_cls, 'jzukcpajs')
        all_actions.extend(_spell_entries('jzukcpajs'))
        if r == 'won':
            return all_actions
        exit_nav = _bfs_nav_to_win(game, ActionInput_cls, max_steps=60)

    if exit_nav is None and has_teleport:
        # Second teleport attempt (cycles to next target)
        r = _cast_spell(game, ActionInput_cls, 'jzukcpajs')
        all_actions.extend(_spell_entries('jzukcpajs'))
        if r == 'won':
            return all_actions
        exit_nav = _bfs_nav_to_win(game, ActionInput_cls, max_steps=60)

    if exit_nav is None:
        if verbose:
            print(f'  sc25 L{level_idx + 1}: cannot reach exit', flush=True)
        return None

    for a in exit_nav:
        all_actions.append(_seq_entry(a))
    # Level-complete animation flush: live env needs one extra tick after the
    # player enters the exit before WIN fires; deepcopy doesn't need this tick.
    all_actions.append(_seq_entry(1))

    if verbose:
        print(f'  sc25 L{level_idx + 1}: solved, final_acts={game.actions_taken}', flush=True)

    return all_actions


# ---------------------------------------------------------------------------
# Main solver entry point
# ---------------------------------------------------------------------------

def solve_sc25(game_class, ActionInput_cls, win_levels: int,
               verbose: bool = False) -> Optional[dict]:
    """Solve all levels of an sc25-type game.

    Returns dict {level_str: [action_entry, ...]} or None on complete failure.
    """
    sequences = {}

    for level_idx in range(win_levels):
        seq = _solve_level(game_class, ActionInput_cls, level_idx, verbose)
        if seq is not None:
            sequences[str(level_idx + 1)] = seq
            if verbose:
                print(f'  sc25 L{level_idx + 1}: OK ({len(seq)} actions)', flush=True)
        else:
            if verbose:
                print(f'  sc25 L{level_idx + 1}: FAILED', flush=True)

    return sequences if sequences else None
