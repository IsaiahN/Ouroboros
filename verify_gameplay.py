#!/usr/bin/env python3
"""
Gameplay Verification Tool
==========================

Quick verification script for testing gameplay changes.
NOT a test file (Rule 5 compliant) - this is a diagnostic TOOL.

Usage:
  python verify_gameplay.py <game_id>
  python verify_gameplay.py --quick  # Test abstraction integration only
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import sys
from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface

async def verify_abstraction_integration():
    """Quick test: Verify abstraction engine is working."""
    print("\n🔍 VERIFICATION: Abstraction Integration")
    print("=" * 60)
    
    try:
        # Initialize gameplay engine
        engine = GameplayEngine()
        
        # Check abstraction engine initialized
        if engine.abstraction_engine is None:
            print("❌ FAIL: Abstraction engine not initialized")
            return False
        else:
            print("✅ PASS: Abstraction engine initialized")
        
        # Check action history tracking
        if 'current_actions' not in engine.game_config:
            print("⚠️  WARN: current_actions not in game_config (will be added on game start)")
        else:
            print("✅ PASS: Action history tracking ready")
        
        # Check abstraction config
        from abstraction_config import is_abstraction_enabled
        if is_abstraction_enabled():
            print("✅ PASS: Abstraction enabled in config")
        else:
            print("❌ FAIL: Abstraction disabled in config")
            return False
        
        print("\n✅ All abstraction checks passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_single_game(game_id: str):
    """Verify gameplay on a specific game."""
    print(f"\n🎮 VERIFICATION: Playing {game_id}")
    print("=" * 60)
    
    try:
        engine = GameplayEngine()
        engine.configure(
            max_actions_per_level=100,  # Quick test
            max_total_actions=300,
            enable_pattern_learning=True
        )
        
        result = await engine.play_single_game(game_id)
        
        print(f"\n📊 RESULTS:")
        print(f"  Final Score: {result.get('final_score', 0)}")
        print(f"  Actions Taken: {result.get('actions_taken', 0)}")
        print(f"  Win: {result.get('win', False)}")
        
        # Check if abstraction was used
        db = DatabaseInterface()
        metrics = db.execute_query("""
            SELECT abstraction_matched, abstraction_score
            FROM abstraction_metrics
            WHERE game_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (game_id,))
        
        if metrics and metrics[0]['abstraction_matched']:
            print(f"  🧠 Abstraction Used: Score {metrics[0]['abstraction_score']:.2f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--quick':
            success = await verify_abstraction_integration()
            sys.exit(0 if success else 1)
        else:
            game_id = sys.argv[1]
            result = await verify_single_game(game_id)
            sys.exit(0 if result and result.get('final_score', 0) > 0 else 1)
    else:
        print("Usage:")
        print("  python verify_gameplay.py <game_id>")
        print("  python verify_gameplay.py --quick")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
