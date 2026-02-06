"""Diagnostic query to analyze what the system has learned across generations."""
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

def safe(val, fmt=".4f"):
    if val is None:
        return "N/A"
    return f"{val:{fmt}}"

# 1. GENERATION OVERVIEW
section("GENERATION OVERVIEW")
r = conn.execute("SELECT MAX(generation) as max_gen, COUNT(DISTINCT generation) as distinct_gens FROM game_results").fetchone()
print(f"Max generation: {r['max_gen']}")
print(f"Distinct generations: {r['distinct_gens']}")
r2 = conn.execute("SELECT COUNT(*) as total FROM game_results").fetchone()
print(f"Total game results: {r2['total']}")

# 2. OVERALL SCORE SUMMARY
section("OVERALL SCORE SUMMARY")
r = conn.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive,
           SUM(CASE WHEN level_completions > 0 THEN 1 ELSE 0 END) as any_level,
           MAX(final_score) as best_score,
           MAX(level_completions) as best_levels,
           AVG(final_score) as avg_score,
           AVG(total_actions) as avg_actions,
           SUM(CASE WHEN win_detected = 1 THEN 1 ELSE 0 END) as wins,
           AVG(frame_changes) as avg_frame_changes,
           AVG(coordinate_successes) as avg_coord_success
    FROM game_results
""").fetchone()
print(f"Total games: {r['total']}")
print(f"Games with score > 0: {r['positive']}")
print(f"Games with any level completed: {r['any_level']}")
print(f"Wins detected: {r['wins']}")
print(f"Best score ever: {r['best_score']}")
print(f"Best levels completed: {r['best_levels']}")
print(f"Average score: {safe(r['avg_score'], '.6f')}")
print(f"Average actions: {safe(r['avg_actions'], '.1f')}")
print(f"Average frame changes per game: {safe(r['avg_frame_changes'], '.1f')}")
print(f"Average coordinate successes: {safe(r['avg_coord_success'], '.1f')}")

# 3. SCORE BY GENERATION (sampled)
section("SCORE BY GENERATION (first 10, last 10)")
rows = conn.execute("""
    SELECT generation, COUNT(*) as games, AVG(final_score) as avg_score,
           MAX(final_score) as max_score, MAX(level_completions) as max_levels,
           SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive,
           AVG(frame_changes) as avg_frame_chg
    FROM game_results GROUP BY generation ORDER BY generation
""").fetchall()
for row in rows[:10]:
    print(f"  Gen {row['generation']:>5}: {row['games']:>4} games, avg={safe(row['avg_score'])}, max={row['max_score']}, lvl={row['max_levels']}, pos={row['positive']}, frame_chg={safe(row['avg_frame_chg'],'.1f')}")
if len(rows) > 20:
    print("  ...")
for row in rows[-10:]:
    print(f"  Gen {row['generation']:>5}: {row['games']:>4} games, avg={safe(row['avg_score'])}, max={row['max_score']}, lvl={row['max_levels']}, pos={row['positive']}, frame_chg={safe(row['avg_frame_chg'],'.1f')}")

# 4. DISTINCT GAMES PLAYED
section("DISTINCT GAMES PLAYED")
games = conn.execute("""
    SELECT game_id, COUNT(*) as plays, MAX(final_score) as best_score,
           MAX(level_completions) as best_levels, AVG(final_score) as avg_score,
           AVG(frame_changes) as avg_fc
    FROM game_results GROUP BY game_id ORDER BY best_score DESC LIMIT 20
""").fetchall()
for g in games:
    print(f"  {g['game_id']}: {g['plays']} plays, best_score={g['best_score']}, best_lvl={g['best_levels']}, avg={safe(g['avg_score'])}, avg_fc={safe(g['avg_fc'],'.1f')}")

# 5. WINNING SEQUENCES
section("WINNING SEQUENCES")
try:
    ws = conn.execute("SELECT COUNT(*) as c FROM winning_sequences").fetchone()
    print(f"Level-winning sequences: {ws['c']}")
    if ws['c'] > 0:
        top_ws = conn.execute("""
            SELECT game_id, level_number, total_actions, total_score, efficiency_score, is_active
            FROM winning_sequences ORDER BY total_score DESC LIMIT 10
        """).fetchall()
        for s in top_ws:
            print(f"  {s['game_id']} L{s['level_number']}: actions={s['total_actions']}, score={s['total_score']}, eff={safe(s['efficiency_score'])}, active={s['is_active']}")
except Exception as e:
    print(f"winning_sequences: {e}")

try:
    wf = conn.execute("SELECT COUNT(*) as c FROM winning_sequences_full_game").fetchone()
    print(f"Full-game winning sequences: {wf['c']}")
except Exception as e:
    print(f"winning_sequences_full_game: {e}")

# 6. DISCOVERED PATTERNS
section("DISCOVERED PATTERNS")
try:
    dp = conn.execute("SELECT COUNT(*) as c FROM discovered_patterns").fetchone()
    print(f"Total discovered patterns: {dp['c']}")
    if dp['c'] > 0:
        top = conn.execute("""
            SELECT pattern_type, COUNT(*) as c, AVG(confidence_score) as avg_conf,
                   AVG(success_rate) as avg_sr
            FROM discovered_patterns GROUP BY pattern_type ORDER BY c DESC LIMIT 10
        """).fetchall()
        for p in top:
            print(f"  {p['pattern_type']}: {p['c']}, avg_conf={safe(p['avg_conf'])}, avg_success={safe(p['avg_sr'])}")
except Exception as e:
    print(f"discovered_patterns: {e}")

# 7. VIRAL PACKAGES
section("VIRAL PACKAGES (Knowledge Transfer)")
try:
    vp = conn.execute("SELECT COUNT(*) as total FROM viral_packages").fetchone()
    print(f"Total viral packages: {vp['total']}")
except Exception as e:
    print(f"viral_packages: {e}")

# 8. AGENT POPULATION
section("AGENT POPULATION")
try:
    agents = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
               COUNT(DISTINCT agent_type) as types
        FROM agents
    """).fetchone()
    print(f"Total agents ever: {agents['total']}")
    print(f"Currently active: {agents['active']}")

    by_type = conn.execute("""
        SELECT agent_type, COUNT(*) as c,
               AVG(discovery_prestige) as avg_prest,
               AVG(total_games_played) as avg_games,
               AVG(total_score_achieved) as avg_total_score,
               MAX(best_single_game_score) as best_single
        FROM agents WHERE is_active = 1 GROUP BY agent_type
    """).fetchall()
    for a in by_type:
        print(f"  {a['agent_type']}: {a['c']} active, prestige={safe(a['avg_prest'])}, avg_games={safe(a['avg_games'],'.1f')}, best={a['best_single']}")
except Exception as e:
    print(f"agents: {e}")

# 9. ACTION DISTRIBUTION from action_traces
section("ACTION DISTRIBUTION (from action_traces)")
try:
    # Check what columns we can use
    total_at = conn.execute("SELECT COUNT(*) as c FROM action_traces").fetchone()
    print(f"Total action traces: {total_at['c']:,}")

    # frame_changed distribution
    fc = conn.execute("""
        SELECT frame_changed, COUNT(*) as c FROM action_traces GROUP BY frame_changed
    """).fetchall()
    for f in fc:
        print(f"  frame_changed={f['frame_changed']}: {f['c']:,}")

    # Score change distribution
    sc = conn.execute("""
        SELECT
            SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as pos,
            SUM(CASE WHEN score_change = 0 THEN 1 ELSE 0 END) as zero,
            SUM(CASE WHEN score_change < 0 THEN 1 ELSE 0 END) as neg,
            AVG(score_change) as avg_sc
        FROM action_traces
    """).fetchone()
    print(f"  Score changes: positive={sc['pos']}, zero={sc['zero']}, negative={sc['neg']}, avg={safe(sc['avg_sc'],'.6f')}")
except Exception as e:
    print(f"action_traces: {e}")

# 10. ROUTING DECISIONS (context_mode column)
section("ROUTING / CONTEXT MODE USAGE")
try:
    modes = conn.execute("""
        SELECT context_mode, COUNT(*) as c FROM action_traces
        WHERE context_mode IS NOT NULL
        GROUP BY context_mode ORDER BY c DESC LIMIT 15
    """).fetchall()
    if modes:
        for m in modes:
            print(f"  {m['context_mode']}: {m['c']:,}")
    else:
        print("  No context_mode data")
except Exception as e:
    print(f"  context_mode query: {e}")

# 11. NAVIGATION STATES
section("NAVIGATION STATE HISTORY")
try:
    nav = conn.execute("SELECT COUNT(*) as c FROM navigation_state_history").fetchone()
    print(f"Total navigation states: {nav['c']:,}")

    if nav['c'] > 0:
        states = conn.execute("""
            SELECT dominant_emotion, COUNT(*) as c FROM navigation_state_history
            GROUP BY dominant_emotion ORDER BY c DESC LIMIT 10
        """).fetchall()
        for s in states:
            print(f"  {s['dominant_emotion']}: {s['c']:,}")

        triggers = conn.execute("""
            SELECT state_change_trigger, COUNT(*) as c FROM navigation_state_history
            WHERE state_change_trigger IS NOT NULL
            GROUP BY state_change_trigger ORDER BY c DESC LIMIT 10
        """).fetchall()
        print("  State change triggers:")
        for t in triggers:
            print(f"    {t['state_change_trigger']}: {t['c']:,}")
except Exception as e:
    print(f"navigation_state_history: {e}")

# 12. SENSATION LEARNING
section("SENSATION LEARNING EVENTS")
try:
    sl = conn.execute("SELECT COUNT(*) as c FROM sensation_learning_events").fetchone()
    print(f"Total sensation events: {sl['c']:,}")
    if sl['c'] > 0:
        # Learning success rate
        lr = conn.execute("""
            SELECT
                SUM(CASE WHEN learning_success = 1 THEN 1 ELSE 0 END) as success,
                COUNT(*) as total,
                AVG(reward_received) as avg_reward,
                AVG(sensation_adjustment) as avg_adj
            FROM sensation_learning_events
        """).fetchone()
        print(f"  Success rate: {lr['success']}/{lr['total']} = {lr['success']/lr['total']*100:.1f}%")
        print(f"  Avg reward: {safe(lr['avg_reward'],'.4f')}, Avg adjustment: {safe(lr['avg_adj'],'.4f')}")
except Exception as e:
    print(f"sensation_learning_events: {e}")

# 13. SYSTEM LOGS (errors)
section("RECENT ERRORS IN SYSTEM LOGS")
try:
    total_logs = conn.execute("SELECT COUNT(*) as c FROM system_logs").fetchone()
    print(f"Total logs: {total_logs['c']:,}")
    err_count = conn.execute("SELECT COUNT(*) as c FROM system_logs WHERE level IN ('ERROR','CRITICAL')").fetchone()
    print(f"Errors/Critical: {err_count['c']:,}")

    if err_count['c'] > 0:
        errors = conn.execute("""
            SELECT message, COUNT(*) as c FROM system_logs
            WHERE level IN ('ERROR', 'CRITICAL')
            GROUP BY message ORDER BY c DESC LIMIT 15
        """).fetchall()
        for e in errors:
            msg = e['message'][:120] + "..." if len(e['message']) > 120 else e['message']
            print(f"  [{e['c']}x] {msg}")
except Exception as e:
    print(f"system_logs: {e}")

# 14. HYPOTHESIS SYSTEM
section("HYPOTHESIS SYSTEM")
try:
    hyp = conn.execute("SELECT COUNT(*) as total FROM hypotheses").fetchone()
    print(f"Total hypotheses: {hyp['total']}")
except Exception as e:
    print(f"hypotheses: {e}")

# 15. ALL NON-EMPTY TABLES
section("ALL NON-EMPTY TABLES")
try:
    db_size = os.path.getsize(DB_PATH) / (1024*1024)
    print(f"Database size: {db_size:.1f} MB")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for t in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) as c FROM [{t['name']}]").fetchone()
            if cnt['c'] > 0:
                print(f"  {t['name']}: {cnt['c']:,} rows")
        except:
            pass
except Exception as e:
    print(f"db size: {e}")

# 16. FRAME CHANGE ANALYSIS - key diagnostic
section("FRAME CHANGE DEEP DIVE (are actions affecting the game?)")
try:
    # Per-game frame change rate
    fc_by_game = conn.execute("""
        SELECT game_id,
               COUNT(*) as total_actions,
               SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frames_changed,
               ROUND(100.0 * SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
        FROM action_traces
        GROUP BY game_id ORDER BY pct DESC LIMIT 20
    """).fetchall()
    for g in fc_by_game:
        print(f"  {g['game_id']}: {g['frames_changed']}/{g['total_actions']} actions caused frame change ({g['pct']}%)")
except Exception as e:
    print(f"frame change analysis: {e}")

# 17. LEVEL COMPLETION EVIDENCE - any level ever beat?
section("LEVEL COMPLETION EVIDENCE")
try:
    lc = conn.execute("""
        SELECT game_id, MAX(level_completions) as max_lc, COUNT(*) as plays
        FROM game_results
        WHERE level_completions > 0
        GROUP BY game_id ORDER BY max_lc DESC LIMIT 20
    """).fetchall()
    if lc:
        for l in lc:
            print(f"  {l['game_id']}: max {l['max_lc']} levels completed ({l['plays']} plays)")
    else:
        print("  NO LEVELS EVER COMPLETED IN ANY GAME")
except Exception as e:
    print(f"level completions: {e}")

conn.close()
print(f"\n{'='*70}")
print("  DIAGNOSIS COMPLETE")
print(f"{'='*70}")
