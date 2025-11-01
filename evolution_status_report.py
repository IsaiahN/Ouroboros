"""Evolution Run Status Report - After Several Hours"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime

db = DatabaseInterface()

print("=" * 80)
print("EVOLUTION RUN STATUS REPORT")
print(f"Generated: {datetime.now()}")
print("=" * 80)

# Time range of run
run_stats = db.execute_query("""
    SELECT 
        MIN(start_time) as first_game,
        MAX(end_time) as last_game,
        COUNT(*) as total_games
    FROM game_results
    WHERE start_time > '2025-10-31 15:00:00'
""")

if run_stats[0]['total_games'] > 0:
    print(f"\n📅 RUN DURATION:")
    print(f"   First game: {run_stats[0]['first_game']}")
    print(f"   Last game: {run_stats[0]['last_game']}")
    print(f"   Total games: {run_stats[0]['total_games']}")
    
    # Calculate duration
    from datetime import datetime
    start = datetime.fromisoformat(run_stats[0]['first_game'])
    end = datetime.fromisoformat(run_stats[0]['last_game'])
    duration = end - start
    hours = duration.total_seconds() / 3600
    print(f"   Duration: {hours:.1f} hours")

# Performance metrics
perf_stats = db.execute_query("""
    SELECT 
        AVG(level_completions) as avg_levels,
        MAX(level_completions) as max_levels,
        AVG(total_actions) as avg_actions,
        COUNT(CASE WHEN level_completions > 0 THEN 1 END) as games_with_levels,
        COUNT(*) as total_games
    FROM game_results
    WHERE start_time > '2025-10-31 15:00:00'
""")

if perf_stats[0]['total_games'] > 0:
    ps = perf_stats[0]
    print(f"\n🎮 PERFORMANCE:")
    print(f"   Total games played: {ps['total_games']}")
    print(f"   Avg levels/game: {ps['avg_levels']:.2f}")
    print(f"   Max levels in single game: {ps['max_levels']}")
    print(f"   Games with levels: {ps['games_with_levels']} ({ps['games_with_levels']/ps['total_games']*100:.1f}%)")
    print(f"   Avg actions/game: {ps['avg_actions']:.0f}")

# Agent evolution
agent_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_agents,
        SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_agents,
        MAX(generation) as current_gen,
        AVG(CASE WHEN is_active THEN avg_score_per_game END) as avg_score,
        MAX(avg_score_per_game) as top_score
    FROM agents
""")

if agent_stats:
    ag = agent_stats[0]
    print(f"\n🧬 AGENT EVOLUTION:")
    print(f"   Current generation: {ag['current_gen']}")
    print(f"   Total agents created: {ag['total_agents']}")
    print(f"   Active agents: {ag['active_agents']}")
    print(f"   Avg score (active): {ag['avg_score']:.4f}")
    print(f"   Top performer: {ag['top_score']:.4f}")

# Sequence learning progress
seq_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_sequences,
        COUNT(DISTINCT game_id) as unique_games,
        AVG(total_actions) as avg_actions,
        MIN(total_actions) as best_sequence,
        MAX(discovered_at) as last_discovery
    FROM winning_sequences
""")

if seq_stats[0]['total_sequences'] > 0:
    sq = seq_stats[0]
    print(f"\n🧠 SEQUENCE LEARNING:")
    print(f"   Total sequences: {sq['total_sequences']}")
    print(f"   Unique games: {sq['unique_games']}")
    print(f"   Avg actions/level: {sq['avg_actions']:.0f}")
    print(f"   Best sequence: {sq['best_sequence']} actions")
    print(f"   Last discovery: {sq['last_discovery']}")

# Pattern discoveries
pattern_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_patterns,
        AVG(occurrence_count) as avg_occurrences,
        MAX(occurrence_count) as max_occurrences,
        AVG(confidence_score) as avg_confidence
    FROM discovered_patterns
""")

if pattern_stats[0]['total_patterns'] > 0:
    pt = pattern_stats[0]
    print(f"\n🔍 PATTERN DISCOVERY:")
    print(f"   Patterns discovered: {pt['total_patterns']}")
    print(f"   Avg occurrences: {pt['avg_occurrences']:.1f}")
    print(f"   Max occurrences: {pt['max_occurrences']}")
    print(f"   Avg confidence: {pt['avg_confidence']:.3f}")

# Error analysis
error_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_errors,
        COUNT(DISTINCT SUBSTR(message, 1, 100)) as unique_errors
    FROM system_logs
    WHERE level = 'ERROR' AND timestamp > '2025-10-31 15:00:00'
""")

if error_stats:
    print(f"\n⚠️  ERROR SUMMARY:")
    print(f"   Total errors: {error_stats[0]['total_errors']}")
    print(f"   Unique error types: {error_stats[0]['unique_errors']}")

# Critical errors
critical_errors = db.execute_query("""
    SELECT SUBSTR(message, 1, 100) as error_msg, COUNT(*) as count
    FROM system_logs
    WHERE level = 'ERROR' AND timestamp > '2025-10-31 15:00:00'
    GROUP BY SUBSTR(message, 1, 100)
    ORDER BY count DESC
    LIMIT 5
""")

if critical_errors:
    print(f"\n   Top 5 error types:")
    for err in critical_errors:
        print(f"      {err['count']:>6}x: {err['error_msg'][:60]}")

# Recent activity
print(f"\n📍 CURRENT STATUS:")
recent_activity = db.execute_query("""
    SELECT MAX(timestamp) as last_log
    FROM system_logs
    WHERE timestamp > datetime('now', '-30 minutes')
""")

if recent_activity[0]['last_log']:
    print(f"   Last activity: {recent_activity[0]['last_log']}")
    print(f"   Status: ⚠️  Evolution appears to have stopped")
else:
    print(f"   Status: ✅ Evolution running")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)

# Check if API client is broken
api_errors = db.execute_query("""
    SELECT COUNT(*) as count
    FROM system_logs
    WHERE level = 'ERROR' 
      AND message LIKE '%NoneType%request%'
      AND timestamp > '2025-10-31 15:00:00'
""")

if api_errors[0]['count'] > 1000:
    print(f"\n❌ CRITICAL: API client failure ({api_errors[0]['count']} errors)")
    print(f"   Error: 'NoneType' object has no attribute 'request'")
    print(f"   Cause: API client (self.client) is None")
    print(f"   Impact: All game creation and actions failing")
    print(f"   Fix needed: Initialize API client properly")

# Check pattern storage
pattern_errors = db.execute_query("""
    SELECT COUNT(*) as count
    FROM system_logs
    WHERE level = 'ERROR' 
      AND message LIKE '%last_seen_at%'
      AND timestamp > '2025-10-31 15:00:00'
""")

if pattern_errors[0]['count'] > 0:
    print(f"\n⚠️  Pattern storage error ({pattern_errors[0]['count']} errors)")
    print(f"   Error: no such column: last_seen_at")
    print(f"   Status: FIXED (changed to last_validated)")
    print(f"   Impact: Pattern learning partially blocked")

print("\n")
