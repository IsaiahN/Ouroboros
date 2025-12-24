#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Configuration for Sequence Abstraction Engine
==============================================

Feature flags, settings, and backwards compatibility controls.
"""

# Feature flag - NOW ENABLED BY DEFAULT (abstractions replace ubersequences)
ENABLE_ABSTRACTION = os.getenv('ENABLE_ABSTRACTION', 'true').lower() == 'true'

# Abstraction levels
ABSTRACTION_LEVELS = {
    'L1_OBJECT': 1,      # Pixel → Object
    'L2_ACTION': 2,      # Object → Action
    'L3_STRATEGY': 3,    # Action → Strategy
    'L4_CONCEPT': 4      # Strategy → Concept
}

# Matching modes
MATCHING_MODES = {
    'EXACT': 'exact',              # Original exact matching only
    'HYBRID': 'hybrid',            # Try exact, fall back to conceptual
    'CONCEPTUAL': 'conceptual'     # Conceptual only (experimental)
}

# Default mode for all agents
DEFAULT_MATCHING_MODE = MATCHING_MODES['HYBRID']

# Confidence thresholds
MIN_CONCEPTUAL_CONFIDENCE = 0.7    # Minimum confidence for conceptual match
MIN_ADAPTATION_CONFIDENCE = 0.6    # Minimum confidence for sequence adaptation

# Pattern recognition settings
MIN_PATTERN_FREQUENCY = 3          # Minimum occurrences to establish pattern
PATTERN_SIMILARITY_THRESHOLD = 0.75 # How similar patterns must be to group

# Performance settings
LAZY_EXTRACTION = True             # Extract concepts on-demand, not upfront
ASYNC_EXTRACTION = True            # Extract in background threads
MAX_EXTRACTION_THREADS = 4         # Max concurrent concept extraction threads

# Database settings
ABSTRACTION_DB_TABLES = [
    'detected_objects',
    'object_tracks',
    'action_effects',
    'causal_chains',
    'movement_patterns',
    'sequence_concepts',
    'abstraction_metrics'
]

# Logging
LOG_ABSTRACTION = True
LOG_LEVEL = 'INFO'

# A/B Testing
AB_TEST_ENABLED = False            # Enable A/B testing of exact vs conceptual
AB_TEST_SAMPLE_RATE = 0.5          # 50% of games use each method

def is_abstraction_enabled():
    """Check if abstraction engine is enabled."""
    return ENABLE_ABSTRACTION

def get_default_matching_mode():
    """Get default matching mode for agents."""
    if not ENABLE_ABSTRACTION:
        return MATCHING_MODES['EXACT']
    return DEFAULT_MATCHING_MODE

def get_abstraction_config():
    """Get full abstraction configuration dictionary."""
    return {
        'enabled': ENABLE_ABSTRACTION,
        'matching_mode': get_default_matching_mode(),
        'levels': ABSTRACTION_LEVELS,
        'min_conceptual_confidence': MIN_CONCEPTUAL_CONFIDENCE,
        'min_adaptation_confidence': MIN_ADAPTATION_CONFIDENCE,
        'min_pattern_frequency': MIN_PATTERN_FREQUENCY,
        'pattern_similarity_threshold': PATTERN_SIMILARITY_THRESHOLD,
        'lazy_extraction': LAZY_EXTRACTION,
        'async_extraction': ASYNC_EXTRACTION,
        'max_extraction_threads': MAX_EXTRACTION_THREADS,
        'log_abstraction': LOG_ABSTRACTION,
        'ab_test_enabled': AB_TEST_ENABLED
    }
