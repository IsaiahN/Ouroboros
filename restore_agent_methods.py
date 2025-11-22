import os

file_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\database_interface.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We will append the missing methods to the end of the file, but inside the class.
# The file ends with the log_event method. We need to find the end of that method and append the new methods.

# Content to append
missing_methods = """
    # ========================================================================
    # OUROBOROS EXTENSIONS
    # ========================================================================

    def execute_script(self, script: str):
        \"\"\"Execute SQL script for schema extensions.\"\"\"
        with self._get_connection() as conn:
            conn.executescript(script)
            conn.commit()

    def store_agent(self, agent_data: dict):
        \"\"\"Store agent in database.\"\"\"
        with self._get_connection() as conn:
            conn.execute(\"\"\"
                INSERT OR REPLACE INTO agents (
                    agent_id, agent_type, genome, epigenetics, generation, parent_ids,
                    specialization, created_at, is_active, total_games_played,
                    total_games_won, total_score_achieved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                agent_data['agent_id'],
                agent_data['agent_type'],
                agent_data['genome'],
                agent_data.get('epigenetics'),
                agent_data.get('generation', 0),
                agent_data.get('parent_ids', '[]'),
                agent_data['specialization'],
                agent_data.get('created_at', datetime.now().isoformat()),
                agent_data.get('is_active', True),
                agent_data.get('total_games_played', 0),
                agent_data.get('total_games_won', 0),
                agent_data.get('total_score_achieved', 0.0)
            ))
            conn.commit()

    def get_active_agents(self) -> list:
        \"\"\"Get all active agents.\"\"\"
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def get_active_agent_count(self) -> int:
        \"\"\"Get count of active agents.\"\"\"
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
            return cursor.fetchone()[0]

    def get_agent(self, agent_id: str) -> dict:
        \"\"\"Get agent by ID.\"\"\"
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def agent_exists(self, agent_id: str) -> bool:
        \"\"\"Check if agent exists.\"\"\"
        return self.get_agent(agent_id) is not None

    def update_agent(self, agent_id: str, agent_data: dict):
        \"\"\"Update agent data.\"\"\"
        with self._get_connection() as conn:
            conn.execute(\"\"\"
                UPDATE agents SET
                    agent_type = ?, genome = ?, generation = ?, parent_ids = ?,
                    specialization = ?, is_active = ?, total_games_played = ?,
                    total_games_won = ?, total_score_achieved = ?
                WHERE agent_id = ?
            \"\"\", (
                agent_data['agent_type'],
                agent_data['genome'],
                agent_data.get('generation', 0),
                agent_data.get('parent_ids', '[]'),
                agent_data['specialization'],
                agent_data.get('is_active', True),
                agent_data.get('total_games_played', 0),
                agent_data.get('total_games_won', 0),
                agent_data.get('total_score_achieved', 0.0),
                agent_id
            ))
            conn.commit()

    def store_arc_reward_data(self, agent_id: str, reward_data: dict):
        \"\"\"Store ARC reward data for agent.\"\"\"
        with self._get_connection() as conn:
            conn.execute(\"\"\"
                INSERT INTO agent_arc_performance (
                    performance_id, agent_id, game_id, session_id, game_timestamp,
                    final_score, win_score_threshold, win_achieved, total_actions,
                    score_efficiency, win_proximity, level_progressions,
                    strategy_used, genome_config, base_reward, win_bonus,
                    efficiency_bonus, level_progression_bonus, total_evolutionary_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                str(uuid.uuid4()),
                agent_id,
                reward_data.get('game_id', ''),
                reward_data.get('session_id', ''),
                datetime.now().isoformat(),
                reward_data.get('arc_native_rewards', {}).get('final_score', 0.0),
                reward_data.get('arc_native_rewards', {}).get('win_score_threshold', 0.0),
                reward_data.get('arc_native_rewards', {}).get('game_win', False),
                reward_data.get('arc_native_rewards', {}).get('total_actions', 0),
                reward_data.get('derived_metrics', {}).get('score_efficiency', 0.0),
                reward_data.get('derived_metrics', {}).get('win_proximity', 0.0),
                reward_data.get('arc_native_rewards', {}).get('level_progressions', 0),
                'agent_strategy',
                json.dumps({}),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('base_reward', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('win_bonus', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('efficiency_bonus', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('level_bonus', 0.0),
                reward_data.get('total_evolutionary_reward', 0.0)
            ))
            conn.commit()

    def get_agent_arc_performance(self, agent_id: str) -> dict:
        \"\"\"Get agent's ARC performance summary.\"\"\"
        with self._get_connection() as conn:
            cursor = conn.execute(\"\"\"
                SELECT
                    COUNT(*) as total_games_played,
                    SUM(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END) as total_games_won,
                    AVG(final_score) as avg_score_per_game,
                    AVG(score_efficiency) as score_efficiency,
                    SUM(level_progressions) as level_progressions_detected,
                    AVG(total_evolutionary_reward) as avg_evolutionary_reward
                FROM agent_arc_performance
                WHERE agent_id = ?
            \"\"\", (agent_id,))

            row = cursor.fetchone()
            if not row or row[0] == 0:
                return None

            data = dict(row)
            data['win_rate'] = data['total_games_won'] / max(data['total_games_played'], 1)
            data['consistency_score'] = 0.5  # Placeholder
            data['level_progression_rate'] = data['level_progressions_detected'] / max(data['total_games_played'], 1)

            return data

    def sync_agent_performance_to_agents_table(self):
        \"\"\"
        Sync agent_arc_performance data to agents table.
        Updates total_games_played, total_games_won, avg_score_per_game, score_efficiency.
        Call this after each evaluation cycle.
        \"\"\"
        with self._get_connection() as conn:
            # Update all agents from their performance data
            conn.execute(\"\"\"
                UPDATE agents
                SET 
                    total_games_played = (
                        SELECT COUNT(*) 
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    total_games_won = (
                        SELECT SUM(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    avg_score_per_game = (
                        SELECT AVG(final_score)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    score_efficiency = (
                        SELECT AVG(score_efficiency)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    )
                WHERE EXISTS (
                    SELECT 1 FROM agent_arc_performance 
                    WHERE agent_id = agents.agent_id
                )
            \"\"\")
            conn.commit()
            
            # Return count of agents updated
            cursor = conn.execute(\"\"\"
                SELECT COUNT(DISTINCT agent_id) 
                FROM agent_arc_performance
            \"\"\")
            return cursor.fetchone()[0]

    def get_population_performance_data(self) -> list:
        \"\"\"Get performance data for all agents.\"\"\"
        agents = self.get_active_agents()
        for agent in agents:
            performance = self.get_agent_arc_performance(agent['agent_id'])
            if performance:
                agent.update(performance)
            else:
                # Set defaults for agents with no performance data
                agent.update({
                    'total_games_played': 0,
                    'total_games_won': 0,
                    'win_rate': 0.0,
                    'avg_score_per_game': 0.0,
                    'score_efficiency': 0.0,
                    'level_progressions_detected': 0
                })
        return agents

    def store_evolution_decision(self, evolution_strategy: dict, performance_data: dict):
        \"\"\"Store Claude Code evolution decision.\"\"\"
        with self._get_connection() as conn:
            conn.execute(\"\"\"
                INSERT INTO claude_evolution_decisions (
                    decision_id, generation, population_analysis, evolution_strategy,
                    reasoning, agents_created, agents_retired, mutations_applied,
                    crossovers_performed, expected_improvement_rate, target_win_rate,
                    strategy_focus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                str(uuid.uuid4()),
                evolution_strategy.get('generation', 0),
                json.dumps(performance_data),
                json.dumps(evolution_strategy),
                evolution_strategy.get('reasoning', ''),
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                evolution_strategy.get('target_win_rate', 0.0),
                evolution_strategy.get('target_win_rate', 0.0),
                evolution_strategy.get('focus', 'balanced')
            ))
            conn.commit()
"""

# Find the last method (log_event) and append after it
last_method_signature = "def log_event(self, logger_name: str, level: str, message: str, **kwargs):"
if last_method_signature in content:
    # Find the end of the log_event method. It ends with conn.commit() and some indentation.
    # We'll search for the last occurrence of conn.commit() inside that method block
    # Actually, simpler: just append to the end of the file, assuming the file ends correctly.
    # But we need to make sure we are inside the class.
    # The file seems to end with log_event.
    
    # Let's just append it to the end of the file. The indentation in missing_methods handles the class membership.
    new_content = content + missing_methods
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully restored agent methods to database_interface.py")
else:
    print("Could not find log_event method to append after.")
