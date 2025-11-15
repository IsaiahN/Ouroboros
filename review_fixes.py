"""Review if sequence replay fixes are working"""
import sqlite3
from datetime import datetime, timedelta

db_path = "core_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("SEQUENCE REPLAY FIX VERIFICATION")
print("=" * 80)

# 1. Check recent game performance (last 7 hours)
cutoff = datetime.now() - timedelta(hours=7.5)
cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

cursor.execute("""
    SELECT 
        COUNT(*) as total_games,
        SUM(CASE WHEN final_score = 0 THEN 1 ELSE 0 END) as zero_scores,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as non_zero_scores,
        AVG(final_score) as avg_score
    FROM game_results
    WHERE start_time >= ?
""", (cutoff_str,))

recent = cursor.fetchone()
print(f"\n1. RECENT PERFORMANCE (Last 7.5 hours):")
print(f"   Total Games: {recent[0]}")
print(f"   Zero Scores: {recent[1]} ({recent[1]/recent[0]*100 if recent[0] > 0 else 0:.1f}%)")
print(f"   Non-Zero Scores: {recent[2]} ({recent[2]/recent[0]*100 if recent[0] > 0 else 0:.1f}%)")
print(f"   Avg Score: {recent[3]:.2f}")

# 2. Check sequence usage in recent games
cursor.execute("""
    SELECT 
        COUNT(DISTINCT gr.game_id) as games_with_sequence_usage
    FROM game_results gr
    JOIN arc_action_tracking aat ON gr.game_id = aat.game_id
    WHERE gr.start_time >= ?
    AND aat.notes LIKE '%sequence%'
""", (cutoff_str,))

seq_usage = cursor.fetchone()[0]
print(f"\n2. SEQUENCE USAGE:")
print(f"   Games with sequence replay: {seq_usage}")
print(f"   Percentage: {seq_usage/recent[0]*100 if recent[0] > 0 else 0:.1f}%")

# 3. Check sequence validation attempts
cursor.execute("""
    SELECT 
        COUNT(*) as attempts,
        SUM(was_successful) as successes,
        SUM(CASE WHEN was_successful = 0 THEN 1 ELSE 0 END) as failures
    FROM sequence_validation_attempts
    WHERE validation_timestamp >= ?
""", (cutoff_str,))

val = cursor.fetchone()
print(f"\n3. SEQUENCE VALIDATION (Recent):")
print(f"   Total Attempts: {val[0]}")
print(f"   Successes: {val[1]}")
print(f"   Failures: {val[2]}")
if val[0] > 0:
    print(f"   Success Rate: {val[1]/val[0]*100:.1f}%")

# 4. Check mode behavior - are generalists exploring too much?
cursor.execute("""
    SELECT 
        aom.mode_name,
        COUNT(*) as games,
        SUM(CASE WHEN gr.final_score = 0 THEN 1 ELSE 0 END) as zero_scores,
        AVG(gr.final_score) as avg_score
    FROM game_results gr
    LEFT JOIN agent_operating_modes aom ON gr.session_id = aom.session_id
    WHERE gr.start_time >= ?
    GROUP BY aom.mode_name
    ORDER BY aom.mode_name
""", (cutoff_str,))

print(f"\n4. MODE BEHAVIOR (Recent):")
for row in cursor.fetchall():
    mode = row[0] or "UNKNOWN"
    games = row[1]
    zeros = row[2]
    avg_score = row[3]
    print(f"   {mode:12s}: {games:4d} games | {zeros:4d} zeros ({zeros/games*100:.1f}%) | "
          f"Avg Score: {avg_score:.2f}")

# 5. Check frustration detector - what's causing 92% frustration?
cursor.execute("""
    SELECT 
        game_id,
        agent_id,
        frustration_type,
        severity,
        description
    FROM frustration_events
    WHERE detected_at >= ?
    ORDER BY detected_at DESC
    LIMIT 20
""", (cutoff_str,))

print(f"\n5. RECENT FRUSTRATION EVENTS (Last 20):")
frustration_counts = {}
for row in cursor.fetchall():
    ftype = row[2]
    frustration_counts[ftype] = frustration_counts.get(ftype, 0) + 1

for ftype, count in sorted(frustration_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {ftype}: {count} occurrences")

# 6. Check if sequences are actually being found
cursor.execute("""
    SELECT 
        ws.game_id,
        ws.level,
        ws.total_actions,
        ws.is_active,
        COALESCE(sr.successful_validations, 0) as successes,
        COALESCE(sr.failed_validations, 0) as failures
    FROM winning_sequences ws
    LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
    ORDER BY ws.game_id, ws.level
""")

print(f"\n6. AVAILABLE SEQUENCES:")
by_game = {}
for row in cursor.fetchall():
    game_id = row[0]
    level = row[1]
    actions = row[2]
    active = row[3]
    successes = row[4]
    failures = row[5]
    
    if game_id not in by_game:
        by_game[game_id] = []
    
    status = "✓ PROVEN" if successes > 0 else ("✗ FAILED" if failures > 0 else "? UNTESTED")
    by_game[game_id].append((level, actions, active, status))

for game_id, sequences in sorted(by_game.items()):
    active_count = sum(1 for s in sequences if s[2] == 1)
    proven_count = sum(1 for s in sequences if "PROVEN" in s[3])
    print(f"   {game_id}: {len(sequences)} sequences ({proven_count} proven, {active_count} active)")
    for level, actions, active, status in sequences[:3]:  # Show first 3
        act_str = "ACTIVE" if active else "INACTIVE"
        print(f"      Level {level}: {actions:5d} actions - {status:12s} [{act_str}]")

# 7. Check if games are being selected properly
cursor.execute("""
    SELECT 
        SUBSTR(gr.session_id, 1, 4) as game_id,
        COUNT(*) as plays,
        AVG(gr.final_score) as avg_score,
        SUM(CASE WHEN gr.final_score = 0 THEN 1 ELSE 0 END) as zero_scores
    FROM game_results gr
    WHERE gr.start_time >= ?
    GROUP BY game_id
    ORDER BY plays DESC
    LIMIT 10
""", (cutoff_str,))

print(f"\n7. MOST PLAYED GAMES (Recent):")
for row in cursor.fetchall():
    game_id = row[0]
    plays = row[1]
    avg_score = row[2]
    zeros = row[3]
    print(f"   {game_id}: {plays:4d} plays | Avg: {avg_score:.2f} | Zeros: {zeros} ({zeros/plays*100:.1f}%)")

conn.close()
print("\n" + "=" * 80)
