"""
Rungs Package
=============
Unified registry of all decision rungs, grouped by cognitive domain.

Usage::

    from rungs import RUNG_REGISTRY   # Dict[str, Type[DecisionRung]]

The registry is the single source of truth consumed by
``DecisionRungSystem.RUNG_REGISTRY``.
"""

from rungs.base import (  # noqa: F401 – re-export for convenience
    Action6CoordinateProvider,
    DecisionRung,
    DecisionStrategy,
    KnowledgeProvenance,
    RungResult,
    filter_available_actions,
    get_available_action_weights,
    get_available_actions_list,
    get_random_available_action,
    is_action_available,
    validate_action,
)
from rungs.emergency import RUNGS as _emergency
from rungs.exploitation import RUNGS as _exploitation
from rungs.exploration import RUNGS as _exploration
from rungs.filter_rungs import RUNGS as _filter
from rungs.hypothesis import RUNGS as _hypothesis

# Import domain registries
from rungs.orientation import RUNGS as _orientation

# Merge into a single flat registry with collision detection (Phase 4.2)
RUNG_REGISTRY: dict = {}
_DOMAIN_NAMES = (
    ('orientation', _orientation),
    ('hypothesis', _hypothesis),
    ('exploitation', _exploitation),
    ('filter', _filter),
    ('emergency', _emergency),
    ('exploration', _exploration),
)
for _domain_name, _domain in _DOMAIN_NAMES:
    for _key in _domain:
        if _key in RUNG_REGISTRY:
            raise ImportError(
                f"Rung registry collision: '{_key}' already registered "
                f"(duplicate found in '{_domain_name}' domain)"
            )
    RUNG_REGISTRY.update(_domain)

__all__ = [
    'RUNG_REGISTRY',
    # Base types re-exported
    'DecisionRung',
    'DecisionStrategy',
    'RungResult',
    'KnowledgeProvenance',
    'Action6CoordinateProvider',
    # Utility functions re-exported
    'filter_available_actions',
    'get_available_action_weights',
    'get_available_actions_list',
    'get_random_available_action',
    'is_action_available',
    'validate_action',
]
