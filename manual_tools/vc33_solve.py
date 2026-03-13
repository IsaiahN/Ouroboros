"""VC33 Rail Puzzle Solver.

BFS search over switch/rail click sequences to solve each level.
A* search with correctly-placed heuristic for harder levels.
Uses Level.clone() for state management — set_level() does NOT reset sprite positions.

Usage:
    python manual_tools/vc33_solve.py              # just compute and verify
    python manual_tools/vc33_solve.py --insert-db   # also insert into winning_sequences
    python manual_tools/vc33_solve.py --level=7     # solve specific level only
"""
import heapq
import json
import os
import sqlite3
import sys
import uuid
from collections import deque
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'environment_files', 'vc33', '9851e02b'))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import numpy as np
from arcengine import ActionInput, GameAction
from vc33 import Vc33, levels


def get_state_hash(game):
    """Hash relevant game state for BFS deduplication.

    Captures people (HQB) and rail (rDn) positions and sizes.
    """
    parts = []
    for tag in ('HQB', 'rDn'):
        sprites = sorted(
            game.current_level.get_sprites_by_tag(tag),
            key=lambda s: (s.name, s.x, s.y),
        )
        for s in sprites:
            parts.append((tag, s.name, s.x, s.y,
                          s.pixels.shape[0], s.pixels.shape[1]))
    return tuple(parts)


def save_base_state(game, n_base):
    """Save positions and pixel arrays of base sprites (not rlV indicators)."""
    sprites = game.current_level.get_sprites()
    return [
        (s.x, s.y, s.pixels.tobytes(), s.pixels.shape, s.pixels.dtype)
        for s in sprites[:n_base]
    ]


def restore_from_pristine(game, level_idx, pristine, saved, n_base):
    """Clone from pristine level and overlay saved sprite state."""
    game._levels[level_idx] = pristine.clone()
    game.set_level(level_idx)
    sprites = game.current_level.get_sprites()
    for i in range(min(len(saved), n_base)):
        x, y, pix_bytes, shape, dtype = saved[i]
        sprites[i].set_position(x, y)
        if shape[0] > 0 and shape[1] > 0:
            sprites[i].pixels = np.frombuffer(
                pix_bytes, dtype=dtype
            ).reshape(shape).copy()
        else:
            sprites[i].pixels = np.zeros(shape, dtype=dtype)
    game.on_set_level(game.current_level)


def apply_click(game, act_idx, switches, zhks):
    """Apply a click action (ZGd switch or zHk rail mover).

    Returns True if the action was successfully applied.
    """
    n_sw = len(switches)
    if act_idx < n_sw:
        game.ccl(switches[act_idx])
        return True
    z = zhks[act_idx - n_sw]
    if game.krt(z):
        anim = game.teu(z)
        # Teleport all sprites to final positions (skip frame-by-frame animation)
        for step in anim.lph:
            step.cab.set_position(*step.shl)
        game.jcy()
        return True
    return False


def solve_level(game, level_idx, max_depth=None, max_states=100000):
    """BFS to find switch click sequence that wins the level.

    Returns (solution_indices, explored_count) or (None, explored_count).
    solution_indices maps to combined [switches..., zhks...] list.
    """
    game.set_level(level_idx)
    pristine = game._levels[level_idx].clone()
    n_base = len(game.current_level.get_sprites())

    # Reset from pristine
    initial_state = save_base_state(game, n_base)
    restore_from_pristine(game, level_idx, pristine, initial_state, n_base)

    switches = game.current_level.get_sprites_by_tag("ZGd")
    zhks = game.current_level.get_sprites_by_tag("zHk")
    n_sw = len(switches)
    n_zhk = len(zhks)
    n_actions = n_sw + n_zhk
    timer = game.current_level.get_data("RoA")

    if max_depth is None:
        max_depth = timer

    print(f"  {n_sw} ZGd + {n_zhk} zHk = {n_actions} actions, "
          f"timer={timer}, max_depth={max_depth}")

    if game.gug():
        return [], 0

    initial_hash = get_state_hash(game)
    visited = {initial_hash}
    queue = deque([([], initial_state)])
    explored = 0

    while queue:
        seq, parent_state = queue.popleft()
        explored += 1

        if len(seq) >= max_depth:
            continue

        if explored > max_states:
            print(f"    max_states ({max_states}) reached, stopping")
            break

        for act in range(n_actions):
            restore_from_pristine(game, level_idx, pristine,
                                  parent_state, n_base)
            switches = game.current_level.get_sprites_by_tag("ZGd")
            zhks = game.current_level.get_sprites_by_tag("zHk")

            success = apply_click(game, act, switches, zhks)
            if not success:
                continue

            if game.gug():
                print(f"  SOLVED! {len(seq)+1} clicks, explored {explored}")
                return seq + [act], explored

            state_hash = get_state_hash(game)
            if state_hash not in visited:
                visited.add(state_hash)
                child_state = save_base_state(game, n_base)
                queue.append((seq + [act], child_state))

        if explored % 2000 == 0:
            print(f"    explored {explored}, depth {len(seq)}, "
                  f"queue {len(queue)}, visited {len(visited)}")

    print(f"  NOT SOLVED (explored {explored}, visited {len(visited)})")
    return None, explored


def count_correctly_placed(game):
    """Count people in their correct target position (for A* heuristic).

    Mirrors gug() logic but counts matches instead of all-or-nothing.
    """
    people = game.current_level.get_sprites_by_tag("HQB")
    markers = game.current_level.get_sprites_by_tag("fZK")
    rails = game.current_level.get_sprites_by_tag("rDn")
    count = 0
    for person in people:
        person_color = person.pixels[-1, -1]
        for rail in rails:
            if game.gdu(person, rail):
                adj_slots = game.suo(rail)
                if not adj_slots:
                    break
                for marker in markers:
                    if (person_color == marker.pixels[-1, -1]
                            and game.ebl(person) == game.ebl(marker)):
                        count += 1
                        break
                break
    return count


def compute_distance_heuristic(game):
    """Sum of cross-axis distances from each person to their target marker.

    Returns 0 when all people are at their target positions.
    Fine-grained: decreases as people move closer to targets.
    """
    people = game.current_level.get_sprites_by_tag("HQB")
    markers = game.current_level.get_sprites_by_tag("fZK")
    total_dist = 0
    for person in people:
        person_color = person.pixels[-1, -1]
        for marker in markers:
            if person_color == marker.pixels[-1, -1]:
                total_dist += abs(game.ebl(person) - game.ebl(marker))
                break
    return total_dist


def solve_level_astar(game, level_idx, max_depth=None, max_states=500000):
    """Greedy best-first search with distance heuristic for harder levels.

    Uses h(n) = sum of cross-axis distances from people to targets.
    Greedy: priority = h(n) only (not g+h), with g as tiebreaker.
    Finds a solution fast but not necessarily shortest.
    """
    game.set_level(level_idx)
    pristine = game._levels[level_idx].clone()
    n_base = len(game.current_level.get_sprites())

    initial_state = save_base_state(game, n_base)
    restore_from_pristine(game, level_idx, pristine, initial_state, n_base)

    switches = game.current_level.get_sprites_by_tag("ZGd")
    zhks = game.current_level.get_sprites_by_tag("zHk")
    n_sw = len(switches)
    n_zhk = len(zhks)
    n_actions = n_sw + n_zhk
    timer = game.current_level.get_data("RoA")

    if max_depth is None:
        max_depth = timer

    print(f"  {n_sw} ZGd + {n_zhk} zHk = {n_actions} actions, "
          f"timer={timer}, max_depth={max_depth} [greedy best-first]")

    if game.gug():
        return [], 0

    initial_hash = get_state_hash(game)
    initial_h = compute_distance_heuristic(game)
    print(f"  Initial distance: {initial_h} "
          f"(sum of cross-axis distances to targets)")

    visited = {initial_hash}
    counter = 0
    # Greedy: priority = (h, g, counter) — pursue lowest distance first
    heap = [(initial_h, 0, counter, [], initial_state)]
    explored = 0
    best_h_seen = initial_h

    while heap:
        h_score, g, _, seq, parent_state = heapq.heappop(heap)
        explored += 1

        if g >= max_depth:
            continue

        if explored > max_states:
            print(f"    max_states ({max_states}) reached, stopping")
            break

        for act in range(n_actions):
            restore_from_pristine(game, level_idx, pristine,
                                  parent_state, n_base)
            switches = game.current_level.get_sprites_by_tag("ZGd")
            zhks = game.current_level.get_sprites_by_tag("zHk")

            success = apply_click(game, act, switches, zhks)
            if not success:
                continue

            if game.gug():
                print(f"  SOLVED! {g + 1} clicks, explored {explored}")
                return seq + [act], explored

            state_hash = get_state_hash(game)
            if state_hash not in visited:
                visited.add(state_hash)
                child_state = save_base_state(game, n_base)
                h = compute_distance_heuristic(game)
                if h < best_h_seen:
                    best_h_seen = h
                    placed = count_correctly_placed(game)
                    print(f"    NEW BEST dist={h} (placed={placed}) "
                          f"at depth {g + 1}, "
                          f"explored {explored}, visited {len(visited)}")
                counter += 1
                heapq.heappush(
                    heap, (h, g + 1, counter, seq + [act], child_state))

        if explored % 2000 == 0:
            print(f"    explored {explored}, depth={g}, h={h_score}, "
                  f"heap {len(heap)}, visited {len(visited)}")

    print(f"  NOT SOLVED (explored {explored}, visited {len(visited)}, "
          f"best_dist={best_h_seen})")
    return None, explored


def grid_to_display(game, gx, gy):
    """Convert grid coordinates to display coordinates."""
    cam = game.camera
    scale = min(64 // cam.width, 64 // cam.height)
    x_pad = (64 - cam.width * scale) // 2
    y_pad = (64 - cam.height * scale) // 2
    dx = (gx - cam.x) * scale + x_pad
    dy = (gy - cam.y) * scale + y_pad
    return dx, dy


def build_action_sequence(game, level_idx, solution_indices, pristine):
    """Convert solution indices to winning_sequences action format.

    Returns list of {"action": 6, "data": {"x": int, "y": int}} dicts.
    """
    # Reset to pristine to get correct switch/zhk positions
    game._levels[level_idx] = pristine.clone()
    game.set_level(level_idx)
    game.on_set_level(game.current_level)

    switches = game.current_level.get_sprites_by_tag("ZGd")
    zhks = game.current_level.get_sprites_by_tag("zHk")
    n_sw = len(switches)

    actions = []
    for act_idx in solution_indices:
        if act_idx < n_sw:
            sprite = switches[act_idx]
        else:
            sprite = zhks[act_idx - n_sw]

        # Target center of sprite
        gx = sprite.x + sprite.width // 2
        gy = sprite.y + sprite.height // 2
        dx, dy = grid_to_display(game, gx, gy)

        actions.append({"action": 6, "data": {"x": int(dx), "y": int(dy)}})

        # Apply click to advance state (positions may change for zHk)
        apply_click(game, act_idx, switches, zhks)
        # Re-get sprites after state change
        switches = game.current_level.get_sprites_by_tag("ZGd")
        zhks = game.current_level.get_sprites_by_tag("zHk")

    return actions


def verify_solution(game, level_idx, solution_indices, pristine):
    """Verify a solution by replaying it through the game."""
    n_base = len(pristine.clone().get_sprites())
    initial_state = save_base_state(game, n_base)
    restore_from_pristine(game, level_idx, pristine, initial_state, n_base)

    # Re-reset from actual pristine
    game._levels[level_idx] = pristine.clone()
    game.set_level(level_idx)
    game.on_set_level(game.current_level)

    switches = game.current_level.get_sprites_by_tag("ZGd")
    zhks = game.current_level.get_sprites_by_tag("zHk")

    for act_idx in solution_indices:
        success = apply_click(game, act_idx, switches, zhks)
        if not success:
            return False
        switches = game.current_level.get_sprites_by_tag("ZGd")
        zhks = game.current_level.get_sprites_by_tag("zHk")

    return game.gug()


def play_and_capture(game, level_idx, action_sequence, pristine):
    """Play solution through game API, capturing frames for DB."""
    game._levels[level_idx] = pristine.clone()
    game.set_level(level_idx)
    game.on_set_level(game.current_level)

    frames = []
    for act_data in action_sequence:
        action = GameAction(6, act_data["data"])
        obs = game.perform_action(ActionInput(action))
        frames.append(obs.frame[-1] if len(obs.frame) > 0 else None)

    return frames


def insert_winning_sequences(db_path, solutions_by_level, pristines, game):
    """Insert computed solutions into winning_sequences table.

    Matches FT09 solver INSERT format exactly (ft09_solve.py).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    inserted = 0
    cumulative_actions = []
    level_breakpoints = {}
    total_score = 0.0

    for level_idx in sorted(solutions_by_level.keys()):
        sol_indices = solutions_by_level[level_idx]
        level_num = level_idx + 1
        pristine = pristines[level_idx]

        seq = build_action_sequence(game, level_idx, sol_indices, pristine)
        start_idx = len(cumulative_actions)
        cumulative_actions.extend(seq)
        level_breakpoints[str(level_num)] = {
            'start': start_idx,
            'end': len(cumulative_actions) - 1,
            'actions': len(seq),
        }
        total_score += 1.0

        efficiency = 1.0 / max(len(seq), 1)
        seq_id = f"seq_solver_{uuid.uuid4().hex[:8]}"

        cursor.execute("""
            INSERT INTO winning_sequences
            (sequence_id, game_id, level_number, agent_id, session_id,
             discovered_at, action_sequence, total_actions, total_score,
             efficiency_score, initial_frame, final_frame, game_type,
             generation_discovered, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seq_id, 'vc33-9851e02b', level_num, 'solver', 'solver-session',
            now, json.dumps(seq), len(seq), float(level_num),
            efficiency, '[]', '[]', 'vc33',
            0, 'vc33_solver',
        ))
        inserted += 1
        print(f"  Inserted L{level_num}: {seq_id} "
              f"({len(seq)} actions, eff={efficiency:.4f})")

    # Insert uber sequence (all levels combined)
    uber_id = f"seq_solver_uber_{uuid.uuid4().hex[:8]}"
    cursor.execute("""
        INSERT INTO winning_sequences
        (sequence_id, game_id, level_number, agent_id, session_id,
         discovered_at, action_sequence, total_actions, total_score,
         efficiency_score, initial_frame, final_frame, game_type,
         generation_discovered, is_uber_sequence, level_breakpoints,
         source_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uber_id, 'vc33-9851e02b', 0, 'solver', 'solver-session',
        now, json.dumps(cumulative_actions), len(cumulative_actions),
        total_score,
        1.0 / max(len(cumulative_actions), 1),
        '[]', '[]', 'vc33',
        0, True, json.dumps(level_breakpoints), 'vc33_solver',
    ))
    inserted += 1
    print(f"  Inserted uber: {uber_id} "
          f"({len(cumulative_actions)} actions, {total_score:.0f} levels)")

    conn.commit()
    conn.close()
    print(f"\n  Total inserted: {inserted} level sequences + 1 uber")


def main():
    import time

    game = Vc33()
    insert_db = '--insert-db' in sys.argv

    # Parse --level=N flag for single-level solving
    target_level = None
    for arg in sys.argv:
        if arg.startswith('--level='):
            target_level = int(arg.split('=')[1])

    # Parse --astar flag to force A* search
    use_astar = '--astar' in sys.argv

    # Parse --max-states=N
    max_states_override = None
    for arg in sys.argv:
        if arg.startswith('--max-states='):
            max_states_override = int(arg.split('=')[1])

    solutions_by_level = {}
    pristines = {}
    total_clicks = 0

    level_range = range(len(levels))
    if target_level is not None:
        level_range = [target_level - 1]  # Convert 1-indexed to 0-indexed

    for level_idx in level_range:
        level_num = level_idx + 1
        print(f"\nLevel {level_num}:")
        t0 = time.time()

        # Save pristine level before any modifications
        game.set_level(level_idx)
        pristines[level_idx] = game._levels[level_idx].clone()

        timer = game.current_level.get_data("RoA")
        n_actions = (len(game.current_level.get_sprites_by_tag("ZGd"))
                     + len(game.current_level.get_sprites_by_tag("zHk")))
        max_states = max_states_override or 200000

        # Use A* for levels with many actions (hard levels) or if forced
        if use_astar or n_actions >= 10:
            max_depth = min(timer, 100)
            solution, explored = solve_level_astar(
                game, level_idx,
                max_depth=max_depth,
                max_states=max_states,
            )
        else:
            solution, explored = solve_level(
                game, level_idx,
                max_depth=min(timer, 50),
                max_states=max_states,
            )

        elapsed = time.time() - t0

        if solution is not None:
            # Verify
            ok = verify_solution(game, level_idx, solution, pristines[level_idx])
            status = "PASS" if ok else "FAIL"
            print(f"  Verification: {status}")
            print(f"  Solution ({len(solution)} clicks): {solution}")
            print(f"  Time: {elapsed:.1f}s")

            if ok:
                solutions_by_level[level_idx] = solution
                total_clicks += len(solution)
        else:
            print(f"  Time: {elapsed:.1f}s")

    print(f"\n{'='*60}")
    print(f"Solved {len(solutions_by_level)}/{len(level_range)} levels, "
          f"{total_clicks} total clicks")

    if insert_db and solutions_by_level:
        db_path = os.path.join(project_root, 'core_data.db')
        print(f"\nInserting into {db_path}...")
        insert_winning_sequences(db_path, solutions_by_level, pristines, game)

    return solutions_by_level


if __name__ == '__main__':
    main()
