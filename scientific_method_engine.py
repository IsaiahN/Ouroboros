import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Scientific Method Engine - Autonomous Theory Formation & Testing
================================================================

This is the CORE component that makes agents actually intelligent.
It implements the scientific method as an action loop:

1. OBSERVE: Notice anomalies, patterns, or unexplained events
2. HYPOTHESIZE: Form a testable theory about WHY
3. PREDICT: What SHOULD happen if theory is true?
4. EXPERIMENT: Design and execute a test
5. ANALYZE: Did prediction match reality?
6. UPDATE: Strengthen or refute the theory
7. GENERALIZE: Abstract to broader principles

The engine runs CONTINUOUSLY during gameplay, not just when called.
It maintains a "hypothesis priority queue" and actively allocates
exploration budget to testing theories.

Key Insight: Agents should spend ~20-30% of their actions on
DELIBERATE EXPERIMENTATION, not just goal-seeking.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TheoryStatus(Enum):
    """Status of a theory in the scientific method pipeline."""
    PROPOSED = "proposed"           # Just formed, not tested
    TESTING = "testing"             # Currently being tested
    SUPPORTED = "supported"         # Evidence supports it (confidence > 0.7)
    REFUTED = "refuted"             # Evidence contradicts it (confidence < 0.3)
    GENERALIZED = "generalized"     # Abstracted to broader principle


class TheoryType(Enum):
    """Categories of theories agents can form."""
    OBJECT_IDENTITY = "object_identity"       # "I am the blue dot"
    OBJECT_DANGER = "object_danger"           # "Red things kill me"
    ACTION_EFFECT = "action_effect"           # "ACTION2 moves me down"
    SPATIAL_RULE = "spatial_rule"             # "Touching the boundary kills me"
    GOAL_HYPOTHESIS = "goal_hypothesis"       # "I need to reach the green area"
    SEQUENCE_PATTERN = "sequence_pattern"     # "UP, UP, RIGHT works on this level"
    COUNTER_BEHAVIOR = "counter_behavior"     # "The number decreases when I move"
    TRIGGER_MECHANISM = "trigger_mechanism"   # "Clicking the button opens the door"


@dataclass
class Theory:
    """A single testable theory."""
    theory_id: str
    theory_type: TheoryType
    game_type: str
    level_number: int
    
    # The theory itself
    description: str                          # Human-readable description
    formal_statement: Dict[str, Any]          # Machine-readable structure
    
    # Predictions - what SHOULD happen if theory is true
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Evidence tracking
    supporting_observations: List[str] = field(default_factory=list)
    contradicting_observations: List[str] = field(default_factory=list)
    
    # Confidence and status
    confidence: float = 0.5
    status: TheoryStatus = TheoryStatus.PROPOSED
    tests_conducted: int = 0
    tests_successful: int = 0
    
    # Generalization tracking
    generalized_from: Optional[str] = None    # Parent theory if this is a generalization
    child_theories: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_tested_at: Optional[str] = None
    discovered_by_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'theory_id': self.theory_id,
            'theory_type': self.theory_type.value,
            'game_type': self.game_type,
            'level_number': self.level_number,
            'description': self.description,
            'formal_statement': self.formal_statement,
            'predictions': self.predictions,
            'supporting_observations': self.supporting_observations,
            'contradicting_observations': self.contradicting_observations,
            'confidence': self.confidence,
            'status': self.status.value,
            'tests_conducted': self.tests_conducted,
            'tests_successful': self.tests_successful,
            'generalized_from': self.generalized_from,
            'child_theories': self.child_theories,
            'created_at': self.created_at,
            'last_tested_at': self.last_tested_at,
            'discovered_by_agent': self.discovered_by_agent
        }


@dataclass 
class Experiment:
    """A designed experiment to test a theory."""
    experiment_id: str
    theory_id: str
    
    # What we're testing
    hypothesis: str                           # "If I move DOWN from here, I should die"
    prediction: Dict[str, Any]                # {action: 'ACTION2', expected_outcome: 'GAME_OVER'}
    
    # Experiment design
    preconditions: Dict[str, Any]             # State that must be true before test
    test_action: str                          # Action to take
    expected_result: Dict[str, Any]           # What we expect to happen
    
    # Results
    actual_result: Optional[Dict[str, Any]] = None
    prediction_matched: Optional[bool] = None
    executed_at: Optional[str] = None


class ScientificMethodEngine:
    """
    The autonomous scientific reasoning system.
    
    This engine runs continuously during gameplay, maintaining a queue
    of theories to test and allocating exploration budget to experiments.
    """
    
    def __init__(self, db):
        """Initialize the scientific method engine."""
        self.db = db
        self._ensure_tables()
        
        # Active theories being tracked (per game session)
        self._active_theories: Dict[str, Theory] = {}
        
        # Pending experiments
        self._experiment_queue: List[Experiment] = []
        
        # Current experiment being conducted
        self._current_experiment: Optional[Experiment] = None
        
        # Observation buffer for pattern detection
        self._observation_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 50
        
        # Experimentation budget (fraction of actions for deliberate tests)
        self._experiment_budget_ratio = 0.20  # 20% of actions for experiments
        self._actions_since_experiment = 0
    
    def _ensure_tables(self):
        """Create tables for theory storage."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS agent_theories (
                    theory_id TEXT PRIMARY KEY,
                    theory_type TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- Theory content
                    description TEXT NOT NULL,
                    formal_statement TEXT NOT NULL,
                    predictions TEXT,
                    
                    -- Evidence
                    supporting_observations TEXT,
                    contradicting_observations TEXT,
                    
                    -- Confidence and status
                    confidence REAL DEFAULT 0.5,
                    status TEXT DEFAULT 'proposed',
                    tests_conducted INTEGER DEFAULT 0,
                    tests_successful INTEGER DEFAULT 0,
                    
                    -- Generalization
                    generalized_from TEXT,
                    child_theories TEXT,
                    
                    -- Network sharing
                    shared_to_network INTEGER DEFAULT 0,
                    network_validations INTEGER DEFAULT 0,
                    
                    -- Metadata
                    created_at TEXT,
                    last_tested_at TEXT,
                    discovered_by_agent TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_agent_theories_lookup
                ON agent_theories (game_type, level_number, status, is_active)
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS theory_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    theory_id TEXT NOT NULL,
                    
                    hypothesis TEXT,
                    prediction TEXT,
                    preconditions TEXT,
                    test_action TEXT,
                    expected_result TEXT,
                    
                    actual_result TEXT,
                    prediction_matched INTEGER,
                    
                    executed_at TEXT,
                    executed_by_agent TEXT,
                    
                    FOREIGN KEY (theory_id) REFERENCES agent_theories(theory_id)
                )
            """)
            
        except Exception as e:
            logger.debug(f"Theory tables setup: {e}")
    
    # =========================================================================
    # PHASE 1: OBSERVATION - Notice patterns and anomalies
    # =========================================================================
    
    def record_observation(self, observation: Dict[str, Any]):
        """
        Record an observation for pattern detection.
        
        Called after every action to build up evidence.
        
        Args:
            observation: Dict with:
                - action: What action was taken
                - frame_before: State before action
                - frame_after: State after action
                - score_before: Score before
                - score_after: Score after
                - game_state: WIN/GAME_OVER/NOT_FINISHED
                - controlled_objects: What agent controls
                - timestamp: When this happened
        """
        self._observation_buffer.append(observation)
        
        # Keep buffer bounded
        if len(self._observation_buffer) > self._max_buffer_size:
            self._observation_buffer.pop(0)
        
        # Check for automatic theory triggers
        self._check_for_theory_triggers(observation)
    
    def _check_for_theory_triggers(self, observation: Dict[str, Any]):
        """
        Check if this observation should trigger theory formation.
        
        Triggers include:
        - GAME_OVER (why did I die?)
        - Score increase (what caused progress?)
        - Level completion (what was the goal?)
        - Unexpected state change (what happened?)
        """
        game_state = observation.get('game_state', '')
        score_change = observation.get('score_after', 0) - observation.get('score_before', 0)
        
        # GAME_OVER trigger - form death theory
        if game_state == 'GAME_OVER':
            self._form_death_theory(observation)
        
        # Score increase - form progress theory
        elif score_change > 0:
            self._form_progress_theory(observation)
        
        # Level change - form goal theory
        elif observation.get('level_changed'):
            self._form_goal_theory(observation)
    
    def _form_death_theory(self, observation: Dict[str, Any]):
        """Form a theory about why the agent died."""
        action = observation.get('action')
        frame = observation.get('frame_before', [])
        controlled = observation.get('controlled_objects', [])
        game_type = observation.get('game_type', 'unknown')
        level = observation.get('level_number', 1)
        
        # Get adjacent objects to player
        adjacent_colors = self._get_adjacent_colors(frame, controlled)
        
        if adjacent_colors:
            for color in adjacent_colors:
                theory = Theory(
                    theory_id=f"death_{game_type}_{level}_{color}_{uuid.uuid4().hex[:8]}",
                    theory_type=TheoryType.OBJECT_DANGER,
                    game_type=game_type,
                    level_number=level,
                    description=f"Color {color} is dangerous - touching it causes GAME_OVER",
                    formal_statement={
                        'condition': 'contact',
                        'object_color': color,
                        'consequence': 'GAME_OVER'
                    },
                    predictions=[{
                        'if': f'move_toward_color_{color}',
                        'then': 'GAME_OVER',
                        'confidence': 0.7
                    }],
                    supporting_observations=[f"Died after {action} while adjacent to color {color}"],
                    confidence=0.6,
                    discovered_by_agent=observation.get('agent_id')
                )
                
                self._add_theory(theory)
                logger.info(f"[SCIENCE] Formed death theory: {theory.description}")
        
        # Also form action-location theory
        if action and controlled:
            theory = Theory(
                theory_id=f"death_action_{game_type}_{level}_{uuid.uuid4().hex[:8]}",
                theory_type=TheoryType.SPATIAL_RULE,
                game_type=game_type,
                level_number=level,
                description=f"{action} at current position leads to GAME_OVER",
                formal_statement={
                    'action': action,
                    'position': controlled[0] if controlled else None,
                    'consequence': 'GAME_OVER'
                },
                predictions=[{
                    'if': f'execute_{action}_at_similar_position',
                    'then': 'GAME_OVER',
                    'confidence': 0.6
                }],
                supporting_observations=[f"Died after {action} at position {controlled[0] if controlled else 'unknown'}"],
                confidence=0.5,
                discovered_by_agent=observation.get('agent_id')
            )
            
            self._add_theory(theory)
    
    def _form_progress_theory(self, observation: Dict[str, Any]):
        """Form a theory about what caused progress."""
        action = observation.get('action')
        frame_before = observation.get('frame_before', [])
        frame_after = observation.get('frame_after', [])
        game_type = observation.get('game_type', 'unknown')
        level = observation.get('level_number', 1)
        
        # Analyze what changed
        changes = self._analyze_frame_changes(frame_before, frame_after)
        
        theory = Theory(
            theory_id=f"progress_{game_type}_{level}_{uuid.uuid4().hex[:8]}",
            theory_type=TheoryType.ACTION_EFFECT,
            game_type=game_type,
            level_number=level,
            description=f"{action} caused score increase - may be goal-directed",
            formal_statement={
                'action': action,
                'result': 'score_increase',
                'frame_changes': changes[:5]  # Top 5 changes
            },
            predictions=[{
                'if': f'repeat_{action}_in_similar_state',
                'then': 'score_increase_possible',
                'confidence': 0.5
            }],
            supporting_observations=[f"Score increased after {action}"],
            confidence=0.5,
            discovered_by_agent=observation.get('agent_id')
        )
        
        self._add_theory(theory)
        logger.info(f"[SCIENCE] Formed progress theory: {theory.description}")
    
    def _form_goal_theory(self, observation: Dict[str, Any]):
        """Form a theory about what the goal is."""
        frame_before = observation.get('frame_before', [])
        frame_after = observation.get('frame_after', [])
        game_type = observation.get('game_type', 'unknown')
        level = observation.get('level_number', 1)
        
        # What disappeared when level completed?
        disappeared_colors = self._find_disappeared_colors(frame_before, frame_after)
        
        if disappeared_colors:
            theory = Theory(
                theory_id=f"goal_{game_type}_{level}_{uuid.uuid4().hex[:8]}",
                theory_type=TheoryType.GOAL_HYPOTHESIS,
                game_type=game_type,
                level_number=level,
                description=f"Goal may be to eliminate/reach colors: {disappeared_colors}",
                formal_statement={
                    'goal_type': 'eliminate_or_reach',
                    'target_colors': list(disappeared_colors)
                },
                predictions=[{
                    'if': 'move_toward_target_colors',
                    'then': 'progress_likely',
                    'confidence': 0.6
                }],
                supporting_observations=[f"Level completed when colors {disappeared_colors} changed/disappeared"],
                confidence=0.6,
                discovered_by_agent=observation.get('agent_id')
            )
            
            self._add_theory(theory)
            logger.info(f"[SCIENCE] Formed goal theory: {theory.description}")
    
    # =========================================================================
    # PHASE 2: HYPOTHESIS GENERATION - Form testable theories
    # =========================================================================
    
    def generate_theory_from_observations(self, 
                                           game_type: str,
                                           level_number: int,
                                           agent_id: str) -> Optional[Theory]:
        """
        Analyze observation buffer and generate a new theory.
        
        This is called periodically to form theories from accumulated evidence.
        """
        if len(self._observation_buffer) < 5:
            return None  # Need minimum observations
        
        # Look for patterns in observations
        patterns = self._find_observation_patterns()
        
        if not patterns:
            return None
        
        # Pick the strongest pattern
        best_pattern = max(patterns, key=lambda p: p.get('strength', 0))
        
        # Convert pattern to theory
        theory = self._pattern_to_theory(best_pattern, game_type, level_number, agent_id)
        
        if theory:
            self._add_theory(theory)
            logger.info(f"[SCIENCE] Generated theory from patterns: {theory.description}")
        
        return theory
    
    def _find_observation_patterns(self) -> List[Dict[str, Any]]:
        """Find patterns in the observation buffer."""
        patterns = []
        
        # Pattern 1: Action-effect consistency
        action_effects = {}
        for obs in self._observation_buffer:
            action = obs.get('action')
            effect = self._classify_effect(obs)
            
            if action:
                if action not in action_effects:
                    action_effects[action] = []
                action_effects[action].append(effect)
        
        for action, effects in action_effects.items():
            if len(effects) >= 3:
                # Count effect frequencies
                effect_counts = {}
                for e in effects:
                    effect_counts[e] = effect_counts.get(e, 0) + 1
                
                dominant_effect = max(effect_counts.items(), key=lambda x: x[1])
                if dominant_effect[1] >= len(effects) * 0.6:  # 60% consistency
                    patterns.append({
                        'type': 'action_effect',
                        'action': action,
                        'effect': dominant_effect[0],
                        'consistency': dominant_effect[1] / len(effects),
                        'strength': dominant_effect[1]
                    })
        
        # Pattern 2: Object-color movement correlation
        # TODO: Implement color-movement correlation detection
        
        # Pattern 3: Spatial patterns (certain areas always cause X)
        # TODO: Implement spatial pattern detection
        
        return patterns
    
    def _classify_effect(self, observation: Dict[str, Any]) -> str:
        """Classify the effect of an observation."""
        score_change = observation.get('score_after', 0) - observation.get('score_before', 0)
        game_state = observation.get('game_state', '')
        
        if game_state == 'GAME_OVER':
            return 'death'
        elif game_state == 'WIN':
            return 'win'
        elif score_change > 0:
            return 'progress'
        elif observation.get('frame_changed'):
            return 'state_change'
        else:
            return 'no_effect'
    
    def _pattern_to_theory(self, pattern: Dict[str, Any], 
                           game_type: str, level_number: int, 
                           agent_id: str) -> Optional[Theory]:
        """Convert a detected pattern into a formal theory."""
        pattern_type = pattern.get('type')
        
        if pattern_type == 'action_effect':
            return Theory(
                theory_id=f"pattern_{game_type}_{level_number}_{uuid.uuid4().hex[:8]}",
                theory_type=TheoryType.ACTION_EFFECT,
                game_type=game_type,
                level_number=level_number,
                description=f"{pattern['action']} consistently causes {pattern['effect']}",
                formal_statement={
                    'action': pattern['action'],
                    'effect': pattern['effect'],
                    'consistency': pattern['consistency']
                },
                predictions=[{
                    'if': f"execute_{pattern['action']}",
                    'then': pattern['effect'],
                    'confidence': pattern['consistency']
                }],
                confidence=pattern['consistency'],
                discovered_by_agent=agent_id
            )
        
        return None
    
    # =========================================================================
    # PHASE 3: EXPERIMENT DESIGN - Create testable predictions
    # =========================================================================
    
    def design_experiment(self, theory: Theory) -> Optional[Experiment]:
        """
        Design an experiment to test a theory.
        
        Returns an Experiment that can be executed during gameplay.
        """
        theory_type = theory.theory_type
        
        if theory_type == TheoryType.OBJECT_DANGER:
            return self._design_danger_test(theory)
        elif theory_type == TheoryType.ACTION_EFFECT:
            return self._design_effect_test(theory)
        elif theory_type == TheoryType.GOAL_HYPOTHESIS:
            return self._design_goal_test(theory)
        elif theory_type == TheoryType.SPATIAL_RULE:
            return self._design_spatial_test(theory)
        
        return None
    
    def _design_danger_test(self, theory: Theory) -> Experiment:
        """Design a test for a danger theory (e.g., 'red kills me')."""
        target_color = theory.formal_statement.get('object_color')
        
        return Experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            theory_id=theory.theory_id,
            hypothesis=f"Moving toward color {target_color} will cause GAME_OVER",
            prediction={'expected_outcome': 'GAME_OVER', 'target': f'color_{target_color}'},
            preconditions={'adjacent_to_color': target_color},
            test_action='MOVE_TOWARD_TARGET',  # Placeholder - resolved at execution
            expected_result={'game_state': 'GAME_OVER'}
        )
    
    def _design_effect_test(self, theory: Theory) -> Experiment:
        """Design a test for an action-effect theory."""
        action = theory.formal_statement.get('action') or 'ACTION1'
        # Try 'effect' first, then 'result', then 'consequence' for backwards compatibility
        expected_effect = (
            theory.formal_statement.get('effect') or 
            theory.formal_statement.get('result') or 
            theory.formal_statement.get('consequence') or
            'unknown_effect'
        )
        
        return Experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            theory_id=theory.theory_id,
            hypothesis=f"Executing {action} will cause {expected_effect}",
            prediction={'expected_outcome': expected_effect},
            preconditions={},  # No special preconditions
            test_action=action,
            expected_result={'effect': expected_effect}
        )
    
    def _design_goal_test(self, theory: Theory) -> Experiment:
        """Design a test for a goal hypothesis."""
        target_colors = theory.formal_statement.get('target_colors', [])
        
        return Experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            theory_id=theory.theory_id,
            hypothesis=f"Moving toward {target_colors} will cause progress",
            prediction={'expected_outcome': 'progress'},
            preconditions={'can_see_target_colors': target_colors},
            test_action='MOVE_TOWARD_TARGET',
            expected_result={'score_increase': True}
        )
    
    def _design_spatial_test(self, theory: Theory) -> Experiment:
        """Design a test for a spatial rule."""
        action = theory.formal_statement.get('action') or 'ACTION1'
        expected = theory.formal_statement.get('consequence')
        
        return Experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            theory_id=theory.theory_id,
            hypothesis=f"Executing {action} at similar position will cause {expected}",
            prediction={'expected_outcome': expected},
            preconditions={'at_similar_position': True},
            test_action=action,
            expected_result={'outcome': expected}
        )
    
    # =========================================================================
    # PHASE 4: EXPERIMENT EXECUTION - Run tests during gameplay
    # =========================================================================
    
    def should_experiment_now(self, action_count: int) -> bool:
        """
        Determine if we should run an experiment on this action.
        
        Balances goal-seeking with deliberate experimentation.
        """
        self._actions_since_experiment += 1
        
        # Check budget
        experiment_interval = int(1 / self._experiment_budget_ratio)  # Every 5 actions at 20%
        
        if self._actions_since_experiment >= experiment_interval:
            if self._experiment_queue or self._get_pending_theories():
                return True
        
        return False
    
    def get_experiment_action(self, 
                               current_state: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        Get an experimental action to test a theory.
        
        Returns:
            Tuple of (action, reasoning) if experiment should be run, None otherwise
        """
        # Check if we have a current experiment
        if self._current_experiment:
            # Check preconditions
            if self._check_preconditions(self._current_experiment, current_state):
                action = self._resolve_action(self._current_experiment, current_state)
                reasoning = f"EXPERIMENT: Testing theory - {self._current_experiment.hypothesis}"
                return (action, reasoning)
        
        # Get next experiment from queue
        if self._experiment_queue:
            self._current_experiment = self._experiment_queue.pop(0)
            self._actions_since_experiment = 0
            
            action = self._resolve_action(self._current_experiment, current_state)
            reasoning = f"EXPERIMENT: Testing theory - {self._current_experiment.hypothesis}"
            return (action, reasoning)
        
        # Generate experiment from pending theories
        pending = self._get_pending_theories()
        if pending:
            theory = pending[0]
            experiment = self.design_experiment(theory)
            if experiment:
                self._current_experiment = experiment
                self._actions_since_experiment = 0
                
                action = self._resolve_action(experiment, current_state)
                reasoning = f"EXPERIMENT: Testing theory - {experiment.hypothesis}"
                return (action, reasoning)
        
        return None
    
    def _resolve_action(self, experiment: Experiment, 
                        current_state: Dict[str, Any]) -> str:
        """Resolve a placeholder action to a concrete ACTION1-7."""
        test_action = experiment.test_action
        
        if test_action.startswith('ACTION'):
            return test_action
        
        if test_action == 'MOVE_TOWARD_TARGET':
            # Find direction toward target
            # TODO: Implement path-finding toward target
            return 'ACTION1'  # Default to UP for now
        
        return 'ACTION1'  # Default fallback
    
    def _check_preconditions(self, experiment: Experiment, 
                             current_state: Dict[str, Any]) -> bool:
        """Check if experiment preconditions are met."""
        # For now, always return True - refine later
        return True
    
    # =========================================================================
    # PHASE 5: RESULT ANALYSIS - Compare prediction to reality
    # =========================================================================
    
    def record_experiment_result(self, 
                                  actual_outcome: Dict[str, Any],
                                  agent_id: str):
        """
        Record the result of an experiment and update the theory.
        
        Called after an experimental action is executed.
        """
        if not self._current_experiment:
            return
        
        experiment = self._current_experiment
        experiment.actual_result = actual_outcome
        experiment.executed_at = datetime.now().isoformat()
        
        # Compare prediction to actual
        prediction_matched = self._compare_prediction_to_result(
            experiment.expected_result, actual_outcome
        )
        experiment.prediction_matched = prediction_matched
        
        # Update the theory
        theory = self._active_theories.get(experiment.theory_id)
        if theory:
            theory.tests_conducted += 1
            theory.last_tested_at = datetime.now().isoformat()
            
            if prediction_matched:
                theory.tests_successful += 1
                theory.supporting_observations.append(
                    f"Experiment {experiment.experiment_id}: Prediction matched"
                )
                # Increase confidence
                theory.confidence = min(0.95, theory.confidence + 0.1)
                logger.info(f"[SCIENCE] Theory SUPPORTED: {theory.description} (conf: {theory.confidence:.2f})")
            else:
                theory.contradicting_observations.append(
                    f"Experiment {experiment.experiment_id}: Prediction failed - got {actual_outcome}"
                )
                # Decrease confidence
                theory.confidence = max(0.1, theory.confidence - 0.15)
                logger.info(f"[SCIENCE] Theory WEAKENED: {theory.description} (conf: {theory.confidence:.2f})")
            
            # Update status based on confidence
            if theory.confidence >= 0.7 and theory.tests_conducted >= 3:
                theory.status = TheoryStatus.SUPPORTED
                self._share_theory_to_network(theory, agent_id)
            elif theory.confidence <= 0.3 and theory.tests_conducted >= 3:
                theory.status = TheoryStatus.REFUTED
            
            # Save updated theory
            self._save_theory(theory)
        
        # Store experiment
        self._save_experiment(experiment, agent_id)
        
        # Clear current experiment
        self._current_experiment = None
    
    def _compare_prediction_to_result(self, 
                                       expected: Dict[str, Any],
                                       actual: Dict[str, Any]) -> bool:
        """Compare expected result to actual result."""
        # Check game state match
        if 'game_state' in expected:
            if actual.get('game_state') != expected['game_state']:
                return False
        
        # Check effect match
        if 'effect' in expected:
            actual_effect = actual.get('effect', '')
            if actual_effect != expected['effect']:
                return False
        
        # Check score increase
        if expected.get('score_increase'):
            if not actual.get('score_increased'):
                return False
        
        return True
    
    # =========================================================================
    # PHASE 6: BELIEF UPDATE - Strengthen or refute theories
    # =========================================================================
    
    def update_beliefs(self, game_type: str, level_number: int):
        """
        Periodic update of all theories based on accumulated evidence.
        
        Called at end of each level or game.
        """
        # Get all active theories for this game/level
        theories = self._get_theories_for_level(game_type, level_number)
        
        for theory in theories:
            # Decay untested theories
            if theory.tests_conducted == 0:
                theory.confidence = max(0.2, theory.confidence * 0.95)
            
            # Mark stale theories
            if theory.last_tested_at:
                # If not tested in a while, reduce confidence slightly
                pass
            
            self._save_theory(theory)
    
    # =========================================================================
    # PHASE 7: GENERALIZATION - Abstract to broader principles
    # =========================================================================
    
    def attempt_generalization(self, game_type: str, agent_id: str) -> Optional[Theory]:
        """
        Attempt to generalize confirmed theories across levels.
        
        If "red kills me" is true on levels 1, 2, and 3, generalize to
        "red kills me on ALL levels of this game type".
        """
        # Get all supported theories for this game type
        supported = self.db.execute_query("""
            SELECT * FROM agent_theories
            WHERE game_type = ? AND status = 'supported' AND is_active = 1
            ORDER BY theory_type, level_number
        """, (game_type,))
        
        if not supported:
            return None
        
        # Group by theory type and formal statement
        theory_groups = {}
        for t in supported:
            key = (t['theory_type'], json.dumps(t['formal_statement'], sort_keys=True))
            if key not in theory_groups:
                theory_groups[key] = []
            theory_groups[key].append(t)
        
        # Look for theories that appear across multiple levels
        for (theory_type, statement), instances in theory_groups.items():
            if len(instances) >= 3:  # Same theory on 3+ levels
                levels = [i['level_number'] for i in instances]
                
                # Check if we already have a generalization
                existing = self.db.execute_query("""
                    SELECT * FROM agent_theories
                    WHERE game_type = ? AND theory_type = ? AND level_number = -1
                    AND formal_statement = ?
                """, (game_type, theory_type, statement))
                
                if not existing:
                    # Create generalized theory
                    generalized = Theory(
                        theory_id=f"gen_{game_type}_{uuid.uuid4().hex[:8]}",
                        theory_type=TheoryType(theory_type),
                        game_type=game_type,
                        level_number=-1,  # -1 = applies to all levels
                        description=f"GENERALIZED: {instances[0]['description']} (applies across levels {levels})",
                        formal_statement=json.loads(statement),
                        predictions=[{
                            'scope': 'all_levels',
                            'applies_to': levels
                        }],
                        confidence=0.8,
                        status=TheoryStatus.GENERALIZED,
                        generalized_from=instances[0]['theory_id'],
                        child_theories=[i['theory_id'] for i in instances],
                        discovered_by_agent=agent_id
                    )
                    
                    self._add_theory(generalized)
                    logger.info(f"[SCIENCE] GENERALIZED theory: {generalized.description}")
                    return generalized
        
        return None
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _add_theory(self, theory: Theory):
        """Add a theory to active tracking and storage."""
        self._active_theories[theory.theory_id] = theory
        self._save_theory(theory)
        
        # Queue an experiment for this theory
        experiment = self.design_experiment(theory)
        if experiment:
            self._experiment_queue.append(experiment)
    
    def _save_theory(self, theory: Theory):
        """Save theory to database."""
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO agent_theories (
                    theory_id, theory_type, game_type, level_number,
                    description, formal_statement, predictions,
                    supporting_observations, contradicting_observations,
                    confidence, status, tests_conducted, tests_successful,
                    generalized_from, child_theories,
                    created_at, last_tested_at, discovered_by_agent, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                theory.theory_id, theory.theory_type.value, theory.game_type, theory.level_number,
                theory.description, json.dumps(theory.formal_statement), json.dumps(theory.predictions),
                json.dumps(theory.supporting_observations), json.dumps(theory.contradicting_observations),
                theory.confidence, theory.status.value, theory.tests_conducted, theory.tests_successful,
                theory.generalized_from, json.dumps(theory.child_theories),
                theory.created_at, theory.last_tested_at, theory.discovered_by_agent
            ))
        except Exception as e:
            logger.debug(f"Error saving theory: {e}")
    
    def _save_experiment(self, experiment: Experiment, agent_id: str):
        """Save experiment to database."""
        try:
            self.db.execute_query("""
                INSERT INTO theory_experiments (
                    experiment_id, theory_id, hypothesis, prediction,
                    preconditions, test_action, expected_result,
                    actual_result, prediction_matched, executed_at, executed_by_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id, experiment.theory_id, experiment.hypothesis,
                json.dumps(experiment.prediction), json.dumps(experiment.preconditions),
                experiment.test_action, json.dumps(experiment.expected_result),
                json.dumps(experiment.actual_result) if experiment.actual_result else None,
                1 if experiment.prediction_matched else 0,
                experiment.executed_at, agent_id
            ))
        except Exception as e:
            logger.debug(f"Error saving experiment: {e}")
    
    def _share_theory_to_network(self, theory: Theory, agent_id: str):
        """Share a confirmed theory to the network for other agents."""
        try:
            self.db.execute_query("""
                UPDATE agent_theories
                SET shared_to_network = 1
                WHERE theory_id = ?
            """, (theory.theory_id,))
            
            logger.info(f"[SCIENCE] Shared theory to network: {theory.description}")
        except Exception as e:
            logger.debug(f"Error sharing theory: {e}")
    
    def _get_theories_for_level(self, game_type: str, level_number: int) -> List[Theory]:
        """Get all theories for a specific level."""
        results = self.db.execute_query("""
            SELECT * FROM agent_theories
            WHERE game_type = ? AND (level_number = ? OR level_number = -1)
            AND is_active = 1
        """, (game_type, level_number))
        
        theories = []
        for r in results or []:
            theories.append(Theory(
                theory_id=r['theory_id'],
                theory_type=TheoryType(r['theory_type']),
                game_type=r['game_type'],
                level_number=r['level_number'],
                description=r['description'],
                formal_statement=json.loads(r['formal_statement']),
                predictions=json.loads(r['predictions'] or '[]'),
                supporting_observations=json.loads(r['supporting_observations'] or '[]'),
                contradicting_observations=json.loads(r['contradicting_observations'] or '[]'),
                confidence=r['confidence'],
                status=TheoryStatus(r['status']),
                tests_conducted=r['tests_conducted'],
                tests_successful=r['tests_successful']
            ))
        
        return theories
    
    def _get_pending_theories(self) -> List[Theory]:
        """Get theories that haven't been fully tested."""
        return [t for t in self._active_theories.values() 
                if t.status == TheoryStatus.PROPOSED and t.tests_conducted < 3]
    
    def _get_adjacent_colors(self, frame: List[List[int]], 
                             controlled: List[Dict]) -> set:
        """Get colors adjacent to controlled objects."""
        if not frame or not controlled:
            return set()
        
        adjacent = set()
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        for obj in controlled:
            x, y = obj.get('x', 0), obj.get('y', 0)
            player_color = obj.get('color')
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        color = frame[ny][nx]
                        if color != 0 and color != player_color:
                            adjacent.add(color)
        
        return adjacent
    
    def _analyze_frame_changes(self, before: List[List[int]], 
                                after: List[List[int]]) -> List[str]:
        """Analyze what changed between frames."""
        changes = []
        
        if not before or not after:
            return ["no_frame_data"]
        
        # Simple change detection
        for y, (row_b, row_a) in enumerate(zip(before, after)):
            for x, (cell_b, cell_a) in enumerate(zip(row_b, row_a)):
                if cell_b != cell_a:
                    changes.append(f"({x},{y}): {cell_b} -> {cell_a}")
        
        return changes[:10]  # Limit to first 10
    
    def _find_disappeared_colors(self, before: List[List[int]], 
                                  after: List[List[int]]) -> set:
        """Find colors that existed before but not after."""
        before_colors = set()
        after_colors = set()
        
        for row in before or []:
            for cell in row:
                if cell != 0:
                    before_colors.add(cell)
        
        for row in after or []:
            for cell in row:
                if cell != 0:
                    after_colors.add(cell)
        
        return before_colors - after_colors
