"""Analyze the Feb 8-9 2026 run results for LS20, FT09, VC33."""
import os
import sqlite3

# game_id format in DB: just the prefix like 'ls20', 'ft09', 'vc33' or full ID
# Let's query to find which format is used
TARGET_GAMES_FULL = ['ls20-cb3b57cc', 'ft09-9ab2447a', 'vc33-9851e02b']
TARGET_GAMES_SHORT = ['ls20', 'ft09', 'vc33']
SESSION_START = '2026-02-08 18:50:00'

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Current generation
    c.execute('SELECT MAX(generation) FROM game_results')
    max_gen = c.fetchone()[0]
    print(f"=== Max generation: {max_gen} ===")

    # Find which game_id format is used
    c.execute("SELECT DISTINCT game_id FROM game_results WHERE game_id LIKE 'ls20%' OR game_id LIKE 'ft09%' OR game_id LIKE 'vc33%' LIMIT 10")
    game_ids = [r[0] for r in c.fetchall()]
    print(f"Game IDs found: {game_ids}")

    # Determine game_id patterns to use
    target_map = {}
    for gid in game_ids:
        for short in TARGET_GAMES_SHORT:
            if gid.startswith(short):
                target_map[short] = gid
                break

    if not target_map:
        print("ERROR: No matching game_ids found!")
        conn.close()
        return

    print(f"Target map: {target_map}")

    # Find session start generation
    c.execute(
        "SELECT MIN(generation) FROM game_results WHERE created_at >= ?",
        (SESSION_START,)
    )
    row = c.fetchone()
    start_gen = row[0] if row and row[0] else max_gen
    print(f"Session start gen: {start_gen}")
    print(f"Gens in session: {max_gen - start_gen + 1}")

    # Total plays
    c.execute("SELECT COUNT(*) FROM game_results WHERE generation >= ?", (start_gen,))
    total = c.fetchone()[0]
    print(f"Total plays this session: {total}\n")

    # Per-game comparison
    print("=" * 85)
    hdr = f"{'METRIC':<28} {'BASELINE':>18} {'THIS SESSION':>18} {'DELTA':>12}"
    print(hdr)
    print("=" * 85)

    for short, game_id in target_map.items():
        print(f"\n--- {short.upper()} ({game_id}) ---")

        base = None
        sess = None
        for label, cond in [("BASELINE", f"generation < {start_gen}"),
                            ("SESSION", f"generation >= {start_gen}")]:
            c.execute(f"""
                SELECT COUNT(*), ROUND(AVG(final_score),4), MAX(final_score),
                       ROUND(AVG(level_completions),2), MAX(level_completions),
                       SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN win_detected=1 THEN 1 ELSE 0 END)
                FROM game_results
                WHERE game_id = ? AND {cond}
            """, (game_id,))
            r = c.fetchone()
            if label == "BASELINE":
                base = r
            else:
                sess = r

        b_plays = base[0] or 0
        s_plays = sess[0] or 0
        b_avg = base[1] or 0
        s_avg = sess[1] or 0
        b_max = base[2] or 0
        s_max = sess[2] or 0
        b_avg_lv = base[3] or 0
        s_avg_lv = sess[3] or 0
        b_max_lv = base[4] or 0
        s_max_lv = sess[4] or 0
        b_pos = base[5] or 0
        s_pos = sess[5] or 0
        b_wins = base[6] or 0
        s_wins = sess[6] or 0

        print(f"  {'Plays':<26} {b_plays:>18} {s_plays:>18}")
        print(f"  {'Avg Score':<26} {b_avg:>18.4f} {s_avg:>18.4f} {s_avg-b_avg:>+12.4f}")
        print(f"  {'Max Score':<26} {b_max:>18.4f} {s_max:>18.4f} {s_max-b_max:>+12.4f}")
        print(f"  {'Avg Levels Completed':<26} {b_avg_lv:>18.2f} {s_avg_lv:>18.2f} {s_avg_lv-b_avg_lv:>+12.2f}")
        print(f"  {'Max Levels Completed':<26} {b_max_lv:>18} {s_max_lv:>18}")
        print(f"  {'Positive Score Games':<26} {b_pos:>18} {s_pos:>18}")
        print(f"  {'Wins Detected':<26} {b_wins:>18} {s_wins:>18}")
        b_rate = (b_pos / b_plays * 100) if b_plays > 0 else 0
        s_rate = (s_pos / s_plays * 100) if s_plays > 0 else 0
        print(f"  {'Positive Rate %':<26} {b_rate:>17.1f}% {s_rate:>17.1f}%")

    # Score distribution
    print("\n" + "=" * 85)
    print("SCORE DISTRIBUTION THIS SESSION")
    print("=" * 85)
    for short, game_id in target_map.items():
        print(f"\n--- {short.upper()} ---")
        c.execute("""
            SELECT final_score, COUNT(*) as cnt
            FROM game_results
            WHERE game_id = ? AND generation >= ?
            GROUP BY final_score ORDER BY final_score DESC LIMIT 15
        """, (game_id, start_gen))
        rows = c.fetchall()
        if rows:
            for score, cnt in rows:
                bar = '#' * min(50, cnt)
                print(f"  score={score:>8.4f}: {cnt:>5} {bar}")
        else:
            print("  No games played this session")

    # Generation trend (last 30 gens)
    print("\n" + "=" * 85)
    print("GEN TREND (last 30)")
    print("=" * 85)
    for short, game_id in target_map.items():
        print(f"\n--- {short.upper()} ---")
        c.execute("""
            SELECT generation, ROUND(AVG(final_score),4), COUNT(*), MAX(level_completions)
            FROM game_results
            WHERE game_id = ? AND generation > ? - 30
            GROUP BY generation ORDER BY generation
        """, (game_id, max_gen))
        rows = c.fetchall()
        if rows:
            for gen, avg_s, cnt, max_lv in rows:
                bar = '#' * int((avg_s or 0) * 100)
                print(f"  gen {gen:>5}: avg={avg_s or 0:>8.4f} n={cnt:>3} max_lv={max_lv} {bar}")
        else:
            print("  No data")

    # Winning sequences
    print("\n" + "=" * 85)
    print("WINNING SEQUENCES")
    print("=" * 85)
    for table in ['winning_sequences', 'winning_sequences_full_game']:
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if c.fetchone():
            placeholders = ','.join('?' for _ in target_map.values())
            game_ids_list = list(target_map.values())
            c.execute(f"""
                SELECT game_type, COUNT(*), MAX(levels_completed)
                FROM {table}
                WHERE game_type IN ({placeholders})
                GROUP BY game_type
            """, game_ids_list)
            rows = c.fetchall()
            if not rows:
                # try game_id column instead
                try:
                    c.execute(f"""
                        SELECT game_id, COUNT(*)
                        FROM {table}
                        WHERE game_id IN ({placeholders})
                        GROUP BY game_id
                    """, game_ids_list)
                    rows2 = c.fetchall()
                    if rows2:
                        for r in rows2:
                            print(f"  [{table}] {r[0]}: {r[1]} sequences")
                    else:
                        print(f"  [{table}] No sequences for target games")
                except Exception:
                    print(f"  [{table}] No sequences for target games")
            else:
                for r in rows:
                    print(f"  [{table}] {r[0]}: {r[1]} seqs, max_lv={r[2]}")
        else:
            print(f"  [{table}] Table does not exist")

    conn.close()
    print("\n=== Analysis complete ===")


if __name__ == '__main__':
    main()
