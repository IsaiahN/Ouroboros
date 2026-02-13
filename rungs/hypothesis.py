"""
Hypothesis Rungs - Form and test theories
=========================================
Extracted from decision_rung_system.py Phase 4.2.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from rungs.base import (
    Action6CoordinateProvider,
    DecisionRung,
    KnowledgeProvenance,
    RungResult,
    filter_available_actions,
    get_available_action_weights,
    get_available_actions_list,
    get_random_available_action,
    is_action_available,
    validate_action,
)

logger = logging.getLogger(__name__)


def _get_frame(game_state: Any) -> Any:
    """Extract frame from game_state whether it's a dict or object."""
    if isinstance(game_state, dict):
        return game_state.get('frame')
    return getattr(game_state, 'frame', None)


class ScientificMethodRung(DecisionRung):
    """Theory formation and testing - HYPOTHESIS"""
    name = "scientific_method"
    category = "hypothesis"
    default_priority = 12
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            theory_stage = sme.get_theory_stage() if hasattr(sme, 'get_theory_stage') else 'exploring'

            if theory_stage == 'contradicted':
                # Force exploration/revision using available movement actions
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                return RungResult(
                    action=random.choice(exploration_actions),
                    confidence=0.7,
                    reason=f"Theory contradicted - forcing exploration",
                    metadata={'theory_stage': theory_stage},
                    resolved_questions=['does_hypothesis_hold'],
                )
            elif theory_stage == 'speculating':
                # Boost exploration using available movement actions
                movement_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                return RungResult(
                    confidence=0.3,
                    weights={a: 1.2 for a in movement_actions},  # Boost available movement
                    reason=f"Speculating - exploration boosted",
                    metadata={'theory_stage': theory_stage},
                    resolved_questions=['hypothesis_speculating'],
                )
            return RungResult(
                metadata={'theory_stage': theory_stage},
                resolved_questions=['theory_stage_observed'],
            )
        except Exception as e:
            return RungResult(reason=f"Scientific method failed: {e}")


class TwoStreamsRung(DecisionRung):
    """Stream A (private) vs Stream B (network) conflict detection - HYPOTHESIS

    Implements the two-stream consciousness model from the unified theory:
    - Stream A: Private memory (agent's personal experience)
    - Stream B: Collective wisdom (network knowledge)

    Uses i_thread engine for stream weights (wA, wB).
    """
    name = "two_streams"
    category = "hypothesis"
    default_priority = 30
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        i_thread = self.engines.i_thread
        agent_id = context.get('agent_id', '')

        # Default weights if i_thread not available
        wA, wB = 0.5, 0.5

        try:
            if i_thread and agent_id:
                state = i_thread.get_state(agent_id)
                if state:
                    wA = state.w_a
                    wB = state.w_b

            stream_a_actions = context.get('stream_a_proposals', set())
            stream_b_actions = context.get('stream_b_proposals', set())

            conflict = stream_a_actions and stream_b_actions and stream_a_actions != stream_b_actions

            if conflict:
                # Conflict = learning signal
                return RungResult(
                    confidence=0.5,
                    reason=f"Stream conflict: A={stream_a_actions}, B={stream_b_actions}, wA={wA:.2f}",
                    metadata={'conflict': True, 'wA': wA, 'wB': wB, 'stream_a': list(stream_a_actions), 'stream_b': list(stream_b_actions)}
                )
            return RungResult(metadata={'conflict': False, 'wA': wA, 'wB': wB})
        except Exception as e:
            return RungResult(reason=f"Two streams failed: {e}")


class MetacognitivePredictionRung(DecisionRung):
    """Make predictions, learn from errors - HYPOTHESIS"""
    name = "metacognitive_prediction"
    category = "hypothesis"
    default_priority = 18
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Use metacognitive_engine which has get_current_prediction()
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            prediction = me.get_current_prediction() if hasattr(me, 'get_current_prediction') else None

            if prediction:
                action = prediction.get('test_action')
                # CRITICAL: Validate action is available in this game
                if action and is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=prediction.get('confidence', 0.3),
                        reason=f"Testing prediction: {prediction.get('hypothesis', '?')}",
                        metadata={'prediction': prediction}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Metacognitive prediction failed: {e}")


class TheoryGateRung(DecisionRung):
    """Working theory must score proposals, contradicted = force exploration - FINALIZER

    Uses scientific_method_engine to check current theory status and force
    exploration when theory is contradicted.
    """
    name = "theory_gate"
    category = "hypothesis"
    default_priority = 32
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            # Get game context for theory lookup
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # get_working_theory requires game_type and level_number
            theory = None
            if hasattr(sme, 'get_working_theory') and game_type:
                theory = sme.get_working_theory(game_type, level)

            if theory and theory.get('stage') == 'contradicted':
                # Force exploration/revision
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6'], context
                )
                action = random.choice(exploration_actions)
                return RungResult(
                    action=action,
                    confidence=0.7,
                    reason=f"Theory contradicted: forcing exploration with {action}",
                    metadata={'theory': theory, 'forced_exploration': True}
                )
            return RungResult(metadata={'theory_stage': theory.get('stage') if theory else 'none'})
        except Exception as e:
            return RungResult(reason=f"Theory gate failed: {e}")


class SensationEngineRung(DecisionRung):
    """Emotional context for actions based on object feelings - HYPOTHESIS"""
    name = "sensation_engine"
    category = "hypothesis"
    default_priority = 33
    confidence_threshold = 0.35

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        se = self.engines.sensation_engine
        if se is None:
            return RungResult()

        try:
            if hasattr(se, 'get_tetrahedral_sensation'):
                sensation = se.get_tetrahedral_sensation(context)

                # Convert sensations to action biases (only for available movement actions)
                weights: Dict[str, float] = {}
                available_movement = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                if sensation.get('approach_score', 0) > 0.5:
                    # Bias toward available movement actions
                    for action in available_movement:
                        weights[action] = 1.0 + sensation['approach_score'] * 0.3
                if sensation.get('threat_level', 0) > 0.5:
                    # Bias away from certain directions
                    threat_direction = sensation.get('threat_direction')
                    if threat_direction and threat_direction in weights:
                        weights[threat_direction] = max(0.1, 1.0 - sensation['threat_level'])

                if weights:
                    return RungResult(
                        confidence=0.4,
                        weights=weights,
                        reason=f"Sensation: approach={sensation.get('approach_score', 0):.2f}, threat={sensation.get('threat_level', 0):.2f}",
                        metadata={'sensation': sensation}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Sensation engine failed: {e}")


class IThreadRung(DecisionRung):
    """Maintain persistent identity, weave stream weights - HYPOTHESIS"""
    name = "i_thread"
    category = "hypothesis"
    default_priority = 31
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ithread = self.engines.i_thread
        if ithread is None:
            return RungResult()

        try:

            # Get stream weights
            wA = ithread.get_wA() if hasattr(ithread, 'get_wA') else 0.5
            wB = ithread.get_wB() if hasattr(ithread, 'get_wB') else 0.5

            # Check for death personas (near cull)
            cull_distance = context.get('cull_distance', 1.0)
            if cull_distance < 0.2 and hasattr(ithread, 'spawn_death_persona'):
                persona = ithread.spawn_death_persona(context.get('agent_role', 'generalist'))
                if persona and persona.get('suggested_action'):
                    action = persona['suggested_action']
                    # CRITICAL: Validate action is available in this game
                    if is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=0.7,
                            reason=f"Death persona ({persona.get('name', 'unknown')}): {persona.get('reason', '')}",
                            metadata={'persona': persona, 'cull_distance': cull_distance}
                        )

            return RungResult(metadata={'wA': wA, 'wB': wB, 'cull_distance': cull_distance})
        except Exception as e:
            return RungResult(reason=f"I-Thread failed: {e}")


class EventUnderstandingRung(DecisionRung):
    """
    Use causal world model to inform decisions.

    This rung builds understanding from frame-to-frame changes:
    - Tracks object movements and interactions
    - Detects collisions, fusions, and other events
    - Attributes causality to actions
    - Classifies the overall process type

    Uses this understanding to:
    - Set context flags for downstream rungs
    - Boost weights for actions that caused productive events
    - Predict continuation of causal chains
    """
    name = "event_understanding"
    category = "hypothesis"
    default_priority = 23  # After orientation, before exploitation
    confidence_threshold = 0.4

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._event_detector: Optional[Any] = None
        self._object_tracker: Optional[Any] = None
        self._event_history: List[Dict] = []  # Recent events for causal chain analysis
        self._db: Optional[Any] = None

    def _get_event_detector(self) -> Optional[Any]:
        """Lazy-load event detector."""
        if self._event_detector is None:
            try:
                from engines.perception.event_detector import EventDetector
                self._event_detector = EventDetector()
            except ImportError:
                pass
        return self._event_detector

    def _get_object_tracker(self) -> Optional[Any]:
        """Lazy-load object tracker."""
        if self._object_tracker is None:
            try:
                from engines.perception.object_tracker import ObjectTracker
                self._object_tracker = ObjectTracker()
            except ImportError:
                pass
        return self._object_tracker

    def _get_db(self) -> Optional[Any]:
        """Lazy-load database interface."""
        if self._db is None:
            try:
                from database_interface import DatabaseInterface
                self._db = DatabaseInterface()
            except ImportError:
                pass
        return self._db

    def _get_recent_events(self, context: Dict[str, Any]) -> List[Dict]:
        """Get recent events from context or database."""
        if 'recent_events' in context:
            return context['recent_events']

        db = self._get_db()
        if db is None:
            return self._event_history[-10:]

        try:
            game_type = context.get('game_type', '')
            result = db.execute_query("""
                SELECT event_type, objects_involved, positions, confidence
                FROM detected_events
                WHERE game_type = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (game_type,))

            return [
                {'type': r['event_type'], 'objects': r['objects_involved'],
                 'positions': r['positions'], 'confidence': r['confidence']}
                for r in (result if result else [])
            ]
        except Exception:
            return self._event_history[-10:]

    def _last_action_caused_productive_event(self, events: List[Dict]) -> bool:
        """Check if the last action caused a productive event."""
        if not events:
            return False

        # Productive events: COLLECTION, TRANSFORMATION toward goal, FUSION
        productive_types = {'COLLECTION', 'TRANSFORMATION', 'FUSION'}

        for event in events[:3]:  # Check recent events
            event_type = event.get('type', event.get('event_type', ''))
            if isinstance(event_type, str) and event_type in productive_types:
                return True
            elif hasattr(event_type, 'value') and event_type.value in productive_types:
                return True

        return False

    def _detected_physics_process(self, events: List[Dict]) -> bool:
        """Check if physics simulation was detected."""
        if not events:
            return False

        movement_count = 0
        for event in events:
            event_type = event.get('type', event.get('event_type', ''))
            if 'MOVEMENT' in str(event_type):
                movement_count += 1

        return movement_count >= 3

    def _get_active_causal_chain(self, events: List[Dict]) -> List[Dict]:
        """Identify active causal chain from recent events."""
        if len(events) < 2:
            return []

        # Look for sequence of related events
        chain = []
        for event in events:
            event_type = str(event.get('type', event.get('event_type', '')))
            if event_type in {'MOVEMENT', 'COLLISION', 'FUSION', 'CHAIN_REACTION'}:
                chain.append(event)
            elif chain:
                break  # Chain broken

        return chain

    def _predict_chain_continuation(self, chain: List[Dict]) -> Optional[str]:
        """Predict what action would continue the causal chain."""
        if not chain:
            return None

        # If last event was a collision, maybe continue pushing
        last_event = chain[-1]
        last_type = str(last_event.get('type', last_event.get('event_type', '')))

        if 'COLLISION' in last_type or 'MOVEMENT' in last_type:
            # Continue in same direction if we have that info
            positions = last_event.get('positions', [])
            if len(positions) >= 2:
                # Calculate movement direction
                try:
                    dy = float(positions[1][0]) - float(positions[0][0])
                    dx = float(positions[1][1]) - float(positions[0][1])

                    if abs(dy) > abs(dx):
                        return 'ACTION2' if dy > 0 else 'ACTION1'  # Down or Up
                    elif abs(dx) > 0:
                        return 'ACTION4' if dx > 0 else 'ACTION3'  # Right or Left
                except (IndexError, TypeError, ValueError):
                    pass

        return None

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        recent_events = self._get_recent_events(context)

        if not recent_events:
            return RungResult()  # No understanding yet

        # Build weight modifiers based on understanding
        weights = get_available_action_weights(context, 1.0)

        # If last action caused productive event, boost similar actions
        if self._last_action_caused_productive_event(recent_events):
            last_action = context.get('last_action')
            if last_action and last_action in weights:
                weights[last_action] = 1.3  # Boost similar actions

        # If physics simulation detected, set context
        if self._detected_physics_process(recent_events):
            context['physics_game_confirmed'] = True

        # If we understand the causal chain, boost actions that extend it
        causal_chain = self._get_active_causal_chain(recent_events)
        if causal_chain:
            next_action = self._predict_chain_continuation(causal_chain)
            if next_action and is_action_available(next_action, context):
                return RungResult(
                    action=next_action,
                    confidence=0.55,
                    reason=f"Continuing causal chain of {len(causal_chain)} events",
                    weights=weights,
                    metadata={
                        'chain_length': len(causal_chain),
                        'last_event_type': str(causal_chain[-1].get('type', '')),
                    }
                )

        return RungResult(weights=weights)


class ResonanceDetectorRung(DecisionRung):
    """Cross-role pattern discovery for objective truth - HYPOTHESIS

    Implements the Resonance Discovery Principle from harmonies theory:
    When agents with radically different biases (Pioneers, Generalists, Exploiters)
    converge on the same pattern, that's evidence of OBJECTIVE TRUTH.

    Resonance detection is the bridge between "widely believed" and "actually true".
    High resonance + high role diversity = structural truth transcending individual bias.
    """
    name = "resonance_detector"
    category = "hypothesis"
    default_priority = 34
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        rd = self.engines.resonance_detector
        if rd is None:
            return RungResult()

        try:
            role = context.get('agent_role', 'generalist')

            # Role-specific query frequencies (from harmonies theory)
            query_probs = {'pioneer': 0.15, 'optimizer': 0.20, 'generalist': 0.30, 'exploiter': 0.10}
            if random.random() > query_probs.get(role, 0.15):
                return RungResult()  # Skip query this time

            if hasattr(rd, 'get_resonant_patterns'):
                # Query patterns with minimum resonance score
                patterns = rd.get_resonant_patterns(min_score=0.6, limit=10)
                if patterns:
                    best = patterns[0]
                    resonance_score = best.get('resonance_score', 0)

                    if resonance_score > 0.6:
                        suggested_action = best.get('suggested_action')
                        # CRITICAL: Validate action is available in this game
                        if not is_action_available(suggested_action, context):
                            return RungResult(reason=f"Resonance pattern suggested unavailable action: {suggested_action}")

                        # Build epistemological provenance
                        # Cross-role resonance is the gold standard for validation
                        role_diversity = best.get('role_diversity', 1)
                        game_types = best.get('game_types', [])

                        provenance = KnowledgeProvenance(
                            detection_source='resonance_patterns',
                            sample_size=role_diversity * len(game_types),
                            agent_diversity=role_diversity,  # Different ROLES = different cognitive biases
                            temporal_spread_generations=0.0,  # Not tracked for resonance
                            validation_type='cross_role_convergence',  # The gold standard
                            positive_outcomes=role_diversity,  # Each role validated
                            negative_outcomes=0,
                            crystallization_stage=4 if role_diversity >= 3 else 3,  # High: crystallized
                            resonance_games=len(game_types),  # How many games share this pattern
                            resonance_score=resonance_score
                        )

                        return RungResult(
                            action=suggested_action,
                            confidence=resonance_score,
                            reason=f"Resonant pattern ({role_diversity} roles, {len(game_types)} games): {best.get('theory_type', 'unknown')}",
                            metadata={
                                'pattern': best,
                                'pattern_hash': best.get('pattern_hash'),
                                'roles_found': best.get('roles_found', []),
                                'game_types': game_types,  # Store the actual list in metadata
                            },
                            provenance=provenance
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Resonance detector failed: {e}")


class InteractableTileDiscoveryRung(DecisionRung):
    """Learn that moving to specific tiles changes agent state - HYPOTHESIS

    For directional games like LS20 where:
    - Walking over tile X changes tool shape (gsu)
    - Walking over tile Y changes tool color (gic)
    - Walking over tile Z changes rotation (bgt)

    This rung:
    1. Tracks frame state BEFORE and AFTER each directional movement
    2. Detects when movement causes state changes BEYOND just position
    3. Maps tile positions to the state changes they cause
    4. Builds a "property modification map" of the level
    5. Suggests revisiting known modifier tiles when current state
       doesn't match the target

    ROOT CAUSE ADDRESSED: LS20 agents never discover that gsu/gic/bgt tiles
    modify the tool's properties. Without this, the 3-property matching
    system is invisible.
    """
    name = "interactable_tile_discovery"
    category = "hypothesis"
    default_priority = 28
    confidence_threshold = 0.4

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # game_key -> {(x, y) -> list of observed state changes}
        self._modifier_map: Dict[str, Dict[Tuple[int, int], List[Dict[str, Any]]]] = {}
        # Track agent position by correlating with frame changes
        self._estimated_position: Optional[Tuple[int, int]] = None
        # Track the "tool state" as a hash of non-position frame elements
        self._last_tool_state_hash: str = ""
        # Track state transitions: (old_state_hash, new_state_hash) -> position
        self._state_transitions: Dict[str, List[Dict[str, Any]]] = {}
        # Known modifier positions per game
        self._known_modifiers: Dict[str, List[Tuple[int, int]]] = {}
        # Count of property changes detected (to know when we've discovered modifiers)
        self._property_changes_detected: Dict[str, int] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        available = context.get('available_actions', [])
        has_directional = any(
            (a in [1, 2, 3, 4] if isinstance(a, int) else a in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'])
            for a in available
        )
        if not has_directional:
            return RungResult()

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        # Merge shared world model causal data (Part 7 unification, Task A3)
        shared_wm = context.get('world_model')
        if shared_wm and isinstance(shared_wm, dict):
            shared_causal = shared_wm.get('causal_map', {})
            if shared_causal:
                if game_key not in self._modifier_map:
                    self._modifier_map[game_key] = {}
                if game_key not in self._known_modifiers:
                    self._known_modifiers[game_key] = []
                for pos_key_str, entry in shared_causal.items():
                    # Parse "x,y" position key from shared causal map
                    try:
                        parts = pos_key_str.split(',')
                        if len(parts) == 2:
                            px, py = int(parts[0]), int(parts[1])
                            pos = (px, py)
                            # Check if this causal entry involves color changes
                            # (which would indicate a modifier tile)
                            obs_list = entry.get('observations', [])
                            has_color_change = False
                            for obs_item in obs_list:
                                for change in obs_item.get('changes', []):
                                    if change.get('old_color') != change.get('new_color'):
                                        has_color_change = True
                                        break
                                if has_color_change:
                                    break
                            if has_color_change and pos not in self._known_modifiers.get(game_key, []):
                                self._known_modifiers.setdefault(game_key, []).append(pos)
                                self._property_changes_detected[game_key] = \
                                    self._property_changes_detected.get(game_key, 0) + 1
                    except (ValueError, IndexError):
                        pass
            # Contribute own discoveries back to shared world model
            if game_key in self._modifier_map and self._modifier_map[game_key]:
                if 'causal_map' not in shared_wm:
                    shared_wm['causal_map'] = {}
                for pos, observations in self._modifier_map[game_key].items():
                    contrib_key = f"{pos[0]},{pos[1]}"
                    if contrib_key not in shared_wm['causal_map']:
                        shared_wm['causal_map'][contrib_key] = {
                            'action': 'movement',
                            'observations': [{'changes': obs.get('state_changes', [])} for obs in observations],
                            'total_observations': len(observations),
                        }

        # If we've discovered modifier tiles, suggest moving toward them
        modifiers = self._known_modifiers.get(game_key, [])
        if modifiers and self._estimated_position:
            # Find nearest unvisited-recently modifier
            ex, ey = self._estimated_position
            nearest = None
            nearest_dist = float('inf')
            for mx, my in modifiers:
                dist = abs(mx - ex) + abs(my - ey)  # Manhattan distance
                if 0 < dist < nearest_dist:
                    nearest_dist = dist
                    nearest = (mx, my)

            if nearest:
                # Suggest direction toward the modifier
                dx = nearest[0] - ex
                dy = nearest[1] - ey

                # Map displacement to action
                if abs(dx) > abs(dy):
                    action = 'ACTION3' if dx < 0 else 'ACTION4'  # left/right
                else:
                    action = 'ACTION1' if dy < 0 else 'ACTION2'  # up/down

                if is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=0.45,
                        reason=f"Moving toward modifier tile at {nearest} (dist={nearest_dist:.0f})",
                        metadata={
                            'target_modifier': nearest,
                            'source': 'interactable_tile_discovery',
                        }
                    )

        # If we haven't found modifiers yet, inject discovery metadata
        changes = self._property_changes_detected.get(game_key, 0)
        if changes > 0:
            return RungResult(
                reason=f"Discovered {changes} property-changing tiles in {game_key}",
                metadata={
                    'modifier_count': changes,
                    'known_modifiers': modifiers,
                }
            )

        return RungResult()

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Detect when movement causes state changes beyond position."""
        if not action or action not in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']:
            return
        if frame_before is None or frame_after is None:
            return

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        try:
            # Compute frame diff
            changes = self._compute_change_regions(frame_before, frame_after)
            if not changes:
                return  # No change = wall hit

            # Separate position changes from state changes
            # Position change: a colored cluster moved (disappeared + reappeared)
            # State change: colors changed WITHOUT corresponding position change
            position_changes = []
            state_changes = []

            for change in changes:
                if change['type'] == 'moved':
                    position_changes.append(change)
                elif change['type'] == 'color_changed':
                    state_changes.append(change)

            # Update estimated position from position changes
            if position_changes:
                # Agent likely moved — update position estimate
                for pc in position_changes:
                    if pc.get('new_pos'):
                        self._estimated_position = pc['new_pos']

            # KEY INSIGHT: If we see state_changes (color modifications) concurrent
            # with position_changes, the tile at the agent's new position likely
            # caused the state change
            if state_changes and self._estimated_position:
                if game_key not in self._modifier_map:
                    self._modifier_map[game_key] = {}
                if game_key not in self._known_modifiers:
                    self._known_modifiers[game_key] = []

                pos = self._estimated_position
                if pos not in self._modifier_map[game_key]:
                    self._modifier_map[game_key][pos] = []

                self._modifier_map[game_key][pos].append({
                    'state_changes': state_changes,
                    'action': action,
                })

                # After 2+ observations at same position, mark as confirmed modifier
                if len(self._modifier_map[game_key][pos]) >= 1:
                    if pos not in self._known_modifiers[game_key]:
                        self._known_modifiers[game_key].append(pos)
                        self._property_changes_detected[game_key] = \
                            self._property_changes_detected.get(game_key, 0) + 1

        except Exception:
            pass

    def _compute_change_regions(
        self, frame_before: Any, frame_after: Any
    ) -> List[Dict[str, Any]]:
        """Analyze frame diff to separate position changes from state changes."""
        changes: List[Dict[str, Any]] = []
        try:
            disappeared: Dict[int, List[Tuple[int, int]]] = {}  # color -> positions
            appeared: Dict[int, List[Tuple[int, int]]] = {}     # color -> positions
            color_changed: List[Tuple[int, int, int, int]] = []  # (x, y, old, new)

            if isinstance(frame_before, list):
                h = min(len(frame_before), len(frame_after))
                for y in range(h):
                    w = min(len(frame_before[y]), len(frame_after[y]))
                    for x in range(w):
                        old = int(frame_before[y][x]) if hasattr(frame_before[y][x], '__int__') else frame_before[y][x]
                        new = int(frame_after[y][x]) if hasattr(frame_after[y][x], '__int__') else frame_after[y][x]
                        if old != new:
                            if old != 0 and new == 0:
                                disappeared.setdefault(old, []).append((x, y))
                            elif old == 0 and new != 0:
                                appeared.setdefault(new, []).append((x, y))
                            elif old != 0 and new != 0:
                                color_changed.append((x, y, old, new))
            else:
                import numpy as np
                fb, fa = np.array(frame_before), np.array(frame_after)
                diff_mask = fb != fa
                ys, xs = np.where(diff_mask)
                for yi, xi in zip(ys, xs):
                    old, new = int(fb[yi, xi]), int(fa[yi, xi])
                    if old != 0 and new == 0:
                        disappeared.setdefault(old, []).append((int(xi), int(yi)))
                    elif old == 0 and new != 0:
                        appeared.setdefault(new, []).append((int(xi), int(yi)))
                    elif old != 0 and new != 0:
                        color_changed.append((int(xi), int(yi), old, new))

            # Classify: same-color disappeared+appeared = movement
            for color in set(disappeared.keys()) & set(appeared.keys()):
                d_pts = disappeared[color]
                a_pts = appeared[color]
                if d_pts and a_pts:
                    d_cx = sum(p[0] for p in d_pts) // len(d_pts)
                    d_cy = sum(p[1] for p in d_pts) // len(d_pts)
                    a_cx = sum(p[0] for p in a_pts) // len(a_pts)
                    a_cy = sum(p[1] for p in a_pts) // len(a_pts)
                    changes.append({
                        'type': 'moved',
                        'color': color,
                        'old_pos': (d_cx, d_cy),
                        'new_pos': (a_cx, a_cy),
                    })

            # Color changes at same position = state modification
            if color_changed:
                changes.append({
                    'type': 'color_changed',
                    'positions': [(x, y) for x, y, _, _ in color_changed],
                    'transitions': [(old, new) for _, _, old, new in color_changed],
                    'count': len(color_changed),
                })

        except Exception:
            pass
        return changes


class GoalRelationshipModelingRung(DecisionRung):
    """Model spatial relationships between game objects for win conditions - HYPOTHESIS

    For puzzle games like VC33 where the win condition involves spatial
    relationships between object types:
    - Passenger blocks (HQB) must be on correct conveyor tracks
    - Tracks are identified by color markers (fZK)
    - Colors must MATCH between passenger and marker

    This rung:
    1. Detect object "groups" by color in the frame
    2. Track which groups change position when actions are taken
    3. Infer goal relationships: "object A needs to be near object B"
    4. Suggest actions that move objects toward their goal positions
    5. Learn from score changes which relationships matter

    ROOT CAUSE ADDRESSED: VC33's win condition requires understanding
    spatial relationships between multiple sprite types simultaneously.
    """
    name = "goal_relationship_modeling"
    category = "hypothesis"
    default_priority = 29
    confidence_threshold = 0.4

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Track object positions over time: game_key -> color -> [(x, y, step)]
        self._object_trajectories: Dict[str, Dict[int, List[Tuple[int, int, int]]]] = {}
        # Track which objects moved in response to clicks
        self._click_object_response: Dict[str, Dict[Tuple[int, int], Set[int]]] = {}
        # Hypothesized goal pairs: (movable_color, target_color)
        self._goal_pairs: Dict[str, List[Tuple[int, int]]] = {}
        # Step counter
        self._step: Dict[str, int] = {}
        # Score at each step
        self._score_history: Dict[str, List[float]] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        available = context.get('available_actions', [])
        if 6 not in available and 'ACTION6' not in available:
            return RungResult()

        frame = _get_frame(game_state)
        if frame is None:
            return RungResult()

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        # Need some click response data first
        responses = self._click_object_response.get(game_key, {})
        if len(responses) < 3:
            return RungResult()

        # Find which click positions move which objects
        # Strategy: click positions that move objects TOWARD color-matched targets
        goal_pairs = self._goal_pairs.get(game_key, [])
        if not goal_pairs:
            # Try to infer goal pairs from color matching
            objects = self._detect_color_groups(frame)
            if len(objects) >= 4:
                # Hypothesis: pairs of same-ish color groups are related
                colors = sorted(objects.keys())
                for i, c1 in enumerate(colors):
                    for c2 in colors[i+1:]:
                        # Colors within small range might be related
                        if abs(c1 - c2) <= 2 and c1 != c2:
                            if game_key not in self._goal_pairs:
                                self._goal_pairs[game_key] = []
                            self._goal_pairs[game_key].append((c1, c2))

        # Suggest clicking positions that historically moved objects
        movable_clicks = []
        for click_pos, moved_colors in responses.items():
            if moved_colors:  # This click moved something
                movable_clicks.append((click_pos, len(moved_colors)))

        if movable_clicks:
            # Pick click that moves the most objects
            movable_clicks.sort(key=lambda x: x[1], reverse=True)
            best_click = movable_clicks[0][0]
            return RungResult(
                action='ACTION6',
                confidence=0.40,
                reason=f"Goal modeling: click at {best_click} moves {movable_clicks[0][1]} object(s)",
                metadata={
                    'x': best_click[0],
                    'y': best_click[1],
                    'source': 'goal_relationship_modeling',
                    'moved_objects': movable_clicks[0][1],
                }
            )

        return RungResult()

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Track object movement in response to actions."""
        if action != 'ACTION6':
            return
        if frame_before is None or frame_after is None:
            return

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        click_x = action_data.get('x', 0)
        click_y = action_data.get('y', 0)
        click_pos = (click_x, click_y)

        self._step[game_key] = self._step.get(game_key, 0) + 1
        step = self._step[game_key]

        # Detect which objects moved
        objects_before = self._detect_color_groups(frame_before)
        objects_after = self._detect_color_groups(frame_after)

        moved_colors: Set[int] = set()
        for color in set(objects_before.keys()) & set(objects_after.keys()):
            before_center = objects_before[color]
            after_center = objects_after[color]
            # Check if center moved significantly (>2 pixels)
            dist = abs(before_center[0] - after_center[0]) + abs(before_center[1] - after_center[1])
            if dist > 2:
                moved_colors.add(color)

                # Record trajectory
                if game_key not in self._object_trajectories:
                    self._object_trajectories[game_key] = {}
                if color not in self._object_trajectories[game_key]:
                    self._object_trajectories[game_key][color] = []
                self._object_trajectories[game_key][color].append(
                    (after_center[0], after_center[1], step)
                )

        # Record which click moved which objects
        if game_key not in self._click_object_response:
            self._click_object_response[game_key] = {}
        self._click_object_response[game_key][click_pos] = moved_colors

    @staticmethod
    def _detect_color_groups(frame: Any) -> Dict[int, Tuple[int, int]]:
        """Detect color groups and their centroids."""
        groups: Dict[int, List[Tuple[int, int]]] = {}
        try:
            if isinstance(frame, list):
                for y, row in enumerate(frame):
                    for x, pixel in enumerate(row):
                        val = int(pixel) if hasattr(pixel, '__int__') else pixel
                        if val != 0:
                            groups.setdefault(val, []).append((x, y))
            else:
                import numpy as np
                arr = np.array(frame)
                for color in np.unique(arr):
                    if color == 0:
                        continue
                    ys, xs = np.where(arr == color)
                    groups[int(color)] = list(zip(xs.tolist(), ys.tolist()))
        except Exception:
            return {}

        # Filter to reasonable-sized groups and compute centroids
        centroids: Dict[int, Tuple[int, int]] = {}
        for color, positions in groups.items():
            size = len(positions)
            if 2 <= size <= 500:
                cx = sum(p[0] for p in positions) // size
                cy = sum(p[1] for p in positions) // size
                centroids[color] = (cx, cy)

        return centroids


class BeliefSystemRung(DecisionRung):
    """Track and use agent beliefs - HYPOTHESIS

    Uses engines/self_model/belief_system.py to:
    1. Query current beliefs about the game
    2. Use high-confidence beliefs to guide action selection
    3. Track belief invalidation cascades

    Beliefs provide persistent knowledge across actions.
    """
    name = "belief_system"
    category = "hypothesis"
    default_priority = 25
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        bs = self.engines.belief_system
        if bs is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            if not game_type:
                return RungResult()

            # Get active beliefs for this game
            if hasattr(bs, 'get_active_beliefs'):
                beliefs = bs.get_active_beliefs(game_type)

                if beliefs:
                    # Find high-confidence beliefs with action implications
                    for belief in beliefs:
                        if belief.get('confidence', 0) > 0.7:
                            # Check if belief suggests an action
                            statement = belief.get('statement', '')
                            if 'ACTION' in statement.upper():
                                # Extract action suggestion
                                for i in range(1, 8):
                                    if f'ACTION{i}' in statement.upper():
                                        return RungResult(
                                            action=f'ACTION{i}',
                                            confidence=belief.get('confidence', 0.5) * 0.7,
                                            reason=f"Belief: {statement[:50]}...",
                                            metadata={'belief': belief}
                                        )

                    # Return belief context for other rungs
                    return RungResult(
                        confidence=0.3,
                        reason=f"Belief system: {len(beliefs)} active beliefs",
                        metadata={'active_beliefs': beliefs[:5]}  # Top 5
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Belief system failed: {e}")


class HypothesisSystemRung(DecisionRung):
    """Manage agent hypotheses - HYPOTHESIS

    Uses engines/social/hypothesis_system.py to:
    1. Get untested hypotheses that need validation
    2. Suggest actions to test hypotheses
    3. Record test results for learning

    This enables agents to actively test their theories.
    """
    name = "hypothesis_system"
    category = "hypothesis"
    default_priority = 26
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        hs = self.engines.hypothesis_system
        if hs is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', '')
            game_type = context.get('game_type', '')

            if not agent_id or not game_type:
                return RungResult()

            # Get testable hypotheses for this game
            if hasattr(hs, 'get_agent_hypotheses'):
                hypotheses = hs.get_agent_hypotheses(agent_id, game_type, status='testing')

                if hypotheses:
                    # Find hypothesis with predicted action
                    for hyp in hypotheses:
                        predicted_action = hyp.get('predicted_action')
                        if predicted_action:
                            return RungResult(
                                action=predicted_action,
                                confidence=0.55,
                                reason=f"Testing hypothesis: {hyp.get('hypothesis_text', '')[:40]}...",
                                metadata={
                                    'hypothesis_id': hyp.get('hypothesis_id'),
                                    'hypothesis': hyp,
                                    'testing_mode': True
                                }
                            )

                        # Check for action sequence
                        sequence = hyp.get('action_sequence')
                        if sequence and isinstance(sequence, list) and len(sequence) > 0:
                            # Get position in sequence
                            seq_pos = context.get('hypothesis_sequence_position', 0)
                            if seq_pos < len(sequence):
                                return RungResult(
                                    action=sequence[seq_pos],
                                    confidence=0.5,
                                    reason=f"Hypothesis sequence step {seq_pos + 1}/{len(sequence)}",
                                    metadata={
                                        'hypothesis_id': hyp.get('hypothesis_id'),
                                        'sequence_position': seq_pos,
                                        'full_sequence': sequence
                                    }
                                )

            # Check for hypothesis suggestions from patterns
            if hasattr(hs, 'suggest_hypothesis_from_pattern'):
                observations = context.get('recent_observations', [])
                if observations:
                    suggestion = hs.suggest_hypothesis_from_pattern(agent_id, game_type, observations)
                    if suggestion:
                        return RungResult(
                            confidence=0.3,
                            reason=f"Hypothesis suggestion: {suggestion.get('suggested_hypothesis', '')[:40]}...",
                            metadata={'hypothesis_suggestion': suggestion}
                        )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Hypothesis system failed: {e}")


class SymbolicTrackerRung(DecisionRung):
    """Track symbolic state for transformation puzzles - HYPOTHESIS

    Uses engines/self_model/symbolic_tracker.py to:
    1. Identify key objects (controllable) vs lock objects (target)
    2. Track symbolic properties: shape, color, orientation
    3. Suggest actions to make key match lock

    Essential for transformation/matching puzzles.
    """
    name = "symbolic_tracker"
    category = "hypothesis"
    default_priority = 24
    confidence_threshold = 0.45

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Private causal map for symbolic observations: game_key -> {pos_key -> effects}
        self._causal_map: Dict[str, Dict[str, Any]] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        st = self.engines.symbolic_tracker
        if st is None:
            return RungResult()

        try:
            frame = _get_frame(game_state)
            if frame is None:
                return RungResult()

            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            game_key = f"{game_type}_L{level}"

            # Merge shared world model causal data (Part 7 unification, Task A3)
            shared_wm = context.get('world_model')
            if shared_wm and isinstance(shared_wm, dict):
                shared_causal = shared_wm.get('causal_map', {})
                if shared_causal and game_key not in self._causal_map:
                    self._causal_map[game_key] = {}
                for pos_key_str, entry in shared_causal.items():
                    if game_key in self._causal_map:
                        if pos_key_str not in self._causal_map[game_key]:
                            # Convert shared format to local format
                            obs_list = entry.get('observations', [])
                            effects = []
                            for obs_item in obs_list:
                                for change in obs_item.get('changes', []):
                                    effects.append(change)
                            if effects:
                                self._causal_map[game_key][pos_key_str] = effects
                # Contribute own observations back to shared world model
                if game_key in self._causal_map and self._causal_map[game_key]:
                    if 'causal_map' not in shared_wm:
                        shared_wm['causal_map'] = {}
                    for pos_key, effects in self._causal_map[game_key].items():
                        if pos_key not in shared_wm['causal_map']:
                            shared_wm['causal_map'][pos_key] = {
                                'action': 'symbolic_transform',
                                'observations': [{'changes': effects}],
                                'total_observations': len(effects),
                            }

            # Identify symbolic objects
            if hasattr(st, 'identify_symbolic_objects'):
                controlled_colors = context.get('controlled_colors', [])
                objects = st.identify_symbolic_objects(frame, controlled_colors)

                keys = objects.get('keys', {})
                locks = objects.get('locks', {})
                tools = objects.get('tools', {})

                if keys and locks:
                    # Check match score
                    if hasattr(st, 'calculate_match_score'):
                        match_score = st.calculate_match_score()

                        if match_score < 1.0:
                            # Not matching - try to identify transformation needed
                            if hasattr(st, 'suggest_transformation'):
                                suggestion = st.suggest_transformation()
                                if suggestion:
                                    action = suggestion.get('action')
                                    if action:
                                        return RungResult(
                                            action=action,
                                            confidence=0.55,
                                            reason=f"Symbolic match {match_score:.0%} - {suggestion.get('reason', 'transform')}",
                                            metadata={
                                                'match_score': match_score,
                                                'keys': keys,
                                                'locks': locks,
                                                'suggestion': suggestion
                                            }
                                        )

                        # Near match - return status
                        return RungResult(
                            confidence=0.3 + match_score * 0.3,
                            reason=f"Symbolic tracking: {len(keys)} keys, {len(locks)} locks, match={match_score:.0%}",
                            metadata={'keys': keys, 'locks': locks, 'tools': tools, 'match_score': match_score}
                        )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Symbolic tracker failed: {e}")


class DeliberationSystemRung(DecisionRung):
    """TRM-inspired iterative refinement - HYPOTHESIS

    Uses scientific_method_engine to get theory hints and deliberation results
    for multi-agent reasoning convergence.
    """
    name = "deliberation_system"
    category = "hypothesis"
    default_priority = 29
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            # Use scientific method engine's theory hint for deliberation guidance
            if hasattr(sme, 'get_active_theory_hint'):
                hint = sme.get_active_theory_hint()

                if hint and hint.get('prediction'):
                    # Theory has a prediction - this is deliberation output
                    action = hint.get('prediction', {}).get('action')
                    confidence = hint.get('weight', 0.5) + 0.3  # Boost confidence

                    # CRITICAL: Validate action is available in this game
                    if action and is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=min(0.9, confidence),
                            reason=f"Deliberation hint: {hint.get('reason', 'theory-guided')}",
                            metadata={'deliberation_hint': hint}
                        )

            # Fallback: Check context for deliberation results from other systems
            deliberation = context.get('deliberation_result')
            if deliberation and deliberation.get('convergence_achieved', False):
                action = deliberation.get('consensus_action')
                # CRITICAL: Validate action is available in this game
                if action and is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=deliberation.get('refinement_confidence', 0.6),
                        reason=f"Deliberation converged: {deliberation.get('refinement_passes', 0)} passes",
                        metadata={'deliberation': deliberation}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Deliberation system failed: {e}")


class HypothesisTestingRung(DecisionRung):
    """Test untested assumptions to validate or disprove them - HYPOTHESIS

    Wires: engines/cognition/metacognition.py:
        - get_untested_assumptions()
        - register_assumption()
        - challenge_assumption()

    Prioritizes actions that would test currently-held assumptions.
    E.g., if agent assumes "ACTION1 moves me up", this rung will
    suggest ACTION1 when testing is needed.
    """
    name = "hypothesis_testing"
    category = "hypothesis"
    default_priority = 19  # After metacognitive_prediction (18)
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # Get untested assumptions for this game/level
            if not hasattr(me, 'get_untested_assumptions'):
                return RungResult()

            untested = me.get_untested_assumptions(game_type, level)

            if not untested:
                return RungResult()

            # Find an assumption we can test
            for assumption in untested:
                assumption_text = assumption.get('assumption_text', '')
                assumption_type = assumption.get('assumption_type', '')
                assumption_id = assumption.get('assumption_id', '')

                # Parse assumption to find testable action
                # E.g., "ACTION1 moves me up" -> suggest ACTION1
                import re
                action_match = re.search(r'ACTION(\d+)', assumption_text.upper())

                if action_match:
                    action = f"ACTION{action_match.group(1)}"
                    # Store assumption_id for challenge_assumption callback
                    context['_testing_assumption_id'] = assumption_id
                    context['_testing_assumption_text'] = assumption_text

                    return RungResult(
                        action=action,
                        confidence=0.55,
                        reason=f"Testing: {assumption_text[:50]}",
                        metadata={
                            'assumption_id': assumption_id,
                            'assumption_type': assumption_type,
                            'assumption_text': assumption_text,
                        }
                    )

                # For non-action assumptions (e.g., "blue is goal"), no direct action
                # but we can store for later validation

            return RungResult(
                confidence=0.1,
                reason=f"{len(untested)} untested assumptions, none directly testable",
                metadata={'untested_count': len(untested)}
            )
        except Exception as e:
            return RungResult(reason=f"Hypothesis testing failed: {e}")


class AssumptionFormationRung(DecisionRung):
    """Form and register assumptions based on observed patterns - HYPOTHESIS

    Wires: engines/cognition/metacognition.py:
        - register_assumption()
        - challenge_assumption()

    Monitors gameplay to detect correlations and form testable assumptions.
    E.g., "When I press ACTION1, the blue object moves up" -> registers assumption.

    This is the WRITE side of the assumption system (HypothesisTestingRung is READ).
    Together they form a complete hypothesis testing loop:
    1. AssumptionFormationRung detects correlation -> register_assumption()
    2. HypothesisTestingRung suggests action to test -> get_untested_assumptions()
    3. After outcome -> challenge_assumption() to validate/invalidate
    """
    name = "assumption_formation"
    category = "hypothesis"
    default_priority = 16  # Before hypothesis_testing
    confidence_threshold = 0.3

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Track recent observations for pattern detection
        self._recent_observations: List[Dict[str, Any]] = []
        self._max_observations = 20

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            agent_id = context.get('agent_id', 'default')
            last_action = context.get('last_action')
            frame_change = context.get('frame_change', {})

            # Skip if no action taken yet
            if not last_action:
                return RungResult()

            # Record observation
            observation = {
                'action': last_action,
                'frame_change': frame_change,
                'score_delta': context.get('score_delta', 0),
                'game_type': game_type,
                'level': level,
            }
            self._recent_observations.append(observation)
            if len(self._recent_observations) > self._max_observations:
                self._recent_observations.pop(0)

            # Need at least 3 observations to detect patterns
            if len(self._recent_observations) < 3:
                return RungResult()

            # Look for consistent action->outcome correlations
            assumptions_formed = []
            action_outcomes: Dict[str, List[Dict]] = {}

            for obs in self._recent_observations:
                action = obs.get('action', '')
                if action:
                    if action not in action_outcomes:
                        action_outcomes[action] = []
                    action_outcomes[action].append(obs)

            # Check each action for consistent outcomes
            for action, outcomes in action_outcomes.items():
                if len(outcomes) >= 2:
                    # Check for consistent positive score
                    positive_scores = [o for o in outcomes if o.get('score_delta', 0) > 0]
                    if len(positive_scores) >= 2:
                        assumption_text = f"{action} consistently gives positive score"
                        if hasattr(me, 'register_assumption'):
                            assumption_id = me.register_assumption(
                                agent_id=agent_id,
                                game_type=game_type,
                                level_number=level,
                                assumption=assumption_text,
                                assumption_type='rule'
                            )
                            assumptions_formed.append(assumption_text)

                    # Check for consistent negative score (form avoidance assumption)
                    negative_scores = [o for o in outcomes if o.get('score_delta', 0) < 0]
                    if len(negative_scores) >= 2:
                        assumption_text = f"{action} consistently causes penalty"
                        if hasattr(me, 'register_assumption'):
                            me.register_assumption(
                                agent_id=agent_id,
                                game_type=game_type,
                                level_number=level,
                                assumption=assumption_text,
                                assumption_type='rule'
                            )
                            assumptions_formed.append(assumption_text)

            if assumptions_formed:
                return RungResult(
                    confidence=0.3,
                    reason=f"Formed {len(assumptions_formed)} assumptions",
                    metadata={'assumptions': assumptions_formed}
                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Assumption formation failed: {e}")



# Registry of rungs in this module
RUNGS = {
    'scientific_method': ScientificMethodRung,
    'two_streams': TwoStreamsRung,
    'metacognitive_prediction': MetacognitivePredictionRung,
    'theory_gate': TheoryGateRung,
    'sensation_engine': SensationEngineRung,
    'i_thread': IThreadRung,
    'event_understanding': EventUnderstandingRung,
    'resonance_detector': ResonanceDetectorRung,
    'interactable_tile_discovery': InteractableTileDiscoveryRung,
    'goal_relationship_modeling': GoalRelationshipModelingRung,
    'belief_system': BeliefSystemRung,
    'hypothesis_system': HypothesisSystemRung,
    'symbolic_tracker': SymbolicTrackerRung,
    'deliberation_system': DeliberationSystemRung,
    'hypothesis_testing': HypothesisTestingRung,
    'assumption_formation': AssumptionFormationRung,
}
