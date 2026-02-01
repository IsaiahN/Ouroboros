import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Collective Reasoning System - Multi-Agent Ensemble Intelligence
===============================================================

Enables top-performing agents to collaborate on challenging games through
consensus-based action selection. Extends existing agent coordination.

Following Rule 2: All collective sessions stored in database
Following Rule 3: Enhances existing gameplay, doesn't replace it
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)


class CollectiveReasoningEngine:
    """
    Coordinates multiple agents to reason collectively about challenging games.

    Collective reasoning modes:
    1. Voting: Agents vote on best action
    2. Consensus: Agents must agree on approach
    3. Specialization: Each agent contributes its expertise
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Collective parameters
        self.min_agents_for_collective = 3
        self.max_agents_for_collective = 5
        self.consensus_threshold = 0.6  # 60% agreement

        # Initialize schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Create collective reasoning tables"""
        try:
            # Collective reasoning sessions
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS collective_reasoning_sessions (
                    session_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,

                    -- Participating agents
                    agent_ids TEXT NOT NULL,  -- JSON: list of agent IDs
                    agent_count INTEGER NOT NULL,
                    lead_agent_id TEXT,  -- Coordinator agent

                    -- Session configuration
                    reasoning_mode TEXT NOT NULL,  -- 'voting', 'consensus', 'specialization'
                    consensus_threshold REAL DEFAULT 0.6,

                    -- Session state
                    session_status TEXT DEFAULT 'active',  -- 'active', 'completed', 'failed'
                    current_turn INTEGER DEFAULT 0,
                    total_turns INTEGER DEFAULT 0,

                    -- Performance
                    initial_score REAL DEFAULT 0.0,
                    final_score REAL DEFAULT 0.0,
                    score_improvement REAL DEFAULT 0.0,
                    actions_taken INTEGER DEFAULT 0,

                    -- Collective dynamics
                    consensus_reached_count INTEGER DEFAULT 0,
                    disagreement_count INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0,

                    -- Timestamps
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # Collective action proposals
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS collective_action_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    proposing_agent_id TEXT NOT NULL,

                    -- Proposal details
                    proposed_action INTEGER NOT NULL,  -- ACTION1-7
                    action_coordinates TEXT,  -- JSON: coordinates if ACTION6
                    reasoning TEXT NOT NULL,  -- Why this action?
                    confidence REAL DEFAULT 0.5,  -- Agent's confidence in proposal

                    -- Voting results
                    votes_for INTEGER DEFAULT 0,
                    votes_against INTEGER DEFAULT 0,
                    votes_abstain INTEGER DEFAULT 0,
                    proposal_accepted BOOLEAN DEFAULT FALSE,

                    -- Execution results
                    was_executed BOOLEAN DEFAULT FALSE,
                    score_before REAL,
                    score_after REAL,
                    actual_effectiveness REAL,

                    -- Timestamps
                    proposed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    voted_at TIMESTAMP,
                    executed_at TIMESTAMP,

                    FOREIGN KEY (session_id) REFERENCES collective_reasoning_sessions(session_id),
                    FOREIGN KEY (proposing_agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Agent votes on proposals
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS collective_votes (
                    vote_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    voting_agent_id TEXT NOT NULL,

                    -- Vote details
                    vote_choice TEXT NOT NULL,  -- 'for', 'against', 'abstain'
                    vote_weight REAL DEFAULT 1.0,  -- Based on agent expertise
                    vote_reasoning TEXT,
                    confidence_in_vote REAL DEFAULT 0.5,

                    -- Timestamps
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (proposal_id) REFERENCES collective_action_proposals(proposal_id),
                    FOREIGN KEY (voting_agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Collective insights (emergent understanding from multiple agents)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS collective_insights (
                    insight_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,

                    -- Insight details
                    insight_type TEXT NOT NULL,  -- 'pattern_recognition', 'strategy_hypothesis', 'failure_prediction'
                    insight_description TEXT NOT NULL,
                    contributing_agents TEXT,  -- JSON: agents who contributed
                    confidence_score REAL DEFAULT 0.5,

                    -- Validation
                    was_correct BOOLEAN,
                    evidence TEXT,  -- JSON: supporting evidence

                    -- Impact
                    actions_influenced INTEGER DEFAULT 0,
                    score_impact REAL DEFAULT 0.0,

                    -- Timestamps
                    emerged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    validated_at TIMESTAMP,

                    FOREIGN KEY (session_id) REFERENCES collective_reasoning_sessions(session_id)
                )
            """)

            # Create indexes
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_collective_sessions_game ON collective_reasoning_sessions(game_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_collective_sessions_status ON collective_reasoning_sessions(session_status)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_collective_proposals_session ON collective_action_proposals(session_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_collective_proposals_accepted ON collective_action_proposals(proposal_accepted)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_collective_votes_proposal ON collective_votes(proposal_id)")

            self.logger.info("Collective reasoning schema initialized")

        except Exception as e:
            self.logger.error(f"Schema initialization error: {e}")

    def start_collective_session(self, game_id: str, generation: int,
                                 reasoning_mode: str = 'voting') -> Optional[str]:
        """
        Start a collective reasoning session with top-performing agents.

        Args:
            game_id: Game to reason about
            generation: Current generation
            reasoning_mode: 'voting', 'consensus', or 'specialization'

        Returns:
            session_id if started, None otherwise
        """
        try:
            # Select top agents for collective reasoning
            agents = self._select_collective_agents(generation)

            if len(agents) < self.min_agents_for_collective:
                self.logger.warning(f"Not enough agents for collective reasoning: {len(agents)}")
                return None

            # Create session
            session_id = f"collective_{uuid.uuid4().hex[:12]}"
            agent_ids = [a['agent_id'] for a in agents]
            lead_agent_id = agents[0]['agent_id']  # Top performer leads

            self.db.execute_query("""
                INSERT INTO collective_reasoning_sessions (
                    session_id, game_id, generation, agent_ids, agent_count,
                    lead_agent_id, reasoning_mode, consensus_threshold
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, game_id, generation, json.dumps(agent_ids),
                len(agent_ids), lead_agent_id, reasoning_mode,
                self.consensus_threshold
            ))

            self.logger.info(
                f"Started collective session {session_id}: {len(agents)} agents, "
                f"mode={reasoning_mode}"
            )

            return session_id

        except Exception as e:
            self.logger.error(f"Error starting collective session: {e}")
            return None

    def _select_collective_agents(self, generation: int) -> List[Dict]:
        """
        Select top-performing agents for collective reasoning.

        FIXED (2025-12-26): Now uses network historical performance, not just
        current generation. This allows collective reasoning to work even with
        few live agents by leveraging the network's accumulated knowledge.
        """
        try:
            # STRATEGY 1: Try current generation first
            agents = self.db.execute_query("""
                SELECT agent_id, agent_type, avg_score_per_game,
                       total_games_won, score_efficiency
                FROM agents
                WHERE generation = ? AND is_active = TRUE
                ORDER BY avg_score_per_game DESC, total_games_won DESC
                LIMIT ?
            """, (generation, self.max_agents_for_collective))

            if agents and len(agents) >= self.min_agents_for_collective:
                return agents

            # STRATEGY 2: Fall back to recent generations (last 5)
            # This uses network history when current generation is sparse
            agents = self.db.execute_query("""
                SELECT agent_id, agent_type, avg_score_per_game,
                       total_games_won, score_efficiency
                FROM agents
                WHERE generation >= ? AND is_active = TRUE
                ORDER BY avg_score_per_game DESC, total_games_won DESC
                LIMIT ?
            """, (max(0, generation - 5), self.max_agents_for_collective))

            if agents and len(agents) >= self.min_agents_for_collective:
                self.logger.info(f"Using cross-generation agents for collective reasoning")
                return agents

            # STRATEGY 3: Use top historical performers regardless of generation
            # This ensures collective reasoning can always draw from network knowledge
            agents = self.db.execute_query("""
                SELECT agent_id, agent_type, avg_score_per_game,
                       total_games_won, score_efficiency
                FROM agents
                WHERE total_games_won > 0
                ORDER BY total_games_won DESC, avg_score_per_game DESC
                LIMIT ?
            """, (self.max_agents_for_collective,))

            if agents:
                self.logger.info(f"Using historical top performers for collective reasoning")
                return agents

            return []

        except Exception as e:
            self.logger.error(f"Error selecting agents: {e}")
            return []

    def propose_action(self, session_id: str, agent_id: str,
                      action: int, coordinates: Optional[Tuple[int, int]],
                      reasoning: str, confidence: float) -> Optional[str]:
        """
        Agent proposes an action for the collective to vote on.

        Args:
            session_id: Collective session
            agent_id: Proposing agent
            action: ACTION1-7
            coordinates: Coordinates if ACTION6
            reasoning: Why this action?
            confidence: Agent's confidence (0-1)

        Returns:
            proposal_id if created, None otherwise
        """
        try:
            # Get current turn
            session = self.db.execute_query("""
                SELECT current_turn FROM collective_reasoning_sessions
                WHERE session_id = ?
            """, (session_id,))

            if not session:
                return None

            turn_number = session[0]['current_turn']

            # Create proposal
            proposal_id = f"prop_{uuid.uuid4().hex[:12]}"

            self.db.execute_query("""
                INSERT INTO collective_action_proposals (
                    proposal_id, session_id, turn_number, proposing_agent_id,
                    proposed_action, action_coordinates, reasoning, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id, session_id, turn_number, agent_id,
                action, json.dumps(coordinates) if coordinates else None,
                reasoning, confidence
            ))

            self.logger.info(
                f"Agent {agent_id[:8]} proposed ACTION{action} "
                f"(confidence: {confidence:.2f})"
            )

            return proposal_id

        except Exception as e:
            self.logger.error(f"Error creating proposal: {e}")
            return None

    def vote_on_proposal(self, proposal_id: str, voting_agent_id: str,
                        vote_choice: str, reasoning: str,
                        confidence: float) -> bool:
        """
        Agent votes on a proposed action.

        Args:
            proposal_id: Proposal to vote on
            voting_agent_id: Agent voting
            vote_choice: 'for', 'against', or 'abstain'
            reasoning: Why this vote?
            confidence: Confidence in vote

        Returns:
            True if vote recorded, False otherwise
        """
        try:
            # Calculate vote weight based on agent performance
            vote_weight = self._calculate_vote_weight(voting_agent_id)

            # Record vote
            vote_id = f"vote_{uuid.uuid4().hex[:12]}"

            self.db.execute_query("""
                INSERT INTO collective_votes (
                    vote_id, proposal_id, voting_agent_id, vote_choice,
                    vote_weight, vote_reasoning, confidence_in_vote
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                vote_id, proposal_id, voting_agent_id, vote_choice,
                vote_weight, reasoning, confidence
            ))

            # Update proposal vote counts
            if vote_choice == 'for':
                self.db.execute_query("""
                    UPDATE collective_action_proposals
                    SET votes_for = votes_for + 1
                    WHERE proposal_id = ?
                """, (proposal_id,))
            elif vote_choice == 'against':
                self.db.execute_query("""
                    UPDATE collective_action_proposals
                    SET votes_against = votes_against + 1
                    WHERE proposal_id = ?
                """, (proposal_id,))
            else:
                self.db.execute_query("""
                    UPDATE collective_action_proposals
                    SET votes_abstain = votes_abstain + 1
                    WHERE proposal_id = ?
                """, (proposal_id,))

            return True

        except Exception as e:
            self.logger.error(f"Error recording vote: {e}")
            return False

    def _calculate_vote_weight(self, agent_id: str) -> float:
        """Calculate agent's vote weight based on performance"""
        try:
            agent = self.db.execute_query("""
                SELECT avg_score_per_game, total_games_won, score_efficiency
                FROM agents
                WHERE agent_id = ?
            """, (agent_id,))

            if not agent:
                return 1.0

            agent = agent[0]

            # Weight based on performance metrics
            score_weight = min(1.5, agent['avg_score_per_game'] / 10.0)
            win_weight = min(1.5, agent['total_games_won'] / 5.0)
            efficiency_weight = min(1.5, agent['score_efficiency'] * 2.0)

            total_weight = (score_weight + win_weight + efficiency_weight) / 3.0
            return max(0.5, min(2.0, total_weight))  # Clamp between 0.5 and 2.0

        except Exception as e:
            self.logger.error(f"Error calculating vote weight: {e}")
            return 1.0

    def resolve_voting(self, session_id: str, turn_number: int) -> Optional[Dict]:
        """
        Resolve voting for current turn and determine consensus action.

        Returns:
            Selected proposal dict if consensus reached, None otherwise
        """
        try:
            # Get all proposals for this turn
            proposals = self.db.execute_query("""
                SELECT * FROM collective_action_proposals
                WHERE session_id = ? AND turn_number = ?
                ORDER BY votes_for DESC
            """, (session_id, turn_number))

            if not proposals:
                return None

            # Calculate weighted votes for each proposal
            for proposal in proposals:
                votes = self.db.execute_query("""
                    SELECT vote_choice, vote_weight
                    FROM collective_votes
                    WHERE proposal_id = ?
                """, (proposal['proposal_id'],))

                weighted_for = sum(v['vote_weight'] for v in votes if v['vote_choice'] == 'for')
                weighted_against = sum(v['vote_weight'] for v in votes if v['vote_choice'] == 'against')
                total_weight = weighted_for + weighted_against

                if total_weight > 0:
                    consensus_ratio = weighted_for / total_weight
                else:
                    consensus_ratio = 0.0

                proposal['consensus_ratio'] = consensus_ratio

            # Select proposal with highest consensus
            best_proposal = max(proposals, key=lambda p: p.get('consensus_ratio', 0.0))

            # Check if consensus threshold met
            session = self.db.execute_query("""
                SELECT consensus_threshold FROM collective_reasoning_sessions
                WHERE session_id = ?
            """, (session_id,))

            threshold = session[0]['consensus_threshold'] if session else 0.6

            if best_proposal['consensus_ratio'] >= threshold:
                # Mark proposal as accepted
                self.db.execute_query("""
                    UPDATE collective_action_proposals
                    SET proposal_accepted = TRUE, voted_at = ?
                    WHERE proposal_id = ?
                """, (datetime.now().isoformat(), best_proposal['proposal_id']))

                # Update session
                self.db.execute_query("""
                    UPDATE collective_reasoning_sessions
                    SET consensus_reached_count = consensus_reached_count + 1
                    WHERE session_id = ?
                """, (session_id,))

                self.logger.info(
                    f"Consensus reached: ACTION{best_proposal['proposed_action']} "
                    f"({best_proposal['consensus_ratio']*100:.1f}% agreement)"
                )

                return best_proposal
            else:
                # No consensus
                self.db.execute_query("""
                    UPDATE collective_reasoning_sessions
                    SET disagreement_count = disagreement_count + 1
                    WHERE session_id = ?
                """, (session_id,))

                self.logger.info(
                    f"No consensus reached (best: {best_proposal['consensus_ratio']*100:.1f}%)"
                )

                return None

        except Exception as e:
            self.logger.error(f"Error resolving voting: {e}")
            return None

    def record_collective_insight(self, session_id: str, generation: int,
                                 insight_type: str, description: str,
                                 contributing_agents: List[str],
                                 confidence: float) -> Optional[str]:
        """Record an emergent insight from collective reasoning"""
        try:
            insight_id = f"insight_collective_{uuid.uuid4().hex[:12]}"

            self.db.execute_query("""
                INSERT INTO collective_insights (
                    insight_id, session_id, generation, insight_type,
                    insight_description, contributing_agents, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                insight_id, session_id, generation, insight_type,
                description, json.dumps(contributing_agents), confidence
            ))

            self.logger.info(f"Recorded collective insight: {insight_type}")

            return insight_id

        except Exception as e:
            self.logger.error(f"Error recording insight: {e}")
            return None

    def complete_session(self, session_id: str, final_score: float):
        """Mark collective reasoning session as complete"""
        try:
            self.db.execute_query("""
                UPDATE collective_reasoning_sessions
                SET session_status = 'completed',
                    final_score = ?,
                    score_improvement = final_score - initial_score,
                    completed_at = ?
                WHERE session_id = ?
            """, (final_score, datetime.now().isoformat(), session_id))

            self.logger.info(f"Completed collective session {session_id}")

        except Exception as e:
            self.logger.error(f"Error completing session: {e}")

    def get_collective_stats(self) -> Dict[str, Any]:
        """Get collective reasoning statistics"""
        try:
            stats = self.db.execute_query("""
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN session_status = 'completed' THEN 1 ELSE 0 END) as completed,
                    AVG(score_improvement) as avg_score_improvement,
                    AVG(consensus_reached_count) as avg_consensus_count,
                    AVG(disagreement_count) as avg_disagreement_count,
                    AVG(avg_confidence) as avg_confidence
                FROM collective_reasoning_sessions
            """)

            insights = self.db.execute_query("""
                SELECT COUNT(*) as total_insights,
                       AVG(confidence_score) as avg_confidence
                FROM collective_insights
            """)

            return {
                'sessions': stats[0] if stats else {},
                'insights': insights[0] if insights else {}
            }

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}
