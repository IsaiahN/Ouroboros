import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Pariah Validator - Automatic False Pariah Detection and Cleanup

A false pariah is as dangerous as a prestige vampire - it blocks network progress
by penalizing actions that are actually ESSENTIAL for winning.

This module runs after each evolution to:
1. Detect false pariahs (actions in winning sequences marked as pariah)
2. Decay stale pariahs (not triggered/validated recently)
3. Track false positive evidence (agents succeed despite pariah warning)
4. Automatically deactivate confirmed false pariahs

Integration: Called from autonomous_evolution_runner after each generation.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from database_interface import DatabaseInterface


class PariahValidator:
    """
    Validates pariahs and removes false positives from the network.
    
    False Pariah Criteria:
    1. Action appears in >50% of winning sequences for same game type
    2. Pariah not triggered in last N generations (stale)
    3. High false positive rate (agents succeed using pariah action)
    4. Pariah from beaten level blocking frontier exploration
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # Configuration
        self.WIN_SEQUENCE_THRESHOLD = 0.3  # If action in >30% of wins, suspicious
        self.WIN_SEQUENCE_CONFIRM = 0.5    # If action in >50% of wins, definitely false
        self.STALE_GENERATIONS = 10        # Pariah not triggered in 10 gens = stale
        self.FALSE_POSITIVE_THRESHOLD = 5  # 5 false positives = deactivate
        self.DECAY_RATE = 0.1              # Reduce toxicity by 10% each validation
        
    def validate_all_pariahs(self, current_generation: int) -> Dict:
        """
        Main entry point - validate all active pariahs.
        
        Returns:
            Dict with validation results and actions taken
        """
        results = {
            'generation': current_generation,
            'timestamp': datetime.now().isoformat(),
            'pariahs_checked': 0,
            'false_positives_detected': 0,
            'stale_pariahs_decayed': 0,
            'pariahs_deactivated': 0,
            'awareness_cleaned': 0,
            'details': []
        }
        
        # Get all active pariahs
        active_pariahs = self.db.execute_query("""
            SELECT pariah_id, pariah_name, action_sequence, source_game_id,
                   source_level_number, toxicity, trigger_count,
                   last_triggered_generation, discovery_generation,
                   false_positive_count
            FROM pariahs
            WHERE is_active = 1
        """)
        
        if not active_pariahs:
            print("[PARIAH-VAL] No active pariahs to validate")
            return results
            
        results['pariahs_checked'] = len(active_pariahs)
        print(f"[PARIAH-VAL] Validating {len(active_pariahs)} active pariahs...")
        
        # Build winning sequence cache per game type
        win_cache = self._build_winning_sequence_cache()
        
        for pariah in active_pariahs:
            pariah_result = self._validate_single_pariah(
                pariah, current_generation, win_cache
            )
            
            if pariah_result['action'] != 'none':
                results['details'].append(pariah_result)
                
            if pariah_result['is_false_positive']:
                results['false_positives_detected'] += 1
            if pariah_result['action'] == 'decayed':
                results['stale_pariahs_decayed'] += 1
            if pariah_result['action'] == 'deactivated':
                results['pariahs_deactivated'] += 1
        
        # Clean up stale awareness records
        awareness_cleaned = self._cleanup_stale_awareness()
        results['awareness_cleaned'] = awareness_cleaned
        
        # Log summary
        print(f"[PARIAH-VAL] Results: "
              f"{results['false_positives_detected']} false positives, "
              f"{results['stale_pariahs_decayed']} decayed, "
              f"{results['pariahs_deactivated']} deactivated, "
              f"{results['awareness_cleaned']} awareness cleaned")
        
        return results
    
    def _build_winning_sequence_cache(self) -> Dict[str, Dict[int, int]]:
        """
        Build cache of action frequencies in winning sequences per game type.
        
        Returns:
            Dict[game_type -> Dict[action_code -> count_in_wins]]
        """
        cache = {}
        
        # Get all winning sequences grouped by game type
        sequences = self.db.execute_query("""
            SELECT game_id, action_sequence
            FROM winning_sequences
            WHERE is_active = 1
        """)
        
        for seq in sequences:
            game_type = seq['game_id'][:4]  # e.g., 'vc33', 'sp80'
            
            if game_type not in cache:
                cache[game_type] = {'_total': 0, '_sequences': []}
            
            cache[game_type]['_total'] += 1
            
            try:
                actions = json.loads(seq['action_sequence'])
                unique_actions = set(actions)
                
                for action in unique_actions:
                    cache[game_type][action] = cache[game_type].get(action, 0) + 1
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
        return cache
    
    def _validate_single_pariah(
        self, 
        pariah: Dict, 
        current_generation: int,
        win_cache: Dict
    ) -> Dict:
        """
        Validate a single pariah and take appropriate action.
        """
        result = {
            'pariah_id': pariah['pariah_id'],
            'pariah_name': pariah['pariah_name'],
            'game_type': pariah['source_game_id'][:4] if pariah['source_game_id'] else 'unknown',
            'is_false_positive': False,
            'reason': None,
            'action': 'none'
        }
        
        game_type = result['game_type']
        
        # Parse action sequence
        try:
            actions = json.loads(pariah['action_sequence'])
            unique_actions = set(actions)
        except (json.JSONDecodeError, TypeError):
            return result
        
        # CHECK 1: Actions in winning sequences (strongest signal)
        if game_type in win_cache:
            total_wins = win_cache[game_type].get('_total', 0)
            
            if total_wins > 0:
                for action in unique_actions:
                    action_in_wins = win_cache[game_type].get(action, 0)
                    win_ratio = action_in_wins / total_wins
                    
                    if win_ratio >= self.WIN_SEQUENCE_CONFIRM:
                        # Definite false positive - action is in most winning sequences
                        result['is_false_positive'] = True
                        result['reason'] = (
                            f"ACTION{action} appears in {win_ratio*100:.0f}% of "
                            f"{game_type} winning sequences - clearly essential"
                        )
                        self._deactivate_pariah(
                            pariah['pariah_id'], 
                            f"False positive: ACTION{action} in {win_ratio*100:.0f}% of wins"
                        )
                        result['action'] = 'deactivated'
                        return result
                        
                    elif win_ratio >= self.WIN_SEQUENCE_THRESHOLD:
                        # Suspicious - increment false positive count
                        result['is_false_positive'] = True
                        result['reason'] = (
                            f"ACTION{action} appears in {win_ratio*100:.0f}% of "
                            f"{game_type} wins - suspicious"
                        )
                        self._increment_false_positive(pariah['pariah_id'])
                        
                        # Check if we've accumulated enough false positives
                        current_fp = (pariah.get('false_positive_count') or 0) + 1
                        if current_fp >= self.FALSE_POSITIVE_THRESHOLD:
                            self._deactivate_pariah(
                                pariah['pariah_id'],
                                f"Accumulated {current_fp} false positive signals"
                            )
                            result['action'] = 'deactivated'
                        else:
                            result['action'] = 'flagged'
                        return result
        
        # CHECK 2: Stale pariah (not triggered recently)
        last_triggered = pariah.get('last_triggered_generation') or 0
        generations_since = current_generation - last_triggered
        
        if generations_since > self.STALE_GENERATIONS:
            # Pariah hasn't been relevant - decay its toxicity
            new_toxicity = max(0.01, pariah['toxicity'] * (1 - self.DECAY_RATE))
            
            self.db.execute_query("""
                UPDATE pariahs
                SET toxicity = ?,
                    obsolescence_score = obsolescence_score + 0.1
                WHERE pariah_id = ?
            """, (new_toxicity, pariah['pariah_id']))
            
            result['reason'] = f"Stale for {generations_since} generations, decayed toxicity"
            result['action'] = 'decayed'
            
            # If toxicity drops too low, deactivate
            if new_toxicity <= 0.02:
                self._deactivate_pariah(
                    pariah['pariah_id'],
                    f"Toxicity decayed to {new_toxicity:.3f} after {generations_since} stale generations"
                )
                result['action'] = 'deactivated'
            
            return result
        
        # CHECK 3: High false positive count already accumulated
        fp_count = pariah.get('false_positive_count') or 0
        if fp_count >= self.FALSE_POSITIVE_THRESHOLD:
            self._deactivate_pariah(
                pariah['pariah_id'],
                f"High false positive count: {fp_count}"
            )
            result['is_false_positive'] = True
            result['reason'] = f"Already has {fp_count} false positive flags"
            result['action'] = 'deactivated'
            return result
        
        return result
    
    def _deactivate_pariah(self, pariah_id: str, reason: str):
        """Deactivate a pariah and all awareness of it."""
        # Update failure_description to include deactivation reason
        self.db.execute_query("""
            UPDATE pariahs
            SET is_active = 0,
                failure_description = failure_description || ' [DEACTIVATED: ' || ? || ']'
            WHERE pariah_id = ?
        """, (reason, pariah_id))
        
        # Also deactivate all awareness
        self.db.execute_query("""
            UPDATE agent_pariah_awareness
            SET is_active = 0
            WHERE pariah_id = ?
        """, (pariah_id,))
        
        print(f"[PARIAH-VAL] Deactivated {pariah_id[:12]}: {reason}")
    
    def _increment_false_positive(self, pariah_id: str):
        """Increment false positive count for a pariah."""
        self.db.execute_query("""
            UPDATE pariahs
            SET false_positive_count = COALESCE(false_positive_count, 0) + 1
            WHERE pariah_id = ?
        """, (pariah_id,))
    
    def _cleanup_stale_awareness(self) -> int:
        """
        Clean up awareness records pointing to inactive pariahs.
        This prevents the bug where awareness.is_active=1 but pariah.is_active=0.
        """
        # Count before
        count_result = self.db.execute_query("""
            SELECT COUNT(*) as cnt
            FROM agent_pariah_awareness pa
            JOIN pariahs p ON pa.pariah_id = p.pariah_id
            WHERE pa.is_active = 1 AND p.is_active = 0
        """)
        
        stale_count = count_result[0]['cnt'] if count_result else 0
        
        if stale_count > 0:
            self.db.execute_query("""
                UPDATE agent_pariah_awareness
                SET is_active = 0
                WHERE pariah_id IN (
                    SELECT pariah_id FROM pariahs WHERE is_active = 0
                )
            """)
            print(f"[PARIAH-VAL] Cleaned {stale_count} stale awareness records")
        
        return stale_count
    
    def record_pariah_success(self, agent_id: str, game_id: str, 
                               actions_used: List[int], score_gained: float):
        """
        Record when an agent succeeds using actions that have pariah warnings.
        This provides evidence of false positives.
        
        Call this from core_gameplay when agent gains score.
        """
        if score_gained <= 0:
            return
        
        game_type = game_id[:4]
        
        # Find pariahs that warned against these actions
        for action in set(actions_used):
            warned_pariahs = self.db.execute_query("""
                SELECT p.pariah_id
                FROM pariahs p
                JOIN agent_pariah_awareness pa ON p.pariah_id = pa.pariah_id
                WHERE pa.agent_id = ?
                AND pa.is_active = 1
                AND p.is_active = 1
                AND p.source_game_id LIKE ?
                AND p.action_sequence LIKE ?
            """, (agent_id, f"{game_type}%", f"%{action}%"))
            
            for pariah in warned_pariahs:
                # Agent succeeded despite warning - increment false positive
                self._increment_false_positive(pariah['pariah_id'])
                
                # Also record the interaction
                self.db.execute_query("""
                    INSERT OR IGNORE INTO pariah_package_interactions
                    (pariah_id, package_id, interaction_type, outcome, 
                     score_impact, interaction_count)
                    VALUES (?, 'success_despite_warning', 'false_positive_evidence',
                            'agent_succeeded', ?, 1)
                    ON CONFLICT(pariah_id, package_id) DO UPDATE SET
                    interaction_count = interaction_count + 1,
                    score_impact = score_impact + ?
                """, (pariah['pariah_id'], score_gained, score_gained))


def run_pariah_validation(db: DatabaseInterface, current_generation: int) -> Dict:
    """
    Convenience function to run pariah validation.
    Call this from autonomous_evolution_runner after each generation.
    """
    validator = PariahValidator(db)
    return validator.validate_all_pariahs(current_generation)


if __name__ == "__main__":
    # Manual run for testing
    from database_interface import DatabaseInterface
    
    db = DatabaseInterface()
    
    # Get current generation
    gen_result = db.execute_query(
        "SELECT MAX(generation) as gen FROM agents WHERE is_active = 1"
    )
    current_gen = gen_result[0]['gen'] if gen_result and gen_result[0]['gen'] else 0
    
    print(f"Running pariah validation for generation {current_gen}...")
    results = run_pariah_validation(db, current_gen)
    
    print(f"\n=== Validation Complete ===")
    print(f"Pariahs checked: {results['pariahs_checked']}")
    print(f"False positives: {results['false_positives_detected']}")
    print(f"Stale decayed: {results['stale_pariahs_decayed']}")
    print(f"Deactivated: {results['pariahs_deactivated']}")
    print(f"Awareness cleaned: {results['awareness_cleaned']}")
    
    if results['details']:
        print(f"\nDetails:")
        for detail in results['details'][:10]:  # Show first 10
            print(f"  {detail['pariah_id'][:12]}: {detail['action']} - {detail['reason']}")
