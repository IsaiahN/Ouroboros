"""
Phase 1: Orient - "What world am I in?"
=======================================

Gathers context about the current game state:
- Discovery phase (movement test, click survey, etc.)
- World model (spatial layout, objects)
- Coverage statistics
- Blocking questions

NO action suggestions - only context building.
This phase answers: "Where am I and what's around me?"
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import GameState, AgentContext

from engines.decision.phase_contracts import OrientContext, PhaseError

logger = logging.getLogger(__name__)


class OrientPhase:
    """
    Phase 1: Build orientation context.

    Queries:
    - DiscoveryEngine for discovery phase
    - GridAnalyzer for spatial layout
    - NetworkExplorationTracker for coverage stats
    - QuestioningEngine for blocking questions
    """

    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines

    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
    ) -> OrientContext:
        """
        Build orientation context.

        NEVER returns None. ALWAYS returns valid OrientContext.
        Missing data -> explicit defaults with warnings logged.
        """
        # === Discovery Phase ===
        discovery_phase = self._get_discovery_phase(game_state)

        # === World Model ===
        world_model = self._get_world_model(game_state)

        # === Coverage Stats ===
        coverage_percent = self._get_coverage(game_state)

        # === Blocking Questions ===
        blocking_questions = self._get_blocking_questions()

        # === Detected Objects ===
        detected_objects = self._detect_objects(game_state)

        # === Frame Change Detection ===
        frame_changed = self._check_frame_changed(game_state)

        # Build context
        ctx = OrientContext(
            world_model=world_model,
            discovery_phase=discovery_phase,
            coverage_percent=coverage_percent,
            budget_used_percent=game_state.budget_used_percent,
            blocking_questions=blocking_questions,
            is_frontier=agent_context.is_frontier,
            urgency=agent_context.urgency,  # Simplified from "mortality_pressure"
            detected_objects=detected_objects,
            frame_changed=frame_changed,
        )

        # Validate contract
        ctx.validate()

        logger.debug(
            f"[ORIENT] discovery={discovery_phase}, coverage={coverage_percent:.1%}, "
            f"questions={len(blocking_questions)}, objects={len(detected_objects)}"
        )

        return ctx

    def _get_discovery_phase(self, game_state: 'GameState') -> str:
        """Get current discovery phase from engine."""
        discovery_engine = self.engines.get('discovery_engine')

        if discovery_engine:
            try:
                phase = discovery_engine.get_phase(
                    game_state.game_id,
                    game_state.level
                )
                if phase in ("idle", "movement_test", "click_survey", "complete"):
                    return phase
                logger.warning(f"[ORIENT] Invalid discovery phase '{phase}', defaulting to 'idle'")
            except Exception as e:
                logger.warning(f"[ORIENT] DiscoveryEngine error: {e}")

        # Default: idle (no active discovery)
        return "idle"

    def _get_world_model(self, game_state: 'GameState') -> Dict[str, Any]:
        """Build world model from frame analysis."""
        world_model: Dict[str, Any] = {
            'objects': [],
            'layout': 'unknown',
            'frame_width': 0,
            'frame_height': 0,
        }

        # Get frame dimensions
        if game_state.frame:
            world_model['frame_height'] = len(game_state.frame)
            if game_state.frame[0]:
                world_model['frame_width'] = len(game_state.frame[0])

        # Try grid analyzer
        grid_analyzer = self.engines.get('grid_analyzer')
        if grid_analyzer:
            try:
                analysis = grid_analyzer.analyze_frame(game_state.frame)
                if analysis:
                    world_model.update(analysis)
                    return world_model
            except Exception as e:
                logger.debug(f"[ORIENT] GridAnalyzer error: {e}")

        # Try visual analyzer as fallback
        visual_analyzer = self.engines.get('visual_analyzer')
        if visual_analyzer:
            try:
                if hasattr(visual_analyzer, 'analyze_frame'):
                    analysis = visual_analyzer.analyze_frame(game_state.frame)
                    if analysis:
                        world_model['layout'] = analysis.get('layout', 'unknown')
                        world_model['objects'] = analysis.get('objects', [])
            except Exception as e:
                logger.debug(f"[ORIENT] VisualAnalyzer error: {e}")

        return world_model

    def _get_coverage(self, game_state: 'GameState') -> float:
        """Get exploration coverage percentage."""
        exploration_tracker = self.engines.get('network_exploration_tracker')

        if exploration_tracker:
            try:
                stats = exploration_tracker.get_exploration_stats(
                    game_state.game_type,
                    game_state.level
                )
                if stats:
                    coverage = stats.get('coverage', stats.get('coverage_percent', 0.0))
                    return min(1.0, max(0.0, float(coverage)))
            except Exception as e:
                logger.debug(f"[ORIENT] ExplorationTracker error: {e}")

        return 0.0

    def _get_blocking_questions(self) -> List[str]:
        """Get Q1-Q9 questions that need answers."""
        sme = self.engines.get('scientific_method_engine')

        if sme and hasattr(sme, 'questioning_engine'):
            try:
                questions = sme.questioning_engine.get_blocking_questions()
                if questions:
                    return list(questions)
            except Exception as e:
                logger.debug(f"[ORIENT] QuestioningEngine error: {e}")

        return []

    def _detect_objects(self, game_state: 'GameState') -> List[Dict[str, Any]]:
        """Detect objects in current frame."""
        detected: List[Dict[str, Any]] = []

        # Try object detector
        object_detector = self.engines.get('object_detector')
        if object_detector:
            try:
                objects = object_detector.detect(game_state.frame)
                if objects:
                    return list(objects)
            except Exception as e:
                logger.debug(f"[ORIENT] ObjectDetector error: {e}")

        # Try visual analyzer
        visual_analyzer = self.engines.get('visual_analyzer')
        if visual_analyzer:
            try:
                if hasattr(visual_analyzer, 'get_priority_targets'):
                    targets = visual_analyzer.get_priority_targets(game_state.frame)
                    if targets:
                        return list(targets)
            except Exception as e:
                logger.debug(f"[ORIENT] VisualAnalyzer targets error: {e}")

        return detected

    def _check_frame_changed(self, game_state: 'GameState') -> bool:
        """Check if frame changed from previous action."""
        if game_state.previous_frame is None:
            return True  # First frame, count as changed

        if game_state.frame == game_state.previous_frame:
            return False

        return True
