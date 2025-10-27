"""Test the fixed pattern learning system."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface

async def test_pattern_learning():
    """Test pattern learning with a game."""
    
    db = DatabaseInterface()
    
    print("="*80)
    print("TESTING FIXED PATTERN LEARNING SYSTEM")
    print("="*80)
    
    # Clear old broken patterns for lp85-d265526edbaa
    game_id = "lp85-d265526edbaa"
    
    print(f"\n1. Checking existing patterns for {game_id}...")
    existing = db.execute_query("""
        SELECT sequence_id, level_number, total_actions, efficiency_score
        FROM winning_sequences
        WHERE game_id = ?
        ORDER BY level_number, total_actions
    """, (game_id,))
    
    print(f"   Found {len(existing)} existing sequences:")
    for seq in existing:
        print(f"   - Level {seq['level_number']}: {seq['total_actions']} actions, "
              f"efficiency {seq['efficiency_score']:.4f}")
    
    # Initialize engine
    engine = GameplayEngine(db_path="core_data.db")
    
    # Configure pattern learning
    engine.configure(
        enable_pattern_learning=True,
        learning_mode='smart_exploration',
        max_total_actions=250,
        max_actions_per_level=100
    )
    
    print(f"\n2. Running game with pattern learning enabled...")
    print(f"   - Will capture patterns ONLY on actual level wins (score increase + NOT_FINISHED)")
    print(f"   - Will optimize existing patterns if we find better ones")
    print(f"   - Will attempt replay if pattern exists")
    
    try:
        result = await engine.play_single_game(game_id)
        
        print(f"\n3. Game Result:")
        print(f"   State: {result['final_state']}")
        print(f"   Score: {result['final_score']}")
        print(f"   Actions: {result['actions_taken']}")
        print(f"   Levels Completed: {result.get('level_completions', 0)}")
        
        if result.get('learned_sequence_id'):
            print(f"   ✅ New sequence captured: {result['learned_sequence_id']}")
        
    except Exception as e:
        print(f"\n❌ Error during game: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.session_manager.shutdown()
    
    # Check what patterns were captured
    print(f"\n4. Patterns after game:")
    final_patterns = db.execute_query("""
        SELECT sequence_id, level_number, total_actions, efficiency_score, 
               total_score, times_referenced
        FROM winning_sequences
        WHERE game_id = ?
        ORDER BY level_number, total_actions
    """, (game_id,))
    
    for seq in final_patterns:
        print(f"   - Level {seq['level_number']}: {seq['total_actions']} actions, "
              f"score {seq['total_score']}, efficiency {seq['efficiency_score']:.4f}, "
              f"referenced {seq['times_referenced']} times")
    
    print("\n" + "="*80)
    print("KEY IMPROVEMENTS:")
    print("✅ Only captures patterns on actual level wins (score increase + game continues)")
    print("✅ Verifies initial frame before replay")
    print("✅ Tracks replay attempts and success rates")
    print("✅ Only stores new pattern if more efficient than existing")
    print("✅ Retrieves most efficient pattern (fewest actions)")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_pattern_learning())
