"""Social package for network contribution, viral knowledge, and peer learning.

This package contains modules for:
- Network contribution (knowledge sharing)
- Hypothesis system (collaborative hypothesis formation)
- Viral packages (knowledge spread)
- Resonance detection (cross-agent patterns)
- Prestige scoring (agent reputation)
- Primitive suggester (direct primitive-to-action mapping)

Note: CODS engine has been deprecated and moved to deprecated/cods_system/.
The PrimitiveSuggester provides direct primitive application without unlock ceremonies.
"""

from engines.social.hypothesis_system import AgentHypothesisSystem
from engines.social.network_contributor import AgentNetworkContributor


# Lazy imports for heavier modules
def get_viral_package_engine():
    from engines.social.viral_package_engine import (
        ViralPackageEngine,
        get_cohort_wisdom,
        update_sequence_role_reputation,
    )
    return ViralPackageEngine, get_cohort_wisdom, update_sequence_role_reputation

def get_resonance_detector():
    from engines.social.resonance_detector import (
        ResonanceDetector,
        should_query_resonance,
    )
    return ResonanceDetector, should_query_resonance

def get_prestige_engine():
    from engines.social.prestige_engine import (
        PrestigeEngine,
        display_prestige_leaderboard,
    )
    return PrestigeEngine, display_prestige_leaderboard

def get_primitive_suggester():
    """Get PrimitiveSuggester for direct primitive-to-action mapping."""
    from engines.social.primitive_suggester import PrimitiveSuggester
    from engines.social.primitive_suggester import get_primitive_suggester as _get
    return PrimitiveSuggester, _get

# Backward compatibility stub - raises warning
def get_cods_engine():
    """DEPRECATED: CODS engine has been replaced by PrimitiveSuggester."""
    import warnings
    warnings.warn(
        "get_cods_engine() is deprecated. Use get_primitive_suggester() instead. "
        "CODS files moved to deprecated/cods_system/",
        DeprecationWarning,
        stacklevel=2
    )
    # Return stub classes that won't break existing code but won't do anything useful
    class CODSEngineStub:
        def __init__(self, *args, **kwargs):
            pass
        def get_action_suggestion(self, *args, **kwargs):
            return None
    class CODSGameContextStub:
        pass
    return CODSEngineStub, CODSGameContextStub, lambda: CODSEngineStub()

__all__ = [
    'AgentNetworkContributor', 'AgentHypothesisSystem',
    'get_viral_package_engine', 'get_resonance_detector', 'get_prestige_engine',
    'get_primitive_suggester',
    'get_cods_engine',  # Deprecated stub for backward compatibility
]
