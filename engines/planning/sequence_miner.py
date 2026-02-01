import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Sequence Miner - Retroactive Learning from Winning Sequences
============================================================

Extracts learning data from stored winning sequences to backfill
knowledge tables that may be empty or incomplete.

What can be mined from sequences:
1. Level Breakpoints - Infer where each level starts based on total_score
2. Interaction Triggers - Correlate actions with frame changes
3. CODS Level Outcomes - All sequence levels are wins
4. Action Effectiveness - Track which actions appear in winning sequences

Migrated from deprecated/sequence_miner.py

Key Methods:
- mine_all_sequences(): Run all mining operations
- mine_single_sequence(): Mine a specific sequence
- compute_level_breakpoints(): Calculate where levels start
- extract_interaction_triggers(): Find action->effect correlations

Following Rules:
- Rule 2: Database-only storage
- Rule 3: Clean integration
- Rule 11: No Unicode emojis
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from engines.engine_logger import get_engine_logger

logger = get_engine_logger("sequence_miner")

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


@dataclass
class MiningResult:
    """Results from mining a single sequence."""
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
    - total_score: Number of levels completed
    - initial_frame, final_frame: Start/end states
    """

    def __init__(self, db: 'DatabaseInterface'):
        self.db = db

    # =========================================================================
    # LEVEL BREAKPOINTS COMPUTATION
    # =========================================================================

    def compute_level_breakpoints(self, sequence_id: str) -> Optional[Dict[str, int]]:
        """
        Compute level breakpoints for a sequence.

        Since we know total_score = number of levels, we can estimate
        breakpoints by dividing actions evenly or detecting frame changes.

        Returns: {"1": 0, "2": 15, "3": 32} or None
        """
        result = self.db.execute_query('''
            SELECT action_sequence, frame_transitions, total_score, total_actions,
                   coordinate_sequence, game_id
            FROM winning_sequences
            WHERE sequence_id = ?
        ''', (sequence_id,))

        if not result:
            return None

        row = result[0]

        try:
            actions = json.loads(row['action_sequence']) if row['action_sequence'] else []
            transitions = json.loads(row['frame_transitions']) if row['frame_transitions'] else []
            total_score = int(row['total_score'] or 1)
            total_actions = row['total_actions'] or len(actions)

            if total_score < 1 or total_actions < 1:
                return None

            breakpoints: Dict[str, int] = {'1': 0}

            # Method 1: Detect by frame shape changes
            if transitions and len(transitions) >= 2:
                current_level = 1
                for i in range(1, len(transitions)):
                    if current_level >= total_score:
                        break

                    frame_before = transitions[i-1]
                    frame_after = transitions[i]

                    if frame_before and frame_after:
                        shape_before = (len(frame_before), len(frame_before[0]) if frame_before else 0)
                        shape_after = (len(frame_after), len(frame_after[0]) if frame_after else 0)

                        if shape_before != shape_after:
                            if shape_after[0] > 20 or shape_before[0] < 10:
                                current_level += 1
                                breakpoints[str(current_level)] = i

                if len(breakpoints) == total_score:
                    return breakpoints

            # Method 2: Even distribution fallback
            if len(breakpoints) < total_score:
                actions_per_level = total_actions / total_score
                for level in range(2, total_score + 1):
                    if str(level) not in breakpoints:
                        breakpoints[str(level)] = int((level - 1) * actions_per_level)

            return breakpoints

        except Exception as e:
            logger.debug(f"Failed to compute breakpoints for {sequence_id}", error=str(e))
            return None

    def backfill_level_breakpoints(self) -> Tuple[int, int]:
        """
        Backfill level_breakpoints for all sequences that don't have them.

        Returns: (updated_count, failed_count)
        """
        result = self.db.execute_query('''
            SELECT sequence_id FROM winning_sequences
            WHERE is_active = 1
            AND (level_breakpoints IS NULL OR level_breakpoints = '{}')
            AND total_score > 0
        ''')

        if not result:
            return 0, 0

        sequences = [row['sequence_id'] for row in result]

        updated = 0
        failed = 0

        for seq_id in sequences:
            breakpoints = self.compute_level_breakpoints(seq_id)
            if breakpoints and len(breakpoints) > 1:
                try:
                    self.db.execute_query('''
                        UPDATE winning_sequences
                        SET level_breakpoints = ?
                        WHERE sequence_id = ?
                    ''', (json.dumps(breakpoints), seq_id))
                    updated += 1
                except Exception as e:
                    logger.debug(f"Failed to update breakpoints for {seq_id}", error=str(e))
                    failed += 1
            else:
                failed += 1

        if updated > 0:
            logger.info(f"Backfilled level_breakpoints: {updated} updated, {failed} failed")

        return updated, failed

    # =========================================================================
    # INTERACTION TRIGGERS EXTRACTION
    # =========================================================================

    def extract_interaction_triggers(self, sequence_id: str) -> List[Dict[str, Any]]:
        """
        Extract interaction triggers from action->frame correlations.

        Returns: List of trigger dictionaries
        """
        result = self.db.execute_query('''
            SELECT action_sequence, frame_transitions, coordinate_sequence,
                   game_id, level_number
            FROM winning_sequences
            WHERE sequence_id = ?
        ''', (sequence_id,))

        if not result:
            return []

        row = result[0]

        try:
            actions = json.loads(row['action_sequence']) if row['action_sequence'] else []
            transitions = json.loads(row['frame_transitions']) if row['frame_transitions'] else []
            coords = json.loads(row['coordinate_sequence']) if row['coordinate_sequence'] else []
            game_id = row['game_id']
            level_number = row['level_number'] or 1

            game_type = game_id.split('-')[0] if '-' in game_id else game_id[:4]

            triggers: List[Dict[str, Any]] = []
            coord_idx = 0

            for i in range(len(actions)):
                if i >= len(transitions) - 1:
                    break

                action = actions[i]
                frame_before = transitions[i]
                frame_after = transitions[i + 1] if i + 1 < len(transitions) else None

                if not frame_before or not frame_after:
                    continue

                action_coord = None
                if action == 6 and coord_idx < len(coords):
                    action_coord = coords[coord_idx]
                    coord_idx += 1

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
                        'confidence': 0.7
                    }
                    triggers.append(trigger)

            return triggers

        except Exception as e:
            logger.debug(f"Failed to extract triggers from {sequence_id}", error=str(e))
            return []

    def _detect_frame_changes(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Optional[Dict[str, Any]]:
        """Detect what changed between two frames."""
        try:
            if len(frame_before) != len(frame_after):
                return {
                    'effect_type': 'frame_resize',
                    'details': {
                        'before_size': (len(frame_before), len(frame_before[0]) if frame_before else 0),
                        'after_size': (len(frame_after), len(frame_after[0]) if frame_after else 0)
                    },
                    'distance': 0
                }

            changed_pixels: List[Tuple[int, int, int, int]] = []
            color_changes: Dict[Tuple[int, int], int] = {}

            for y, (row_before, row_after) in enumerate(zip(frame_before, frame_after)):
                if len(row_before) != len(row_after):
                    continue
                for x, (px_before, px_after) in enumerate(zip(row_before, row_after)):
                    if px_before != px_after:
                        changed_pixels.append((x, y, px_before, px_after))
                        key = (px_before, px_after)
                        color_changes[key] = color_changes.get(key, 0) + 1

            if not changed_pixels:
                return None

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
                'distance': 0
            }

        except Exception:
            return None

    def backfill_interaction_triggers(self, min_occurrences: int = 2) -> Tuple[int, int]:
        """
        Extract and store interaction triggers from all active sequences.

        Returns: (inserted_count, updated_count)
        """
        result = self.db.execute_query('''
            SELECT sequence_id FROM winning_sequences
            WHERE is_active = 1 AND frame_transitions IS NOT NULL
        ''')

        if not result:
            return 0, 0

        sequences = [row['sequence_id'] for row in result]

        # Aggregate triggers
        trigger_map: Dict[Tuple, Dict[str, Any]] = {}

        for seq_id in sequences:
            triggers = self.extract_interaction_triggers(seq_id)
            for t in triggers:
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

        inserted = 0
        updated = 0

        for key, info in trigger_map.items():
            if info['count'] < min_occurrences:
                continue

            t = info['data']
            t['occurrence_count'] = info['count']
            t['confidence'] = info['confidence']

            try:
                existing = self.db.execute_query('''
                    SELECT trigger_id, occurrence_count, confidence
                    FROM interaction_triggers
                    WHERE game_type = ? AND level_number = ?
                    AND trigger_action = ? AND effect_type = ?
                ''', (t['game_type'], t['level_number'], t['trigger_action'], t['effect_type']))

                if existing:
                    self.db.execute_query('''
                        UPDATE interaction_triggers
                        SET occurrence_count = occurrence_count + ?,
                            consistent_count = consistent_count + ?,
                            confidence = MIN(0.95, confidence + 0.05),
                            last_observed = CURRENT_TIMESTAMP
                        WHERE trigger_id = ?
                    ''', (t['occurrence_count'], t['occurrence_count'], existing[0]['trigger_id']))
                    updated += 1
                else:
                    self.db.execute_query('''
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
                logger.debug("Trigger insert/update failed", error=str(e))

        if inserted > 0 or updated > 0:
            logger.info(f"Interaction triggers: {inserted} inserted, {updated} updated")

        return inserted, updated

    # =========================================================================
    # CODS LEVEL OUTCOMES
    # =========================================================================

    def backfill_cods_level_outcomes(self) -> int:
        """
        Backfill cods_level_outcomes from winning sequences.

        Returns: Number of outcomes recorded
        """
        result = self.db.execute_query('''
            SELECT sequence_id, game_id, level_number, total_actions,
                   total_score, agent_id, generation_discovered
            FROM winning_sequences
            WHERE is_active = 1
        ''')

        if not result:
            return 0

        recorded = 0

        for seq in result:
            game_id = seq['game_id']
            max_level = int(seq['level_number'] or seq['total_score'] or 1)
            agent_id = seq['agent_id']
            generation = seq['generation_discovered'] or 0
            total_actions = seq['total_actions'] or 1

            actions_per_level = total_actions / max_level if max_level > 0 else total_actions

            for level in range(1, max_level + 1):
                outcome_id = f"mined_{seq['sequence_id']}_{level}"

                try:
                    exists = self.db.execute_query(
                        'SELECT 1 FROM cods_level_outcomes WHERE outcome_id = ?',
                        (outcome_id,)
                    )
                    if exists:
                        continue

                    self.db.execute_query('''
                        INSERT INTO cods_level_outcomes (
                            outcome_id, game_id, agent_id, level_number,
                            passed, actions_used, score_gained,
                            generation, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        outcome_id, game_id, agent_id, level,
                        True,
                        int(actions_per_level),
                        1.0,
                        generation,
                        datetime.now().isoformat()
                    ))
                    recorded += 1

                except Exception as e:
                    logger.debug("Level outcome insert failed", error=str(e))

        if recorded > 0:
            logger.info(f"CODS level outcomes: {recorded} recorded")

        return recorded

    # =========================================================================
    # ACTION EFFECTIVENESS
    # =========================================================================

    def backfill_action_effectiveness(self) -> int:
        """
        Update action_effectiveness based on actions in winning sequences.

        Returns: Number of records updated
        """
        result = self.db.execute_query('''
            SELECT game_id, action_sequence FROM winning_sequences
            WHERE is_active = 1 AND action_sequence IS NOT NULL
        ''')

        if not result:
            return 0

        action_counts: Dict[str, Dict[int, int]] = {}

        for row in result:
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
                frequency = count / total_actions if total_actions > 0 else 0

                try:
                    existing = self.db.execute_query('''
                        SELECT id, successes, attempts FROM action_effectiveness
                        WHERE game_id = ? AND action_number = ?
                    ''', (game_id, action_number))

                    if existing:
                        self.db.execute_query('''
                            UPDATE action_effectiveness
                            SET successes = successes + ?,
                                attempts = attempts + ?,
                                success_rate = CAST(successes + ? AS REAL) / (attempts + ?),
                                last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (count, count, count, count, existing[0]['id']))
                    else:
                        self.db.execute_query('''
                            INSERT INTO action_effectiveness (
                                game_id, action_number, attempts, successes,
                                success_rate, avg_score_impact, created_at, last_updated
                            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (game_id, action_number, count, count, 1.0, frequency))

                    updated += 1

                except Exception as e:
                    logger.debug("Action effectiveness update failed", error=str(e))

        if updated > 0:
            logger.info(f"Action effectiveness: {updated} records updated")

        return updated

    # =========================================================================
    # FULL MINING RUN
    # =========================================================================

    def mine_all_sequences(self) -> Dict[str, Any]:
        """
        Run all mining operations on the database.

        Returns: Summary of all operations
        """
        logger.info("Starting full sequence mining...")

        results: Dict[str, Any] = {
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

        logger.info(f"Mining complete", results=results)

        return results

    def mine_single_sequence(self, sequence_id: str) -> MiningResult:
        """
        Mine a single sequence for all learnable data.

        Returns: MiningResult with details
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
            seq_data = self.db.execute_query('''
                SELECT level_breakpoints FROM winning_sequences
                WHERE sequence_id = ?
            ''', (sequence_id,))

            if seq_data and (not seq_data[0]['level_breakpoints'] or seq_data[0]['level_breakpoints'] == '{}'):
                breakpoints = self.compute_level_breakpoints(sequence_id)
                if breakpoints and len(breakpoints) > 1:
                    self.db.execute_query('''
                        UPDATE winning_sequences
                        SET level_breakpoints = ?
                        WHERE sequence_id = ?
                    ''', (json.dumps(breakpoints), sequence_id))
                    result.level_breakpoints_computed = True

            # 2. Extract interaction triggers
            triggers = self.extract_interaction_triggers(sequence_id)
            result.interaction_triggers_extracted = len(triggers)

            # Store triggers
            for t in triggers:
                try:
                    self.db.execute_query('''
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

        except Exception as e:
            result.errors.append(str(e))

        return result

    def get_mining_stats(self) -> Dict[str, Any]:
        """Get current state of mined data."""
        try:
            sequences = self.db.execute_query(
                'SELECT COUNT(*) as cnt FROM winning_sequences WHERE is_active = 1'
            )
            with_breakpoints = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM winning_sequences WHERE is_active = 1 AND level_breakpoints IS NOT NULL AND level_breakpoints != '{}'"
            )
            triggers = self.db.execute_query(
                'SELECT COUNT(*) as cnt FROM interaction_triggers'
            )
            outcomes = self.db.execute_query(
                'SELECT COUNT(*) as cnt FROM cods_level_outcomes'
            )
            effectiveness = self.db.execute_query(
                'SELECT COUNT(*) as cnt FROM action_effectiveness'
            )

            return {
                'active_sequences': sequences[0]['cnt'] if sequences else 0,
                'with_breakpoints': with_breakpoints[0]['cnt'] if with_breakpoints else 0,
                'interaction_triggers': triggers[0]['cnt'] if triggers else 0,
                'cods_level_outcomes': outcomes[0]['cnt'] if outcomes else 0,
                'action_effectiveness': effectiveness[0]['cnt'] if effectiveness else 0
            }
        except Exception as e:
            return {'error': str(e)}
