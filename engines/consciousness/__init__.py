"""Consciousness package for self-reflection, identity, and sensation.

This package contains modules for:
- Weaving reports (self-reflection)
- I-Thread (identity and stream weighting)
- Sensation engine (emotional coloring)
- Persona management (death personas, etc.)
"""

from engines.consciousness.weaving_reporter import WeavingReporter

# Lazy imports to avoid circular dependencies
def get_i_thread():
    from engines.consciousness.i_thread import IThread, DeliberationEngine, ROLE_DEFAULT_WEIGHTS
    return IThread, DeliberationEngine, ROLE_DEFAULT_WEIGHTS

def get_sensation_engine():
    from engines.consciousness.sensation_engine import SensationEngine, get_sensation_mode
    return SensationEngine, get_sensation_mode

def get_persona_manager():
    from engines.consciousness.persona_runtime import PersonaManager, PersonaDecision
    return PersonaManager, PersonaDecision

__all__ = ['WeavingReporter', 'get_i_thread', 'get_sensation_engine', 'get_persona_manager']
