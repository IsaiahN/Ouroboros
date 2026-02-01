import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

"""
Meta-Learning Curriculum - Intelligent game selection for generalization
=========================================================================

Implements 4-stage curriculum for teaching agents to generalize:
1. Specialization: Master one game deeply (build foundation)
2. Near Transfer: Transfer skills to similar game (test transfer)
3. Diversification: Learn from diverse set (build repertoire)
4. Generalization: Zero-shot on new games (true AGI test)

Following Rule 2: All progress tracked in database
Following Rule 3: Integrates with existing gameplay systems
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from database_interface import DatabaseInterface


class MetaLearningCurriculum:
    """
    Intelligent curriculum for teaching agents to generalize across games
    Progressively increases difficulty and diversity to build meta-learning capability
    """

    # Curriculum stages (order matters!)
    CURRICULUM_STAGES = [
        {
            'stage_number': 1,
            'stage_name': 'specialization',
            'description': 'Master one game deeply to build foundational skills',
            'games_strategy': 'single_game',  # Focus on one game
            'min_win_rate': 0.70,  # Must achieve 70% win rate
            'min_transfer_rate': None,  # Not applicable yet
            'max_repeats_per_game': 50,  # Can repeat many times
            'exploration_weight': 0.3,  # Low exploration
            'focus': 'Deep mastery of single game mechanics'
        },
        {
            'stage_number': 2,
            'stage_name': 'near_transfer',
            'description': 'Transfer learned skills to similar game',
            'games_strategy': 'similar_pair',  # Original + 1 similar
            'min_win_rate': 0.50,  # 50% on both games
            'min_transfer_rate': 0.30,  # At least 30% of rules transfer
            'max_repeats_per_game': 30,
            'exploration_weight': 0.5,  # Medium exploration
            'focus': 'Rule transfer and adaptation'
        },
        {
            'stage_number': 3,
            'stage_name': 'diversification',
            'description': 'Learn from diverse set of games',
            'games_strategy': 'diverse_set',  # 4-6 different games
            'min_win_rate': 0.30,  # 30% average across all
            'min_transfer_rate': 0.50,  # 50% of rules should transfer
            'max_repeats_per_game': 10,  # Limited repetition
            'exploration_weight': 0.7,  # High exploration
            'focus': 'Building general rule library'
        },
        {
            'stage_number': 4,
            'stage_name': 'generalization',
            'description': 'Zero-shot performance on completely new games',
            'games_strategy': 'novel_games',  # Only never-seen games
            'min_win_rate': 0.20,  # 20% on completely new games (challenging!)
            'min_transfer_rate': 0.60,  # 60% of rules should work
            'max_repeats_per_game': 5,  # Very limited repetition
            'exploration_weight': 0.8,  # Very high exploration
            'focus': 'True generalization and zero-shot learning'
        }
    ]

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.current_generation = 0
        self.agent_stages = {}  # Track current stage per agent

    def initialize_agent_curriculum(self, agent_id: str, generation: int):
        """
        Initialize curriculum tracking for new agent
        Starts at stage 1 (specialization)
        """
        stage_1 = self.CURRICULUM_STAGES[0]

        self.db.execute_query("""
            INSERT INTO curriculum_progress (
                agent_id, stage_number, stage_name,
                required_win_rate, required_transfer_rate,
                entered_stage
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            agent_id,
            stage_1['stage_number'],
            stage_1['stage_name'],
            stage_1['min_win_rate'],
            stage_1.get('min_transfer_rate')
        ))

        self.agent_stages[agent_id] = stage_1['stage_number']

    def get_agent_current_stage(self, agent_id: str) -> int:
        """
        Get agent's current curriculum stage

        Returns:
            Stage number (1-4) or 1 if not tracked
        """
        if agent_id in self.agent_stages:
            return self.agent_stages[agent_id]

        # Query database
        result = self.db.execute_query("""
            SELECT stage_number
            FROM curriculum_progress
            WHERE agent_id = ? AND stage_completed = FALSE
            ORDER BY stage_number DESC
            LIMIT 1
        """, (agent_id,))

        if result:
            stage_num = result[0]['stage_number']
            self.agent_stages[agent_id] = stage_num
            return stage_num

        # Agent not in curriculum yet - initialize
        self.initialize_agent_curriculum(agent_id, self.current_generation)
        return 1

    def select_games_for_agent(self, agent_id: str,
                               available_games: List[str],
                               num_games: int = 5) -> List[str]:
        """
        Select appropriate games for agent based on curriculum stage

        Args:
            agent_id: Agent ID
            available_games: List of available game IDs
            num_games: Number of games to select

        Returns:
            List of game IDs appropriate for agent's curriculum stage
        """
        stage_num = self.get_agent_current_stage(agent_id)
        stage = self.CURRICULUM_STAGES[stage_num - 1]

        strategy = stage['games_strategy']

        if strategy == 'single_game':
            # Stage 1: Single game focus
            return self._select_single_game(agent_id, available_games)

        elif strategy == 'similar_pair':
            # Stage 2: Original game + one similar game
            return self._select_similar_pair(agent_id, available_games)

        elif strategy == 'diverse_set':
            # Stage 3: Diverse set of games
            return self._select_diverse_set(agent_id, available_games, num_games)

        elif strategy == 'novel_games':
            # Stage 4: Only novel games
            return self._select_novel_games(agent_id, available_games, num_games)

        else:
            # Fallback: random selection
            import random
            return random.sample(available_games, min(num_games, len(available_games)))

    def _select_single_game(self, agent_id: str, available_games: List[str]) -> List[str]:
        """Stage 1: Select single game for deep specialization"""
        # Check if agent already has a focus game
        result = self.db.execute_query("""
            SELECT game_id, attempts
            FROM agent_game_diversity
            WHERE agent_id = ?
            ORDER BY attempts DESC
            LIMIT 1
        """, (agent_id,))

        if result and result[0]['attempts'] > 0:
            # Continue with same game
            return [result[0]['game_id']]

        # Assign first available game
        if available_games:
            return [available_games[0]]

        return []

    def _select_similar_pair(self, agent_id: str, available_games: List[str]) -> List[str]:
        """Stage 2: Select original game + one similar game"""
        # Get the game agent mastered in stage 1
        result = self.db.execute_query("""
            SELECT game_id, best_score
            FROM agent_game_diversity
            WHERE agent_id = ?
            ORDER BY attempts DESC, best_score DESC
            LIMIT 1
        """, (agent_id,))

        if not result:
            # Fallback to first two games
            return available_games[:2] if len(available_games) >= 2 else available_games

        mastered_game = result[0]['game_id']

        # Find a similar game (not yet mastered)
        other_games = [g for g in available_games if g != mastered_game]

        if other_games:
            # For now, just pick next game (could use similarity metric)
            return [mastered_game, other_games[0]]

        return [mastered_game]

    def _select_diverse_set(self, agent_id: str, available_games: List[str],
                           num_games: int) -> List[str]:
        """Stage 3: Select diverse set of games"""
        # Get games agent has already played
        played_games = self.db.execute_query("""
            SELECT game_id, attempts
            FROM agent_game_diversity
            WHERE agent_id = ?
            ORDER BY attempts ASC
        """, (agent_id,))

        played_dict = {g['game_id']: g['attempts'] for g in played_games} if played_games else {}

        # Prioritize games with fewer attempts, include some new ones
        game_scores = []
        for game_id in available_games:
            attempts = played_dict.get(game_id, 0)

            # Score: prefer games with 1-5 attempts, then new games, then underplayed
            if 1 <= attempts <= 5:
                score = 100 - attempts  # Highest priority
            elif attempts == 0:
                score = 50  # New games - medium priority
            else:
                score = max(0, 20 - attempts)  # Overplayed games - low priority

            game_scores.append((game_id, score))

        # Sort by score and select top N
        game_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [g[0] for g in game_scores[:num_games]]

        return selected if selected else available_games[:num_games]

    def _select_novel_games(self, agent_id: str, available_games: List[str],
                           num_games: int) -> List[str]:
        """Stage 4: Select only novel (never played) games"""
        # Get games agent has never played
        played_games = self.db.execute_query("""
            SELECT game_id
            FROM agent_game_diversity
            WHERE agent_id = ?
        """, (agent_id,))

        played_set = {g['game_id'] for g in played_games} if played_games else set()

        # Filter to only novel games
        novel_games = [g for g in available_games if g not in played_set]

        if not novel_games:
            # All games played - select least played
            return self._select_diverse_set(agent_id, available_games, num_games)

        # Randomly select from novel games
        import random
        selected = random.sample(novel_games, min(num_games, len(novel_games)))

        return selected

    def update_stage_progress(self, agent_id: str):
        """
        Update agent's curriculum progress and check for stage advancement
        Called after each game session
        """
        stage_num = self.get_agent_current_stage(agent_id)
        stage = self.CURRICULUM_STAGES[stage_num - 1]

        # Get agent performance in current stage
        performance = self._get_stage_performance(agent_id, stage_num)

        # Update database with current performance
        self.db.execute_query("""
            UPDATE curriculum_progress
            SET achieved_win_rate = ?,
                achieved_transfer_rate = ?,
                games_played_in_stage = ?,
                games_won_in_stage = ?
            WHERE agent_id = ? AND stage_number = ?
        """, (
            performance['win_rate'],
            performance['transfer_rate'],
            performance['games_played'],
            performance['games_won'],
            agent_id,
            stage_num
        ))

        # Check if agent should advance to next stage
        if self._should_advance_stage(agent_id, stage, performance):
            self._advance_to_next_stage(agent_id, stage_num)

    def _get_stage_performance(self, agent_id: str, stage_num: int) -> Dict[str, Any]:
        """Get agent's performance in current curriculum stage"""
        # Get games played since entering this stage
        result = self.db.execute_query("""
            SELECT entered_stage FROM curriculum_progress
            WHERE agent_id = ? AND stage_number = ?
        """, (agent_id, stage_num))

        if not result:
            return {
                'win_rate': 0.0,
                'transfer_rate': 0.0,
                'games_played': 0,
                'games_won': 0
            }

        entered_timestamp = result[0]['entered_stage']

        # Get performance since entering stage
        perf_result = self.db.execute_query("""
            SELECT
                COUNT(*) as games_played,
                SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as games_won
            FROM agent_arc_performance
            WHERE agent_id = ? AND game_timestamp >= ?
        """, (agent_id, entered_timestamp))

        games_played = perf_result[0]['games_played'] if perf_result else 0
        games_won = perf_result[0]['games_won'] if perf_result else 0

        win_rate = games_won / games_played if games_played > 0 else 0.0

        # Get transfer rate (from meta-learning metrics)
        transfer_result = self.db.execute_query("""
            SELECT transfer_success_rate
            FROM agent_meta_learning
            WHERE agent_id = ?
        """, (agent_id,))

        transfer_rate = transfer_result[0]['transfer_success_rate'] if transfer_result else 0.0

        return {
            'win_rate': win_rate,
            'transfer_rate': transfer_rate,
            'games_played': games_played,
            'games_won': games_won
        }

    def _should_advance_stage(self, agent_id: str, stage: Dict[str, Any],
                             performance: Dict[str, Any]) -> bool:
        """Check if agent meets requirements to advance to next stage"""
        # Need minimum games played
        if performance['games_played'] < 10:
            return False

        # Check win rate requirement
        if performance['win_rate'] < stage['min_win_rate']:
            return False

        # Check transfer rate requirement (if applicable)
        min_transfer = stage.get('min_transfer_rate')
        if min_transfer is not None:
            if performance['transfer_rate'] < min_transfer:
                return False

        return True

    def _advance_to_next_stage(self, agent_id: str, current_stage_num: int):
        """Advance agent to next curriculum stage"""
        if current_stage_num >= len(self.CURRICULUM_STAGES):
            # Already at final stage - mark as "graduated"
            return

        # Mark current stage as completed
        self.db.execute_query("""
            UPDATE curriculum_progress
            SET stage_completed = TRUE,
                completion_timestamp = CURRENT_TIMESTAMP,
                exited_stage = CURRENT_TIMESTAMP
            WHERE agent_id = ? AND stage_number = ?
        """, (agent_id, current_stage_num))

        # Initialize next stage
        next_stage_num = current_stage_num + 1
        next_stage = self.CURRICULUM_STAGES[next_stage_num - 1]

        self.db.execute_query("""
            INSERT INTO curriculum_progress (
                agent_id, stage_number, stage_name,
                required_win_rate, required_transfer_rate,
                entered_stage
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            agent_id,
            next_stage['stage_number'],
            next_stage['stage_name'],
            next_stage['min_win_rate'],
            next_stage.get('min_transfer_rate')
        ))

        # Update cache
        self.agent_stages[agent_id] = next_stage_num

        # Log advancement (Rule 2: database only)
        try:
            self.db.execute_query("""
                INSERT INTO system_logs (level, component, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                'INFO',
                'curriculum',
                f"Agent {agent_id} advanced to stage {next_stage_num}: {next_stage['stage_name']}",
                datetime.now().isoformat()
            ))
        except:
            pass  # Non-critical logging

    def get_curriculum_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Get curriculum configuration for agent
        Returns config that can be passed to GameplayEngine
        """
        stage_num = self.get_agent_current_stage(agent_id)
        stage = self.CURRICULUM_STAGES[stage_num - 1]

        return {
            'stage_number': stage_num,
            'stage_name': stage['stage_name'],
            'max_repeats_per_game': stage['max_repeats_per_game'],
            'exploration_weight': stage['exploration_weight'],
            'enable_rule_learning': stage_num >= 2,  # Enable from stage 2
            'enable_rule_transfer': stage_num >= 2,
            'focus': stage['focus']
        }


# [CHECKPOINT: META-LEARNING CURRICULUM IMPLEMENTATION COMPLETE]
# Next: Enhance agent genome to include learned structures
