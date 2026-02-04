"""
Engine Registry - Data-Driven Lazy-Loading Central Access
==========================================================

REFACTORED: January 31, 2026
- Data-driven loading (no more 20+ individual loader methods)
- All import errors logged (no silent failures)
- Cleaner architecture

Provides lazy-loaded access to all engines via a single registry.
Engines are only instantiated when first accessed.

This enables:
1. Fast startup (no loading unused engines)
2. Single point of configuration (db_path, etc.)
3. Easy mocking for tests
4. Graceful degradation with LOGGED errors (not silent)

Usage:
    from engines.registry import EngineRegistry

    registry = EngineRegistry(db_path="core_data.db")

    # Access via properties
    if registry.self_model:
        suggestion = registry.self_model.get_embedding_suggested_action(...)

    # Or by name
    engine = registry.get('scientific_method')
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import importlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from engines.engine_logger import get_engine_logger, log_import_error

# Note: TYPE_CHECKING imports removed - interfaces not yet implemented
# TODO: Add back when engines/interfaces.py is fully typed:
# if TYPE_CHECKING:
#     from engines.interfaces import SelfModelInterface, VisualAnalyzerInterface, etc.

logger = get_engine_logger("registry")


# =============================================================================
# ENGINE LOADER CONFIGURATION
# =============================================================================
# Format: 'engine_name': EngineConfig(...)
# - module: Full module path to import from
# - class_name: Class to instantiate
# - requires_db: True if constructor needs DatabaseInterface
# - requires_db_path: True if constructor needs db_path string
# - fallback_legacy_attr: Attribute on legacy_core to use as fallback

@dataclass
class EngineConfig:
    """Configuration for loading an engine."""
    module: str
    class_name: str
    requires_db: bool = False
    requires_db_path: bool = False  # Some engines take path, not interface
    fallback_legacy_attr: Optional[str] = None  # Attribute on legacy_core


ENGINE_CONFIGS: Dict[str, EngineConfig] = {
    # =========================================================================
    # Self-Model Engines
    # =========================================================================
    'self_model': EngineConfig(
        module='engines.self_model.cognitive_core',
        class_name='CognitiveCore',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'embedding_matcher': EngineConfig(
        module='engines.self_model',
        class_name='EmbeddingMatcher',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'few_shot_relations': EngineConfig(
        module='engines.self_model',
        class_name='FewShotRelations',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'network_sharing': EngineConfig(
        module='engines.self_model',
        class_name='NetworkSharingEngine',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'action6_behavior': EngineConfig(
        module='engines.self_model',
        class_name='Action6BehaviorEngine',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'control_tracker': EngineConfig(
        module='engines.self_model.control_tracker',
        class_name='ControlTracker',
        requires_db_path=True
    ),
    'discovery_engine': EngineConfig(
        module='engines.self_model.discovery_engine',
        class_name='DiscoveryEngine',
        requires_db_path=True
    ),
    'grid_analyzer': EngineConfig(
        module='engines.self_model.grid_analysis',
        class_name='GridAnalyzer'
    ),
    'trigger_sequences': EngineConfig(
        module='engines.self_model.trigger_sequences',
        class_name='TriggerSequenceTracker',
        requires_db_path=True
    ),
    'valence_goals': EngineConfig(
        module='engines.self_model.valence_goals',
        class_name='ValenceGoalEngine',
        requires_db_path=True
    ),
    'universal_patterns': EngineConfig(
        module='engines.self_model.universal_patterns',
        class_name='UniversalPatternEngine',
        requires_db_path=True
    ),
    'click_behavior': EngineConfig(
        module='engines.self_model.click_behavior',
        class_name='ClickBehaviorClassifier',
        requires_db_path=True
    ),
    'belief_system': EngineConfig(
        module='engines.self_model.belief_system',
        class_name='BeliefSystem',
        requires_db_path=True
    ),

    # =========================================================================
    # Perception Engines
    # =========================================================================
    'visual_analyzer': EngineConfig(
        module='engines.perception.visual_analyzer',
        class_name='VisualAnalyzer',
        fallback_legacy_attr='visual_analyzer'
    ),
    'terminal_pattern_detector': EngineConfig(
        module='engines.perception.terminal_pattern_detector',
        class_name='TerminalPatternDetector',
        requires_db=True,
        fallback_legacy_attr='terminal_pattern_detector'
    ),

    # =========================================================================
    # Cognition Engines
    # =========================================================================
    'metacognitive_engine': EngineConfig(
        module='engines.cognition',
        class_name='MetacognitiveReasoningEngine',
        requires_db=True,
        fallback_legacy_attr='agent_self_model'
    ),

    # =========================================================================
    # Memory Engines
    # =========================================================================
    'episodic_memory': EngineConfig(
        module='engines.memory',
        class_name='EpisodicMemorySystem',
        requires_db_path=True,
        fallback_legacy_attr='agent_self_model'
    ),
    'near_miss_analyzer': EngineConfig(
        module='engines.memory.near_miss_analyzer',
        class_name='NearMissAnalyzer',
        requires_db=True,
        fallback_legacy_attr='near_miss_analyzer'
    ),

    # =========================================================================
    # Social Engines
    # =========================================================================
    'primitive_suggester': EngineConfig(
        module='engines.social.primitive_suggester',
        class_name='PrimitiveSuggester',
        requires_db=True
    ),
    # DEPRECATED: cods_engine replaced by primitive_suggester (Jan 2026)
    # All 315 primitives now always available - no unlock ceremony needed
    'viral_package_engine': EngineConfig(
        module='engines.social.viral_package_engine',
        class_name='ViralPackageEngine',
        requires_db=True,
        fallback_legacy_attr='viral_package_engine'
    ),
    'resonance_detector': EngineConfig(
        module='engines.social.resonance_detector',
        class_name='ResonanceDetector',
        requires_db=True,
        fallback_legacy_attr='resonance_detector'
    ),

    # =========================================================================
    # Consciousness Engines
    # =========================================================================
    'sensation_engine': EngineConfig(
        module='engines.consciousness.sensation_engine',
        class_name='SensationEngine',
        requires_db=True,
        fallback_legacy_attr='sensation_engine'
    ),
    'i_thread': EngineConfig(
        module='engines.consciousness.i_thread',
        class_name='IThread',
        requires_db=True,
        fallback_legacy_attr='i_thread'
    ),

    # =========================================================================
    # Regulation Engines
    # =========================================================================
    'frustration_detector': EngineConfig(
        module='engines.regulation.frustration_detector',
        class_name='FrustrationDetector',
        requires_db=True,
        fallback_legacy_attr='frustration_detector'
    ),
    'regulatory_engine': EngineConfig(
        module='engines.regulation.regulatory_signal_engine',
        class_name='RegulatorySignalEngine',
        requires_db=True,
        fallback_legacy_attr='regulatory_engine'
    ),
    'imagination_budget': EngineConfig(
        module='engines.regulation.imagination_budget',
        class_name='ImaginationBudgetManager'
    ),
    'network_exploration_tracker': EngineConfig(
        module='engines.regulation.network_exploration_tracker',
        class_name='NetworkExplorationTracker',
        requires_db_path=True,
        fallback_legacy_attr='network_exploration_tracker'
    ),

    # =========================================================================
    # Planning Engines
    # =========================================================================
    'subgoal_planner': EngineConfig(
        module='engines.planning.subgoal_planner',
        class_name='SubgoalPlanner',
        requires_db=True,
        fallback_legacy_attr='subgoal_planner'
    ),
    'abstraction_engine': EngineConfig(
        module='engines.planning.sequence_abstraction',
        class_name='SequenceAbstraction',
        requires_db_path=True,
        fallback_legacy_attr='abstraction_engine'
    ),
    'replay_learning_engine': EngineConfig(
        module='engines.planning.replay_learning_engine',
        class_name='ReplayLearningEngine',
        requires_db=True,
        fallback_legacy_attr='replay_learning_engine'
    ),

    # =========================================================================
    # Reasoning Engines
    # =========================================================================
    'scientific_method_engine': EngineConfig(
        module='engines.reasoning.scientific_method_engine',
        class_name='ScientificMethodEngine',
        requires_db_path=True,
        fallback_legacy_attr='scientific_method_engine'
    ),
    'hypothesis_system': EngineConfig(
        module='engines.social.hypothesis_system',
        class_name='AgentHypothesisSystem',
        requires_db=True,
        fallback_legacy_attr='hypothesis_system'
    ),
    'symbolic_tracker': EngineConfig(
        module='engines.self_model.symbolic_tracker',
        class_name='SymbolicStateTracker',
        requires_db=True
    ),

    # =========================================================================
    # Other Engines
    # =========================================================================
    'breakthrough_allocator': EngineConfig(
        module='breakthrough_budget_allocator',
        class_name='BreakthroughBudgetAllocator',
        requires_db=True,
        fallback_legacy_attr='breakthrough_allocator'
    ),
    'multi_stage_pipeline': EngineConfig(
        module='multi_stage_matching_pipeline',
        class_name='MultiStageMatchingPipeline',
        requires_db=True,
        fallback_legacy_attr='multi_stage_pipeline'
    ),
}


class EngineRegistry:
    """
    Central registry for all decision engines.

    Lazily loads engines on first access to minimize startup time.
    Falls back to legacy implementations if new modules not available.
    ALL import errors are logged (no silent failures).
    """

    def __init__(self, db_path: str = "core_data.db", legacy_core: Any = None):
        """
        Initialize the registry.

        Args:
            db_path: Path to the database
            legacy_core: Optional reference to legacy CoreGameplay for fallback
        """
        self._db_path = db_path
        self._legacy_core = legacy_core
        self._engines: Dict[str, Any] = {}
        self._loaded: Set[str] = set()
        self._load_errors: Dict[str, str] = {}
        self._db_interface: Optional[Any] = None  # Lazy-loaded

        logger.info("Registry initialized", db_path=db_path)

    def _get_db_interface(self) -> Any:
        """Get or create DatabaseInterface (lazy loaded)."""
        if self._db_interface is None:
            try:
                from database_interface import DatabaseInterface
                self._db_interface = DatabaseInterface(self._db_path)
            except ImportError as e:
                logger.error("Failed to import DatabaseInterface", exc=e)
                raise
        return self._db_interface

    def get(self, name: str) -> Optional[Any]:
        """
        Get engine by name, lazy-loading if needed.

        Args:
            name: Engine name (e.g., 'self_model', 'visual_analyzer')

        Returns:
            Engine instance or None if unavailable
        """
        if name not in self._loaded:
            self._load_engine(name)
        return self._engines.get(name)

    def _load_engine(self, name: str) -> None:
        """Load engine using data-driven configuration."""
        if name in self._loaded:
            return

        self._loaded.add(name)

        # Check if we have a configuration for this engine
        if name not in ENGINE_CONFIGS:
            # Handle special cases (stubs, action_handler)
            engine = self._load_special_engine(name)
            if engine:
                self._engines[name] = engine
            return

        config = ENGINE_CONFIGS[name]

        # Try to load the engine
        try:
            module = importlib.import_module(config.module)
            cls = getattr(module, config.class_name)

            # Instantiate with appropriate arguments
            if config.requires_db:
                db = self._get_db_interface()
                engine = cls(db)
            elif config.requires_db_path:
                engine = cls(self._db_path)
            else:
                engine = cls()

            self._engines[name] = engine
            logger.debug(f"Loaded engine: {name}", module=config.module)
            return

        except ImportError as e:
            log_import_error(name, config.module, e)
            self._load_errors[name] = f"ImportError: {e}"

        except AttributeError as e:
            logger.warning(
                f"Class not found: {config.class_name}",
                module=config.module,
                error=str(e)
            )
            self._load_errors[name] = f"AttributeError: {e}"

        except Exception as e:
            logger.error(f"Failed to instantiate {name}", exc=e)
            self._load_errors[name] = f"{type(e).__name__}: {e}"

        # Try fallback to legacy_core
        if config.fallback_legacy_attr and self._legacy_core:
            if hasattr(self._legacy_core, config.fallback_legacy_attr):
                engine = getattr(self._legacy_core, config.fallback_legacy_attr)
                self._engines[name] = engine
                logger.debug(f"Using legacy fallback for {name}")
                return

        # Engine unavailable
        logger.warning(f"Engine unavailable: {name}")

    def _load_special_engine(self, name: str) -> Optional[Any]:  # noqa: ANN401
        """Load engines that need special handling."""
        if name == 'action_handler':
            # Action handler requires session manager, can't standalone load
            if self._legacy_core and hasattr(self._legacy_core, 'action_handler'):
                return self._legacy_core.action_handler
            return None

        logger.warning(f"Unknown engine: {name}")
        return None

    # =========================================================================
    # PROPERTY ACCESS (Preferred way to access engines)
    # Keep for IDE autocomplete and type hints
    # =========================================================================

    @property
    def self_model(self) -> Optional[Any]:
        return self.get('self_model')

    @property
    def embedding_matcher(self) -> Optional[Any]:
        return self.get('embedding_matcher')

    @property
    def few_shot_relations(self) -> Optional[Any]:
        return self.get('few_shot_relations')

    @property
    def metacognitive_engine(self) -> Optional[Any]:
        return self.get('metacognitive_engine')

    @property
    def episodic_memory(self) -> Optional[Any]:
        return self.get('episodic_memory')

    @property
    def network_sharing(self) -> Optional[Any]:
        return self.get('network_sharing')

    @property
    def action6_behavior(self) -> Optional[Any]:
        return self.get('action6_behavior')

    @property
    def visual_analyzer(self) -> Optional[Any]:
        return self.get('visual_analyzer')

    @property
    def terminal_pattern_detector(self) -> Optional[Any]:
        return self.get('terminal_pattern_detector')

    @property
    def scientific_method_engine(self) -> Optional[Any]:
        return self.get('scientific_method_engine')

    @property
    def primitive_suggester(self) -> Optional[Any]:
        """Direct primitive-to-action mapping (replaces deprecated CODS)."""
        return self.get('primitive_suggester')

    @property
    def cods_engine(self) -> Optional[Any]:
        """DEPRECATED: Use primitive_suggester instead."""
        import warnings
        warnings.warn("cods_engine is deprecated, use primitive_suggester", DeprecationWarning)
        return self.get('primitive_suggester')  # Return primitive_suggester as fallback

    @property
    def viral_package_engine(self) -> Optional[Any]:
        return self.get('viral_package_engine')

    @property
    def frustration_detector(self) -> Optional[Any]:
        return self.get('frustration_detector')

    @property
    def sensation_engine(self) -> Optional[Any]:
        return self.get('sensation_engine')

    @property
    def i_thread(self) -> Optional[Any]:
        return self.get('i_thread')

    @property
    def near_miss_analyzer(self) -> Optional[Any]:
        return self.get('near_miss_analyzer')

    @property
    def subgoal_planner(self) -> Optional[Any]:
        return self.get('subgoal_planner')

    @property
    def breakthrough_allocator(self) -> Optional[Any]:
        return self.get('breakthrough_allocator')

    @property
    def regulatory_engine(self) -> Optional[Any]:
        return self.get('regulatory_engine')

    @property
    def resonance_detector(self) -> Optional[Any]:
        return self.get('resonance_detector')

    @property
    def action_handler(self) -> Optional[Any]:
        return self.get('action_handler')

    @property
    def multi_stage_pipeline(self) -> Optional[Any]:
        return self.get('multi_stage_pipeline')

    @property
    def abstraction_engine(self) -> Optional[Any]:
        return self.get('abstraction_engine')

    @property
    def replay_learning_engine(self) -> Optional[Any]:
        return self.get('replay_learning_engine')

    @property
    def imagination_budget(self) -> Optional[Any]:
        return self.get('imagination_budget')

    @property
    def network_exploration_tracker(self) -> Optional[Any]:
        return self.get('network_exploration_tracker')

    @property
    def control_tracker(self) -> Optional[Any]:
        return self.get('control_tracker')

    @property
    def discovery_engine(self) -> Optional[Any]:
        return self.get('discovery_engine')

    @property
    def grid_analyzer(self) -> Optional[Any]:
        return self.get('grid_analyzer')

    @property
    def trigger_sequences(self) -> Optional[Any]:
        return self.get('trigger_sequences')

    @property
    def valence_goals(self) -> Optional[Any]:
        return self.get('valence_goals')

    @property
    def universal_patterns(self) -> Optional[Any]:
        return self.get('universal_patterns')

    @property
    def click_behavior(self) -> Optional[Any]:
        return self.get('click_behavior')

    @property
    def belief_system(self) -> Optional[Any]:
        return self.get('belief_system')

    @property
    def hypothesis_system(self) -> Optional[Any]:
        return self.get('hypothesis_system')

    @property
    def symbolic_tracker(self) -> Optional[Any]:
        return self.get('symbolic_tracker')

    # =========================================================================
    # DIAGNOSTICS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get loading status for all engines."""
        all_engines = list(ENGINE_CONFIGS.keys()) + ['action_handler']

        status = {}
        for name in all_engines:
            if name in self._loaded:
                if name in self._engines:
                    status[name] = 'loaded'
                elif name in self._load_errors:
                    status[name] = f'error: {self._load_errors[name]}'
                else:
                    status[name] = 'unavailable'
            else:
                status[name] = 'not_loaded'

        return {
            'engines': status,
            'loaded_count': len(self._engines),
            'error_count': len(self._load_errors),
            'errors': self._load_errors,
        }

    def preload_all(self) -> Dict[str, str]:
        """
        Preload all engines (for diagnostics or warm start).

        Returns:
            Dict mapping engine name to status
        """
        all_engines = list(ENGINE_CONFIGS.keys()) + ['action_handler']

        results: Dict[str, str] = {}
        for name in all_engines:
            self.get(name)
            if name in self._engines:
                results[name] = 'loaded'
            elif name in self._load_errors:
                results[name] = self._load_errors[name]
            else:
                results[name] = 'unavailable'

        logger.info(
            f"Preloaded engines",
            loaded=len(self._engines),
            errors=len(self._load_errors)
        )
        return results


# =============================================================================
# MODULE-LEVEL SINGLETON (optional convenience)
# =============================================================================

_default_registry: Optional[EngineRegistry] = None

def get_registry(db_path: str = "core_data.db") -> EngineRegistry:
    """Get or create the default engine registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = EngineRegistry(db_path)
    return _default_registry


__all__ = ['EngineRegistry', 'get_registry', 'ENGINE_CONFIGS']
