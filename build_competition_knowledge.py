"""
build_competition_knowledge.py

Exports bundled knowledge JSONs from core_data.db for the competition notebook.

For each game, produces competition_knowledge/{game_id}.json containing:
  - causal_map   : tile effects from world_model_states
  - rules        : learned rules from world_model_states
  - color_cycles : from world_model_states (if present)
  - winning_sequences : best sequence per level (replay-ready)
  - win_templates / goal_cells : from world_model_states (if present)

Run with:
  PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe build_competition_knowledge.py
"""

import json
import os
import sqlite3

DB_PATH = 'core_data.db'
OUT_DIR = 'competition_knowledge'

os.makedirs(OUT_DIR, exist_ok=True)


def best_sequences_for_game(con, game_id: str) -> dict:
    """
    Return {level_str: [action_entry, ...]} using the best (highest efficiency,
    fewest failures) winning sequence per level.
    """
    rows = con.execute(
        """
        SELECT level_number, action_sequence, coordinate_sequence,
               total_actions, efficiency_score
        FROM winning_sequences
        WHERE game_id = ?
          AND is_active = 1
          AND consecutive_failures < 3
        ORDER BY level_number ASC, efficiency_score DESC
        """,
        (game_id,),
    ).fetchall()

    best_per_level: dict = {}
    for row in rows:
        lvl = row[0]
        if lvl not in best_per_level:
            best_per_level[lvl] = row  # first = highest efficiency

    result: dict = {}
    for lvl, row in sorted(best_per_level.items()):
        if lvl == 0:          # level 0 is a sentinel/init sequence — skip
            continue
        level_str = str(lvl)
        try:
            actions = json.loads(row[1]) if row[1] else []
            coords  = json.loads(row[2]) if row[2] else []
        except Exception:
            actions = []
            coords  = []

        entries = []
        for i, act in enumerate(actions):
            # action_sequence entries are already {'action': int, 'data': {...}}
            # (the sequence stores the full action+data dict).
            # Fall back to pairing with coordinate_sequence for older rows.
            if isinstance(act, dict):
                entries.append(act)
            else:
                coord = coords[i] if i < len(coords) else None
                if coord and isinstance(coord, dict) and 'x' in coord and 'y' in coord:
                    entries.append({
                        'action': int(act),
                        'data': {'x': int(coord['x']), 'y': int(coord['y'])},
                    })
                else:
                    entries.append(int(act))

        if entries:
            result[level_str] = entries
            print(f'    L{lvl}: {len(entries)} steps  efficiency={row[4]:.3f}')

    return result


def export_game(con, game_id: str) -> bool:
    # Try the primary state_id format
    for state_id in [f'wm_{game_id}', f'wms_{game_id[:4]}_best']:
        row = con.execute(
            'SELECT objects_json FROM world_model_states WHERE state_id = ?',
            (state_id,),
        ).fetchone()
        if row:
            break
    else:
        print(f'  [{game_id}] No world_model_state found — sequences only')
        row = None

    causal_map: dict = {}
    rules: list = []
    color_cycles: dict = {}
    win_templates: dict = {}
    goal_cells: dict = {}
    goal_source: str = ''

    if row:
        try:
            state = json.loads(row[0])
        except Exception as e:
            print(f'  [{game_id}] JSON parse error: {e}')
            state = {}

        raw_cm = state.get('causal_map', {})
        print(f'  [{game_id}] causal_map entries: {len(raw_cm)}')

        # Summarise each entry: instead of keeping all raw observations
        # (which bloat the file to tens of MB), pre-compute the derived
        # fields that _inject_knowledge() actually needs:
        #   affected, color_transitions, observation_count,
        #   productive_count, destructive_count
        for raw_key, val in raw_cm.items():
            key = raw_key.strip()
            if not key.startswith('('):
                key = f'({key})'

            observations = val.get('observations', []) if isinstance(val, dict) else []
            obs_count = val.get('observation_count', len(observations)) if isinstance(val, dict) else 0
            productive = val.get('productive_count', 0) if isinstance(val, dict) else 0
            destructive = val.get('destructive_count', 0) if isinstance(val, dict) else 0

            affected_set: list = []
            color_trans: dict = {}
            for obs in observations:
                for ch in obs.get('changes', []):
                    cx, cy = ch.get('x', 0), ch.get('y', 0)
                    cell = [cx, cy]
                    if cell not in affected_set:
                        affected_set.append(cell)
                    ckey = f'({cx},{cy})'
                    fc, tc = ch.get('from_color', 0), ch.get('to_color', 0)
                    if ckey not in color_trans:
                        color_trans[ckey] = []
                    pair = [fc, tc]
                    if pair not in color_trans[ckey]:
                        color_trans[ckey].append(pair)

            # Keep at most 8 observations for confidence check in _inject_knowledge
            # (it only uses them to derive affected + transitions, already done above)
            summary_obs = [{'changes': []}] * min(obs_count, 8)

            # Output format matches what _inject_knowledge() in the
            # competition notebook expects: 'affected', 'transitions',
            # 'obs' (count), 'conf' (confidence 0-1).
            conf = round(productive / max(obs_count, 1), 3)
            causal_map[key] = {
                'affected': affected_set,
                'transitions': color_trans,
                'obs': obs_count,
                'conf': conf,
            }

        # Rules
        for r in state.get('rules_learned', []):
            if isinstance(r, dict):
                rules.append({
                    'type': r.get('type', r.get('rule_type', 'unknown')),
                    'desc': r.get('description', r.get('desc', '')),
                    'evidence': r.get('evidence_count', r.get('evidence', 1)),
                    'confidence': round(float(r.get('confidence', 0.5)), 3),
                })

        # Color cycles
        for pos_key, cycle in state.get('color_cycles', {}).items():
            key = pos_key.strip()
            if not key.startswith('('):
                key = f'({key})'
            color_cycles[key] = cycle

        # Win templates
        for lvl_str, cells in state.get('win_templates', {}).items():
            if isinstance(cells, dict):
                win_templates[lvl_str] = {
                    (k.strip() if k.strip().startswith('(') else f'({k.strip()})'): v
                    for k, v in cells.items()
                }

        # Goal cells
        for pos_key, color in state.get('goal_cells', {}).items():
            key = pos_key.strip()
            if not key.startswith('('):
                key = f'({key})'
            goal_cells[key] = color

        goal_source = state.get('goal_source', '')

    # Winning sequences
    print(f'  [{game_id}] building winning sequences...')
    winning_seqs = best_sequences_for_game(con, game_id)
    print(f'  [{game_id}] {len(winning_seqs)} levels with sequences')

    out = {
        'game_id': game_id,
        'causal_map': causal_map,
        'rules': rules,
        'color_cycles': color_cycles,
        'win_templates': win_templates,
        'goal_cells': goal_cells,
        'goal_source': goal_source,
        'winning_sequences': winning_seqs,
    }

    path = os.path.join(OUT_DIR, f'{game_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f)   # no indent — keep file size small

    size_kb = os.path.getsize(path) / 1024
    print(f'  [{game_id}] -> {path}  ({size_kb:.0f} KB)')
    return True


def main():
    con = sqlite3.connect(DB_PATH)

    # All game_ids that have winning sequences
    game_ids = [
        r[0] for r in con.execute(
            'SELECT DISTINCT game_id FROM winning_sequences ORDER BY game_id'
        ).fetchall()
    ]
    print(f'Games with winning sequences: {game_ids}')
    print()

    # Also include any game_ids found only in world_model_states
    wm_ids = [
        r[0][3:] for r in con.execute(
            "SELECT state_id FROM world_model_states WHERE state_id LIKE 'wm_%'"
        ).fetchall()
        if r[0] != 'wm_' and '-' in r[0][3:]  # filter to real game_ids
    ]
    all_ids = sorted(set(game_ids) | set(wm_ids))
    print(f'All exportable game_ids: {all_ids}')
    print()

    exported = 0
    for game_id in all_ids:
        print(f'Exporting {game_id}...')
        try:
            export_game(con, game_id)
            exported += 1
        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback; traceback.print_exc()
        print()

    con.close()
    print(f'Done. Exported {exported}/{len(all_ids)} games to {OUT_DIR}/')
    print()

    # Summary
    files = os.listdir(OUT_DIR)
    total_kb = sum(os.path.getsize(os.path.join(OUT_DIR, f)) for f in files) / 1024
    print(f'Knowledge bundle: {len(files)} files, {total_kb:.0f} KB total')


if __name__ == '__main__':
    main()
