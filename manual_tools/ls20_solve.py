"""LS20 Maze Puzzle Solver.

BFS over (x, y, shape, color, rotation, visited_targets) state space.
Movement is 5px steps with wall collision. Config changers cycle on walk-over.
Targets must be visited with matching config.

Usage:
    python manual_tools/ls20_solve.py              # solve and verify all levels
    python manual_tools/ls20_solve.py --insert-db   # also insert into winning_sequences
    python manual_tools/ls20_solve.py --level=1     # solve specific level only
"""
import json
import os
import sqlite3
import sys
import uuid
from collections import deque
from datetime import datetime

# Add game directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
game_dir = os.path.join(project_root, 'environment_files', 'ls20', 'cb3b57cc')
sys.path.insert(0, game_dir)

import ls20  # noqa: E402
from arcengine import ActionInput, GameAction  # noqa: E402

ACTIONS = {1: (0, -5), 2: (0, 5), 3: (-5, 0), 4: (5, 0)}
ACTION_NAMES = {1: 'UP', 2: 'DOWN', 3: 'LEFT', 4: 'RIGHT'}


def extract_level_info(game, level_idx):
    """Extract maze layout and puzzle info for a level."""
    game.set_level(level_idx)

    agent_pos = (game.mgu.x, game.mgu.y)
    initial_config = (game.snw, game.tmx, game.tuv)

    # Walls
    walls = set()
    for w in game.current_level.get_sprites_by_tag('jdd'):
        walls.add((w.x, w.y))

    # Config changers: (x, y) -> type
    changers = {}
    for s in game.current_level.get_sprites_by_tag('gsu'):
        changers[(s.x, s.y)] = 'shape'
    for s in game.current_level.get_sprites_by_tag('gic'):
        changers[(s.x, s.y)] = 'color'
    for s in game.current_level.get_sprites_by_tag('bgt'):
        changers[(s.x, s.y)] = 'rotation'

    # Targets: list of (x, y, shape, color, rot)
    targets = []
    for i in range(len(game.qqv)):
        targets.append((
            game.qqv[i].x, game.qqv[i].y,
            game.gfy[i], game.vxy[i], game.cjl[i],
        ))

    # Collectible items: (x, y) list
    items = []
    for s in game.current_level.get_sprites_by_tag('iri'):
        items.append((s.x, s.y))

    # Fuel (from level's "vxy" data)
    max_fuel = game.current_level.get_data('vxy') or 42

    return {
        'agent_pos': agent_pos,
        'initial_config': initial_config,
        'walls': walls,
        'changers': changers,
        'targets': targets,
        'items': items,
        'max_fuel': max_fuel,
    }


def solve_level(game, level_idx):
    """BFS over full state space with fuel tracking.

    State: (x, y, shape, color, rot, visited_targets, collected_items, fuel)
    Fuel decrements each step unless an item is collected (refuels to max).
    If fuel reaches 0, the agent dies — that state is pruned.
    """
    info = extract_level_info(game, level_idx)

    agent_pos = info['agent_pos']
    s0, c0, r0 = info['initial_config']
    walls = info['walls']
    changers = info['changers']
    targets = info['targets']
    items = info['items']
    max_fuel = info['max_fuel']
    n_targets = len(targets)
    n_items = len(items)

    # Position -> index mappings
    target_map = {}
    for i, (tx, ty, ts, tc, tr) in enumerate(targets):
        target_map[(tx, ty)] = i

    # Item detection uses 5x5 region check (rbt method).
    # Items may not be on the movement grid, so precompute which
    # items are reachable from each grid position.
    # Grid: x ∈ {agent_x % 5, agent_x % 5 + 5, ...}, y similarly
    x_off = agent_pos[0] % 5  # typically 4
    y_off = agent_pos[1] % 5  # typically 0
    item_at_pos = {}  # grid_pos -> list of item indices
    for gx in range(x_off, 64, 5):
        for gy in range(y_off, 64, 5):
            hits = []
            for i, (ix, iy) in enumerate(items):
                if gx <= ix < gx + 5 and gy <= iy < gy + 5:
                    hits.append(i)
            if hits:
                item_at_pos[(gx, gy)] = hits

    # State: (x, y, shape, color, rot, vis_targets, col_items, fuel)
    initial_state = (agent_pos[0], agent_pos[1], s0, c0, r0, 0, 0, max_fuel)
    goal_visited = (1 << n_targets) - 1

    # For pruning: track best fuel at each core state
    # core_state = (x, y, shape, color, rot, vis_targets, col_items)
    best_fuel = {}
    core = initial_state[:7]
    best_fuel[core] = max_fuel

    queue = deque([(initial_state, [])])
    explored = 0

    print(f"  Agent=({agent_pos[0]},{agent_pos[1]}), config=s{s0}/c{c0}/r{r0}, "
          f"targets={n_targets}, items={n_items}, fuel={max_fuel}")
    for i, (tx, ty, ts, tc, tr) in enumerate(targets):
        print(f"    T{i}: ({tx},{ty}) need s={ts}/c={tc}/r={tr}")

    while queue:
        state, path = queue.popleft()
        x, y, shape, color, rot, vis, col, fuel = state
        explored += 1

        if explored % 100000 == 0:
            print(f"    explored {explored}, queue {len(queue)}, "
                  f"best_fuel {len(best_fuel)}")

        for action, (dx, dy) in ACTIONS.items():
            nx, ny = x + dx, y + dy

            if nx < 0 or nx >= 64 or ny < 0 or ny >= 64:
                continue
            if (nx, ny) in walls:
                continue

            new_shape, new_color, new_rot = shape, color, rot
            new_vis = vis
            new_col = col
            collected_item = False

            # Collectible items at destination (5x5 region check)
            if (nx, ny) in item_at_pos:
                for iidx in item_at_pos[(nx, ny)]:
                    if not (col & (1 << iidx)):
                        collected_item = True
                        new_col = new_col | (1 << iidx)

            # Config changer at destination
            if (nx, ny) in changers:
                ctype = changers[(nx, ny)]
                if ctype == 'shape':
                    new_shape = (shape + 1) % 6
                elif ctype == 'color':
                    new_color = (color + 1) % 4
                elif ctype == 'rotation':
                    new_rot = (rot + 1) % 4

            # Target at destination
            if (nx, ny) in target_map:
                tidx = target_map[(nx, ny)]
                if not (vis & (1 << tidx)):
                    ts, tc, tr = (targets[tidx][2],
                                  targets[tidx][3],
                                  targets[tidx][4])
                    if (new_shape == ts and new_color == tc
                            and new_rot == tr):
                        new_vis = vis | (1 << tidx)
                    else:
                        continue  # Wrong config, can't move

            # Fuel update
            if collected_item:
                new_fuel = max_fuel  # refuel, pca() skipped
            else:
                new_fuel = fuel - 1  # pca() decrements
                if new_fuel < 0:
                    continue  # Death — prune

            # Pruning: skip if we've seen this core state with more fuel
            new_core = (nx, ny, new_shape, new_color, new_rot,
                        new_vis, new_col)
            prev_best = best_fuel.get(new_core, -1)
            if new_fuel <= prev_best:
                continue
            best_fuel[new_core] = new_fuel

            new_path = path + [action]

            if new_vis == goal_visited:
                print(f"  SOLVED! {len(new_path)} steps, "
                      f"explored {explored}")
                return new_path

            new_state = (nx, ny, new_shape, new_color, new_rot,
                         new_vis, new_col, new_fuel)
            queue.append((new_state, new_path))

    print(f"  NOT SOLVED (explored {explored})")
    return None


def verify_solution(level_idx, solution):
    """Verify solution by running through actual game engine."""
    game = ls20.Ls20()
    action_map = {
        1: GameAction.ACTION1,
        2: GameAction.ACTION2,
        3: GameAction.ACTION3,
        4: GameAction.ACTION4,
    }

    for i, act in enumerate(solution):
        obs = game.perform_action(ActionInput(id=action_map[act]))
        lc = getattr(obs, 'levels_completed', 0) or 0

        if obs.state.name == 'GAME_OVER':
            print(f"  GAME OVER at step {i + 1}")
            return False

        if lc > level_idx:
            print(f"  Verified: level {level_idx + 1} completed "
                  f"at step {i + 1}")
            return True

    print(f"  Verification FAILED: level not completed")
    return False


def build_action_sequence(solution):
    """Convert solution to replay format."""
    return [{'action': act} for act in solution]


def insert_winning_sequences(db_path, solutions_by_level):
    """Insert solutions into winning_sequences table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    inserted = 0
    cumulative_actions = []
    level_breakpoints = {}
    total_score = 0.0

    for level_idx in sorted(solutions_by_level.keys()):
        solution = solutions_by_level[level_idx]
        level_num = level_idx + 1

        seq = build_action_sequence(solution)
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
            seq_id, 'ls20-cb3b57cc', level_num, 'solver', 'solver-session',
            now, json.dumps(seq), len(seq), float(level_num),
            efficiency, '[]', '[]', 'ls20',
            0, 'ls20_solver',
        ))
        inserted += 1
        print(f"  Inserted L{level_num}: {seq_id} "
              f"({len(seq)} actions, eff={efficiency:.4f})")

    # Uber sequence
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
        uber_id, 'ls20-cb3b57cc', 0, 'solver', 'solver-session',
        now, json.dumps(cumulative_actions), len(cumulative_actions),
        total_score,
        1.0 / max(len(cumulative_actions), 1),
        '[]', '[]', 'ls20',
        0, True, json.dumps(level_breakpoints), 'ls20_solver',
    ))
    inserted += 1
    print(f"  Inserted uber: {uber_id} "
          f"({len(cumulative_actions)} actions, {total_score:.0f} levels)")

    conn.commit()
    conn.close()
    print(f"\n  Total inserted: {inserted} sequences")


def main():
    import time

    insert_db = '--insert-db' in sys.argv

    target_level = None
    for arg in sys.argv:
        if arg.startswith('--level='):
            target_level = int(arg.split('=')[1])

    solutions_by_level = {}
    total_steps = 0

    level_range = range(7)
    if target_level is not None:
        level_range = [target_level - 1]

    for level_idx in level_range:
        level_num = level_idx + 1
        print(f"\nLevel {level_num}:")
        t0 = time.time()

        game = ls20.Ls20()
        solution = solve_level(game, level_idx)
        elapsed = time.time() - t0

        if solution is not None:
            print(f"  Solution ({len(solution)} steps): {solution}")
            print(f"  Time: {elapsed:.1f}s")

            # Build cumulative solution for verification
            # (verify needs actions from L1 through current level)
            cumulative = []
            for prev_idx in sorted(solutions_by_level.keys()):
                cumulative.extend(solutions_by_level[prev_idx])
            cumulative.extend(solution)

            ok = verify_solution(level_idx, cumulative)
            print(f"  Verification: {'PASS' if ok else 'FAIL'}")

            if ok:
                solutions_by_level[level_idx] = solution
                total_steps += len(solution)
        else:
            print(f"  Time: {elapsed:.1f}s")

    print(f"\n{'=' * 60}")
    print(f"Solved {len(solutions_by_level)}/{len(level_range)} levels, "
          f"{total_steps} total steps")

    if insert_db and solutions_by_level:
        db_path = os.path.join(project_root, 'core_data.db')
        print(f"\nInserting into {db_path}...")
        insert_winning_sequences(db_path, solutions_by_level)

    return solutions_by_level


if __name__ == '__main__':
    main()
