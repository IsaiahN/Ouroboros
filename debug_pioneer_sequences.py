#!/usr/bin/env python3
"""
Debug why pioneers get 0 levels when optimizers get 2 levels on same game type
"""

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=" * 70)
print("PIONEER vs OPTIMIZER LEVEL COMPLETION DISCREPANCY")
print("=" * 70)

# Get recent games for vc33 showing the discrepancy
vc33_games = db.execute_query("""
    SELECT 
        gr.game_id,
        gr.status,
        gr.final_score,
        gr.level_completions,
        gr.total_actions,
        aap.agent_id
    FROM game_results gr
    LEFT JOIN agent_arc_performance aap ON gr.game_id = aap.game_id AND gr.session_id = aap.session_id
    WHERE gr.game_id LIKE 'vc33%'
    ORDER BY gr.rowid DESC
    LIMIT 20
""")

print("\nRecent vc33 games:")
print("-" * 70)
for game in vc33_games:
    agent_mode_query = db.execute_query("""
        SELECT operating_mode 
        FROM agent_operating_modes 
        WHERE agent_id = ?
        ORDER BY assigned_timestamp DESC
        LIMIT 1
    """, (game['agent_id'],))
    mode = agent_mode_query[0]['operating_mode'] if agent_mode_query else 'unknown'
    
    print(f"{mode:10s} | {game['game_id']}: "
          f"levels={game['level_completions']}, "
          f"score={game['final_score']}, "
          f"actions={game['total_actions']}")

# Check what sequences exist for vc33
print("\n" + "=" * 70)
print("SEQUENCES AVAILABLE FOR vc33")
print("=" * 70)

sequences = db.execute_query("""
    SELECT 
        level_number,
        total_actions,
        total_score,
        COUNT(*) as seq_count,
        MIN(total_actions) as min_actions
    FROM winning_sequences
    WHERE game_id LIKE 'vc33%'
    GROUP BY level_number
    ORDER BY level_number
""")

if sequences:
    print("\nAvailable sequences:")
    for seq in sequences:
        print(f"  Level {seq['level_number']}: "
              f"{seq['seq_count']} sequences, "
              f"min {seq['min_actions']} actions, "
              f"score={seq['total_score']}")
else:
    print("\n✗ NO SEQUENCES FOUND for vc33!")

# Check if pioneers are actually attempting to use sequences
print("\n" + "=" * 70)
print("SEQUENCE VALIDATION ATTEMPTS")
print("=" * 70)

validations = db.execute_query("""
    SELECT 
        agent_id,
        game_id,
        success,
        actions_completed,
        score_achieved
    FROM sequence_validation_attempts
    WHERE game_id LIKE 'vc33%'
    ORDER BY attempt_timestamp DESC
    LIMIT 10
""")

if validations:
    print("\nRecent validation attempts:")
    for val in validations:
        print(f"  {val['game_id']}: "
              f"success={val['success']}, "
              f"actions={val['actions_completed']}, "
              f"score={val['score_achieved']}")
else:
    print("\n✗ NO VALIDATION ATTEMPTS found!")
    print("  → This suggests sequences are NOT being replayed at all!")

print("\n" + "=" * 70)
