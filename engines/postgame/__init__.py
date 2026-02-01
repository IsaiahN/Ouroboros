import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Post-Game Processing Module
===========================

This module consolidates ALL post-game processing into one location:

1. FITNESS CALCULATION (fitness_calculator.py)
   - RLVR rewards calculation
   - Evolutionary fitness scoring
   - Win/efficiency/exploration bonuses

2. LESSONS EXTRACTION (lessons_extractor.py)
   - Extract rules learned from the game
   - Identify what worked vs what failed
   - Generate transferable lessons for viral packages

3. REPLAY LEARNING (replay_learning.py)
   - Learn WHY sequences work
   - Generate predictions and verify against outcomes
   - Induce rules and primitives from replays

4. ORCHESTRATION (orchestrator.py)
   - Coordinate all post-game processing
   - Single entry point for game_loop.py
   - Ensure correct order of operations

Usage:
    from engines.postgame import PostGameProcessor
    
    processor = PostGameProcessor(db)
    
    # Call at game end from game_loop.py
    result = processor.process_game_end(
        game_result=result,
        agent_id=agent_id,
        action_sequence=actions,
        frame_history=frames
    )

Following Rules:
- Rule 2: All data stored in database
- Rule 3: Clean integration, no orphaned code
- Rule 10: Enhance existing architecture
"""

from .orchestrator import PostGameProcessor
from .fitness_calculator import FitnessCalculator
from .lessons_extractor import LessonsExtractor
from .replay_learning import ReplayLearner

__all__ = [
    'PostGameProcessor',
    'FitnessCalculator',
    'LessonsExtractor',
    'ReplayLearner',
]
