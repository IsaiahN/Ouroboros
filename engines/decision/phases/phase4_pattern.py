"""
Phase 4: Pattern Match - "Have I seen this before?"
===================================================

Queries pattern-matching engines:
- EmbeddingMatcher for similar states
- CODSEngine for operator suggestions
- UniversalPatternEngine for cross-game patterns
- ResonanceDetector for cross-domain signals
- TriggerSequenceTracker for trigger chains
- AbstractionEngine for templates

This phase answers: "Does this situation match any known pattern?"
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import (
        GameState, AgentContext, OrientContext, GroundTruthContext, ReasonContext
    )

from engines.decision.phase_contracts import PatternContext, PatternMatch, PhaseError

logger = logging.getLogger(__name__)


class PatternPhase:
    """
    Phase 4: Pattern matching across all sources.

    Queries:
    - EmbeddingMatcher for neural similarity
    - CODSEngine for operator suggestions
    - UniversalPatternEngine for cross-game patterns
    - ResonanceDetector for cross-domain signals
    - TriggerSequenceTracker for trigger chains
    - AbstractionEngine for templates
    """

    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines

    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        orient_ctx: 'OrientContext',
        ground_ctx: 'GroundTruthContext',
        reason_ctx: 'ReasonContext',
    ) -> PatternContext:
        """
        Gather all pattern matches.

        Queries multiple engines and combines results into ranked suggestions.
        """
        suggestions: List[PatternMatch] = []

        # === Embedding Matches ===
        embedding_matches = self._get_embedding_matches(game_state, orient_ctx)
        suggestions.extend(embedding_matches)

        # === CODS Suggestion ===
        cods_suggestion = self._get_cods_suggestion(game_state, reason_ctx)
        if cods_suggestion and cods_suggestion.get('action'):
            suggestions.append(PatternMatch(
                action=cods_suggestion['action'],
                confidence=cods_suggestion.get('confidence', 0.7),
                source="cods",
                evidence=cods_suggestion.get('operator', 'unknown operator'),
            ))

        # === Universal Patterns ===
        universal_matches = self._get_universal_patterns(game_state, orient_ctx)
        suggestions.extend(universal_matches)

        # === Resonance Score ===
        resonance_score = self._get_resonance_score(game_state)

        # === Trigger Chains ===
        trigger_chains = self._get_trigger_chains(game_state)
        for chain in trigger_chains:
            if chain.get('next_action'):
                suggestions.append(PatternMatch(
                    action=chain['next_action'],
                    confidence=chain.get('confidence', 0.6),
                    source="trigger",
                    evidence=f"Trigger chain: {chain.get('pattern', 'unknown')}",
                ))

        # === Abstraction Template ===
        template = self._get_abstraction_template(game_state)
        if template and template.get('suggested_action'):
            suggestions.append(PatternMatch(
                action=template['suggested_action'],
                confidence=template.get('confidence', 0.65),
                source="abstraction",
                evidence=f"Template: {template.get('name', 'unknown')}",
            ))

        # === Sort by confidence ===
        suggestions.sort(key=lambda x: -x.confidence)

        # === Check for proven sequence ===
        has_proven = ground_ctx.network_sequence_available

        # Build context
        ctx = PatternContext(
            pattern_suggestions=suggestions,
            cods_suggestion=cods_suggestion,
            has_proven_sequence=has_proven,
            abstraction_template=template,
            resonance_score=resonance_score,
            trigger_chains=trigger_chains,
        )

        # Validate contract
        ctx.validate()

        logger.debug(
            f"[PATTERN] suggestions={len(suggestions)}, resonance={resonance_score:.2f}, "
            f"cods={'yes' if cods_suggestion else 'no'}, proven_seq={has_proven}"
        )

        return ctx

    def _get_embedding_matches(
        self,
        game_state: 'GameState',
        orient_ctx: 'OrientContext',
    ) -> List[PatternMatch]:
        """Get matches from embedding similarity."""
        matches: List[PatternMatch] = []

        embedding_matcher = self.engines.get('embedding_matcher')
        if not embedding_matcher:
            # Try self_model as fallback
            self_model = self.engines.get('self_model')
            if self_model and hasattr(self_model, 'get_embedding_suggested_action'):
                embedding_matcher = self_model

        if embedding_matcher:
            try:
                if hasattr(embedding_matcher, 'find_similar'):
                    results = embedding_matcher.find_similar(
                        game_state.frame,
                        game_type=game_state.game_type,
                        level=game_state.level,
                        top_k=3,
                    )
                    if results:
                        for r in results:
                            if r.get('action'):
                                matches.append(PatternMatch(
                                    action=r['action'],
                                    confidence=r.get('similarity', 0.5),
                                    source="embedding",
                                    evidence=f"Similar frame: {r.get('distance', 'unknown')}",
                                ))
                elif hasattr(embedding_matcher, 'get_embedding_suggested_action'):
                    result = embedding_matcher.get_embedding_suggested_action(
                        game_type=game_state.game_type,
                        level=game_state.level,
                        current_frame=game_state.frame,
                        top_k=3,
                    )
                    if result and result.get('action'):
                        matches.append(PatternMatch(
                            action=result['action'],
                            confidence=result.get('confidence', 0.5),
                            source="embedding",
                            evidence="Neural similarity match",
                        ))
            except Exception as e:
                logger.debug(f"[PATTERN] EmbeddingMatcher error: {e}")

        return matches

    def _get_cods_suggestion(
        self,
        game_state: 'GameState',
        reason_ctx: 'ReasonContext',
    ) -> Optional[Dict[str, Any]]:
        """Get CODS operator suggestion."""
        cods_engine = self.engines.get('cods_engine')
        if cods_engine:
            try:
                if hasattr(cods_engine, 'suggest_action'):
                    result = cods_engine.suggest_action(
                        game_id=game_state.game_id,
                        level=game_state.level,
                        frame=game_state.frame,
                        action_number=game_state.action_number,
                    )
                    if result:
                        return result
            except Exception as e:
                logger.debug(f"[PATTERN] CODSEngine error: {e}")

        return None

    def _get_universal_patterns(
        self,
        game_state: 'GameState',
        orient_ctx: 'OrientContext',
    ) -> List[PatternMatch]:
        """Get matches from universal pattern engine."""
        matches: List[PatternMatch] = []

        universal_engine = self.engines.get('universal_patterns')
        if universal_engine:
            try:
                if hasattr(universal_engine, 'match_patterns'):
                    results = universal_engine.match_patterns(
                        frame=game_state.frame,
                        world_model=orient_ctx.world_model,
                    )
                    if results:
                        for r in results:
                            if r.get('action'):
                                matches.append(PatternMatch(
                                    action=r['action'],
                                    confidence=r.get('confidence', 0.5),
                                    source="universal",
                                    evidence=f"Universal pattern: {r.get('pattern_name', 'unknown')}",
                                ))
            except Exception as e:
                logger.debug(f"[PATTERN] UniversalPatternEngine error: {e}")

        return matches

    def _get_resonance_score(self, game_state: 'GameState') -> float:
        """Get cross-domain resonance score."""
        resonance_detector = self.engines.get('resonance_detector')
        if resonance_detector:
            try:
                if hasattr(resonance_detector, 'get_resonance_score'):
                    score = resonance_detector.get_resonance_score(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if score is not None:
                        return max(0.0, min(1.0, float(score)))
                elif hasattr(resonance_detector, 'get_resonant_patterns'):
                    patterns = resonance_detector.get_resonant_patterns(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if patterns:
                        # Average confidence of resonant patterns
                        total = sum(p.get('confidence', 0.5) for p in patterns)
                        return min(1.0, total / len(patterns))
            except Exception as e:
                logger.debug(f"[PATTERN] ResonanceDetector error: {e}")

        return 0.0

    def _get_trigger_chains(self, game_state: 'GameState') -> List[Dict[str, Any]]:
        """Get trigger sequence chains."""
        chains: List[Dict[str, Any]] = []

        trigger_tracker = self.engines.get('trigger_sequences')
        if trigger_tracker:
            try:
                if hasattr(trigger_tracker, 'get_chains'):
                    result = trigger_tracker.get_chains(
                        game_id=game_state.game_id,
                        level=game_state.level,
                        action_number=game_state.action_number,
                    )
                    if result:
                        chains.extend(result)
            except Exception as e:
                logger.debug(f"[PATTERN] TriggerSequenceTracker error: {e}")

        return chains

    def _get_abstraction_template(
        self, game_state: 'GameState'
    ) -> Optional[Dict[str, Any]]:
        """Get applicable abstraction template."""
        abstraction_engine = self.engines.get('abstraction_engine')
        if abstraction_engine:
            try:
                if hasattr(abstraction_engine, 'get_template'):
                    template = abstraction_engine.get_template(
                        game_type=game_state.game_type,
                        level=game_state.level,
                        action_number=game_state.action_number,
                    )
                    if template:
                        return template
                elif hasattr(abstraction_engine, 'should_use_template'):
                    should_use = abstraction_engine.should_use_template(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if should_use:
                        return {'should_use': True, 'confidence': 0.6}
            except Exception as e:
                logger.debug(f"[PATTERN] AbstractionEngine error: {e}")

        return None
