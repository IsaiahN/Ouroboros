"""
Rule Induction Engine - Learn abstract rules from successful game attempts
===========================================================================

Extracts transferable rules from winning games:
- Analyzes visual conditions that led to success
- Identifies causal action-effect relationships
- Creates abstract rule templates
- Matches rules to new games for transfer learning

Following Rule 2: All rules stored in database
Following Rule 3: Integrates with existing gameplay systems
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from database_interface import DatabaseInterface
from visual_reasoning_engine import VisualReasoningEngine

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


class RuleInductionEngine:
    """
    Learn abstract, transferable rules from ARC game successes
    Enables meta-learning and generalization to unseen levels
    """
    
    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.visual_engine = VisualReasoningEngine(database_interface)
        self.engine_id = f"rule_induction_{uuid.uuid4().hex[:8]}"
    
    def extract_rule_from_game_session(self, game_session_data: Dict[str, Any], 
                                        skip_if_exists: bool = True) -> Optional[Dict[str, Any]]:
        """
        Extract transferable rule from successful game attempt
        
        DEDUPLICATION: By default, skips creating a new rule if one already
        exists for this game + level + similar action pattern. Different
        strategies for the same level will still each get their own rules.
        
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
        if not game_session_data.get('won', False):
            # Only learn from successful attempts
            return None
        
        if not game_session_data.get('initial_frame') or not game_session_data.get('action_sequence'):
            return None
        
        # DEDUPLICATION CHECK: Don't create duplicate rules for same game/level/pattern
        if skip_if_exists:
            game_id = game_session_data['game_id']
            level_number = game_session_data.get('level_number', 1)
            action_sequence = game_session_data['action_sequence']
            
            # Create a simple hash of the action sequence for matching
            # Different sequences = different rules (preserves diversity)
            action_hash = hash(str(action_sequence)) % 1000000
            
            existing = self.db.execute_query("""
                SELECT rule_id, success_count FROM learned_rules 
                WHERE source_game_id LIKE ? 
                ORDER BY success_count DESC LIMIT 5
            """, (f"{game_id.split('-')[0]}%",))
            
            if existing:
                # Check if any existing rule has a similar action template
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
                                # Similar rule exists - increment success count instead of creating new
                                self.db.execute_query(
                                    "UPDATE learned_rules SET success_count = success_count + 1 WHERE rule_id = ?",
                                    (rule['rule_id'],)
                                )
                                return {'rule_id': rule['rule_id'], 'deduplicated': True}
                        except (json.JSONDecodeError, TypeError):
                            pass
        
        try:
            # 1. Analyze initial visual state
            initial_features = self.visual_engine.analyze_grid(game_session_data['initial_frame'])
            
            # 2. Extract action effects
            action_effects = self._analyze_action_effects(game_session_data)
            
            # 3. Identify preconditions (what visual features were present)
            preconditions = self._extract_preconditions(initial_features)
            
            # 4. Create abstract action template
            action_template = self._abstract_action_sequence(
                game_session_data['action_sequence'],
                initial_features
            )
            
            # 5. Build rule
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
            
            # Store in database (Rule 2)
            self._store_rule(rule)
            
            return rule
            
        except Exception as e:
            self._log_error(f"Rule extraction failed: {e}")
            return None
    
    def _analyze_action_effects(self, game_session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze what each action accomplished
        
        Returns:
            List of action effects with before/after states
        """
        effects = []
        
        actions = game_session_data.get('action_sequence', [])
        frame_states = game_session_data.get('frame_states', [])
        
        if len(frame_states) < len(actions) + 1:
            # Need initial frame + frame after each action
            return effects
        
        for i, action in enumerate(actions):
            before_frame = frame_states[i]
            after_frame = frame_states[i + 1]
            
            # Analyze what changed
            before_analysis = self.visual_engine.analyze_grid(before_frame)
            after_analysis = self.visual_engine.analyze_grid(after_frame)
            
            effect = {
                'action': action,
                'changes': self._compute_changes(before_analysis, after_analysis),
                'score_delta': 0  # Would need score tracking per action
            }
            
            effects.append(effect)
        
        return effects
    
    def _compute_changes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Compute what changed between two visual analyses"""
        changes = {
            'color_change': after['colors']['unique_colors'] != before['colors']['unique_colors'],
            'shape_count_change': len(after['shapes']) != len(before['shapes']),
            'symmetry_change': after['symmetry']['has_any_symmetry'] != before['symmetry']['has_any_symmetry'],
            'complexity_change': after['complexity']['overall_complexity'] - before['complexity']['overall_complexity']
        }
        return changes
    
    def _extract_preconditions(self, visual_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract key preconditions from visual features
        
        Returns:
            List of conditions that must be true for rule to apply
        """
        preconditions = []
        
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
                'operator': 'approximately',  # Allow some variation
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
    
    def _abstract_action_sequence(self, actions: List[Dict[str, Any]], 
                                  initial_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create abstract action template from concrete action sequence
        
        Returns:
            Action template that can be instantiated for new grids
        """
        action_types = [a.get('action_type', a.get('type', 0)) for a in actions]
        
        # Count action type usage
        action_counts = {}
        for atype in action_types:
            action_counts[atype] = action_counts.get(atype, 0) + 1
        
        # Check if coordinates are used (ACTION6)
        has_coordinates = any(a.get('action_type', 0) == 6 for a in actions)
        
        template = {
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
            
            # Filter out any None values and convert to proper type
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
    
    def _infer_coordinate_strategy(self, coords: List[Tuple[int, int]], 
                                   visual_features: Dict[str, Any]) -> str:
        """Infer what coordinate strategy was used"""
        if not coords:
            return 'none'
        
        # Check if targeting shapes
        shapes = visual_features.get('shapes', [])
        if shapes:
            # Check if coordinates near shape centers
            shape_centers = [tuple(s['center']) for s in shapes]
            near_centers = sum(1 for c in coords if any(
                abs(c[0] - sc[0]) <= 1 and abs(c[1] - sc[1]) <= 1
                for sc in shape_centers
            ))
            
            if near_centers / len(coords) > 0.5:
                return 'target_shape_centers'
        
        # Check if following a pattern
        if len(coords) >= 3:
            # Linear pattern?
            dx_values = [coords[i+1][0] - coords[i][0] for i in range(len(coords)-1)]
            dy_values = [coords[i+1][1] - coords[i][1] for i in range(len(coords)-1)]
            
            if len(set(dx_values)) == 1 and len(set(dy_values)) == 1:
                return 'linear_pattern'
        
        # Check for symmetry-based targeting
        if visual_features['symmetry']['has_any_symmetry']:
            return 'symmetry_aligned'
        
        return 'exploratory'
    
    def _calculate_initial_confidence(self, game_session_data: Dict[str, Any]) -> float:
        """Calculate initial confidence for newly extracted rule"""
        # Base confidence from win
        confidence = 0.5
        
        # Bonus if actions were efficient
        actions_taken = len(game_session_data.get('action_sequence', []))
        if actions_taken < 50:
            confidence += 0.2
        
        # Bonus if score was high
        score = game_session_data.get('score_achieved', 0)
        if score > 0.5:  # Assuming normalized score
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _create_visual_signature(self, visual_features: Dict[str, Any]) -> str:
        """
        Create compact visual signature for quick rule matching
        
        Returns:
            String signature summarizing key visual features
        """
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
    
    def match_rule_to_game(self, rule: Dict[str, Any], 
                          current_frame: List[List[int]]) -> Tuple[bool, float]:
        """
        Check if learned rule applies to new game
        
        Args:
            rule: Learned rule dictionary
            current_frame: Initial frame of new game
            
        Returns:
            (matches, confidence_score) tuple
        """
        # Analyze current game
        current_features = self.visual_engine.analyze_grid(current_frame)
        
        # Check each precondition
        preconditions = rule.get('preconditions', [])
        if not preconditions:
            return False, 0.0
        
        matches = 0
        total_weight = 0.0
        
        for condition in preconditions:
            weight = condition.get('confidence', 1.0)
            total_weight += weight
            
            if self._check_condition(condition, current_features):
                matches += weight
        
        if total_weight == 0:
            return False, 0.0
        
        confidence = matches / total_weight
        
        # Rule matches if confidence > 0.6
        return confidence > 0.6, confidence
    
    def _check_condition(self, condition: Dict[str, Any], 
                        visual_features: Dict[str, Any]) -> bool:
        """Check if a single condition is satisfied"""
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
    
    def get_applicable_rules(self, current_frame: List[List[int]], 
                            agent_id: Optional[str] = None,
                            min_confidence: float = 0.6) -> List[Tuple[Dict, float]]:
        """
        Get all rules that apply to current game
        
        Args:
            current_frame: Initial game frame
            agent_id: Optional agent ID to filter rules
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of (rule, confidence) tuples sorted by confidence
        """
        # Get rules from database
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
        
        applicable = []
        
        for rule_data in rules:
            # Parse JSON fields
            rule = dict(rule_data)
            rule['preconditions'] = json.loads(rule.get('preconditions', '[]'))
            rule['action_template'] = json.loads(rule.get('action_template', '{}'))
            
            # Check if rule matches
            matches, confidence = self.match_rule_to_game(rule, current_frame)
            
            if matches and confidence >= min_confidence:
                applicable.append((rule, confidence))
        
        # Sort by confidence
        applicable.sort(key=lambda x: x[1], reverse=True)
        
        return applicable
    
    def update_rule_success(self, rule_id: str, success: bool, target_game_id: str):
        """
        Update rule after transfer attempt
        
        Args:
            rule_id: Rule ID
            success: Whether rule worked on new game
            target_game_id: Game ID where rule was tried
        """
        if success:
            # Increment success count, update confidence
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
                applicable_games = json.loads(rule[0]['applicable_games'])
                if target_game_id not in applicable_games:
                    applicable_games.append(target_game_id)
                    self.db.execute_query("""
                        UPDATE learned_rules
                        SET applicable_games = ?
                        WHERE rule_id = ?
                    """, (json.dumps(applicable_games), rule_id))
        else:
            # Increment failure count, reduce confidence
            self.db.execute_query("""
                UPDATE learned_rules
                SET failure_count = failure_count + 1,
                    confidence = MAX(confidence - 0.1, 0.0)
                WHERE rule_id = ?
            """, (rule_id,))
        
        # Log transfer attempt
        self._log_transfer_attempt(rule_id, target_game_id, success)
    
    def _store_rule(self, rule: Dict[str, Any]):
        """Store rule in database (Rule 2)"""
        self.db.execute_query("""
            INSERT INTO learned_rules (
                rule_id, agent_id, source_game_id, preconditions, action_template,
                confidence, success_count, failure_count, applicable_games,
                transferred_successfully, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            rule['created_at']
        ))
    
    def _log_transfer_attempt(self, rule_id: str, target_game_id: str, success: bool):
        """Log rule transfer attempt to database"""
        transfer_id = f"transfer_{uuid.uuid4().hex[:12]}"
        
        # Get rule details
        rule = self.db.execute_query(
            "SELECT source_game_id, confidence FROM learned_rules WHERE rule_id = ?",
            (rule_id,)
        )
        
        if rule:
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
    
    def _log_error(self, message: str):
        """Log error to database (Rule 2)"""
        try:
            self.db.execute_query(
                """INSERT INTO system_logs (level, component, message, timestamp)
                   VALUES (?, ?, ?, ?)""",
                ('ERROR', 'rule_induction_engine', message, datetime.now().isoformat())
            )
        except:
            pass  # Don't fail if logging fails


# [CHECKPOINT: RULE INDUCTION ENGINE IMPLEMENTATION COMPLETE]
# Next: Extend database schema with new tables for meta-learning
