"""FT09 Puzzle Solver — Computes optimal solutions for all 6 levels.

Approach:
- L1-L4 (all Hkx, center-only clicks): Analytical per-cell solution from constraints
- L5 (27 Hkx + 3 NTi, cross-pattern): Gaussian elimination over GF(2)
- L6 (22 NTi, up+self pattern): Gaussian elimination over GF(2)

Usage:
    python manual_tools/ft09_solve.py              # just compute and verify
    python manual_tools/ft09_solve.py --insert-db   # also insert into winning_sequences
"""
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'environment_files', 'ft09', '9ab2447a'))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import numpy as np
from arcengine import ActionInput, GameAction
from ft09 import Ft09, levels


def get_cell_click_pattern(cell, is_nti):
    """Get the effective click pattern for a cell.

    For Hkx (is_nti=False): center-only [[0,0,0],[0,1,0],[0,0,0]]
    For NTi: determined by which pixels == 6 in the sprite
    """
    if not is_nti:
        return [[0, 0, 0], [0, 1, 0], [0, 0, 0]]

    pattern = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    for j in range(3):
        for i in range(3):
            if cell.pixels[j][i] == 6:
                pattern[j][i] = 1
    return pattern


def solve_center_only(game, level_idx):
    """Solve a level where ALL cells have center-only click patterns.

    Each cell is independent — determine target color from constraints.
    Uses two-pass approach:
      1. Collect positive (must-be) and negative (must-not-be) requirements
      2. Resolve: positive wins, negatives filter, cheapest remaining chosen

    Returns list of (x, y, clicks_needed) tuples.
    """
    game.set_level(level_idx)
    cells = list(game.fhc) + list(game.mou)
    constraints = game.gig
    palette = list(game.gqb)
    n_colors = len(palette)

    cell_pos_set = {(c.x, c.y) for c in cells}

    # Per-cell: positive requirement (palette index) and set of forbidden indices
    cell_required = {}   # (x,y) -> palette index (positive requirement)
    cell_forbidden = {}  # (x,y) -> set of forbidden palette indices

    for constraint in constraints:
        nRq = constraint.pixels[1][1]

        for row in range(3):
            for col in range(3):
                if row == 1 and col == 1:
                    continue

                flag = constraint.pixels[row][col]
                tx = constraint.x + (col - 1) * 4
                ty = constraint.y + (row - 1) * 4

                if (tx, ty) not in cell_pos_set:
                    continue

                if flag == 0:
                    # Must equal nRq
                    if nRq not in palette:
                        continue
                    target_idx = palette.index(nRq)
                    existing = cell_required.get((tx, ty))
                    if existing is not None and existing != target_idx:
                        print(f"  CONFLICT at ({tx},{ty}): was palette[{existing}], "
                              f"now palette[{target_idx}]")
                    cell_required[(tx, ty)] = target_idx
                else:
                    # Must NOT equal nRq
                    if nRq not in palette:
                        continue  # Always satisfied
                    forbidden_idx = palette.index(nRq)
                    cell_forbidden.setdefault((tx, ty), set()).add(forbidden_idx)

    # Resolve target for each cell
    cell_target_idx = {}
    for c in cells:
        pos = (c.x, c.y)
        if pos in cell_required:
            # Positive requirement takes priority
            cell_target_idx[pos] = cell_required[pos]
        elif pos in cell_forbidden:
            # Only negative constraints: find cheapest allowed color
            forbidden = cell_forbidden[pos]
            allowed = [i for i in range(n_colors) if i not in forbidden]
            if not allowed:
                print(f"  UNSOLVABLE at {pos}: all colors forbidden!")
                cell_target_idx[pos] = 0
            else:
                # Pick cheapest (fewest clicks from starting index 0)
                cell_target_idx[pos] = min(allowed)
        else:
            # No constraints: stay at palette[0]
            cell_target_idx[pos] = 0

    # Compute click sequence
    result = []
    for c in cells:
        target_idx = cell_target_idx[(c.x, c.y)]
        clicks_needed = target_idx  # Start at index 0, need target_idx clicks
        if clicks_needed > 0:
            result.append((c.x, c.y, clicks_needed))

    return result


def solve_lights_out(game, level_idx):
    """Solve a level with NTi cells using Gaussian elimination over GF(n).

    Returns list of (x, y, clicks_needed) tuples.
    """
    game.set_level(level_idx)
    cells_hkx = list(game.fhc)
    cells_nti = list(game.mou)
    all_cells = cells_hkx + cells_nti
    constraints = game.gig
    palette = list(game.gqb)
    n_colors = len(palette)

    n_cells = len(all_cells)
    cell_pos_to_idx = {}
    for idx, c in enumerate(all_cells):
        cell_pos_to_idx[(c.x, c.y)] = idx

    # Determine target state for each cell from constraints
    # target[i] = number of color advances needed (0 to n_colors-1)
    target = [0] * n_cells

    for constraint in constraints:
        nRq = constraint.pixels[1][1]

        for row in range(3):
            for col in range(3):
                if row == 1 and col == 1:
                    continue

                flag = constraint.pixels[row][col]
                tx = constraint.x + (col - 1) * 4
                ty = constraint.y + (row - 1) * 4

                if (tx, ty) not in cell_pos_to_idx:
                    continue

                cell_idx = cell_pos_to_idx[(tx, ty)]

                if flag == 0:
                    if nRq not in palette:
                        continue
                    target[cell_idx] = palette.index(nRq)
                else:
                    if nRq not in palette:
                        continue
                    nrq_idx = palette.index(nRq)
                    if n_colors == 2:
                        target[cell_idx] = 1 - nrq_idx

    # Build the click-effect matrix A[n_cells x n_cells] over GF(n_colors)
    # A[j][i] = 1 if clicking cell i affects cell j, else 0
    A = np.zeros((n_cells, n_cells), dtype=int)

    for i, cell in enumerate(all_cells):
        is_nti = cell in cells_nti
        pattern = get_cell_click_pattern(cell, is_nti)

        for drow in range(3):
            for dcol in range(3):
                if pattern[drow][dcol] == 1:
                    affected_x = cell.x + (dcol - 1) * 4
                    affected_y = cell.y + (drow - 1) * 4
                    if (affected_x, affected_y) in cell_pos_to_idx:
                        j = cell_pos_to_idx[(affected_x, affected_y)]
                        A[j][i] = 1

    # Solve A * x = target (mod n_colors) using Gaussian elimination
    # For GF(2): standard binary Gaussian elimination
    if n_colors == 2:
        solution = gaussian_elimination_gf2(A, target, n_cells)
    else:
        solution = gaussian_elimination_gfn(A, target, n_cells, n_colors)

    if solution is None:
        print(f"  WARNING: No solution found for level {level_idx + 1}!")
        return []

    result = []
    for i, clicks in enumerate(solution):
        if clicks > 0:
            c = all_cells[i]
            result.append((c.x, c.y, clicks))

    return result


def gaussian_elimination_gf2(A, b, n):
    """Solve Ax = b over GF(2) using Gaussian elimination with back-substitution."""
    # Augmented matrix [A | b]
    aug = np.zeros((n, n + 1), dtype=int)
    aug[:, :n] = A % 2
    aug[:, n] = [x % 2 for x in b]

    pivot_col = [0] * n  # Track which column is the pivot for each row
    pivot_row = [-1] * n

    row = 0
    for col in range(n):
        # Find pivot
        found = -1
        for r in range(row, n):
            if aug[r][col] == 1:
                found = r
                break
        if found == -1:
            continue

        # Swap rows
        aug[[row, found]] = aug[[found, row]]
        pivot_col[row] = col
        pivot_row[col] = row

        # Eliminate
        for r in range(n):
            if r != row and aug[r][col] == 1:
                aug[r] = (aug[r] + aug[row]) % 2

        row += 1

    # Extract solution (free variables set to 0)
    x = [0] * n
    for r in range(row):
        col = pivot_col[r]
        x[col] = aug[r][n]

    # Verify
    for j in range(n):
        check = sum(A[j][i] * x[i] for i in range(n)) % 2
        if check != b[j] % 2:
            return None  # No solution

    return x


def gaussian_elimination_gfn(A, b, n, mod):
    """Solve Ax = b over GF(mod) — works for prime mod."""
    aug = np.zeros((n, n + 1), dtype=int)
    aug[:, :n] = A % mod
    aug[:, n] = [x % mod for x in b]

    pivot_col = [0] * n
    row = 0

    for col in range(n):
        found = -1
        for r in range(row, n):
            if aug[r][col] != 0:
                found = r
                break
        if found == -1:
            continue

        aug[[row, found]] = aug[[found, row]]
        pivot_col[row] = col

        # Normalize pivot row
        inv = pow(int(aug[row][col]), -1, mod)
        aug[row] = (aug[row] * inv) % mod

        # Eliminate
        for r in range(n):
            if r != row and aug[r][col] != 0:
                factor = aug[r][col]
                aug[r] = (aug[r] - factor * aug[row]) % mod

        row += 1

    x = [0] * n
    for r in range(row):
        col = pivot_col[r]
        x[col] = int(aug[r][n])

    # Verify
    for j in range(n):
        check = sum(A[j][i] * x[i] for i in range(n)) % mod
        if check != b[j] % mod:
            return None

    return x


def verify_solution(game, level_idx, click_list):
    """Verify a solution by applying clicks and checking cgj()."""
    game.set_level(level_idx)

    palette = list(game.gqb)
    all_cells = list(game.fhc) + list(game.mou)
    cell_map = {(c.x, c.y): c for c in all_cells}

    is_nti_set = {(c.x, c.y) for c in game.mou}

    for gx, gy, n_clicks in click_list:
        cell = cell_map[(gx, gy)]
        is_nti = (gx, gy) in is_nti_set
        pattern = get_cell_click_pattern(cell, is_nti)

        for _ in range(n_clicks):
            # Apply click pattern
            for drow in range(3):
                for dcol in range(3):
                    if pattern[drow][dcol] == 1:
                        ax = gx + (dcol - 1) * 4
                        ay = gy + (drow - 1) * 4
                        if (ax, ay) in cell_map:
                            affected = cell_map[(ax, ay)]
                            cur_color = affected.pixels[1][1]
                            if cur_color in palette:
                                cur_idx = palette.index(cur_color)
                                new_idx = (cur_idx + 1) % len(palette)
                                affected.color_remap(cur_color, palette[new_idx])

    return game.cgj()


def grid_to_display(gx, gy, grid_size=32):
    """Convert grid coordinates to display coordinates (center of cell)."""
    scale = 64 // grid_size
    # Sprite is 3 pixels, at scale 2 that's 6 display pixels.
    # Click at center of sprite: grid (gx+1) * scale
    return (gx + 1) * scale, (gy + 1) * scale


def build_action_sequence(click_list, grid_size=32):
    """Convert (gx, gy, n_clicks) list to winning_sequences action format."""
    sequence = []
    for gx, gy, n_clicks in click_list:
        dx, dy = grid_to_display(gx, gy, grid_size)
        for _ in range(n_clicks):
            sequence.append({'action': 6, 'data': {'x': dx, 'y': dy}})
    return sequence


def play_and_capture(game, solutions_by_level):
    """Play all levels through the game API to capture frames.

    Returns (action_sequence, initial_frame, final_frame, total_score) or None.
    """
    game.full_reset()
    all_actions = []
    initial_frame = None
    final_frame = None

    for level_idx in range(len(solutions_by_level)):
        click_list = solutions_by_level[level_idx]
        seq = build_action_sequence(click_list)

        for i, act in enumerate(seq):
            action_input = ActionInput()
            action_input.id = GameAction.ACTION6
            action_input.data = act['data']

            result = game.perform_action(action_input, raw=True)

            if initial_frame is None and result.frame:
                initial_frame = result.frame[0].tolist() if hasattr(result.frame[0], 'tolist') else result.frame[0]

            all_actions.append(act)

            if result.state.name == 'WIN':
                final_frame = result.frame[-1].tolist() if result.frame and hasattr(result.frame[-1], 'tolist') else None
                return all_actions, initial_frame, final_frame, result.levels_completed

            if result.state.name == 'GAME_OVER':
                print(f"  GAME OVER at level {level_idx + 1}, action {i + 1}!")
                return None

    return all_actions, initial_frame, final_frame, game._score


def insert_winning_sequences(db_path, solutions_by_level, game):
    """Insert solver-generated sequences into winning_sequences table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Play through to capture frames
    play_result = play_and_capture(game, solutions_by_level)
    if play_result is None:
        print("ERROR: Could not play through all levels!")
        conn.close()
        return False

    full_action_seq, initial_frame, final_frame, total_score = play_result
    print(f"\n  Full playthrough: {len(full_action_seq)} actions, score={total_score}")

    # Insert per-level sequences
    now = datetime.now().isoformat()
    inserted = 0

    # Build cumulative sequences for uber sequence
    cumulative_actions = []
    level_breakpoints = {}

    for level_idx in range(len(solutions_by_level)):
        click_list = solutions_by_level[level_idx]
        level_num = level_idx + 1
        seq = build_action_sequence(click_list)
        start_idx = len(cumulative_actions)
        cumulative_actions.extend(seq)
        level_breakpoints[str(level_num)] = {
            'start': start_idx,
            'end': len(cumulative_actions) - 1,
            'actions': len(seq),
        }

        # Insert individual level sequence
        seq_id = f"seq_solver_{uuid.uuid4().hex[:8]}"
        efficiency = 1.0 / max(len(seq), 1)

        cursor.execute("""
            INSERT INTO winning_sequences
            (sequence_id, game_id, level_number, agent_id, session_id,
             discovered_at, action_sequence, total_actions, total_score,
             efficiency_score, initial_frame, final_frame, game_type,
             generation_discovered, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seq_id, 'ft09-9ab2447a', level_num, 'solver', 'solver-session',
            now, json.dumps(seq), len(seq), float(level_num),
            efficiency, '[]', '[]', 'ft09',
            0, 'ft09_solver',
        ))
        inserted += 1
        print(f"  Inserted L{level_num}: {seq_id} ({len(seq)} actions, eff={efficiency:.4f})")

    # Insert uber sequence (all levels combined)
    uber_id = f"seq_solver_uber_{uuid.uuid4().hex[:8]}"
    cursor.execute("""
        INSERT INTO winning_sequences
        (sequence_id, game_id, level_number, agent_id, session_id,
         discovered_at, action_sequence, total_actions, total_score,
         efficiency_score, initial_frame, final_frame, game_type,
         generation_discovered, is_uber_sequence, level_breakpoints, source_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uber_id, 'ft09-9ab2447a', 0, 'solver', 'solver-session',
        now, json.dumps(cumulative_actions), len(cumulative_actions), float(total_score),
        1.0 / max(len(cumulative_actions), 1),
        json.dumps(initial_frame) if initial_frame else '[]',
        json.dumps(final_frame) if final_frame else '[]',
        'ft09', 0, True, json.dumps(level_breakpoints), 'ft09_solver',
    ))
    print(f"  Inserted uber: {uber_id} ({len(cumulative_actions)} actions, {total_score} levels)")

    conn.commit()
    conn.close()
    print(f"\n  Total inserted: {inserted} level sequences + 1 uber sequence")
    return True


def main():
    insert_db = '--insert-db' in sys.argv

    game = Ft09()
    solutions = {}

    for level_idx in range(6):
        game.set_level(level_idx)
        name = game.current_level.name
        n_hkx = len(game.fhc)
        n_nti = len(game.mou)
        n_constraints = len(game.gig)
        palette = list(game.gqb)
        budget = game.lpw.oro
        has_nti = n_nti > 0

        print(f"\n=== Level {level_idx + 1} ({name}) ===")
        print(f"  Cells: {n_hkx} Hkx + {n_nti} NTi, Palette: {palette}, Budget: {budget}")

        if not has_nti:
            click_list = solve_center_only(game, level_idx)
            method = "analytical (center-only)"
        else:
            click_list = solve_lights_out(game, level_idx)
            method = "Gaussian elimination (Lights Out)"

        total_clicks = sum(c[2] for c in click_list)
        print(f"  Method: {method}")
        print(f"  Solution: {len(click_list)} cells to click, {total_clicks} total clicks")
        print(f"  Budget usage: {total_clicks}/{budget} ({100 * total_clicks / budget:.0f}%)")

        # Verify
        valid = verify_solution(game, level_idx, click_list)
        print(f"  Verified: {'PASS' if valid else 'FAIL'}")

        if valid:
            solutions[level_idx] = click_list
            for gx, gy, n in click_list:
                dx, dy = grid_to_display(gx, gy)
                print(f"    Click ({gx},{gy}) x{n} -> display ({dx},{dy})")
        else:
            print("  ERROR: Solution verification failed!")
            # Try brute force for small levels
            if n_hkx + n_nti <= 14 and len(palette) == 2:
                print("  Attempting brute force...")
                click_list = brute_force_solve(game, level_idx)
                if click_list:
                    solutions[level_idx] = click_list
                else:
                    print("  Brute force also failed!")

    print(f"\n{'=' * 60}")
    print(f"Solutions found: {len(solutions)}/{len(levels)} levels")

    if len(solutions) == len(levels):
        # Play through to verify full game completion
        print("\nPlaying full game to verify...")
        result = play_and_capture(game, solutions)
        if result:
            actions, _, _, score = result
            print(f"  Full game: {len(actions)} actions, {score} levels completed")
            if score == len(levels):
                print("  FULL GAME WIN!")
            else:
                print(f"  WARNING: Only {score}/{len(levels)} levels completed")

    if insert_db and len(solutions) == len(levels):
        db_path = os.path.join(project_root, 'core_data.db')
        print(f"\nInserting into {db_path}...")
        insert_winning_sequences(db_path, solutions, game)


def brute_force_solve(game, level_idx):
    """Brute force for small levels — try all click combinations."""
    import itertools

    game.set_level(level_idx)
    cells = list(game.fhc) + list(game.mou)
    palette = list(game.gqb)
    n_colors = len(palette)
    n_cells = len(cells)

    print(f"  Brute force: {n_cells} cells, {n_colors} colors, {n_colors**n_cells} combos")

    for combo in itertools.product(range(n_colors), repeat=n_cells):
        click_list = [(cells[i].x, cells[i].y, combo[i]) for i in range(n_cells) if combo[i] > 0]
        if verify_solution(game, level_idx, click_list):
            total = sum(combo)
            print(f"  Brute force found: {total} clicks")
            return click_list

    return None


if __name__ == '__main__':
    main()
