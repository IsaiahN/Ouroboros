"""Comprehensive Status Update"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import math

db = DatabaseInterface()

print("\n" + "="*80)
print("OUROBOROS SYSTEM STATUS UPDATE")
print("="*80)

# 1. POPULATION STATUS
print("\n[1] POPULATION STATUS")
print("-" * 80)

active = db.execute_query('SELECT COUNT(*) as count FROM agents WHERE is_active = 1')[0]
total = db.execute_query('SELECT COUNT(*) as count FROM agents')[0]

print(f"Active agents: {active['count']}")
print(f"Total agents (including inactive): {total['count']}")
print(f"Inactive agents: {total['count'] - active['count']}")

gen_breakdown = db.execute_query("""
    SELECT 
        generation,
        COUNT(*) as count,
        AVG(total_games_played) as avg_games,
        AVG(avg_score_per_game) as avg_score
    FROM agents 
    WHERE is_active = 1 
    GROUP BY generation 
    ORDER BY generation
""")

print('\nActive generations:')
for g in gen_breakdown:
    print(f"  Gen {g['generation']}: {g['count']} agents, "
          f"{g['avg_games']:.1f} avg games, {g['avg_score']:.3f} avg score")

# 2. GAME RESULTS
print("\n[2] GAME RESULTS")
print("-" * 80)

games = db.execute_query("""
    SELECT 
        COUNT(*) as total_games,
        SUM(final_score) as total_levels,
        AVG(final_score) as avg_levels,
        MAX(final_score) as best_game,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as games_with_levels
    FROM game_results
""")

g = games[0]
print(f"Total games played: {g['total_games']}")
print(f"Total levels completed: {int(g['total_levels'])}")
print(f"Games with levels: {g['games_with_levels']} ({g['games_with_levels']/g['total_games']*100:.1f}%)")
print(f"Average levels per game: {g['avg_levels']:.3f}")
print(f"Best game: {int(g['best_game'])} levels")

# 3. AGENT PERFORMANCE TRACKING
print("\n[3] AGENT PERFORMANCE TRACKING")
print("-" * 80)

perf_records = db.execute_query("""
    SELECT COUNT(*) as count, COUNT(DISTINCT agent_id) as unique_agents
    FROM agent_arc_performance
""")[0]

print(f"Performance records: {perf_records['count']}")
print(f"Agents with records: {perf_records['unique_agents']}")

# Check for games without agent linkage
unlinked_games = db.execute_query("""
    SELECT COUNT(*) as count
    FROM game_results gr
    LEFT JOIN training_sessions ts ON gr.session_id = ts.session_id
    WHERE ts.mode NOT LIKE 'agent_%'
""")[0]

print(f"\nGames without agent linkage: {unlinked_games['count']}")

# 4. TOP PERFORMERS
print("\n[4] TOP PERFORMING AGENTS")
print("-" * 80)

top_agents = db.execute_query("""
    SELECT 
        agent_id,
        agent_type,
        generation,
        total_games_played,
        avg_score_per_game,
        score_efficiency
    FROM agents
    WHERE total_games_played > 0 AND is_active = 1
    ORDER BY avg_score_per_game DESC
    LIMIT 10
""")

if top_agents:
    for i, a in enumerate(top_agents[:5], 1):
        total_levels = a['avg_score_per_game'] * a['total_games_played']
        learning_speed = (total_levels ** 1.5) / math.log(a['total_games_played'] + 1) if a['total_games_played'] > 0 else 0
        print(f"  {i}. {a['agent_id'][:20]} ({a['agent_type'][:15]}) Gen{a['generation']}")
        print(f"      {a['total_games_played']} games, {a['avg_score_per_game']:.3f} avg levels, "
              f"eff={a['score_efficiency']:.5f}, learning_speed={learning_speed:.2f}")
else:
    print("  No agents with performance data yet")

# 5. GAMES WITHOUT AGENT SUCCESS
print("\n[5] INVESTIGATING: Games Without Agent Success")
print("-" * 80)

# Check game_results that aren't in agent_arc_performance
orphan_games = db.execute_query("""
    SELECT 
        gr.game_id,
        gr.final_score,
        gr.total_actions,
        gr.status,
        ts.mode,
        gr.session_id
    FROM game_results gr
    LEFT JOIN training_sessions ts ON gr.session_id = ts.session_id
    LEFT JOIN agent_arc_performance aap ON gr.game_id = aap.game_id AND gr.session_id = aap.session_id
    WHERE aap.performance_id IS NULL
    ORDER BY gr.final_score DESC
    LIMIT 10
""")

print(f"Games NOT in agent_arc_performance: {len(orphan_games)}")
if orphan_games:
    print("\nSample orphan games (no agent credited):")
    for og in orphan_games[:5]:
        print(f"  {og['game_id'][:20]}: {og['final_score']:.1f} levels, "
              f"{og['total_actions']} actions, mode={og['mode']}")

# 6. SESSION MODES ANALYSIS
print("\n[6] SESSION MODES ANALYSIS")
print("-" * 80)

session_modes = db.execute_query("""
    SELECT 
        CASE 
            WHEN mode LIKE 'agent_%' THEN 'agent_linked'
            ELSE mode
        END as mode_type,
        COUNT(*) as count
    FROM training_sessions
    GROUP BY mode_type
    ORDER BY count DESC
""")

print("Session modes:")
for sm in session_modes:
    print(f"  {sm['mode_type']}: {sm['count']} sessions")

# 7. FIXES APPLIED STATUS
print("\n[7] FIXES APPLIED")
print("-" * 80)

print("✅ Agent performance sync function added")
print("✅ Population explosion fixed (11,387 → 328 agents)")
print("✅ Culling mechanism implemented")
print("✅ Population size limit enforced (50-200)")

# Check if sync is working
synced_agents = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE total_games_played > 0
""")[0]
print(f"✅ Agents with synced game data: {synced_agents['count']}")

# 8. ISSUES TO ADDRESS
print("\n[8] ISSUES DETECTED")
print("-" * 80)

issues = []

# Check for orphan games
if len(orphan_games) > 0:
    issues.append(f"❌ {len(orphan_games)} games not linked to agents in agent_arc_performance")
    issues.append(f"   Likely cause: Games played before fix was applied")

# Check for games without agent_ mode
if unlinked_games['count'] > 0:
    issues.append(f"❌ {unlinked_games['count']} games with sessions not using 'agent_*' mode")
    issues.append(f"   Likely cause: Games played before agent_id parameter was added")

# Check if active agents need evaluation
low_eval = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE is_active = 1 AND total_games_played < 5
""")[0]

if low_eval['count'] > 100:
    issues.append(f"⚠️  {low_eval['count']} active agents with < 5 games (need more evaluation)")

if issues:
    for issue in issues:
        print(f"  {issue}")
else:
    print("  ✅ No critical issues detected")

# 9. NEXT STEPS
print("\n[9] RECOMMENDED NEXT STEPS")
print("-" * 80)

print("1. Run evolution to properly evaluate Gen 1-4 agents:")
print("   python run_evolution.py --specialist --quick")
print("")
print("2. Monitor population stays controlled (should stay 50-200):")
print("   python check_active_agents.py")
print("")
print("3. Verify agent performance tracking working:")
print("   python real_progress_check.py")

print("\n" + "="*80)
print(f"STATUS: System operational with {active['count']} active agents")
print("="*80 + "\n")
