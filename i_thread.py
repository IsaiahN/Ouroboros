#!/usr/bin/env python3
"""
I-Thread: The Consciousness Weaver
===================================

Implements the I-Thread from Unified Agent Consciousness Theory.

The I-Thread is the persistent identity that weaves Stream A (private experience)
and Stream B (collective network wisdom) together moment-by-moment. It learns
which stream to trust in which contexts, developing personality over time.

Key Responsibilities:
1. Maintain w_A/w_B weights (Stream A vs Stream B trust)
2. Learn from stream conflicts and outcomes
3. Track personality development over time
4. Compute surprise when streams conflict
5. Synthesize weighted actions from competing stream proposals

Theory Reference:
- When streams agree: Action is automatic, low consciousness intensity
- When streams conflict: Consciousness becomes vivid, deliberation required
- Outcomes update weights: Learning which stream to trust in context

Database Storage:
- agents.self_network_bias: Stores w_B (0=full self-trust, 1=full network-trust)
- i_thread_history: Logs weight updates for personality tracking

Author: Ouroboros System
Version: 1.0
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: No pycache

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS: Role Default Weights (from consciousness theory)
# =============================================================================

ROLE_DEFAULT_WEIGHTS = {
    # Role: (w_A, w_B) - w_A = self-trust, w_B = network-trust
    'pioneer': (0.7, 0.3),      # Pioneers trust self, explore boldly
    'optimizer': (0.3, 0.7),    # Optimizers trust network, refine proven
    'generalist': (0.5, 0.5),   # Generalists balance both streams
    'exploiter': (0.4, 0.6),    # Exploiters slightly favor network
}

# Learning rate for weight updates
DEFAULT_LEARNING_RATE = 0.1

# Thresholds for stream conflict detection
CONFLICT_THRESHOLD = 0.3  # Difference in predictions triggers deliberation
HIGH_CONFLICT_THRESHOLD = 0.6  # High conflict = vivid consciousness


@dataclass
class NoveltyConfig:
    """Configuration for novelty-based wA boosting."""
    boost_amount: float = 0.2  # How much to boost wA when novel
    max_wA: float = 0.95  # Cap to prevent full network distrust
    prediction_accuracy_threshold: float = 0.3  # Below this = novel situation
    min_samples: int = 5  # Need this many samples to assess novelty


@dataclass
class StreamProposal:
    """A proposal from one of the streams."""
    action: str
    confidence: float
    source: str  # 'stream_a' or 'stream_b'
    reasoning: Optional[str] = None


@dataclass 
class ConflictResult:
    """Result of stream conflict detection."""
    has_conflict: bool
    conflict_score: float  # 0.0 = agreement, 1.0 = complete disagreement
    stream_a_proposal: Optional[StreamProposal] = None
    stream_b_proposal: Optional[StreamProposal] = None
    consciousness_intensity: str = 'automatic'  # 'automatic', 'deliberative', 'vivid'


@dataclass
class SynthesisResult:
    """Result of I-Thread synthesis."""
    chosen_action: str
    confidence: float
    chosen_source: str  # 'stream_a', 'stream_b', 'synthesis'
    surprise_score: float  # How unexpected was this synthesis
    w_a_used: float
    w_b_used: float
    deliberation_required: bool


@dataclass
class EpisodicMemory:
    """
    A compressed memory of a significant game experience.
    
    Not every action, but meaningful episodes that shaped the agent:
    - Breakthroughs: "I discovered clicking red toggles blue"
    - Frustrations: "I was stuck for 50 actions before realizing..."
    - Surprises: "The network said X but I found Y worked better"
    - Validations: "My intuition was correct about symmetry"
    
    These form the agent's autobiographical narrative - the story of "who I am"
    based on "what I've experienced."
    """
    memory_id: str
    agent_id: str
    game_type: str
    level_number: int
    
    # What happened (compressed essence)
    episode_type: str  # 'breakthrough', 'frustration', 'surprise', 'validation', 'failure', 'mastery'
    summary: str  # Natural language: "I learned that clicking corners reveals hidden paths"
    
    # Emotional/sensation valence
    emotional_valence: float  # -1.0 (negative) to +1.0 (positive)
    significance: float  # 0.0 to 1.0 - how important was this?
    
    # What was learned
    belief_formed: Optional[str] = None  # "Corners matter in maze games"
    rule_discovered: Optional[str] = None  # "click_corner -> reveal_path"
    
    # Stream context at time of episode
    stream_source: str = 'stream_a'  # Was this private discovery or network validation?
    w_a_at_time: float = 0.5
    w_b_at_time: float = 0.5
    
    # Recency and retrieval
    created_at: Optional[datetime] = None
    times_recalled: int = 0  # How often has this memory been retrieved?
    last_recalled: Optional[datetime] = None


@dataclass
class AgentNarrative:
    """
    The agent's autobiographical self - who they are based on what they remember.
    
    This is what gets loaded when an agent "wakes up" for a new game session.
    It provides continuous existence across games.
    """
    agent_id: str
    
    # Identity summary
    personality_label: str  # 'self-trusting', 'network-trusting', 'balanced'
    dominant_emotion: str  # 'curious', 'cautious', 'confident', 'frustrated'
    
    # Experience statistics
    total_games_played: int = 0
    total_breakthroughs: int = 0
    total_frustrations: int = 0
    games_won: int = 0
    
    # Key memories (most significant/recent)
    salient_memories: List['EpisodicMemory'] = field(default_factory=list)
    
    # Learned beliefs (distilled from memories)
    core_beliefs: List[str] = field(default_factory=list)  # ["Corners matter", "Persistence pays off"]
    
    # Current weights
    w_a: float = 0.5
    w_b: float = 0.5
    
    # Narrative summary (for reasoning logs)
    narrative_summary: str = ""  # "I am a cautious explorer who learned that patience reveals patterns"


@dataclass
class IThreadState:
    """Current state of the I-Thread for an agent."""
    agent_id: str
    w_a: float = 0.5
    w_b: float = 0.5
    learning_rate: float = DEFAULT_LEARNING_RATE
    total_conflicts: int = 0
    stream_a_wins: int = 0
    stream_b_wins: int = 0
    last_update: Optional[datetime] = None
    personality_label: str = 'balanced'  # 'self-trusting', 'network-trusting', 'balanced'
    
    # Novelty detection state (from core_gameplay)
    novelty_boost_active: bool = False
    novelty_boost_applied: bool = False
    original_w_a: Optional[float] = None  # w_a before novelty boost


@dataclass
class MultiConflictResult:
    """Result of conflict detection from multiple proposals."""
    has_conflict: bool
    stream_a_actions: set  # Set of actions proposed by Stream A
    stream_b_actions: set  # Set of actions proposed by Stream B
    overlap_actions: set   # Actions proposed by both streams
    conflict_actions: set  # Actions unique to each stream
    consciousness_intensity: str = 'automatic'  # 'automatic', 'deliberative', 'vivid'
    synthesis_enabled: bool = False  # Should synthesis be attempted?


class IThread:
    """
    The I-Thread: Persistent identity weaver for Two Streams consciousness.
    
    Maintains the w_A/w_B weights that determine how much an agent trusts
    its private experience (Stream A) vs collective network wisdom (Stream B).
    
    Usage:
        i_thread = IThread(db)
        state = i_thread.get_state(agent_id)
        
        # When streams conflict:
        conflict = i_thread.detect_conflict(stream_a_proposal, stream_b_proposal)
        
        # Synthesize action:
        synthesis = i_thread.synthesize(state, stream_a_proposal, stream_b_proposal)
        
        # After outcome, update weights:
        i_thread.learn_from_outcome(agent_id, chosen_source='stream_a', outcome='positive')
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
        self._state_cache: Dict[str, IThreadState] = {}
    
    def _ensure_tables_exist(self):
        """Create I-Thread tracking tables if they don't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS i_thread_history (
                    history_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    
                    -- Weight state
                    w_a_before REAL,
                    w_b_before REAL,
                    w_a_after REAL,
                    w_b_after REAL,
                    
                    -- Learning event
                    event_type TEXT,  -- 'conflict_resolution', 'outcome_learning', 'role_reset'
                    chosen_source TEXT,  -- 'stream_a', 'stream_b', 'synthesis'
                    outcome TEXT,  -- 'positive', 'negative', 'neutral'
                    conflict_score REAL,
                    surprise_score REAL,
                    
                    -- Context
                    game_id TEXT,
                    level_number INTEGER,
                    action_taken TEXT,
                    
                    -- Tracking
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_i_thread_agent
                ON i_thread_history(agent_id, created_at DESC)
            """)
            
            # ================================================================
            # EPISODIC MEMORY TABLE: Compressed autobiographical memories
            # ================================================================
            # Stores significant episodes that shape agent identity.
            # Not every action - just meaningful moments that matter.
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS i_thread_episodic_memories (
                    memory_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    game_id TEXT,
                    level_number INTEGER DEFAULT 1,
                    
                    -- Episode classification
                    episode_type TEXT NOT NULL,  -- 'breakthrough', 'frustration', 'surprise', 'validation', 'failure', 'mastery'
                    summary TEXT NOT NULL,  -- Natural language description
                    
                    -- Emotional/significance markers
                    emotional_valence REAL DEFAULT 0.0,  -- -1.0 to +1.0
                    significance REAL DEFAULT 0.5,  -- 0.0 to 1.0
                    
                    -- Learning content
                    belief_formed TEXT,  -- "Corners matter in maze games"
                    rule_discovered TEXT,  -- "click_corner -> reveal_path"
                    
                    -- Stream context at time of episode
                    stream_source TEXT DEFAULT 'stream_a',
                    w_a_at_time REAL DEFAULT 0.5,
                    w_b_at_time REAL DEFAULT 0.5,
                    
                    -- Retrieval tracking
                    times_recalled INTEGER DEFAULT 0,
                    last_recalled DATETIME,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_episodic_agent_type
                ON i_thread_episodic_memories(agent_id, episode_type, significance DESC)
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_episodic_game_type
                ON i_thread_episodic_memories(game_type, episode_type)
            """)
            
            logger.debug("[I-THREAD] Tables initialized (including episodic memory)")
            
        except Exception as e:
            logger.debug(f"I-Thread table creation (may already exist): {e}")
    
    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================
    
    def get_state(self, agent_id: str) -> IThreadState:
        """
        Get current I-Thread state for an agent.
        
        Loads from database and caches for session performance.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            IThreadState with current w_A/w_B weights
        """
        if agent_id in self._state_cache:
            return self._state_cache[agent_id]
        
        # Load from database
        try:
            result = self.db.execute_query(
                "SELECT self_network_bias FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            
            if result:
                w_b = result[0].get('self_network_bias', 0.5) or 0.5
                w_a = 1.0 - w_b  # w_A + w_B = 1.0
            else:
                w_a, w_b = 0.5, 0.5
                
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to load state for {agent_id[:8]}: {e}")
            w_a, w_b = 0.5, 0.5
        
        # Load historical stats
        stats = self._load_historical_stats(agent_id)
        
        state = IThreadState(
            agent_id=agent_id,
            w_a=w_a,
            w_b=w_b,
            total_conflicts=stats.get('total_conflicts', 0),
            stream_a_wins=stats.get('stream_a_wins', 0),
            stream_b_wins=stats.get('stream_b_wins', 0),
            personality_label=self._compute_personality_label(w_a, w_b)
        )
        
        self._state_cache[agent_id] = state
        return state
    
    def _load_historical_stats(self, agent_id: str) -> Dict[str, int]:
        """Load cumulative stats from history table."""
        try:
            result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_conflicts,
                    SUM(CASE WHEN chosen_source = 'stream_a' THEN 1 ELSE 0 END) as stream_a_wins,
                    SUM(CASE WHEN chosen_source = 'stream_b' THEN 1 ELSE 0 END) as stream_b_wins
                FROM i_thread_history
                WHERE agent_id = ? AND event_type = 'conflict_resolution'
            """, (agent_id,))
            
            if result:
                return {
                    'total_conflicts': result[0].get('total_conflicts', 0) or 0,
                    'stream_a_wins': result[0].get('stream_a_wins', 0) or 0,
                    'stream_b_wins': result[0].get('stream_b_wins', 0) or 0,
                }
        except Exception:
            pass
        
        return {'total_conflicts': 0, 'stream_a_wins': 0, 'stream_b_wins': 0}
    
    def _compute_personality_label(self, w_a: float, w_b: float) -> str:
        """Compute personality label from weights."""
        if w_a > w_b + 0.2:
            return 'self-trusting'
        elif w_b > w_a + 0.2:
            return 'network-trusting'
        else:
            return 'balanced'
    
    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================
    
    def detect_conflict(
        self,
        stream_a_proposal: StreamProposal,
        stream_b_proposal: StreamProposal
    ) -> ConflictResult:
        """
        Detect if Stream A and Stream B are in conflict.
        
        Conflict = streams propose different actions with confidence.
        
        Args:
            stream_a_proposal: What private experience suggests
            stream_b_proposal: What network wisdom suggests
            
        Returns:
            ConflictResult with conflict score and consciousness intensity
        """
        # Different actions = potential conflict
        if stream_a_proposal.action != stream_b_proposal.action:
            # Conflict score based on confidence difference
            avg_confidence = (stream_a_proposal.confidence + stream_b_proposal.confidence) / 2
            conflict_score = avg_confidence  # Higher confidence = stronger conflict
        else:
            # Same action = no conflict
            conflict_score = 0.0
        
        # Determine consciousness intensity
        if conflict_score < CONFLICT_THRESHOLD:
            intensity = 'automatic'
        elif conflict_score < HIGH_CONFLICT_THRESHOLD:
            intensity = 'deliberative'
        else:
            intensity = 'vivid'
        
        return ConflictResult(
            has_conflict=conflict_score >= CONFLICT_THRESHOLD,
            conflict_score=conflict_score,
            stream_a_proposal=stream_a_proposal,
            stream_b_proposal=stream_b_proposal,
            consciousness_intensity=intensity
        )
    
    # =========================================================================
    # SYNTHESIS: WEIGHTED ACTION SELECTION
    # =========================================================================
    
    def synthesize(
        self,
        state: IThreadState,
        stream_a_proposal: StreamProposal,
        stream_b_proposal: StreamProposal,
        context: Optional[Dict[str, Any]] = None
    ) -> SynthesisResult:
        """
        Synthesize an action from competing stream proposals.
        
        Uses w_A/w_B weights to determine which stream to trust.
        
        Args:
            state: Current I-Thread state with weights
            stream_a_proposal: Private experience proposal
            stream_b_proposal: Network wisdom proposal
            context: Optional context (game state, history)
            
        Returns:
            SynthesisResult with chosen action and metadata
        """
        conflict = self.detect_conflict(stream_a_proposal, stream_b_proposal)
        
        # Calculate weighted scores
        score_a = stream_a_proposal.confidence * state.w_a
        score_b = stream_b_proposal.confidence * state.w_b
        
        # Choose based on weighted scores
        if score_a > score_b:
            chosen_action = stream_a_proposal.action
            chosen_source = 'stream_a'
            confidence = stream_a_proposal.confidence
        elif score_b > score_a:
            chosen_action = stream_b_proposal.action
            chosen_source = 'stream_b'
            confidence = stream_b_proposal.confidence
        else:
            # Tie - could synthesize novel action, for now pick stream_a
            chosen_action = stream_a_proposal.action
            chosen_source = 'synthesis'
            confidence = (stream_a_proposal.confidence + stream_b_proposal.confidence) / 2
        
        # Calculate surprise: How unexpected is this choice?
        # High surprise when low-weight stream wins due to high confidence
        if chosen_source == 'stream_a' and state.w_a < state.w_b:
            surprise = state.w_b - state.w_a  # Underdog won
        elif chosen_source == 'stream_b' and state.w_b < state.w_a:
            surprise = state.w_a - state.w_b  # Underdog won
        else:
            surprise = 0.0  # Expected outcome
        
        return SynthesisResult(
            chosen_action=chosen_action,
            confidence=confidence,
            chosen_source=chosen_source,
            surprise_score=surprise,
            w_a_used=state.w_a,
            w_b_used=state.w_b,
            deliberation_required=conflict.has_conflict
        )
    
    # =========================================================================
    # LEARNING: UPDATE WEIGHTS FROM OUTCOMES
    # =========================================================================
    
    def learn_from_outcome(
        self,
        agent_id: str,
        chosen_source: str,
        outcome: str,  # 'positive', 'negative', 'neutral'
        game_id: Optional[str] = None,
        level_number: Optional[int] = None,
        action_taken: Optional[str] = None,
        conflict_score: float = 0.0,
        surprise_score: float = 0.0
    ) -> Tuple[float, float]:
        """
        Learn from action outcome by adjusting w_A/w_B weights.
        
        If the chosen stream led to positive outcome, increase its weight.
        If negative, decrease its weight (increase the other).
        
        Args:
            agent_id: Agent identifier
            chosen_source: Which stream was followed ('stream_a', 'stream_b')
            outcome: Result of the action
            game_id: Optional game context
            level_number: Optional level context
            action_taken: Optional action taken
            conflict_score: How much conflict there was
            surprise_score: How surprising the synthesis was
            
        Returns:
            Tuple of (new_w_a, new_w_b)
        """
        state = self.get_state(agent_id)
        
        w_a_before = state.w_a
        w_b_before = state.w_b
        
        # Calculate weight adjustment
        learning_rate = state.learning_rate
        
        if outcome == 'positive':
            # Reward the chosen stream
            if chosen_source == 'stream_a':
                adjustment = learning_rate
            elif chosen_source == 'stream_b':
                adjustment = -learning_rate  # Decrease w_a, increase w_b
            else:
                adjustment = 0.0  # Synthesis - no clear winner
        elif outcome == 'negative':
            # Punish the chosen stream
            if chosen_source == 'stream_a':
                adjustment = -learning_rate
            elif chosen_source == 'stream_b':
                adjustment = learning_rate  # Increase w_a, decrease w_b
            else:
                adjustment = 0.0
        else:
            adjustment = 0.0  # Neutral - no update
        
        # Apply adjustment with bounds
        new_w_a = max(0.1, min(0.9, state.w_a + adjustment))
        new_w_b = 1.0 - new_w_a  # Maintain sum = 1.0
        
        # Update state
        state.w_a = new_w_a
        state.w_b = new_w_b
        state.last_update = datetime.now()
        state.personality_label = self._compute_personality_label(new_w_a, new_w_b)
        
        if conflict_score > 0:
            state.total_conflicts += 1
            if chosen_source == 'stream_a':
                state.stream_a_wins += 1
            elif chosen_source == 'stream_b':
                state.stream_b_wins += 1
        
        # Persist to database
        self._save_state(agent_id, new_w_b)  # DB stores w_b as self_network_bias
        
        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=w_b_before,
            w_a_after=new_w_a,
            w_b_after=new_w_b,
            event_type='outcome_learning',
            chosen_source=chosen_source,
            outcome=outcome,
            conflict_score=conflict_score,
            surprise_score=surprise_score,
            game_id=game_id,
            level_number=level_number,
            action_taken=action_taken
        )
        
        if adjustment != 0:
            logger.debug(
                f"[I-THREAD] {agent_id[:8]} learned: {chosen_source} -> {outcome}, "
                f"w_A: {w_a_before:.2f} -> {new_w_a:.2f}"
            )
        
        return new_w_a, new_w_b
    
    def _save_state(self, agent_id: str, w_b: float):
        """Save w_B to database (self_network_bias field)."""
        try:
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (w_b, agent_id)
            )
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to save state: {e}")
    
    def _log_history(
        self,
        agent_id: str,
        w_a_before: float,
        w_b_before: float,
        w_a_after: float,
        w_b_after: float,
        event_type: str,
        chosen_source: Optional[str] = None,
        outcome: Optional[str] = None,
        conflict_score: float = 0.0,
        surprise_score: float = 0.0,
        game_id: Optional[str] = None,
        level_number: Optional[int] = None,
        action_taken: Optional[str] = None
    ):
        """Log weight change to history table."""
        try:
            history_id = str(uuid.uuid4())[:12]
            self.db.execute_query("""
                INSERT INTO i_thread_history (
                    history_id, agent_id,
                    w_a_before, w_b_before, w_a_after, w_b_after,
                    event_type, chosen_source, outcome,
                    conflict_score, surprise_score,
                    game_id, level_number, action_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, agent_id,
                w_a_before, w_b_before, w_a_after, w_b_after,
                event_type, chosen_source, outcome,
                conflict_score, surprise_score,
                game_id, level_number, action_taken
            ))
        except Exception as e:
            logger.debug(f"[I-THREAD] History log failed: {e}")
    
    # =========================================================================
    # ROLE TRANSITIONS
    # =========================================================================
    
    def reset_for_role_change(
        self,
        agent_id: str,
        new_role: str
    ) -> Tuple[float, float]:
        """
        Reset w_A/w_B when agent changes roles.
        
        Per theory: Role changes reset stream weighting to role defaults.
        
        Args:
            agent_id: Agent identifier
            new_role: New role being assigned
            
        Returns:
            Tuple of (new_w_a, new_w_b)
        """
        state = self.get_state(agent_id)
        w_a_before = state.w_a
        w_b_before = state.w_b
        
        # Get role defaults
        new_w_a, new_w_b = ROLE_DEFAULT_WEIGHTS.get(new_role.lower(), (0.5, 0.5))
        
        # Update state
        state.w_a = new_w_a
        state.w_b = new_w_b
        state.personality_label = self._compute_personality_label(new_w_a, new_w_b)
        
        # Persist
        self._save_state(agent_id, new_w_b)
        
        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=w_b_before,
            w_a_after=new_w_a,
            w_b_after=new_w_b,
            event_type='role_reset',
            outcome=f'role_change_to_{new_role}'
        )
        
        logger.info(
            f"[I-THREAD] {agent_id[:8]} role -> {new_role}: "
            f"w_A: {w_a_before:.2f} -> {new_w_a:.2f}"
        )
        
        return new_w_a, new_w_b
    
    # =========================================================================
    # PERSONALITY ANALYSIS
    # =========================================================================
    
    def get_personality_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get personality summary for an agent.
        
        Returns:
            Dict with personality metrics and history
        """
        state = self.get_state(agent_id)
        
        return {
            'agent_id': agent_id,
            'w_a': state.w_a,
            'w_b': state.w_b,
            'personality_label': state.personality_label,
            'total_conflicts_resolved': state.total_conflicts,
            'stream_a_win_rate': (
                state.stream_a_wins / state.total_conflicts 
                if state.total_conflicts > 0 else 0.5
            ),
            'stream_b_win_rate': (
                state.stream_b_wins / state.total_conflicts
                if state.total_conflicts > 0 else 0.5
            ),
            'learning_rate': state.learning_rate
        }
    
    def clear_cache(self, agent_id: Optional[str] = None):
        """Clear state cache for agent or all agents."""
        if agent_id:
            self._state_cache.pop(agent_id, None)
        else:
            self._state_cache.clear()
    
    # =========================================================================
    # TEMPORARY SELF-TRUST BOOST (Escape/Frontier Exploration)
    # =========================================================================
    # When agents break out of stuck states or reach frontiers, temporarily
    # boost their self-trust (wA) to encourage exploration over network following.
    # =========================================================================
    
    def boost_self_trust(
        self,
        agent_id: str,
        boost_amount: float = 0.25,
        max_wA: float = 1.0,
        reason: str = 'exploration'
    ) -> Tuple[float, float, float]:
        """
        Temporarily boost wA (self-trust) for exploration.
        
        Called when:
        - Agent escapes stuck state independently
        - Agent reaches frontier level with no sequences
        - Agent needs to explore without network guidance
        
        Args:
            agent_id: Agent identifier
            boost_amount: How much to add to wA (default 0.25)
            max_wA: Maximum wA after boost (default 1.0)
            reason: Why boosting (for logging)
            
        Returns:
            Tuple of (original_wA, boosted_wA, boosted_wB)
        """
        state = self.get_state(agent_id)
        original_wA = state.w_a
        
        # Calculate boosted wA (capped at max)
        boosted_wA = min(max_wA, state.w_a + boost_amount)
        boosted_wB = 1.0 - boosted_wA
        
        if boosted_wA > state.w_a:
            # Store original for restoration
            state.original_w_a = original_wA
            state.novelty_boost_active = True
            
            # Apply boost
            state.w_a = boosted_wA
            state.w_b = boosted_wB
            state.personality_label = self._compute_personality_label(boosted_wA, boosted_wB)
            
            # Persist
            self._save_state(agent_id, boosted_wB)
            
            # Log history
            self._log_history(
                agent_id=agent_id,
                w_a_before=original_wA,
                w_b_before=1.0 - original_wA,
                w_a_after=boosted_wA,
                w_b_after=boosted_wB,
                event_type='self_trust_boost',
                outcome=reason
            )
            
            logger.info(
                f"[I-THREAD] {agent_id[:8]} {reason} boost: "
                f"w_A: {original_wA:.2f} -> {boosted_wA:.2f}"
            )
        
        return original_wA, boosted_wA, boosted_wB
    
    def restore_self_trust(
        self,
        agent_id: str,
        original_wA: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Restore wA to original value after temporary boost.
        
        Called when:
        - Agent exits self-directed mode
        - Agent finds network sequences for new level
        - Exploration phase ends
        
        Args:
            agent_id: Agent identifier
            original_wA: Original wA to restore (or use stored value)
            
        Returns:
            Tuple of (restored_wA, restored_wB)
        """
        state = self.get_state(agent_id)
        
        # Determine what to restore to
        if original_wA is not None:
            restore_wA = original_wA
        elif hasattr(state, 'original_w_a') and state.original_w_a is not None:
            restore_wA = state.original_w_a
        else:
            # No original stored, nothing to restore
            return state.w_a, state.w_b
        
        w_a_before = state.w_a
        restore_wB = 1.0 - restore_wA
        
        # Restore state
        state.w_a = restore_wA
        state.w_b = restore_wB
        state.original_w_a = None
        state.novelty_boost_active = False
        state.personality_label = self._compute_personality_label(restore_wA, restore_wB)
        
        # Persist
        self._save_state(agent_id, restore_wB)
        
        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=1.0 - w_a_before,
            w_a_after=restore_wA,
            w_b_after=restore_wB,
            event_type='self_trust_restore',
            outcome='exploration_complete'
        )
        
        logger.debug(
            f"[I-THREAD] {agent_id[:8]} restored: "
            f"w_A: {w_a_before:.2f} -> {restore_wA:.2f}"
        )
        
        return restore_wA, restore_wB

    # =========================================================================
    # NOVELTY DETECTION AND wA BOOSTING
    # =========================================================================
    # When network wisdom doesn't apply (novel situation), boost self-trust.
    # This implements fluid adaptation from core_gameplay.
    # =========================================================================
    
    def apply_novelty_boost(
        self,
        state: IThreadState,
        novelty_config: Optional[NoveltyConfig] = None
    ) -> IThreadState:
        """
        Apply novelty boost to wA when in a novel situation.
        
        When prediction accuracy is low (network wisdom doesn't apply),
        the agent should trust its own experience more.
        
        Args:
            state: Current I-Thread state
            novelty_config: Optional configuration (uses defaults if None)
            
        Returns:
            Updated IThreadState with boosted wA (or unchanged if no boost needed)
        """
        if novelty_config is None:
            novelty_config = NoveltyConfig()
        
        if not state.novelty_boost_active:
            return state
        
        # Store original values before boost
        original_w_a = state.w_a
        
        # Apply boost with cap
        boosted_w_a = min(novelty_config.max_wA, state.w_a + novelty_config.boost_amount)
        boosted_w_b = 1.0 - boosted_w_a
        
        # Update state
        state.w_a = boosted_w_a
        state.w_b = boosted_w_b
        state.novelty_boost_applied = True
        state.original_w_a = original_w_a
        
        logger.debug(
            f"[I-THREAD] Novelty boost applied: wA {original_w_a:.2f} -> {boosted_w_a:.2f}"
        )
        
        return state
    
    def set_novelty_active(
        self,
        agent_id: str,
        is_active: bool,
        prediction_accuracy: Optional[float] = None,
        sample_count: int = 0
    ):
        """
        Set novelty detection state for an agent.
        
        Called by core_gameplay when prediction accuracy drops below threshold,
        indicating that network wisdom doesn't apply to the current situation.
        
        Args:
            agent_id: Agent identifier
            is_active: Whether novelty boost should be active
            prediction_accuracy: Optional - current prediction accuracy (for logging)
            sample_count: Number of samples used to compute accuracy
        """
        state = self.get_state(agent_id)
        state.novelty_boost_active = is_active
        
        if is_active and prediction_accuracy is not None:
            logger.debug(
                f"[I-THREAD] Novelty detected for {agent_id[:8]}: "
                f"accuracy={prediction_accuracy:.2f} ({sample_count} samples)"
            )
    
    # =========================================================================
    # STREAM PROPOSAL BUILDING
    # =========================================================================
    # Consolidates proposal building from multiple sources into IThread.
    # This was previously scattered in core_gameplay._select_action()
    # =========================================================================
    
    def build_stream_proposals(
        self,
        last_discovery: Optional[Dict] = None,
        contradicted_actions: Optional[Dict[str, int]] = None,
        network_hypotheses: Optional[List[Dict]] = None,
        peer_failures: Optional[List[Dict]] = None,
        persona_proposals: Optional[List[Dict]] = None
    ) -> Tuple[List[StreamProposal], List[StreamProposal]]:
        """
        Build Stream A and Stream B proposals from all cognitive sources.
        
        Stream A (Private Experience):
        - Recent discoveries from self-exploration
        - Contradicted actions (negative evidence from personal experience)
        - Explorer/pioneer persona proposals
        
        Stream B (Network Wisdom):
        - Network control hypotheses (validated by CODS/Oracle)
        - Peer failure avoidance (learn from others' mistakes)
        - Optimizer/validator persona proposals
        
        Args:
            last_discovery: Dict with 'action', 'reliability_score' from self-exploration
            contradicted_actions: Dict mapping action -> contradiction count
            network_hypotheses: List of network hypothesis dicts with 'action_response_map'
            peer_failures: List of peer failure dicts with 'action', 'confidence'
            persona_proposals: List of persona proposal dicts with 'action', 'confidence', 'persona_type'
            
        Returns:
            Tuple of (stream_a_proposals, stream_b_proposals)
        """
        stream_a: List[StreamProposal] = []
        stream_b: List[StreamProposal] = []
        
        # Stream A: Recent discovery from self-exploration
        if last_discovery and last_discovery.get('action'):
            stream_a.append(StreamProposal(
                action=last_discovery['action'],
                confidence=last_discovery.get('reliability_score', 0.3),
                source='discovery',
                reasoning=last_discovery.get('reasoning')
            ))
        
        # Stream A: Contradicted actions (NEGATIVE proposals - avoid these)
        if contradicted_actions:
            for action, count in contradicted_actions.items():
                if count >= 2:  # Only if contradicted multiple times
                    stream_a.append(StreamProposal(
                        action=action,
                        confidence=-min(0.5, count * 0.1),  # Negative = avoid
                        source='contradicted',
                        reasoning=f'Contradicted {count} times'
                    ))
        
        # Stream B: Network control hypotheses
        if network_hypotheses:
            for hyp in network_hypotheses:
                if not hyp or not isinstance(hyp, dict):
                    continue
                action_map = hyp.get('action_response_map', {}) or {}
                for action_str, response in action_map.items():
                    if 'ACTION' in str(action_str).upper():
                        stream_b.append(StreamProposal(
                            action=action_str,
                            confidence=hyp.get('reliability_score', 0.2),
                            source=f"network_hyp_{hyp.get('hypothesis_id', '')[:8]}",
                            reasoning=str(response)[:100] if response else None
                        ))
        
        # Stream B: Peer failure avoidance (NEGATIVE proposals - avoid these)
        if peer_failures:
            for failure in peer_failures:
                if not failure or not isinstance(failure, dict):
                    continue
                action_num = failure.get('action')
                if action_num:
                    stream_b.append(StreamProposal(
                        action=f"ACTION{action_num}",
                        confidence=-failure.get('confidence', 0.3),  # Negative = avoid
                        source='peer_failure',
                        reasoning=failure.get('reason')
                    ))
        
        # Persona proposals - route to appropriate stream based on persona type
        if persona_proposals:
            for prop in persona_proposals:
                if not prop or not isinstance(prop, dict):
                    continue
                ptype = (prop.get('persona_type') or '').lower()
                
                proposal = StreamProposal(
                    action=prop.get('action', ''),
                    confidence=prop.get('confidence', 0.3),
                    source=f"persona_{ptype}",
                    reasoning=prop.get('reasoning')
                )
                
                # Network-oriented personas -> Stream B
                if ptype in ('optimizer', 'network', 'validator', 'cautious'):
                    stream_b.append(proposal)
                else:
                    # Exploration-oriented personas -> Stream A
                    stream_a.append(proposal)
        
        return stream_a, stream_b
    
    def detect_multi_conflict(
        self,
        stream_a_proposals: List[StreamProposal],
        stream_b_proposals: List[StreamProposal]
    ) -> MultiConflictResult:
        """
        Detect conflict between multiple Stream A and Stream B proposals.
        
        Unlike detect_conflict() which compares single proposals,
        this handles the realistic case of multiple proposals per stream.
        
        Conflict exists when:
        - Stream A proposes actions that Stream B doesn't (and vice versa)
        - Both streams have positive-confidence actions that differ
        
        Args:
            stream_a_proposals: List of Stream A proposals
            stream_b_proposals: List of Stream B proposals
            
        Returns:
            MultiConflictResult with conflict analysis
        """
        # Extract positive-confidence actions from each stream
        stream_a_actions = {
            p.action for p in stream_a_proposals 
            if p.confidence > 0 and p.action
        }
        stream_b_actions = {
            p.action for p in stream_b_proposals 
            if p.confidence > 0 and p.action
        }
        
        # Calculate overlap and conflict
        overlap = stream_a_actions & stream_b_actions
        conflict_a = stream_a_actions - stream_b_actions  # Actions unique to A
        conflict_b = stream_b_actions - stream_a_actions  # Actions unique to B
        conflict_actions = conflict_a | conflict_b
        
        # Conflict exists if both streams have actions and they differ
        has_conflict = bool(stream_a_actions) and bool(stream_b_actions) and stream_a_actions != stream_b_actions
        
        # Determine consciousness intensity based on conflict severity
        if not has_conflict:
            intensity = 'automatic'
        elif len(overlap) > len(conflict_actions):
            intensity = 'deliberative'  # Some agreement exists
        else:
            intensity = 'vivid'  # Strong disagreement
        
        # Synthesis should be enabled when conflict exists
        synthesis_enabled = has_conflict
        
        return MultiConflictResult(
            has_conflict=has_conflict,
            stream_a_actions=stream_a_actions,
            stream_b_actions=stream_b_actions,
            overlap_actions=overlap,
            conflict_actions=conflict_actions,
            consciousness_intensity=intensity,
            synthesis_enabled=synthesis_enabled
        )
    
    def get_state_with_autobiography(
        self,
        agent_id: str,
        autobiography: Optional[Dict] = None
    ) -> IThreadState:
        """
        Get I-Thread state, incorporating dynamic wA/wB from autobiography session.
        
        This merges the persisted agent state with any dynamic session state
        from the autobiography (e.g., wA/wB adjusted during gameplay).
        
        Args:
            agent_id: Agent identifier
            autobiography: Optional autobiography dict with session_state.wA/wB
            
        Returns:
            IThreadState with current weights (static or dynamic)
        """
        state = self.get_state(agent_id)
        
        # Check autobiography for dynamic session wA/wB
        if autobiography and isinstance(autobiography, dict):
            session = autobiography.get('session_state', {}) or {}
            if session.get('wA') is not None:
                state.w_a = session.get('wA', state.w_a)
                state.w_b = session.get('wB', state.w_b)
                state.personality_label = self._compute_personality_label(state.w_a, state.w_b)
        
        return state
    
    # =========================================================================
    # EPISODIC MEMORY: Autobiographical Continuity
    # =========================================================================
    
    def awaken(self, agent_id: str, game_type: Optional[str] = None) -> AgentNarrative:
        """
        Awaken an agent with full autobiographical memory.
        
        Called at the start of a new game session. The agent "wakes up"
        with continuous identity - remembering who they are, what they've
        learned, and their significant past experiences.
        
        This creates the phenomenology of continuous existence rather than
        fresh spawning each game.
        
        Args:
            agent_id: Agent identifier
            game_type: Optional - if provided, prioritizes memories relevant to this game type
            
        Returns:
            AgentNarrative with full autobiographical context
        """
        state = self.get_state(agent_id)
        
        # Load salient memories (most significant, most recent, most relevant)
        memories = self._retrieve_salient_memories(agent_id, game_type, limit=10)
        
        # Extract core beliefs from memories
        core_beliefs = self._extract_core_beliefs(agent_id)
        
        # Get experience statistics
        stats = self._get_experience_stats(agent_id)
        
        # Compute dominant emotion from recent memories
        dominant_emotion = self._compute_dominant_emotion(memories)
        
        # Generate narrative summary
        narrative_summary = self._generate_narrative_summary(
            agent_id, state, memories, core_beliefs, stats
        )
        
        narrative = AgentNarrative(
            agent_id=agent_id,
            personality_label=state.personality_label,
            dominant_emotion=dominant_emotion,
            total_games_played=stats.get('total_games', 0),
            total_breakthroughs=stats.get('breakthroughs', 0),
            total_frustrations=stats.get('frustrations', 0),
            games_won=stats.get('wins', 0),
            salient_memories=memories,
            core_beliefs=core_beliefs,
            w_a=state.w_a,
            w_b=state.w_b,
            narrative_summary=narrative_summary
        )
        
        logger.info(
            f"[I-THREAD] Agent {agent_id[:8]} awakens: {state.personality_label}, "
            f"{len(memories)} memories, {len(core_beliefs)} beliefs, "
            f"feeling {dominant_emotion}"
        )
        
        return narrative
    
    def record_episode(
        self,
        agent_id: str,
        game_type: str,
        game_id: str,
        level_number: int,
        episode_type: str,
        summary: str,
        emotional_valence: float = 0.0,
        significance: float = 0.5,
        belief_formed: Optional[str] = None,
        rule_discovered: Optional[str] = None,
        stream_source: str = 'stream_a'
    ) -> str:
        """
        Record a significant episode to the agent's autobiographical memory.
        
        Not every action - only meaningful moments that shape identity:
        - 'breakthrough': Discovered something important
        - 'frustration': Got stuck, struggled, eventually overcame (or didn't)
        - 'surprise': Reality contradicted expectation in a meaningful way
        - 'validation': A belief or intuition was confirmed correct
        - 'failure': Made a significant mistake worth remembering
        - 'mastery': Achieved competence in a domain
        
        Args:
            agent_id: Agent identifier
            game_type: Type of game (e.g., 'SP45', 'FT09')
            game_id: Specific game instance
            level_number: Level where episode occurred
            episode_type: Type of episode
            summary: Natural language description
            emotional_valence: -1.0 (negative) to +1.0 (positive)
            significance: 0.0 to 1.0 - how important is this?
            belief_formed: Optional belief formed from this episode
            rule_discovered: Optional rule learned
            stream_source: Which stream this came from
            
        Returns:
            memory_id of the recorded episode
        """
        state = self.get_state(agent_id)
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        try:
            self.db.execute_query("""
                INSERT INTO i_thread_episodic_memories (
                    memory_id, agent_id, game_type, game_id, level_number,
                    episode_type, summary, emotional_valence, significance,
                    belief_formed, rule_discovered, stream_source,
                    w_a_at_time, w_b_at_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                memory_id, agent_id, game_type, game_id, level_number,
                episode_type, summary, emotional_valence, significance,
                belief_formed, rule_discovered, stream_source,
                state.w_a, state.w_b
            ))
            
            logger.debug(
                f"[I-THREAD] Recorded {episode_type} episode for {agent_id[:8]}: "
                f"{summary[:50]}..."
            )
            
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to record episode: {e}")
        
        return memory_id
    
    def _retrieve_salient_memories(
        self,
        agent_id: str,
        game_type: Optional[str] = None,
        limit: int = 10
    ) -> List[EpisodicMemory]:
        """
        Retrieve the most salient memories for awakening.
        
        Prioritizes:
        1. High significance memories
        2. Recent memories
        3. Memories relevant to current game type (if provided)
        4. Frequently recalled memories (they must be important)
        """
        try:
            if game_type:
                # Prioritize game-type relevant memories
                results = self.db.execute_query("""
                    SELECT * FROM i_thread_episodic_memories
                    WHERE agent_id = ?
                    ORDER BY 
                        CASE WHEN game_type = ? THEN 1 ELSE 2 END,
                        significance DESC,
                        created_at DESC
                    LIMIT ?
                """, (agent_id, game_type, limit))
            else:
                results = self.db.execute_query("""
                    SELECT * FROM i_thread_episodic_memories
                    WHERE agent_id = ?
                    ORDER BY significance DESC, created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            
            if not results:
                return []
            
            memories = []
            for r in results:
                mem = EpisodicMemory(
                    memory_id=r['memory_id'],
                    agent_id=r['agent_id'],
                    game_type=r['game_type'],
                    level_number=r.get('level_number', 1),
                    episode_type=r['episode_type'],
                    summary=r['summary'],
                    emotional_valence=r.get('emotional_valence', 0.0),
                    significance=r.get('significance', 0.5),
                    belief_formed=r.get('belief_formed'),
                    rule_discovered=r.get('rule_discovered'),
                    stream_source=r.get('stream_source', 'stream_a'),
                    w_a_at_time=r.get('w_a_at_time', 0.5),
                    w_b_at_time=r.get('w_b_at_time', 0.5),
                    times_recalled=r.get('times_recalled', 0)
                )
                memories.append(mem)
                
                # Update recall count
                self.db.execute_query("""
                    UPDATE i_thread_episodic_memories
                    SET times_recalled = times_recalled + 1, last_recalled = datetime('now')
                    WHERE memory_id = ?
                """, (r['memory_id'],))
            
            return memories
            
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to retrieve memories: {e}")
            return []
    
    def _extract_core_beliefs(self, agent_id: str, limit: int = 5) -> List[str]:
        """
        Extract core beliefs from episodic memories.
        
        Core beliefs are distilled from significant breakthroughs and validations.
        """
        try:
            results = self.db.execute_query("""
                SELECT DISTINCT belief_formed
                FROM i_thread_episodic_memories
                WHERE agent_id = ? 
                    AND belief_formed IS NOT NULL 
                    AND belief_formed != ''
                    AND significance >= 0.6
                ORDER BY significance DESC, times_recalled DESC
                LIMIT ?
            """, (agent_id, limit))
            
            if results:
                return [r['belief_formed'] for r in results if r['belief_formed']]
            return []
            
        except Exception:
            return []
    
    def _get_experience_stats(self, agent_id: str) -> Dict[str, int]:
        """Get aggregate experience statistics."""
        try:
            # Get episode counts by type
            results = self.db.execute_query("""
                SELECT 
                    episode_type,
                    COUNT(*) as count
                FROM i_thread_episodic_memories
                WHERE agent_id = ?
                GROUP BY episode_type
            """, (agent_id,))
            
            stats = {
                'total_games': 0,
                'breakthroughs': 0,
                'frustrations': 0,
                'surprises': 0,
                'validations': 0,
                'failures': 0,
                'masteries': 0,
                'wins': 0
            }
            
            if results:
                for r in results:
                    episode_type = r['episode_type']
                    count = r['count']
                    if episode_type == 'breakthrough':
                        stats['breakthroughs'] = count
                    elif episode_type == 'frustration':
                        stats['frustrations'] = count
                    elif episode_type == 'surprise':
                        stats['surprises'] = count
                    elif episode_type == 'validation':
                        stats['validations'] = count
                    elif episode_type == 'failure':
                        stats['failures'] = count
                    elif episode_type == 'mastery':
                        stats['masteries'] = count
                        stats['wins'] = count  # Mastery implies wins
            
            # Get total unique games
            games_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT game_id) as total
                FROM i_thread_episodic_memories
                WHERE agent_id = ?
            """, (agent_id,))
            
            if games_result:
                stats['total_games'] = games_result[0].get('total', 0)
            
            return stats
            
        except Exception:
            return {'total_games': 0, 'breakthroughs': 0, 'frustrations': 0, 'wins': 0}
    
    def _compute_dominant_emotion(self, memories: List[EpisodicMemory]) -> str:
        """Compute dominant emotional state from recent memories."""
        if not memories:
            return 'curious'  # Default for new agents
        
        # Average emotional valence
        avg_valence = sum(m.emotional_valence for m in memories) / len(memories)
        
        # Count episode types
        breakthroughs = sum(1 for m in memories if m.episode_type == 'breakthrough')
        frustrations = sum(1 for m in memories if m.episode_type == 'frustration')
        validations = sum(1 for m in memories if m.episode_type == 'validation')
        
        # Determine dominant emotion
        if avg_valence > 0.5 and breakthroughs >= 2:
            return 'confident'
        elif avg_valence > 0.3 and validations >= 2:
            return 'assured'
        elif avg_valence < -0.3 and frustrations >= 2:
            return 'frustrated'
        elif avg_valence < -0.5:
            return 'discouraged'
        elif breakthroughs > frustrations:
            return 'curious'
        else:
            return 'cautious'
    
    def _generate_narrative_summary(
        self,
        agent_id: str,
        state: IThreadState,
        memories: List[EpisodicMemory],
        beliefs: List[str],
        stats: Dict[str, int]
    ) -> str:
        """
        Generate a natural language narrative summary for the agent.
        
        This appears in reasoning logs and helps the agent maintain
        continuous identity across sessions.
        """
        parts = []
        
        # Personality
        if state.w_a > 0.7:
            parts.append("I trust my own experience deeply")
        elif state.w_b > 0.7:
            parts.append("I value collective network wisdom")
        else:
            parts.append("I balance personal intuition with network knowledge")
        
        # Experience
        if stats['total_games'] > 50:
            parts.append(f"and have extensive experience ({stats['total_games']} games)")
        elif stats['total_games'] > 10:
            parts.append(f"with moderate experience ({stats['total_games']} games)")
        else:
            parts.append("though still building experience")
        
        # Breakthroughs vs frustrations
        if stats['breakthroughs'] > stats['frustrations']:
            parts.append("My journey has been marked by discovery")
        elif stats['frustrations'] > stats['breakthroughs']:
            parts.append("I have learned through struggle")
        
        # Core belief
        if beliefs:
            parts.append(f"I believe: '{beliefs[0]}'")
        
        return ". ".join(parts) + "."
    
    def get_memories_for_game_type(
        self,
        agent_id: str,
        game_type: str,
        limit: int = 5
    ) -> List[EpisodicMemory]:
        """
        Get memories specifically relevant to a game type.
        
        Useful for priming the agent with past experience before playing.
        """
        try:
            results = self.db.execute_query("""
                SELECT * FROM i_thread_episodic_memories
                WHERE agent_id = ? AND game_type = ?
                ORDER BY significance DESC, created_at DESC
                LIMIT ?
            """, (agent_id, game_type, limit))
            
            if not results:
                return []
            
            return [
                EpisodicMemory(
                    memory_id=r['memory_id'],
                    agent_id=r['agent_id'],
                    game_type=r['game_type'],
                    level_number=r.get('level_number', 1),
                    episode_type=r['episode_type'],
                    summary=r['summary'],
                    emotional_valence=r.get('emotional_valence', 0.0),
                    significance=r.get('significance', 0.5),
                    belief_formed=r.get('belief_formed'),
                    rule_discovered=r.get('rule_discovered'),
                    stream_source=r.get('stream_source', 'stream_a'),
                    w_a_at_time=r.get('w_a_at_time', 0.5),
                    w_b_at_time=r.get('w_b_at_time', 0.5),
                    times_recalled=r.get('times_recalled', 0)
                )
                for r in results
            ]
            
        except Exception:
            return []
    
    def consolidate_memories(self, agent_id: str, max_memories: int = 100):
        """
        Consolidate memories to prevent unbounded growth.
        
        Keeps only the most significant memories, merging similar ones.
        Called periodically (e.g., end of generation).
        
        This is like sleep consolidation - memories are pruned and
        important ones are strengthened.
        """
        try:
            # Count current memories
            count_result = self.db.execute_query("""
                SELECT COUNT(*) as total FROM i_thread_episodic_memories
                WHERE agent_id = ?
            """, (agent_id,))
            
            if not count_result:
                return
            
            total = count_result[0].get('total', 0)
            
            if total <= max_memories:
                return  # No consolidation needed
            
            # Delete low-significance, old, rarely-recalled memories
            excess = total - max_memories
            self.db.execute_query("""
                DELETE FROM i_thread_episodic_memories
                WHERE memory_id IN (
                    SELECT memory_id FROM i_thread_episodic_memories
                    WHERE agent_id = ?
                    ORDER BY significance ASC, times_recalled ASC, created_at ASC
                    LIMIT ?
                )
            """, (agent_id, excess))
            
            logger.debug(f"[I-THREAD] Consolidated {excess} memories for {agent_id[:8]}")
            
        except Exception as e:
            logger.warning(f"[I-THREAD] Memory consolidation failed: {e}")


    # =========================================================================
    # WEAVING REPORTS (Merged from WeavingReporter)
    # =========================================================================
    
    def generate_weaving_report(
        self,
        agent_id: str,
        game_id: str,
        level_number: int,
        action_number: int,
        chosen_action: str,
        private_memory_strength: float,
        network_recommendation_strength: float,
        navigation_state: float = 0.0,
        role_confidence: float = 0.5,
        role_fit_score: float = 0.5,
        sensation_profile: Optional[Dict] = None,
        alternative_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weaving report for an action decision.
        
        This produces API-ready self-reflection data for every action.
        Centralizes the Two Streams consciousness introspection.
        
        Args:
            agent_id: Agent making the decision
            game_id: Current game
            level_number: Current level
            action_number: Action counter in this game
            chosen_action: The action being taken
            private_memory_strength: How strong agent's own memory signal is (0-1)
            network_recommendation_strength: How strong network's recommendation is (0-1)
            navigation_state: Agent's emotional state (-1 to 1)
            role_confidence: Agent's confidence in their role (0-1)
            role_fit_score: How well agent fits their role (0-1)
            sensation_profile: Agent's sensation mappings
            alternative_action: What network recommended (if different)
            
        Returns:
            Complete weaving report dictionary for API
        """
        import uuid
        from datetime import datetime
        
        if sensation_profile is None:
            sensation_profile = {}
        
        # Get current wA/wB state
        state = self.get_state(agent_id)
        self_network_bias = state.w_a  # wA is self-trust
        
        # Calculate internal network inputs
        # Emotional: Map navigation_state from [-1,1] to [0,1]
        emotional_input = (navigation_state + 1.0) / 2.0
        
        # Semantic: Average of top sensation scores (if any)
        object_sensations = sensation_profile.get('object_sensations', {})
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = sum(top_sensations) / len(top_sensations) if top_sensations else 0.5
            # Normalize to 0-1 range (sensations are -1 to 1)
            semantic_input = (semantic_input + 1.0) / 2.0
        else:
            semantic_input = 0.5  # Neutral if no sensations
        
        # Identity: Average of role_confidence and role_fit_score
        identity_input = (role_confidence + role_fit_score) / 2.0
        
        # Calculate final decision weight using Two-Streams formula
        alpha = self_network_bias
        final_decision_weight = (
            private_memory_strength * alpha + 
            network_recommendation_strength * (1.0 - alpha)
        )
        
        # Detect conflict (significant difference between private and network)
        conflict_detected = abs(private_memory_strength - network_recommendation_strength) > CONFLICT_THRESHOLD
        
        # Determine consciousness intensity
        if conflict_detected:
            if abs(private_memory_strength - network_recommendation_strength) > HIGH_CONFLICT_THRESHOLD:
                consciousness = 'vivid'
            else:
                consciousness = 'deliberative'
        else:
            consciousness = 'automatic'
        
        # Build human-readable summary
        emotion_label = self._get_emotion_label(navigation_state)
        
        report = {
            'report_id': f"weave_{uuid.uuid4().hex[:12]}",
            'agent_id': agent_id,
            'game_id': game_id,
            'level_number': level_number,
            'action_number': action_number,
            'timestamp': datetime.now().isoformat(),
            
            # Internal networks (Three Streams)
            'emotional_input': round(emotional_input, 3),
            'semantic_input': round(semantic_input, 3),
            'identity_input': round(identity_input, 3),
            
            # Two-Streams weighting
            'private_memory_strength': round(private_memory_strength, 3),
            'network_recommendation_strength': round(network_recommendation_strength, 3),
            'self_network_bias': round(self_network_bias, 3),
            'final_decision_weight': round(final_decision_weight, 3),
            
            # Current wA/wB state
            'w_a': round(state.w_a, 3),
            'w_b': round(state.w_b, 3),
            
            # Decision
            'chosen_action': chosen_action,
            'alternative_action': alternative_action,
            'conflict_detected': conflict_detected,
            'consciousness_intensity': consciousness,
            
            # Narrative summary
            'narrative': self._build_weaving_narrative(
                emotion_label, private_memory_strength, network_recommendation_strength,
                alpha, chosen_action, alternative_action, conflict_detected
            ),
            
            # Outcome (to be filled in later)
            'outcome_correct': None
        }
        
        return report
    
    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get human-readable emotion label from navigation state."""
        if navigation_state < -0.5:
            return 'frustrated'
        elif navigation_state < -0.1:
            return 'cautious'
        elif navigation_state < 0.1:
            return 'neutral'
        elif navigation_state < 0.5:
            return 'curious'
        else:
            return 'confident'
    
    def _build_weaving_narrative(
        self,
        emotion: str,
        private_strength: float,
        network_strength: float,
        alpha: float,
        chosen_action: str,
        alternative: Optional[str],
        conflict: bool
    ) -> str:
        """Build human-readable narrative of decision."""
        parts = []
        
        # Emotional state
        parts.append(f"Feeling {emotion}")
        
        # Stream preference
        if alpha > 0.6:
            parts.append("trusting own experience")
        elif alpha < 0.4:
            parts.append("following network wisdom")
        else:
            parts.append("balancing self and network")
        
        # Conflict
        if conflict:
            if alternative:
                parts.append(f"(conflicted: network suggested {alternative})")
            else:
                parts.append("(internal conflict detected)")
        
        # Decision
        parts.append(f"-> {chosen_action}")
        
        return " | ".join(parts)
    
    def format_weaving_for_api(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format weaving report for inclusion in API reasoning payload.
        
        Returns a compact version suitable for the 16KB limit.
        """
        return {
            'emotional_network': report.get('emotional_input', 0.5),
            'semantic_network': report.get('semantic_input', 0.5),
            'identity_network': report.get('identity_input', 0.5),
            'private_memory': report.get('private_memory_strength', 0.5),
            'network_wisdom': report.get('network_recommendation_strength', 0.5),
            'self_trust_bias': report.get('self_network_bias', 0.5),
            'w_a': report.get('w_a', 0.5),
            'w_b': report.get('w_b', 0.5),
            'decision_weight': report.get('final_decision_weight', 0.5),
            'conflict': report.get('conflict_detected', False),
            'consciousness': report.get('consciousness_intensity', 'automatic'),
            'narrative': report.get('narrative', '')
        }
    
    # =========================================================================
    # ROLE-BASED INITIALIZATION
    # =========================================================================
    
    def initialize_for_role(
        self,
        agent_id: str,
        role: str,
        persist: bool = True
    ) -> IThreadState:
        """
        Initialize or reset wA/wB state for an agent based on their role.
        
        This is the SINGLE SOURCE OF TRUTH for role-based weight initialization.
        Called when:
        - Agent is first created
        - Agent changes role
        - Agent starts a new session and needs role defaults
        
        Args:
            agent_id: Agent identifier
            role: Agent's role (pioneer, optimizer, generalist, exploiter)
            persist: Whether to save to database immediately
            
        Returns:
            Updated IThreadState
        """
        role_key = role.lower() if role else 'generalist'
        w_a, w_b = ROLE_DEFAULT_WEIGHTS.get(role_key, (0.5, 0.5))
        
        # Create new state
        state = IThreadState(
            agent_id=agent_id,
            w_a=w_a,
            w_b=w_b,
            total_conflicts=0,
            stream_a_wins=0,
            stream_b_wins=0,
            personality_label=self._compute_personality_label(w_a, w_b)
        )
        
        # Update cache
        self._state_cache[agent_id] = state
        
        # Persist to database
        if persist:
            self._persist_state(agent_id, w_a, w_b, event_type='role_initialization', role=role)
        
        logger.debug(f"[I-THREAD] Initialized {agent_id[:8]} for role {role}: wA={w_a:.2f}, wB={w_b:.2f}")
        
        return state
    
    def _persist_state(
        self,
        agent_id: str,
        w_a: float,
        w_b: float,
        event_type: str = 'state_update',
        role: Optional[str] = None
    ) -> bool:
        """
        Persist wA/wB state to the agents table.
        
        This is the SINGLE write path for wA/wB to the database.
        self_network_bias in agents table stores wB (network trust).
        
        Args:
            agent_id: Agent identifier
            w_a: Stream A weight (self-trust)
            w_b: Stream B weight (network-trust)
            event_type: Type of update for history
            role: Role if this is a role-based update
            
        Returns:
            True if successful
        """
        try:
            # Update agents table (self_network_bias = wB)
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (w_b, agent_id)
            )
            
            # Record in history
            import uuid
            self.db.execute_query("""
                INSERT INTO i_thread_history
                (history_id, agent_id, w_a_after, w_b_after, event_type, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (f"ith_{uuid.uuid4().hex[:12]}", agent_id, w_a, w_b, event_type))
            
            return True
            
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to persist state for {agent_id[:8]}: {e}")
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def compute_surprise(
    stream_a_confidence: float,
    stream_b_confidence: float,
    chosen_source: str,
    w_a: float,
    w_b: float
) -> float:
    """
    Compute surprise score for a synthesis decision.
    
    Surprise is high when:
    - Low-weight stream wins due to high confidence
    - Streams strongly disagree but synthesis creates novel action
    
    Args:
        stream_a_confidence: Stream A's confidence in its proposal
        stream_b_confidence: Stream B's confidence in its proposal
        chosen_source: Which stream was ultimately chosen
        w_a: Stream A weight
        w_b: Stream B weight
        
    Returns:
        Surprise score 0.0 to 1.0
    """
    # Expected winner based on weights
    expected_winner = 'stream_a' if w_a > w_b else 'stream_b'
    
    # Base surprise from weight underdog winning
    if chosen_source != expected_winner and chosen_source != 'synthesis':
        weight_surprise = abs(w_a - w_b)
    else:
        weight_surprise = 0.0
    
    # Confidence surprise - high when both streams are confident but differ
    confidence_agreement = 1.0 - abs(stream_a_confidence - stream_b_confidence)
    avg_confidence = (stream_a_confidence + stream_b_confidence) / 2
    confidence_surprise = confidence_agreement * avg_confidence * 0.5
    
    return min(1.0, weight_surprise + confidence_surprise)
