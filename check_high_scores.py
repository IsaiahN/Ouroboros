import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check for scores of 4.0 or higher
print("=" * 80)
print("GAMES WITH SCORES OF 4.0 OR HIGHER")
print("=" * 80)

high_scores = db.execute_query("""
    SELECT 
        game_id,
        final_score,
        total_actions,
        datetime(end_time) as completed,
        session_id
    FROM game_results 
    WHERE final_score >= 4.0
    ORDER BY final_score DESC, end_time DESC
    LIMIT 50
""")

if high_scores:
    print(f"\nFound {len(high_scores)} games with scores >= 4.0\n")
    for game in high_scores:
        print(f"  {game['game_id']}: score={game['final_score']:.1f}, "
              f"actions={game['total_actions']}, "
              f"completed={game['completed']}")
else:
    print("\nNo games found with scores >= 4.0")

# Check highest scores overall
print("\n" + "=" * 80)
print("TOP 20 HIGHEST SCORING GAMES (ALL TIME)")
print("=" * 80)

top_scores = db.execute_query("""
    SELECT 
        game_id,
        final_score,
        total_actions,
        datetime(end_time) as completed,
        session_id
    FROM game_results 
    WHERE final_score > 0
    ORDER BY final_score DESC, end_time DESC
    LIMIT 20
""")

if top_scores:
    print(f"\nTop {len(top_scores)} scoring games:\n")
    for i, game in enumerate(top_scores, 1):
        print(f"  #{i}. {game['game_id']}: score={game['final_score']:.1f}, "
              f"actions={game['total_actions']}, "
              f"completed={game['completed']}")
else:
    print("\nNo games found with scores > 0")

print("\n" + "=" * 80)
