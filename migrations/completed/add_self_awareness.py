"""
Add self-awareness logic to GameplayEngine.
Allows agents to query their own performance history and adjust behavior.
"""

SELF_AWARENESS_METHOD = '''
    def _get_agent_self_awareness(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent's self-awareness data from performance history (Task #6).
        Allows agents to know their own performance and adjust behavior.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict with performance metrics and self-awareness insights
        """
        try:
            # Get latest performance snapshot
            perf_data = self.db.execute_query("""
                SELECT *
                FROM agent_performance_history
                WHERE agent_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (agent_id,))
            
            if not perf_data:
                return {
                    'has_history': False,
                    'confidence': 0.5,  # Neutral confidence for new agents
                    'strategy_adjustment': 'explore'  # Default to exploration
                }
            
            perf = perf_data[0]
            
            # Calculate self-awareness metrics
            confidence = min(1.0, perf['win_rate'] + (perf['avg_score'] / 10.0))
            
            # Determine strategy based on performance
            if perf['win_rate'] > 0.7:
                strategy = 'exploit'  # High win rate - exploit what works
            elif perf['win_rate'] < 0.3:
                strategy = 'explore'  # Low win rate - try new approaches
            else:
                strategy = 'balanced'  # Moderate - balance exploration/exploitation
            
            # Check if improving or declining
            if perf['games_played'] >= 5:
                # Get previous snapshot for trend
                prev_data = self.db.execute_query("""
                    SELECT avg_score, win_rate
                    FROM agent_performance_history
                    WHERE agent_id = ?
                    ORDER BY recorded_at DESC
                    LIMIT 1 OFFSET 1
                """, (agent_id,))
                
                if prev_data:
                    score_trend = perf['avg_score'] - prev_data[0]['avg_score']
                    win_trend = perf['win_rate'] - prev_data[0]['win_rate']
                    
                    if score_trend > 0.5 or win_trend > 0.1:
                        trend = 'improving'
                    elif score_trend < -0.5 or win_trend < -0.1:
                        trend = 'declining'
                    else:
                        trend = 'stable'
                else:
                    trend = 'unknown'
            else:
                trend = 'insufficient_data'
            
            return {
                'has_history': True,
                'games_played': perf['games_played'],
                'avg_score': perf['avg_score'],
                'best_score': perf['best_score'],
                'win_rate': perf['win_rate'],
                'avg_efficiency': perf['avg_efficiency'],
                'confidence': confidence,
                'strategy_adjustment': strategy,
                'performance_trend': trend,
                'prestige': perf['prestige_score'],
                'sequences_discovered': perf['sequences_discovered']
            }
            
        except Exception as e:
            logger.error(f"Error getting agent self-awareness: {e}")
            return {
                'has_history': False,
                'confidence': 0.5,
                'strategy_adjustment': 'explore'
            }
    
    def _apply_self_awareness_to_strategy(self, agent_id: str, base_config: Dict) -> Dict:
        """
        Apply self-awareness insights to adjust agent strategy.
        
        Args:
            agent_id: Agent ID
            base_config: Base game configuration
            
        Returns:
            Modified configuration based on self-awareness
        """
        awareness = self._get_agent_self_awareness(agent_id)
        
        if not awareness['has_history']:
            return base_config  # No history, use base config
        
        # Adjust exploration rate based on performance
        if awareness['strategy_adjustment'] == 'explore':
            base_config['exploration_rate'] = min(1.0, base_config.get('exploration_rate', 0.3) * 1.5)
            logger.debug(f"Agent {agent_id}: Increasing exploration (low win rate)")
        elif awareness['strategy_adjustment'] == 'exploit':
            base_config['exploration_rate'] = max(0.1, base_config.get('exploration_rate', 0.3) * 0.5)
            logger.debug(f"Agent {agent_id}: Decreasing exploration (high win rate)")
        
        # Adjust confidence-based parameters
        base_config['confidence_level'] = awareness['confidence']
        
        # Log self-awareness
        if awareness['games_played'] > 0:
            logger.info(f"🧠 Agent {agent_id} self-awareness: "
                       f"Win rate {awareness['win_rate']:.1%}, "
                       f"Avg score {awareness['avg_score']:.2f}, "
                       f"Strategy: {awareness['strategy_adjustment']}, "
                       f"Trend: {awareness['performance_trend']}")
        
        return base_config
'''

import re

FILE_PATH = "core_gameplay.py"

# Read the file
with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Find the _track_agent_performance method and insert self-awareness methods after it
pattern = r'(def _track_agent_performance\(self.*?\n(?:.*?\n)*?.*?logger\.error\(f"Error tracking agent performance: \{e\}"\)\s*\n)'

match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert after _track_agent_performance
    insertion_point = match.end()
    new_content = (
        content[:insertion_point]
        + "\n"
        + SELF_AWARENESS_METHOD
        + "\n"
        + content[insertion_point:]
    )

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ Successfully added self-awareness methods to GameplayEngine")
    print("\nMethods added:")
    print("  - _get_agent_self_awareness(agent_id)")
    print("  - _apply_self_awareness_to_strategy(agent_id, base_config)")
    print("\nUsage:")
    print("  Call _apply_self_awareness_to_strategy() before starting a game")
    print("  to adjust agent behavior based on performance history")
else:
    print("ERROR: Could not find _track_agent_performance method")
    print("Self-awareness methods not added")
    exit(1)
