#!/usr/bin/env python3
"""
Sequence Repair System
======================

Attempts to rescue "suspicious" sequences (0% validation success) by:
1. Identifying sequences that fail validation.
2. Hypothesizing they are missing the final 'Submit' action (ACTION6).
3. Stitching the missing action and replaying.
4. If successful, updating the sequence in the database.

This addresses the "Optimizer Penultimate Checkpoint Bug" where the optimizer
might find a solution but fail to record the final submission step.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SequenceRepairSystem:
    def __init__(self, db_path: str = "core_data.db"):
        self.db = DatabaseInterface(db_path)
        
    async def repair_sequences(self, limit: int = 50):
        """Attempt to repair failing sequences."""
        logger.info(f"Starting sequence repair cycle (limit={limit})...")
        
        # 1. Find candidates: 0% success rate or never validated but high usage
        candidates = self._find_repair_candidates(limit)
        logger.info(f"Found {len(candidates)} candidates for repair")
        
        repaired_count = 0
        
        for seq in candidates:
            success = await self._attempt_repair(seq)
            if success:
                repaired_count += 1
                
        logger.info(f"Repair cycle complete. Successfully repaired {repaired_count}/{len(candidates)} sequences.")
        return repaired_count

    def _find_repair_candidates(self, limit: int) -> List[Dict]:
        """Find sequences that are failing validation."""
        query = """
            SELECT ws.sequence_id, ws.game_id, ws.action_sequence, ws.total_actions,
                   ws.level_number, ws.initial_frame, ws.coordinate_sequence, ws.total_score
            FROM winning_sequences ws
            JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
            WHERE ws.is_active = 1
            AND sr.successful_validations = 0
            AND sr.total_validation_attempts > 0
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))

    async def _attempt_repair(self, seq: Dict) -> bool:
        """Try to repair a single sequence."""
        sequence_id = seq['sequence_id']
        game_id = seq['game_id']
        original_actions = self._parse_actions(seq['action_sequence'])
        
        if not original_actions:
            logger.warning(f"Could not parse actions for {sequence_id}")
            return False
            
        # Check if already ends with ACTION6 (Submit)
        last_action = original_actions[-1] if original_actions else None
        last_action_type = last_action.get('action_type') if isinstance(last_action, dict) else last_action
        
        if last_action_type == 'ACTION6' or last_action_type == 6:
            logger.info(f"Sequence {sequence_id} already ends with ACTION6. Skipping simple stitch.")
            return False
            
        # HYPOTHESIS: Missing final ACTION6
        logger.info(f"Attempting repair on {sequence_id} (Game {game_id}): Appending ACTION6")
        
        repaired_actions = original_actions.copy()
        # Append ACTION6 in the same format as existing actions
        # Check format of existing actions to match
        if original_actions and isinstance(original_actions[0], dict):
            # Dict format
            repaired_actions.append({
                'action_type': 'ACTION6',
                'params': {},
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Integer format (most common)
            repaired_actions.append(6)
        
        # Create a temporary sequence object for replay
        # Must include all fields expected by _try_replay_sequence
        temp_sequence = seq.copy()
        temp_sequence['action_sequence'] = json.dumps(repaired_actions)
        temp_sequence['total_actions'] = len(repaired_actions)
        # Ensure required fields exist (use defaults if missing)
        if 'level_number' not in temp_sequence:
            temp_sequence['level_number'] = 1
        if 'initial_frame' not in temp_sequence:
            temp_sequence['initial_frame'] = '[]'
        if 'coordinate_sequence' not in temp_sequence:
            temp_sequence['coordinate_sequence'] = '[]'
        
        
        # Replay using GameplayEngine
        engine = GameplayEngine(api_key=None, db_path=self.db.db_path)
        
        try:
            # _try_replay_sequence expects a full sequence dict, not just action_sequence string
            result = await engine._try_replay_sequence(game_id, temp_sequence)
            
            if result and result.get('win'):
                logger.info(f"✅ REPAIR SUCCESS: Sequence {sequence_id} fixed by appending ACTION6!")
                self._save_repaired_sequence(sequence_id, repaired_actions)
                return True
            else:
                logger.info(f"❌ Repair failed for {sequence_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error replaying repair candidate {sequence_id}: {e}")
            return False

    def _save_repaired_sequence(self, sequence_id: str, new_actions: List[Dict]):
        """Update the sequence in the database with the repaired version."""
        # 1. Update winning_sequences
        self.db.execute_query("""
            UPDATE winning_sequences
            SET action_sequence = ?,
                total_actions = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE sequence_id = ?
        """, (json.dumps(new_actions), len(new_actions), sequence_id))
        
        # 2. Reset reputation so it can be validated fresh
        self.db.execute_query("""
            UPDATE sequence_reputation
            SET successful_validations = 1, -- Count this repair as a success
                total_validation_attempts = 1,
                last_validation_date = CURRENT_TIMESTAMP
            WHERE sequence_id = ?
        """, (sequence_id,))
        
        logger.info(f"Saved repaired sequence {sequence_id} to database")

    def _parse_actions(self, action_data: Any) -> List[Dict]:
        """Robustly parse action sequence data."""
        try:
            if isinstance(action_data, str):
                return json.loads(action_data)
            elif isinstance(action_data, list):
                return action_data
            return []
        except Exception:
            return []

if __name__ == "__main__":
    repair_system = SequenceRepairSystem()
    asyncio.run(repair_system.repair_sequences())
