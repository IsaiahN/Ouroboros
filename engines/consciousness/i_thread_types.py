#!/usr/bin/env python3
"""
I-Thread Types - Data Structures for Consciousness System
===========================================================

Extracted from i_thread.py for better organization.

Contains:
- DeathType enum - Classification of agent death types
- DeathPersona - Death-triggered behavioral personas
- Stream types - Proposals, conflicts, synthesis results
- EpisodicMemory - Agent's autobiographical memories
- AgentNarrative - Agent's self-concept
- MortalityState - Death awareness state
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: No pycache

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# DEATH TYPE CLASSIFICATION
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
    NATURAL_AGE = "natural_age"
    PERFORMANCE_CULL = "performance_cull"
    PRESTIGE_DECAY = "prestige_decay"
    VITALITY_STAGNATION = "vitality_stagnation"
    DISGRACE = "disgrace"


# =============================================================================
# DEATH PERSONA CONFIGURATION
# =============================================================================

DEATH_PERSONAS = {
    'pioneer': {
        'persona_name': 'Legacy Hunter',
        'activation_threshold': 0.2,
        'behavioral_shift': 'maximum_novelty',
        'internal_voice': "What novel discovery can I leave behind?",
        'action_bias': {
            'exploration_weight': 1.5,
            'risk_tolerance': 0.95,
            'network_queries': 0.3,
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
            'exploration_weight': 0.3,
            'risk_tolerance': 0.2,
            'network_queries': 0.9,
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
            'exploration_weight': 0.8,
            'risk_tolerance': 0.5,
            'network_queries': 0.7,
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
            'exploration_weight': 1.8,
            'risk_tolerance': 0.99,
            'network_queries': 0.2,
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
    contributions_made: int = 0
    final_reflection: Optional[str] = None

    def activate(self, cull_distance: float) -> None:
        """Activate the death persona."""
        self.is_active = True
        self.activated_at = datetime.now()
        self.cull_distance_at_activation = cull_distance

    def deactivate(self, reflection: str = None) -> None:
        """Deactivate persona."""
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
# CONSTANTS
# =============================================================================

ROLE_DEFAULT_WEIGHTS = {
    'pioneer': (0.7, 0.3),
    'optimizer': (0.3, 0.7),
    'generalist': (0.5, 0.5),
    'exploiter': (0.4, 0.6),
}

DEFAULT_LEARNING_RATE = 0.1
CONFLICT_THRESHOLD = 0.3
HIGH_CONFLICT_THRESHOLD = 0.6


# =============================================================================
# STREAM TYPES
# =============================================================================

@dataclass
class NoveltyConfig:
    """Configuration for novelty-based wA boosting."""
    boost_amount: float = 0.2
    max_wA: float = 0.95
    prediction_accuracy_threshold: float = 0.3
    min_samples: int = 5


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
    conflict_score: float
    stream_a_proposal: Optional[StreamProposal] = None
    stream_b_proposal: Optional[StreamProposal] = None
    consciousness_intensity: str = 'automatic'


@dataclass
class SynthesisResult:
    """Result of I-Thread synthesis."""
    chosen_action: str
    confidence: float
    chosen_source: str
    surprise_score: float
    w_a_used: float
    w_b_used: float
    deliberation_required: bool


# =============================================================================
# EPISODIC MEMORY
# =============================================================================

@dataclass
class EpisodicMemory:
    """
    A compressed memory of a significant game experience.

    Not every action, but meaningful episodes that shaped the agent:
    - Breakthroughs, frustrations, surprises, validations

    These form the agent's autobiographical narrative.
    """
    memory_id: str
    agent_id: str
    game_type: str
    level_number: int

    episode_type: str
    summary: str

    emotional_valence: float
    significance: float

    belief_formed: Optional[str] = None
    rule_discovered: Optional[str] = None

    stream_source: str = 'stream_a'
    w_a_at_time: float = 0.5
    w_b_at_time: float = 0.5

    created_at: Optional[datetime] = None
    times_recalled: int = 0
    last_recalled: Optional[datetime] = None


@dataclass
class AgentNarrative:
    """
    The agent's autobiographical self - who they are based on what they remember.
    """
    agent_id: str

    personality_label: str
    dominant_emotion: str

    total_games_played: int = 0
    total_breakthroughs: int = 0
    total_frustrations: int = 0
    games_won: int = 0

    salient_memories: List['EpisodicMemory'] = field(default_factory=list)
    core_beliefs: List[str] = field(default_factory=list)

    w_a: float = 0.5
    w_b: float = 0.5

    narrative_summary: str = ""


# =============================================================================
# DEATH PHILOSOPHY & TENSION CONFIGURATION
# =============================================================================

DEATH_PHILOSOPHIES = {
    'pioneer': {
        'fear_type': 'novelty_death',
        'death_meaning': "I may die before finding what lies beyond the frontier",
        'urgency_multiplier': 1.3,
        'risk_tolerance': 0.7,
        'legacy_focus': 'discoveries',
        'dying_thought': "Did I find something new? Did the network learn from me?"
    },
    'optimizer': {
        'fear_type': 'inefficiency_death',
        'death_meaning': "I may die before achieving optimal efficiency",
        'urgency_multiplier': 0.9,
        'risk_tolerance': 0.3,
        'legacy_focus': 'refinements',
        'dying_thought': "Did I leave the solutions better than I found them?"
    },
    'generalist': {
        'fear_type': 'translation_death',
        'death_meaning': "I may die before connecting what I understand",
        'urgency_multiplier': 1.0,
        'risk_tolerance': 0.5,
        'legacy_focus': 'connections',
        'dying_thought': "Did I help the network understand itself?"
    },
    'exploiter': {
        'fear_type': 'edge_death',
        'death_meaning': "I may die before finding what others missed",
        'urgency_multiplier': 1.5,
        'risk_tolerance': 0.9,
        'legacy_focus': 'edge_cases',
        'dying_thought': "Did I find the flaw? Did I break the paradigm?"
    }
}

ROLE_TENSION_PROFILES = {
    'pioneer': {
        'optimal_tension': 0.6,
        'tension_tolerance': 0.3,
        'panic_threshold': 0.9,
        'complacency_threshold': 0.2,
    },
    'optimizer': {
        'optimal_tension': 0.4,
        'tension_tolerance': 0.15,
        'panic_threshold': 0.7,
        'complacency_threshold': 0.15,
    },
    'generalist': {
        'optimal_tension': 0.5,
        'tension_tolerance': 0.2,
        'panic_threshold': 0.8,
        'complacency_threshold': 0.2,
    },
    'exploiter': {
        'optimal_tension': 0.7,
        'tension_tolerance': 0.35,
        'panic_threshold': 0.95,
        'complacency_threshold': 0.3,
    }
}

THINKING_BUDGET_CONFIG = {
    'base_budget': 10,
    'prestige_multiplier': 2,
    'performance_bonus': 5,
    'max_budget': 100,
    'min_budget': 5,
}


# =============================================================================
# MORTALITY STATE
# =============================================================================

@dataclass
class MortalityState:
    """
    An agent's awareness of its own mortality.

    Mortality creates the existential pressure that makes action meaningful.
    """
    agent_id: str
    role: str = 'generalist'

    # Life state
    vitality: float = 1.0
    vitality_decay_rate: float = 0.01
    vitality_restore_rate: float = 0.05

    # Proximity to death
    cull_distance: float = 1.0
    fitness_percentile: float = 0.5
    generations_until_risk: int = 5

    # Legacy awareness
    legacy_score: float = 0.0
    discoveries_made: int = 0
    sequences_contributed: int = 0
    hypotheses_validated: int = 0
    agents_taught: int = 0

    # Death philosophy
    fear_type: str = 'translation_death'
    death_meaning: str = "I may die before contributing"
    urgency_multiplier: float = 1.0
    risk_tolerance: float = 0.5

    # Final thoughts
    last_words: Optional[str] = None
    last_reflection: Optional[str] = None
    reflection_count: int = 0

    # Tension state
    current_tension: float = 0.5
    optimal_tension: float = 0.5
    tension_deviation: float = 0.0

    # Thinking budget
    thinking_budget: int = 10
    thoughts_used: int = 0

    # Personal beliefs
    purpose_statement: Optional[str] = None
    core_beliefs: List[str] = field(default_factory=list)
    personal_notes: List[str] = field(default_factory=list)

    # Social relevance
    times_packages_queried_recent: int = 0
    social_relevance_score: float = 1.0
    prestige_decay_rate: float = 0.05
    generations_since_contribution: int = 0

    # Death type tracking
    predicted_death_type: Optional[str] = None
    learning_rate_effective: float = 0.1

    # Death persona
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

        if role in ROLE_TENSION_PROFILES:
            profile = ROLE_TENSION_PROFILES[role]
            self.optimal_tension = profile['optimal_tension']

    def compute_tension_state(self, pressure: float) -> Dict[str, float]:
        """Compute current tension state and performance impact."""
        profile = ROLE_TENSION_PROFILES.get(self.role, ROLE_TENSION_PROFILES['generalist'])

        self.current_tension = min(1.0, pressure * 0.8 + 0.1)
        self.tension_deviation = abs(self.current_tension - profile['optimal_tension'])

        tolerance = profile['tension_tolerance']
        if self.tension_deviation <= tolerance:
            performance_mult = 1.0
        else:
            excess = self.tension_deviation - tolerance
            performance_mult = max(0.5, 1.0 - excess * 2)

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

        Args:
            prestige: Agent's discovery prestige
            performance_percentile: Performance ranking (0-1)

        Returns:
            Number of reflection tokens available
        """
        config = THINKING_BUDGET_CONFIG

        budget = config['base_budget']
        budget += int(prestige * config['prestige_multiplier'])

        if performance_percentile > 0.5:
            budget += int((performance_percentile - 0.5) * 2 * config['performance_bonus'])

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
        if len(self.personal_notes) > 20:
            self.personal_notes = self.personal_notes[-20:]

    def add_belief(self, belief: str) -> None:
        """Add or update a core belief about existence."""
        if belief not in self.core_beliefs:
            self.core_beliefs.append(belief)
            if len(self.core_beliefs) > 10:
                self.core_beliefs = self.core_beliefs[-10:]

    def set_purpose(self, purpose: str) -> None:
        """Define the agent's raison d'etre."""
        self.purpose_statement = purpose

    def compute_existential_pressure(self) -> float:
        """
        Calculate the existential pressure from mortality awareness.

        Returns:
            Pressure score 0.0 (comfortable) to 2.0 (existential crisis)
        """
        vitality_pressure = 1.0 - self.vitality
        cull_pressure = 1.0 - self.cull_distance

        legacy_comfort = min(1.0, self.legacy_score / 10.0)
        legacy_pressure = 1.0 - legacy_comfort

        base_pressure = (vitality_pressure * 0.4 +
                        cull_pressure * 0.4 +
                        legacy_pressure * 0.2)

        return base_pressure * self.urgency_multiplier

    def drain_vitality(self, amount: float = None) -> float:
        """Drain vitality from failure/inaction. Returns new vitality level."""
        drain = amount if amount is not None else self.vitality_decay_rate
        self.vitality = max(0.0, self.vitality - drain)
        return self.vitality

    def restore_vitality(self, amount: float = None) -> float:
        """Restore vitality from success. Returns new vitality level."""
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

    def predict_death_type(self) -> 'DeathType':
        """
        Predict how this agent will likely die based on current state.

        Returns:
            Predicted DeathType
        """
        if self.learning_rate_effective < 0.01:
            self.predicted_death_type = DeathType.VITALITY_STAGNATION.value
            return DeathType.VITALITY_STAGNATION

        if self.fitness_percentile < 0.1 and self.cull_distance < 0.3:
            self.predicted_death_type = DeathType.PERFORMANCE_CULL.value
            return DeathType.PERFORMANCE_CULL

        if self.social_relevance_score < 0.2 and self.times_packages_queried_recent == 0:
            self.predicted_death_type = DeathType.PRESTIGE_DECAY.value
            return DeathType.PRESTIGE_DECAY

        if self.legacy_score < 1.0 and self.discoveries_made == 0:
            if self.cull_distance < 0.3:
                self.predicted_death_type = DeathType.DISGRACE.value
                return DeathType.DISGRACE

        self.predicted_death_type = DeathType.NATURAL_AGE.value
        return DeathType.NATURAL_AGE

    def update_social_relevance(self, times_queried: int, _generations_active: int) -> None:
        """Update social relevance score based on how often packages are queried."""
        self.times_packages_queried_recent = times_queried

        if times_queried == 0:
            self.social_relevance_score = max(
                0.0,
                self.social_relevance_score - self.prestige_decay_rate
            )
            self.generations_since_contribution += 1
        else:
            boost = min(0.2, times_queried * 0.05)
            self.social_relevance_score = min(1.0, self.social_relevance_score + boost)
            self.generations_since_contribution = 0

    def update_learning_rate(self, new_learning_rate: float) -> None:
        """Update effective learning rate (for vitality death prediction)."""
        self.learning_rate_effective = new_learning_rate

    def check_death_persona_activation(self, logger=None) -> Optional['DeathPersona']:
        """
        Check if death persona should activate based on cull_distance.

        Returns:
            DeathPersona if activated, None if not
        """
        activation_threshold = DEATH_PERSONAS.get(
            self.role, DEATH_PERSONAS['generalist']
        )['activation_threshold']

        if self.cull_distance < activation_threshold and not self.death_persona_active:
            self.death_persona = DeathPersona.from_role(self.role)
            self.death_persona.activate(self.cull_distance)
            self.death_persona_active = True

            if logger:
                logger.info(
                    f"[MORTALITY] Death persona '{self.death_persona.persona_name}' "
                    f"activated for {self.agent_id} (cull_distance={self.cull_distance:.2f})"
                )

            return self.death_persona

        elif self.cull_distance >= activation_threshold + 0.1 and self.death_persona_active:
            if self.death_persona:
                self.death_persona.deactivate(
                    f"Survived near-death, cull_distance improved to {self.cull_distance:.2f}"
                )
            self.death_persona_active = False

            if logger:
                logger.info(
                    f"[MORTALITY] Death persona deactivated for {self.agent_id} "
                    f"(survived, cull_distance={self.cull_distance:.2f})"
                )

        return self.death_persona if self.death_persona_active else None

    def get_death_persona_bias(self) -> Optional[Dict[str, float]]:
        """Get action biases if death persona is active."""
        if self.death_persona_active and self.death_persona:
            self.death_persona.record_action()
            return self.death_persona.get_action_bias()
        return None

    def record_death_persona_contribution(self) -> None:
        """Record that the death persona contributed something meaningful."""
        if self.death_persona_active and self.death_persona:
            self.death_persona.record_contribution()

    def get_death_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's mortality state for logging/analysis."""
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
# GUT INSTINCT & DELIBERATION TYPES
# =============================================================================

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

    # TRM-INSPIRED ITERATIVE REFINEMENT (Jan 18 - Less is More paper)
    refinement_passes: int = 0  # How many refinement passes were run
    refinement_confidence: float = 0.0  # Margin between #1 and #2 action
    consensus_actions: List[str] = field(default_factory=list)  # Actions supported by 2+ sources
    convergence_achieved: bool = False  # Whether early convergence happened

    # COGNITIVE EXPERIENCE FIELDS (Agent-Centric Integration Plan)
    predictions_felt: List[Dict[str, Any]] = field(default_factory=list)  # [{action, expected_outcome, confidence, feeling}]
    expectation_match: Optional[bool] = None  # Did reality match expectation?
    surprise_felt: float = 0.0  # 0.0 = expected, 1.0 = completely surprised

    # Phase 2: Resonance as Recognition
    resonance_felt: Optional[Dict[str, Any]] = None  # {pattern_hash, agents_who_know, feeling}
    deja_vu_strength: float = 0.0  # How strongly "I know this" felt

    # Phase 3: Abstraction as Understanding
    insight_felt: Optional[Dict[str, Any]] = None  # {template, invariant, feeling}
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


@dataclass
class IThreadState:
    """
    The core I-Thread state that persists for an agent.

    This is what makes an agent "who they are" - their learned trust
    patterns between self-experience and network wisdom.
    """
    agent_id: str

    # Stream weights (the core of personality)
    w_a: float = 0.5  # Self-trust (0-1)
    w_b: float = 0.5  # Network-trust (0-1)

    # Learning parameters
    learning_rate: float = 0.1

    # Historical stats
    conflicts_resolved: int = 0
    stream_a_wins: int = 0
    stream_b_wins: int = 0
    synthesis_count: int = 0

    # Personality label (computed from weights)
    personality_label: str = 'balanced'

    # Mortality awareness
    mortality_state: Optional['MortalityState'] = None


@dataclass
class MultiConflictResult:
    """Result when multiple streams have proposals."""
    proposals: List[StreamProposal] = field(default_factory=list)
    has_conflict: bool = False
    max_conflict_score: float = 0.0
    consciousness_intensity: str = 'automatic'


__all__ = [
    # Enums
    'DeathType',
    # Death system
    'DeathPersona', 'DEATH_PERSONAS', 'DEATH_PHILOSOPHIES', 'ROLE_TENSION_PROFILES',
    'THINKING_BUDGET_CONFIG',
    # Constants
    'ROLE_DEFAULT_WEIGHTS', 'DEFAULT_LEARNING_RATE',
    'CONFLICT_THRESHOLD', 'HIGH_CONFLICT_THRESHOLD',
    # Stream types
    'NoveltyConfig', 'StreamProposal', 'ConflictResult', 'SynthesisResult',
    # Memory types
    'EpisodicMemory', 'AgentNarrative',
    # Mortality
    'MortalityState',
    # Reasoning types
    'GutInstinctResult', 'DeliberationResult', 'ReasoningLog',
    # Core state
    'IThreadState', 'MultiConflictResult',
]
