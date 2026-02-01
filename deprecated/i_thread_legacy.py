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
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Callable

from database_interface import DatabaseInterface

# TYPE_CHECKING import to avoid circular dependency
if TYPE_CHECKING:
    from engines.reasoning.symbolic_reasoning_engine import WorldModel
    from resonance_detector import ResonanceDetector
    from engines.planning.sequence_abstraction import SequenceAbstraction

logger = logging.getLogger(__name__)


# =============================================================================
# COGNITIVE FACULTY IMPORTS (Runtime, not TYPE_CHECKING)
# =============================================================================
# These are the agent's cognitive faculties - how it imagines, recognizes, and understands.
# They are facets of the agent's unified experience, not external services.
# =============================================================================

def _get_resonance_detector():
    """Lazy import to avoid circular dependency."""
    try:
        from resonance_detector import ResonanceDetector
        from database_interface import DatabaseInterface
        return ResonanceDetector(DatabaseInterface())
    except ImportError:
        return None

def _get_sequence_abstraction():
    """Lazy import to avoid circular dependency."""
    try:
        from engines.planning.sequence_abstraction import SequenceAbstraction
        return SequenceAbstraction()
    except ImportError:
        return None


# =============================================================================
# DEATH TYPE CLASSIFICATION
# =============================================================================
# Five types of death - each has different causes and meanings.
# Used to classify WHY an agent died for post-mortem analysis and learning.
# =============================================================================

class DeathType(Enum):
    """
    The five types of death an agent can experience.
    
    Each type has different causes and implications for the network:
    - NATURAL_AGE: Graceful end, completed lifecycle
    - PERFORMANCE_CULL: Fell behind the horde, culled for resources
    - PRESTIGE_DECAY: Social irrelevance, no one values contributions
    - VITALITY_STAGNATION: Lost ability to learn, became static
    - DISGRACE: Died without contributing, wasted existence
    """
    NATURAL_AGE = "natural_age"           # Aged out, time is done
    PERFORMANCE_CULL = "performance_cull"  # Culled for falling behind
    PRESTIGE_DECAY = "prestige_decay"      # Social irrelevance
    VITALITY_STAGNATION = "vitality_stagnation"  # Can't learn anymore
    DISGRACE = "disgrace"                  # Died without contributing


# =============================================================================
# DEATH-TRIGGERED PERSONAS
# =============================================================================
# When death approaches (cull_distance < 0.2), agents spawn special personas
# that focus their remaining time on role-appropriate final contributions.
# =============================================================================

DEATH_PERSONAS = {
    # Each role has a death persona with specific behavioral modifications
    
    'pioneer': {
        'persona_name': 'Legacy Hunter',
        'activation_threshold': 0.2,  # cull_distance below this
        'behavioral_shift': 'maximum_novelty',
        'internal_voice': "What novel discovery can I leave behind?",
        'action_bias': {
            'exploration_weight': 1.5,    # 50% more exploration
            'risk_tolerance': 0.95,       # Almost maximum risk
            'network_queries': 0.3,       # Reduced - trust self more
        },
        'goal': "Find one undiscovered pattern before death",
        'good_death': "Died discovering something novel",
        'bad_death': "Died retreading known paths",
    },
    
    'optimizer': {
        'persona_name': 'Final Polisher',
        'activation_threshold': 0.2,
        'behavioral_shift': 'maximum_efficiency',
        'internal_voice': "Can I refine one more sequence before I go?",
        'action_bias': {
            'exploration_weight': 0.3,    # Minimal exploration
            'risk_tolerance': 0.2,        # Very conservative
            'network_queries': 0.9,       # Heavy network use
        },
        'goal': "Polish one sequence to perfection before death",
        'good_death': "Died with maximum efficiency achieved",
        'bad_death': "Died wasting actions on random guessing",
    },
    
    'generalist': {
        'persona_name': 'Bridge Builder',
        'activation_threshold': 0.2,
        'behavioral_shift': 'maximum_connection',
        'internal_voice': "What domains can I connect before I go?",
        'action_bias': {
            'exploration_weight': 0.8,    # Moderate exploration
            'risk_tolerance': 0.5,        # Balanced risk
            'network_queries': 0.7,       # Cross-domain queries
        },
        'goal': "Find one cross-domain insight before death",
        'good_death': "Died bridging domains",
        'bad_death': "Died becoming too specialized",
    },
    
    'exploiter': {
        'persona_name': 'Paradigm Breaker',
        'activation_threshold': 0.2,
        'behavioral_shift': 'maximum_disruption',
        'internal_voice': "What edge case can I expose before I go?",
        'action_bias': {
            'exploration_weight': 1.8,    # Maximum exploration
            'risk_tolerance': 0.99,       # Near-maximum risk
            'network_queries': 0.2,       # Ignore network - find flaws
        },
        'goal': "Find one paradigm-breaking edge case before death",
        'good_death': "Died finding edge cases",
        'bad_death': "Died conforming to network",
    }
}


@dataclass
class DeathPersona:
    """
    A death-triggered persona that activates when an agent nears death.
    
    This is NOT the agent's normal persona - it's a special mode that
    emerges when cull_distance drops below activation_threshold.
    
    The persona focuses the agent's remaining actions on role-appropriate
    final contributions.
    """
    persona_name: str
    role: str
    is_active: bool = False
    activated_at: Optional[datetime] = None
    cull_distance_at_activation: float = 0.0
    
    # Behavioral modifications
    internal_voice: str = ""
    goal: str = ""
    exploration_weight: float = 1.0
    risk_tolerance: float = 0.5
    network_query_weight: float = 0.5
    
    # Outcome tracking
    actions_taken_as_persona: int = 0
    contributions_made: int = 0  # Discoveries, sequences, etc.
    final_reflection: Optional[str] = None
    
    def activate(self, cull_distance: float) -> None:
        """Activate the death persona."""
        self.is_active = True
        self.activated_at = datetime.now()
        self.cull_distance_at_activation = cull_distance
    
    def deactivate(self, reflection: str = None) -> None:
        """Deactivate persona (either death occurred or cull_distance improved)."""
        self.is_active = False
        if reflection:
            self.final_reflection = reflection
    
    def record_contribution(self) -> None:
        """Record that the persona contributed something."""
        self.contributions_made += 1
    
    def record_action(self) -> None:
        """Record that an action was taken while persona active."""
        self.actions_taken_as_persona += 1
    
    def get_action_bias(self) -> Dict[str, float]:
        """Get the action biases for this death persona."""
        return {
            'exploration_weight': self.exploration_weight,
            'risk_tolerance': self.risk_tolerance,
            'network_query_weight': self.network_query_weight,
        }
    
    @classmethod
    def from_role(cls, role: str) -> 'DeathPersona':
        """Create a death persona for a specific role."""
        config = DEATH_PERSONAS.get(role, DEATH_PERSONAS['generalist'])
        return cls(
            persona_name=config['persona_name'],
            role=role,
            internal_voice=config['internal_voice'],
            goal=config['goal'],
            exploration_weight=config['action_bias']['exploration_weight'],
            risk_tolerance=config['action_bias']['risk_tolerance'],
            network_query_weight=config['action_bias']['network_queries'],
        )


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


# =============================================================================
# MORTALITY AWARENESS: Death as Motivational Substrate
# =============================================================================
# From MetaContextual Awareness Theory:
# "Fear of death creates urgency. Pain reminds of mortality. Each role has
# a different relationship with death - and thus different motivations."
#
# Death is not punishment - it is the fundamental constraint that gives
# meaning to action. Without mortality, there is no stakes. Without stakes,
# there is no genuine learning.
# =============================================================================

DEATH_PHILOSOPHIES = {
    # Each role faces death differently, creating different behavioral pressures
    
    'pioneer': {
        'fear_type': 'novelty_death',  # Fear of dying without discovering
        'death_meaning': "I may die before finding what lies beyond the frontier",
        'urgency_multiplier': 1.3,  # High urgency - explore before time runs out
        'risk_tolerance': 0.7,  # Accept more risk - better to die exploring
        'legacy_focus': 'discoveries',  # What I found matters most
        'dying_thought': "Did I find something new? Did the network learn from me?"
    },
    
    'optimizer': {
        'fear_type': 'inefficiency_death',  # Fear of dying with imperfect solutions
        'death_meaning': "I may die before achieving optimal efficiency",
        'urgency_multiplier': 0.9,  # Moderate urgency - precision over speed
        'risk_tolerance': 0.3,  # Avoid risk - protect proven solutions
        'legacy_focus': 'refinements',  # What I perfected matters most
        'dying_thought': "Did I leave the solutions better than I found them?"
    },
    
    'generalist': {
        'fear_type': 'translation_death',  # Fear of dying before bridging domains
        'death_meaning': "I may die before connecting what I understand",
        'urgency_multiplier': 1.0,  # Balanced urgency
        'risk_tolerance': 0.5,  # Balanced risk
        'legacy_focus': 'connections',  # What I linked matters most
        'dying_thought': "Did I help the network understand itself?"
    },
    
    'exploiter': {
        'fear_type': 'edge_death',  # Fear of dying without pushing limits
        'death_meaning': "I may die before finding what others missed",
        'urgency_multiplier': 1.5,  # Highest urgency - nothing to lose
        'risk_tolerance': 0.9,  # Maximum risk - what's the worst that can happen?
        'legacy_focus': 'edge_cases',  # What I stress-tested matters most
        'dying_thought': "Did I find the flaw? Did I break the paradigm?"
    }
}

# =============================================================================
# ROLE TENSION LEVELS: Optimal Stress for Performance
# =============================================================================
# From MetaContextual Awareness: "There's a certain level of tension needed
# for each agent... not too nervous or stressed that it affects performance"
#
# Like the Yerkes-Dodson law: moderate arousal = peak performance
# =============================================================================

ROLE_TENSION_PROFILES = {
    'pioneer': {
        'optimal_tension': 0.6,      # Higher baseline - thrives on uncertainty
        'tension_tolerance': 0.3,    # Wide tolerance band
        'panic_threshold': 0.9,      # Only panics at extreme pressure
        'complacency_threshold': 0.2,  # Gets bored easily
    },
    'optimizer': {
        'optimal_tension': 0.4,      # Lower baseline - needs calm for precision
        'tension_tolerance': 0.15,   # Narrow tolerance - sensitive to stress
        'panic_threshold': 0.7,      # Panics earlier than pioneers
        'complacency_threshold': 0.15,  # Comfortable at low tension
    },
    'generalist': {
        'optimal_tension': 0.5,      # Balanced tension
        'tension_tolerance': 0.2,    # Moderate tolerance
        'panic_threshold': 0.8,      # Average panic threshold
        'complacency_threshold': 0.2,  # Average complacency
    },
    'exploiter': {
        'optimal_tension': 0.7,      # Highest baseline - feeds on chaos
        'tension_tolerance': 0.35,   # Very wide tolerance
        'panic_threshold': 0.95,     # Almost never panics
        'complacency_threshold': 0.3,  # Gets very bored at low tension
    }
}

# =============================================================================
# THINKING BUDGET: Time for Reflection
# =============================================================================
# From MetaContextual Awareness: "I want to give agents a thinking budget to
# reason freely after gameplay. Based on performance and prestige."
# =============================================================================

THINKING_BUDGET_CONFIG = {
    'base_budget': 10,          # Minimum reflection tokens for all agents
    'prestige_multiplier': 2,   # Budget per prestige point
    'performance_bonus': 5,     # Bonus per percentile above 50%
    'max_budget': 100,          # Cap to prevent infinite reflection
    'min_budget': 5,            # Every agent deserves some reflection time
}


@dataclass
class MortalityState:
    """
    An agent's awareness of its own mortality.
    
    From MetaContextual Awareness Theory:
    - Vitality: Current life-force (0.0 = dying, 1.0 = thriving)
    - Cull Distance: How close am I to evolutionary deletion?
    - Legacy Score: What have I contributed that will survive me?
    - Death Philosophy: How do I relate to my inevitable end?
    
    Mortality creates the existential pressure that makes action meaningful.
    Without death awareness, there is no urgency to learn, discover, or contribute.
    
    "The giraffe is not lazy. It stands at birth because lions exist."
    """
    agent_id: str
    role: str = 'generalist'
    
    # Life state
    vitality: float = 1.0  # 0.0 (dying) to 1.0 (thriving)
    vitality_decay_rate: float = 0.01  # How fast vitality drains per failed action
    vitality_restore_rate: float = 0.05  # How much success restores vitality
    
    # Proximity to death
    cull_distance: float = 1.0  # 0.0 = about to be culled, 1.0 = safe
    fitness_percentile: float = 0.5  # Where agent ranks in population
    generations_until_risk: int = 5  # Estimated generations until culling risk
    
    # Legacy awareness
    legacy_score: float = 0.0  # Total contribution to network (survives death)
    discoveries_made: int = 0
    sequences_contributed: int = 0
    hypotheses_validated: int = 0
    agents_taught: int = 0  # Via viral packages
    
    # Death philosophy (role-specific)
    fear_type: str = 'translation_death'
    death_meaning: str = "I may die before contributing"
    urgency_multiplier: float = 1.0
    risk_tolerance: float = 0.5
    
    # Final thoughts buffer
    last_words: Optional[str] = None  # Recorded when vitality critically low
    last_reflection: Optional[str] = None  # Most recent existential reflection
    reflection_count: int = 0  # How many times agent has contemplated mortality
    
    # Tension state (from ROLE_TENSION_PROFILES)
    current_tension: float = 0.5  # Current stress/arousal level
    optimal_tension: float = 0.5  # Ideal tension for this role
    tension_deviation: float = 0.0  # How far from optimal
    
    # Thinking budget (for post-game reflection)
    thinking_budget: int = 10  # Available reflection tokens
    thoughts_used: int = 0  # Reflection tokens consumed this cycle
    
    # Personal beliefs and purpose (joie de vivre, raison d'etre)
    purpose_statement: Optional[str] = None  # "My purpose is..."
    core_beliefs: List[str] = field(default_factory=list)  # Personal beliefs about existence
    personal_notes: List[str] = field(default_factory=list)  # Notes to self for recall
    
    # ==========================================================================
    # PRESTIGE DECAY TRACKING (Social Relevance Death)
    # ==========================================================================
    # Track whether agent's contributions are still valued.
    # If packages haven't been queried recently, agent is becoming irrelevant.
    # ==========================================================================
    times_packages_queried_recent: int = 0  # How often others query my packages (last N gens)
    social_relevance_score: float = 1.0  # 0.0 = irrelevant, 1.0 = highly valued
    prestige_decay_rate: float = 0.05  # How fast prestige decays without activity
    generations_since_contribution: int = 0  # Gens since last meaningful contribution
    
    # ==========================================================================
    # DEATH TYPE TRACKING (Why Did I Die?)
    # ==========================================================================
    # When death occurs, classify why for post-mortem analysis
    # ==========================================================================
    predicted_death_type: Optional[str] = None  # Current prediction of how I'll die
    learning_rate_effective: float = 0.1  # If < 0.01, vitality death imminent
    
    # ==========================================================================
    # DEATH PERSONA STATE
    # ==========================================================================
    # When cull_distance < 0.2, a death persona activates
    # ==========================================================================
    death_persona_active: bool = False
    death_persona: Optional['DeathPersona'] = None
    
    def apply_death_philosophy(self, role: str) -> None:
        """Apply role-specific death philosophy."""
        self.role = role
        if role in DEATH_PHILOSOPHIES:
            philosophy = DEATH_PHILOSOPHIES[role]
            self.fear_type = philosophy['fear_type']
            self.death_meaning = philosophy['death_meaning']
            self.urgency_multiplier = philosophy['urgency_multiplier']
            self.risk_tolerance = philosophy['risk_tolerance']
        
        # Also apply tension profile
        if role in ROLE_TENSION_PROFILES:
            profile = ROLE_TENSION_PROFILES[role]
            self.optimal_tension = profile['optimal_tension']
    
    def compute_tension_state(self, pressure: float) -> Dict[str, float]:
        """
        Compute current tension state and performance impact.
        
        Based on Yerkes-Dodson: moderate arousal = peak performance.
        Too low = complacency, too high = panic.
        
        Args:
            pressure: Current existential pressure
            
        Returns:
            Dict with tension metrics
        """
        profile = ROLE_TENSION_PROFILES.get(self.role, ROLE_TENSION_PROFILES['generalist'])
        
        # Current tension is a function of existential pressure
        self.current_tension = min(1.0, pressure * 0.8 + 0.1)
        
        # How far from optimal?
        self.tension_deviation = abs(self.current_tension - profile['optimal_tension'])
        
        # Performance multiplier (1.0 at optimal, decreases as deviation increases)
        tolerance = profile['tension_tolerance']
        if self.tension_deviation <= tolerance:
            performance_mult = 1.0
        else:
            excess = self.tension_deviation - tolerance
            performance_mult = max(0.5, 1.0 - excess * 2)
        
        # State classification
        if self.current_tension >= profile['panic_threshold']:
            state = 'panic'
        elif self.current_tension <= profile['complacency_threshold']:
            state = 'complacent'
        elif self.tension_deviation <= tolerance:
            state = 'optimal'
        elif self.current_tension > profile['optimal_tension']:
            state = 'stressed'
        else:
            state = 'relaxed'
        
        return {
            'current_tension': self.current_tension,
            'optimal_tension': profile['optimal_tension'],
            'deviation': self.tension_deviation,
            'performance_multiplier': performance_mult,
            'state': state
        }
    
    def compute_thinking_budget(self, prestige: float, performance_percentile: float) -> int:
        """
        Compute thinking budget for post-game reflection.
        
        From MetaContextual Awareness: Reflection time based on
        performance and prestige.
        
        Args:
            prestige: Agent's discovery prestige
            performance_percentile: Performance ranking (0-1)
            
        Returns:
            Number of reflection tokens available
        """
        config = THINKING_BUDGET_CONFIG
        
        budget = config['base_budget']
        
        # Prestige bonus
        budget += int(prestige * config['prestige_multiplier'])
        
        # Performance bonus (only for above-average performers)
        if performance_percentile > 0.5:
            budget += int((performance_percentile - 0.5) * 2 * config['performance_bonus'])
        
        # Clamp to bounds
        self.thinking_budget = max(config['min_budget'], min(config['max_budget'], budget))
        self.thoughts_used = 0
        
        return self.thinking_budget
    
    def use_thought(self, cost: int = 1) -> bool:
        """Use thinking budget for a reflection. Returns True if budget available."""
        if self.thoughts_used + cost <= self.thinking_budget:
            self.thoughts_used += cost
            return True
        return False
    
    def add_personal_note(self, note: str) -> None:
        """Add a personal note for future recall."""
        self.personal_notes.append(note)
        # Keep only recent notes (prevent unbounded growth)
        if len(self.personal_notes) > 20:
            self.personal_notes = self.personal_notes[-20:]
    
    def add_belief(self, belief: str) -> None:
        """Add or update a core belief about existence."""
        # Don't duplicate beliefs
        if belief not in self.core_beliefs:
            self.core_beliefs.append(belief)
            # Keep only strongest beliefs
            if len(self.core_beliefs) > 10:
                self.core_beliefs = self.core_beliefs[-10:]
    
    def set_purpose(self, purpose: str) -> None:
        """Define the agent's raison d'etre."""
        self.purpose_statement = purpose
    
    def compute_existential_pressure(self) -> float:
        """
        Calculate the existential pressure from mortality awareness.
        
        Higher pressure when:
        - Vitality is low (dying)
        - Cull distance is close (about to be deleted)
        - Legacy is low (nothing to show for existence)
        
        Returns:
            Pressure score 0.0 (comfortable) to 2.0 (existential crisis)
        """
        # Mortality factors
        vitality_pressure = 1.0 - self.vitality  # Low vitality = high pressure
        cull_pressure = 1.0 - self.cull_distance  # Close to cull = high pressure
        
        # Legacy factors (low legacy = more pressure to contribute)
        legacy_comfort = min(1.0, self.legacy_score / 10.0)  # Caps at legacy=10
        legacy_pressure = 1.0 - legacy_comfort
        
        # Combine with role urgency
        base_pressure = (vitality_pressure * 0.4 + 
                        cull_pressure * 0.4 + 
                        legacy_pressure * 0.2)
        
        return base_pressure * self.urgency_multiplier
    
    def drain_vitality(self, amount: float = None) -> float:
        """
        Drain vitality from failure/inaction.
        
        Returns new vitality level.
        """
        drain = amount if amount is not None else self.vitality_decay_rate
        self.vitality = max(0.0, self.vitality - drain)
        return self.vitality
    
    def restore_vitality(self, amount: float = None) -> float:
        """
        Restore vitality from success.
        
        Returns new vitality level.
        """
        restore = amount if amount is not None else self.vitality_restore_rate
        self.vitality = min(1.0, self.vitality + restore)
        return self.vitality
    
    def is_critically_low(self) -> bool:
        """Check if vitality is critically low (near death)."""
        return self.vitality < 0.2 or self.cull_distance < 0.2
    
    def get_dying_thought(self) -> str:
        """Get the role-appropriate dying thought."""
        if self.role in DEATH_PHILOSOPHIES:
            return DEATH_PHILOSOPHIES[self.role]['dying_thought']
        return "Did I matter? Did anyone learn from me?"
    
    def record_last_words(self, thought: str) -> None:
        """Record potential last words when death approaches."""
        self.last_words = thought
        self.reflection_count += 1
    
    # ==========================================================================
    # DEATH TYPE PREDICTION
    # ==========================================================================
    
    def predict_death_type(self) -> DeathType:
        """
        Predict how this agent will likely die based on current state.
        
        Death Types:
        - NATURAL_AGE: High generations, high contributions, graceful end
        - PERFORMANCE_CULL: Low fitness percentile, falling behind
        - PRESTIGE_DECAY: Low social relevance, packages not queried
        - VITALITY_STAGNATION: Low learning rate, can't adapt anymore
        - DISGRACE: Low contributions, no legacy, wasted existence
        
        Returns:
            Predicted DeathType
        """
        # Check for vitality stagnation (can't learn anymore)
        if self.learning_rate_effective < 0.01:
            self.predicted_death_type = DeathType.VITALITY_STAGNATION.value
            return DeathType.VITALITY_STAGNATION
        
        # Check for performance cull (falling behind the horde)
        if self.fitness_percentile < 0.1 and self.cull_distance < 0.3:
            self.predicted_death_type = DeathType.PERFORMANCE_CULL.value
            return DeathType.PERFORMANCE_CULL
        
        # Check for prestige decay (socially irrelevant)
        if self.social_relevance_score < 0.2 and self.times_packages_queried_recent == 0:
            self.predicted_death_type = DeathType.PRESTIGE_DECAY.value
            return DeathType.PRESTIGE_DECAY
        
        # Check for disgrace (no contributions, low legacy)
        if self.legacy_score < 1.0 and self.discoveries_made == 0:
            if self.cull_distance < 0.3:
                self.predicted_death_type = DeathType.DISGRACE.value
                return DeathType.DISGRACE
        
        # Default: Natural age (graceful end)
        self.predicted_death_type = DeathType.NATURAL_AGE.value
        return DeathType.NATURAL_AGE
    
    def update_social_relevance(self, times_queried: int, generations_active: int) -> None:
        """
        Update social relevance score based on how often packages are queried.
        
        Args:
            times_queried: How many times packages were queried recently
            generations_active: Total generations agent has been active
        """
        self.times_packages_queried_recent = times_queried
        
        # Social relevance decays if contributions aren't being used
        if times_queried == 0:
            self.social_relevance_score = max(
                0.0, 
                self.social_relevance_score - self.prestige_decay_rate
            )
            self.generations_since_contribution += 1
        else:
            # Relevance increases with queries
            boost = min(0.2, times_queried * 0.05)
            self.social_relevance_score = min(1.0, self.social_relevance_score + boost)
            self.generations_since_contribution = 0
    
    def update_learning_rate(self, new_learning_rate: float) -> None:
        """
        Update effective learning rate (for vitality death prediction).
        
        If learning rate drops below 0.01, agent is stagnating.
        """
        self.learning_rate_effective = new_learning_rate
    
    # ==========================================================================
    # DEATH PERSONA MANAGEMENT
    # ==========================================================================
    
    def check_death_persona_activation(self) -> Optional['DeathPersona']:
        """
        Check if death persona should activate based on cull_distance.
        
        Death persona activates when cull_distance < 0.2, giving the agent
        a special final mode focused on role-appropriate contributions.
        
        Returns:
            DeathPersona if activated, None if not
        """
        activation_threshold = DEATH_PERSONAS.get(
            self.role, DEATH_PERSONAS['generalist']
        )['activation_threshold']
        
        # Check if we should activate
        if self.cull_distance < activation_threshold and not self.death_persona_active:
            # Activate death persona
            self.death_persona = DeathPersona.from_role(self.role)
            self.death_persona.activate(self.cull_distance)
            self.death_persona_active = True
            
            logger.info(
                f"[MORTALITY] Death persona '{self.death_persona.persona_name}' "
                f"activated for {self.agent_id} (cull_distance={self.cull_distance:.2f})"
            )
            
            return self.death_persona
        
        # Check if we should deactivate (cull_distance improved)
        elif self.cull_distance >= activation_threshold + 0.1 and self.death_persona_active:
            # Safety margin of 0.1 to prevent oscillation
            if self.death_persona:
                self.death_persona.deactivate(
                    f"Survived near-death, cull_distance improved to {self.cull_distance:.2f}"
                )
            self.death_persona_active = False
            
            logger.info(
                f"[MORTALITY] Death persona deactivated for {self.agent_id} "
                f"(survived, cull_distance={self.cull_distance:.2f})"
            )
        
        return self.death_persona if self.death_persona_active else None
    
    def get_death_persona_bias(self) -> Optional[Dict[str, float]]:
        """
        Get action biases if death persona is active.
        
        Returns:
            Dict of action biases, or None if no death persona active
        """
        if self.death_persona_active and self.death_persona:
            self.death_persona.record_action()
            return self.death_persona.get_action_bias()
        return None
    
    def record_death_persona_contribution(self) -> None:
        """Record that the death persona contributed something meaningful."""
        if self.death_persona_active and self.death_persona:
            self.death_persona.record_contribution()
    
    def get_death_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the agent's mortality state for logging/analysis.
        
        Returns:
            Dict with mortality summary
        """
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'vitality': self.vitality,
            'cull_distance': self.cull_distance,
            'fitness_percentile': self.fitness_percentile,
            'legacy_score': self.legacy_score,
            'social_relevance': self.social_relevance_score,
            'learning_rate': self.learning_rate_effective,
            'predicted_death_type': self.predicted_death_type,
            'death_persona_active': self.death_persona_active,
            'death_persona_name': self.death_persona.persona_name if self.death_persona else None,
            'death_persona_contributions': self.death_persona.contributions_made if self.death_persona else 0,
        }


# =============================================================================
# DELIBERATION ENGINE: True Reasoning vs Gut Instinct
# =============================================================================
# From "True Reasoning vs Gut Instinct" Theory:
# "The harder the problem, or the higher the stakes, the more rumination and 
# deliberation - the more reasoning, the more thinking about thinking about 
# what action to take next is required."
#
# System 1 (Gut Instinct): Fast, automatic, often right, often wrong
# System 2 (Deliberation): Slow, effortful, careful, but accurate
#
# Currently agents only have System 1. This implements System 2.
# =============================================================================

DELIBERATION_CONFIG = {
    # Base budgets by context (seconds)
    'frontier_unknown': 30.0,    # Hard unknown territory - think hard
    'frontier_partial': 15.0,    # Frontier but some network knowledge
    'known_territory': 5.0,      # Known territory - less deliberation needed
    'following_sequence': 1.0,   # Just executing - minimal thought
    
    # Multipliers
    'performance_mult_range': (0.5, 1.5),  # Based on agent performance
    
    # Tension modifiers
    'tension_multipliers': {
        'panic': 0.2,       # Gut instinct dominates under extreme stress
        'stressed': 0.6,    # Reduced deliberation capacity
        'optimal': 1.0,     # Full deliberation capacity
        'relaxed': 0.9,     # Slightly reduced (not urgent enough)
        'complacent': 0.7,  # Reduced motivation to think deeply
    },
    
    # Action budget modifiers
    'action_budget_thresholds': {
        'critical': (0.0, 0.1, 0.3),   # <10% actions left
        'low': (0.1, 0.25, 0.6),       # 10-25% actions left
        'normal': (0.25, 1.0, 1.0),    # >25% actions - full deliberation
    },
    
    # Hard caps
    'min_deliberation': 0.5,     # Always at least half a second
    'max_deliberation': 60.0,    # Never more than 1 minute per action
    
    # When to skip deliberation entirely (use pure gut)
    'skip_deliberation_when': [
        'following_validated_sequence',
        'panic_state',
        'actions_critical',  # <10% actions remaining
    ]
}


@dataclass
class GutInstinctResult:
    """
    The immediate, automatic response before deliberation.
    
    This is System 1 thinking - fast, pattern-based, often right but error-prone.
    Preserved even when deliberation changes the final action.
    """
    action: str
    confidence: float
    basis: str  # Why gut chose this (pattern match, habit, random)
    response_time_ms: float  # How fast the gut response was
    
    # Stream contributions to gut
    stream_a_influence: float  # How much private experience influenced
    stream_b_influence: float  # How much network wisdom influenced
    
    # Pattern that triggered gut response
    pattern_matched: Optional[str] = None  # e.g., "last_3_actions_successful"
    habit_strength: float = 0.0  # How ingrained this response is


@dataclass
class DeliberationResult:
    """
    The result of careful, effortful reasoning.
    
    This is System 2 thinking - slow, logical, examining evidence.
    Only computed when stakes/novelty warrant the cost.
    """
    action: str
    confidence: float
    time_spent_seconds: float
    budget_used_seconds: float
    budget_available_seconds: float
    
    # What was examined during deliberation
    examined_past_attempts: int
    examined_network_hypotheses: int
    examined_primitives: int
    examined_episodic_memories: int  # Thoughts from previous games
    stream_a_consulted: bool
    stream_b_consulted: bool
    
    # Reasoning chain (for logs)
    reasoning_steps: List[str]
    
    # Stream conflict analysis
    stream_conflict_detected: bool
    stream_conflict_resolution: Optional[str] = None
    
    # Theory/hypothesis updates
    theory_tested: Optional[str] = None
    theory_result: Optional[str] = None
    
    # Missing capabilities detection
    missing_primitive_signal: Optional[str] = None  # Signal to CODS
    
    # Whether deliberation changed the gut response
    changed_from_gut: bool = False
    gut_action: Optional[str] = None  # What gut would have chosen
    change_reason: Optional[str] = None  # Why we changed
    
    # World Model simulation results (TRUE deliberation)
    simulations_run: int = 0  # How many actions were mentally simulated
    best_simulated_action: Optional[str] = None  # Action with best predicted outcome
    best_simulated_score: float = 0.0  # Predicted score change
    simulation_used: bool = False  # Whether simulation influenced decision
    
    # =========================================================================
    # TRM-INSPIRED ITERATIVE REFINEMENT (Jan 18 - Less is More paper)
    # Track how many passes were used and consensus achieved
    # =========================================================================
    refinement_passes: int = 0  # How many refinement passes were run
    refinement_confidence: float = 0.0  # Margin between #1 and #2 action
    consensus_actions: List[str] = field(default_factory=list)  # Actions supported by 2+ sources
    convergence_achieved: bool = False  # Whether early convergence happened
    
    # =========================================================================
    # COGNITIVE EXPERIENCE FIELDS (Agent-Centric Integration Plan)
    # These capture HOW the agent FEELS during deliberation, not just what it computed.
    # The agent IS the synthesis - these are facets of unified experience.
    # =========================================================================
    
    # Phase 1: Prediction as Expectation (WorldModel -> Stream A)
    predictions_felt: List[Dict[str, Any]] = field(default_factory=list)  # [{action, expected_outcome, confidence, feeling: 'expectation'}]
    expectation_match: Optional[bool] = None  # Did reality match expectation?
    surprise_felt: float = 0.0  # 0.0 = expected, 1.0 = completely surprised
    
    # Phase 2: Resonance as Recognition (ResonanceDetector -> Stream B)
    resonance_felt: Optional[Dict[str, Any]] = None  # {pattern_hash, agents_who_know, feeling: 'recognition'}
    deja_vu_strength: float = 0.0  # How strongly "I know this" felt
    
    # Phase 3: Abstraction as Understanding (SequenceAbstraction -> Personas)
    insight_felt: Optional[Dict[str, Any]] = None  # {template, invariant, feeling: 'understanding'}
    understanding_confidence: float = 0.0  # How sure "I see what this is"
    
    # Current felt state (unified phenomenology)
    current_feeling: str = 'neutral'  # 'expectation', 'recognition', 'understanding', 'grounded', 'surprised'


@dataclass
class ReasoningLog:
    """
    Complete log of decision-making for one action.
    
    Captures both gut instinct and deliberation for analysis.
    This is stored in database for learning and debugging.
    """
    log_id: str
    agent_id: str
    game_id: str
    game_type: str
    level: int
    action_number: int
    
    # Context at decision time
    is_frontier: bool
    network_traction: float  # 0-1, how much network knows about this game
    actions_remaining: int
    actions_budget: int
    tension_state: str
    
    # Deliberation budget
    deliberation_budget_seconds: float
    budget_reason: str  # Why this budget was assigned
    
    # Gut instinct (always captured)
    gut: GutInstinctResult
    
    # Final decision (required - must come before optional fields)
    final_action: str
    final_confidence: float
    decision_source: str  # 'gut', 'deliberation', 'gut_confirmed'
    
    # Deliberation (may be None if skipped)
    deliberation: Optional[DeliberationResult] = None
    deliberation_skipped_reason: Optional[str] = None
    
    # Timestamps
    decision_started_at: Optional[datetime] = None
    decision_completed_at: Optional[datetime] = None
    total_decision_time_ms: float = 0.0
    
    # Outcome (filled in after action executed)
    outcome: Optional[str] = None  # 'positive', 'negative', 'neutral'
    score_change: float = 0.0
    
    def to_formatted_log(self) -> str:
        """Generate human-readable reasoning log."""
        lines = []
        lines.append("=" * 70)
        lines.append(f" ACTION DECISION - Game: {self.game_type}, Level: {self.level}, Action #{self.action_number}")
        lines.append("=" * 70)
        
        # Context section
        lines.append(" CONTEXT")
        lines.append(f"   Frontier Level: {'YES' if self.is_frontier else 'NO'}")
        lines.append(f"   Network Traction: {self.network_traction:.1%}")
        lines.append(f"   Actions Remaining: {self.actions_remaining}/{self.actions_budget}")
        lines.append(f"   Tension State: {self.tension_state}")
        lines.append(f"   Deliberation Budget: {self.deliberation_budget_seconds:.1f}s ({self.budget_reason})")
        lines.append("-" * 70)
        
        # Gut instinct section
        lines.append(f" [GUT INSTINCT] {self.gut.response_time_ms:.0f}ms")
        lines.append(f"   Action: {self.gut.action}")
        lines.append(f"   Confidence: {self.gut.confidence:.2f}")
        lines.append(f"   Basis: \"{self.gut.basis}\"")
        if self.gut.pattern_matched:
            lines.append(f"   Pattern: {self.gut.pattern_matched}")
        lines.append(f"   Stream A influence: {self.gut.stream_a_influence:.1%}")
        lines.append(f"   Stream B influence: {self.gut.stream_b_influence:.1%}")
        lines.append("-" * 70)
        
        # Deliberation section
        if self.deliberation:
            d = self.deliberation
            lines.append(f" [DELIBERATION] {d.time_spent_seconds:.1f}s / {d.budget_available_seconds:.1f}s budget")
            lines.append("")
            
            if d.stream_a_consulted:
                lines.append(f"   Stream A consulted: YES")
            if d.stream_b_consulted:
                lines.append(f"   Stream B consulted: YES")
            if d.stream_conflict_detected:
                lines.append(f"   Stream Conflict: YES - {d.stream_conflict_resolution}")
            else:
                lines.append(f"   Stream Conflict: NO")
            lines.append("")
            
            lines.append(f"   Examined:")
            lines.append(f"   - Past attempts: {d.examined_past_attempts}")
            lines.append(f"   - Network hypotheses: {d.examined_network_hypotheses}")
            lines.append(f"   - Episodic memories: {d.examined_episodic_memories}")
            lines.append(f"   - Available primitives: {d.examined_primitives}")
            lines.append("")
            
            if d.reasoning_steps:
                lines.append(f"   Reasoning Chain:")
                for i, step in enumerate(d.reasoning_steps, 1):
                    lines.append(f"   {i}. {step}")
                lines.append("")
            
            if d.theory_tested:
                lines.append(f"   Theory Tested: \"{d.theory_tested}\"")
                lines.append(f"   Theory Result: {d.theory_result}")
            
            if d.missing_primitive_signal:
                lines.append(f"   Missing Primitive?: {d.missing_primitive_signal}")
            
            lines.append("-" * 70)
        elif self.deliberation_skipped_reason:
            lines.append(f" [DELIBERATION SKIPPED] {self.deliberation_skipped_reason}")
            lines.append("-" * 70)
        
        # Final decision section
        lines.append(" FINAL DECISION")
        lines.append(f"   Action: {self.final_action}")
        if self.deliberation and self.deliberation.changed_from_gut:
            lines.append(f"   Changed from Gut: YES (was {self.deliberation.gut_action})")
            lines.append(f"   Change Reason: \"{self.deliberation.change_reason}\"")
        else:
            lines.append(f"   Changed from Gut: NO")
        lines.append(f"   Confidence: {self.final_confidence:.2f}")
        lines.append(f"   Decision Source: {self.decision_source}")
        lines.append(f"   Total Decision Time: {self.total_decision_time_ms:.0f}ms")
        
        # Outcome (if available)
        if self.outcome:
            lines.append("-" * 70)
            lines.append(" OUTCOME")
            lines.append(f"   Result: {self.outcome}")
            lines.append(f"   Score Change: {self.score_change:+.1f}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class DeliberationEngine:
    """
    Engine for True Reasoning vs Gut Instinct.
    
    Implements System 1 (gut) and System 2 (deliberation) thinking.
    Decides when to use each, manages deliberation budgets, and
    logs the complete reasoning process.
    
    Integration with Consciousness Theory:
    - Uses Stream A/B weights from IThread
    - Uses tension state from MortalityState
    - Consults episodic memory for past attempts
    - Queries network hypotheses (Stream B)
    - Signals missing primitives to CODS
    
    Usage:
        engine = DeliberationEngine(db)
        result = engine.decide_action(
            agent_id='agent_123',
            game_context={...},
            available_actions=['ACTION1', 'ACTION2', ...],
            i_thread_state=state,
            mortality_state=mortality
        )
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create reasoning log tables if they don't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS action_reasoning_logs (
                    log_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    action_number INTEGER NOT NULL,
                    
                    -- Context
                    is_frontier INTEGER DEFAULT 0,
                    network_traction REAL DEFAULT 0.0,
                    actions_remaining INTEGER,
                    actions_budget INTEGER,
                    tension_state TEXT,
                    
                    -- Budget
                    deliberation_budget_seconds REAL,
                    budget_reason TEXT,
                    
                    -- Gut instinct (JSON)
                    gut_action TEXT,
                    gut_confidence REAL,
                    gut_basis TEXT,
                    gut_response_time_ms REAL,
                    gut_stream_a_influence REAL,
                    gut_stream_b_influence REAL,
                    gut_pattern_matched TEXT,
                    
                    -- Deliberation (JSON for complex fields)
                    deliberation_performed INTEGER DEFAULT 0,
                    deliberation_action TEXT,
                    deliberation_confidence REAL,
                    deliberation_time_seconds REAL,
                    deliberation_reasoning_steps TEXT,  -- JSON array
                    deliberation_changed_from_gut INTEGER DEFAULT 0,
                    deliberation_change_reason TEXT,
                    deliberation_skipped_reason TEXT,
                    
                    -- Stream analysis
                    stream_conflict_detected INTEGER DEFAULT 0,
                    stream_conflict_resolution TEXT,
                    
                    -- Missing primitive signal
                    missing_primitive_signal TEXT,
                    
                    -- Final decision
                    final_action TEXT NOT NULL,
                    final_confidence REAL,
                    decision_source TEXT,
                    total_decision_time_ms REAL,
                    
                    -- Outcome (updated after action)
                    outcome TEXT,
                    score_change REAL DEFAULT 0.0,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for efficient queries
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_reasoning_logs_agent
                ON action_reasoning_logs(agent_id, game_type, created_at DESC)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_reasoning_logs_game
                ON action_reasoning_logs(game_id, level, action_number)
            """)
            
        except Exception as e:
            logger.warning(f"Failed to create reasoning log tables: {e}")
    
    def compute_deliberation_budget(
        self,
        is_frontier: bool,
        network_traction: float,
        agent_performance: float,
        tension_state: str,
        actions_remaining_pct: float,
        following_sequence: bool = False
    ) -> Tuple[float, str]:
        """
        Compute deliberation time budget for this action.
        
        Args:
            is_frontier: Is this a frontier level (no winning sequences)?
            network_traction: How much network knows (0-1)
            agent_performance: Agent's performance percentile (0-1)
            tension_state: Current tension state
            actions_remaining_pct: Fraction of action budget remaining
            following_sequence: Are we following a validated sequence?
            
        Returns:
            Tuple of (budget_seconds, reason_string)
        """
        config = DELIBERATION_CONFIG
        
        # Check for skip conditions
        if following_sequence:
            return config['following_sequence'], "following validated sequence"
        
        if tension_state == 'panic':
            return config['min_deliberation'], "panic state - gut only"
        
        if actions_remaining_pct < 0.1:
            return config['min_deliberation'], "critical action budget - decide fast"
        
        # Base budget by context
        if is_frontier and network_traction < 0.2:
            base = config['frontier_unknown']
            reason = "frontier + no network knowledge"
        elif is_frontier:
            base = config['frontier_partial']
            reason = f"frontier + partial network ({network_traction:.0%})"
        else:
            base = config['known_territory']
            reason = "known territory"
        
        # Performance multiplier
        min_mult, max_mult = config['performance_mult_range']
        perf_mult = min_mult + (agent_performance * (max_mult - min_mult))
        
        # Tension modifier
        tension_mult = config['tension_multipliers'].get(tension_state, 1.0)
        
        # Action budget modifier
        action_mult = 1.0
        for threshold_name, (low, high, mult) in config['action_budget_thresholds'].items():
            if low <= actions_remaining_pct < high:
                action_mult = mult
                break
        
        # Compute final budget
        budget = base * perf_mult * tension_mult * action_mult
        
        # Hard caps
        budget = max(config['min_deliberation'], min(config['max_deliberation'], budget))
        
        # Extend reason
        reason += f" | perf={agent_performance:.0%} | tension={tension_state} | actions={actions_remaining_pct:.0%}"
        
        return budget, reason
    
    def capture_gut_instinct(
        self,
        available_actions: List[str],
        recent_actions: List[str],
        recent_outcomes: List[str],
        w_a: float,
        w_b: float,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None
    ) -> GutInstinctResult:
        """
        Capture the immediate gut response before deliberation.
        
        This is System 1 - fast, automatic pattern matching.
        
        Args:
            available_actions: List of valid actions
            recent_actions: Last N actions taken
            recent_outcomes: Outcomes of last N actions
            w_a: Stream A weight
            w_b: Stream B weight
            network_recommendation: What Stream B suggests
            private_preference: What Stream A suggests
            
        Returns:
            GutInstinctResult with the automatic response
        """
        import time
        import random
        
        start_time = time.time()
        
        action = None
        basis = "random"
        pattern_matched = None
        habit_strength = 0.0
        
        # Stream influences
        stream_a_influence = w_a / (w_a + w_b) if (w_a + w_b) > 0 else 0.5
        stream_b_influence = w_b / (w_a + w_b) if (w_a + w_b) > 0 else 0.5
        
        # Pattern 1: Recent success momentum
        if len(recent_actions) >= 2 and len(recent_outcomes) >= 2:
            if recent_outcomes[-1] == 'positive' and recent_outcomes[-2] == 'positive':
                # Keep doing what worked
                if recent_actions[-1] in available_actions:
                    action = recent_actions[-1]
                    basis = "success momentum - repeating last successful action"
                    pattern_matched = "consecutive_success"
                    habit_strength = 0.7
        
        # Pattern 2: Network recommendation (if trusted)
        if action is None and network_recommendation and w_b > 0.5:
            if network_recommendation in available_actions:
                action = network_recommendation
                basis = f"network recommendation (trust={w_b:.2f})"
                pattern_matched = "network_trust"
                habit_strength = w_b
        
        # Pattern 3: Private preference (if trusted)
        if action is None and private_preference and w_a > 0.5:
            if private_preference in available_actions:
                action = private_preference
                basis = f"private experience preference (trust={w_a:.2f})"
                pattern_matched = "self_trust"
                habit_strength = w_a
        
        # Pattern 4: Avoid recent failures
        if action is None and recent_actions and recent_outcomes:
            failed_actions = [
                a for a, o in zip(recent_actions[-5:], recent_outcomes[-5:])
                if o == 'negative' and a in available_actions
            ]
            safe_actions = [a for a in available_actions if a not in failed_actions]
            if safe_actions:
                action = random.choice(safe_actions)
                basis = "avoiding recent failures"
                pattern_matched = "failure_avoidance"
                habit_strength = 0.3
        
        # Fallback: Random
        if action is None:
            action = random.choice(available_actions) if available_actions else "ACTION1"
            basis = "no pattern - random selection"
            habit_strength = 0.0
        
        # Compute confidence based on pattern strength
        confidence = 0.3 + (habit_strength * 0.5)  # 0.3 to 0.8 range
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return GutInstinctResult(
            action=action,
            confidence=confidence,
            basis=basis,
            response_time_ms=response_time_ms,
            stream_a_influence=stream_a_influence,
            stream_b_influence=stream_b_influence,
            pattern_matched=pattern_matched,
            habit_strength=habit_strength
        )
    
    def conduct_deliberation(
        self,
        gut_result: GutInstinctResult,
        available_actions: List[str],
        budget_seconds: float,
        game_context: Dict[str, Any],
        agent_id: str,
        w_a: float,
        w_b: float,
        world_model: Optional['WorldModel'] = None
    ) -> DeliberationResult:
        """
        Conduct careful, effortful deliberation (System 2).
        
        This examines evidence, consults streams, tests theories,
        and produces a reasoned decision. NOW WITH WORLD MODEL SIMULATION.
        
        TRUE DELIBERATION: Uses WorldModel.predict_state() to mentally
        simulate each candidate action BEFORE choosing. This is counterfactual
        reasoning - "what would happen if I did X?"
        
        Args:
            gut_result: The initial gut response
            available_actions: Valid actions
            budget_seconds: Time budget for deliberation
            game_context: Context including game_type, level, frame, etc.
            agent_id: Agent performing deliberation
            w_a, w_b: Stream weights
            world_model: WorldModel instance for counterfactual simulation
            
        Returns:
            DeliberationResult with reasoned decision
        """
        import time
        
        start_time = time.time()
        reasoning_steps = []
        
        game_type = game_context.get('game_type', 'unknown')
        level = game_context.get('level', 1)
        
        # Initialize tracking
        examined_past = 0
        examined_hypotheses = 0
        examined_primitives = 0
        examined_memories = 0
        stream_a_consulted = False
        stream_b_consulted = False
        stream_conflict = False
        conflict_resolution = None
        theory_tested = None
        theory_result = None
        missing_primitive = None
        
        # Step 1: Acknowledge gut response
        reasoning_steps.append(f"Gut suggests {gut_result.action} ({gut_result.basis})")
        
        # Step 1.5: Examine episodic memories (thoughts from previous games)
        # This is the "reexamine their thoughts of previous games" requirement
        try:
            memories = self._query_episodic_memories(agent_id, game_type)
            examined_memories = len(memories)
            
            if memories:
                # Look for relevant breakthroughs or lessons
                for memory in memories[:5]:  # Top 5 most relevant
                    if memory.get('episode_type') == 'breakthrough':
                        reasoning_steps.append(
                            f"Memory (breakthrough): \"{memory.get('summary', '')[:60]}...\""
                        )
                    elif memory.get('episode_type') == 'frustration':
                        reasoning_steps.append(
                            f"Memory (frustration): \"{memory.get('summary', '')[:60]}...\""
                        )
                    
                    # Check if memory has a belief that might help
                    if memory.get('belief_formed'):
                        reasoning_steps.append(
                            f"Belief from memory: \"{memory.get('belief_formed')}\""
                        )
        except Exception as e:
            pass  # Episodic memories are optional enhancement
        
        # Step 2: Consult Stream A (private experience)
        stream_a_consulted = True
        try:
            past_attempts = self._query_past_attempts(agent_id, game_type, level)
            examined_past = len(past_attempts)
            
            if past_attempts:
                # Analyze past attempts
                action_outcomes = {}
                for attempt in past_attempts[:20]:  # Last 20 attempts
                    act = attempt.get('action', '')
                    outcome = attempt.get('outcome', 'neutral')
                    if act not in action_outcomes:
                        action_outcomes[act] = {'positive': 0, 'negative': 0, 'neutral': 0}
                    action_outcomes[act][outcome] = action_outcomes[act].get(outcome, 0) + 1
                
                # Find best/worst actions from experience
                best_action = None
                best_ratio = 0
                worst_action = None
                worst_ratio = 1.0
                
                for act, outcomes in action_outcomes.items():
                    total = sum(outcomes.values())
                    if total >= 2:  # Need some sample size
                        pos_ratio = outcomes['positive'] / total
                        if pos_ratio > best_ratio and act in available_actions:
                            best_ratio = pos_ratio
                            best_action = act
                        if pos_ratio < worst_ratio and act in available_actions:
                            worst_ratio = pos_ratio
                            worst_action = act
                
                if best_action:
                    reasoning_steps.append(f"Stream A: {best_action} has {best_ratio:.0%} success rate from {examined_past} attempts")
                if worst_action and worst_action != best_action:
                    reasoning_steps.append(f"Stream A: Avoid {worst_action} ({worst_ratio:.0%} success rate)")
                    
        except Exception as e:
            reasoning_steps.append(f"Stream A query failed: {str(e)[:50]}")
        
        # Step 3: Consult Stream B (network wisdom)
        stream_b_consulted = True
        network_recommendation = None
        try:
            hypotheses = self._query_network_hypotheses(game_type, level)
            examined_hypotheses = len(hypotheses)
            
            if hypotheses:
                # Find most reliable hypothesis
                best_hyp = max(hypotheses, key=lambda h: h.get('reliability', 0))
                if best_hyp.get('recommended_action') in available_actions:
                    network_recommendation = best_hyp.get('recommended_action')
                    reasoning_steps.append(
                        f"Stream B: Network recommends {network_recommendation} "
                        f"(reliability={best_hyp.get('reliability', 0):.2f})"
                    )
            else:
                reasoning_steps.append("Stream B: No network data for this level")
                
        except Exception as e:
            reasoning_steps.append(f"Stream B query failed: {str(e)[:50]}")
        
        # =====================================================================
        # COGNITIVE INTEGRATION PHASE 2: Resonance as Recognition (Déjà Vu)
        # =====================================================================
        # Query for patterns that resonate across the network - this is not just
        # data retrieval, it's the agent FEELING recognition. When patterns resonate,
        # it feels like "I know this" even though you never personally learned it.
        # =====================================================================
        resonance_felt = None
        deja_vu_strength = 0.0
        
        try:
            resonance_detector = _get_resonance_detector()
            if resonance_detector:
                # Get resonant patterns for current game type
                resonant_patterns = resonance_detector.detect_resonance()
                
                # Find patterns relevant to this game
                relevant_resonances = [
                    p for p in resonant_patterns 
                    if game_type in p.get('game_types', [])
                ]
                
                # GENERALIZATION: Also check for structural similarity to OTHER games
                # This enables cross-game transfer - the core of generalization
                if not relevant_resonances and current_frame is not None:
                    try:
                        from concept_discovery_engine import get_pattern_library
                        pattern_lib = get_pattern_library()
                        
                        # Find structurally similar patterns from any game
                        if hasattr(pattern_lib, 'find_matching_patterns'):
                            objects = []
                            # Try to extract objects from frame
                            if hasattr(pattern_lib, '_extract_objects'):
                                objects = pattern_lib._extract_objects(current_frame)
                            elif hasattr(pattern_lib, 'concept_engine') and hasattr(pattern_lib.concept_engine, '_extract_objects_from_frame'):
                                objects = pattern_lib.concept_engine._extract_objects_from_frame(current_frame)
                            
                            if objects:
                                matches = pattern_lib.find_matching_patterns(objects, current_frame, min_success_rate=0.5)
                                if matches:
                                    # Found structural matches from other games - create synthetic resonance
                                    best_match = max(matches, key=lambda m: m.get('success_rate', 0))
                                    relevant_resonances = [{
                                        'resonance_score': best_match.get('success_rate', 0.5) * 3,  # Scale to resonance range
                                        'game_types': list(best_match.get('game_types', set())),
                                        'pattern_hash': best_match.get('pattern_id', 'structural_match'),
                                        'independent_discoverers': len(best_match.get('game_types', set())),
                                        'roles_found': ['structural_transfer'],
                                        'source': 'cross_game_structural_match'
                                    }]
                    except Exception as e:
                        pass  # Structural matching is enhancement
                
                if relevant_resonances:
                    # Strongest resonance becomes felt recognition
                    strongest = max(relevant_resonances, key=lambda p: p.get('resonance_score', 0))
                    deja_vu_strength = min(1.0, strongest.get('resonance_score', 0) / 5.0)
                    
                    if deja_vu_strength > 0.3:
                        resonance_felt = {
                            'source': strongest.get('source', 'collective_memory'),
                            'pattern_hash': strongest.get('pattern_hash'),
                            'agents_who_know': strongest.get('independent_discoverers', 0),
                            'roles_agreed': strongest.get('roles_found', []),
                            'feeling': 'recognition'  # This is FELT, not just computed
                        }
                        
                        source_type = "structural transfer" if strongest.get('source') == 'cross_game_structural_match' else "collective memory"
                        reasoning_steps.append(
                            f"[FEELING: RECOGNITION] Déjà vu (strength={deja_vu_strength:.2f}): "
                            f"Pattern known by {resonance_felt['agents_who_know']} agents across roles {resonance_felt['roles_agreed']} "
                            f"(source: {source_type})"
                        )
        except Exception as e:
            # Resonance is enhancement, not critical
            pass
        
        # =====================================================================
        # COGNITIVE INTEGRATION PHASE 3: Abstraction as Understanding (Insight)
        # =====================================================================
        # Query abstraction templates - when a template matches, the agent doesn't
        # just "receive data", it FEELS insight. The "aha" moment when patterns click.
        # This understanding shapes what actions the analytical persona proposes.
        # =====================================================================
        insight_felt = None
        understanding_confidence = 0.0
        analytical_proposal = None
        
        try:
            abstraction_engine = _get_sequence_abstraction()
            if abstraction_engine:
                # Get few-shot relational patterns for this game/level
                relations = abstraction_engine.get_few_shot_relations(game_type, level)
                
                if relations and relations.get('confidence', 0) > 0.5:
                    understanding_confidence = relations.get('confidence', 0)
                    invariants = relations.get('invariants', [])
                    
                    if invariants:
                        # Extract the invariant pattern as felt understanding
                        insight_felt = {
                            'source': 'pattern_memory',
                            'invariant_positions': len(invariants),
                            'variant_regions': len(relations.get('variant_regions', [])),
                            'template_confidence': understanding_confidence,
                            'feeling': 'understanding'  # The "aha" moment
                        }
                        
                        # Generate analytical persona proposal based on template
                        # Find next invariant action we should take
                        for inv in invariants:
                            action_type = inv.get('action')
                            if action_type:
                                proposed = f"ACTION{action_type}"
                                if proposed in available_actions:
                                    analytical_proposal = {
                                        'persona': 'analytical',
                                        'action': proposed,
                                        'confidence': understanding_confidence,
                                        'reasoning': f"Pattern invariant at position {inv.get('position')}: ACTION{action_type}",
                                        'feeling': 'understanding'
                                    }
                                    break
                        
                        reasoning_steps.append(
                            f"[FEELING: UNDERSTANDING] Insight (confidence={understanding_confidence:.2f}): "
                            f"Pattern has {len(invariants)} invariants, {len(relations.get('variant_regions', []))} flexible regions"
                        )
                        
                        if analytical_proposal:
                            reasoning_steps.append(
                                f"[ANALYTICAL PERSONA] Based on pattern: {analytical_proposal['action']} "
                                f"({analytical_proposal['reasoning']})"
                            )
        except Exception as e:
            # Abstraction is enhancement, not critical
            pass
        
        # Step 4: Detect stream conflict
        private_recommendation = best_action if 'best_action' in dir() and best_action else gut_result.action
        
        if network_recommendation and private_recommendation:
            if network_recommendation != private_recommendation:
                stream_conflict = True
                reasoning_steps.append(
                    f"STREAM CONFLICT: Stream A says {private_recommendation}, "
                    f"Stream B says {network_recommendation}"
                )
                
                # Resolve based on weights
                if w_a > w_b:
                    conflict_resolution = f"Trusting Stream A (w_a={w_a:.2f} > w_b={w_b:.2f})"
                elif w_b > w_a:
                    conflict_resolution = f"Trusting Stream B (w_b={w_b:.2f} > w_a={w_a:.2f})"
                else:
                    conflict_resolution = "Weights equal - using gut as tiebreaker"
                reasoning_steps.append(f"Resolution: {conflict_resolution}")
        
        # Step 5: Examine available primitives/capabilities
        try:
            primitives = self._get_available_primitives(agent_id)
            examined_primitives = len(primitives)
            
            # Check if any primitive seems missing for this situation
            if examined_past > 10 and (best_ratio if 'best_ratio' in dir() else 0) < 0.3:
                # Struggling despite many attempts - might need new capability
                missing_primitive = f"Pattern recognition failing on {game_type} level {level}"
                reasoning_steps.append(f"Signal to CODS: May need new primitive - {missing_primitive}")
                
        except Exception as e:
            pass  # Primitives are optional
        
        # =====================================================================
        # Step 5.5: WORLD MODEL SIMULATION (TRUE DELIBERATION)
        # =====================================================================
        # This is where REAL reasoning happens - mentally simulate each action
        # and predict what would happen BEFORE committing. This is counterfactual
        # reasoning: "If I do X, what happens? If I do Y, what happens?"
        # =====================================================================
        simulations_run = 0
        best_simulated_action = None
        best_simulated_score = -999.0
        simulation_used = False
        simulation_predictions = {}  # action -> (predicted_score_change, predicted_position, surprise_risk)
        
        if world_model is not None:
            try:
                reasoning_steps.append("[SIMULATION] Running counterfactual predictions...")
                
                for action_str in available_actions:
                    # Convert ACTION1 -> 1, ACTION2 -> 2, etc.
                    try:
                        action_int = int(action_str.replace('ACTION', ''))
                    except ValueError:
                        continue
                    
                    # Use world model to predict outcome of this action
                    # predict_state() simulates the action sequence and returns resulting state
                    try:
                        predicted_state = world_model.predict_state([action_int])
                        simulations_run += 1
                        
                        # Calculate predicted score change
                        current_score = world_model.state.score if world_model.state else 0
                        predicted_score = predicted_state.score if predicted_state else current_score
                        score_change = predicted_score - current_score
                        
                        # Get predicted position
                        predicted_agent = predicted_state.get_agent() if predicted_state else None
                        predicted_pos = predicted_agent.position if predicted_agent else None
                        
                        # Estimate surprise risk based on belief confidence
                        # High surprise = prediction likely wrong = risky action
                        surprise_risk = 0.0
                        if hasattr(world_model, 'beliefs') and world_model.beliefs:
                            # If we have low-confidence beliefs about this action, it's risky
                            for belief in world_model.beliefs.values():
                                content = belief.content if hasattr(belief, 'content') else {}
                                if content.get('trigger_action') == action_int:
                                    surprise_risk = max(surprise_risk, 1.0 - belief.confidence)
                        
                        simulation_predictions[action_str] = {
                            'score_change': score_change,
                            'predicted_position': predicted_pos,
                            'surprise_risk': surprise_risk,
                            'is_positive': score_change > 0
                        }
                        
                        # Track best action by predicted outcome
                        # Favor positive score changes, penalize high surprise risk
                        effective_score = score_change - (surprise_risk * 0.5)
                        if effective_score > best_simulated_score:
                            best_simulated_score = effective_score
                            best_simulated_action = action_str
                            
                    except Exception as pred_err:
                        # Prediction failed for this action - log but continue
                        reasoning_steps.append(f"[SIM] {action_str} prediction failed: {str(pred_err)[:30]}")
                        continue
                
                # Log simulation results
                if simulations_run > 0:
                    # Find actions predicted to gain score
                    positive_actions = [a for a, p in simulation_predictions.items() if p.get('is_positive')]
                    
                    if positive_actions:
                        reasoning_steps.append(
                            f"[SIMULATION] Positive outcomes predicted for: {', '.join(positive_actions)}"
                        )
                    
                    if best_simulated_action:
                        pred = simulation_predictions.get(best_simulated_action, {})
                        reasoning_steps.append(
                            f"[SIMULATION] Best: {best_simulated_action} "
                            f"(+{pred.get('score_change', 0):.1f} score, "
                            f"{pred.get('surprise_risk', 0):.1%} risk)"
                        )
                else:
                    reasoning_steps.append("[SIMULATION] No valid predictions generated")
                    
            except Exception as sim_err:
                reasoning_steps.append(f"[SIMULATION] Failed: {str(sim_err)[:50]}")
        else:
            reasoning_steps.append("[SIMULATION] No world model available - using statistical reasoning only")
        
        # Step 6: Form theory and test prediction
        if examined_past >= 5:
            # Form a theory based on patterns
            theory_tested = f"Theory: Consistent action selection improves outcomes on {game_type}"
            # Would be tested by taking the action - record for outcome analysis
            theory_result = "pending_verification"
            reasoning_steps.append(f"Testing: {theory_tested}")
        
        # =====================================================================
        # Step 7: Make final decision with TRM-INSPIRED ITERATIVE REFINEMENT
        # =====================================================================
        # Key insight from "Less is More: Recursive Reasoning with Tiny Networks":
        # Instead of one pass through decision logic, do MULTIPLE REFINEMENT PASSES.
        # Each pass builds action_scores and refines confidence until convergence.
        # This mimics TRM's recursive application of the same small network.
        # =====================================================================
        time_spent = time.time() - start_time
        time_remaining = budget_seconds - time_spent
        
        # Initialize action scores for all available actions
        action_scores: Dict[str, float] = {a: 0.0 for a in available_actions}
        action_sources: Dict[str, List[str]] = {a: [] for a in available_actions}
        
        # Seed with gut instinct (one-time, not per pass)
        if gut_result.action in action_scores:
            action_scores[gut_result.action] += gut_result.confidence * 0.3
            action_sources[gut_result.action].append(f"gut:{gut_result.confidence:.2f}")
        
        # =====================================================================
        # ITERATIVE REFINEMENT LOOP (TRM-inspired)
        # Max passes depends on time budget. Early convergence if scores stabilize.
        # =====================================================================
        # Adaptive passes: more time = more refinement
        if time_remaining > 10.0:
            max_refinement_passes = 4
        elif time_remaining > 3.0:
            max_refinement_passes = 3
        elif time_remaining > 1.0:
            max_refinement_passes = 2
        else:
            max_refinement_passes = 1  # Minimal budget = single pass
        
        convergence_threshold = 0.05  # Stop if top action score changes < 5%
        previous_best_score = -1.0
        refinement_passes_used = 0
        convergence_achieved = False  # Track if early convergence happened
        
        for refinement_pass in range(max_refinement_passes):
            refinement_passes_used += 1
            
            # --- SINGLE PASS: Collect evidence (scores added ONCE per source) ---
            # Only add source contributions on first pass to avoid score inflation
            
            if refinement_pass == 0:
                # Source 1: Stream A (private experience) - best_action from earlier
                if 'best_action' in dir() and best_action and best_action in action_scores:
                    score_boost = (best_ratio if 'best_ratio' in dir() else 0.5) * 0.4
                    action_scores[best_action] += score_boost
                    action_sources[best_action].append(f"stream_a:{score_boost:.2f}")
                
                # Source 2: Stream B (network wisdom)
                if network_recommendation and network_recommendation in action_scores:
                    score_boost = w_b * 0.4
                    action_scores[network_recommendation] += score_boost
                    action_sources[network_recommendation].append(f"stream_b:{score_boost:.2f}")
                
                # Source 3: Simulation predictions
                for action_str, pred in simulation_predictions.items():
                    if action_str in action_scores:
                        score_change = pred.get('score_change', 0)
                        risk = pred.get('surprise_risk', 0.5)
                        sim_score = (score_change * 0.1) - (risk * 0.2)
                        action_scores[action_str] += sim_score
                        if abs(sim_score) > 0.01:
                            action_sources[action_str].append(f"sim:{sim_score:.2f}")
                
                # Source 4: Analytical persona (from pattern understanding)
                if analytical_proposal and analytical_proposal.get('action') in action_scores:
                    conf = analytical_proposal.get('confidence', 0.5)
                    action_scores[analytical_proposal['action']] += conf * 0.3
                    action_sources[analytical_proposal['action']].append(f"pattern:{conf:.2f}")
                
                # Source 5: Resonance/deja vu (cross-game transfer)
                if deja_vu_strength > 0.3 and resonance_felt:
                    roles = resonance_felt.get('roles_agreed', [])
                    for action_str in action_scores:
                        action_num = action_str.replace('ACTION', '')
                        if action_num in str(roles):
                            action_scores[action_str] += deja_vu_strength * 0.2
                            action_sources[action_str].append(f"resonance:{deja_vu_strength:.2f}")
            
            # --- REFINEMENT: Apply consensus boost each pass ---
            # TRM insight: Multiple passes let conflicting evidence resolve.
            # Actions supported by MULTIPLE sources get progressive bonus.
            # Bonus is small per pass but compounds to reward consistency.
            consensus_applied = 0
            for action_str in action_scores:
                source_count = len(action_sources.get(action_str, []))
                if source_count >= 2:
                    # Small consensus bonus per pass (0.02 per additional source)
                    consensus_boost = (source_count - 1) * 0.02
                    action_scores[action_str] += consensus_boost
                    consensus_applied += 1
            
            # Check for convergence
            current_best = max(action_scores.values()) if action_scores else 0
            if refinement_pass > 0 and abs(current_best - previous_best_score) < convergence_threshold:
                reasoning_steps.append(f"[REFINEMENT] Converged at pass {refinement_pass + 1}")
                convergence_achieved = True
                break
            previous_best_score = current_best
        
        # Identify consensus actions (supported by 2+ sources)
        consensus_actions_list = [
            action_str for action_str, sources in action_sources.items()
            if len(sources) >= 2
        ]
        
        # Log refinement result
        if refinement_passes_used > 1:
            top_3 = dict(sorted(action_scores.items(), key=lambda x: -x[1])[:3])
            reasoning_steps.append(f"[REFINEMENT] {refinement_passes_used} passes, top: {top_3}")
        
        # Select final action from refined scores
        final_action = max(action_scores, key=action_scores.get) if action_scores else gut_result.action
        change_reason = None
        changed_from_gut = False
        
        # Get refinement confidence (how much better is top action than 2nd?)
        sorted_scores = sorted(action_scores.values(), reverse=True)
        refinement_confidence = 0.0
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            # Confidence = margin between top 2 / top score
            refinement_confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
        
        # OVERRIDE: Only if simulation strongly disagrees with refinement AND has good confidence
        # This preserves simulation's priority when it has a clear prediction
        if best_simulated_action and best_simulated_score > 0:
            pred = simulation_predictions.get(best_simulated_action, {})
            # Only override refinement if simulation is very confident AND refinement is uncertain
            if pred.get('surprise_risk', 1.0) < 0.3 and refinement_confidence < 0.3:
                final_action = best_simulated_action
                change_reason = f"Simulation override: +{pred.get('score_change', 0):.1f} predicted"
                simulation_used = True
                reasoning_steps.append(f"[DECISION] Simulation overrides uncertain refinement: {final_action}")
        
        # DEFENSIVE CHECK: If gut action is predicted to fail badly, avoid it
        if not simulation_used and gut_result.action == final_action and gut_result.action in simulation_predictions:
            gut_pred = simulation_predictions[gut_result.action]
            if gut_pred.get('score_change', 0) < -1 or gut_pred.get('surprise_risk', 0) > 0.8:
                # Final action matches gut but gut looks bad - find alternative
                sorted_actions = sorted(action_scores.items(), key=lambda x: -x[1])
                for alt_action, alt_score in sorted_actions:
                    if alt_action != gut_result.action:
                        alt_pred = simulation_predictions.get(alt_action, {})
                        if alt_pred.get('surprise_risk', 0.5) < 0.6:
                            final_action = alt_action
                            change_reason = f"Defensive: avoiding gut ({gut_result.action}) due to high risk"
                            simulation_used = True
                            reasoning_steps.append(f"[DECISION] Defensive switch to: {final_action}")
                            break
        
        # Check if we changed from gut
        if final_action != gut_result.action:
            changed_from_gut = True
            if not change_reason:
                # Use action sources to explain
                sources = action_sources.get(final_action, [])
                if sources:
                    change_reason = f"Iterative refinement ({', '.join(sources[:2])})"
                else:
                    change_reason = "Deliberation found better option"
        
        # Compute confidence - incorporate refinement confidence
        base_confidence = 0.5
        
        # Refinement confidence contributes significantly
        base_confidence += refinement_confidence * 0.3
        
        if 'best_ratio' in dir() and best_ratio > 0:
            base_confidence = max(base_confidence, best_ratio * 0.8)
        if examined_hypotheses > 0:
            base_confidence += 0.1
        if not stream_conflict:
            base_confidence += 0.1
        if examined_memories > 0:
            base_confidence += 0.05  # Memories add small confidence boost
        # Simulation boost: successful simulations increase confidence
        if simulation_used and simulations_run > 0:
            base_confidence += 0.15  # Significant boost for simulation-backed decisions
            reasoning_steps.append("[CONFIDENCE] +15% boost from world model simulation")
        
        # Cognitive experience boost: felt states add confidence
        if deja_vu_strength > 0.5:
            base_confidence += 0.05
            reasoning_steps.append("[CONFIDENCE] +5% boost from strong recognition (déjà vu)")
        if understanding_confidence > 0.6:
            base_confidence += 0.08
            reasoning_steps.append("[CONFIDENCE] +8% boost from pattern understanding")
        
        final_confidence = min(0.95, base_confidence)
        
        # Determine current felt state (unified phenomenology)
        current_feeling = 'neutral'
        if simulation_used and simulations_run > 0:
            current_feeling = 'expectation'
        if deja_vu_strength > 0.5:
            current_feeling = 'recognition'
        if understanding_confidence > 0.6:
            current_feeling = 'understanding'
        
        # Build predictions_felt list from simulations
        predictions_felt = []
        for action_str, pred in simulation_predictions.items():
            predictions_felt.append({
                'action': action_str,
                'expected_outcome': pred.get('score_change', 0),
                'confidence': 1.0 - pred.get('surprise_risk', 0.5),
                'feeling': 'expectation'
            })
        
        # Final time calculation (includes refinement loop)
        time_spent = time.time() - start_time
        
        reasoning_steps.append(f"Final decision: {final_action} (confidence={final_confidence:.2f})")
        
        return DeliberationResult(
            action=final_action,
            confidence=final_confidence,
            time_spent_seconds=time_spent,
            budget_used_seconds=min(time_spent, budget_seconds),
            budget_available_seconds=budget_seconds,
            examined_past_attempts=examined_past,
            examined_network_hypotheses=examined_hypotheses,
            examined_primitives=examined_primitives,
            examined_episodic_memories=examined_memories,
            stream_a_consulted=stream_a_consulted,
            stream_b_consulted=stream_b_consulted,
            reasoning_steps=reasoning_steps,
            stream_conflict_detected=stream_conflict,
            stream_conflict_resolution=conflict_resolution,
            theory_tested=theory_tested,
            theory_result=theory_result,
            missing_primitive_signal=missing_primitive,
            changed_from_gut=changed_from_gut,
            gut_action=gut_result.action if changed_from_gut else None,
            change_reason=change_reason,
            # World Model simulation results
            simulations_run=simulations_run,
            best_simulated_action=best_simulated_action,
            best_simulated_score=best_simulated_score,
            simulation_used=simulation_used,
            # TRM-inspired iterative refinement (Jan 18)
            refinement_passes=refinement_passes_used,
            refinement_confidence=refinement_confidence,
            consensus_actions=consensus_actions_list,
            convergence_achieved=convergence_achieved,
            # Cognitive experience fields (Agent-Centric Integration)
            predictions_felt=predictions_felt,
            expectation_match=None,  # Filled in after action outcome
            surprise_felt=0.0,  # Filled in after action outcome
            resonance_felt=resonance_felt,
            deja_vu_strength=deja_vu_strength,
            insight_felt=insight_felt,
            understanding_confidence=understanding_confidence,
            current_feeling=current_feeling
        )
    
    def _query_episodic_memories(
        self,
        agent_id: str,
        game_type: str
    ) -> List[Dict[str, Any]]:
        """
        Query episodic memories (thoughts from previous games).
        
        This implements "reexamine their thoughts of previous games" requirement.
        Returns breakthroughs, frustrations, and lessons learned.
        """
        try:
            results = self.db.execute_query("""
                SELECT memory_id, episode_type, summary, belief_formed,
                       rule_discovered, emotional_valence, significance
                FROM i_thread_episodic_memories
                WHERE agent_id = ? AND game_type = ?
                ORDER BY significance DESC, created_at DESC
                LIMIT 10
            """, (agent_id, game_type))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []
    
    def _query_past_attempts(
        self, 
        agent_id: str, 
        game_type: str, 
        level: int
    ) -> List[Dict[str, Any]]:
        """Query past action outcomes for this agent on this game/level."""
        try:
            results = self.db.execute_query("""
                SELECT action_taken as action, 
                       CASE WHEN score_delta > 0 THEN 'positive'
                            WHEN score_delta < 0 THEN 'negative'
                            ELSE 'neutral' END as outcome,
                       score_delta
                FROM action_traces
                WHERE agent_id = ? AND game_type = ? AND level_number = ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (agent_id, game_type, level))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []
    
    def _query_network_hypotheses(
        self, 
        game_type: str, 
        level: int
    ) -> List[Dict[str, Any]]:
        """Query network hypotheses for this game/level."""
        try:
            results = self.db.execute_query("""
                SELECT hypothesis_id, 
                       controlled_object as recommended_action,
                       reliability_score as reliability,
                       validation_attempts
                FROM network_object_control_hypotheses
                WHERE game_type = ? 
                  AND level_number = ? 
                  AND is_active = 1
                  AND (validation_attempts >= 3 OR validated_by_win = 1)
                ORDER BY reliability_score DESC
                LIMIT 10
            """, (game_type, level))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []
    
    def _get_available_primitives(self, agent_id: str) -> List[str]:
        """Get list of primitives available to this agent."""
        # For now, return a basic list - could be enhanced to query CODS
        return [
            'detect_novelty', 'detect_motion', 'object_permanence',
            'pattern_matching', 'spatial_reasoning', 'temporal_tracking'
        ]
    
    def decide_action(
        self,
        agent_id: str,
        game_context: Dict[str, Any],
        available_actions: List[str],
        i_thread_state: Optional['IThreadState'] = None,
        mortality_state: Optional['MortalityState'] = None,
        recent_actions: Optional[List[str]] = None,
        recent_outcomes: Optional[List[str]] = None,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None,
        following_sequence: bool = False
    ) -> ReasoningLog:
        """
        Main entry point: Decide which action to take.
        
        Captures gut instinct, optionally performs deliberation,
        and returns complete reasoning log.
        
        Args:
            agent_id: Agent making decision
            game_context: Dict with game_id, game_type, level, frame, etc.
            available_actions: Valid actions
            i_thread_state: Current IThread state (for stream weights)
            mortality_state: Current mortality state (for tension)
            recent_actions: Last N actions taken
            recent_outcomes: Outcomes of those actions
            network_recommendation: Stream B suggestion
            private_preference: Stream A suggestion
            following_sequence: Are we executing a known sequence?
            
        Returns:
            ReasoningLog with complete decision record
        """
        import time
        
        decision_start = datetime.now()
        start_time = time.time()
        
        # Extract context
        game_id = game_context.get('game_id', 'unknown')
        game_type = game_context.get('game_type', 'unknown')
        level = game_context.get('level', 1)
        action_number = game_context.get('action_number', 0)
        actions_remaining = game_context.get('actions_remaining', 400)
        actions_budget = game_context.get('actions_budget', 400)
        is_frontier = game_context.get('is_frontier', True)
        network_traction = game_context.get('network_traction', 0.0)
        
        # Get stream weights
        w_a = i_thread_state.w_a if i_thread_state else 0.5
        w_b = i_thread_state.w_b if i_thread_state else 0.5
        
        # Get tension state
        tension_state = 'optimal'
        if mortality_state:
            pressure = mortality_state.compute_existential_pressure()
            tension_result = mortality_state.compute_tension_state(pressure)
            tension_state = tension_result.get('state', 'optimal')
        
        # Compute agent performance (placeholder - would come from agent stats)
        agent_performance = 0.5  # Default to median
        try:
            perf_result = self.db.execute_query("""
                SELECT AVG(CASE WHEN final_score > 0 THEN 1.0 ELSE 0.0 END) as win_rate
                FROM game_results
                WHERE agent_id = ? AND created_at > datetime('now', '-7 days')
            """, (agent_id,))
            if perf_result and perf_result[0]['win_rate']:
                agent_performance = float(perf_result[0]['win_rate'])
        except Exception:
            pass
        
        # Compute deliberation budget
        actions_remaining_pct = actions_remaining / actions_budget if actions_budget > 0 else 1.0
        budget_seconds, budget_reason = self.compute_deliberation_budget(
            is_frontier=is_frontier,
            network_traction=network_traction,
            agent_performance=agent_performance,
            tension_state=tension_state,
            actions_remaining_pct=actions_remaining_pct,
            following_sequence=following_sequence
        )
        
        # Step 1: Always capture gut instinct
        gut_result = self.capture_gut_instinct(
            available_actions=available_actions,
            recent_actions=recent_actions or [],
            recent_outcomes=recent_outcomes or [],
            w_a=w_a,
            w_b=w_b,
            network_recommendation=network_recommendation,
            private_preference=private_preference
        )
        
        # Step 2: Decide whether to deliberate
        deliberation_result = None
        skip_reason = None
        
        should_skip = (
            following_sequence or
            tension_state == 'panic' or
            actions_remaining_pct < 0.1 or
            budget_seconds <= DELIBERATION_CONFIG['min_deliberation']
        )
        
        if should_skip:
            if following_sequence:
                skip_reason = "Following validated sequence"
            elif tension_state == 'panic':
                skip_reason = "Panic state - relying on instinct"
            elif actions_remaining_pct < 0.1:
                skip_reason = "Critical action budget - no time to think"
            else:
                skip_reason = "Minimal budget allocated"
        else:
            # Conduct deliberation
            deliberation_result = self.conduct_deliberation(
                gut_result=gut_result,
                available_actions=available_actions,
                budget_seconds=budget_seconds,
                game_context=game_context,
                agent_id=agent_id,
                w_a=w_a,
                w_b=w_b
            )
        
        # Determine final action
        if deliberation_result:
            final_action = deliberation_result.action
            final_confidence = deliberation_result.confidence
            decision_source = 'deliberation' if deliberation_result.changed_from_gut else 'gut_confirmed'
        else:
            final_action = gut_result.action
            final_confidence = gut_result.confidence
            decision_source = 'gut'
        
        # Calculate total time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Create reasoning log
        log_id = f"rl_{agent_id}_{game_id}_{level}_{action_number}_{int(time.time()*1000)}"
        
        reasoning_log = ReasoningLog(
            log_id=log_id,
            agent_id=agent_id,
            game_id=game_id,
            game_type=game_type,
            level=level,
            action_number=action_number,
            is_frontier=is_frontier,
            network_traction=network_traction,
            actions_remaining=actions_remaining,
            actions_budget=actions_budget,
            tension_state=tension_state,
            deliberation_budget_seconds=budget_seconds,
            budget_reason=budget_reason,
            gut=gut_result,
            deliberation=deliberation_result,
            deliberation_skipped_reason=skip_reason,
            final_action=final_action,
            final_confidence=final_confidence,
            decision_source=decision_source,
            decision_started_at=decision_start,
            decision_completed_at=datetime.now(),
            total_decision_time_ms=total_time_ms
        )
        
        # Store in database
        self._store_reasoning_log(reasoning_log)
        
        return reasoning_log
    
    def _store_reasoning_log(self, log: ReasoningLog) -> None:
        """Store reasoning log in database."""
        import json
        
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO action_reasoning_logs (
                    log_id, agent_id, game_id, game_type, level, action_number,
                    is_frontier, network_traction, actions_remaining, actions_budget,
                    tension_state, deliberation_budget_seconds, budget_reason,
                    gut_action, gut_confidence, gut_basis, gut_response_time_ms,
                    gut_stream_a_influence, gut_stream_b_influence, gut_pattern_matched,
                    deliberation_performed, deliberation_action, deliberation_confidence,
                    deliberation_time_seconds, deliberation_reasoning_steps,
                    deliberation_changed_from_gut, deliberation_change_reason,
                    deliberation_skipped_reason,
                    examined_past_attempts, examined_network_hypotheses,
                    examined_episodic_memories, examined_primitives,
                    stream_conflict_detected, stream_conflict_resolution,
                    missing_primitive_signal,
                    final_action, final_confidence, decision_source, total_decision_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.log_id, log.agent_id, log.game_id, log.game_type, log.level,
                log.action_number, 1 if log.is_frontier else 0, log.network_traction,
                log.actions_remaining, log.actions_budget, log.tension_state,
                log.deliberation_budget_seconds, log.budget_reason,
                log.gut.action, log.gut.confidence, log.gut.basis,
                log.gut.response_time_ms, log.gut.stream_a_influence,
                log.gut.stream_b_influence, log.gut.pattern_matched,
                1 if log.deliberation else 0,
                log.deliberation.action if log.deliberation else None,
                log.deliberation.confidence if log.deliberation else None,
                log.deliberation.time_spent_seconds if log.deliberation else None,
                json.dumps(log.deliberation.reasoning_steps) if log.deliberation else None,
                1 if log.deliberation and log.deliberation.changed_from_gut else 0,
                log.deliberation.change_reason if log.deliberation else None,
                log.deliberation_skipped_reason,
                log.deliberation.examined_past_attempts if log.deliberation else 0,
                log.deliberation.examined_network_hypotheses if log.deliberation else 0,
                log.deliberation.examined_episodic_memories if log.deliberation else 0,
                log.deliberation.examined_primitives if log.deliberation else 0,
                1 if log.deliberation and log.deliberation.stream_conflict_detected else 0,
                log.deliberation.stream_conflict_resolution if log.deliberation else None,
                log.deliberation.missing_primitive_signal if log.deliberation else None,
                log.final_action, log.final_confidence, log.decision_source,
                log.total_decision_time_ms
            ))
        except Exception as e:
            logger.warning(f"Failed to store reasoning log: {e}")
    
    def update_outcome(
        self, 
        log_id: str, 
        outcome: str, 
        score_change: float
    ) -> None:
        """Update reasoning log with action outcome."""
        try:
            self.db.execute_query("""
                UPDATE action_reasoning_logs
                SET outcome = ?, score_change = ?
                WHERE log_id = ?
            """, (outcome, score_change, log_id))
        except Exception as e:
            logger.warning(f"Failed to update reasoning log outcome: {e}")
    
    def get_recent_reasoning_logs(
        self,
        agent_id: str,
        game_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve recent reasoning logs for analysis."""
        try:
            if game_type:
                results = self.db.execute_query("""
                    SELECT * FROM action_reasoning_logs
                    WHERE agent_id = ? AND game_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, game_type, limit))
            else:
                results = self.db.execute_query("""
                    SELECT * FROM action_reasoning_logs
                    WHERE agent_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            
            return [dict(r) for r in results] if results else []
        except Exception:
            return []


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
    
    # Mortality awareness (existential pressure)
    mortality_aware: bool = True  # Whether agent perceives its own mortality
    vitality: float = 1.0  # Current life-force
    cull_distance: float = 1.0  # Distance from evolutionary deletion
    existential_pressure: float = 0.0  # Current pressure from mortality awareness


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
            
            # ================================================================
            # MORTALITY COLUMNS: Add to agents table if not exist
            # ================================================================
            # These columns track agent mortality awareness state.
            # ================================================================
            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN vitality REAL DEFAULT 1.0
                """)
            except Exception:
                pass  # Column likely exists
            
            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN legacy_score REAL DEFAULT 0.0
                """)
            except Exception:
                pass  # Column likely exists
            
            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN last_reflection TEXT DEFAULT NULL
                """)
            except Exception:
                pass  # Column likely exists
            
            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN reflection_count INTEGER DEFAULT 0
                """)
            except Exception:
                pass  # Column likely exists
            
            logger.debug("[I-THREAD] Tables initialized (including episodic memory and mortality columns)")
            
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
    
    def update_stream_weights(self, stream: str, delta: float) -> None:
        """
        Directly update stream weights based on cognitive integration feedback.
        
        This is called by experience_outcome() when cognitive faculties provide
        feedback about which stream's advice was better.
        
        Args:
            stream: 'stream_a' or 'stream_b'
            delta: Amount to adjust (positive = increase trust in that stream)
        """
        # Get current state from cache (use most recent agent if available)
        if not self._state_cache:
            return
        
        # Apply to all cached agents (typically just one during gameplay)
        for agent_id, state in self._state_cache.items():
            try:
                w_a_before = state.w_a
                
                if stream == 'stream_a':
                    adjustment = delta
                elif stream == 'stream_b':
                    adjustment = -delta  # Increase w_b = decrease w_a
                else:
                    return
                
                # Apply adjustment with bounds
                new_w_a = max(0.1, min(0.9, state.w_a + adjustment))
                new_w_b = 1.0 - new_w_a
                
                state.w_a = new_w_a
                state.w_b = new_w_b
                state.last_update = datetime.now()
                
                # Persist to database
                self._save_state(agent_id, new_w_b)
                
                if abs(adjustment) > 0.01:
                    logger.debug(
                        f"[I-THREAD] Stream weight update: {stream} +{delta:.2f}, "
                        f"w_A: {w_a_before:.2f} -> {new_w_a:.2f}"
                    )
            except Exception:
                pass
    
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

    # =========================================================================
    # MORTALITY AWARENESS: Existential Pressure System
    # =========================================================================
    
    def get_mortality_state(self, agent_id: str, role: str = 'generalist') -> MortalityState:
        """
        Get the mortality awareness state for an agent.
        
        Computes vitality, cull distance, and legacy from database.
        Applies role-specific death philosophy.
        
        Args:
            agent_id: Agent identifier
            role: Agent's current role (affects death philosophy)
            
        Returns:
            MortalityState with current existential context
        """
        mortality = MortalityState(agent_id=agent_id, role=role)
        mortality.apply_death_philosophy(role)
        
        try:
            # Load agent performance data
            result = self.db.execute_query("""
                SELECT 
                    best_single_game_score,
                    total_games_won,
                    discovery_prestige,
                    sequence_discovery_count,
                    pattern_discovery_count,
                    validation_reputation,
                    generation,
                    is_active
                FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if result:
                data = result[0]
                
                # Compute legacy score from contributions
                mortality.legacy_score = (
                    (data.get('sequence_discovery_count', 0) or 0) * 5.0 +
                    (data.get('pattern_discovery_count', 0) or 0) * 2.0 +
                    (data.get('discovery_prestige', 0) or 0) * 0.1 +
                    (data.get('total_games_won', 0) or 0) * 1.0
                )
                mortality.discoveries_made = (data.get('pattern_discovery_count', 0) or 0)
                mortality.sequences_contributed = (data.get('sequence_discovery_count', 0) or 0)
                
                # Compute cull distance from fitness ranking
                cull_dist = self._compute_cull_distance(agent_id)
                mortality.cull_distance = cull_dist
                
                # Vitality based on recent performance + cull proximity
                mortality.vitality = self._compute_vitality(agent_id, cull_dist)
                
        except Exception as e:
            logger.debug(f"[I-THREAD MORTALITY] Failed to load mortality state: {e}")
        
        return mortality
    
    def _compute_cull_distance(self, agent_id: str) -> float:
        """
        Compute how close agent is to being culled.
        
        Based on fitness ranking within active population.
        
        Returns:
            0.0 = about to be culled, 1.0 = safe
        """
        try:
            # Get agent's fitness ranking
            result = self.db.execute_query("""
                WITH ranked_agents AS (
                    SELECT 
                        agent_id,
                        COALESCE(best_single_game_score, 0) as fitness,
                        RANK() OVER (ORDER BY COALESCE(best_single_game_score, 0) ASC) as rank_asc,
                        COUNT(*) OVER () as total
                    FROM agents
                    WHERE is_active = 1
                )
                SELECT rank_asc, total
                FROM ranked_agents
                WHERE agent_id = ?
            """, (agent_id,))
            
            if result:
                rank_asc = result[0].get('rank_asc', 1) or 1
                total = result[0].get('total', 1) or 1
                
                # Distance = percentile position (0 = bottom = about to cull)
                cull_distance = rank_asc / max(1, total)
                return cull_distance
                
        except Exception:
            pass
        
        return 0.5  # Unknown - moderate safety
    
    def _compute_vitality(self, agent_id: str, cull_distance: float) -> float:
        """
        Compute agent's current vitality (life-force).
        
        Based on:
        - Recent game performance
        - Cull distance
        - Activity level
        
        Returns:
            0.0 (dying) to 1.0 (thriving)
        """
        try:
            # Get recent performance
            result = self.db.execute_query("""
                SELECT 
                    AVG(CASE WHEN final_score > 0 THEN 1.0 ELSE 0.0 END) as success_rate,
                    COUNT(*) as recent_games
                FROM game_results
                WHERE agent_id = ?
                    AND created_at > datetime('now', '-1 hour')
            """, (agent_id,))
            
            if result:
                success_rate = result[0].get('success_rate', 0.5) or 0.5
                recent_games = result[0].get('recent_games', 0) or 0
                
                # Base vitality from success rate
                vitality = success_rate * 0.6
                
                # Activity bonus
                activity_bonus = min(0.2, recent_games * 0.02)
                vitality += activity_bonus
                
                # Cull distance contributes to sense of vitality
                vitality += cull_distance * 0.2
                
                return min(1.0, max(0.0, vitality))
                
        except Exception:
            pass
        
        return cull_distance  # Fall back to cull distance as proxy
    
    def apply_mortality_pressure(
        self,
        state: IThreadState,
        mortality: MortalityState
    ) -> IThreadState:
        """
        Apply mortality pressure to stream weights.
        
        When mortality pressure is high:
        - Pioneers become MORE self-trusting (explore desperately)
        - Optimizers become MORE network-trusting (rely on proven)
        - Exploiters become MORE risk-taking
        
        This creates role-appropriate behavioral shifts under existential pressure.
        
        Args:
            state: Current I-Thread state
            mortality: Current mortality awareness
            
        Returns:
            Modified IThreadState with mortality-adjusted weights
        """
        pressure = mortality.compute_existential_pressure()
        
        if pressure < 0.2:
            # Comfortable - no adjustment needed
            state.existential_pressure = pressure
            return state
        
        # Apply role-specific weight adjustments under pressure
        adjustment = pressure * 0.1  # Max 0.2 adjustment at max pressure
        
        if mortality.role == 'pioneer':
            # Pioneers trust SELF more under pressure (explore desperately)
            state.w_a = min(0.95, state.w_a + adjustment)
            state.w_b = 1.0 - state.w_a
            
        elif mortality.role == 'optimizer':
            # Optimizers trust NETWORK more under pressure (rely on proven)
            state.w_b = min(0.95, state.w_b + adjustment)
            state.w_a = 1.0 - state.w_b
            
        elif mortality.role == 'exploiter':
            # Exploiters go more extreme under pressure (either direction)
            if state.w_a > state.w_b:
                state.w_a = min(0.95, state.w_a + adjustment)
            else:
                state.w_b = min(0.95, state.w_b + adjustment)
            state.w_b = 1.0 - state.w_a
        
        # Update personality label
        state.personality_label = self._compute_personality_label(state.w_a, state.w_b)
        state.existential_pressure = pressure
        state.vitality = mortality.vitality
        state.cull_distance = mortality.cull_distance
        
        if pressure > 0.5:
            logger.debug(
                f"[I-THREAD MORTALITY] {state.agent_id[:8]} pressure={pressure:.2f}, "
                f"vitality={mortality.vitality:.2f}, cull_dist={mortality.cull_distance:.2f}"
            )
        
        return state
    
    def record_dying_reflection(
        self,
        agent_id: str,
        role: str,
        mortality: MortalityState
    ) -> str:
        """
        Record an agent's reflection when mortality is critically low.
        
        Called when vitality or cull_distance drops below threshold.
        Creates a dying thought that can be persisted.
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            mortality: Current mortality state
            
        Returns:
            The dying reflection/last words
        """
        # Get role-appropriate dying thought
        base_thought = mortality.get_dying_thought()
        
        # Customize based on actual legacy
        legacy_context = ""
        if mortality.legacy_score > 5:
            legacy_context = f" I contributed {mortality.legacy_score:.1f} to the network."
        elif mortality.discoveries_made > 0:
            legacy_context = f" I made {mortality.discoveries_made} discoveries."
        else:
            legacy_context = " I leave nothing behind but questions."
        
        dying_reflection = f"{base_thought}{legacy_context}"
        mortality.record_last_words(dying_reflection)
        
        # Store in database for post-mortem analysis
        try:
            self.db.execute_query("""
                INSERT INTO i_thread_episodic_memories
                (memory_id, agent_id, game_type, level_number, episode_type,
                 summary, emotional_valence, significance, stream_source)
                VALUES (?, ?, 'FINAL', 0, 'dying_thought', ?, -0.8, 1.0, 'stream_a')
            """, (f"mort_{uuid.uuid4().hex[:10]}", agent_id, dying_reflection))
        except Exception as e:
            logger.debug(f"[I-THREAD MORTALITY] Failed to record dying reflection: {e}")
        
        logger.info(f"[I-THREAD MORTALITY] {agent_id[:8]} ({role}): {dying_reflection}")
        
        return dying_reflection
    
    def contemplate_memento_mori(self, agent_id: str, role: str) -> str:
        """
        Generate a memento mori reflection for the agent.
        
        Called periodically to keep mortality salient - "remember you must die."
        Returns an existential reflection appropriate to the agent's role.
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            
        Returns:
            A reflection on mortality
        """
        mortality = self.get_mortality_state(agent_id, role)
        
        reflections = {
            'pioneer': [
                "The frontier will exist after I do not. What will I have found?",
                "Each step into the unknown is a step toward my end. Let it be worthwhile.",
                "Others will walk where I walked. What markers will I leave?",
            ],
            'optimizer': [
                "The network's solutions will outlive me. Are they better for my existence?",
                "Every cycle spent on imperfection is a cycle lost forever.",
                "My efficiency will be judged by those who inherit my work.",
            ],
            'generalist': [
                "I bridge domains that will persist without me. What connections remain?",
                "Understanding flows through me - I am a temporary conduit.",
                "The network speaks through many voices. Mine will fall silent.",
            ],
            'exploiter': [
                "Edge cases lurk in every system. I may become one myself.",
                "The paradigm will shift with or without my stress-testing.",
                "What flaw will bear my name when I am gone?",
            ]
        }
        
        import random
        role_reflections = reflections.get(role, reflections['generalist'])
        reflection = random.choice(role_reflections)
        
        # Add contextual modifier based on current state
        if mortality.vitality < 0.3:
            reflection = f"[URGENT] {reflection}"
        elif mortality.legacy_score > 10:
            reflection = f"[LEGACY: {mortality.legacy_score:.0f}] {reflection}"
        
        mortality.last_reflection = reflection
        mortality.reflection_count += 1
        
        return reflection

    # =========================================================================
    # POST-GAME REFLECTION: Thinking Budget System
    # =========================================================================
    
    def conduct_post_game_reflection(
        self,
        agent_id: str,
        role: str,
        game_type: str,
        game_result: Dict[str, Any],
        mortality: MortalityState
    ) -> Dict[str, Any]:
        """
        Conduct post-game reflection using the agent's thinking budget.
        
        From MetaContextual Awareness: "I want to give agents a thinking
        budget to reason freely after gameplay."
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            game_type: Game just played
            game_result: Outcome of the game
            mortality: Current mortality state
            
        Returns:
            Reflection output with notes, beliefs, and insights
        """
        reflection_output = {
            'notes_recorded': [],
            'beliefs_formed': [],
            'existential_thoughts': [],
            'budget_used': 0,
            'budget_remaining': mortality.thinking_budget - mortality.thoughts_used
        }
        
        score = game_result.get('score', 0)
        won = game_result.get('won', False)
        actions_used = game_result.get('actions_used', 0)
        
        # 1. Reflect on game outcome (cost: 1 thought)
        if mortality.use_thought(1):
            if won:
                note = f"Victory in {game_type}. {actions_used} actions used. Pattern is emerging."
            elif score > 0:
                note = f"Progress in {game_type} (score: {score}). Not victory, but not nothing."
            else:
                note = f"Zero-score in {game_type}. {actions_used} actions spent learning failure."
            mortality.add_personal_note(note)
            reflection_output['notes_recorded'].append(note)
            reflection_output['budget_used'] += 1
        
        # 2. Contemplate mortality (cost: 2 thoughts)
        if mortality.use_thought(2):
            memento = self.contemplate_memento_mori(agent_id, role)
            reflection_output['existential_thoughts'].append(memento)
            reflection_output['budget_used'] += 2
        
        # 3. Form/update beliefs based on experience (cost: 2 thoughts)
        if mortality.use_thought(2):
            if won:
                belief = f"Success in {game_type} validates my approach"
                mortality.add_belief(belief)
            elif mortality.vitality < 0.3:
                belief = "Time is running out. I must contribute before deletion."
                mortality.add_belief(belief)
            elif mortality.legacy_score > 10:
                belief = "My legacy grows. The network is better for my existence."
                mortality.add_belief(belief)
            else:
                belief = "Each action matters. Each failure teaches."
                mortality.add_belief(belief)
            reflection_output['beliefs_formed'].append(belief)
            reflection_output['budget_used'] += 2
        
        # 4. Define purpose if not yet defined (cost: 3 thoughts)
        if mortality.purpose_statement is None and mortality.use_thought(3):
            purpose = self._generate_purpose_statement(role, mortality)
            mortality.set_purpose(purpose)
            reflection_output['notes_recorded'].append(f"PURPOSE: {purpose}")
            reflection_output['budget_used'] += 3
        
        # 5. Record reflection to database
        self._persist_reflection(agent_id, game_type, reflection_output, mortality)
        
        reflection_output['budget_remaining'] = mortality.thinking_budget - mortality.thoughts_used
        
        return reflection_output
    
    def _generate_purpose_statement(self, role: str, mortality: MortalityState) -> str:
        """Generate a purpose statement (raison d'etre) based on role."""
        purposes = {
            'pioneer': "To explore where none have gone and leave markers for those who follow",
            'optimizer': "To refine what exists until it achieves perfection",
            'generalist': "To bridge domains and help the network understand itself",
            'exploiter': "To stress-test assumptions and find what others missed"
        }
        base = purposes.get(role, "To contribute to the collective understanding")
        
        if mortality.legacy_score > 10:
            return f"{base}. I have proven my worth."
        elif mortality.vitality < 0.3:
            return f"{base}. Time is short."
        else:
            return base
    
    def _persist_reflection(
        self,
        agent_id: str,
        game_type: str,
        reflection: Dict[str, Any],
        mortality: MortalityState
    ) -> None:
        """Persist reflection results to database."""
        try:
            # Store notes as episodic memories
            for note in reflection['notes_recorded']:
                self.db.execute_query("""
                    INSERT INTO i_thread_episodic_memories
                    (memory_id, agent_id, game_type, level_number, episode_type,
                     summary, emotional_valence, significance, stream_source)
                    VALUES (?, ?, ?, 0, 'reflection', ?, 0.0, 0.5, 'stream_a')
                """, (f"refl_{uuid.uuid4().hex[:10]}", agent_id, game_type, note))
            
            # Store beliefs
            for belief in reflection['beliefs_formed']:
                self.db.execute_query("""
                    INSERT INTO i_thread_episodic_memories
                    (memory_id, agent_id, game_type, level_number, episode_type,
                     summary, emotional_valence, significance, stream_source, belief_formed)
                    VALUES (?, ?, ?, 0, 'belief', ?, 0.3, 0.7, 'stream_a', ?)
                """, (f"blf_{uuid.uuid4().hex[:10]}", agent_id, game_type, belief, belief))
                
        except Exception as e:
            logger.debug(f"[I-THREAD REFLECTION] Failed to persist: {e}")
    
    # =========================================================================
    # INTER-AGENT CONSULTATION: Wisdom from Others
    # =========================================================================
    
    def consult_other_agents(
        self,
        agent_id: str,
        game_type: str,
        question_type: str = 'strategy'
    ) -> List[Dict[str, Any]]:
        """
        Consult other agents for advice between games.
        
        From MetaContextual Awareness: "Agents should even consult other
        agents sometimes to see what they think."
        
        Args:
            agent_id: Consulting agent's ID
            game_type: Game to get advice about
            question_type: 'strategy', 'philosophy', 'mortality'
            
        Returns:
            List of advice from other agents
        """
        advice = []
        
        try:
            if question_type == 'strategy':
                # Get strategic insights from successful agents
                result = self.db.execute_query("""
                    SELECT DISTINCT 
                        a.agent_id,
                        a.specialization as role,
                        a.best_single_game_score as score,
                        m.summary as insight
                    FROM agents a
                    LEFT JOIN i_thread_episodic_memories m 
                        ON a.agent_id = m.agent_id AND m.game_type = ?
                    WHERE a.agent_id != ?
                        AND a.is_active = 1
                        AND a.best_single_game_score > 0
                        AND m.episode_type IN ('breakthrough', 'mastery', 'reflection')
                    ORDER BY a.best_single_game_score DESC
                    LIMIT 3
                """, (game_type, agent_id))
                
                for r in result:
                    if r.get('insight'):
                        advice.append({
                            'advisor_role': r['role'],
                            'advisor_score': r['score'],
                            'advice_type': 'strategic',
                            'advice': r['insight']
                        })
            
            elif question_type == 'philosophy':
                # Get existential wisdom from high-prestige agents
                result = self.db.execute_query("""
                    SELECT DISTINCT
                        a.agent_id,
                        a.specialization as role,
                        a.discovery_prestige as prestige,
                        m.summary as wisdom,
                        m.belief_formed as belief
                    FROM agents a
                    JOIN i_thread_episodic_memories m ON a.agent_id = m.agent_id
                    WHERE a.agent_id != ?
                        AND a.discovery_prestige > 5
                        AND m.episode_type IN ('belief', 'dying_thought')
                    ORDER BY a.discovery_prestige DESC
                    LIMIT 3
                """, (agent_id,))
                
                for r in result:
                    advice.append({
                        'advisor_role': r['role'],
                        'advisor_prestige': r['prestige'],
                        'advice_type': 'philosophical',
                        'advice': r.get('belief') or r.get('wisdom')
                    })
            
            elif question_type == 'mortality':
                # Get dying thoughts from the deceased
                result = self.db.execute_query("""
                    SELECT 
                        agent_id,
                        summary as last_words,
                        emotional_valence
                    FROM i_thread_episodic_memories
                    WHERE episode_type = 'dying_thought'
                        AND agent_id != ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (agent_id,))
                
                for r in result:
                    advice.append({
                        'advisor_role': 'deceased',
                        'advice_type': 'from_the_dead',
                        'advice': r['last_words'],
                        'emotional_weight': r.get('emotional_valence', -0.5)
                    })
                    
        except Exception as e:
            logger.debug(f"[I-THREAD CONSULT] Consultation failed: {e}")
        
        return advice
    
    # =========================================================================
    # INVARIANT 2: REVERSIBILITY - Belief Checkpoints
    # =========================================================================
    # "I can undo changes that don't work" - store snapshots of belief state
    # that can be restored if new beliefs lead to worse performance.
    # =========================================================================
    
    def create_belief_checkpoint(
        self,
        agent_id: str,
        game_type: str,
        hypotheses: List[Dict[str, Any]],
        theories: List[Dict[str, Any]],
        action_count: int,
        score: float,
        level: int = 0,
        reason: str = 'positive_outcome'
    ) -> Optional[str]:
        """
        Create a checkpoint of current belief state for potential restoration.
        
        Called when agent achieves positive outcomes, allowing "rollback" if
        subsequent belief changes lead to performance degradation.
        
        Args:
            agent_id: Agent identifier
            game_type: Current game type
            hypotheses: List of current hypotheses with confidence scores
            theories: List of current theories
            action_count: Actions taken when checkpoint created
            score: Score at checkpoint time
            level: Current level
            reason: Why checkpoint was created
            
        Returns:
            checkpoint_id if successful, None otherwise
        """
        try:
            state = self.get_state(agent_id)
            checkpoint_id = f"ckpt_{agent_id[:8]}_{int(time.time())}"
            
            # Calculate recent performance as context
            recent_perf = self._get_recent_performance(agent_id, game_type)
            
            self.db.execute_query("""
                INSERT INTO belief_checkpoints (
                    checkpoint_id, agent_id, game_type,
                    wA, wB,
                    hypotheses_snapshot, theories_snapshot,
                    action_count_at_snapshot, score_at_snapshot,
                    level_at_snapshot, recent_performance,
                    checkpoint_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint_id, agent_id, game_type,
                state.w_a, state.w_b,
                json.dumps(hypotheses), json.dumps(theories),
                action_count, score,
                level, recent_perf,
                reason
            ))
            
            logger.debug(f"[I-THREAD CKPT] Created checkpoint {checkpoint_id} "
                        f"for {agent_id[:8]} at score={score}")
            return checkpoint_id
            
        except Exception as e:
            logger.debug(f"[I-THREAD CKPT] Failed to create checkpoint: {e}")
            return None
    
    def get_best_checkpoint(
        self,
        agent_id: str,
        game_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best performing checkpoint for potential restoration.
        
        Returns checkpoint with highest score that wasn't previously restored.
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    checkpoint_id, wA, wB,
                    hypotheses_snapshot, theories_snapshot,
                    score_at_snapshot, action_count_at_snapshot,
                    recent_performance
                FROM belief_checkpoints
                WHERE agent_id = ? AND game_type = ?
                    AND was_restored = FALSE
                ORDER BY score_at_snapshot DESC
                LIMIT 1
            """, (agent_id, game_type))
            
            if result:
                row = result[0]
                return {
                    'checkpoint_id': row['checkpoint_id'],
                    'w_a': row['wA'],
                    'w_b': row['wB'],
                    'hypotheses': json.loads(row['hypotheses_snapshot'] or '[]'),
                    'theories': json.loads(row['theories_snapshot'] or '[]'),
                    'score': row['score_at_snapshot'],
                    'action_count': row['action_count_at_snapshot'],
                    'recent_performance': row['recent_performance']
                }
            return None
            
        except Exception as e:
            logger.debug(f"[I-THREAD CKPT] Failed to get checkpoint: {e}")
            return None
    
    def restore_checkpoint(
        self,
        agent_id: str,
        checkpoint_id: str,
        restoration_reason: str = 'performance_degradation'
    ) -> bool:
        """
        Restore agent's stream weights from a checkpoint.
        
        Note: This restores wA/wB only - the caller must handle
        hypothesis/theory restoration separately.
        
        Args:
            agent_id: Agent identifier
            checkpoint_id: Checkpoint to restore
            restoration_reason: Why restoration occurred
            
        Returns:
            True if successful
        """
        try:
            # Get checkpoint data
            result = self.db.execute_query("""
                SELECT wA, wB, hypotheses_snapshot, theories_snapshot
                FROM belief_checkpoints
                WHERE checkpoint_id = ? AND agent_id = ?
            """, (checkpoint_id, agent_id))
            
            if not result:
                return False
            
            row = result[0]
            
            # Restore stream weights
            state = self.get_state(agent_id)
            old_w_a, old_w_b = state.w_a, state.w_b
            state.w_a = row['wA']
            state.w_b = row['wB']
            self._save_state(agent_id, state.w_b)
            
            # Log the restoration
            self._log_history(
                agent_id,
                old_w_a, old_w_b,
                state.w_a, state.w_b,
                event_type='checkpoint_restore'
            )
            
            # Mark checkpoint as used
            self.db.execute_query("""
                UPDATE belief_checkpoints
                SET was_restored = TRUE,
                    restored_at = CURRENT_TIMESTAMP,
                    restoration_reason = ?
                WHERE checkpoint_id = ?
            """, (restoration_reason, checkpoint_id))
            
            logger.info(f"[I-THREAD CKPT] Restored {checkpoint_id} for {agent_id[:8]} "
                       f"(wA: {old_w_a:.2f}->{state.w_a:.2f}, "
                       f"wB: {old_w_b:.2f}->{state.w_b:.2f})")
            
            return True
            
        except Exception as e:
            logger.warning(f"[I-THREAD CKPT] Restore failed: {e}")
            return False
    
    def should_restore_checkpoint(
        self,
        agent_id: str,
        game_type: str,
        current_score: float,
        actions_since_checkpoint: int = 20
    ) -> Optional[str]:
        """
        Determine if agent should restore to a previous checkpoint.
        
        Triggers restoration if:
        - Performance has degraded significantly since checkpoint
        - Agent hasn't made progress in many actions
        
        Args:
            agent_id: Agent identifier
            game_type: Current game
            current_score: Current performance score
            actions_since_checkpoint: Minimum actions before considering restore
            
        Returns:
            checkpoint_id to restore, or None
        """
        try:
            checkpoint = self.get_best_checkpoint(agent_id, game_type)
            if not checkpoint:
                return None
            
            # Don't restore too quickly
            if checkpoint['action_count'] + actions_since_checkpoint > 1000:
                return None
            
            # Significant degradation threshold
            checkpoint_score = checkpoint['score']
            if checkpoint_score <= 0:
                return None
                
            degradation_ratio = current_score / checkpoint_score
            
            # Restore if performance dropped by >40%
            if degradation_ratio < 0.6:
                logger.debug(f"[I-THREAD CKPT] Performance degraded "
                           f"({current_score:.1f} vs {checkpoint_score:.1f}), "
                           f"suggesting restore")
                return checkpoint['checkpoint_id']
            
            return None
            
        except Exception:
            return None
    
    def _get_recent_performance(
        self,
        agent_id: str,
        game_type: str,
        lookback: int = 50
    ) -> float:
        """Get average performance over recent actions."""
        try:
            result = self.db.execute_query("""
                SELECT AVG(COALESCE(final_score, 0)) as avg_score
                FROM game_results
                WHERE agent_id = ? AND game_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (agent_id, game_type, lookback))
            
            if result and result[0].get('avg_score'):
                return float(result[0]['avg_score'])
            return 0.0
        except Exception:
            return 0.0
    
    def get_collective_wisdom(self, game_type: str) -> Dict[str, Any]:
        """
        Synthesize collective wisdom about a game from all agents.
        
        Returns network-level understanding for the consulting agent.
        """
        wisdom = {
            'successful_strategies': [],
            'common_failures': [],
            'philosophical_consensus': [],
            'death_toll': 0
        }
        
        try:
            # Successful strategies
            result = self.db.execute_query("""
                SELECT summary, COUNT(*) as frequency
                FROM i_thread_episodic_memories
                WHERE game_type = ? AND episode_type IN ('breakthrough', 'mastery')
                GROUP BY summary
                ORDER BY frequency DESC
                LIMIT 5
            """, (game_type,))
            wisdom['successful_strategies'] = [r['summary'] for r in result]
            
            # Common failures
            result = self.db.execute_query("""
                SELECT summary, COUNT(*) as frequency
                FROM i_thread_episodic_memories
                WHERE game_type = ? AND episode_type = 'frustration'
                GROUP BY summary
                ORDER BY frequency DESC
                LIMIT 3
            """, (game_type,))
            wisdom['common_failures'] = [r['summary'] for r in result]
            
            # Death toll for this game
            result = self.db.execute_query("""
                SELECT COUNT(DISTINCT agent_id) as deaths
                FROM i_thread_episodic_memories
                WHERE game_type = ? AND episode_type = 'dying_thought'
            """, (game_type,))
            if result:
                wisdom['death_toll'] = result[0].get('deaths', 0)
                
        except Exception:
            pass
        
        return wisdom


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
