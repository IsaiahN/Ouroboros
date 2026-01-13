import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Replay Learning Engine - Learn rules and primitives during sequence replay
============================================================================

Purpose:
- Enable agents to learn WHY sequences work, not just that they work
- Generate predictions BEFORE each replay action
- Compare predictions to actual outcomes AFTER each action
- Induce rules and primitives from prediction/outcome comparisons
- Store learning events for network synthesis (viral knowledge transfer)

Key Insight (from user):
"With each replay, agents should get smart enough to understand WHY that game 
level works the way it does, learn the rules, and could play it without 
sequences or even BETTER because they understand the rules. They would even 
know what is wasted movement (useful for optimizer class)."

Following Rule 2: All data stored in database
Following Rule 11: No Unicode emojis
"""

import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

try:
    from database_interface import DatabaseInterface
except ImportError:
    DatabaseInterface = None


@dataclass
class ReplayPrediction:
    """Agent's prediction about what the next sequence action will do."""
    action_index: int
    action_type: int  # 1-7
    coordinate: Optional[Tuple[int, int]] = None  # For ACTION6
    
    # Predictions (generated BEFORE seeing the action outcome)
    predicted_frame_change: str = "unknown"  # 'none', 'minor', 'major', 'level_transition'
    predicted_object_effect: str = "unknown"  # 'move', 'toggle', 'collect', 'destroy', 'none'
    predicted_score_change: float = 0.0
    hypothesized_rule: str = ""  # Agent's best guess about the underlying rule
    confidence: float = 0.0  # 0.0-1.0
    
    # Set AFTER observing outcome
    actual_frame_change: str = ""
    actual_object_effect: str = ""
    actual_score_change: float = 0.0
    prediction_correct: bool = False
    
    # Learning derived from comparison
    inferred_rule: str = ""
    primitive_candidate: str = ""
    wasted_action: bool = False  # True if action had no effect (optimizer signal)
    

@dataclass
class ReplayLearningContext:
    """Context accumulated during a replay session for learning."""
    sequence_id: str
    game_id: str
    game_type: str
    level_number: int
    agent_id: str
    
    # Accumulated learning
    predictions: List[ReplayPrediction] = field(default_factory=list)
    correct_predictions: int = 0
    total_predictions: int = 0
    
    # Pattern detection
    action_effect_map: Dict[int, List[str]] = field(default_factory=dict)  # action -> [observed effects]
    click_effect_map: Dict[str, List[str]] = field(default_factory=dict)  # "color_at_coord" -> [effects]
    wasted_action_indices: List[int] = field(default_factory=list)
    
    # Inferred rules (built up during replay)
    inferred_rules: List[Dict[str, Any]] = field(default_factory=list)
    inferred_primitives: List[str] = field(default_factory=list)
    
    # For rule induction
    frame_before_first_action: Optional[List] = None
    consecutive_no_change_count: int = 0


class ReplayLearningEngine:
    """
    Enable agents to learn from sequence replays through prediction and comparison.
    
    Core Loop (per replay action):
    1. PREDICT: What will this action do? (before seeing outcome)
    2. EXECUTE: Run the actual sequence action
    3. COMPARE: What actually happened vs prediction?
    4. LEARN: Extract rules, mark wasted actions, build understanding
    
    This transforms passive sequence replay into active learning.
    """
    
    def __init__(self, database_interface: 'DatabaseInterface'):
        self.db = database_interface
        self.engine_id = f"replay_learn_{uuid.uuid4().hex[:8]}"
        self._ensure_tables_exist()
        
        # Action type names for reasoning
        self.ACTION_NAMES = {
            1: 'UP', 2: 'DOWN', 3: 'RIGHT', 4: 'LEFT',
            5: 'SPECIAL', 6: 'CLICK', 7: 'UNDO'
        }
        
        # Cache for game type patterns (learned from previous replays)
        self._game_type_patterns: Dict[str, Dict] = {}
        self._load_known_patterns()
    
    def _ensure_tables_exist(self):
        """Create database tables for replay learning (Rule 2: Database-only)."""
        try:
            # Main learning events table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS replay_learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER DEFAULT 1,
                    agent_id TEXT,
                    action_index INTEGER NOT NULL,
                    action_type INTEGER NOT NULL,
                    coordinate_x INTEGER,
                    coordinate_y INTEGER,
                    
                    -- Predictions (made before action)
                    predicted_frame_change TEXT,
                    predicted_object_effect TEXT,
                    predicted_score_change REAL DEFAULT 0.0,
                    hypothesized_rule TEXT,
                    prediction_confidence REAL DEFAULT 0.0,
                    
                    -- Actuals (observed after action)
                    actual_frame_change TEXT,
                    actual_object_effect TEXT,
                    actual_score_change REAL DEFAULT 0.0,
                    prediction_correct BOOLEAN DEFAULT FALSE,
                    
                    -- Learning outputs
                    inferred_rule TEXT,
                    primitive_candidate TEXT,
                    wasted_action BOOLEAN DEFAULT FALSE,
                    
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
                )
            """)
            
            # Aggregated patterns per game type (for transfer learning)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS replay_inferred_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_description TEXT NOT NULL,
                    action_mapping TEXT,
                    confidence REAL DEFAULT 0.5,
                    observation_count INTEGER DEFAULT 1,
                    last_observed TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(game_type, pattern_type, pattern_description)
                )
            """)
            
            # Wasted action markers for optimizer use
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS replay_wasted_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_id TEXT NOT NULL,
                    action_index INTEGER NOT NULL,
                    waste_reason TEXT,
                    potential_savings INTEGER DEFAULT 1,
                    verified_removable BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(sequence_id, action_index)
                )
            """)
            
            # Session-level learning summaries (for evolution tracking)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS replay_learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    sequence_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER DEFAULT 1,
                    agent_id TEXT,
                    prediction_accuracy REAL DEFAULT 0.0,
                    rules_inferred_count INTEGER DEFAULT 0,
                    primitives_discovered_count INTEGER DEFAULT 0,
                    wasted_actions_count INTEGER DEFAULT 0,
                    learning_quality TEXT DEFAULT 'low',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices for fast lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_replay_learning_game_type 
                ON replay_learning_events(game_type, level_number)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_replay_patterns_game_type 
                ON replay_inferred_patterns(game_type)
            """)
            
        except Exception as e:
            # Table creation is non-critical
            pass
    
    def _load_known_patterns(self):
        """Load previously learned patterns for each game type."""
        try:
            patterns = self.db.execute_query("""
                SELECT game_type, pattern_type, pattern_description, action_mapping, confidence
                FROM replay_inferred_patterns
                WHERE confidence >= 0.6
                ORDER BY confidence DESC
            """)
            
            if patterns:
                for p in patterns:
                    game_type = p['game_type']
                    if game_type not in self._game_type_patterns:
                        self._game_type_patterns[game_type] = {
                            'action_effects': {},
                            'click_effects': {},
                            'rules': []
                        }
                    
                    if p['pattern_type'] == 'action_effect':
                        try:
                            mapping = json.loads(p['action_mapping']) if p['action_mapping'] else {}
                            self._game_type_patterns[game_type]['action_effects'].update(mapping)
                        except:
                            pass
                    elif p['pattern_type'] == 'rule':
                        self._game_type_patterns[game_type]['rules'].append({
                            'description': p['pattern_description'],
                            'confidence': p['confidence']
                        })
        except Exception:
            pass
    
    def start_learning_session(
        self,
        sequence_id: str,
        game_id: str,
        level_number: int,
        agent_id: str,
        initial_frame: Optional[List] = None
    ) -> ReplayLearningContext:
        """
        Initialize a learning context for a replay session.
        
        Call this BEFORE starting sequence replay.
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        context = ReplayLearningContext(
            sequence_id=sequence_id,
            game_id=game_id,
            game_type=game_type,
            level_number=level_number,
            agent_id=agent_id,
            frame_before_first_action=initial_frame
        )
        
        # Pre-load any known patterns for this game type
        if game_type in self._game_type_patterns:
            known = self._game_type_patterns[game_type]
            context.action_effect_map = {
                int(k): v for k, v in known.get('action_effects', {}).items()
                if isinstance(k, (int, str)) and str(k).isdigit()
            }
        
        return context
    
    def generate_prediction(
        self,
        context: ReplayLearningContext,
        action_index: int,
        action_type: int,
        current_frame: List,
        sequence_actions: List[int],
        coordinate: Optional[Tuple[int, int]] = None
    ) -> ReplayPrediction:
        """
        Generate a prediction for what the upcoming action will do.
        
        Call this BEFORE executing each sequence action.
        Uses:
        - Previously observed effects in this replay
        - Known patterns for this game type
        - Sequence structure analysis (what comes next, pattern of actions)
        """
        prediction = ReplayPrediction(
            action_index=action_index,
            action_type=action_type,
            coordinate=coordinate
        )
        
        # Build prediction based on accumulated knowledge
        action_key = action_type
        
        # 1. Use known effects from this replay session
        if action_key in context.action_effect_map and context.action_effect_map[action_key]:
            effects = context.action_effect_map[action_key]
            most_common = max(set(effects), key=effects.count)
            prediction.predicted_object_effect = most_common
            prediction.confidence = effects.count(most_common) / len(effects)
        
        # 2. Use known patterns from game type (previous replays)
        elif context.game_type in self._game_type_patterns:
            known = self._game_type_patterns[context.game_type]
            if str(action_key) in known.get('action_effects', {}):
                prediction.predicted_object_effect = known['action_effects'][str(action_key)]
                prediction.confidence = 0.5  # Moderate confidence for transferred knowledge
        
        # 3. Default predictions based on action type
        if prediction.predicted_object_effect == "unknown":
            if action_type in [1, 2, 3, 4]:  # Movement
                prediction.predicted_object_effect = "move"
                prediction.predicted_frame_change = "minor"
                prediction.hypothesized_rule = f"ACTION{action_type} moves controlled object {self.ACTION_NAMES.get(action_type, 'UNKNOWN')}"
                prediction.confidence = 0.3
            elif action_type == 5:  # Special
                prediction.predicted_object_effect = "toggle"
                prediction.predicted_frame_change = "minor"
                prediction.hypothesized_rule = "ACTION5 toggles or rotates something"
                prediction.confidence = 0.2
            elif action_type == 6:  # Click
                prediction.predicted_object_effect = "toggle"
                prediction.predicted_frame_change = "minor"
                if coordinate:
                    pixel_color = self._get_pixel_color(current_frame, coordinate)
                    prediction.hypothesized_rule = f"Clicking {pixel_color} at ({coordinate[0]},{coordinate[1]}) toggles it"
                prediction.confidence = 0.3
            elif action_type == 7:  # Undo
                prediction.predicted_object_effect = "none"
                prediction.predicted_frame_change = "minor"
                prediction.hypothesized_rule = "ACTION7 undoes last action"
                prediction.confidence = 0.6
        
        # 4. Analyze sequence structure for score prediction
        remaining_actions = len(sequence_actions) - action_index
        if remaining_actions <= 3:
            # Near end of sequence - might trigger level completion
            prediction.predicted_score_change = 0.5  # Possible
        
        # 5. Detect potential wasted actions early
        # If same action repeated 3+ times consecutively, middle ones might be wasted
        if action_index >= 2:
            recent = sequence_actions[max(0, action_index-3):action_index]
            if len(recent) >= 2 and all(a == action_type for a in recent):
                prediction.hypothesized_rule += " (possibly redundant - repeated action)"
        
        context.predictions.append(prediction)
        context.total_predictions += 1
        
        return prediction
    
    def record_outcome(
        self,
        context: ReplayLearningContext,
        prediction: ReplayPrediction,
        frame_before: List,
        frame_after: List,
        score_before: float,
        score_after: float
    ) -> Dict[str, Any]:
        """
        Record what actually happened and compare to prediction.
        
        Call this AFTER executing each sequence action.
        Returns learning insights for this action.
        """
        # Analyze actual outcome
        frame_change = self._classify_frame_change(frame_before, frame_after)
        object_effect = self._detect_object_effect(frame_before, frame_after, prediction.action_type, prediction.coordinate)
        score_change = score_after - score_before
        
        # Update prediction with actuals
        prediction.actual_frame_change = frame_change
        prediction.actual_object_effect = object_effect
        prediction.actual_score_change = score_change
        
        # Compare prediction to actual
        prediction.prediction_correct = (
            prediction.predicted_object_effect == object_effect or
            (prediction.predicted_frame_change == frame_change and frame_change != 'none')
        )
        
        if prediction.prediction_correct:
            context.correct_predictions += 1
        
        # Detect wasted actions (no effect)
        if frame_change == 'none' and score_change == 0:
            prediction.wasted_action = True
            context.wasted_action_indices.append(prediction.action_index)
            context.consecutive_no_change_count += 1
            
            if context.consecutive_no_change_count >= 3:
                prediction.inferred_rule = "REDUNDANT: Multiple consecutive no-effect actions"
        else:
            context.consecutive_no_change_count = 0
        
        # Update action-effect mapping for future predictions
        action_key = prediction.action_type
        if action_key not in context.action_effect_map:
            context.action_effect_map[action_key] = []
        context.action_effect_map[action_key].append(object_effect)
        
        # Infer rules from comparison
        learning_result = self._induce_rule(context, prediction, frame_before, frame_after)
        
        # Store learning event in database
        self._store_learning_event(context, prediction)
        
        return learning_result
    
    def _classify_frame_change(self, before: List, after: List) -> str:
        """Classify the magnitude of frame change."""
        if not before or not after:
            return 'unknown'
        
        try:
            # Count pixel differences
            diff_count = 0
            total_pixels = 0
            
            for r1, r2 in zip(before, after):
                if isinstance(r1, list) and isinstance(r2, list):
                    for c1, c2 in zip(r1, r2):
                        total_pixels += 1
                        if c1 != c2:
                            diff_count += 1
            
            if total_pixels == 0:
                return 'unknown'
            
            diff_ratio = diff_count / total_pixels
            
            if diff_ratio == 0:
                return 'none'
            elif diff_ratio < 0.05:
                return 'minor'
            elif diff_ratio < 0.3:
                return 'major'
            else:
                return 'level_transition'
                
        except Exception:
            return 'unknown'
    
    def _detect_object_effect(
        self,
        before: List,
        after: List,
        action_type: int,
        coordinate: Optional[Tuple[int, int]]
    ) -> str:
        """Detect what effect the action had on objects."""
        if not before or not after:
            return 'unknown'
        
        try:
            # For click actions, check the clicked region
            if action_type == 6 and coordinate:
                x, y = coordinate
                # Check 3x3 region around click
                before_region = self._get_region(before, x, y, 3)
                after_region = self._get_region(after, x, y, 3)
                
                if before_region != after_region:
                    # Something changed at click location
                    return 'toggle'
                else:
                    return 'none'
            
            # For movement actions, detect object displacement
            if action_type in [1, 2, 3, 4]:
                # Find positions that changed
                changes = self._find_changed_positions(before, after)
                if len(changes) > 0:
                    return 'move'
                else:
                    return 'none'
            
            # For other actions
            frame_change = self._classify_frame_change(before, after)
            if frame_change == 'none':
                return 'none'
            elif frame_change == 'level_transition':
                return 'collect'  # Likely collected something to trigger transition
            else:
                return 'toggle'
                
        except Exception:
            return 'unknown'
    
    def _get_region(self, frame: List, x: int, y: int, size: int) -> List:
        """Get a region of pixels around a coordinate."""
        region = []
        half = size // 2
        
        try:
            for dy in range(-half, half + 1):
                row = []
                for dx in range(-half, half + 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < len(frame) and 0 <= nx < len(frame[0]):
                        row.append(frame[ny][nx])
                    else:
                        row.append(-1)  # Out of bounds
                region.append(row)
        except:
            pass
        
        return region
    
    def _find_changed_positions(self, before: List, after: List) -> List[Tuple[int, int]]:
        """Find all positions where pixels changed."""
        changes = []
        
        try:
            for y, (row1, row2) in enumerate(zip(before, after)):
                if isinstance(row1, list) and isinstance(row2, list):
                    for x, (c1, c2) in enumerate(zip(row1, row2)):
                        if c1 != c2:
                            changes.append((x, y))
        except:
            pass
        
        return changes
    
    def _get_pixel_color(self, frame: List, coord: Tuple[int, int]) -> str:
        """Get the color/value at a coordinate."""
        try:
            x, y = coord
            if 0 <= y < len(frame) and 0 <= x < len(frame[0]):
                return str(frame[y][x])
        except:
            pass
        return "unknown"
    
    def _induce_rule(
        self,
        context: ReplayLearningContext,
        prediction: ReplayPrediction,
        frame_before: List,
        frame_after: List
    ) -> Dict[str, Any]:
        """Induce a rule from the prediction/outcome comparison."""
        result = {
            'action_index': prediction.action_index,
            'action_type': prediction.action_type,
            'prediction_correct': prediction.prediction_correct,
            'inferred_rule': None,
            'primitive_candidate': None,
            'wasted': prediction.wasted_action,
            'optimizer_suggestion': None
        }
        
        # Rule induction based on observed patterns
        action_name = self.ACTION_NAMES.get(prediction.action_type, f'ACTION{prediction.action_type}')
        
        if prediction.actual_object_effect == 'move':
            # Movement rule
            rule = f"{action_name} moves controlled object"
            prediction.inferred_rule = rule
            result['inferred_rule'] = rule
            result['primitive_candidate'] = 'object_control'
            
        elif prediction.actual_object_effect == 'toggle':
            # Toggle rule
            if prediction.action_type == 6 and prediction.coordinate:
                color = self._get_pixel_color(frame_before, prediction.coordinate)
                rule = f"Clicking color {color} toggles state"
                prediction.inferred_rule = rule
                result['inferred_rule'] = rule
                result['primitive_candidate'] = 'toggle_interaction'
            else:
                rule = f"{action_name} toggles something"
                prediction.inferred_rule = rule
                result['inferred_rule'] = rule
                result['primitive_candidate'] = 'toggle_interaction'
        
        elif prediction.wasted_action:
            # Wasted action - valuable for optimizers
            result['optimizer_suggestion'] = f"Action {prediction.action_index} ({action_name}) had no effect - potentially removable"
            prediction.inferred_rule = "NO_EFFECT: Action did not change game state"
        
        # Level completion detection
        if prediction.actual_score_change > 0:
            rule = f"Actions before index {prediction.action_index} complete level {context.level_number}"
            prediction.inferred_rule = rule
            result['inferred_rule'] = rule
            result['primitive_candidate'] = 'level_completion_trigger'
        
        # Store rule if significant
        if result['inferred_rule']:
            context.inferred_rules.append({
                'rule': result['inferred_rule'],
                'action_index': prediction.action_index,
                'confidence': prediction.confidence + 0.2 if prediction.prediction_correct else prediction.confidence
            })
        
        if result['primitive_candidate'] and result['primitive_candidate'] not in context.inferred_primitives:
            context.inferred_primitives.append(result['primitive_candidate'])
        
        return result
    
    def _store_learning_event(self, context: ReplayLearningContext, prediction: ReplayPrediction):
        """Store a learning event in the database."""
        try:
            self.db.execute_query("""
                INSERT INTO replay_learning_events (
                    sequence_id, game_id, game_type, level_number, agent_id,
                    action_index, action_type, coordinate_x, coordinate_y,
                    predicted_frame_change, predicted_object_effect, predicted_score_change,
                    hypothesized_rule, prediction_confidence,
                    actual_frame_change, actual_object_effect, actual_score_change,
                    prediction_correct, inferred_rule, primitive_candidate, wasted_action,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context.sequence_id,
                context.game_id,
                context.game_type,
                context.level_number,
                context.agent_id,
                prediction.action_index,
                prediction.action_type,
                prediction.coordinate[0] if prediction.coordinate else None,
                prediction.coordinate[1] if prediction.coordinate else None,
                prediction.predicted_frame_change,
                prediction.predicted_object_effect,
                prediction.predicted_score_change,
                prediction.hypothesized_rule,
                prediction.confidence,
                prediction.actual_frame_change,
                prediction.actual_object_effect,
                prediction.actual_score_change,
                prediction.prediction_correct,
                prediction.inferred_rule,
                prediction.primitive_candidate,
                prediction.wasted_action,
                datetime.now().isoformat()
            ))
        except Exception as e:
            pass  # Non-critical - don't break replay for logging
    
    def finalize_session(self, context: ReplayLearningContext) -> Dict[str, Any]:
        """
        Finalize learning session and store aggregated patterns.
        
        Call this AFTER sequence replay completes.
        Returns summary of what was learned.
        """
        summary = {
            'sequence_id': context.sequence_id,
            'game_type': context.game_type,
            'level_number': context.level_number,
            'total_actions': context.total_predictions,
            'prediction_accuracy': (
                context.correct_predictions / context.total_predictions 
                if context.total_predictions > 0 else 0.0
            ),
            'wasted_actions': len(context.wasted_action_indices),
            'wasted_action_indices': context.wasted_action_indices,
            'inferred_rules': context.inferred_rules,
            'inferred_primitives': context.inferred_primitives,
            'action_effect_map': context.action_effect_map
        }
        
        # Store aggregated patterns for future replays
        self._store_aggregated_patterns(context)
        
        # Store wasted actions for optimizer use
        self._store_wasted_actions(context)
        
        # Update cache
        if context.game_type not in self._game_type_patterns:
            self._game_type_patterns[context.game_type] = {
                'action_effects': {},
                'click_effects': {},
                'rules': []
            }
        
        # Merge action effects
        for action, effects in context.action_effect_map.items():
            if effects:
                most_common = max(set(effects), key=effects.count)
                self._game_type_patterns[context.game_type]['action_effects'][str(action)] = most_common
        
        return summary
    
    def _store_aggregated_patterns(self, context: ReplayLearningContext):
        """Store patterns learned from this replay for future transfer."""
        try:
            # Store action-effect mappings
            for action, effects in context.action_effect_map.items():
                if not effects:
                    continue
                    
                most_common = max(set(effects), key=effects.count)
                confidence = effects.count(most_common) / len(effects)
                
                self.db.execute_query("""
                    INSERT INTO replay_inferred_patterns (
                        game_type, pattern_type, pattern_description, action_mapping, 
                        confidence, observation_count, last_observed, created_at
                    ) VALUES (?, 'action_effect', ?, ?, ?, 1, ?, ?)
                    ON CONFLICT(game_type, pattern_type, pattern_description) DO UPDATE SET
                        confidence = (confidence + excluded.confidence) / 2,
                        observation_count = observation_count + 1,
                        last_observed = excluded.last_observed
                """, (
                    context.game_type,
                    f"ACTION{action} causes {most_common}",
                    json.dumps({str(action): most_common}),
                    confidence,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            # Store inferred rules
            for rule in context.inferred_rules:
                self.db.execute_query("""
                    INSERT INTO replay_inferred_patterns (
                        game_type, pattern_type, pattern_description, 
                        confidence, observation_count, last_observed, created_at
                    ) VALUES (?, 'rule', ?, ?, 1, ?, ?)
                    ON CONFLICT(game_type, pattern_type, pattern_description) DO UPDATE SET
                        confidence = (confidence + excluded.confidence) / 2,
                        observation_count = observation_count + 1,
                        last_observed = excluded.last_observed
                """, (
                    context.game_type,
                    rule['rule'],
                    rule.get('confidence', 0.5),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
        except Exception:
            pass
    
    def _store_wasted_actions(self, context: ReplayLearningContext):
        """Store wasted actions for optimizer agents to use."""
        try:
            for idx in context.wasted_action_indices:
                self.db.execute_query("""
                    INSERT OR IGNORE INTO replay_wasted_actions (
                        sequence_id, action_index, waste_reason, potential_savings, created_at
                    ) VALUES (?, ?, 'no_effect', 1, ?)
                """, (
                    context.sequence_id,
                    idx,
                    datetime.now().isoformat()
                ))
        except Exception:
            pass
    
    def get_wasted_actions_for_optimizer(self, sequence_id: str) -> List[Dict]:
        """
        Get list of wasted actions for an optimizer to try removing.
        
        Optimizer agents can use this to create more efficient sequences.
        """
        try:
            result = self.db.execute_query("""
                SELECT action_index, waste_reason, potential_savings, verified_removable
                FROM replay_wasted_actions
                WHERE sequence_id = ?
                ORDER BY action_index
            """, (sequence_id,))
            
            return result if result else []
        except Exception:
            return []
    
    def get_known_rules_for_game(self, game_type: str) -> List[Dict]:
        """
        Get all inferred rules for a game type.
        
        Agents can use these to understand the game without replaying.
        """
        try:
            result = self.db.execute_query("""
                SELECT pattern_description as rule, confidence, observation_count
                FROM replay_inferred_patterns
                WHERE game_type = ? AND pattern_type = 'rule'
                ORDER BY confidence DESC, observation_count DESC
                LIMIT 20
            """, (game_type,))
            
            return result if result else []
        except Exception:
            return []
    
    def build_rich_reasoning(
        self,
        prediction: ReplayPrediction,
        learning_result: Dict[str, Any],
        sequence_id: str,
        total_steps: int,
        agent_role: str
    ) -> Dict[str, Any]:
        """
        Build rich reasoning payload for the reasoning log.
        
        Replaces monotonous "replaying sequence" with actual learning.
        """
        action_name = self.ACTION_NAMES.get(prediction.action_type, f'ACTION{prediction.action_type}')
        
        reasoning = {
            'action': f'ACTION{prediction.action_type}',
            'sequence_id': sequence_id,
            'replay_step': prediction.action_index + 1,
            'total_steps': total_steps,
            'agent_role': agent_role,
            
            # Prediction (what agent expected)
            'prediction': {
                'expected_effect': prediction.predicted_object_effect,
                'expected_frame_change': prediction.predicted_frame_change,
                'hypothesis': prediction.hypothesized_rule,
                'confidence': round(prediction.confidence, 2)
            },
            
            # Actual outcome
            'actual': {
                'effect': prediction.actual_object_effect,
                'frame_change': prediction.actual_frame_change,
                'score_change': prediction.actual_score_change
            },
            
            # Learning
            'prediction_correct': prediction.prediction_correct,
            'learning': {
                'inferred_rule': learning_result.get('inferred_rule'),
                'primitive': learning_result.get('primitive_candidate'),
                'wasted': prediction.wasted_action
            }
        }
        
        # Add coordinate for clicks
        if prediction.coordinate:
            reasoning['coordinate'] = {'x': prediction.coordinate[0], 'y': prediction.coordinate[1]}
        
        # Build human-readable reasoning string
        if prediction.prediction_correct:
            reasoning['reasoning'] = (
                f"{agent_role.upper()}: Predicted {action_name} would cause '{prediction.predicted_object_effect}' "
                f"[CORRECT] - {prediction.inferred_rule or 'pattern confirmed'}"
            )
        elif prediction.wasted_action:
            reasoning['reasoning'] = (
                f"{agent_role.upper()}: {action_name} had no effect - marking as potentially redundant for optimizer"
            )
        else:
            reasoning['reasoning'] = (
                f"{agent_role.upper()}: Predicted '{prediction.predicted_object_effect}' but got '{prediction.actual_object_effect}' "
                f"- updating understanding: {prediction.inferred_rule or 'learning new pattern'}"
            )
        
        return reasoning
