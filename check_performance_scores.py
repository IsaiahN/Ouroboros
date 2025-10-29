import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check agent_arc_performance table for high scores
print("=" * 80)
print("HIGH SCORES FROM agent_arc_performance TABLE")
print("=" * 80)

high_performance = db.execute_query("""
    SELECT 
        game_id,
        agent_id,
        session_id,
        final_score,
        total_actions,
        win_achieved,
        datetime(game_timestamp) as played
    FROM agent_arc_performance 
    WHERE final_score >= 3.0
    ORDER BY final_score DESC, game_timestamp DESC
    LIMIT 50
""")

if high_performance:
    print(f"\nFound {len(high_performance)} performances with scores >= 3.0\n")
    for perf in high_performance:
        win_status = "WIN" if perf['win_achieved'] else "NOT_WIN"
        print(f"  {perf['game_id']}: score={perf['final_score']:.1f}, "
              f"actions={perf['total_actions']}, "
              f"status={win_status}, "
              f"agent={perf['agent_id'][:12]}, "
              f"played={perf['played']}")
else:
    print("\nNo performances found with scores >= 3.0")

# Check for that specific game you mentioned
print("\n" + "=" * 80)
print("CHECKING SPECIFIC GAME: vc33-6ae7bf49eea5")
print("=" * 80)

specific_game = db.execute_query("""
    SELECT 
        game_id,
        agent_id,
        session_id,
        final_score,
        total_actions,
        win_achieved,
        datetime(game_timestamp) as played
    FROM agent_arc_performance 
    WHERE game_id = 'vc33-6ae7bf49eea5'
    ORDER BY final_score DESC, game_timestamp DESC
    LIMIT 10
""")

if specific_game:
    print(f"\nFound {len(specific_game)} performances for vc33-6ae7bf49eea5:\n")
    for perf in specific_game:
        win_status = "WIN" if perf['win_achieved'] else "NOT_WIN"
        print(f"  Score: {perf['final_score']:.1f}, "
              f"Actions: {perf['total_actions']}, "
              f"Status: {win_status}, "
              f"Agent: {perf['agent_id'][:12]}, "
              f"Session: {perf['session_id'][:20]}, "
              f"Played: {perf['played']}")
else:
    print("\nNo performances found for vc33-6ae7bf49eea5")

# Check all scores >= 2.0
print("\n" + "=" * 80)
print("TOP 20 SCORES FROM agent_arc_performance (>= 2.0)")
print("=" * 80)

top_performances = db.execute_query("""
    SELECT 
        game_id,
        agent_id,
        final_score,
        total_actions,
        win_achieved,
        datetime(game_timestamp) as played
    FROM agent_arc_performance 
    WHERE final_score >= 2.0
    ORDER BY final_score DESC, game_timestamp DESC
    LIMIT 20
""")

if top_performances:
    print(f"\nTop {len(top_performances)} performances:\n")
    for i, perf in enumerate(top_performances, 1):
        win_status = "WIN" if perf['win_achieved'] else ""
        print(f"  #{i}. {perf['game_id']}: score={perf['final_score']:.1f}, "
              f"actions={perf['total_actions']}, "
              f"{win_status}, "
              f"agent={perf['agent_id'][:12]}, "
              f"played={perf['played']}")

print("\n" + "=" * 80)
