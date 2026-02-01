"""
Decision Phases Package
=======================

Contains the 7 phase implementations:
- emergency.py: Pre-phase safety checks
- phase1_orient.py: "What world am I in?"
- phase2_ground_truth.py: "What do I empirically know?"
- phase3_reason.py: "What should I believe?"
- phase4_pattern.py: "Have I seen this before?"
- phase5_propose.py: "What's my best move?"
- phase6_filter.py: "Remove bad options"
- phase7_select.py: "Final weighted decision"
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from engines.decision.phases.emergency import EmergencyCheck, EmergencyThresholds
from engines.decision.phases.phase1_orient import OrientPhase
from engines.decision.phases.phase2_ground_truth import GroundTruthPhase
from engines.decision.phases.phase3_reason import ReasonPhase
from engines.decision.phases.phase4_pattern import PatternPhase
from engines.decision.phases.phase5_propose import ProposePhase
from engines.decision.phases.phase6_filter import FilterPhase
from engines.decision.phases.phase7_select import SelectPhase

__all__ = [
    'EmergencyCheck',
    'EmergencyThresholds',
    'OrientPhase',
    'GroundTruthPhase',
    'ReasonPhase',
    'PatternPhase',
    'ProposePhase',
    'FilterPhase',
    'SelectPhase',
]
