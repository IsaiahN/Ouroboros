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
