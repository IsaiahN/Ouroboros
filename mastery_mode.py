"""
Mastery Mode - Force a specific agent to master a specific game.

This mode repeatedly plays the same game with the same agent until:
1. Game reaches WIN state (full completion)
2. Graceful shutdown is triggered
3. Max attempts reached (configurable safety limit)

Use cases:
- Investigate breakthrough games (like as66)
- Debug specific agent behaviors
- Force knowledge extraction from partial completions

Author: Claude Code (Ouroboros System)
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from database_interface import DatabaseInterface
from game_session_manager import GameSessionManager
from core_gameplay import GameplayEngine
from database_logger import setup_database_logging
from disk_space_monitor import DiskSpaceMonitor
import logging
import signal

logger = logging.getLogger(__name__)


class MasteryMode:
    """
    Dedicated mode for agent mastery of a specific game.
    
    Repeatedly plays game until WIN or shutdown.
    """
    
    def __init__(self, agent_id: str, game_id: str, max_attempts: int = 100, agent_mode: Optional[str] = None):
        """
        Initialize mastery mode.
        
        Args:
            agent_id: Agent to use for mastery
            game_id: Game to master
            max_attempts: Safety limit on attempts (default: 100, use -1 for unlimited)
            agent_mode: Force specific agent mode ('pioneer', 'optimizer', 'exploiter', 'generalist')
        """
        self.agent_id = agent_id
        self.game_id = game_id
        self.disk_monitor = DiskSpaceMonitor()
        self.max_attempts = max_attempts if max_attempts != -1 else float('inf')
        self.agent_mode = agent_mode
        self.db = DatabaseInterface()
        self.is_shutting_down = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info(f"\n🛑 Mastery mode shutdown requested (signal {signum})")
        self.is_shutting_down = True
        
    async def run_mastery_session(self) -> Dict[str, Any]:
        """
        Run mastery session until WIN or shutdown.
        
        Returns:
            Summary dict with results
        """
        setup_database_logging()
        
        logger.info("=" * 80)
        logger.info("🎯 MASTERY MODE INITIATED")
        logger.info("=" * 80)
        logger.info(f"Agent: {self.agent_id}")
        logger.info(f"Game: {self.game_id}")
        logger.info(f"Max Attempts: {'UNLIMITED' if self.max_attempts == float('inf') else self.max_attempts}")
        logger.info(f"Agent Mode: {self.agent_mode or 'AUTO (from database)'}")
        logger.info(f"Goal: Reach WIN state")
        logger.info("=" * 80)
        
        # Get agent info
        agent_info = self.db.get_agent(self.agent_id)
        if not agent_info:
            logger.error(f"❌ Agent {self.agent_id} not found in database")
            return {'success': False, 'error': 'Agent not found'}
        
        # Determine agent mode
        if self.agent_mode:
            actual_mode = self.agent_mode
            logger.info(f"Agent Mode: {actual_mode} (FORCED)")
        else:
            # Get mode from database
            cursor = self.db.execute_query("""
                SELECT operating_mode 
                FROM agent_operating_modes 
                WHERE agent_id = ? 
                ORDER BY assigned_timestamp DESC 
                LIMIT 1
            """, (self.agent_id,))
            actual_mode = cursor[0]['operating_mode'] if cursor else 'generalist'
            logger.info(f"Agent Mode: {actual_mode} (from database)")
        
        logger.info(f"Agent Info:")
        logger.info(f"  Generation: {agent_info.get('generation', 'unknown')}")
        logger.info(f"  Fitness: {agent_info.get('score_efficiency', 0.0):.4f}")
        
        # Track mastery session
        session_start = datetime.now()
        attempts = []
        best_score = 0.0
        best_levels = 0
        win_achieved = False
        
        # Create gameplay engine (includes session manager)
        gameplay_engine = GameplayEngine()
        
        try:
            # Start session
            await gameplay_engine.session_manager.start_session()
            
            attempt_num = 0
            while not self.is_shutting_down and attempt_num < self.max_attempts:
                attempt_num += 1
                
                # Check disk space every 10 attempts
                if attempt_num % 10 == 1:
                    safe, message, stats = self.disk_monitor.check_disk_space()
                    if not safe:
                        logger.critical(message)
                        logger.critical("🚨 ABORTING MASTERY MODE: Disk space critical!")
                        print(f"\n{message}")
                        print("\n🚨 ABORTING: Disk space critical!")
                        print("Run emergency_cleanup_mastery.py to free up space.")
                        break
                    elif attempt_num == 1:
                        logger.info(message)
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🎮 MASTERY ATTEMPT #{attempt_num}/{self.max_attempts}")
                logger.info("=" * 80)
                
                try:
                    # Configure game parameters
                    gameplay_engine.game_config['max_actions_per_level'] = 400
                    gameplay_engine.game_config['max_total_actions'] = 7000
                    gameplay_engine.game_config['agent_id'] = self.agent_id
                    gameplay_engine.game_config['game_id'] = self.game_id
                    gameplay_engine.game_config['enable_pattern_learning'] = True  # CRITICAL: Enable sequence capture
                    
                    # Set agent operating mode
                    if self.agent_mode:
                        gameplay_engine.game_config['agent_operating_mode'] = self.agent_mode
                    else:
                        gameplay_engine.game_config['agent_operating_mode'] = actual_mode
                    
                    # Play the game
                    result = await gameplay_engine.play_single_game(
                        game_id=self.game_id,
                        agent_id=self.agent_id
                    )
                    
                    # Extract results
                    final_state = result.get('final_state', 'UNKNOWN')
                    final_score = result.get('final_score', 0.0)
                    levels_completed = int(final_score)  # Score = levels completed
                    total_actions = result.get('actions_taken', 0)
                    
                    # Track this attempt
                    attempt_data = {
                        'attempt': attempt_num,
                        'state': final_state,
                        'score': final_score,
                        'levels': levels_completed,
                        'actions': total_actions,
                        'timestamp': datetime.now().isoformat()
                    }
                    attempts.append(attempt_data)
                    
                    # Update best scores
                    if final_score > best_score:
                        best_score = final_score
                        logger.info(f"🌟 NEW BEST SCORE: {best_score} (levels: {levels_completed})")
                    
                    if levels_completed > best_levels:
                        best_levels = levels_completed
                        logger.info(f"🏆 NEW BEST LEVELS: {best_levels}")
                    
                    # Check for WIN
                    if final_state == "WIN":
                        win_achieved = True
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("🎉 MASTERY ACHIEVED - WIN STATE REACHED!")
                        logger.info("=" * 80)
                        logger.info(f"Attempts: {attempt_num}")
                        logger.info(f"Final Score: {final_score}")
                        logger.info(f"Levels Completed: {levels_completed}")
                        logger.info(f"Total Actions: {total_actions}")
                        logger.info("=" * 80)
                        break
                    
                    # Report attempt result
                    logger.info(f"Attempt #{attempt_num} Result:")
                    logger.info(f"  State: {final_state}")
                    logger.info(f"  Score: {final_score}")
                    logger.info(f"  Levels: {levels_completed}")
                    logger.info(f"  Actions: {total_actions}")
                    
                    # Small delay between attempts
                    if not self.is_shutting_down and attempt_num < self.max_attempts:
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Attempt #{attempt_num} error: {e}")
                    attempts.append({
                        'attempt': attempt_num,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Continue to next attempt
                    await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Mastery session error: {e}")
            return {
                'success': False,
                'error': str(e),
                'attempts': attempts
            }
        
        # Summary
        session_duration = (datetime.now() - session_start).total_seconds()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 MASTERY SESSION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Agent: {self.agent_id}")
        logger.info(f"Game: {self.game_id}")
        logger.info(f"Duration: {session_duration:.1f} seconds")
        logger.info(f"Attempts: {len(attempts)}")
        logger.info(f"Best Score: {best_score}")
        logger.info(f"Best Levels: {best_levels}")
        logger.info(f"Win Achieved: {'YES ✅' if win_achieved else 'NO ❌'}")
        
        if self.is_shutting_down:
            logger.info(f"Stopped: Graceful shutdown")
        elif attempt_num >= self.max_attempts:
            logger.info(f"Stopped: Max attempts reached ({self.max_attempts})")
        
        logger.info("=" * 80)
        
        return {
            'success': True,
            'win_achieved': win_achieved,
            'attempts': len(attempts),
            'best_score': best_score,
            'best_levels': best_levels,
            'duration_seconds': session_duration,
            'attempt_details': attempts
        }


async def main():
    """Main entry point for mastery mode."""
    if len(sys.argv) < 3:
        print("Usage: python mastery_mode.py <agent_id> <game_id> [max_attempts] [agent_mode]")
        print("")
        print("Arguments:")
        print("  agent_id      - Agent to use (e.g., offspring_2d969449)")
        print("  game_id       - Game to master (e.g., as66-821a4dcad9c2)")
        print("  max_attempts  - Max attempts (default: 100, use -1 for unlimited)")
        print("  agent_mode    - Force mode: pioneer, optimizer, exploiter, generalist")
        print("")
        print("Examples:")
        print("  # Basic: 100 attempts, auto mode")
        print("  python mastery_mode.py offspring_4dc42110 as66-821a4dcad9c2")
        print("")
        print("  # Unlimited attempts")
        print("  python mastery_mode.py offspring_4dc42110 as66-821a4dcad9c2 -1")
        print("")
        print("  # Force pioneer mode with 50 attempts")
        print("  python mastery_mode.py offspring_4dc42110 as66-821a4dcad9c2 50 pioneer")
        print("")
        print("  # Unlimited + force generalist mode")
        print("  python mastery_mode.py offspring_4dc42110 as66-821a4dcad9c2 -1 generalist")
        print("")
        print("Press Ctrl+C to stop gracefully")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    game_id = sys.argv[2]
    max_attempts = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    agent_mode = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Validate agent_mode if provided
    valid_modes = ['pioneer', 'optimizer', 'exploiter', 'generalist']
    if agent_mode and agent_mode not in valid_modes:
        print(f"Error: Invalid agent_mode '{agent_mode}'")
        print(f"Valid modes: {', '.join(valid_modes)}")
        sys.exit(1)
    
    mastery = MasteryMode(agent_id, game_id, max_attempts, agent_mode)
    result = await mastery.run_mastery_session()
    
    # Exit with appropriate code
    sys.exit(0 if result.get('win_achieved') else 1)


if __name__ == "__main__":
    asyncio.run(main())
