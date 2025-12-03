#!/usr/bin/env python3
"""
Somatic Profile System
======================

Role-specific emotional intelligence for agents.
Modifies how agents "feel" about situations without hard-coding strategies.

Following Rule 2: All data in database (emotional state logged)
Following Rule 4: LLM self-management (autonomous emotional modulation)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Dict
from database_interface import DatabaseInterface

# Somatic profiles per role (from task.md)
SOMATIC_PROFILES = {
    'Pioneer': {
        'name': 'Optimistic Resilience',
        'multipliers': {
            'curiosity': 3.0,
            'optimism': 2.0,
            'confidence': 1.5
        },
        'dampeners': {
            'fear_of_failure': 0.3,
            'network_pessimism': 0.5
        },
        'overrides': {
            'confidence_boost_on_frontier': 2.0  # Extra boost when pioneering
        }
    },
    'Exploiter': {
        'name': 'Critical Pragmatism',
        'multipliers': {
            'skepticism': 2.0,
            'precision_satisfaction': 3.0,
            'critical_thinking': 2.5
        },
        'dampeners': {
            'network_consensus_bias': 0.3,  # Amplifies negative network data
            'complacency': 0.2
        },
        'overrides': {}
    },
    'Optimizer': {
        'name': 'Efficiency OCD',
        'multipliers': {
            'latency_aversion': 3.0,
            'elegance_reward': 1.5,
            'perfectionism': 2.0
        },
        'dampeners': {},
        'overrides': {
            'network_benchmark_sensitivity': 2.0  # Strong +/- based on comparison
        }
    },
    'Generalist': {
        'name': 'Stable Equilibrium',
        'multipliers': {
            # All 1.0 - pure reflection of history/network
        },
        'dampeners': {},
        'overrides': {}
    }
}

class SomaticProfileSystem:
    """Manage and apply somatic profiles for agents."""
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db = DatabaseInterface(db_path)
        self._ensure_emotional_state_table()
    
    def _ensure_emotional_state_table(self):
        """Create agent_emotional_state table if it doesn't exist."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_emotional_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                game_id TEXT,
                level_number INTEGER,
                emotion_type TEXT NOT NULL,
                base_value REAL NOT NULL,
                modified_value REAL NOT NULL,
                role_multiplier REAL,
                timestamp TEXT NOT NULL
            )
        """)
    
    def get_profile_for_role(self, role: str) -> Dict:
        """Get somatic profile for a given role."""
        return SOMATIC_PROFILES.get(role, SOMATIC_PROFILES['Generalist'])
    
    def apply_emotional_modifiers(self, role: str, emotion_type: str, base_value: float) -> float:
        """
        Apply role-specific emotional modifiers.
        
        Args:
            role: Agent role (Pioneer, Exploiter, Optimizer, Generalist)
            emotion_type: Type of emotion (curiosity, fear, skepticism, etc.)
            base_value: Base emotional value (0.0 - 1.0)
        
        Returns:
            Modified emotional value
        """
        profile = self.get_profile_for_role(role)
        
        # Apply multipliers
        if emotion_type in profile['multipliers']:
            modified = base_value * profile['multipliers'][emotion_type]
        # Apply dampeners
        elif emotion_type in profile['dampeners']:
            modified = base_value * profile['dampeners'][emotion_type]
        else:
            modified = base_value  # No modification
        
        # Clamp to reasonable range (0.0 - 5.0)
        return max(0.0, min(5.0, modified))
    
    def calculate_confidence_boost(self, role: str, is_frontier: bool = False) -> float:
        """Calculate confidence boost for current situation."""
        profile = self.get_profile_for_role(role)
        
        if role == 'Pioneer' and is_frontier:
            return profile['overrides'].get('confidence_boost_on_frontier', 1.0)
        
        return 1.0  # No boost
    
    def log_emotional_state(self, agent_id: str, game_id: str, level_number: int,
                           role: str, emotion_type: str, base_value: float):
        """Log agent's emotional state to database."""
        modified_value = self.apply_emotional_modifiers(role, emotion_type, base_value)
        profile = self.get_profile_for_role(role)
        
        # Get multiplier used
        multiplier = profile['multipliers'].get(emotion_type) or \
                    profile['dampeners'].get(emotion_type) or 1.0
        
        from datetime import datetime
        self.db.execute_query("""
            INSERT INTO agent_emotional_state
            (agent_id, game_id, level_number, emotion_type, base_value, 
             modified_value, role_multiplier, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, game_id, level_number, emotion_type, base_value,
              modified_value, multiplier, datetime.now().isoformat()))

if __name__ == "__main__":
    # Test somatic profiles
    sps = SomaticProfileSystem()
    
    print("=" * 70)
    print("SOMATIC PROFILE SYSTEM TEST")
    print("=" * 70)
    
    roles = ['Pioneer', 'Exploiter', 'Optimizer', 'Generalist']
    emotions = ['curiosity', 'fear_of_failure', 'skepticism', 'latency_aversion']
    
    print("\nEmotional Modifiers (base value = 1.0):\n")
    for role in roles:
        print(f"{role}:")
        profile = sps.get_profile_for_role(role)
        print(f"  Profile: {profile['name']}")
        
        for emotion in emotions:
            modified = sps.apply_emotional_modifiers(role, emotion, 1.0)
            if modified != 1.0:
                print(f"    {emotion}: {modified:.1f}x")
        print()
    
    print("[OK] Somatic profiles loaded successfully")
