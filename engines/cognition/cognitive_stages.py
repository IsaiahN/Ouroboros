"""
Cognitive Stage System - Developmental progression tracking.

Tracks and evolves agent cognitive development through three Piaget-inspired stages:

1. PREOPERATIONAL (Early Development)
   - Explores through action-effect observation
   - No planning, reactive behavior
   - Learning object permanence and causation

2. CONCRETE_OPERATIONAL (Learned Patterns)
   - Can apply learned sequences
   - Understands conservation and reversibility
   - Logical thinking about concrete objects

3. FORMAL_OPERATIONAL (Abstract Reasoning)
   - Hypothetical-deductive reasoning
   - Can create and test hypotheses
   - Abstract pattern generalization

Stage transitions based on demonstrated competencies, not age/time.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class CognitiveStageSystem:
    """
    Tracks and evolves agent cognitive development through three stages:

    1. PREOPERATIONAL (Early Development)
       - Explores through action-effect observation
       - No planning, reactive behavior
       - Learning object permanence and causation

    2. CONCRETE_OPERATIONAL (Learned Patterns)
       - Can apply learned sequences
       - Understands conservation and reversibility
       - Logical thinking about concrete objects

    3. FORMAL_OPERATIONAL (Abstract Reasoning)
       - Hypothetical-deductive reasoning
       - Can create and test hypotheses
       - Abstract pattern generalization

    Stage transitions based on demonstrated competencies, not age/time.
    """

    # Stage names (Piaget-based, adapted for AI agents)
    PREOPERATIONAL = 'preoperational'
    CONCRETE_OPERATIONAL = 'concrete_operational'
    FORMAL_OPERATIONAL = 'formal_operational'

    # Competency thresholds for stage transitions
    COMPETENCIES = {
        'preoperational_to_concrete': {
            'games_played': 5,          # Minimum experience
            'sequences_discovered': 1,   # Can find a winning pattern
            'object_control_learned': True,  # Knows "I am this object"
            'action_effect_pairs': 3     # Understands cause-effect
        },
        'concrete_to_formal': {
            'games_played': 20,
            'sequences_discovered': 5,
            'hypotheses_created': 2,     # Has generated own hypotheses
            'cross_game_transfer': True, # Applied learning across game types
            'validation_success_rate': 0.6  # Sequences work for others too
        }
    }

    def __init__(self, db: 'DatabaseInterface'):
        """Initialize cognitive stage system."""
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure cognitive stage tracking table exists."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_cognitive_stages (
                agent_id TEXT PRIMARY KEY,
                current_stage TEXT NOT NULL DEFAULT 'preoperational',
                stage_entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Competency tracking
                games_played INTEGER DEFAULT 0,
                sequences_discovered INTEGER DEFAULT 0,
                hypotheses_created INTEGER DEFAULT 0,
                object_control_learned BOOLEAN DEFAULT FALSE,
                action_effect_pairs INTEGER DEFAULT 0,
                cross_game_transfer BOOLEAN DEFAULT FALSE,
                validation_success_rate REAL DEFAULT 0.0,

                -- Stage history
                preoperational_exit DATETIME,
                concrete_exit DATETIME,

                last_evaluated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cognitive_stage
            ON agent_cognitive_stages(current_stage)
        """)

    def get_stage(self, agent_id: str) -> str:
        """Get agent's current cognitive stage."""
        result = self.db.execute_query("""
            SELECT current_stage FROM agent_cognitive_stages WHERE agent_id = ?
        """, (agent_id,))

        if result:
            return result[0]['current_stage']

        # Initialize new agent at preoperational stage
        self._initialize_agent(agent_id)
        return self.PREOPERATIONAL

    def _initialize_agent(self, agent_id: str) -> None:
        """Initialize cognitive stage tracking for new agent."""
        self.db.execute_query("""
            INSERT OR IGNORE INTO agent_cognitive_stages (agent_id, current_stage)
            VALUES (?, ?)
        """, (agent_id, self.PREOPERATIONAL))

    def update_competencies(
        self,
        agent_id: str,
        games_played_delta: int = 0,
        sequences_discovered_delta: int = 0,
        hypotheses_created_delta: int = 0,
        object_control_learned: Optional[bool] = None,
        action_effect_pairs_delta: int = 0,
        cross_game_transfer: Optional[bool] = None,
        validation_success_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update agent's cognitive competencies and check for stage transition.

        Returns:
            Dict with current_stage, transitioned (bool), and competencies
        """
        # Ensure agent exists
        self._initialize_agent(agent_id)

        # Build update query dynamically
        updates = []
        params = []

        if games_played_delta:
            updates.append("games_played = games_played + ?")
            params.append(games_played_delta)
        if sequences_discovered_delta:
            updates.append("sequences_discovered = sequences_discovered + ?")
            params.append(sequences_discovered_delta)
        if hypotheses_created_delta:
            updates.append("hypotheses_created = hypotheses_created + ?")
            params.append(hypotheses_created_delta)
        if object_control_learned is not None:
            updates.append("object_control_learned = ?")
            params.append(object_control_learned)
        if action_effect_pairs_delta:
            updates.append("action_effect_pairs = action_effect_pairs + ?")
            params.append(action_effect_pairs_delta)
        if cross_game_transfer is not None:
            updates.append("cross_game_transfer = ?")
            params.append(cross_game_transfer)
        if validation_success_rate is not None:
            updates.append("validation_success_rate = ?")
            params.append(validation_success_rate)

        updates.append("last_evaluated = CURRENT_TIMESTAMP")

        if updates:
            query = f"UPDATE agent_cognitive_stages SET {', '.join(updates)} WHERE agent_id = ?"
            params.append(agent_id)
            self.db.execute_query(query, tuple(params))

        # Check for stage transition
        return self._evaluate_stage_transition(agent_id)

    def _evaluate_stage_transition(self, agent_id: str) -> Dict[str, Any]:
        """Evaluate if agent should transition to next cognitive stage."""
        result = self.db.execute_query("""
            SELECT * FROM agent_cognitive_stages WHERE agent_id = ?
        """, (agent_id,))

        if not result:
            return {'current_stage': self.PREOPERATIONAL, 'transitioned': False}

        r = result[0]
        current_stage = r['current_stage']
        transitioned = False
        new_stage = current_stage

        if current_stage == self.PREOPERATIONAL:
            # Check for transition to concrete operational
            reqs = self.COMPETENCIES['preoperational_to_concrete']
            if (r['games_played'] >= reqs['games_played'] and
                r['sequences_discovered'] >= reqs['sequences_discovered'] and
                r['object_control_learned'] and
                r['action_effect_pairs'] >= reqs['action_effect_pairs']):

                new_stage = self.CONCRETE_OPERATIONAL
                transitioned = True
                self.db.execute_query("""
                    UPDATE agent_cognitive_stages
                    SET current_stage = ?,
                        preoperational_exit = CURRENT_TIMESTAMP,
                        stage_entered_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (new_stage, agent_id))
                logger.info(f"[COGNITIVE] Agent {agent_id[:8]} -> CONCRETE_OPERATIONAL stage")

        elif current_stage == self.CONCRETE_OPERATIONAL:
            # Check for transition to formal operational
            reqs = self.COMPETENCIES['concrete_to_formal']
            if (r['games_played'] >= reqs['games_played'] and
                r['sequences_discovered'] >= reqs['sequences_discovered'] and
                r['hypotheses_created'] >= reqs['hypotheses_created'] and
                r['cross_game_transfer'] and
                r['validation_success_rate'] >= reqs['validation_success_rate']):

                new_stage = self.FORMAL_OPERATIONAL
                transitioned = True
                self.db.execute_query("""
                    UPDATE agent_cognitive_stages
                    SET current_stage = ?,
                        concrete_exit = CURRENT_TIMESTAMP,
                        stage_entered_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (new_stage, agent_id))
                logger.info(f"[COGNITIVE] Agent {agent_id[:8]} -> FORMAL_OPERATIONAL stage")

        return {
            'current_stage': new_stage,
            'transitioned': transitioned,
            'competencies': dict(r)
        }

    def get_stage_capabilities(self, agent_id: str) -> Dict[str, bool]:
        """Get what cognitive capabilities an agent has based on their stage."""
        stage = self.get_stage(agent_id)

        capabilities = {
            # Preoperational capabilities (all agents have these)
            'action_exploration': True,
            'object_observation': True,
            'pattern_recognition': True,

            # Concrete operational capabilities
            'sequence_following': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],
            'reversibility_understanding': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],
            'conservation_of_state': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],

            # Formal operational capabilities
            'hypothesis_generation': stage == self.FORMAL_OPERATIONAL,
            'abstract_generalization': stage == self.FORMAL_OPERATIONAL,
            'hypothetical_reasoning': stage == self.FORMAL_OPERATIONAL,
            'cross_domain_transfer': stage == self.FORMAL_OPERATIONAL
        }

        return capabilities

    def get_population_distribution(self) -> Dict[str, int]:
        """Get distribution of agents across cognitive stages."""
        result = self.db.execute_query("""
            SELECT current_stage, COUNT(*) as count
            FROM agent_cognitive_stages
            GROUP BY current_stage
        """)

        distribution = {
            self.PREOPERATIONAL: 0,
            self.CONCRETE_OPERATIONAL: 0,
            self.FORMAL_OPERATIONAL: 0
        }

        for r in result or []:
            stage = r['current_stage']
            if stage in distribution:
                distribution[stage] = r['count']

        return distribution
