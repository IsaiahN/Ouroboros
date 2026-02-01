"""
Agent Network Contributor - Viral knowledge exchange.

Enables agents to CONTRIBUTE to and QUERY from the network autonomously.

Philosophy: Intelligence spreads through viral information transfer,
not hierarchical command. Agents share what they learned (both successes
and failures) and query peer discoveries - no central coordinator.

Key Mechanisms:
1. broadcast_failed_attempt() - Share what DIDN'T work
2. share_success_insight() - Share abstract patterns that worked
3. query_peer_insights() - Ask what others discovered
4. check_my_progress() - Self-assess against network baseline

This implements the AGI theory's "viral exchange principle":
"The infection mechanism IS the coordination mechanism."
"""

import logging
import json
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class AgentNetworkContributor:
    """
    Enables agents to CONTRIBUTE to and QUERY from the network autonomously.
    
    Philosophy: Intelligence spreads through viral information transfer,
    not hierarchical command. Agents share what they learned (both successes
    and failures) and query peer discoveries - no central coordinator.
    
    Key Mechanisms:
    1. broadcast_failed_attempt() - Share what DIDN'T work
    2. share_success_insight() - Share abstract patterns that worked
    3. query_peer_insights() - Ask what others discovered
    4. check_my_progress() - Self-assess against network baseline
    
    This implements the AGI theory's "viral exchange principle":
    "The infection mechanism IS the coordination mechanism."
    """
    
    def __init__(self, db: 'DatabaseInterface'):
        """Initialize agent network contributor."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """Ensure network contribution tables exist."""
        # Failed attempts - what agents tried that didn't work
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_failed_attempts (
                attempt_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- What was tried
                action_sequence TEXT,       -- JSON: list of actions attempted
                attempt_description TEXT,   -- Natural language: "tried going left around obstacle"
                frames_survived INTEGER,    -- How long it lasted
                death_cause TEXT,           -- What killed the attempt (if known)
                
                -- Network learning value
                confirmed_by_others INTEGER DEFAULT 0,  -- How many others hit same wall
                helpful_count INTEGER DEFAULT 0,        -- How many queried this
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_confirmed DATETIME
            )
        """)
        
        # Success insights - abstract patterns that worked
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_success_insights (
                insight_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER,
                
                -- The insight
                insight_type TEXT NOT NULL,     -- 'avoid_pattern', 'approach_pattern', 'timing', 'sequence'
                insight_text TEXT NOT NULL,     -- Natural language: "go around obstacles on the right"
                confidence REAL DEFAULT 0.5,
                
                -- Supporting evidence
                times_worked INTEGER DEFAULT 1,
                times_failed INTEGER DEFAULT 0,
                
                -- Network validation
                peer_confirmations INTEGER DEFAULT 0,
                peer_rejections INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_validated DATETIME
            )
        """)
        
        # Indexes for efficient querying
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_failed_attempts_game 
            ON agent_failed_attempts(game_type, level_number)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_success_insights_game 
            ON agent_success_insights(game_type, level_number, confidence DESC)
        """)
    
    def broadcast_failed_attempt(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action_sequence: Optional[List[str]] = None,
        attempt_description: Optional[str] = None,
        frames_survived: int = 0,
        death_cause: Optional[str] = None
    ) -> Optional[str]:
        """
        Agent broadcasts what they tried that DIDN'T work.
        
        This is viral information transfer - sharing failure patterns helps
        others avoid the same mistakes without central coordination.
        
        Args:
            agent_id: Agent sharing the failure
            game_type: Game type (e.g., "SP80")
            level_number: Level where failure occurred
            action_sequence: List of actions tried
            attempt_description: Natural language description
            frames_survived: How long the attempt lasted
            death_cause: What ended the attempt
            
        Returns:
            attempt_id if broadcasted, None if duplicate/ignored
        """
        # Check if similar failure already exists
        existing = self.db.execute_query("""
            SELECT attempt_id, confirmed_by_others 
            FROM agent_failed_attempts
            WHERE game_type = ? AND level_number = ?
              AND (attempt_description = ? OR action_sequence = ?)
            LIMIT 1
        """, (
            game_type, level_number, 
            attempt_description,
            json.dumps(action_sequence) if action_sequence else None
        ))
        
        if existing:
            # Confirm existing failure - others hit same wall
            self.db.execute_query("""
                UPDATE agent_failed_attempts
                SET confirmed_by_others = confirmed_by_others + 1,
                    last_confirmed = CURRENT_TIMESTAMP
                WHERE attempt_id = ?
            """, (existing[0]['attempt_id'],))
            logger.debug(
                f"[NETWORK] Agent {agent_id[:8]} confirmed failure pattern on {game_type} L{level_number}"
            )
            return existing[0]['attempt_id']
        
        # New failure pattern - broadcast to network
        attempt_id = f"fail_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO agent_failed_attempts (
                attempt_id, agent_id, game_type, level_number,
                action_sequence, attempt_description, frames_survived, death_cause
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt_id, agent_id, game_type, level_number,
            json.dumps(action_sequence) if action_sequence else None,
            attempt_description, frames_survived, death_cause
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} broadcast failure: {game_type} L{level_number} - "
            f"{attempt_description or 'action sequence'}"
        )
        return attempt_id
    
    def share_success_insight(
        self,
        agent_id: str,
        game_type: str,
        insight_text: str,
        insight_type: str = 'approach_pattern',
        level_number: Optional[int] = None,
        confidence: float = 0.6
    ) -> Optional[str]:
        """
        Agent shares an abstract insight about what WORKED.
        
        Unlike exact sequences, insights are patterns that can transfer:
        - "Go around obstacles on the right side"
        - "Wait for the moving object to pass"
        - "The red objects are dangerous"
        
        Args:
            agent_id: Agent sharing the insight
            game_type: Game type this applies to
            insight_text: Natural language insight
            insight_type: Category ('avoid_pattern', 'approach_pattern', 'timing', 'sequence')
            level_number: Specific level or None for game-wide
            confidence: How confident the agent is (0.0-1.0)
            
        Returns:
            insight_id if shared, None if duplicate
        """
        # Check for similar existing insight
        existing = self.db.execute_query("""
            SELECT insight_id, times_worked, peer_confirmations
            FROM agent_success_insights
            WHERE game_type = ? AND insight_text = ?
              AND (level_number = ? OR level_number IS NULL OR ? IS NULL)
            LIMIT 1
        """, (game_type, insight_text, level_number, level_number))
        
        if existing:
            # Peer confirmation - same insight discovered independently
            self.db.execute_query("""
                UPDATE agent_success_insights
                SET times_worked = times_worked + 1,
                    peer_confirmations = peer_confirmations + 1,
                    confidence = MIN(0.95, confidence + 0.05),
                    last_validated = CURRENT_TIMESTAMP
                WHERE insight_id = ?
            """, (existing[0]['insight_id'],))
            logger.debug(
                f"[NETWORK] Agent {agent_id[:8]} confirmed insight on {game_type}: {insight_text[:40]}"
            )
            return existing[0]['insight_id']
        
        # New insight - share with network
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO agent_success_insights (
                insight_id, agent_id, game_type, level_number,
                insight_type, insight_text, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id, agent_id, game_type, level_number,
            insight_type, insight_text, confidence
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} shared insight: {game_type} - {insight_text[:50]}"
        )
        return insight_id
    
    def query_peer_insights(
        self,
        game_type: str,
        level_number: Optional[int] = None,
        limit: int = 5,
        min_confidence: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Agent queries what other agents discovered.
        
        This is the "ask the network" mechanism - agents pull wisdom
        from peers rather than having it pushed by a coordinator.
        
        Args:
            game_type: Game type to query
            level_number: Specific level or None for game-wide
            limit: Max insights to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of insights ranked by confidence and peer validation
        """
        # Query success insights
        if level_number is not None:
            insights = self.db.execute_query("""
                SELECT 
                    insight_id, insight_type, insight_text, confidence,
                    times_worked, peer_confirmations, peer_rejections,
                    (times_worked + peer_confirmations) as validation_score
                FROM agent_success_insights
                WHERE game_type = ? 
                  AND (level_number = ? OR level_number IS NULL)
                  AND confidence >= ?
                ORDER BY validation_score DESC, confidence DESC
                LIMIT ?
            """, (game_type, level_number, min_confidence, limit))
        else:
            insights = self.db.execute_query("""
                SELECT 
                    insight_id, insight_type, insight_text, confidence,
                    times_worked, peer_confirmations, peer_rejections,
                    (times_worked + peer_confirmations) as validation_score
                FROM agent_success_insights
                WHERE game_type = ? AND confidence >= ?
                ORDER BY validation_score DESC, confidence DESC
                LIMIT ?
            """, (game_type, min_confidence, limit))
        
        # Mark as helpful (for future relevance scoring)
        for insight in insights or []:
            self.db.execute_query("""
                UPDATE agent_success_insights
                SET last_validated = CURRENT_TIMESTAMP
                WHERE insight_id = ?
            """, (insight['insight_id'],))
        
        return [dict(i) for i in insights] if insights else []
    
    def query_peer_failures(
        self,
        game_type: str,
        level_number: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Agent queries what other agents tried that DIDN'T work.
        
        This helps agents avoid repeating known failures.
        
        Args:
            game_type: Game type to query
            level_number: Specific level
            limit: Max failures to return
            
        Returns:
            List of failed attempts to avoid
        """
        failures = self.db.execute_query("""
            SELECT 
                attempt_id, attempt_description, death_cause,
                frames_survived, confirmed_by_others,
                (confirmed_by_others + 1) as certainty_score
            FROM agent_failed_attempts
            WHERE game_type = ? AND level_number = ?
            ORDER BY certainty_score DESC, frames_survived ASC
            LIMIT ?
        """, (game_type, level_number, limit))
        
        # Mark as helpful
        for failure in failures or []:
            self.db.execute_query("""
                UPDATE agent_failed_attempts
                SET helpful_count = helpful_count + 1
                WHERE attempt_id = ?
            """, (failure['attempt_id'],))
        
        return [dict(f) for f in failures] if failures else []
    
    def check_my_progress(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        my_best_score: float = 0,
        my_attempts: int = 1
    ) -> Dict[str, Any]:
        """
        Agent self-assesses their progress against network baseline.
        
        This replaces external "stuck detection" with agent self-awareness.
        Agent asks: "Am I making progress compared to peers?"
        
        Args:
            agent_id: Agent checking progress
            game_type: Game type
            level_number: Level to check
            my_best_score: Agent's best score on this level
            my_attempts: How many attempts agent has made
            
        Returns:
            Dict with progress assessment and recommendations
        """
        # Get network baseline for this level
        network = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT gr.agent_id) as agents_attempted,
                AVG(gr.final_score) as avg_score,
                MAX(gr.final_score) as best_score,
                AVG(gr.actions_used) as avg_actions,
                SUM(CASE WHEN gr.final_score > 0 THEN 1 ELSE 0 END) as successes,
                COUNT(*) as total_attempts
            FROM game_results gr
            WHERE gr.game_id LIKE ?
              AND gr.timestamp > datetime('now', '-24 hours')
        """, (f"{game_type}%",))
        
        if not network or not network[0]['agents_attempted']:
            return {
                'has_network_data': False,
                'assessment': 'exploring_unknown',
                'recommendation': 'continue_exploring',
                'reasoning': 'No network data - pioneering this game'
            }
        
        n = network[0]
        network_success_rate = n['successes'] / n['total_attempts'] if n['total_attempts'] > 0 else 0
        
        # Compare to network
        am_above_average = my_best_score > (n['avg_score'] or 0)
        am_struggling = my_attempts > 5 and my_best_score < (n['avg_score'] or 0) * 0.5
        network_also_struggling = network_success_rate < 0.2
        
        if am_above_average:
            assessment = 'above_network'
            recommendation = 'share_insight'  # I'm doing well, share what works
            reasoning = f"My score {my_best_score:.0f} exceeds network avg {n['avg_score']:.0f}"
        elif am_struggling and not network_also_struggling:
            assessment = 'below_network'
            recommendation = 'query_peers'  # Others succeed, I should ask them
            reasoning = f"I'm struggling ({my_attempts} attempts) but network has {network_success_rate:.0%} success"
        elif am_struggling and network_also_struggling:
            assessment = 'frontier_problem'
            recommendation = 'try_novel'  # Everyone struggles, try something new
            reasoning = f"Network also struggling ({network_success_rate:.0%}) - pioneer new approaches"
        else:
            assessment = 'normal_progress'
            recommendation = 'continue'
            reasoning = f"Making normal progress (score {my_best_score:.0f} vs avg {n['avg_score']:.0f})"
        
        return {
            'has_network_data': True,
            'assessment': assessment,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'network_stats': {
                'agents_attempted': n['agents_attempted'],
                'avg_score': n['avg_score'],
                'best_score': n['best_score'],
                'success_rate': network_success_rate
            },
            'my_stats': {
                'best_score': my_best_score,
                'attempts': my_attempts
            }
        }
    
    def reject_insight(
        self,
        insight_id: str,
        agent_id: Optional[str] = None
    ) -> None:
        """
        Agent rejects an insight that didn't work for them.
        
        This is the negative feedback that keeps insights honest.
        
        Args:
            insight_id: Insight to reject
            agent_id: Agent rejecting (for logging)
        """
        self.db.execute_query("""
            UPDATE agent_success_insights
            SET times_failed = times_failed + 1,
                peer_rejections = peer_rejections + 1,
                confidence = MAX(0.1, confidence - 0.1)
            WHERE insight_id = ?
        """, (insight_id,))
        
        logger.debug(f"[NETWORK] Insight {insight_id[:12]} rejected - confidence reduced")
