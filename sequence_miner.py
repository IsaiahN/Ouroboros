"""
Sequence Miner - Retroactive Learning from Winning Sequences

This module extracts learning data from stored winning sequences to backfill
knowledge tables that may be empty or incomplete. Since action_traces get 
cleaned up to save disk space, sequences are the permanent record of successful
gameplay that can teach the network.

What can be mined from sequences:
1. Level Breakpoints - Infer where each level starts based on total_score
2. Interaction Triggers - Correlate actions with frame changes
3. CODS Level Outcomes - All sequence levels are wins
4. Action Effectiveness - Track which actions appear in winning sequences

Author: Ouroboros System
Created: 2025-12-28
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MiningResult:
    """Results from mining a single sequence"""
    sequence_id: str
    level_breakpoints_computed: bool
    interaction_triggers_extracted: int
    level_outcomes_recorded: int
    action_effectiveness_updated: int
    errors: List[str]


class SequenceMiner:
    """
    Mines winning sequences for retroactive learning data.
    
    Sequences contain:
    - action_sequence: List of actions taken
    - coordinate_sequence: Coordinates for ACTION6
    - frame_transitions: Frame state after each action
    - total_score: Number of levels completed (= final level number)
    - initial_frame, final_frame: Start/end states
    
    This data can be used to:
    1. Compute level_breakpoints (where each level starts)
    2. Extract interaction_triggers (action -> effect correlations)
    3. Record cods_level_outcomes (all as passed=True)
    4. Update action_effectiveness (boost winning actions)
    """
    
    def __init__(self, db_path: str = 'core_data.db'):
        self.db_path = db_path
        self.conn = None
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # =========================================================================
    # LEVEL BREAKPOINTS COMPUTATION
    # =========================================================================
    
    def compute_level_breakpoints(self, sequence_id: str) -> Optional[Dict[str, int]]:
        """
        Compute level breakpoints for a sequence by dividing actions across levels.
        
        Since we know:
        - total_score = number of levels completed
        - total_actions = length of action sequence
        
        We can estimate breakpoints by:
        1. Dividing actions evenly: actions_per_level = total_actions / total_score
        2. Detecting frame shape changes (new level = new grid size)
        3. Using coordinate jumps (large position changes suggest new level)
        
        Returns: {"1": 0, "2": 15, "3": 32} or None if cannot compute
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT action_sequence, frame_transitions, total_score, total_actions,
                   coordinate_sequence, game_id
            FROM winning_sequences 
            WHERE sequence_id = ?
        ''', (sequence_id,))
        
        row = c.fetchone()
        if not row:
            return None
        
        try:
            actions = json.loads(row['action_sequence']) if row['action_sequence'] else []
            transitions = json.loads(row['frame_transitions']) if row['frame_transitions'] else []
            total_score = int(row['total_score'] or 1)
            total_actions = row['total_actions'] or len(actions)
            
            if total_score < 1 or total_actions < 1:
                return None
            
            breakpoints = {'1': 0}  # Level 1 always starts at action 0
            
            # Method 1: Try to detect by frame shape changes
            if transitions and len(transitions) >= 2:
                current_level = 1
                for i in range(1, len(transitions)):
                    if current_level >= total_score:
                        break  # Already found all levels
                    
                    frame_before = transitions[i-1]
                    frame_after = transitions[i]
                    
                    # Check for significant shape change
                    if frame_before and frame_after:
                        shape_before = (len(frame_before), len(frame_before[0]) if frame_before else 0)
                        shape_after = (len(frame_after), len(frame_after[0]) if frame_after else 0)
                        
                        # Significant shape change AND going to larger frame often = new level
                        if shape_before != shape_after:
                            # Check if this looks like a level transition
                            # (full grid appearing after smaller selection)
                            if shape_after[0] > 20 or shape_before[0] < 10:
                                current_level += 1
                                breakpoints[str(current_level)] = i
                
                # If we found all levels via shape detection, use those
                if len(breakpoints) == total_score:
                    return breakpoints
            
            # Method 2: Fall back to even distribution
            if len(breakpoints) < total_score:
                actions_per_level = total_actions / total_score
                for level in range(2, total_score + 1):
                    if str(level) not in breakpoints:
                        breakpoints[str(level)] = int((level - 1) * actions_per_level)
            
            return breakpoints
            
        except Exception as e:
            logger.warning(f"[MINER] Failed to compute breakpoints for {sequence_id}: {e}")
            return None
    
    def backfill_level_breakpoints(self) -> Tuple[int, int]:
        """
        Backfill level_breakpoints for all sequences that don't have them.
        
        Returns: (updated_count, failed_count)
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        # Find sequences without breakpoints
        c.execute('''
            SELECT sequence_id FROM winning_sequences 
            WHERE is_active = 1 
            AND (level_breakpoints IS NULL OR level_breakpoints = '{}')
            AND total_score > 0
        ''')
        
        sequences = [row[0] for row in c.fetchall()]
        
        updated = 0
        failed = 0
        
        for seq_id in sequences:
            breakpoints = self.compute_level_breakpoints(seq_id)
            if breakpoints and len(breakpoints) > 1:
                try:
                    c.execute('''
                        UPDATE winning_sequences 
                        SET level_breakpoints = ?
                        WHERE sequence_id = ?
                    ''', (json.dumps(breakpoints), seq_id))
                    updated += 1
                except Exception as e:
                    logger.warning(f"[MINER] Failed to update breakpoints for {seq_id}: {e}")
                    failed += 1
            else:
                failed += 1
        
        conn.commit()
        
        if updated > 0:
            logger.info(f"[MINER] Backfilled level_breakpoints: {updated} updated, {failed} failed")
        
        return updated, failed
    
    # =========================================================================
    # INTERACTION TRIGGERS EXTRACTION
    # =========================================================================
    
    def extract_interaction_triggers(self, sequence_id: str) -> List[Dict]:
        """
        Extract interaction triggers from a sequence's action->frame correlations.
        
        For each action in the sequence:
        1. Compare frame[i] vs frame[i+1]
        2. Identify what changed (color changes, positions, etc.)
        3. Record as interaction trigger
        
        Returns: List of trigger dictionaries
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT action_sequence, frame_transitions, coordinate_sequence,
                   game_id, level_number
            FROM winning_sequences 
            WHERE sequence_id = ?
        ''', (sequence_id,))
        
        row = c.fetchone()
        if not row:
            return []
        
        try:
            actions = json.loads(row['action_sequence']) if row['action_sequence'] else []
            transitions = json.loads(row['frame_transitions']) if row['frame_transitions'] else []
            coords = json.loads(row['coordinate_sequence']) if row['coordinate_sequence'] else []
            game_id = row['game_id']
            level_number = row['level_number'] or 1
            
            # Extract game_type from game_id
            game_type = game_id.split('-')[0] if '-' in game_id else game_id[:4]
            
            triggers = []
            coord_idx = 0
            
            for i in range(len(actions)):
                if i >= len(transitions) - 1:
                    break  # Need frame before and after
                
                action = actions[i]
                frame_before = transitions[i]
                frame_after = transitions[i + 1] if i + 1 < len(transitions) else None
                
                if not frame_before or not frame_after:
                    continue
                
                # Get coordinates for ACTION6
                action_coord = None
                if action == 6 and coord_idx < len(coords):
                    action_coord = coords[coord_idx]
                    coord_idx += 1
                
                # Detect changes
                changes = self._detect_frame_changes(frame_before, frame_after)
                
                if changes:
                    trigger = {
                        'game_type': game_type,
                        'level_number': level_number,
                        'trigger_action': f'ACTION{action}',
                        'trigger_position_x': action_coord[0] if action_coord else None,
                        'trigger_position_y': action_coord[1] if action_coord else None,
                        'effect_type': changes['effect_type'],
                        'effect_details': json.dumps(changes['details']),
                        'effect_distance': changes.get('distance', 0),
                        'occurrence_count': 1,
                        'consistent_count': 1,
                        'confidence': 0.7  # From winning sequence = higher base confidence
                    }
                    triggers.append(trigger)
            
            return triggers
            
        except Exception as e:
            logger.warning(f"[MINER] Failed to extract triggers from {sequence_id}: {e}")
            return []
    
    def _detect_frame_changes(self, frame_before: List, frame_after: List) -> Optional[Dict]:
        """
        Detect what changed between two frames.
        
        Returns: {effect_type: str, details: dict, distance: float} or None
        """
        try:
            # Handle different frame sizes
            if len(frame_before) != len(frame_after):
                return {
                    'effect_type': 'frame_resize',
                    'details': {
                        'before_size': (len(frame_before), len(frame_before[0]) if frame_before else 0),
                        'after_size': (len(frame_after), len(frame_after[0]) if frame_after else 0)
                    },
                    'distance': 0
                }
            
            # Count changed pixels
            changed_pixels = []
            color_changes = {}
            
            for y, (row_before, row_after) in enumerate(zip(frame_before, frame_after)):
                if len(row_before) != len(row_after):
                    continue
                for x, (px_before, px_after) in enumerate(zip(row_before, row_after)):
                    if px_before != px_after:
                        changed_pixels.append((x, y, px_before, px_after))
                        key = (px_before, px_after)
                        color_changes[key] = color_changes.get(key, 0) + 1
            
            if not changed_pixels:
                return None  # No change
            
            # Determine effect type based on change pattern
            if len(color_changes) == 1:
                (from_color, to_color), count = list(color_changes.items())[0]
                effect_type = 'color_change'
                details = {
                    'from_color': from_color,
                    'to_color': to_color,
                    'pixel_count': count
                }
            else:
                effect_type = 'multi_change'
                details = {
                    'pixel_count': len(changed_pixels),
                    'color_changes': len(color_changes)
                }
            
            return {
                'effect_type': effect_type,
                'details': details,
                'distance': 0  # Would need action position to calculate
            }
            
        except Exception:
            return None
    
    def backfill_interaction_triggers(self, min_occurrences: int = 2) -> Tuple[int, int]:
        """
        Extract and store interaction triggers from all active sequences.
        
        Returns: (inserted_count, updated_count)
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        # Get all active sequences with frame_transitions
        c.execute('''
            SELECT sequence_id FROM winning_sequences 
            WHERE is_active = 1 AND frame_transitions IS NOT NULL
        ''')
        
        sequences = [row[0] for row in c.fetchall()]
        
        # Aggregate triggers across sequences
        trigger_map = {}  # key -> {trigger_data, count}
        
        for seq_id in sequences:
            triggers = self.extract_interaction_triggers(seq_id)
            for t in triggers:
                # Create unique key
                key = (
                    t['game_type'],
                    t['level_number'],
                    t['trigger_action'],
                    t.get('trigger_position_x'),
                    t.get('trigger_position_y'),
                    t['effect_type']
                )
                
                if key in trigger_map:
                    trigger_map[key]['count'] += 1
                    trigger_map[key]['confidence'] = min(0.95, trigger_map[key]['confidence'] + 0.05)
                else:
                    trigger_map[key] = {
                        'data': t,
                        'count': 1,
                        'confidence': t['confidence']
                    }
        
        # Insert triggers that appear multiple times (more reliable)
        inserted = 0
        updated = 0
        
        for key, info in trigger_map.items():
            if info['count'] < min_occurrences:
                continue
            
            t = info['data']
            t['occurrence_count'] = info['count']
            t['confidence'] = info['confidence']
            
            try:
                # Check if exists
                c.execute('''
                    SELECT trigger_id, occurrence_count, confidence 
                    FROM interaction_triggers
                    WHERE game_type = ? AND level_number = ? 
                    AND trigger_action = ? AND effect_type = ?
                ''', (t['game_type'], t['level_number'], t['trigger_action'], t['effect_type']))
                
                existing = c.fetchone()
                
                if existing:
                    # Update existing
                    c.execute('''
                        UPDATE interaction_triggers
                        SET occurrence_count = occurrence_count + ?,
                            consistent_count = consistent_count + ?,
                            confidence = MIN(0.95, confidence + 0.05),
                            last_observed = CURRENT_TIMESTAMP
                        WHERE trigger_id = ?
                    ''', (t['occurrence_count'], t['occurrence_count'], existing[0]))
                    updated += 1
                else:
                    # Insert new
                    c.execute('''
                        INSERT INTO interaction_triggers (
                            game_type, level_number, trigger_action,
                            trigger_position_x, trigger_position_y,
                            effect_type, effect_details, effect_distance,
                            occurrence_count, consistent_count, confidence,
                            first_observed, last_observed, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                  CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                    ''', (
                        t['game_type'], t['level_number'], t['trigger_action'],
                        t.get('trigger_position_x'), t.get('trigger_position_y'),
                        t['effect_type'], t.get('effect_details', '{}'),
                        t.get('effect_distance', 0),
                        t['occurrence_count'], t['occurrence_count'], t['confidence']
                    ))
                    inserted += 1
                    
            except Exception as e:
                logger.debug(f"[MINER] Trigger insert/update failed: {e}")
        
        conn.commit()
        
        if inserted > 0 or updated > 0:
            logger.info(f"[MINER] Interaction triggers: {inserted} inserted, {updated} updated")
        
        return inserted, updated
    
    # =========================================================================
    # CODS LEVEL OUTCOMES
    # =========================================================================
    
    def backfill_cods_level_outcomes(self) -> int:
        """
        Backfill cods_level_outcomes from winning sequences.
        
        Every sequence represents a successful level completion, so we can
        record level outcomes with passed=True.
        
        Returns: Number of outcomes recorded
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        # Get sequence data needed for outcomes
        c.execute('''
            SELECT sequence_id, game_id, level_number, total_actions, 
                   total_score, agent_id, generation_discovered
            FROM winning_sequences 
            WHERE is_active = 1
        ''')
        
        sequences = c.fetchall()
        recorded = 0
        
        for seq in sequences:
            game_id = seq['game_id']
            max_level = int(seq['level_number'] or seq['total_score'] or 1)
            agent_id = seq['agent_id']
            generation = seq['generation_discovered'] or 0
            total_actions = seq['total_actions'] or 1
            
            # For cumulative sequences, record outcome for each level
            actions_per_level = total_actions / max_level if max_level > 0 else total_actions
            
            for level in range(1, max_level + 1):
                outcome_id = f"mined_{seq['sequence_id']}_{level}"
                
                try:
                    # Check if already exists
                    c.execute('SELECT 1 FROM cods_level_outcomes WHERE outcome_id = ?', (outcome_id,))
                    if c.fetchone():
                        continue
                    
                    c.execute('''
                        INSERT INTO cods_level_outcomes (
                            outcome_id, game_id, agent_id, level_number,
                            passed, actions_used, score_gained,
                            generation, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        outcome_id, game_id, agent_id, level,
                        True,  # passed = True (it's a winning sequence)
                        int(actions_per_level),  # estimated actions for this level
                        1.0,  # Each level = 1.0 score
                        generation,
                        datetime.now().isoformat()
                    ))
                    recorded += 1
                    
                except Exception as e:
                    logger.debug(f"[MINER] Level outcome insert failed: {e}")
        
        conn.commit()
        
        if recorded > 0:
            logger.info(f"[MINER] CODS level outcomes: {recorded} recorded")
        
        return recorded
    
    # =========================================================================
    # ACTION EFFECTIVENESS
    # =========================================================================
    
    def backfill_action_effectiveness(self) -> int:
        """
        Update action_effectiveness based on actions in winning sequences.
        
        Actions that appear in winning sequences should have boosted success rates.
        
        Returns: Number of records updated
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        # Count action usage across all winning sequences per game
        c.execute('''
            SELECT game_id, action_sequence FROM winning_sequences 
            WHERE is_active = 1 AND action_sequence IS NOT NULL
        ''')
        
        # Aggregate: game_id -> action_number -> count
        action_counts = {}  # {game_id: {action: count}}
        
        for row in c.fetchall():
            game_id = row['game_id']
            try:
                actions = json.loads(row['action_sequence'])
                if game_id not in action_counts:
                    action_counts[game_id] = {}
                
                for action in actions:
                    action_counts[game_id][action] = action_counts[game_id].get(action, 0) + 1
            except:
                continue
        
        updated = 0
        
        for game_id, counts in action_counts.items():
            total_actions = sum(counts.values())
            
            for action_number, count in counts.items():
                # Calculate success rate boost based on frequency in wins
                frequency = count / total_actions if total_actions > 0 else 0
                
                try:
                    # Check if exists
                    c.execute('''
                        SELECT id, successes, attempts FROM action_effectiveness
                        WHERE game_id = ? AND action_number = ?
                    ''', (game_id, action_number))
                    
                    existing = c.fetchone()
                    
                    if existing:
                        # Update: add winning sequence usage as successes
                        c.execute('''
                            UPDATE action_effectiveness
                            SET successes = successes + ?,
                                attempts = attempts + ?,
                                success_rate = CAST(successes + ? AS REAL) / (attempts + ?),
                                last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (count, count, count, count, existing[0]))
                    else:
                        # Insert new
                        c.execute('''
                            INSERT INTO action_effectiveness (
                                game_id, action_number, attempts, successes,
                                success_rate, avg_score_impact, created_at, last_updated
                            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (game_id, action_number, count, count, 1.0, frequency))
                    
                    updated += 1
                    
                except Exception as e:
                    logger.debug(f"[MINER] Action effectiveness update failed: {e}")
        
        conn.commit()
        
        if updated > 0:
            logger.info(f"[MINER] Action effectiveness: {updated} records updated")
        
        return updated
    
    # =========================================================================
    # FULL MINING RUN
    # =========================================================================
    
    def mine_all_sequences(self) -> Dict[str, Any]:
        """
        Run all mining operations on the database.
        
        Returns: Summary of all operations
        """
        logger.info("[MINER] Starting full sequence mining...")
        
        results = {
            'level_breakpoints': {'updated': 0, 'failed': 0},
            'interaction_triggers': {'inserted': 0, 'updated': 0},
            'cods_level_outcomes': {'recorded': 0},
            'action_effectiveness': {'updated': 0}
        }
        
        # 1. Level breakpoints
        updated, failed = self.backfill_level_breakpoints()
        results['level_breakpoints']['updated'] = updated
        results['level_breakpoints']['failed'] = failed
        
        # 2. Interaction triggers
        inserted, updated = self.backfill_interaction_triggers()
        results['interaction_triggers']['inserted'] = inserted
        results['interaction_triggers']['updated'] = updated
        
        # 3. CODS level outcomes
        recorded = self.backfill_cods_level_outcomes()
        results['cods_level_outcomes']['recorded'] = recorded
        
        # 4. Action effectiveness
        updated = self.backfill_action_effectiveness()
        results['action_effectiveness']['updated'] = updated
        
        logger.info(f"[MINER] Mining complete: {results}")
        
        return results
    
    def mine_single_sequence(self, sequence_id: str) -> MiningResult:
        """
        Mine a single sequence for all learnable data.
        Used during sequence replay to learn from the sequence being followed.
        
        Returns: MiningResult with details of what was learned
        """
        result = MiningResult(
            sequence_id=sequence_id,
            level_breakpoints_computed=False,
            interaction_triggers_extracted=0,
            level_outcomes_recorded=0,
            action_effectiveness_updated=0,
            errors=[]
        )
        
        try:
            # 1. Compute level breakpoints if missing
            conn = self._get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT level_breakpoints FROM winning_sequences 
                WHERE sequence_id = ?
            ''', (sequence_id,))
            row = c.fetchone()
            
            if row and (not row[0] or row[0] == '{}'):
                breakpoints = self.compute_level_breakpoints(sequence_id)
                if breakpoints and len(breakpoints) > 1:
                    c.execute('''
                        UPDATE winning_sequences 
                        SET level_breakpoints = ?
                        WHERE sequence_id = ?
                    ''', (json.dumps(breakpoints), sequence_id))
                    conn.commit()
                    result.level_breakpoints_computed = True
            
            # 2. Extract interaction triggers
            triggers = self.extract_interaction_triggers(sequence_id)
            result.interaction_triggers_extracted = len(triggers)
            
            # Store triggers (with lower occurrence requirement for single seq)
            for t in triggers:
                try:
                    c.execute('''
                        INSERT OR IGNORE INTO interaction_triggers (
                            game_type, level_number, trigger_action,
                            effect_type, effect_details,
                            occurrence_count, consistent_count, confidence,
                            first_observed, last_observed, is_active
                        ) VALUES (?, ?, ?, ?, ?, 1, 1, 0.5, 
                                  CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                    ''', (
                        t['game_type'], t['level_number'], t['trigger_action'],
                        t['effect_type'], t.get('effect_details', '{}')
                    ))
                except:
                    pass
            
            conn.commit()
            
        except Exception as e:
            result.errors.append(str(e))
        
        return result


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

def run_sequence_mining():
    """Run sequence mining as standalone script"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    print("=" * 60)
    print("SEQUENCE MINER - Retroactive Learning from Winning Sequences")
    print("=" * 60)
    
    miner = SequenceMiner()
    
    try:
        # Show current state
        conn = miner._get_connection()
        c = conn.cursor()
        
        print("\n[BEFORE MINING]")
        c.execute('SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1')
        print(f"  Active sequences: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1 AND level_breakpoints IS NOT NULL AND level_breakpoints != '{}'")
        print(f"  With level_breakpoints: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM interaction_triggers')
        print(f"  Interaction triggers: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM cods_level_outcomes')
        print(f"  CODS level outcomes: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM action_effectiveness')
        print(f"  Action effectiveness records: {c.fetchone()[0]}")
        
        # Run mining
        print("\n[MINING...]")
        results = miner.mine_all_sequences()
        
        # Show results
        print("\n[AFTER MINING]")
        c.execute("SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1 AND level_breakpoints IS NOT NULL AND level_breakpoints != '{}'")
        print(f"  With level_breakpoints: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM interaction_triggers')
        print(f"  Interaction triggers: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM cods_level_outcomes')
        print(f"  CODS level outcomes: {c.fetchone()[0]}")
        
        c.execute('SELECT COUNT(*) FROM action_effectiveness')
        print(f"  Action effectiveness records: {c.fetchone()[0]}")
        
        print("\n[SUMMARY]")
        print(f"  Level breakpoints: {results['level_breakpoints']['updated']} updated, {results['level_breakpoints']['failed']} failed")
        print(f"  Interaction triggers: {results['interaction_triggers']['inserted']} inserted, {results['interaction_triggers']['updated']} updated")
        print(f"  CODS level outcomes: {results['cods_level_outcomes']['recorded']} recorded")
        print(f"  Action effectiveness: {results['action_effectiveness']['updated']} updated")
        
        print("\n" + "=" * 60)
        print("Mining complete!")
        print("=" * 60)
        
    finally:
        miner.close()


if __name__ == '__main__':
    run_sequence_mining()
