#!/usr/bin/env python3
"""
Agent Self-Model System
=======================

Implements "I am this object" tracking for agents.
Identifies which objects/pixels agents control in each game/level.

This addresses the agent self-model requirement from operational philosophy.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class AgentSelfModel:
    """
    Tracks which objects agents control in games.
    
    Builds a "self-model" for each agent by analyzing:
    - Which pixels/objects respond to agent actions
    - Correlation between actions and frame changes
    - Controlled vs environmental objects
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize self-model system."""
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create agent_object_control table if needed."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_object_control (
                agent_id TEXT,
                game_id TEXT,
                level_number INTEGER,
                controlled_objects TEXT,
                confidence REAL,
                learned_at TEXT,
                PRIMARY KEY (agent_id, game_id, level_number)
            )
        """)
    
    def identify_controlled_objects(
        self, 
        game_id: str, 
        level: int, 
        action_sequence: List[Dict],
        frame_sequence: List[Dict]
    ) -> Tuple[List[str], float]:
        """
        Identify which objects respond to actions.
        
        Args:
            game_id: Game identifier
            level: Level number
            action_sequence: List of actions taken
            frame_sequence: List of frames (before/after each action)
        
        Returns:
            (controlled_objects, confidence)
        """
        if not action_sequence or not frame_sequence:
            return ([], 0.0)
        
        # Track which coordinates change in response to actions
        responsive_coords = {}
        
        for i, action in enumerate(action_sequence):
            if i >= len(frame_sequence) - 1:
                break
            
            frame_before = frame_sequence[i]
            frame_after = frame_sequence[i + 1]
            
            # Find changed coordinates
            changed = self._find_changed_coordinates(frame_before, frame_after)
            
            # Track action -> coordinate correlation
            action_type = action.get('action_type', 'unknown')
            for coord in changed:
                if coord not in responsive_coords:
                    responsive_coords[coord] = {}
                if action_type not in responsive_coords[coord]:
                    responsive_coords[coord][action_type] = 0
                responsive_coords[coord][action_type] += 1
        
        # Identify consistently responsive objects (high correlation)
        controlled = []
        for coord, action_counts in responsive_coords.items():
            # If coordinate responds to multiple action types, likely controlled
            if len(action_counts) >= 2:
                controlled.append(coord)
        
        # Calculate confidence based on consistency
        confidence = min(1.0, len(controlled) / max(1, len(responsive_coords)))
        
        return (controlled, confidence)
    
    def _find_changed_coordinates(
        self, 
        frame_before: Dict, 
        frame_after: Dict
    ) -> List[str]:
        """
        Find coordinates that changed between frames.
        
        Args:
            frame_before: Frame state before action
            frame_after: Frame state after action
        
        Returns:
            List of changed coordinate strings (e.g., "x:5,y:10")
        """
        changed = []
        
        # Simple pixel-level comparison
        # In real implementation, would compare grid states
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return changed
        
        for y in range(min(len(grid_before), len(grid_after))):
            for x in range(min(len(grid_before[y]), len(grid_after[y]))):
                if grid_before[y][x] != grid_after[y][x]:
                    changed.append(f"x:{x},y:{y}")
        
        return changed
    
    def store_control_map(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        confidence: float
    ):
        """
        Store agent's control map in database.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
            controlled_objects: List of controlled object coordinates
            confidence: Confidence score (0.0-1.0)
        """
        from datetime import datetime
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_object_control
            (agent_id, game_id, level_number, controlled_objects, confidence, learned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            game_id,
            level,
            json.dumps(controlled_objects),
            confidence,
            datetime.now().isoformat()
        ))
        
        logger.info(
            f"Stored control map for {agent_id} on {game_id} L{level}: "
            f"{len(controlled_objects)} objects (confidence: {confidence:.2f})"
        )
    
    def get_controlled_objects(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> Optional[List[str]]:
        """
        Retrieve agent's known controlled objects.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
        
        Returns:
            List of controlled object coordinates, or None if not learned
        """
        result = self.db.execute_query("""
            SELECT controlled_objects, confidence
            FROM agent_object_control
            WHERE agent_id = ? AND game_id = ? AND level_number = ?
        """, (agent_id, game_id, level))
        
        if result and result[0]['controlled_objects']:
            return json.loads(result[0]['controlled_objects'])
        
        return None
    
    def build_control_map(
        self,
        agent_id: str,
        game_id: str,
        gameplay_data: Dict
    ) -> Dict[int, List[str]]:
        """
        Build complete control map for all levels in a game.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            gameplay_data: Complete gameplay data with actions and frames
        
        Returns:
            Dictionary mapping level -> controlled objects
        """
        control_map = {}
        
        for level_data in gameplay_data.get('levels', []):
            level = level_data.get('level_number')
            actions = level_data.get('actions', [])
            frames = level_data.get('frames', [])
            
            if level is None or not actions or not frames:
                continue
            
            controlled, confidence = self.identify_controlled_objects(
                game_id, level, actions, frames
            )
            
            if controlled and confidence > 0.5:
                control_map[level] = controlled
                self.store_control_map(agent_id, game_id, level, controlled, confidence)
        
        return control_map


# ============================================================================
# TWO-STREAMS CONSCIOUSNESS: WEAVING REPORTER
# ============================================================================

class WeavingReporter:
    """
    Generates self-reflection "weaving reports" for every action.
    
    Philosophy: Every action sent to ARC API includes full self_reflection weaving data.
    This is the agent's introspection visible in every API call.
    
    Local Database Storage: Uses sampling to prevent bloat:
    - Sampling Rate: Store 1 in 10 decisions locally (10%)
    - Exception: Always store if conflict_detected = True
    - Exception: Always store level completion / game end decisions
    """
    
    # Sampling rate for local storage (10% of non-exceptional decisions)
    SAMPLING_RATE = 0.1
    
    def __init__(self, db: DatabaseInterface):
        """Initialize weaving reporter."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure decision_weaving_reports table exists."""
        # Table should be created in Phase 1, but ensure it exists
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS decision_weaving_reports (
                report_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER,
                action_number INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                emotional_input REAL,
                semantic_input REAL,
                identity_input REAL,
                private_memory_strength REAL,
                network_recommendation_strength REAL,
                self_network_bias REAL,
                final_decision_weight REAL,
                chosen_action TEXT,
                alternative_action TEXT,
                conflict_detected BOOLEAN DEFAULT FALSE,
                outcome_correct BOOLEAN,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_weaving_agent_game 
            ON decision_weaving_reports(agent_id, game_id)
        """)
    
    def generate_report(
        self,
        agent_id: str,
        game_id: str,
        level_number: int,
        action_number: int,
        chosen_action: str,
        private_memory_strength: float,
        network_recommendation_strength: float,
        self_network_bias: float,
        navigation_state: float,
        role_confidence: float,
        role_fit_score: float,
        sensation_profile: Dict,
        alternative_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weaving report for an action decision.
        
        This is called for EVERY action to produce API-ready self-reflection.
        
        Args:
            agent_id: Agent making the decision
            game_id: Current game
            level_number: Current level
            action_number: Action counter in this game
            chosen_action: The action being taken
            private_memory_strength: How strong agent's own memory signal is (0-1)
            network_recommendation_strength: How strong network's recommendation is (0-1)
            self_network_bias: Agent's bias toward self (0=network, 1=self)
            navigation_state: Agent's emotional state (-1 to 1)
            role_confidence: Agent's confidence in their role (0-1)
            role_fit_score: How well agent fits their role (0-1)
            sensation_profile: Agent's sensation mappings
            alternative_action: What network recommended (if different)
            
        Returns:
            Complete weaving report dictionary for API
        """
        import uuid
        from datetime import datetime
        
        # Calculate internal network inputs
        # Emotional: Map navigation_state from [-1,1] to [0,1]
        emotional_input = (navigation_state + 1.0) / 2.0
        
        # Semantic: Average of top sensation scores (if any)
        object_sensations = sensation_profile.get('object_sensations', {})
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = sum(top_sensations) / len(top_sensations) if top_sensations else 0.5
            # Normalize to 0-1 range (sensations are -1 to 1)
            semantic_input = (semantic_input + 1.0) / 2.0
        else:
            semantic_input = 0.5  # Neutral if no sensations
        
        # Identity: Average of role_confidence and role_fit_score
        identity_input = (role_confidence + role_fit_score) / 2.0
        
        # Calculate final decision weight using Two-Streams formula
        # final_weight = private * bias + network * (1 - bias)
        alpha = self_network_bias
        final_decision_weight = (
            private_memory_strength * alpha + 
            network_recommendation_strength * (1.0 - alpha)
        )
        
        # Detect conflict (significant difference between private and network)
        conflict_detected = abs(private_memory_strength - network_recommendation_strength) > 0.3
        
        # Build human-readable summary
        emotion_label = self._get_emotion_label(navigation_state)
        
        report = {
            'report_id': f"weave_{uuid.uuid4().hex[:12]}",
            'agent_id': agent_id,
            'game_id': game_id,
            'level_number': level_number,
            'action_number': action_number,
            'timestamp': datetime.now().isoformat(),
            
            # Internal networks (Three Streams)
            'emotional_input': round(emotional_input, 3),
            'semantic_input': round(semantic_input, 3),
            'identity_input': round(identity_input, 3),
            
            # Two-Streams weighting
            'private_memory_strength': round(private_memory_strength, 3),
            'network_recommendation_strength': round(network_recommendation_strength, 3),
            'self_network_bias': round(self_network_bias, 3),
            'final_decision_weight': round(final_decision_weight, 3),
            
            # Decision
            'chosen_action': chosen_action,
            'alternative_action': alternative_action,
            'conflict_detected': conflict_detected,
            
            # Narrative summary
            'narrative': self._build_narrative(
                emotion_label, private_memory_strength, network_recommendation_strength,
                alpha, chosen_action, alternative_action, conflict_detected
            ),
            
            # Outcome (to be filled in later)
            'outcome_correct': None
        }
        
        return report
    
    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get human-readable emotion label from navigation state."""
        if navigation_state < -0.5:
            return 'frustrated'
        elif navigation_state < -0.1:
            return 'cautious'
        elif navigation_state < 0.1:
            return 'neutral'
        elif navigation_state < 0.5:
            return 'curious'
        else:
            return 'confident'
    
    def _build_narrative(
        self,
        emotion: str,
        private_strength: float,
        network_strength: float,
        alpha: float,
        chosen_action: str,
        alternative: Optional[str],
        conflict: bool
    ) -> str:
        """Build human-readable narrative of decision."""
        parts = []
        
        # Emotional state
        parts.append(f"Feeling {emotion}")
        
        # Stream preference
        if alpha > 0.6:
            parts.append("trusting own experience")
        elif alpha < 0.4:
            parts.append("following network wisdom")
        else:
            parts.append("balancing self and network")
        
        # Conflict
        if conflict:
            if alternative:
                parts.append(f"(conflicted: network suggested {alternative})")
            else:
                parts.append("(internal conflict detected)")
        
        # Decision
        parts.append(f"-> {chosen_action}")
        
        return " | ".join(parts)
    
    def format_for_api(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format weaving report for inclusion in API reasoning payload.
        
        Returns a compact version suitable for the 16KB limit.
        """
        return {
            'emotional_network': report['emotional_input'],
            'semantic_network': report['semantic_input'],
            'identity_network': report['identity_input'],
            'private_memory': report['private_memory_strength'],
            'network_wisdom': report['network_recommendation_strength'],
            'self_trust_bias': report['self_network_bias'],
            'decision_weight': report['final_decision_weight'],
            'conflict': report['conflict_detected'],
            'narrative': report['narrative']
        }
    
    def should_store_locally(self, report: Dict[str, Any], is_terminal: bool = False) -> bool:
        """
        Determine if this report should be stored in local database.
        
        Storage criteria (to prevent bloat):
        - Always store if conflict_detected = True
        - Always store if is_terminal (level/game end)
        - Otherwise, sample at 10% rate
        """
        import random
        
        # Always store conflicts
        if report.get('conflict_detected'):
            return True
        
        # Always store terminal decisions
        if is_terminal:
            return True
        
        # Otherwise, sample
        return random.random() < self.SAMPLING_RATE
    
    def store_report(self, report: Dict[str, Any]) -> None:
        """Store a weaving report in the database."""
        self.db.execute_query("""
            INSERT INTO decision_weaving_reports
            (report_id, agent_id, game_id, level_number, action_number, timestamp,
             emotional_input, semantic_input, identity_input,
             private_memory_strength, network_recommendation_strength,
             self_network_bias, final_decision_weight,
             chosen_action, alternative_action, conflict_detected, outcome_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report['report_id'], report['agent_id'], report['game_id'],
            report['level_number'], report['action_number'], report['timestamp'],
            report['emotional_input'], report['semantic_input'], report['identity_input'],
            report['private_memory_strength'], report['network_recommendation_strength'],
            report['self_network_bias'], report['final_decision_weight'],
            report['chosen_action'], report['alternative_action'],
            report['conflict_detected'], report.get('outcome_correct')
        ))
    
    def update_outcome(self, report_id: str, outcome_correct: bool) -> None:
        """Update the outcome for a stored report (for meta-learning)."""
        self.db.execute_query("""
            UPDATE decision_weaving_reports
            SET outcome_correct = ?
            WHERE report_id = ?
        """, (outcome_correct, report_id))


if __name__ == "__main__":
    # Test self-model system
    print("=" * 70)
    print("AGENT SELF-MODEL SYSTEM TEST")
    print("=" * 70)
    
    asm = AgentSelfModel()
    
    # Test table creation
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='agent_object_control'
    """)
    
    if result:
        print("[OK] agent_object_control table exists")
    else:
        print("[FAIL] Table creation failed")
    
    # Test basic functionality
    test_controlled = ["x:5,y:10", "x:6,y:10"]
    asm.store_control_map("test_agent", "test_game", 1, test_controlled, 0.85)
    
    retrieved = asm.get_controlled_objects("test_agent", "test_game", 1)
    if retrieved == test_controlled:
        print("[OK] Store and retrieve working")
    else:
        print(f"[FAIL] Mismatch: {retrieved} != {test_controlled}")
    
    print("\n[OK] Agent Self-Model system operational")
