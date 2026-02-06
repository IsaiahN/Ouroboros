"""Deep diagnosis Part 2 - routing traces, action patterns, and root cause analysis."""
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core_data.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

# 1. COGNITIVE ROUTING TRACES - what is the router deciding?
section("COGNITIVE ROUTING TRACES (347K rows)")
try:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cognitive_routing_traces)").fetchall()]
    print(f"Columns: {cols}")

    # Sample a few recent traces
    sample = conn.execute("SELECT * FROM cognitive_routing_traces ORDER BY ROWID DESC LIMIT 5").fetchall()
    if sample:
        for s in sample:
            d = dict(s)
            for k, v in d.items():
                if v is not None and str(v).strip():
                    print(f"  {k}: {str(v)[:100]}")
            print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 2. What rungs are being selected?
section("RUNG DISTRIBUTION IN ROUTING TRACES")
try:
    # Try common column names for rung
    for col in ['selected_rung', 'rung_name', 'rung', 'decision_rung']:
        if col in cols:
            rungs = conn.execute(f"""
                SELECT [{col}], COUNT(*) as c FROM cognitive_routing_traces
                GROUP BY [{col}] ORDER BY c DESC LIMIT 20
            """).fetchall()
            print(f"By {col}:")
            for r in rungs:
                print(f"  {r[col]}: {r['c']:,}")
            break
except Exception as e:
    print(f"Error: {e}")

# 3. ACTION TRACES - what actions are being sent?
section("ACTION TRACES - COORDINATE PATTERNS")
try:
    # What coordinates are being targeted?
    coord_sample = conn.execute("""
        SELECT coordinates, frame_changed, score_change, game_id
        FROM action_traces
        WHERE game_id = 'vc33-9851e02b'
        ORDER BY ROWID DESC LIMIT 20
    """).fetchall()
    print("Recent vc33 actions:")
    for c in coord_sample:
        print(f"  coords={c['coordinates']}, frame_changed={c['frame_changed']}, score_chg={c['score_change']}")

    # Frame change rate by coordinate range
    print("\nvc33 - Coordinate clustering (are we exploring or repeating?):")
    coord_analysis = conn.execute("""
        SELECT coordinates, COUNT(*) as times_tried,
               SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as times_changed
        FROM action_traces
        WHERE game_id = 'vc33-9851e02b'
        GROUP BY coordinates
        ORDER BY times_tried DESC LIMIT 20
    """).fetchall()
    for c in coord_analysis:
        print(f"  {c['coordinates']}: tried {c['times_tried']}x, changed frame {c['times_changed']}x")
except Exception as e:
    print(f"Error: {e}")

# 4. ls20 ACTIONS - the game that sometimes scores
section("ls20 ACTION PATTERNS (the only game that scores)")
try:
    ls20_coords = conn.execute("""
        SELECT coordinates, COUNT(*) as times_tried,
               SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as times_changed
        FROM action_traces
        WHERE game_id = 'ls20-cb3b57cc'
        GROUP BY coordinates
        ORDER BY times_changed DESC LIMIT 20
    """).fetchall()
    print("Most productive ls20 coordinates:")
    for c in ls20_coords:
        print(f"  {c['coordinates']}: tried {c['times_tried']}x, changed frame {c['times_changed']}x")

    # How did ls20 get level 1 completion?
    ls20_success = conn.execute("""
        SELECT session_id, final_score, level_completions, total_actions
        FROM game_results
        WHERE game_id LIKE 'ls20%' AND level_completions > 0
        ORDER BY final_score DESC LIMIT 10
    """).fetchall()
    print(f"\nls20 successful sessions ({len(ls20_success)} found):")
    for s in ls20_success:
        print(f"  session={s['session_id'][:16]}..., score={s['final_score']:.4f}, levels={s['level_completions']}, actions={s['total_actions']}")
except Exception as e:
    print(f"Error: {e}")

# 5. TRAINING SESSIONS - what are these 322K rows?
section("TRAINING SESSIONS (322K rows)")
try:
    ts_cols = [r[1] for r in conn.execute("PRAGMA table_info(training_sessions)").fetchall()]
    print(f"Columns: {ts_cols}")

    ts_sample = conn.execute("SELECT * FROM training_sessions ORDER BY ROWID DESC LIMIT 3").fetchall()
    for s in ts_sample:
        d = dict(s)
        for k, v in d.items():
            if v is not None and str(v).strip():
                print(f"  {k}: {str(v)[:100]}")
        print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 6. PLAYER STATE HISTORY - the 9.4M row elephant
section("PLAYER STATE HISTORY (9.4M rows - 9.6 GB)")
try:
    ps_cols = [r[1] for r in conn.execute("PRAGMA table_info(player_state_history)").fetchall()]
    print(f"Columns: {ps_cols}")

    # Just count distribution by game
    ps_dist = conn.execute("""
        SELECT game_id, COUNT(*) as c FROM player_state_history GROUP BY game_id
    """).fetchall()
    for p in ps_dist:
        print(f"  {p['game_id']}: {p['c']:,} rows")

    # Sample one row
    ps_sample = conn.execute("SELECT * FROM player_state_history LIMIT 1").fetchone()
    if ps_sample:
        d = dict(ps_sample)
        total_size = sum(len(str(v)) for v in d.values() if v)
        print(f"\nSample row total text size: ~{total_size:,} bytes")
        for k, v in d.items():
            val_preview = str(v)[:80] + "..." if v and len(str(v)) > 80 else str(v)
            print(f"  {k}: {val_preview}")
except Exception as e:
    print(f"Error: {e}")

# 7. WORKING THEORY HISTORY
section("WORKING THEORY HISTORY (15K rows)")
try:
    wt_cols = [r[1] for r in conn.execute("PRAGMA table_info(working_theory_history)").fetchall()]
    print(f"Columns: {wt_cols}")

    wt_sample = conn.execute("SELECT * FROM working_theory_history ORDER BY ROWID DESC LIMIT 5").fetchall()
    for s in wt_sample:
        d = dict(s)
        for k, v in d.items():
            if v is not None and str(v).strip():
                val = str(v)[:120] + "..." if len(str(v)) > 120 else str(v)
                print(f"  {k}: {val}")
        print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 8. METACOGNITIVE PREDICTIONS - 17K rows
section("METACOGNITIVE PREDICTIONS (17K rows)")
try:
    mp_cols = [r[1] for r in conn.execute("PRAGMA table_info(metacognitive_predictions)").fetchall()]
    print(f"Columns: {mp_cols}")

    mp_sample = conn.execute("SELECT * FROM metacognitive_predictions ORDER BY ROWID DESC LIMIT 3").fetchall()
    for s in mp_sample:
        d = dict(s)
        for k, v in d.items():
            if v is not None and str(v).strip():
                val = str(v)[:120] + "..." if len(str(v)) > 120 else str(v)
                print(f"  {k}: {val}")
        print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 9. PARIAHS - negative patterns learned
section("PARIAHS (58 entries)")
try:
    pariah_cols = [r[1] for r in conn.execute("PRAGMA table_info(pariahs)").fetchall()]
    print(f"Columns: {pariah_cols}")

    pariahs = conn.execute("SELECT * FROM pariahs LIMIT 10").fetchall()
    for p in pariahs:
        d = dict(p)
        for k, v in d.items():
            if v is not None and str(v).strip():
                val = str(v)[:120] + "..." if len(str(v)) > 120 else str(v)
                print(f"  {k}: {val}")
        print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 10. ACTION PROPOSALS LOG - what is being proposed?
section("ACTION PROPOSALS LOG (63K rows)")
try:
    ap_cols = [r[1] for r in conn.execute("PRAGMA table_info(action_proposals_log)").fetchall()]
    print(f"Columns: {ap_cols}")

    ap_sample = conn.execute("SELECT * FROM action_proposals_log ORDER BY ROWID DESC LIMIT 5").fetchall()
    for s in ap_sample:
        d = dict(s)
        for k, v in d.items():
            if v is not None and str(v).strip():
                val = str(v)[:120] + "..." if len(str(v)) > 120 else str(v)
                print(f"  {k}: {val}")
        print("  ---")
except Exception as e:
    print(f"Error: {e}")

# 11. GAME SCHEDULER - why only 2 games?
section("GAME SCHEDULING ANALYSIS")
try:
    # How many unique games exist in environment_files?
    env_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "environment_files")
    if os.path.exists(env_dir):
        game_dirs = [d for d in os.listdir(env_dir) if os.path.isdir(os.path.join(env_dir, d))]
        print(f"Games in environment_files/: {len(game_dirs)}")
        for g in game_dirs[:20]:
            print(f"  {g}")
    else:
        print("No environment_files/ directory found")
except Exception as e:
    print(f"Error: {e}")

# 12. GENERATION GAPS - why only 199 distinct generations out of 4992?
section("GENERATION DISTRIBUTION ANALYSIS")
try:
    gen_list = conn.execute("SELECT DISTINCT generation FROM game_results ORDER BY generation").fetchall()
    gens = [g['generation'] for g in gen_list]
    print(f"Generation range: {min(gens)} to {max(gens)}")
    print(f"Distinct generations with results: {len(gens)}")
    print(f"Expected if continuous: {max(gens) - min(gens) + 1}")
    print(f"Missing generations: {max(gens) - min(gens) + 1 - len(gens)}")

    # Show where the gaps are
    gaps = []
    for i in range(1, len(gens)):
        if gens[i] - gens[i-1] > 1:
            gaps.append((gens[i-1], gens[i], gens[i] - gens[i-1] - 1))
    print(f"\nLargest gaps:")
    gaps.sort(key=lambda x: -x[2])
    for start, end, size in gaps[:10]:
        print(f"  Gen {start} -> {end}: {size} missing generations")

    # Games per generation histogram
    games_per_gen = conn.execute("""
        SELECT generation, COUNT(*) as games FROM game_results
        GROUP BY generation ORDER BY games DESC LIMIT 10
    """).fetchall()
    print(f"\nMost games in a single generation:")
    for g in games_per_gen:
        print(f"  Gen {g['generation']}: {g['games']} games")
except Exception as e:
    print(f"Error: {e}")

conn.close()
print(f"\n{'='*70}")
print("  DEEP DIAGNOSIS COMPLETE")
print(f"{'='*70}")
