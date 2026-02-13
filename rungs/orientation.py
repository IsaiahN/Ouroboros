"""
Orientation Rungs - Understanding the world
===========================================
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
    return _get_frame(game_state)


class SurveyRung(DecisionRung):
    """Survey the environment at level start - ORIENTATION

    Uses grid_analyzer engine to analyze frame and build survey context.
    Identifies objects, colors, and grid structure for the agent's world model.
    """
    name = "survey"
    category = "orientation"
    default_priority = 5
    confidence_threshold = 0.0  # Always runs, modifies context not action

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Check if survey already done for this level
        if context.get('survey_complete', False):
            return RungResult(confidence=0.0, reason="Survey already complete")

        # Build survey context using grid_analyzer
        try:
            survey: Dict[str, Any] = self._build_survey_context(game_state, context)
            context['survey'] = survey
            context['survey_complete'] = True

            # Genuine epistemic resolution: we now know what objects exist
            resolved = ['what_objects_exist']
            if survey.get('has_boundary'):
                resolved.append('has_boundary_structure')

            return RungResult(
                confidence=0.1,  # Low confidence - doesn't suggest action, just observes
                reason=f"Survey complete: {len(survey.get('detected_features', {}))} features detected",
                metadata={'survey': survey},
                resolved_questions=resolved,
            )
        except Exception as e:
            return RungResult(reason=f"Survey failed: {e}")

    def _build_survey_context(self, game_state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build survey context from frame analysis using grid_analyzer."""
        survey: Dict[str, Any] = {
            'detected_features': {},
            'unique_colors': set(),
            'object_count': 0,
            'grid_size': (0, 0),
            'has_boundary': False
        }

        # Get frame from game_state
        frame = _get_frame(game_state)
        if frame is None:
            return survey

        # Convert numpy array to list if needed
        if hasattr(frame, 'tolist'):
            frame = frame.tolist()

        # Analyze grid structure
        if isinstance(frame, list) and len(frame) > 0:
            survey['grid_size'] = (len(frame), len(frame[0]) if len(frame) > 0 else 0)

            # Find unique colors and objects
            colors: set = set()
            object_positions: Dict[int, List[tuple]] = {}

            for y, row in enumerate(frame):
                for x, color in enumerate(row):
                    if color > 0:  # Non-background
                        colors.add(color)
                        if color not in object_positions:
                            object_positions[color] = []
                        object_positions[color].append((y, x))

            survey['unique_colors'] = colors
            survey['object_count'] = len(object_positions)

            # Detect features for each color
            for color, positions in object_positions.items():
                feature = {
                    'color': color,
                    'pixel_count': len(positions),
                    'positions': positions[:10],  # Sample for memory
                    'is_single': len(positions) <= 4,
                    'is_large': len(positions) > 20
                }

                # Check if on boundary (potential boundary marker)
                boundary_positions = [p for p in positions if p[0] == 0 or p[1] == 0
                                      or p[0] == len(frame) - 1 or p[1] == len(frame[0]) - 1]
                if len(boundary_positions) > len(positions) * 0.5:
                    feature['likely_boundary'] = True
                    survey['has_boundary'] = True

                survey['detected_features'][f'color_{color}'] = feature

        # Try to use grid_analyzer for more sophisticated analysis
        grid_analyzer = self.engines.grid_analyzer
        if grid_analyzer and frame:
            try:
                if hasattr(grid_analyzer, 'analyze_grid_structure'):
                    analysis = grid_analyzer.analyze_grid_structure(frame)
                    survey['grid_analysis'] = analysis
            except Exception:
                pass  # Grid analyzer enhancement is optional

        return survey


class QuestioningRung(DecisionRung):
    """Q1-Q9 questioning engine - can BLOCK actions - ORIENTATION"""
    name = "questioning_engine"
    category = "orientation"
    default_priority = 10
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            if not hasattr(sme, 'questioning_engine'):
                return RungResult()

            qe = sme.questioning_engine
            blocking_questions: List[Any] = qe.get_blocking_questions() if hasattr(qe, 'get_blocking_questions') else []

            if blocking_questions:
                # Q4, Q9, or META is blocking - force specific action types
                allowed_actions = qe.get_allowed_actions(blocking_questions)
                return RungResult(
                    action=random.choice(allowed_actions) if allowed_actions else None,
                    confidence=0.8,
                    reason=f"Blocked by questions: {blocking_questions}",
                    metadata={'blocking_questions': blocking_questions, 'allowed': allowed_actions}
                )
            return RungResult(confidence=0.0)
        except Exception as e:
            return RungResult(reason=f"Questioning failed: {e}")


class ExplorationPhaseRung(DecisionRung):
    """Phase-based exploration forcing - ORIENTATION"""
    name = "exploration_phase"
    category = "orientation"
    default_priority = 22
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            budget_used = context.get('budget_used_percent', 0)
            coverage = context.get('coverage_percent', 0)

            # Discovery phase: 0-30% budget AND low coverage
            if budget_used < 0.3 and coverage < 0.3:
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6'], context
                )
                chosen_action = random.choice(exploration_actions)

                # If ACTION6 (click), provide coordinates from visual_analyzer
                metadata: Dict[str, Any] = {
                    'phase': 'discovery',
                    'budget_used': budget_used,
                    'coverage': coverage
                }
                if chosen_action == 'ACTION6':
                    # Try to get grid exploration targets for coordinates
                    va = self.engines.visual_analyzer if self.engines else None
                    if va and hasattr(va, 'get_grid_exploration_targets'):
                        targets = va.get_grid_exploration_targets()
                        if targets:
                            target = targets[0]
                            metadata['x'] = target.get('x', 32)
                            metadata['y'] = target.get('y', 32)
                            metadata['grid_target'] = target
                        else:
                            # Fallback: random position in 64x64 grid
                            metadata['x'] = random.randint(4, 60)
                            metadata['y'] = random.randint(4, 60)
                    else:
                        # No visual analyzer - use random position
                        metadata['x'] = random.randint(4, 60)
                        metadata['y'] = random.randint(4, 60)

                # Dynamic confidence: starts at 0.55 (fresh game, unknown
                # territory) and decays as exploration exhausts itself.
                # Without this, the hardcoded 0.6 exceeds the router's 0.50
                # commit threshold every time, monopolising the first
                # iteration and preventing any other rung from executing.
                #
                # Decay factors:
                #   - budget_used: you've spent actions without advancing
                #   - coverage: grid has been explored (less to discover)
                #   - action_count penalty: even at 0% budget_used,
                #     repeated calls without progress should decay.
                action_count = context.get('action_count', 0)
                # How many actions have occurred since last level change?
                # Proxy: if score hasn't increased, exploration isn't working.
                actions_since_progress = action_count - context.get(
                    'last_progress_action', 0
                )
                # Decay: steep drop from budget consumption, mild from
                # action repetition (each action without progress = -0.005).
                staleness_penalty = min(0.3, actions_since_progress * 0.005)
                confidence = max(
                    0.15,  # Floor: never fully block, but yield to better rungs
                    0.55 - budget_used * 0.8 - coverage * 0.5 - staleness_penalty
                )

                return RungResult(
                    action=chosen_action,
                    confidence=confidence,
                    reason=f"Discovery phase: budget={budget_used:.0%}, coverage={coverage:.0%}, conf={confidence:.2f}",
                    metadata=metadata
                )
            return RungResult(metadata={'phase': 'intermediate' if budget_used < 0.7 else 'final'})
        except Exception as e:
            return RungResult(reason=f"Exploration phase failed: {e}")


class FrustrationDetectionRung(DecisionRung):
    """Detect stuck agents and trigger network signals - ORIENTATION"""
    name = "frustration_detection"
    category = "orientation"
    default_priority = 13
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        fd = self.engines.frustration_detector
        if fd is None:
            return RungResult()

        try:
            if hasattr(fd, 'is_frustrated'):
                frustration = fd.is_frustrated()
                if frustration.get('is_frustrated', False):
                    # Force exploration when frustrated
                    return RungResult(
                        action=get_random_available_action(context),
                        confidence=0.65,
                        reason=f"Frustration detected: {frustration.get('reason', 'unknown')}",
                        metadata={'frustration': frustration}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Frustration detection failed: {e}")


class PaletteDetectionRung(DecisionRung):
    """
    TWO-STAGE DECOMPOSITION: Stage 1 - Detect palette/legend blocks.

    Based on ARC-AGI-2 insights (76.11% success):
    "~70% of models cluster around wrong solutions where they use the 'palette'
    as top-to-bottom instead of inside-out."

    This rung runs EARLY to:
    1. Extract all objects from the frame (hollow frames, fills, irregular)
    2. Detect multi-colored palette/legend blocks
    3. Determine correct mapping direction (inside-out vs top-to-bottom)
    4. Populate context for downstream rungs

    Sets context fields:
    - detected_palette: PaletteInfo dict or None
    - extracted_objects: Dict with categorized objects
    - detected_transformations: List of detected transformation rules
    """
    name = "palette_detection"
    category = "orientation"
    default_priority = 3  # Very early - before frame_interpretation
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._palette_detector: Optional[Any] = None
        self._cached_analysis: Dict[str, Any] = {}  # Cache by frame hash

    def _get_palette_detector(self) -> Optional[Any]:
        """Lazy-load palette detector."""
        if self._palette_detector is None:
            try:
                from engines.perception.palette_detector import PaletteDetector
                self._palette_detector = PaletteDetector()
            except ImportError as e:
                logger.debug(f"[PALETTE-RUNG] PaletteDetector not available: {e}")
        return self._palette_detector

    def _frame_to_hash(self, frame: Any) -> str:
        """Generate hash for frame caching."""
        if frame is None:
            return "none"
        try:
            import hashlib
            if hasattr(frame, 'tobytes'):
                return hashlib.md5(frame.tobytes()).hexdigest()[:16]
            return hashlib.md5(str(frame).encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Get frame from game_state
        frame = _get_frame(game_state)
        if frame is None:
            return RungResult(
                confidence=0.0,
                reason="No frame available for palette detection"
            )

        # Check cache
        frame_hash = self._frame_to_hash(frame)
        if frame_hash in self._cached_analysis:
            cached = self._cached_analysis[frame_hash]
            context['detected_palette'] = cached.get('detected_palette')
            context['extracted_objects'] = cached.get('extracted_objects')
            context['detected_transformations'] = cached.get('detected_transformations')
            return RungResult(
                confidence=0.0,  # Context-setter only: no action to suggest
                reason=f"Cached palette analysis: {'found' if cached.get('detected_palette') else 'none'}",
                metadata={'cached': True, **cached}
            )

        # Get detector
        detector = self._get_palette_detector()
        if detector is None:
            return RungResult(
                confidence=0.0,
                reason="Palette detector not available"
            )

        try:
            import numpy as np
            frame_arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Could not convert frame to array: {e}"
            )

        # Stage 1: Extract objects
        try:
            extracted = detector.extract_objects(frame_arr)
            extracted_dict = {
                'palettes': [o.to_dict() for o in extracted.get('palettes', [])],
                'hollow_frames': [o.to_dict() for o in extracted.get('hollow_frames', [])],
                'filled_shapes': [o.to_dict() for o in extracted.get('filled_shapes', [])],
                'irregular_shapes': [o.to_dict() for o in extracted.get('irregular_shapes', [])],
                'object_count': len(extracted.get('all_objects', [])),
            }
        except Exception as e:
            extracted_dict = {'error': str(e), 'object_count': 0}
            extracted = {}

        # Stage 1.5: Detect palette
        palette_dict = None
        try:
            palette = detector.detect_palette(frame_arr)
            if palette:
                palette_dict = palette.to_dict()
        except Exception as e:
            logger.debug(f"[PALETTE-RUNG] Palette detection failed: {e}")

        # Stage 2: Detect transformations
        transformations = []
        try:
            if palette and extracted:
                trans = detector.detect_transformations(extracted, palette, frame_arr)
                transformations = [t.to_dict() for t in trans]
        except Exception as e:
            logger.debug(f"[PALETTE-RUNG] Transformation detection failed: {e}")

        # Set context
        context['detected_palette'] = palette_dict
        context['extracted_objects'] = extracted_dict
        context['detected_transformations'] = transformations

        # Cache result
        analysis = {
            'detected_palette': palette_dict,
            'extracted_objects': extracted_dict,
            'detected_transformations': transformations,
        }
        self._cached_analysis[frame_hash] = analysis

        # Limit cache size
        if len(self._cached_analysis) > 100:
            oldest = list(self._cached_analysis.keys())[:50]
            for k in oldest:
                del self._cached_analysis[k]

        # Build reason
        parts = []
        if palette_dict:
            parts.append(f"palette={palette_dict.get('palette_type', 'unknown')}")
            parts.append(f"direction={palette_dict.get('mapping_direction', 'unknown')}")
            parts.append(f"conf={palette_dict.get('confidence', 0):.2f}")
        else:
            parts.append("no_palette")

        parts.append(f"objects={extracted_dict.get('object_count', 0)}")
        if transformations:
            parts.append(f"transforms={len(transformations)}")

        return RungResult(
            confidence=0.0,  # Context-setter only: enriches context, never suggests action
            reason=f"Two-stage analysis: {', '.join(parts)}",
            metadata={
                'palette_found': palette_dict is not None,
                'object_count': extracted_dict.get('object_count', 0),
                'transformation_count': len(transformations),
                'analysis': analysis,
            }
        )

    def clear_cache(self):
        """Clear analysis cache (call on game/level change)."""
        self._cached_analysis.clear()


class SparseGridRung(DecisionRung):
    """
    SPARSE GRID REPRESENTATION: Efficient frame analysis for pattern matching.

    Converts frames to sparse representation (only non-background cells) for:
    1. Efficient structural comparison between frames
    2. Position-invariant pattern hashing
    3. Color-invariant pattern matching
    4. Connected component extraction

    Sets context fields:
    - sparse_grid: SparseGrid object for current frame
    - sparse_hash: Structural hash of current frame
    - sparse_cell_count: Number of non-background cells
    - sparse_colors: Set of colors used (excluding background)
    - sparse_components: List of connected component bounding boxes
    """
    name = "sparse_grid"
    category = "orientation"
    default_priority = 3  # Very early - alongside palette_detection
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cached_sparse: Dict[str, Any] = {}  # Cache by frame hash
        self._previous_sparse: Optional[Any] = None  # For diff calculation

    def _frame_to_hash(self, frame: Any) -> str:
        """Generate hash for frame caching."""
        if frame is None:
            return "none"
        try:
            import hashlib
            if hasattr(frame, 'tobytes'):
                return hashlib.md5(frame.tobytes()).hexdigest()[:16]
            return hashlib.md5(str(frame).encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Get frame from game_state
        frame = _get_frame(game_state)
        if frame is None:
            return RungResult(
                confidence=0.0,
                reason="No frame available for sparse grid"
            )

        # Check cache
        frame_hash = self._frame_to_hash(frame)
        if frame_hash in self._cached_sparse:
            cached = self._cached_sparse[frame_hash]
            context['sparse_grid'] = cached.get('sparse_grid')
            context['sparse_hash'] = cached.get('sparse_hash')
            context['sparse_cell_count'] = cached.get('sparse_cell_count')
            context['sparse_colors'] = cached.get('sparse_colors')
            context['sparse_components'] = cached.get('sparse_components')
            context['sparse_diff'] = cached.get('sparse_diff')
            return RungResult(
                confidence=0.1,
                reason=f"Cached sparse: {cached.get('sparse_cell_count', 0)} cells",
                metadata={'cached': True, **cached}
            )

        # Import sparse grid module
        try:
            from engines.perception.sparse_grid import sparse_from_frame
        except ImportError as e:
            return RungResult(
                confidence=0.0,
                reason=f"Sparse grid module not available: {e}"
            )

        try:
            import numpy as np
            frame_arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Could not convert frame to array: {e}"
            )

        # Create sparse grid
        try:
            sparse = sparse_from_frame(frame_arr)
            sparse_hash = sparse.structural_hash()
            cell_count = len(sparse)
            colors = sparse.colors  # Property, not method

            # Extract connected components
            components = []
            try:
                comps = sparse.extract_connected_components()
                for comp in comps:
                    bbox = comp.bounding_box  # Property, not method
                    if bbox:
                        components.append({
                            'min_y': bbox[0], 'min_x': bbox[1],
                            'max_y': bbox[2], 'max_x': bbox[3],
                            'cell_count': len(comp),
                            'colors': list(comp.colors),  # Property, not method
                        })
            except Exception as e:
                logger.debug(f"[SPARSE-RUNG] Component extraction failed: {e}")

            # Calculate diff from previous frame
            diff_info = None
            if self._previous_sparse is not None:
                try:
                    diff = self._previous_sparse.diff(sparse)  # Use method, not function
                    diff_info = {
                        'added_count': len(diff.added),
                        'removed_count': len(diff.removed),
                        'changed_count': len(diff.changed),
                        'total_changes': diff.total_changes,  # Correct property name
                    }
                except Exception as e:
                    logger.debug(f"[SPARSE-RUNG] Diff calculation failed: {e}")

            # Store for next diff
            self._previous_sparse = sparse

        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Sparse grid creation failed: {e}"
            )

        # Set context
        context['sparse_grid'] = sparse
        context['sparse_hash'] = sparse_hash
        context['sparse_cell_count'] = cell_count
        context['sparse_colors'] = colors
        context['sparse_components'] = components
        context['sparse_diff'] = diff_info

        # Cache result
        sparse_data = {
            'sparse_grid': sparse,
            'sparse_hash': sparse_hash,
            'sparse_cell_count': cell_count,
            'sparse_colors': colors,
            'sparse_components': components,
            'sparse_diff': diff_info,
        }
        self._cached_sparse[frame_hash] = sparse_data

        # Limit cache size
        if len(self._cached_sparse) > 100:
            oldest = list(self._cached_sparse.keys())[:50]
            for k in oldest:
                del self._cached_sparse[k]

        # Build reason
        parts = [f"cells={cell_count}", f"colors={len(colors)}"]
        if components:
            parts.append(f"components={len(components)}")
        if diff_info:
            parts.append(f"delta={diff_info['total_changes']}")

        return RungResult(
            confidence=0.1,  # Low - context setter
            reason=f"Sparse grid: {', '.join(parts)}",
            metadata={
                'sparse_hash': sparse_hash,
                'cell_count': cell_count,
                'color_count': len(colors),
                'component_count': len(components),
                'diff_info': diff_info,
            }
        )

    def clear_cache(self):
        """Clear sparse cache (call on game/level change)."""
        self._cached_sparse.clear()
        self._previous_sparse = None


class FrameInterpretationRung(DecisionRung):
    """
    HIGH PRIORITY: Interpret dramatic frame changes and set context.

    This rung sets context flags for downstream rungs based on frame delta
    magnitude. Does NOT suppress actions - the ARC API is blocking so spam
    is impossible anyway.

    Sets context flags:
    - likely_physics_game: True if large frame delta
    - expect_large_deltas: True if physics signature detected
    - detected_process_type: The type of process observed
    """
    name = "frame_interpretation"
    category = "orientation"
    default_priority = 4  # Early, after emergency rungs
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._event_detector: Optional[Any] = None
        self._recent_process_types: List[str] = []

    def _get_event_detector(self) -> Optional[Any]:
        """Lazy-load event detector."""
        if self._event_detector is None:
            try:
                from engines.perception.event_detector import EventDetector
                self._event_detector = EventDetector()
            except ImportError:
                pass
        return self._event_detector

    def _has_physics_signature(self, events: List[Any]) -> bool:
        """Check if events show physics-like behavior."""
        if not events:
            return False

        movement_count = sum(
            1 for e in events
            if hasattr(e, 'event_type') and str(e.event_type) == 'MOVEMENT'
        )
        return movement_count >= 3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        delta_count = context.get('frame_delta_count', 0)
        recent_events = context.get('recent_events', [])

        # Interpret dramatic changes
        if delta_count > 500:  # Significant frame change
            # Annotate context for downstream rungs
            context['likely_physics_game'] = True
            context['expect_large_deltas'] = True

            # Check for physics signature
            if recent_events and self._has_physics_signature(recent_events):
                context['detected_process_type'] = 'PHYSICS_SIMULATION'
                self._recent_process_types.append('PHYSICS_SIMULATION')

            return RungResult(
                confidence=0.0,  # No action suggestion
                reason=f"Large frame delta ({delta_count}) - likely physics/animation game",
                metadata={
                    'delta_count': delta_count,
                    'physics_signature': bool(recent_events and self._has_physics_signature(recent_events)),
                    'recent_process_types': self._recent_process_types[-5:] if self._recent_process_types else [],
                }
            )

        # Small delta - probably direct control game
        if delta_count > 0 and delta_count < 100:
            context['likely_direct_control'] = True

        return RungResult()


class BreakthroughBudgetRung(DecisionRung):
    """Dynamic action allocation based on breakthrough potential - ORIENTATION"""
    name = "breakthrough_budget"
    category = "orientation"
    default_priority = 6
    confidence_threshold = 0.0  # Context modifier, not action suggester

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        allocator = self.engines.breakthrough_allocator
        if allocator is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')

            if hasattr(allocator, 'get_budget'):
                budget = allocator.get_budget(game_type)
                context['action_budget'] = budget.get('per_level', 400)
                context['total_budget'] = budget.get('total', 2000)
                context['budget_phase'] = budget.get('phase', 'DISCOVERY')

                return RungResult(
                    confidence=0.1,  # Low - doesn't suggest action
                    reason=f"Budget phase: {budget.get('phase', 'DISCOVERY')}, per_level={budget.get('per_level', 400)}",
                    metadata={'budget': budget}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Breakthrough budget failed: {e}")


class RegulatorySignalRung(DecisionRung):
    """Network homeostasis through distributed signals - ORIENTATION"""
    name = "regulatory_signal"
    category = "orientation"
    default_priority = 7
    confidence_threshold = 0.0  # Context modifier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        re = self.engines.regulatory_engine
        if re is None:
            return RungResult()

        try:
            if hasattr(re, 'get_active_signals'):
                signals = re.get_active_signals()

                # Apply signal effects to context
                for signal in signals:
                    if signal.get('type') == 'diversity_stress':
                        context['knowledge_diversity_boost'] = context.get('knowledge_diversity_boost', 0) + 0.15
                    elif signal.get('type') == 'metabolism_stress':
                        context['action_budget_multiplier'] = context.get('action_budget_multiplier', 1.0) + 0.1
                    elif signal.get('type') == 'exploration_need':
                        context['mutation_rate'] = context.get('mutation_rate', 0) + 0.05

                if signals:
                    return RungResult(
                        confidence=0.1,
                        reason=f"Regulatory signals: {len(signals)} active",
                        metadata={'signals': signals}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Regulatory signal failed: {e}")


class GridExplorationRung(DecisionRung):
    """Systematic 8x8 grid walking when stuck - EXPLORATION"""
    name = "grid_exploration"
    category = "orientation"
    default_priority = 47
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        va = self.engines.visual_analyzer
        if va is None:
            return RungResult()

        try:
            # ACTION6 is typically 'click' - only suggest if available
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            if 6 not in available:
                return RungResult()  # Click not available for this game

            if hasattr(va, 'get_grid_exploration_targets'):
                targets = va.get_grid_exploration_targets()
                if targets:
                    target = targets[0]
                    return RungResult(
                        action='ACTION6',
                        confidence=0.35,
                        reason=f"Grid exploration: ({target.get('x', 0)}, {target.get('y', 0)}) - systematic search",
                        metadata={'grid_target': target, 'grid_index': va.grid_walking_index if hasattr(va, 'grid_walking_index') else 0}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Grid exploration failed: {e}")


class AffordanceDetectionRung(DecisionRung):
    """Wire seed affordance primitives into gameplay decisions - ORIENTATION

    The AFFORDANCE category (is_reference, is_interactive, is_obstacle,
    is_container, is_tool, is_movable) exists in seed_primitives.py but
    was NEVER queried by any decision rung.

    This rung:
    1. Runs affordance primitives on objects detected in the frame
    2. Tags objects with affordance labels (reference, interactive, obstacle)
    3. Injects affordance data into context for downstream rungs
    4. Specifically detects reference objects (CRITICAL for FT09)

    ROOT CAUSE ADDRESSED: "No is_reference primitive active" - the entire
    affordance detection category was registered but disconnected.
    """
    name = "affordance_detection"
    category = "orientation"
    default_priority = 8
    confidence_threshold = 0.3
    required_primitives = [
        'is_reference', 'is_interactive', 'is_obstacle',
        'is_container', 'is_tool', 'is_movable'
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Cache affordances per game_key to avoid recomputing every frame
        self._affordance_cache: Dict[str, Dict[str, List[str]]] = {}
        # Track interaction history for is_interactive primitive
        self._interaction_history: List[Dict[str, Any]] = []
        # Track rule history for is_reference primitive
        self._rule_history: List[Dict[str, Any]] = []
        # Track effect history for is_tool primitive
        self._effect_history: List[Dict[str, Any]] = []
        # Discovered objects by game
        self._object_registry: Dict[str, List[Dict[str, Any]]] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        """Detect affordances and inject into context. Does NOT suggest actions."""
        frame = _get_frame(game_state)
        if frame is None:
            return RungResult()

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        # Detect distinct objects in frame
        objects = self._detect_objects(frame)
        if not objects:
            return RungResult()

        self._object_registry[game_key] = objects

        # Run affordance primitives on each object
        affordances: Dict[str, List[str]] = {
            'reference': [],
            'interactive': [],
            'obstacle': [],
            'container': [],
            'tool': [],
            'movable': [],
        }

        for obj in objects:
            obj_id = obj.get('object_id', '')

            # is_obstacle: checks frame for blocking behavior
            if self.call_primitive('is_obstacle', obj_id, frame):
                affordances['obstacle'].append(obj_id)

            # is_interactive: checks interaction history
            if self.call_primitive('is_interactive', obj_id, self._interaction_history):
                affordances['interactive'].append(obj_id)

            # is_reference: checks rule history
            if self.call_primitive('is_reference', obj_id, frame, self._rule_history):
                affordances['reference'].append(obj_id)

            # is_tool: checks effect history
            if self.call_primitive('is_tool', obj_id, self._effect_history):
                affordances['tool'].append(obj_id)

        # Inject affordance data into context for downstream rungs
        context['affordances'] = affordances
        context['detected_objects'] = objects
        context['reference_objects'] = affordances['reference']
        context['interactive_objects'] = affordances['interactive']
        context['obstacle_objects'] = affordances['obstacle']

        # Heuristic: if no interaction history yet but we see distinct colored
        # objects that don't move, they might be reference objects
        if not affordances['reference'] and len(objects) > 2:
            # Objects with unique colors that don't appear elsewhere could be references
            color_counts: Dict[int, int] = {}
            for obj in objects:
                c = obj.get('color', 0)
                color_counts[c] = color_counts.get(c, 0) + 1
            unique_color_objs = [
                o for o in objects
                if color_counts.get(o.get('color', 0), 0) == 1
            ]
            if unique_color_objs:
                context['potential_reference_objects'] = unique_color_objs

        # This rung is informational - enriches context, doesn't suggest action
        if affordances['reference']:
            return RungResult(
                reason=f"Affordances detected: {sum(len(v) for v in affordances.values())} tagged objects, {len(affordances['reference'])} reference objects",
                metadata={'affordances': affordances}
            )

        return RungResult(
            reason=f"Affordances: {sum(len(v) for v in affordances.values())} tagged",
            metadata={'affordances': affordances}
        )

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Update interaction and effect histories for affordance detection."""
        if frame_before is None or frame_after is None:
            return

        frame_changed = False
        try:
            if isinstance(frame_before, list) and isinstance(frame_after, list):
                frame_changed = frame_before != frame_after
            else:
                import numpy as np
                frame_changed = not np.array_equal(frame_before, frame_after)
        except Exception:
            pass

        # Update interaction history
        if action == 'ACTION6':
            x, y = action_data.get('x', 0), action_data.get('y', 0)
            # Find which object was at (x, y)
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            game_key = f"{game_type}_L{level}"
            objects = self._object_registry.get(game_key, [])
            for obj in objects:
                if self._point_in_object(x, y, obj):
                    self._interaction_history.append({
                        'object_id': obj['object_id'],
                        'action': action,
                        'responded': frame_changed,
                        'x': x, 'y': y,
                    })
                    if frame_changed:
                        self._effect_history.append({
                            'tool_object': obj['object_id'],
                            'caused_effect': True,
                        })
                    break

        elif frame_changed and action in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']:
            # Directional movement that caused change - might have interacted with tile
            self._interaction_history.append({
                'object_id': f'tile_at_movement_{action}',
                'action': action,
                'responded': True,
            })

            # Check if significant state change happened (potential rule discovery)
            try:
                change_count = self._count_frame_changes(frame_before, frame_after)
                if change_count > 10:  # Significant state change
                    self._rule_history.append({
                        'reference_object': f'tile_at_movement_{action}',
                        'rule_confidence': 0.5,
                        'change_count': change_count,
                    })
            except Exception:
                pass

    def _detect_objects(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """Detect distinct colored objects in the frame."""
        if frame is None or (isinstance(frame, list) and len(frame) == 0):
            return []

        color_pixels: Dict[int, List[Tuple[int, int]]] = {}
        try:
            for y, row in enumerate(frame):
                for x, pixel in enumerate(row):
                    val = int(pixel) if hasattr(pixel, '__int__') else pixel
                    if val != 0:
                        if val not in color_pixels:
                            color_pixels[val] = []
                        color_pixels[val].append((x, y))
        except Exception:
            return []

        objects = []
        frame_area = len(frame) * (len(frame[0]) if len(frame) > 0 else 64)
        for color, pixels in color_pixels.items():
            size = len(pixels)
            if size < 2 or size > frame_area * 0.5:
                continue
            avg_x = sum(p[0] for p in pixels) // size
            avg_y = sum(p[1] for p in pixels) // size
            min_x = min(p[0] for p in pixels)
            max_x = max(p[0] for p in pixels)
            min_y = min(p[1] for p in pixels)
            max_y = max(p[1] for p in pixels)
            objects.append({
                'object_id': f'color_{color}',
                'color': color,
                'center_x': avg_x,
                'center_y': avg_y,
                'size': size,
                'bbox': (min_x, min_y, max_x, max_y),
                'positions': pixels if size < 200 else [],  # Don't store huge position lists
            })

        return objects

    @staticmethod
    def _point_in_object(x: int, y: int, obj: Dict[str, Any]) -> bool:
        """Check if point is within object bounding box."""
        bbox = obj.get('bbox')
        if bbox:
            return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]
        return False

    @staticmethod
    def _count_frame_changes(frame_before: Any, frame_after: Any) -> int:
        """Count number of pixel changes between frames."""
        count = 0
        try:
            if isinstance(frame_before, list):
                for y in range(min(len(frame_before), len(frame_after))):
                    for x in range(min(len(frame_before[y]), len(frame_after[y]))):
                        if frame_before[y][x] != frame_after[y][x]:
                            count += 1
            else:
                import numpy as np
                count = int(np.sum(np.array(frame_before) != np.array(frame_after)))
        except Exception:
            pass
        return count


class ControlTrackerRung(DecisionRung):
    """Track which objects the agent controls - ORIENTATION (self-model)

    Uses engines/self_model/control_tracker.py to:
    1. Track action-movement correlations to identify controlled objects
    2. Provide "I am this object" identity information
    3. Suggest actions that move the controlled object toward goals

    This is CRITICAL for agents to understand their embodiment in the game.
    """
    name = "control_tracker"
    category = "orientation"
    default_priority = 8  # Early - need to know what we control
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ct = self.engines.control_tracker
        if ct is None:
            return RungResult()

        try:
            game_id = context.get('game_id', context.get('game_type', ''))
            level = context.get('level', context.get('level_number', 1))

            if not game_id:
                return RungResult()

            # Get controlled objects for this game/level
            if hasattr(ct, 'get_controlled_objects'):
                controlled = ct.get_controlled_objects(game_id, level)

                if controlled:
                    # We know what we control - add to context for other rungs
                    best = controlled[0]  # Highest confidence
                    action_map = best.action_map

                    # If we have a goal/target, suggest action to move toward it
                    target = context.get('target_position') or context.get('goal_position')
                    player_pos = context.get('player_position')

                    if target and player_pos:
                        dx = target[0] - player_pos[0]
                        dy = target[1] - player_pos[1]

                        # Find action that moves in correct direction
                        for action, direction in action_map.items():
                            if direction == 'right' and dx > 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} right toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'right'}
                                )
                            elif direction == 'left' and dx < 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} left toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'left'}
                                )
                            elif direction == 'down' and dy > 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} down toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'down'}
                                )
                            elif direction == 'up' and dy < 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} up toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'up'}
                                )

                    # No target - just return info about what we control
                    return RungResult(
                        confidence=0.3,
                        reason=f"Control tracker: {best.object_id} ({best.confidence.value})",
                        metadata={
                            'controlled_objects': [c.to_dict() for c in controlled],
                            'primary_control': best.to_dict()
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Control tracker failed: {e}")


class ImaginationBudgetRung(DecisionRung):
    """Allocate computational budget based on novelty - ORIENTATION"""
    name = "imagination_budget"
    category = "orientation"
    default_priority = 4
    confidence_threshold = 0.0  # Context modifier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ib = self.engines.imagination_budget
        if ib is None:
            return RungResult()

        try:
            if hasattr(ib, 'calculate_budget'):
                budget = ib.calculate_budget(
                    is_novel=context.get('is_novel_game', False),
                    is_frontier=context.get('frontier_mode', False),
                    surprise_score=context.get('surprise_score', 0)
                )

                context['imagination_budget_remaining'] = budget.get('total', 0.5)
                context['question_tier'] = budget.get('tier', 'Q1')

                return RungResult(
                    confidence=0.1,
                    reason=f"Imagination budget: {budget.get('total', 0.5):.2f}, tier={budget.get('tier', 'Q1')}",
                    metadata={'budget': budget}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Imagination budget failed: {e}")


class NetworkExplorationStatsRung(DecisionRung):
    """Track coverage, identify coldspots/hotspots - ORIENTATION"""
    name = "network_exploration_stats"
    category = "orientation"
    default_priority = 9
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        net = self.engines.network_exploration_tracker
        if net is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if hasattr(net, 'get_exploration_stats'):
                stats = net.get_exploration_stats(game_type, level)

                context['coverage_percent'] = stats.get('coverage_percent', 0)

                # If there are coldspots, bias toward them
                coldspots = stats.get('coldspots', [])
                if coldspots:
                    direction = stats.get('recommended_direction')
                    direction_map = {'north': 'ACTION1', 'south': 'ACTION2', 'west': 'ACTION3', 'east': 'ACTION4'}
                    if direction and direction in direction_map:
                        return RungResult(
                            action=direction_map[direction],
                            confidence=0.45,
                            reason=f"Exploring coldspot: {direction}, coverage={stats.get('coverage_percent', 0):.0%}",
                            metadata={'stats': stats, 'coldspots': len(coldspots)}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network exploration stats failed: {e}")


# =============================================================================
# WIRED METACOGNITION RUNGS (Feb 2026)


class SelfTrustBoostRung(DecisionRung):
    """Manage wA (self-trust) based on context - ORIENTATION

    Wires: engines/consciousness/i_thread.py:
        - boost_self_trust()
        - restore_self_trust()

    On frontier levels (no winning sequences), boosts self-trust to encourage
    exploration over network following. When sequences become available,
    restores normal trust balance.

    This implements the Two Streams principle: trust yourself more when
    network wisdom doesn't apply.
    """
    name = "self_trust_boost"
    category = "orientation"
    default_priority = 3  # Very early - affects all downstream decisions
    confidence_threshold = 0.0  # Always runs, just adjusts weights

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._last_frontier_state: Dict[str, bool] = {}  # agent_id -> was_frontier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        i_thread = self.engines.i_thread
        if i_thread is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', 'default')
            is_frontier = context.get('frontier_mode', False) or context.get('is_frontier', False)
            has_sequence = context.get('has_winning_sequence', False) or context.get('active_sequence')

            # Track state transition
            was_frontier = self._last_frontier_state.get(agent_id, False)
            self._last_frontier_state[agent_id] = is_frontier

            # Boost when entering frontier (no sequences available)
            if is_frontier and not has_sequence and not was_frontier:
                if hasattr(i_thread, 'boost_self_trust'):
                    original, boosted, new_wB = i_thread.boost_self_trust(
                        agent_id=agent_id,
                        boost_amount=0.25,
                        reason='frontier_exploration'
                    )
                    return RungResult(
                        confidence=0.1,  # Context modifier, not action suggestion
                        reason=f"Frontier boost: wA {original:.2f} -> {boosted:.2f}",
                        metadata={
                            'boost_applied': True,
                            'original_wA': original,
                            'boosted_wA': boosted,
                            'trigger': 'frontier_entry'
                        }
                    )

            # Restore when leaving frontier (sequences now available)
            if (not is_frontier or has_sequence) and was_frontier:
                if hasattr(i_thread, 'restore_self_trust'):
                    restored_wA, restored_wB = i_thread.restore_self_trust(agent_id=agent_id)
                    return RungResult(
                        confidence=0.1,
                        reason=f"Trust restored: wA -> {restored_wA:.2f}",
                        metadata={
                            'restore_applied': True,
                            'restored_wA': restored_wA,
                            'trigger': 'frontier_exit'
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Self trust boost failed: {e}")



# Registry of rungs in this module
RUNGS = {
    'survey': SurveyRung,
    'questioning_engine': QuestioningRung,
    'exploration_phase': ExplorationPhaseRung,
    'frustration_detection': FrustrationDetectionRung,
    'palette_detection': PaletteDetectionRung,
    'sparse_grid': SparseGridRung,
    'frame_interpretation': FrameInterpretationRung,
    'breakthrough_budget': BreakthroughBudgetRung,
    'regulatory_signal': RegulatorySignalRung,
    'grid_exploration': GridExplorationRung,
    'affordance_detection': AffordanceDetectionRung,
    'control_tracker': ControlTrackerRung,
    'imagination_budget': ImaginationBudgetRung,
    'network_exploration_stats': NetworkExplorationStatsRung,
    'self_trust_boost': SelfTrustBoostRung,
}
