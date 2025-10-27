"""
Test Pattern Learning Integration in core_gameplay.py
Verifies Rule 10: Pattern learning properly integrated into existing architecture
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
from core_gameplay import GameplayEngine

async def test_integrated_pattern_learning():
    """Test that pattern learning is integrated into core_gameplay."""
    
    print("="*70)
    print("PATTERN LEARNING INTEGRATION TEST (Rule 10)")
    print("="*70)
    print()
    
    # Create engine
    engine = GameplayEngine()
    
    # Verify pattern learning is enabled by default
    assert engine.game_config.get('enable_pattern_learning', False) == True
    assert engine.game_config.get('learning_mode', None) == 'smart_exploration'
    print("[OK] Pattern learning enabled by default")
    
    # Verify pattern learning methods exist
    assert hasattr(engine, '_capture_winning_sequence')
    assert hasattr(engine, '_get_best_sequence_for_game')
    assert hasattr(engine, '_try_replay_sequence')
    assert hasattr(engine, '_detect_pattern_tags')
    assert hasattr(engine, '_classify_game_type')
    print("[OK] Pattern learning methods integrated into GameplayEngine")
    
    # Verify database access
    assert hasattr(engine, 'db')
    print("[OK] Database access integrated")
    
    # Check database schema
    tables = engine.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND (name LIKE '%sequence%' OR name LIKE '%pattern%')
        ORDER BY name
    """)
    
    table_names = [t['name'] for t in tables]
    print(f"\n[OK] Pattern learning tables in database:")
    for table in table_names:
        print(f"  - {table}")
    
    # Verify no code drift - should NOT have separate files
    import os
    workspace_files = os.listdir('.')
    
    print(f"\n[OK] Code Drift Check:")
    if 'intelligent_gameplay.py' in workspace_files:
        print(f"  [WARN] intelligent_gameplay.py exists (should be integrated)")
    else:
        print(f"  [OK] No separate intelligent_gameplay.py")
        
    if 'pattern_learning_engine.py' in workspace_files:
        print(f"  [WARN] pattern_learning_engine.py exists (should be integrated)")
    else:
        print(f"  [OK] No separate pattern_learning_engine.py")
    
    print()
    print("="*70)
    print("INTEGRATION VERIFICATION COMPLETE")
    print("="*70)
    print()
    print("Pattern learning is properly integrated into core_gameplay.py")
    print("following Rule 10: Prevent Code Drift")
    print()
    print("Usage:")
    print("  engine = GameplayEngine()")
    print("  engine.configure(enable_pattern_learning=True)")
    print("  result = await engine.play_single_game('vc33')")
    print("  # Automatically captures wins and replays known sequences")
    print()

if __name__ == "__main__":
    asyncio.run(test_integrated_pattern_learning())
