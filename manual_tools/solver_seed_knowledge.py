"""H34: Solver-Seeded Causal Knowledge.

Runs solver sequences through game engines step-by-step, observes
frame diffs at each step, and stores the resulting causal knowledge
(effects, rules, color cycles, walls, solver_targets) into
world_model_states for cognitive agents to load as prior knowledge.

Usage:
    python manual_tools/solver_seed_knowledge.py              # dry run
    python manual_tools/solver_seed_knowledge.py --insert-db   # insert into DB
"""
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Game engine paths
ft09_dir = os.path.join(project_root, 'environment_files', 'ft09', '9ab2447a')
vc33_dir = os.path.join(project_root, 'environment_files', 'vc33', 'a1b2c3d4')
ls20_dir = os.path.join(project_root, 'environment_files', 'ls20', 'cb3b57cc')


def load_solver_sequences(db_path):
    """Load all solver sequences from winning_sequences table."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT game_type, level_number, action_sequence
        FROM winning_sequences
        WHERE source_mode LIKE '%solver%'
          AND is_uber_sequence = 0
          AND is_active = 1
        ORDER BY game_type, level_number
    """).fetchall()
    conn.close()

    seqs = defaultdict(dict)
    for r in rows:
        seqs[r['game_type']][r['level_number']] = json.loads(r['action_sequence'])
    return dict(seqs)


def extract_frame(obs):
    """Get 2D numpy frame from observation."""
    frame = obs.frame if hasattr(obs, 'frame') else obs
    if isinstance(frame, list):
        frame = frame[-1] if frame else None
    if frame is None:
        return None
    arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
    if arr.ndim == 3:
        arr = arr[0] if arr.shape[0] == 1 else arr[:, :, 0]
    return arr


def compute_diff(frame_before, frame_after):
    """Compute which pixel positions changed between frames."""
    if frame_before is None or frame_after is None:
        return set()
    diff_mask = frame_before != frame_after
    ys, xs = np.where(diff_mask)
    return set(zip(xs.tolist(), ys.tolist()))


def seed_ft09(solver_seqs):
    """Run FT09 solver sequences, observe effects per click position."""
    sys.path.insert(0, ft09_dir)
    from arcengine import ActionInput, GameAction
    from ft09 import Ft09

    effects = {}  # (x,y) -> {affected: set, color_transitions: dict, obs_count: int}
    solver_targets = {}  # level_num -> [(x,y), ...]
    color_cycles = {}
    goal_states = {}  # level_num -> {(x,y): target_color}

    # Play through entire game, tracking frame diffs at each step
    game = Ft09()
    prev_frame = None

    for level_num in sorted(solver_seqs.keys()):
        seq = solver_seqs[level_num]
        level_positions = []
        level_affected = set()  # all positions that changed during this level

        for act in seq:
            data = act.get('data', {})
            click_x = data.get('x', 0)
            click_y = data.get('y', 0)
            pos = (click_x, click_y)

            # Execute action
            ai = ActionInput()
            ai.id = GameAction.ACTION6
            ai.data = data
            result = game.perform_action(ai, raw=True)
            frame_after = extract_frame(result)

            # Compute diff (skip first action — no prev_frame)
            if prev_frame is not None and frame_after is not None:
                changed = compute_diff(prev_frame, frame_after)
                level_affected |= changed

                if pos not in effects:
                    effects[pos] = {
                        'affected': set(),
                        'color_transitions': defaultdict(list),
                        'obs_count': 0,
                    }
                effects[pos]['affected'] |= changed
                effects[pos]['obs_count'] += 1

                for cx, cy in changed:
                    if 0 <= cy < prev_frame.shape[0] and 0 <= cx < prev_frame.shape[1]:
                        old_c = int(prev_frame[cy, cx])
                        new_c = int(frame_after[cy, cx])
                        effects[pos]['color_transitions'][(cx, cy)].append(
                            (old_c, new_c)
                        )

            prev_frame = frame_after
            level_positions.append(pos)

        # Capture goal state: pixel colors at affected positions after solving
        if frame_after is not None and level_affected:
            level_goal = {}
            for (gx, gy) in level_affected:
                if 0 <= gy < frame_after.shape[0] and 0 <= gx < frame_after.shape[1]:
                    level_goal[f"{gx},{gy}"] = int(frame_after[gy, gx])
            goal_states[str(level_num)] = level_goal

        solver_targets[level_num] = level_positions
        print(f"  FT09 L{level_num}: {len(seq)} clicks, "
              f"{len(level_positions)} positions, "
              f"{len(goal_states.get(str(level_num), {}))} goal cells")

    # Build causal_data in world_model_states format
    causal_data = {}
    for pos, eff in effects.items():
        pos_key = f"{pos[0]},{pos[1]}"
        observations = []
        for aff_pos in sorted(eff['affected']):
            transitions = eff['color_transitions'].get(aff_pos, [])
            if transitions:
                observations.append({
                    'changes': [{'x': aff_pos[0], 'y': aff_pos[1],
                                 'from_color': transitions[0][0],
                                 'to_color': transitions[0][1]}]
                })
        causal_data[pos_key] = {
            'observations': observations,
            'observation_count': eff['obs_count'],
            'productive_count': eff['obs_count'],  # Solver clicks are all productive
            'destructive_count': 0,
            'confidence': min(0.95, 0.3 + eff['obs_count'] * 0.15),
        }

    # Extract color cycles from transitions
    for pos, eff in effects.items():
        for tile_pos, transitions in eff['color_transitions'].items():
            if len(transitions) >= 2:
                cycle = [t[0] for t in transitions] + [transitions[-1][1]]
                color_cycles[f"{tile_pos[0]},{tile_pos[1]}"] = cycle

    rules = [{
        'type': 'toggle_neighborhood',
        'desc': 'Clicking toggles self and neighbors (Lights Out)',
        'evidence': sum(e['obs_count'] for e in effects.values()),
        'confidence': 0.95,
    }]

    return {
        'causal_map': causal_data,
        'color_cycles': color_cycles,
        'walls': [],
        'rules': rules,
        'solver_targets': {str(k): [(p[0], p[1]) for p in v]
                           for k, v in solver_targets.items()},
        'goal_states': goal_states,
        'completeness': 0.9,
    }


def seed_vc33(solver_seqs):
    """Run VC33 solver sequences, observe effects per switch click."""
    # Find actual vc33 directory
    vc33_base = os.path.join(project_root, 'environment_files', 'vc33')
    vc33_subdirs = [d for d in os.listdir(vc33_base)
                    if os.path.isdir(os.path.join(vc33_base, d))]
    if not vc33_subdirs:
        print("  VC33: no game directory found!")
        return None
    actual_vc33_dir = os.path.join(vc33_base, vc33_subdirs[0])
    sys.path.insert(0, actual_vc33_dir)
    from arcengine import ActionInput, GameAction
    from vc33 import Vc33

    effects = {}
    solver_targets = {}
    goal_states = {}

    game = Vc33()

    # Play through entire game, tracking frame diffs
    prev_frame = None

    for level_num in sorted(solver_seqs.keys()):
        seq = solver_seqs[level_num]
        level_positions = []
        level_affected = set()

        for act in seq:
            data = act.get('data', {})
            click_x = data.get('x', 0)
            click_y = data.get('y', 0)
            pos = (click_x, click_y)

            ai = ActionInput()
            ai.id = GameAction.ACTION6
            ai.data = data
            result = game.perform_action(ai, raw=True)
            frame_after = extract_frame(result)

            if prev_frame is not None and frame_after is not None:
                changed = compute_diff(prev_frame, frame_after)
                level_affected |= changed

                if pos not in effects:
                    effects[pos] = {
                        'affected': set(),
                        'color_transitions': defaultdict(list),
                        'obs_count': 0,
                    }
                effects[pos]['affected'] |= changed
                effects[pos]['obs_count'] += 1

                for cx, cy in changed:
                    if 0 <= cy < prev_frame.shape[0] and 0 <= cx < prev_frame.shape[1]:
                        old_c = int(prev_frame[cy, cx])
                        new_c = int(frame_after[cy, cx])
                        effects[pos]['color_transitions'][(cx, cy)].append(
                            (old_c, new_c)
                        )

            prev_frame = frame_after
            level_positions.append(pos)

        # Capture goal state from solved frame
        if frame_after is not None and level_affected:
            level_goal = {}
            for (gx, gy) in level_affected:
                if 0 <= gy < frame_after.shape[0] and 0 <= gx < frame_after.shape[1]:
                    level_goal[f"{gx},{gy}"] = int(frame_after[gy, gx])
            goal_states[str(level_num)] = level_goal

        solver_targets[level_num] = level_positions
        print(f"  VC33 L{level_num}: {len(seq)} clicks, "
              f"{len(level_positions)} positions, "
              f"{len(goal_states.get(str(level_num), {}))} goal cells")

    # Build causal_data
    causal_data = {}
    for pos, eff in effects.items():
        pos_key = f"{pos[0]},{pos[1]}"
        observations = []
        for aff_pos in sorted(eff['affected']):
            transitions = eff['color_transitions'].get(aff_pos, [])
            if transitions:
                observations.append({
                    'changes': [{'x': aff_pos[0], 'y': aff_pos[1],
                                 'from_color': transitions[0][0],
                                 'to_color': transitions[0][1]}]
                })
        causal_data[pos_key] = {
            'observations': observations,
            'observation_count': eff['obs_count'],
            'productive_count': eff['obs_count'],
            'destructive_count': 0,
            'confidence': min(0.95, 0.3 + eff['obs_count'] * 0.15),
        }

    color_cycles = {}
    for pos, eff in effects.items():
        for tile_pos, transitions in eff['color_transitions'].items():
            if len(transitions) >= 2:
                cycle = [t[0] for t in transitions] + [transitions[-1][1]]
                color_cycles[f"{tile_pos[0]},{tile_pos[1]}"] = cycle

    rules = [{
        'type': 'rail_slide',
        'desc': 'Clicking switches slides rail segments (rail puzzle)',
        'evidence': sum(e['obs_count'] for e in effects.values()),
        'confidence': 0.95,
    }]

    return {
        'causal_map': causal_data,
        'color_cycles': color_cycles,
        'walls': [],
        'rules': rules,
        'solver_targets': {str(k): [(p[0], p[1]) for p in v]
                           for k, v in solver_targets.items()},
        'goal_states': goal_states,
        'completeness': 0.9,
    }


def seed_ls20(solver_seqs):
    """Run LS20 solver sequences, observe movement walls and paths.

    H39b: Also extracts structured level info (targets with required configs,
    config changer positions, initial player config) for cognitive navigation.
    """
    sys.path.insert(0, ls20_dir)
    # ls20_solve.py is in manual_tools/ (sibling file)
    manual_tools_dir = os.path.dirname(os.path.abspath(__file__))
    if manual_tools_dir not in sys.path:
        sys.path.insert(0, manual_tools_dir)
    from arcengine import ActionInput, GameAction
    from ls20 import Ls20
    from ls20_solve import extract_level_info

    walls = []  # [(pos, action)]
    open_paths = set()
    visited = set()
    solver_targets = {}  # level -> [(x,y), ...]
    solver_level_configs = {}  # H39b: level -> {targets, changers, initial_config}

    action_map = {
        1: GameAction.ACTION1, 2: GameAction.ACTION2,
        3: GameAction.ACTION3, 4: GameAction.ACTION4,
    }

    game = Ls20()

    for level_num in sorted(solver_seqs.keys()):
        seq = solver_seqs[level_num]
        level_waypoints = []

        # Reset game, replay prior levels
        game = Ls20()
        cumulative = []
        for prev_level in range(1, level_num):
            prev_seq = solver_seqs.get(prev_level, [])
            cumulative.extend(prev_seq)
        for act in cumulative:
            a = act.get('action', act) if isinstance(act, dict) else act
            ai = ActionInput()
            ai.id = action_map[a]
            game.perform_action(ai)

        # H39b: Extract level info BEFORE playing (captures initial state)
        try:
            level_info = extract_level_info(game, level_num - 1)
            solver_level_configs[level_num] = {
                'agent_pos': list(level_info['agent_pos']),
                'targets': [
                    [t[0], t[1], t[2], t[3], t[4]]
                    for t in level_info['targets']
                ],
                'changers': {
                    f"{x},{y}": ctype
                    for (x, y), ctype in level_info['changers'].items()
                },
                'initial_config': list(level_info['initial_config']),
                'walls': [
                    [wx, wy]
                    for wx, wy in sorted(level_info['walls'])
                ],
                # H44: Store items + fuel for fuel-aware BFS navigation
                'items': [
                    [ix, iy]
                    for ix, iy in level_info['items']
                ],
                'max_fuel': level_info['max_fuel'],
            }
            n_targets = len(level_info['targets'])
            n_changers = len(level_info['changers'])
            n_items = len(level_info['items'])
            print(f"  LS20 L{level_num}: {n_targets} targets, "
                  f"{n_changers} changers, {n_items} items, "
                  f"fuel={level_info['max_fuel']}, "
                  f"init=s{level_info['initial_config'][0]}/"
                  f"c{level_info['initial_config'][1]}/"
                  f"r{level_info['initial_config'][2]}")
        except Exception as e:
            print(f"  LS20 L{level_num}: extract_level_info failed: {e}")

        # Play step by step
        prev_x, prev_y = game.mgu.x, game.mgu.y
        for act in seq:
            a = act.get('action', act) if isinstance(act, dict) else act

            ai = ActionInput()
            ai.id = action_map[a]
            game.perform_action(ai)

            new_x, new_y = game.mgu.x, game.mgu.y

            if new_x == prev_x and new_y == prev_y:
                # Wall: movement failed
                walls.append({'pos': [prev_x, prev_y], 'action': a})
            else:
                # Open path
                open_paths.add(((prev_x, prev_y), a))
                visited.add((new_x, new_y))
                level_waypoints.append((new_x, new_y))

            prev_x, prev_y = new_x, new_y

        solver_targets[level_num] = level_waypoints
        print(f"  LS20 L{level_num}: {len(seq)} moves, "
              f"{len(level_waypoints)} waypoints, "
              f"{len([w for w in walls])} walls total")

    # LS20 has no click effects — knowledge is movement-based
    rules = [{
        'type': 'maze_navigation',
        'desc': 'Navigate maze with config changers to match targets',
        'evidence': len(visited),
        'confidence': 0.90,
    }]

    return {
        'causal_map': {},
        'color_cycles': {},
        'walls': walls,
        'rules': rules,
        'solver_targets': {str(k): v for k, v in solver_targets.items()},
        'solver_level_configs': {
            str(k): v for k, v in solver_level_configs.items()
        },
        'completeness': 0.7,
        # H51d: solver_level_configs are variant-specific (maze layout).
        # Tag with source variant so loading code can skip for other variants.
        'source_game_id': 'ls20-cb3b57cc',
    }


def insert_knowledge(db_path, game_type, knowledge):
    """Insert solver knowledge into world_model_states.

    Uses state_id 'solver_seed_{game_type}' (separate from runtime
    'wms_{game_type}_best') so agent-accumulated data never overwrites
    solver-seeded goal_states and solver_targets.
    """
    conn = sqlite3.connect(db_path)
    state_id = f"solver_seed_{game_type}"
    objects_json = json.dumps(knowledge)
    step_number = len(knowledge.get('causal_map', {})) + 100

    conn.execute("""
        INSERT OR REPLACE INTO world_model_states
            (state_id, game_id, session_id, step_number,
             objects_json, grid_hash, score, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        state_id, f"{game_type}-solver", "solver-seed",
        step_number, objects_json, '', 0.0,
        json.dumps({'source': 'solver_seed_knowledge', 'game_type': game_type}),
    ))
    conn.commit()
    conn.close()
    print(f"  Inserted {game_type}: state_id={state_id}, "
          f"step_number={step_number}, "
          f"{len(objects_json)} bytes")


def main():
    insert_db = '--insert-db' in sys.argv
    db_path = os.path.join(project_root, 'core_data.db')

    print("Loading solver sequences from DB...")
    all_seqs = load_solver_sequences(db_path)
    print(f"  Found: {', '.join(f'{k} ({len(v)} levels)' for k, v in all_seqs.items())}")

    results = {}

    if 'ft09' in all_seqs:
        print("\nSeeding FT09 knowledge...")
        results['ft09'] = seed_ft09(all_seqs['ft09'])

    if 'vc33' in all_seqs:
        print("\nSeeding VC33 knowledge...")
        results['vc33'] = seed_vc33(all_seqs['vc33'])

    if 'ls20' in all_seqs:
        print("\nSeeding LS20 knowledge...")
        results['ls20'] = seed_ls20(all_seqs['ls20'])

    # Summary
    print(f"\n{'=' * 60}")
    for gt, knowledge in results.items():
        n_effects = len(knowledge.get('causal_map', {}))
        n_rules = len(knowledge.get('rules', []))
        n_walls = len(knowledge.get('walls', []))
        n_targets = sum(len(v) for v in knowledge.get('solver_targets', {}).values())
        n_configs = len(knowledge.get('solver_level_configs', {}))
        print(f"  {gt}: {n_effects} effects, {n_rules} rules, "
              f"{n_walls} walls, {n_targets} solver_target positions"
              f"{f', {n_configs} level_configs' if n_configs else ''}")

    if insert_db:
        print(f"\nInserting into {db_path}...")
        for gt, knowledge in results.items():
            insert_knowledge(db_path, gt, knowledge)
        print("Done.")
    else:
        print("\nDry run. Use --insert-db to write to database.")


if __name__ == '__main__':
    main()
