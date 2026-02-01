"""
Add _track_agent_performance method to GameplayEngine class.
This method records agent performance metrics to the agent_performance_history table.
"""

PERFORMANCE_TRACKING_METHOD = '''
    def _track_agent_performance(self, agent_id: str, game_id: str,
                                final_score: float, actions_taken: int,
                                level_completions: int, win: bool,
                                duration_seconds: float):
        """
        Track agent performance metrics for self-model (Task #6).
        Records performance to agent_performance_history table.

        Args:
            agent_id: Agent ID
            game_id: Game that was played
            final_score: Final score achieved
            actions_taken: Total actions taken
            level_completions: Levels completed
            win: Whether the game was won
            duration_seconds: Game duration
        """
        try:
            # Get current performance snapshot
            current = self.db.execute_query("""
                SELECT games_played, total_score, total_actions,
                       total_levels_completed, wins, best_score, worst_score
                FROM agent_performance_history
                WHERE agent_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (agent_id,))

            if current:
                # Update cumulative metrics
                games_played = current[0]['games_played'] + 1
                total_score = current[0]['total_score'] + final_score
                total_actions = current[0]['total_actions'] + actions_taken
                total_levels = current[0]['total_levels_completed'] + level_completions
                wins = current[0]['wins'] + (1 if win else 0)
                best_score = max(current[0]['best_score'], final_score)
                worst_score = min(current[0]['worst_score'], final_score) if current[0]['worst_score'] > 0 else final_score
            else:
                # First game for this agent
                games_played = 1
                total_score = final_score
                total_actions = actions_taken
                total_levels = level_completions
                wins = 1 if win else 0
                best_score = final_score
                worst_score = final_score

            # Calculate averages
            avg_score = total_score / games_played
            avg_actions = total_actions / games_played
            avg_levels = total_levels / games_played
            avg_efficiency = total_score / total_actions if total_actions > 0 else 0.0
            win_rate = wins / games_played

            # Get prestige score
            prestige_data = self.db.execute_query("""
                SELECT prestige_score
                FROM agents
                WHERE agent_id = ?
            """, (agent_id,))
            prestige_score = prestige_data[0]['prestige_score'] if prestige_data else 0.0

            # Get sequence contribution
            sequences_discovered = self.db.execute_query("""
                SELECT COUNT(*) as cnt
                FROM winning_sequences
                WHERE agent_id = ?
            """, (agent_id,))[0]['cnt']

            sequences_validated = self.db.execute_query("""
                SELECT COUNT(*) as cnt
                FROM sequence_validation_attempts
                WHERE agent_id = ?
            """, (agent_id,))[0]['cnt'] if self.db.execute_query("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sequence_validation_attempts'
            """) else 0

            # Insert performance snapshot
            self.db.execute_query("""
                INSERT INTO agent_performance_history (
                    agent_id, games_played, total_score, avg_score,
                    best_score, worst_score, total_levels_completed,
                    avg_levels_per_game, total_actions, avg_actions_per_game,
                    avg_efficiency, wins, win_rate, sequences_discovered,
                    sequences_validated, prestige_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (agent_id, games_played, total_score, avg_score,
                  best_score, worst_score, total_levels, avg_levels,
                  total_actions, avg_actions, avg_efficiency, wins,
                  win_rate, sequences_discovered, sequences_validated,
                  prestige_score))

            self.db.checkpoint_wal()

            logger.debug(f"[STATS] Agent {agent_id} performance: {games_played} games, "
                        f"avg score {avg_score:.2f}, win rate {win_rate:.1%}")

        except Exception as e:
            logger.error(f"Error tracking agent performance: {e}")
'''

# Read the file
FILE_PATH = "core_gameplay.py"
with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Find a good insertion point - after _track_game_diversity method
pattern = r'(def _track_game_diversity\(self.*?\n(?:.*?\n)*?.*?logger\.error\(f"Error tracking game diversity: \{e\}"\)\s*\n)'

import re

match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert after _track_game_diversity
    insertion_point = match.end()
    new_content = (
        content[:insertion_point]
        + "\n"
        + PERFORMANCE_TRACKING_METHOD
        + "\n"
        + content[insertion_point:]
    )

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("[OK] Successfully added _track_agent_performance method to GameplayEngine")
else:
    print("ERROR: Could not find insertion point after _track_game_diversity")
    exit(1)
