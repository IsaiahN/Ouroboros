import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

"""
Subgoal Planning System - Hierarchical Multi-Step Planning for ARC Games
=========================================================================

Breaks down complex ARC problems into achievable sub-objectives and plans
multi-step action sequences. Integrates with existing core_gameplay.py.

Following Rule 2: All plans and results stored in database
Following Rule 3: Enhances existing action selection, doesn't replace it
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class SubgoalPlanner:
    """
    Plans multi-step action sequences by breaking down ARC problems into subgoals.

    Subgoal hierarchy:
    1. High-level objective (e.g., "win game", "complete level")
    2. Mid-level subgoals (e.g., "identify pattern", "fill region", "transform object")
    3. Low-level actions (existing ACTION1-ACTION7)
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Initialize subgoal planning schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Create subgoal planning tables in database"""
        try:
            # Subgoal plans
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS subgoal_plans (
                    plan_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,

                    -- Plan structure
                    high_level_objective TEXT NOT NULL,
                    subgoal_sequence TEXT NOT NULL,  -- JSON: ordered list of subgoals
                    total_subgoals INTEGER NOT NULL,

                    -- Execution tracking
                    plan_status TEXT DEFAULT 'active',  -- 'active', 'completed', 'failed', 'abandoned'
                    current_subgoal_index INTEGER DEFAULT 0,
                    completed_subgoals INTEGER DEFAULT 0,
                    failed_subgoals INTEGER DEFAULT 0,

                    -- Performance
                    actions_planned INTEGER DEFAULT 0,
                    actions_executed INTEGER DEFAULT 0,
                    score_at_start REAL DEFAULT 0.0,
                    score_at_end REAL DEFAULT 0.0,
                    plan_efficiency REAL DEFAULT 0.0,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,

                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Subgoal execution results
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS subgoal_executions (
                    execution_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    subgoal_index INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,

                    -- Subgoal details
                    subgoal_type TEXT NOT NULL,  -- 'identify_pattern', 'fill_region', 'transform', etc.
                    subgoal_description TEXT NOT NULL,
                    preconditions TEXT,  -- JSON: what must be true before
                    postconditions TEXT,  -- JSON: what should be true after

                    -- Execution
                    actions_taken TEXT,  -- JSON: list of actions executed
                    execution_status TEXT NOT NULL,  -- 'success', 'partial', 'failed'
                    score_before REAL DEFAULT 0.0,
                    score_after REAL DEFAULT 0.0,
                    score_delta REAL DEFAULT 0.0,

                    -- Learning
                    success_factors TEXT,  -- JSON: what worked
                    failure_factors TEXT,  -- JSON: what didn't work

                    -- Timestamps
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,

                    FOREIGN KEY (plan_id) REFERENCES subgoal_plans(plan_id),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Subgoal patterns (learned successful subgoal sequences)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS subgoal_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_name TEXT NOT NULL,

                    -- Pattern structure
                    subgoal_sequence TEXT NOT NULL,  -- JSON: ordered subgoals
                    game_context TEXT,  -- JSON: when this pattern applies

                    -- Effectiveness
                    times_attempted INTEGER DEFAULT 0,
                    times_succeeded INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    avg_score_improvement REAL DEFAULT 0.0,
                    avg_actions_required REAL DEFAULT 0.0,

                    -- Discovery
                    discovered_by_agent TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    discovered_generation INTEGER DEFAULT 0,

                    -- Usage
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,

                    FOREIGN KEY (discovered_by_agent) REFERENCES agents(agent_id)
                )
            """)

            # Create indexes
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_subgoal_plans_agent ON subgoal_plans(agent_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_subgoal_plans_game ON subgoal_plans(game_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_subgoal_plans_status ON subgoal_plans(plan_status)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_subgoal_executions_plan ON subgoal_executions(plan_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_subgoal_patterns_success ON subgoal_patterns(success_rate DESC)")

            self.logger.info("Subgoal planning schema initialized")

        except Exception as e:
            self.logger.error(f"Schema initialization error: {e}")

    def generate_subgoals(self, game_id: str, level_number: int, frame_data: List[List[int]],
                         agent_id: str = "unknown", session_id: str = "unknown",
                         current_score: float = 0.0, generation: int = 0) -> List[Dict]:
        """
        Generate subgoals for a level (wrapper for create_plan).

        Args:
            game_id: Current game
            level_number: Current level number
            frame_data: Current game frame
            agent_id: Agent ID (optional)
            session_id: Session ID (optional)
            current_score: Current score
            generation: Agent generation

        Returns:
            List of subgoal dictionaries, or empty list if no plan could be created
        """
        try:
            # Analyze frame to identify objectives and decompose into subgoals
            objectives = self._identify_objectives(frame_data, current_score)
            if not objectives:
                return []

            primary_objective = self._select_primary_objective(objectives, current_score)
            subgoals = self._decompose_into_subgoals(primary_objective, frame_data)

            return subgoals if subgoals else []
        except Exception as e:
            self.logger.error(f"Subgoal generation error: {e}")
            return []

    def create_plan(self, agent_id: str, game_id: str, session_id: str,
                   current_frame: List[List[int]], current_score: float,
                   generation: int = 0) -> Optional[str]:
        """
        Create a hierarchical plan for the current game state.

        Args:
            agent_id: Agent creating the plan
            game_id: Current game
            session_id: Current session
            current_frame: Current game frame
            current_score: Current score
            generation: Agent generation

        Returns:
            plan_id if created, None otherwise
        """
        try:
            # Analyze frame to identify high-level objectives
            objectives = self._identify_objectives(current_frame, current_score)

            if not objectives:
                return None

            # Select primary objective based on current state
            primary_objective = self._select_primary_objective(objectives, current_score)

            # Decompose into subgoals
            subgoals = self._decompose_into_subgoals(primary_objective, current_frame)

            if not subgoals:
                return None

            # Create plan
            plan_id = f"plan_{uuid.uuid4().hex[:12]}"

            # Estimate actions needed
            actions_planned = sum(sg.get('estimated_actions', 5) for sg in subgoals)

            self.db.execute_query("""
                INSERT INTO subgoal_plans (
                    plan_id, agent_id, game_id, session_id, generation,
                    high_level_objective, subgoal_sequence, total_subgoals,
                    actions_planned, score_at_start
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_id, agent_id, game_id, session_id, generation,
                primary_objective, json.dumps(subgoals), len(subgoals),
                actions_planned, current_score
            ))

            self.logger.info(f"Created plan {plan_id}: {primary_objective} with {len(subgoals)} subgoals")
            return plan_id

        except Exception as e:
            self.logger.error(f"Plan creation error: {e}")
            return None

    def _identify_objectives(self, frame: List[List[int]], score: float) -> List[Dict]:
        """Identify possible high-level objectives from current game state"""
        objectives = []

        # Objective 1: Win the game (always applicable if not won)
        if score < 20.0:
            objectives.append({
                'type': 'win_game',
                'description': 'Complete all levels and win',
                'priority': 1.0
            })

        # Objective 2: Complete current level
        if score < 10.0 or (score >= 10.0 and score < 20.0):
            objectives.append({
                'type': 'complete_level',
                'description': 'Complete current level',
                'priority': 0.9
            })

        # Objective 3: Improve score significantly
        objectives.append({
            'type': 'improve_score',
            'description': 'Improve score by 5+ points',
            'priority': 0.7
        })

        # Frame-based objectives
        if len(frame) > 0:
            # Objective 4: Fill empty regions
            empty_count = sum(1 for row in frame for cell in row if cell == 0)
            total_cells = len(frame) * len(frame[0]) if frame else 1
            empty_ratio = empty_count / total_cells if total_cells > 0 else 0

            if empty_ratio > 0.3:
                objectives.append({
                    'type': 'fill_regions',
                    'description': 'Fill empty regions strategically',
                    'priority': 0.6
                })

            # Objective 5: Transform patterns
            objectives.append({
                'type': 'transform_patterns',
                'description': 'Apply transformations to visible patterns',
                'priority': 0.5
            })

        return objectives

    def _select_primary_objective(self, objectives: List[Dict], score: float) -> str:
        """Select the most appropriate objective given current state"""
        if not objectives:
            return "improve_score"

        # Sort by priority
        sorted_objs = sorted(objectives, key=lambda x: x['priority'], reverse=True)
        return sorted_objs[0]['description']

    def _decompose_into_subgoals(self, objective: str, frame: List[List[int]]) -> List[Dict]:
        """Decompose high-level objective into executable subgoals"""
        subgoals = []

        if "win" in objective.lower() or "complete all" in objective.lower():
            # Win game: identify pattern → apply pattern → verify
            subgoals = [
                {
                    'type': 'identify_pattern',
                    'description': 'Analyze frame for transformation patterns',
                    'estimated_actions': 10,
                    'preconditions': {'frame_available': True},
                    'postconditions': {'pattern_identified': True}
                },
                {
                    'type': 'apply_transformation',
                    'description': 'Apply identified transformation',
                    'estimated_actions': 20,
                    'preconditions': {'pattern_identified': True},
                    'postconditions': {'transformation_applied': True}
                },
                {
                    'type': 'verify_result',
                    'description': 'Check if transformation improved score',
                    'estimated_actions': 5,
                    'preconditions': {'transformation_applied': True},
                    'postconditions': {'score_improved': True}
                }
            ]

        elif "complete level" in objective.lower():
            # Complete level: explore → fill critical regions → verify
            subgoals = [
                {
                    'type': 'explore_frame',
                    'description': 'Explore frame to understand structure',
                    'estimated_actions': 15,
                    'preconditions': {},
                    'postconditions': {'frame_explored': True}
                },
                {
                    'type': 'fill_critical_regions',
                    'description': 'Fill regions likely to score points',
                    'estimated_actions': 25,
                    'preconditions': {'frame_explored': True},
                    'postconditions': {'regions_filled': True}
                },
                {
                    'type': 'refine_solution',
                    'description': 'Refine solution based on feedback',
                    'estimated_actions': 10,
                    'preconditions': {'regions_filled': True},
                    'postconditions': {'solution_refined': True}
                }
            ]

        elif "improve score" in objective.lower():
            # Improve score: try high-value actions
            subgoals = [
                {
                    'type': 'identify_high_value_actions',
                    'description': 'Find actions that maximize score',
                    'estimated_actions': 8,
                    'preconditions': {},
                    'postconditions': {'high_value_actions_found': True}
                },
                {
                    'type': 'execute_high_value_actions',
                    'description': 'Execute identified high-value actions',
                    'estimated_actions': 15,
                    'preconditions': {'high_value_actions_found': True},
                    'postconditions': {'actions_executed': True}
                }
            ]

        elif "fill regions" in objective.lower():
            # Fill regions subgoal
            subgoals = [
                {
                    'type': 'identify_empty_regions',
                    'description': 'Locate empty or incomplete regions',
                    'estimated_actions': 5,
                    'preconditions': {},
                    'postconditions': {'regions_identified': True}
                },
                {
                    'type': 'fill_regions_strategically',
                    'description': 'Fill identified regions',
                    'estimated_actions': 20,
                    'preconditions': {'regions_identified': True},
                    'postconditions': {'regions_filled': True}
                }
            ]

        else:
            # Default: explore and act
            subgoals = [
                {
                    'type': 'explore',
                    'description': 'Explore game state',
                    'estimated_actions': 10,
                    'preconditions': {},
                    'postconditions': {'explored': True}
                },
                {
                    'type': 'act',
                    'description': 'Take strategic actions',
                    'estimated_actions': 15,
                    'preconditions': {'explored': True},
                    'postconditions': {'acted': True}
                }
            ]

        return subgoals

    def get_next_subgoal_actions(self, plan_id: str, current_frame: List[List[int]],
                                available_actions: List[int]) -> List[int]:
        """
        Get recommended actions for the current subgoal.

        Returns:
            List of action IDs to prioritize for current subgoal
        """
        try:
            # Get current plan
            plan = self.db.execute_query("""
                SELECT high_level_objective, subgoal_sequence, current_subgoal_index
                FROM subgoal_plans
                WHERE plan_id = ? AND plan_status = 'active'
            """, (plan_id,))

            if not plan:
                return available_actions  # No plan, use all actions

            plan = plan[0]
            subgoals = json.loads(plan['subgoal_sequence'])
            current_idx = plan['current_subgoal_index']

            if current_idx >= len(subgoals):
                # Plan completed, mark it
                self._complete_plan(plan_id)
                return available_actions

            current_subgoal = subgoals[current_idx]
            subgoal_type = current_subgoal['type']

            # Map subgoal types to action priorities
            action_priorities = self._get_action_priorities_for_subgoal(subgoal_type, current_frame)

            # Sort available actions by priority
            sorted_actions = sorted(
                available_actions,
                key=lambda a: action_priorities.get(a, 0.5),
                reverse=True
            )

            return sorted_actions

        except Exception as e:
            self.logger.error(f"Error getting subgoal actions: {e}")
            return available_actions

    def _get_action_priorities_for_subgoal(self, subgoal_type: str,
                                          frame: List[List[int]]) -> Dict[int, float]:
        """Get action priority weights for specific subgoal type"""

        # Default priorities (equal weight)
        priorities = {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5, 7: 0.5}

        if subgoal_type == 'explore_frame' or subgoal_type == 'identify_pattern':
            # Prioritize exploration actions
            priorities[1] = 0.8  # ACTION1 (often reveals information)
            priorities[7] = 0.8  # ACTION7 (exploration)
            priorities[6] = 0.7  # ACTION6 (coordinate exploration)
            priorities[2] = 0.4
            priorities[3] = 0.4

        elif subgoal_type == 'fill_regions' or subgoal_type == 'fill_critical_regions':
            # Prioritize ACTION6 for filling
            priorities[6] = 1.0  # ACTION6 (coordinate-based filling)
            priorities[2] = 0.6
            priorities[3] = 0.6
            priorities[1] = 0.3

        elif subgoal_type == 'apply_transformation' or subgoal_type == 'transform_patterns':
            # Prioritize transformation actions
            priorities[2] = 0.8
            priorities[3] = 0.8
            priorities[6] = 0.7
            priorities[4] = 0.6

        elif subgoal_type == 'verify_result' or subgoal_type == 'refine_solution':
            # Prioritize checking actions
            priorities[1] = 0.7
            priorities[5] = 0.7
            priorities[7] = 0.6

        return priorities

    def record_subgoal_execution(self, plan_id: str, actions_taken: List[int],
                                score_before: float, score_after: float,
                                success: bool):
        """Record the result of executing current subgoal"""
        try:
            # Get current plan
            plan = self.db.execute_query("""
                SELECT agent_id, game_id, subgoal_sequence, current_subgoal_index,
                       completed_subgoals, failed_subgoals
                FROM subgoal_plans
                WHERE plan_id = ?
            """, (plan_id,))

            if not plan:
                return

            plan = plan[0]
            subgoals = json.loads(plan['subgoal_sequence'])
            current_idx = plan['current_subgoal_index']

            if current_idx >= len(subgoals):
                return

            current_subgoal = subgoals[current_idx]

            # Record execution
            execution_id = f"exec_{uuid.uuid4().hex[:12]}"
            execution_status = 'success' if success else 'failed'

            self.db.execute_query("""
                INSERT INTO subgoal_executions (
                    execution_id, plan_id, subgoal_index, agent_id, game_id,
                    subgoal_type, subgoal_description, actions_taken,
                    execution_status, score_before, score_after, score_delta,
                    completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id, plan_id, current_idx, plan['agent_id'], plan['game_id'],
                current_subgoal['type'], current_subgoal['description'],
                json.dumps(actions_taken), execution_status,
                score_before, score_after, score_after - score_before,
                datetime.now().isoformat()
            ))

            # Update plan progress
            if success:
                new_completed = plan['completed_subgoals'] + 1
                new_failed = plan['failed_subgoals']
            else:
                new_completed = plan['completed_subgoals']
                new_failed = plan['failed_subgoals'] + 1

            new_idx = current_idx + 1

            self.db.execute_query("""
                UPDATE subgoal_plans
                SET current_subgoal_index = ?,
                    completed_subgoals = ?,
                    failed_subgoals = ?,
                    actions_executed = actions_executed + ?
                WHERE plan_id = ?
            """, (new_idx, new_completed, new_failed, len(actions_taken), plan_id))

            self.logger.info(f"Recorded subgoal execution: {execution_status} (plan {plan_id})")

        except Exception as e:
            self.logger.error(f"Error recording subgoal execution: {e}")

    def _complete_plan(self, plan_id: str):
        """Mark plan as completed"""
        try:
            self.db.execute_query("""
                UPDATE subgoal_plans
                SET plan_status = 'completed',
                    completed_at = ?
                WHERE plan_id = ?
            """, (datetime.now().isoformat(), plan_id))

            self.logger.info(f"Plan {plan_id} completed")

        except Exception as e:
            self.logger.error(f"Error completing plan: {e}")

    def learn_subgoal_pattern(self, plan_id: str, agent_id: str, generation: int):
        """
        Learn a reusable subgoal pattern from successful plan execution.
        """
        try:
            # Get completed plan
            plan = self.db.execute_query("""
                SELECT subgoal_sequence, high_level_objective,
                       score_at_start, score_at_end, actions_executed
                FROM subgoal_plans
                WHERE plan_id = ? AND plan_status = 'completed'
            """, (plan_id,))

            if not plan:
                return

            plan = plan[0]

            # Only learn from successful plans (score improvement)
            if plan['score_at_end'] <= plan['score_at_start']:
                return

            score_improvement = plan['score_at_end'] - plan['score_at_start']

            # Create pattern
            pattern_id = f"sgpat_{uuid.uuid4().hex[:12]}"
            pattern_name = f"subgoal_pattern_{plan['high_level_objective'][:20]}_{pattern_id[:8]}"

            self.db.execute_query("""
                INSERT INTO subgoal_patterns (
                    pattern_id, pattern_name, subgoal_sequence,
                    times_attempted, times_succeeded, success_rate,
                    avg_score_improvement, avg_actions_required,
                    discovered_by_agent, discovered_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id, pattern_name, plan['subgoal_sequence'],
                1, 1, 1.0, score_improvement, plan['actions_executed'],
                agent_id, generation
            ))

            self.logger.info(f"Learned subgoal pattern {pattern_id} from plan {plan_id}")

        except Exception as e:
            self.logger.error(f"Error learning subgoal pattern: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get subgoal planning statistics"""
        try:
            plans = self.db.execute_query("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN plan_status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN plan_status = 'failed' THEN 1 ELSE 0 END) as failed,
                       AVG(completed_subgoals) as avg_completed_subgoals,
                       AVG(plan_efficiency) as avg_efficiency
                FROM subgoal_plans
            """)

            patterns = self.db.execute_query("""
                SELECT COUNT(*) as total,
                       AVG(success_rate) as avg_success_rate
                FROM subgoal_patterns
                WHERE is_active = TRUE
            """)

            return {
                'total_plans': plans[0]['total'] if plans else 0,
                'completed_plans': plans[0]['completed'] if plans else 0,
                'failed_plans': plans[0]['failed'] if plans else 0,
                'avg_completed_subgoals': plans[0]['avg_completed_subgoals'] if plans else 0,
                'learned_patterns': patterns[0]['total'] if patterns else 0,
                'avg_pattern_success_rate': patterns[0]['avg_success_rate'] if patterns else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}
