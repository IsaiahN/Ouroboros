import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Rule Induction Engine - Learn Abstract Rules from Successful Game Attempts
==========================================================================

Extracts transferable rules from winning games:
- Analyzes visual conditions that led to success
- Identifies causal action-effect relationships
- Creates abstract rule templates
- Matches rules to new games for transfer learning

Migrated from deprecated/rule_induction_engine.py

Key Methods:
- extract_rule_from_game_session(): Extract rule from winning game
- match_rule_to_game(): Check if rule applies to new game
- get_applicable_rules(): Get all rules that apply to current game
- update_rule_success(): Update rule after transfer attempt

Following Rules:
- Rule 2: Database-only storage
- Rule 3: Clean integration
- Rule 11: No Unicode emojis
"""

import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from engines.engine_logger import get_engine_logger
from engines.perception.visual_reasoning import VisualReasoningEngine

logger = get_engine_logger("rule_induction")

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


class RuleInductionEngine:
    """
    Learn abstract, transferable rules from ARC game successes.
    Enables meta-learning and generalization to unseen levels.
    """

    def __init__(self, database_interface: 'DatabaseInterface'):
        self.db = database_interface
        self.visual_engine = VisualReasoningEngine(database_interface)
        self.engine_id = f"rule_induction_{uuid.uuid4().hex[:8]}"
        self._schema_initialized = False

    def _ensure_schema(self) -> None:
        """Lazy initialization of database schema."""
        if self._schema_initialized:
            return

        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS learned_rules (
                    rule_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    source_game_id TEXT,
                    preconditions TEXT,
                    action_template TEXT,
                    confidence REAL DEFAULT 0.5,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    applicable_games TEXT,
                    transferred_successfully BOOLEAN DEFAULT FALSE,
                    visual_signature TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_learned_rules_confidence
                ON learned_rules(confidence DESC, success_count DESC)
            """)

            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS rule_transfers (
                    transfer_id TEXT PRIMARY KEY,
                    rule_id TEXT,
                    source_game_id TEXT,
                    target_game_id TEXT,
                    transfer_successful BOOLEAN,
                    confidence_before REAL,
                    actual_result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rule_id) REFERENCES learned_rules(rule_id)
                )
            """)

            self._schema_initialized = True
            logger.debug("Schema initialized")

        except Exception as e:
            logger.error("Failed to initialize schema", error=str(e))

    def extract_rule_from_game_session(
        self,
        game_session_data: Dict[str, Any],
        skip_if_exists: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Extract transferable rule from successful game attempt.

        Args:
            game_session_data: Complete game session with:
                - game_id
                - initial_frame
                - action_sequence
                - frame_states (after each action)
                - won (boolean)
                - score_achieved
            skip_if_exists: If True, return existing rule instead of creating duplicate

        Returns:
            Rule dictionary or None if no rule can be extracted
        """
        self._ensure_schema()

        if not game_session_data.get('won', False):
            return None

        if not game_session_data.get('initial_frame') or not game_session_data.get('action_sequence'):
            return None

        # Deduplication check
        if skip_if_exists:
            game_id = game_session_data['game_id']
            action_sequence = game_session_data['action_sequence']
            action_hash = hash(str(action_sequence)) % 1000000

            existing = self.db.execute_query("""
                SELECT rule_id, success_count FROM learned_rules
                WHERE source_game_id LIKE ?
                ORDER BY success_count DESC LIMIT 5
            """, (f"{game_id.split('-')[0]}%",))

            if existing:
                for rule in existing:
                    rule_data = self.db.execute_query(
                        "SELECT action_template FROM learned_rules WHERE rule_id = ?",
                        (rule['rule_id'],)
                    )
                    if rule_data:
                        try:
                            existing_template = json.loads(rule_data[0]['action_template'])
                            existing_hash = hash(str(existing_template.get('action_sequence', []))) % 1000000
                            if existing_hash == action_hash:
                                self.db.execute_query(
                                    "UPDATE learned_rules SET success_count = success_count + 1 WHERE rule_id = ?",
                                    (rule['rule_id'],)
                                )
                                logger.debug("Deduplicated existing rule", rule_id=rule['rule_id'])
                                return {'rule_id': rule['rule_id'], 'deduplicated': True}
                        except (json.JSONDecodeError, TypeError):
                            pass

        try:
            # Analyze initial visual state
            initial_features = self.visual_engine.analyze_grid(game_session_data['initial_frame'])

            # Extract action effects
            action_effects = self._analyze_action_effects(game_session_data)

            # Identify preconditions
            preconditions = self._extract_preconditions(initial_features)

            # Create abstract action template
            action_template = self._abstract_action_sequence(
                game_session_data['action_sequence'],
                initial_features
            )

            # Build rule
            rule = {
                'rule_id': f"rule_{uuid.uuid4().hex[:12]}",
                'agent_id': game_session_data.get('agent_id', 'unknown'),
                'source_game_id': game_session_data['game_id'],
                'preconditions': preconditions,
                'action_template': action_template,
                'expected_outcome': 'win',
                'confidence': self._calculate_initial_confidence(game_session_data),
                'success_count': 1,
                'failure_count': 0,
                'applicable_games': [game_session_data['game_id']],
                'transferred_successfully': False,
                'visual_signature': self._create_visual_signature(initial_features),
                'created_at': datetime.now().isoformat()
            }

            self._store_rule(rule)

            logger.info("Extracted new rule", rule_id=rule['rule_id'], game_id=rule['source_game_id'])
            return rule

        except Exception as e:
            logger.error("Rule extraction failed", error=str(e))
            return None

    def _analyze_action_effects(self, game_session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze what each action accomplished."""
        effects: List[Dict[str, Any]] = []

        actions = game_session_data.get('action_sequence', [])
        frame_states = game_session_data.get('frame_states', [])

        if len(frame_states) < len(actions) + 1:
            return effects

        for i, action in enumerate(actions):
            before_frame = frame_states[i]
            after_frame = frame_states[i + 1]

            before_analysis = self.visual_engine.analyze_grid(before_frame)
            after_analysis = self.visual_engine.analyze_grid(after_frame)

            effect = {
                'action': action,
                'changes': self._compute_changes(before_analysis, after_analysis),
                'score_delta': 0
            }

            effects.append(effect)

        return effects

    def _compute_changes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Compute what changed between two visual analyses."""
        return {
            'color_change': after['colors']['unique_colors'] != before['colors']['unique_colors'],
            'shape_count_change': len(after['shapes']) != len(before['shapes']),
            'symmetry_change': after['symmetry']['has_any_symmetry'] != before['symmetry']['has_any_symmetry'],
            'complexity_change': after['complexity']['overall_complexity'] - before['complexity']['overall_complexity']
        }

    def _extract_preconditions(self, visual_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key preconditions from visual features."""
        preconditions: List[Dict[str, Any]] = []

        # Symmetry preconditions
        if visual_features['symmetry']['has_any_symmetry']:
            for sym_type, detected in visual_features['symmetry']['detected'].items():
                if detected:
                    preconditions.append({
                        'type': 'symmetry',
                        'subtype': sym_type,
                        'required': True,
                        'confidence': visual_features['symmetry']['confidence'].get(sym_type, 0.0)
                    })

        # Color preconditions
        colors = visual_features['colors']
        if colors['unique_colors'] > 0:
            preconditions.append({
                'type': 'color_count',
                'value': colors['unique_colors'],
                'operator': 'approximately',
                'tolerance': 2
            })

        # Sparsity precondition
        if colors.get('is_sparse', False):
            preconditions.append({
                'type': 'sparsity',
                'is_sparse': True,
                'background_threshold': 0.6
            })

        # Shape count precondition
        shape_count = len(visual_features.get('shapes', []))
        if shape_count > 0:
            preconditions.append({
                'type': 'shape_count',
                'value': shape_count,
                'operator': 'approximately',
                'tolerance': 2
            })

        # Pattern precondition
        patterns = visual_features.get('patterns', [])
        if patterns:
            preconditions.append({
                'type': 'has_repeating_patterns',
                'pattern_count': len(patterns),
                'min_frequency': 2
            })

        # Complexity precondition
        complexity = visual_features['complexity']['overall_complexity']
        preconditions.append({
            'type': 'complexity',
            'level': 'low' if complexity < 0.3 else 'medium' if complexity < 0.7 else 'high',
            'value': complexity
        })

        return preconditions

    def _abstract_action_sequence(
        self,
        actions: List[Dict[str, Any]],
        initial_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create abstract action template from concrete action sequence."""
        action_types = [a.get('action_type', a.get('type', 0)) for a in actions]

        action_counts: Dict[int, int] = {}
        for atype in action_types:
            action_counts[atype] = action_counts.get(atype, 0) + 1

        has_coordinates = any(a.get('action_type', 0) == 6 for a in actions)

        template: Dict[str, Any] = {
            'sequence_length': len(actions),
            'action_types': action_types,
            'action_counts': action_counts,
            'has_coordinate_actions': has_coordinates,
            'primary_actions': [at for at, count in action_counts.items() if count >= 2]
        }

        # If uses coordinates, analyze coordinate strategy
        if has_coordinates:
            coords_used = [
                (a.get('coordinate_x'), a.get('coordinate_y'))
                for a in actions
                if a.get('action_type', 0) == 6
                   and a.get('coordinate_x') is not None
                   and a.get('coordinate_y') is not None
            ]

            valid_coords: List[Tuple[int, int]] = [
                (int(x), int(y)) for x, y in coords_used
                if x is not None and y is not None
            ]

            if valid_coords:
                template['coordinate_strategy'] = self._infer_coordinate_strategy(
                    valid_coords,
                    initial_features
                )

        return template

    def _infer_coordinate_strategy(
        self,
        coords: List[Tuple[int, int]],
        visual_features: Dict[str, Any]
    ) -> str:
        """Infer what coordinate strategy was used."""
        if not coords:
            return 'none'

        shapes = visual_features.get('shapes', [])
        if shapes:
            shape_centers = [tuple(s['center']) for s in shapes]
            near_centers = sum(1 for c in coords if any(
                abs(c[0] - sc[0]) <= 1 and abs(c[1] - sc[1]) <= 1
                for sc in shape_centers
            ))

            if near_centers / len(coords) > 0.5:
                return 'target_shape_centers'

        # Check for linear pattern
        if len(coords) >= 3:
            dx_values = [coords[i+1][0] - coords[i][0] for i in range(len(coords)-1)]
            dy_values = [coords[i+1][1] - coords[i][1] for i in range(len(coords)-1)]

            if len(set(dx_values)) == 1 and len(set(dy_values)) == 1:
                return 'linear_pattern'

        if visual_features['symmetry']['has_any_symmetry']:
            return 'symmetry_aligned'

        return 'exploratory'

    def _calculate_initial_confidence(self, game_session_data: Dict[str, Any]) -> float:
        """Calculate initial confidence for newly extracted rule."""
        confidence = 0.5

        actions_taken = len(game_session_data.get('action_sequence', []))
        if actions_taken < 50:
            confidence += 0.2

        score = game_session_data.get('score_achieved', 0)
        if score > 0.5:
            confidence += 0.2

        return min(confidence, 1.0)

    def _create_visual_signature(self, visual_features: Dict[str, Any]) -> str:
        """Create compact visual signature for quick rule matching."""
        sig_parts = []

        # Symmetry signature
        sym = visual_features['symmetry']
        if sym['has_any_symmetry']:
            sym_types = [k for k, v in sym['detected'].items() if v]
            sig_parts.append(f"SYM:{'_'.join(sym_types[:2])}")

        # Color signature
        colors = visual_features['colors']
        sig_parts.append(f"COL:{colors['unique_colors']}")

        # Shape signature
        shape_count = len(visual_features.get('shapes', []))
        sig_parts.append(f"SHP:{shape_count}")

        # Pattern signature
        pattern_count = len(visual_features.get('patterns', []))
        if pattern_count > 0:
            sig_parts.append(f"PAT:{pattern_count}")

        # Complexity signature
        complexity = visual_features['complexity']['overall_complexity']
        comp_level = 'L' if complexity < 0.3 else 'M' if complexity < 0.7 else 'H'
        sig_parts.append(f"CMP:{comp_level}")

        return '|'.join(sig_parts)

    def match_rule_to_game(
        self,
        rule: Dict[str, Any],
        current_frame: List[List[int]]
    ) -> Tuple[bool, float]:
        """
        Check if learned rule applies to new game.

        Args:
            rule: Learned rule dictionary
            current_frame: Initial frame of new game

        Returns:
            (matches, confidence_score) tuple
        """
        current_features = self.visual_engine.analyze_grid(current_frame)

        preconditions = rule.get('preconditions', [])
        if not preconditions:
            return False, 0.0

        matches = 0.0
        total_weight = 0.0

        for condition in preconditions:
            weight = condition.get('confidence', 1.0)
            total_weight += weight

            if self._check_condition(condition, current_features):
                matches += weight

        if total_weight == 0:
            return False, 0.0

        confidence = matches / total_weight

        return confidence > 0.6, confidence

    def _check_condition(
        self,
        condition: Dict[str, Any],
        visual_features: Dict[str, Any]
    ) -> bool:
        """Check if a single condition is satisfied."""
        cond_type = condition['type']

        if cond_type == 'symmetry':
            subtype = condition['subtype']
            return visual_features['symmetry']['detected'].get(subtype, False)

        elif cond_type == 'color_count':
            current_count = visual_features['colors']['unique_colors']
            expected = condition['value']
            tolerance = condition.get('tolerance', 2)
            return abs(current_count - expected) <= tolerance

        elif cond_type == 'sparsity':
            return visual_features['colors'].get('is_sparse', False) == condition['is_sparse']

        elif cond_type == 'shape_count':
            current_count = len(visual_features.get('shapes', []))
            expected = condition['value']
            tolerance = condition.get('tolerance', 2)
            return abs(current_count - expected) <= tolerance

        elif cond_type == 'has_repeating_patterns':
            pattern_count = len(visual_features.get('patterns', []))
            return pattern_count >= condition.get('min_frequency', 1)

        elif cond_type == 'complexity':
            current_complexity = visual_features['complexity']['overall_complexity']
            expected_level = condition['level']

            if expected_level == 'low':
                return current_complexity < 0.4
            elif expected_level == 'medium':
                return 0.3 < current_complexity < 0.8
            else:  # high
                return current_complexity > 0.6

        return False

    def get_applicable_rules(
        self,
        current_frame: List[List[int]],
        agent_id: Optional[str] = None,
        min_confidence: float = 0.6
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Get all rules that apply to current game.

        Args:
            current_frame: Initial game frame
            agent_id: Optional agent ID to filter rules
            min_confidence: Minimum confidence threshold

        Returns:
            List of (rule, confidence) tuples sorted by confidence
        """
        self._ensure_schema()

        if agent_id:
            rules = self.db.execute_query("""
                SELECT * FROM learned_rules
                WHERE agent_id = ? AND confidence >= ?
                ORDER BY confidence DESC, success_count DESC
            """, (agent_id, min_confidence))
        else:
            rules = self.db.execute_query("""
                SELECT * FROM learned_rules
                WHERE confidence >= ?
                ORDER BY confidence DESC, success_count DESC
            """, (min_confidence,))

        if not rules:
            return []

        applicable: List[Tuple[Dict[str, Any], float]] = []

        for rule_data in rules:
            rule = dict(rule_data)
            rule['preconditions'] = json.loads(rule.get('preconditions', '[]'))
            rule['action_template'] = json.loads(rule.get('action_template', '{}'))

            matches, confidence = self.match_rule_to_game(rule, current_frame)

            if matches and confidence >= min_confidence:
                applicable.append((rule, confidence))

        applicable.sort(key=lambda x: x[1], reverse=True)

        return applicable

    def update_rule_success(self, rule_id: str, success: bool, target_game_id: str) -> None:
        """Update rule after transfer attempt."""
        self._ensure_schema()

        if success:
            self.db.execute_query("""
                UPDATE learned_rules
                SET success_count = success_count + 1,
                    confidence = MIN(confidence + 0.05, 1.0),
                    transferred_successfully = 1
                WHERE rule_id = ?
            """, (rule_id,))

            # Add to applicable games
            rule = self.db.execute_query(
                "SELECT applicable_games FROM learned_rules WHERE rule_id = ?",
                (rule_id,)
            )
            if rule:
                applicable_games = json.loads(rule[0]['applicable_games'] or '[]')
                if target_game_id not in applicable_games:
                    applicable_games.append(target_game_id)
                    self.db.execute_query("""
                        UPDATE learned_rules
                        SET applicable_games = ?
                        WHERE rule_id = ?
                    """, (json.dumps(applicable_games), rule_id))

            logger.info("Rule transfer succeeded", rule_id=rule_id, target_game=target_game_id)
        else:
            self.db.execute_query("""
                UPDATE learned_rules
                SET failure_count = failure_count + 1,
                    confidence = MAX(confidence - 0.1, 0.0)
                WHERE rule_id = ?
            """, (rule_id,))

            logger.debug("Rule transfer failed", rule_id=rule_id, target_game=target_game_id)

        self._log_transfer_attempt(rule_id, target_game_id, success)

    def _store_rule(self, rule: Dict[str, Any]) -> None:
        """Store rule in database."""
        self.db.execute_query("""
            INSERT INTO learned_rules (
                rule_id, agent_id, source_game_id, preconditions, action_template,
                confidence, success_count, failure_count, applicable_games,
                transferred_successfully, visual_signature, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule['rule_id'],
            rule['agent_id'],
            rule['source_game_id'],
            json.dumps(rule['preconditions']),
            json.dumps(rule['action_template']),
            rule['confidence'],
            rule['success_count'],
            rule['failure_count'],
            json.dumps(rule['applicable_games']),
            rule['transferred_successfully'],
            rule.get('visual_signature', ''),
            rule['created_at']
        ))

    def _log_transfer_attempt(self, rule_id: str, target_game_id: str, success: bool) -> None:
        """Log rule transfer attempt to database."""
        transfer_id = f"transfer_{uuid.uuid4().hex[:12]}"

        rule = self.db.execute_query(
            "SELECT source_game_id, confidence FROM learned_rules WHERE rule_id = ?",
            (rule_id,)
        )

        if rule:
            try:
                self.db.execute_query("""
                    INSERT INTO rule_transfers (
                        transfer_id, rule_id, source_game_id, target_game_id,
                        transfer_successful, confidence_before, actual_result, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transfer_id,
                    rule_id,
                    rule[0]['source_game_id'],
                    target_game_id,
                    success,
                    rule[0]['confidence'],
                    'success' if success else 'failure',
                    datetime.now().isoformat()
                ))
            except Exception as e:
                logger.debug("Failed to log transfer attempt", error=str(e))
