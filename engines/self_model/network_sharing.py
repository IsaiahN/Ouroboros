"""
Network Sharing Module
======================

Handles sharing discoveries to the network and retrieving network knowledge.

Core methods:
- share_control_discovery_to_network: Share "I am this object" discoveries
- learn_from_movement_correlation: Learn object control from action-movement
- get_network_control_hypotheses: Retrieve validated hypotheses from network
- validate_control_hypothesis: Update hypothesis reliability after use
- synthesize_composite_hypothesis: Tier 6 synthesis of multiple hypotheses

This module implements the "thought process colony" for self-model knowledge:
- Tier 1: Observation (discoveries made during gameplay)
- Tier 2: Sharing (this module - broadcast to network)
- Tier 3: Validation (other agents validate)
- Tier 4: Usage (agents use hypotheses)
- Tier 5: Selection (hypotheses compete by outcome)
- Tier 6: Synthesis (combine hypotheses into composites)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class NetworkSharingEngine:
    """
    Handles network-level knowledge sharing for self-model discoveries.
    
    Implements the thought process colony pattern:
    - Individual agents make discoveries
    - Discoveries are shared to network as hypotheses
    - Other agents validate hypotheses
    - Best hypotheses rise through selection
    - Top hypotheses get synthesized into composites
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize network sharing engine.
        
        Args:
            db_path: Path to database
        """
        from database_interface import DatabaseInterface
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        # Tables should already exist from complete_database_schema.sql
        # Just verify key table exists
        try:
            self.db.execute_query("""
                SELECT 1 FROM network_object_control_hypotheses LIMIT 1
            """)
        except Exception:
            logger.warning("[NETWORK] network_object_control_hypotheses table may not exist")
    
    def _generate_hypothesis_id(self) -> str:
        """Generate unique hypothesis ID."""
        return f"hyp_{uuid.uuid4().hex[:12]}"
    
    def _create_pattern_signature(
        self,
        controlled_objects: List[str],
        action_response_map: Dict[str, Any]
    ) -> str:
        """Create deduplication signature for control pattern."""
        # Sort for consistency
        obj_str = ",".join(sorted(controlled_objects))
        action_str = json.dumps(action_response_map, sort_keys=True)
        return f"{obj_str}|{action_str}"
    
    def share_control_discovery_to_network(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, List[str]],
        confidence: float,
        generation: int = 0
    ) -> Optional[str]:
        """
        Share "I am this object" discovery to network for other agents to validate.
        
        This is the core of network-level self-model learning:
        - Agent discovers which objects it controls
        - Shares hypothesis to network
        - Other agents validate during their gameplay
        - High-reliability patterns become network knowledge
        
        Args:
            agent_id: Discovering agent
            game_id: Game where discovery was made
            level: Level number
            controlled_objects: Coordinates of controlled objects
            action_response_map: Maps action types to responding coordinates
            confidence: Discovery confidence
            generation: Current evolution generation
        
        Returns:
            hypothesis_id if shared, None if already exists or low confidence
        """
        if confidence < 0.6 or not controlled_objects:
            return None
        
        # Extract game type (e.g., 'ft09' from 'ft09-abc123')
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Create control pattern signature for deduplication
        pattern_signature = self._create_pattern_signature(
            controlled_objects, action_response_map
        )
        
        # Check if similar hypothesis already exists
        existing = self.db.execute_query("""
            SELECT hypothesis_id, validation_attempts, reliability_score
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND control_pattern = ? AND is_active = TRUE
        """, (game_type, level, pattern_signature))
        
        if existing:
            # Update existing with validation attempt
            return existing[0]['hypothesis_id']
        
        # Create new hypothesis
        hypothesis_id = f"oc_{game_type}_L{level}_{uuid.uuid4().hex[:8]}"
        
        self.db.execute_query("""
            INSERT INTO network_object_control_hypotheses
            (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
             discovered_by_agent, discovery_generation, reliability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hypothesis_id,
            game_type,
            level,
            pattern_signature,
            json.dumps(action_response_map),
            agent_id,
            generation,
            confidence  # Initial reliability = discovery confidence
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} shared 'I am object' hypothesis: "
            f"{hypothesis_id} for {game_type} L{level} ({len(controlled_objects)} objects)"
        )
        
        return hypothesis_id
    
    def learn_from_movement_correlation(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        action: str,
        direction: str,
        controlled_color: int,
        generation: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Learn object control from action-movement correlation.
        
        When frame_changes show "color_X moved [direction]" after an action
        that corresponds to that direction, we learn that we control color_X.
        
        This is the core "I am this object" learning mechanism.
        Returns discovery info for immediate exploitation.
        
        Args:
            agent_id: Agent making the discovery
            game_id: Game identifier
            level: Level number
            action: Action taken (e.g., ACTION3)
            direction: Direction object moved (e.g., "left")
            controlled_color: Color number that moved
            generation: Current evolution generation
            
        Returns:
            Discovery dict if new/validated discovery, None if contradiction.
            Dict contains: controlled_color, action, direction, is_validated, 
                          reliability_score, observation_count, hypothesis_id
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Create control pattern
        control_pattern = {
            'discovery_type': 'movement_correlation',
            'controlled_color': controlled_color,
            'action': action,
            'direction': direction
        }
        
        # Build action-response map
        action_response = {action: direction}
        
        # Check if we already have this knowledge
        existing = self.db.execute_query("""
            SELECT hypothesis_id, reliability_score, validation_attempts
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND control_pattern LIKE ? AND is_active = TRUE
        """, (game_type, level, f'%"controlled_color": {controlled_color}%'))
        
        if existing:
            row = existing[0]
            current_attempts = row['validation_attempts'] or 0
            
            # Check for contradiction
            try:
                existing_pattern = self.db.execute_query("""
                    SELECT action_response_map FROM network_object_control_hypotheses
                    WHERE hypothesis_id = ?
                """, (row['hypothesis_id'],))
                if existing_pattern:
                    existing_responses = json.loads(
                        existing_pattern[0]['action_response_map']
                    )
                    expected_direction = existing_responses.get(action)
                    
                    if expected_direction and expected_direction != direction:
                        # CONTRADICTION: Same action, different direction
                        self.db.execute_query("""
                            UPDATE network_object_control_hypotheses
                            SET validation_attempts = validation_attempts + 1,
                                reliability_score = MAX(0.1, reliability_score - 0.15),
                                last_validated = CURRENT_TIMESTAMP
                            WHERE hypothesis_id = ?
                        """, (row['hypothesis_id'],))
                        logger.warning(
                            f"[MOVEMENT] CONTRADICTION: {action} moved color_{controlled_color} "
                            f"{direction} but expected {expected_direction} - lowering reliability"
                        )
                        return None
            except Exception as e:
                logger.debug(f"Pattern comparison failed: {e}")
            
            # Consistent observation - increase reliability
            new_reliability = min(0.95, row['reliability_score'] + 0.1)
            self.db.execute_query("""
                UPDATE network_object_control_hypotheses
                SET reliability_score = ?,
                    validation_attempts = validation_attempts + 1,
                    validation_successes = validation_successes + 1,
                    last_validated = CURRENT_TIMESTAMP
                WHERE hypothesis_id = ?
            """, (new_reliability, row['hypothesis_id']))
            
            is_validated = current_attempts + 1 >= 3
            if is_validated:
                logger.info(
                    f"[MOVEMENT] VALIDATED (x{current_attempts + 1}): color_{controlled_color} "
                    f"responds to {action} with {direction} (reliability {new_reliability:.2f})"
                )
            
            return {
                'controlled_color': controlled_color,
                'action': action,
                'direction': direction,
                'is_validated': is_validated,
                'reliability_score': new_reliability,
                'observation_count': current_attempts + 1,
                'hypothesis_id': row['hypothesis_id']
            }
        else:
            # Create new hypothesis with LOW initial confidence
            hypothesis_id = self._generate_hypothesis_id()
            self.db.execute_query("""
                INSERT INTO network_object_control_hypotheses
                (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
                 discovered_by_agent, discovery_generation, reliability_score, discovery_method,
                 validation_attempts, validation_successes)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.3, 'movement_correlation', 1, 1)
            """, (
                hypothesis_id, game_type, level, json.dumps(control_pattern),
                json.dumps(action_response), agent_id, generation
            ))
            logger.debug(
                f"[MOVEMENT] Observation 1/3: {action} may control color_{controlled_color} "
                f"(needs 2 more consistent observations)"
            )
            
            return {
                'controlled_color': controlled_color,
                'action': action,
                'direction': direction,
                'is_validated': False,
                'reliability_score': 0.3,
                'observation_count': 1,
                'hypothesis_id': hypothesis_id
            }
    
    def get_network_control_hypotheses(
        self,
        game_id: str,
        level: int,
        min_reliability: float = 0.3,
        include_unvalidated: bool = True
    ) -> List[Dict]:
        """
        Get network-validated "I am this object" hypotheses for a game/level.
        
        Use this to bootstrap agent self-model with network knowledge.
        Implements Tier 5 - Selection: Order by outcome (best_score_achieved)
        
        Args:
            game_id: Game identifier
            level: Level number
            min_reliability: Minimum reliability score to return
            include_unvalidated: If True, include fresh hypotheses for bootstrapping
        
        Returns:
            List of hypothesis dictionaries with control patterns and reliability
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Get validated hypotheses (high confidence)
        results = self.db.execute_query("""
            SELECT 
                hypothesis_id,
                control_pattern,
                action_response_map,
                reliability_score,
                validation_attempts,
                validation_successes,
                validated_by_win,
                COALESCE(best_score_achieved, 0) as best_score_achieved,
                0 as is_bootstrap
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND is_active = TRUE 
                  AND reliability_score >= ?
                  AND (validation_attempts >= 3 OR validated_by_win = TRUE)
            ORDER BY validated_by_win DESC, 
                     best_score_achieved DESC, 
                     reliability_score DESC
            LIMIT 5
        """, (game_type, level, min_reliability))
        
        # COLD-START BOOTSTRAP: Include fresh hypotheses for testing
        if include_unvalidated and (not results or len(results) < 3):
            bootstrap_results = self.db.execute_query("""
                SELECT 
                    hypothesis_id,
                    control_pattern,
                    action_response_map,
                    reliability_score,
                    validation_attempts,
                    validation_successes,
                    validated_by_win,
                    COALESCE(best_score_achieved, 0) as best_score_achieved,
                    1 as is_bootstrap
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND level_number = ? 
                      AND is_active = TRUE 
                      AND validation_attempts < 3
                      AND validated_by_win = FALSE
                ORDER BY reliability_score DESC, discovered_at DESC
                LIMIT 2
            """, (game_type, level))
            
            if bootstrap_results:
                existing_ids = {r['hypothesis_id'] for r in (results or [])}
                for br in bootstrap_results:
                    if br['hypothesis_id'] not in existing_ids:
                        results = (results or []) + [br]
        
        hypotheses = []
        for row in results or []:
            controlled_objects = self._parse_control_pattern_to_colors(
                row['control_pattern']
            )
            
            hypotheses.append({
                'hypothesis_id': row['hypothesis_id'],
                'controlled_objects': controlled_objects,
                'action_response_map': json.loads(row['action_response_map']) 
                    if row['action_response_map'] else {},
                'reliability': row['reliability_score'],
                'validation_count': row['validation_attempts'],
                'success_rate': row['validation_successes'] / max(1, row['validation_attempts']),
                'validated_by_win': row['validated_by_win'],
                'best_score_achieved': row['best_score_achieved'],
                'is_bootstrap': row.get('is_bootstrap', 0) == 1
            })
        
        # TIER 6 - SYNTHESIS: Try composite if no high-confidence hypotheses
        if len(hypotheses) >= 2 and all(h['reliability'] < 0.8 for h in hypotheses):
            composite = self.synthesize_composite_hypothesis(game_id, level)
            if composite and composite.get('hypothesis_id') not in [
                h['hypothesis_id'] for h in hypotheses
            ]:
                hypotheses.insert(0, {
                    'hypothesis_id': composite['hypothesis_id'],
                    'controlled_objects': composite.get('control_pattern', '').split(',') 
                        if isinstance(composite.get('control_pattern'), str) else [],
                    'action_response_map': composite.get('action_map', {}),
                    'reliability': composite.get('reliability', 0.5),
                    'validation_count': 0,
                    'success_rate': 0.0,
                    'validated_by_win': False,
                    'best_score_achieved': 0,
                    'is_composite': True
                })
        
        return hypotheses
    
    def validate_control_hypothesis(
        self,
        hypothesis_id: str,
        success: bool,
        validated_by_win: bool = False,
        score_achieved: Optional[int] = None
    ) -> None:
        """
        Record validation result for a network control hypothesis.
        
        Called when an agent uses a network hypothesis and succeeds/fails.
        Updates Bayesian reliability score.
        
        Args:
            hypothesis_id: Hypothesis being validated
            success: Whether the hypothesis helped (True) or failed (False)
            validated_by_win: Whether validation came from level/game win
            score_achieved: Score achieved while using this hypothesis
        """
        # Get current stats
        current = self.db.execute_query("""
            SELECT validation_attempts, validation_successes, validation_failures, 
                   reliability_score, COALESCE(best_score_achieved, 0) as best_score
            FROM network_object_control_hypotheses
            WHERE hypothesis_id = ?
        """, (hypothesis_id,))
        
        if not current:
            return
        
        row = current[0]
        attempts = row['validation_attempts'] + 1
        successes = row['validation_successes'] + (1 if success else 0)
        failures = row['validation_failures'] + (0 if success else 1)
        
        # Bayesian reliability update with prior
        prior_successes = 1
        prior_total = 2
        reliability = (successes + prior_successes) / (attempts + prior_total)
        
        # Update best score if this attempt was better
        best_score = row['best_score']
        if score_achieved is not None and score_achieved > best_score:
            best_score = score_achieved
        
        # Mark validated_by_win if this validation was from a win
        win_flag = validated_by_win or row.get('validated_by_win', False)
        
        # Deactivate if reliability drops too low
        is_active = reliability >= 0.2
        
        self.db.execute_query("""
            UPDATE network_object_control_hypotheses
            SET validation_attempts = ?,
                validation_successes = ?,
                validation_failures = ?,
                reliability_score = ?,
                validated_by_win = ?,
                best_score_achieved = ?,
                is_active = ?,
                last_validated = CURRENT_TIMESTAMP
            WHERE hypothesis_id = ?
        """, (
            attempts, successes, failures, reliability, 
            win_flag, best_score, is_active, hypothesis_id
        ))
        
        if not is_active:
            logger.info(
                f"[NETWORK] Control hypothesis {hypothesis_id} deactivated "
                f"(reliability: {reliability:.2f})"
            )
    
    def synthesize_composite_hypothesis(
        self,
        game_id: str,
        level: int
    ) -> Optional[Dict]:
        """
        TIER 6 - SYNTHESIS: Combine validated hypotheses into composite strategies.
        
        When multiple validated hypotheses exist for a game/level:
        1. Queries all validated hypotheses
        2. Identifies complementary patterns (e.g., control + goal)
        3. Creates a composite hypothesis combining them
        4. Stores composite with references to source hypotheses
        
        Args:
            game_id: Game identifier
            level: Level number
            
        Returns:
            Composite hypothesis dict if synthesis successful, None otherwise
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Get all validated hypotheses for this game/level
        validated = self.db.execute_query("""
            SELECT 
                hypothesis_id,
                control_pattern,
                action_response_map,
                reliability_score,
                validation_attempts,
                best_score_achieved
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ?
                  AND is_active = TRUE
                  AND reliability_score >= 0.5
                  AND (validation_attempts >= 3 OR validated_by_win = TRUE)
            ORDER BY best_score_achieved DESC, reliability_score DESC
            LIMIT 10
        """, (game_type, level))
        
        if not validated or len(validated) < 2:
            return None
        
        # Group hypotheses by pattern type
        control_hypotheses = []
        
        for row in validated:
            try:
                action_map = json.loads(row['action_response_map']) \
                    if row['action_response_map'] else {}
                hypothesis = {
                    'id': row['hypothesis_id'],
                    'control_pattern': row['control_pattern'],
                    'action_map': action_map,
                    'reliability': row['reliability_score'],
                    'best_score': row.get('best_score_achieved', 0)
                }
                
                # Control hypotheses have directional mappings
                if any(k in str(action_map) for k in [
                    'up', 'down', 'left', 'right', 
                    'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'
                ]):
                    control_hypotheses.append(hypothesis)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if not control_hypotheses:
            return None
        
        best_control = control_hypotheses[0]
        
        # Check if composite already exists
        composite_id = f"composite_{game_type}_{level}_{best_control['id'][:8]}"
        existing = self.db.execute_query("""
            SELECT hypothesis_id FROM network_object_control_hypotheses
            WHERE hypothesis_id = ?
        """, (composite_id,))
        
        if existing:
            return {
                'hypothesis_id': composite_id,
                'is_composite': True,
                'source_hypotheses': [best_control['id']],
                'reliability': best_control['reliability']
            }
        
        # Build composite action map
        composite_action_map = dict(best_control['action_map'])
        source_ids = [best_control['id']]
        
        for h in control_hypotheses[1:3]:
            for key, value in h['action_map'].items():
                if key not in composite_action_map:
                    composite_action_map[key] = value
                    source_ids.append(h['id'])
        
        # Calculate composite reliability
        total_weight = sum(h['reliability'] for h in control_hypotheses[:3])
        composite_reliability = total_weight / min(3, len(control_hypotheses))
        
        # Store composite hypothesis
        try:
            self.db.execute_query("""
                INSERT INTO network_object_control_hypotheses
                (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
                 discovered_by_agent, discovery_generation, validation_attempts, 
                 validation_successes, reliability_score, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, TRUE)
            """, (
                composite_id,
                game_type,
                level,
                best_control['control_pattern'],
                json.dumps(composite_action_map),
                f"synthesis_from_{len(source_ids)}_sources",
                0,  # generation
                composite_reliability
            ))
            
            logger.info(
                f"[TIER-6] Synthesized composite hypothesis {composite_id} "
                f"from {len(source_ids)} sources"
            )
            
            return {
                'hypothesis_id': composite_id,
                'is_composite': True,
                'source_hypotheses': source_ids,
                'control_pattern': best_control['control_pattern'],
                'action_map': composite_action_map,
                'reliability': composite_reliability
            }
        except Exception as e:
            logger.debug(f"Failed to store composite hypothesis: {e}")
            return None
    
    def _parse_control_pattern_to_colors(self, control_pattern: str) -> List[str]:
        """
        Parse control_pattern from database into color-based identifiers.
        
        Handles multiple formats:
        1. Old coordinate list: ["x:4,y:10", "x:5,y:10"]
        2. Movement correlation dict: {"controlled_color": 9}
        3. New color list: ["moveable_color_9", "toggleable_color_12"]
        
        Args:
            control_pattern: JSON string from database
            
        Returns:
            List of color-based identifiers
        """
        if not control_pattern:
            return []
        
        try:
            pattern = json.loads(control_pattern)
            
            # Format 2: Movement correlation dict
            if isinstance(pattern, dict):
                if 'controlled_color' in pattern:
                    color = pattern['controlled_color']
                    return [f"moveable_color_{color}"]
                if 'effect_type' in pattern and 'color_before' in pattern:
                    color = pattern['color_before']
                    effect = pattern['effect_type']
                    return [f"{effect}_color_{color}"]
            
            # Format 3: Already color-based list
            if isinstance(pattern, list):
                if all(isinstance(x, str) and 'color_' in x for x in pattern):
                    return pattern
                # Format 1: Coordinate list - return as-is for now
                return pattern
            
        except (json.JSONDecodeError, TypeError):
            pass
        
        return []


__all__ = ['NetworkSharingEngine']
