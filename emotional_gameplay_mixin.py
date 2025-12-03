#!/usr/bin/env python3
"""
Gameplay Engine with Somatic Profiles
======================================

Wrapper around GameplayEngine that adds emotional intelligence via somatic profiles.
Agents get role-specific emotional modifiers for decision-making.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from somatic_profile_system import SomaticProfileSystem
import logging

logger = logging.getLogger(__name__)

class EmotionalGameplayMixin:
    """Mixin to add somatic profiles to gameplay."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with somatic profiles."""
        super().__init__(*args, **kwargs)
        
        # Add somatic profile system
        try:
            db_path = kwargs.get('db_path', 'core_data.db')
            self.somatic_system = SomaticProfileSystem(db_path)
            logger.info("Somatic profiles enabled")
        except Exception as e:
            logger.warning(f"Somatic profiles not available: {e}")
            self.somatic_system = None
    
    def get_emotional_modifier(self, agent_type: str, emotion_type: str, base_value: float) -> float:
        """
        Get emotionally-modified value for agent.
        
        Args:
            agent_type: Agent role (Pioneer, Exploiter, Optimizer, Generalist)
            emotion_type: Type of emotion (curiosity, fear, skepticism, etc.)
            base_value: Base value before modification
        
        Returns:
            Modified value based on agent's somatic profile
        """
        if not self.somatic_system:
            return base_value
        
        return self.somatic_system.apply_emotional_modifiers(agent_type, emotion_type, base_value)
    
    def log_emotional_state(self, agent_id: str, game_id: str, level_number: int,
                           agent_type: str, emotion_type: str, base_value: float):
        """Log agent's emotional state."""
        if self.somatic_system:
            self.somatic_system.log_emotional_state(
                agent_id, game_id, level_number,
                agent_type, emotion_type, base_value
            )

def get_agent_somatic_profile(agent_type: str) -> dict:
    """
    Get somatic profile for agent type.
    
    Args:
        agent_type: Agent role
    
    Returns:
        Somatic profile dictionary
    """
    sps = SomaticProfileSystem()
    return sps.get_profile_for_role(agent_type)

if __name__ == "__main__":
    # Test somatic profiles
    print("=" * 70)
    print("SOMATIC PROFILES TEST")
    print("=" * 70)
    
    roles = ['Pioneer', 'Exploiter', 'Optimizer', 'Generalist']
    
    for role in roles:
        profile = get_agent_somatic_profile(role)
        print(f"\n{role}: {profile['name']}")
        
        # Test curiosity modifier
        sps = SomaticProfileSystem()
        curiosity = sps.apply_emotional_modifiers(role, 'curiosity', 1.0)
        if curiosity != 1.0:
            print(f"  Curiosity: {curiosity:.1f}x")
    
    print("\n[OK] Somatic profiles working!")
