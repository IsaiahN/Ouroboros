#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
SAFE DATABASE CLEANUP
=====================
The primary database cleanup routine for the Ouroboros system.
Called by autonomous_evolution_runner.py and can be run standalone.

DATA LIFECYCLE PHILOSOPHY:
==========================
Data in this system follows a lifecycle:

1. RAW OBSERVATIONS (Per-Game Ephemeral)
   - object_property_snapshots, trigger_sequence_events, collision_events
   - Only useful DURING gameplay to detect patterns
   - Once patterns extracted to aggregated tables, raw data is redundant
   - CLEANUP: After game ends AND patterns recorded

2. AGGREGATED KNOWLEDGE (Permanent Network Memory)
   - interaction_triggers, trigger_sequences, collision_effects
   - Compressed patterns validated across multiple agents/generations
   - Like winning_sequences - these ARE the learned knowledge
   - CLEANUP: NEVER delete (only deprecate if stale)

3. VALIDATION-DEPENDENT DATA (Cross-Generational)
   - Triggers have occurrence_count, consistent_count, inconsistent_count
   - Each new agent validates/refutes patterns, refining confidence
   - Raw data from current generation needed for validation
   - CLEANUP: Keep current generation's raw data until validation complete

RETENTION STRATEGY:
==================
- Raw data: Keep from last 30 GENERATIONS (not time-based!)
- Aggregated patterns: Keep forever (mark is_active=FALSE if stale)
- Stale pattern threshold: 50 generations with no observations
- ASYNC-SAFE: Uses generations as computational clock, not wall time
- PORTABLE: Works on any hardware speed - fast machine = more gens/day

WHAT THIS CLEANS:
- Zero-score game results (failed games, no learning value)
- Old system/database logs (keep recent 5,000)
- Old score history (>7 days)
- Old sensation learning events (keep 200,000)
- Excessive navigation state history (keep 50,000)
- Old action traces (keep 500,000)
- Raw observation data from COMPLETED generations
- Stale patterns (50+ generations without observation)

WHAT THIS PRESERVES:
- Winning sequences (CRITICAL)
- Active agents
- Game results with positive scores
- All aggregated knowledge patterns (interaction_triggers, trigger_sequences, etc.)
- Current generation's raw observation data (for cross-agent validation)

Per Master Ruleset Rule 2: All data in database, intelligent cleanup

Usage:
    python safe_cleanup.py              # Dry run (shows what would be deleted)
    python safe_cleanup.py --execute    # Actually perform cleanup
    
Called from autonomous_evolution_runner.py every 10 generations.
"""
import sqlite3
import os
from datetime import datetime, timedelta

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


class SafeDatabaseCleaner:
    """
    Safe database cleanup that preserves all critical learning data.
    
    DATA CATEGORIES:
    ================
    
    1. EPHEMERAL RAW DATA (delete after N generations complete):
       - object_property_snapshots: Object state per action (huge volume)
       - object_property_changes: Property change log
       - trigger_sequence_events: Individual trigger steps during gameplay
       - collision_events: Individual collision records
       - action6_availability_events: ACTION6 state changes
       
       These are PER-GAME observations. They're linked to game_id, which
       has a generation number. We keep raw data from the last N generations
       (default: 10) to ensure cross-agent validation can complete.
       
       SAFE: Uses multi-layer protection:
       1. Try generation-based via game_results.generation
       2. Try generation-based via session -> agent link
       3. Final fallback: keep most recent 50M records by count
       
       ALL methods are generation-agnostic (no time assumptions).
       System paused for a month? Nothing deleted until new gens run.
       
       RETENTION: Keep raw data from last 30 generations
    
    2. AGGREGATED KNOWLEDGE (never delete, only deprecate):
       - interaction_triggers: Causal patterns with consistency scores
       - trigger_sequences: Proven trigger orderings (winning sequences)
       - collision_effects: What happens when objects collide
       - selectability_conditions: What enables ACTION6
       - autonomous_objects: NPCs/independent movers
       
       These ARE the learned knowledge. Like winning_sequences, they
       represent compressed wisdom from thousands of observations.
       
       RETENTION: Permanent. Mark is_active=FALSE if stale (50+ generations
       without observation or confidence < 10% after 20+ attempts).
    
    3. OPERATIONAL DATA (standard retention by count/age):
       - score_history: 7 days
       - system_logs: 5,000 entries
       - navigation_state_history: 50,000 entries
       - action_traces: 500,000 entries
       - sensation_learning_events: 200,000 entries
       - agent_operating_modes: 100,000 entries
       - decision_weaving_reports: 50,000 entries
       - role_cohort_wisdom: 7 days (cache, recalculated on demand)
       - network_failure_hypotheses: 10,000 (keep validated + high-confidence)
    """
    
    def __init__(self, db_path='core_data.db'):
        self.db_path = db_path
        
        # =================================================================
        # OPERATIONAL DATA RETENTION (by count or age)
        # =================================================================
        self.score_history_retention_days = 7
        # FIX (2025-01-11): Increased from 5,000 to 50,000 to match database_logger.py
        # These logs are NOT used for reasoning - only for debugging
        self.system_logs_retention = 50000
        self.navigation_retention = 50000
        self.action_traces_retention = 50000  # Reduced from 500K - old traces already captured in winning_sequences
        self.sensation_events_retention = 200000
        self.operating_modes_retention = 100000
        self.weaving_reports_retention = 50000
        self.cohort_wisdom_retention_days = 7
        self.failure_hypotheses_retention = 10000
        
        # =================================================================
        # RAW OBSERVATION DATA RETENTION
        # =================================================================
        # Strategy: Keep raw data from the last N GENERATIONS.
        # 
        # This is GENERATION-BASED, not time-based. The system measures
        # its own computational progress, not human wall-clock time.
        # 
        # Benefits:
        # - Works asynchronously (no 24/7 requirement)
        # - Portable across different hardware speeds
        # - Self-referential (system measures itself)
        # - Safe during pauses (nothing deleted until new gens run)
        #
        # If someone runs this on fast hardware: more gens/day, more cleanup
        # If someone runs this on slow hardware: fewer gens/day, less cleanup
        # If system pauses for a week: no cleanup until evolution resumes
        #
        # 30 generations = roughly 1 week of continuous evolution at ~4h/gen
        # But the actual time doesn't matter - what matters is 30 generations
        # of learning have occurred, making older raw data redundant.
        self.raw_data_generation_retention = 30  # Keep raw data from last 30 generations
        
        # =================================================================
        # AGGREGATED KNOWLEDGE DEPRECATION
        # =================================================================
        # Patterns become stale if not observed for many generations.
        # Don't delete - just mark inactive (game might return).
        self.pattern_staleness_generations = 50
        self.pattern_low_confidence_threshold = 0.10
        self.pattern_min_attempts_for_deprecation = 20
    
    def cleanup(self, dry_run=True, verbose=True):
        """
        Run all cleanup operations.
        
        Args:
            dry_run: If True, only report what would be deleted
            verbose: If True, print progress messages
            
        Returns:
            dict with cleanup statistics
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        results = {
            'dry_run': dry_run,
            'total_deleted': 0,
            'tables_cleaned': {}
        }
        
        if verbose:
            db_size = os.path.getsize(self.db_path) / (1024*1024*1024)
            print(f'Database size: {db_size:.2f} GB')
        
        # 1. Zero-score game results
        if verbose:
            print('\n1. Zero-score game results')
        results['tables_cleaned']['game_results'] = self._clean_zero_score_games(c, conn, dry_run, verbose)
        
        # 2. Old score history
        if verbose:
            print('\n2. Old score history (>7 days)')
        results['tables_cleaned']['score_history'] = self._clean_old_score_history(c, conn, dry_run, verbose)
        
        # 3. System logs
        if verbose:
            print('\n3. Excessive system logs')
        results['tables_cleaned']['system_logs'] = self._clean_system_logs(c, conn, dry_run, verbose)
        
        # 4. Navigation state history
        if verbose:
            print('\n4. Old navigation state history')
        results['tables_cleaned']['navigation_state_history'] = self._clean_navigation_history(c, conn, dry_run, verbose)
        
        # 5. Action traces
        if verbose:
            print('\n5. Old action traces')
        results['tables_cleaned']['action_traces'] = self._clean_action_traces(c, conn, dry_run, verbose)
        
        # 6. Sensation learning events
        if verbose:
            print('\n6. Old sensation learning events')
        results['tables_cleaned']['sensation_learning_events'] = self._clean_sensation_events(c, conn, dry_run, verbose)
        
        # 7. Agent operating modes
        if verbose:
            print('\n7. Old agent operating modes')
        results['tables_cleaned']['agent_operating_modes'] = self._clean_operating_modes(c, conn, dry_run, verbose)
        
        # 8. Two-Streams: Decision weaving reports
        if verbose:
            print('\n8. Old decision weaving reports (Two-Streams)')
        results['tables_cleaned']['decision_weaving_reports'] = self._clean_weaving_reports(c, conn, dry_run, verbose)
        
        # 9. Two-Streams: Role cohort wisdom cache
        if verbose:
            print('\n9. Old role cohort wisdom cache')
        results['tables_cleaned']['role_cohort_wisdom'] = self._clean_cohort_wisdom(c, conn, dry_run, verbose)
        
        # 10. Network failure hypotheses (keep high-value + validated)
        if verbose:
            print('\n10. Old/low-value failure hypotheses')
        results['tables_cleaned']['network_failure_hypotheses'] = self._clean_failure_hypotheses(c, conn, dry_run, verbose)
        
        # =====================================================================
        # SESSION 23: RAW OBSERVATION DATA CLEANUP
        # =====================================================================
        # These tables contain per-action raw data that feeds aggregated patterns.
        # Strategy: Keep only current generation (last 24h) for cross-agent validation.
        # Once generation completes, patterns are in aggregated tables.
        
        # 11. Object property snapshots (HUGE volume - every object * every action)
        if verbose:
            print('\n11. Old object property snapshots (raw data)')
        results['tables_cleaned']['object_property_snapshots'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose, 
            table='object_property_snapshots',
            id_column='snapshot_id',
            timestamp_column='timestamp'
        )
        
        # 12. Object property changes
        if verbose:
            print('\n12. Old object property changes (raw data)')
        results['tables_cleaned']['object_property_changes'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='object_property_changes', 
            id_column='change_id',
            timestamp_column='timestamp'
        )
        
        # 13. Trigger sequence events (steps during gameplay, before finalization)
        if verbose:
            print('\n13. Old trigger sequence events (raw data)')
        results['tables_cleaned']['trigger_sequence_events'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='trigger_sequence_events',
            id_column='event_id', 
            timestamp_column='timestamp'
        )
        
        # 14. Collision events
        if verbose:
            print('\n14. Old collision events (raw data)')
        results['tables_cleaned']['collision_events'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='collision_events',
            id_column='collision_id',
            timestamp_column='timestamp'
        )
        
        # 15. ACTION6 availability events
        if verbose:
            print('\n15. Old ACTION6 availability events (raw data)')
        results['tables_cleaned']['action6_availability_events'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='action6_availability_events',
            id_column='event_id',
            timestamp_column='timestamp'
        )
        
        # =====================================================================
        # SESSION 25: PERCEPTUAL PRIMITIVES DATA CLEANUP
        # =====================================================================
        # New tables from perceptual primitives framework (agent_self_model.py)
        # Classification:
        #   RAW (30 gen retention): perceptual_observations, control_transfer_events, indirect_causation_events
        #   AGGREGATED (permanent with deprecation): self_object_identity, control_transfer_patterns,
        #       grid_region_classification, detected_resource_counters, valence_associations, inferred_goal_states
        
        # 16. Perceptual observations (RAW - per-action data)
        if verbose:
            print('\n16. Old perceptual observations (raw data)')
        results['tables_cleaned']['perceptual_observations'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='perceptual_observations',
            id_column='observation_id',
            timestamp_column='timestamp'
        )
        
        # 17. Control transfer events (RAW - individual transfer occurrences)
        if verbose:
            print('\n17. Old control transfer events (raw data)')
        results['tables_cleaned']['control_transfer_events'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='control_transfer_events',
            id_column='event_id',
            timestamp_column='timestamp'
        )
        
        # 18. Indirect causation events (RAW - individual causation occurrences)
        if verbose:
            print('\n18. Old indirect causation events (raw data)')
        results['tables_cleaned']['indirect_causation_events'] = self._clean_raw_observation_data(
            c, conn, dry_run, verbose,
            table='indirect_causation_events',
            id_column='event_id',
            timestamp_column='timestamp'
        )
        
        # =====================================================================
        # AGGREGATED KNOWLEDGE DEPRECATION (mark stale, don't delete)
        # =====================================================================
        
        # 19. Deprecate stale interaction triggers
        if verbose:
            print('\n19. Deprecate stale interaction triggers')
        results['tables_cleaned']['interaction_triggers_deprecated'] = self._deprecate_stale_patterns(
            c, conn, dry_run, verbose,
            table='interaction_triggers',
            use_confidence=True
        )
        
        # 20. Deprecate stale trigger sequences (but NOT delete - these are like winning sequences)
        if verbose:
            print('\n20. Deprecate stale trigger sequences')
        results['tables_cleaned']['trigger_sequences_deprecated'] = self._deprecate_stale_patterns(
            c, conn, dry_run, verbose,
            table='trigger_sequences',
            use_confidence=False  # trigger_sequences use success_rate, not confidence
        )
        
        # =====================================================================
        # SESSION 25: AGGREGATED PERCEPTUAL KNOWLEDGE DEPRECATION
        # =====================================================================
        # These tables contain network-learned patterns from perceptual primitives.
        # Don't delete - just mark stale (patterns may become relevant again).
        
        # 21. Deprecate stale self-object identity mappings
        if verbose:
            print('\n21. Deprecate stale self-object identity')
        results['tables_cleaned']['self_object_identity_deprecated'] = self._deprecate_stale_patterns(
            c, conn, dry_run, verbose,
            table='self_object_identity',
            use_confidence=True
        )
        
        # 22. Deprecate stale control transfer patterns
        if verbose:
            print('\n22. Deprecate stale control transfer patterns')
        results['tables_cleaned']['control_transfer_patterns_deprecated'] = self._deprecate_stale_patterns(
            c, conn, dry_run, verbose,
            table='control_transfer_patterns',
            use_confidence=True
        )
        
        # 23. Deprecate stale valence associations
        if verbose:
            print('\n23. Deprecate stale valence associations')
        results['tables_cleaned']['valence_associations_deprecated'] = self._deprecate_stale_patterns(
            c, conn, dry_run, verbose,
            table='valence_associations',
            use_confidence=True
        )

        # 24. Apply decay scores to metacog/observer telemetry (no deletes; skip legacy)
        if verbose:
            print('\n24. Apply decay scores (metacog/observer/oracle/valence)')
        results['tables_cleaned']['decay_updates'] = self._apply_decay_scores(
            c, conn, dry_run, verbose,
            tables=[
                'metacognitive_assumptions',
                'metacognitive_eliminations',
                'metacognitive_failure_patterns',
                'metacognitive_insights',
                'metacognitive_predictions',
                'gap_registry',
                'interventions',
                'oracle_observations',
                'valence_associations',
            ]
        )
        
        # NOTE: grid_region_classification, detected_resource_counters, inferred_goal_states
        # do NOT have is_active columns - they're structural data that doesn't become stale.
        # They remain as permanent reference data for the game/level.
        
        # Calculate total
        results['total_deleted'] = sum(r.get('deleted', 0) for r in results['tables_cleaned'].values())
        
        conn.close()
        return results
    
    def _clean_zero_score_games(self, c, conn, dry_run, verbose):
        """Delete zero-score game results."""
        c.execute('SELECT COUNT(*) FROM game_results WHERE final_score = 0')
        count = c.fetchone()[0]
        
        if verbose:
            print(f'   Found: {count:,} zero-score games')
        
        if not dry_run and count > 0:
            c.execute('DELETE FROM game_results WHERE final_score = 0')
            conn.commit()
            if verbose:
                print(f'   Deleted: {count:,} rows')
            return {'found': count, 'deleted': count}
        elif count > 0 and verbose:
            print(f'   Would delete: {count:,} rows')
        
        return {'found': count, 'deleted': 0}
    
    def _clean_old_score_history(self, c, conn, dry_run, verbose):
        """Delete score history older than retention period."""
        cutoff = (datetime.now() - timedelta(days=self.score_history_retention_days)).isoformat()
        c.execute('SELECT COUNT(*) FROM score_history WHERE timestamp < ?', (cutoff,))
        count = c.fetchone()[0]
        
        if verbose:
            print(f'   Found: {count:,} old records')
        
        if not dry_run and count > 0:
            c.execute('DELETE FROM score_history WHERE timestamp < ?', (cutoff,))
            conn.commit()
            if verbose:
                print(f'   Deleted: {count:,} rows')
            return {'found': count, 'deleted': count}
        elif count > 0 and verbose:
            print(f'   Would delete: {count:,} rows')
        
        return {'found': count, 'deleted': 0}
    
    def _clean_system_logs(self, c, conn, dry_run, verbose):
        """Keep only the most recent system logs."""
        c.execute('SELECT COUNT(*) FROM system_logs')
        total = c.fetchone()[0]
        excess = max(0, total - self.system_logs_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM system_logs 
                WHERE id NOT IN (
                    SELECT id FROM system_logs 
                    ORDER BY timestamp DESC 
                    LIMIT {self.system_logs_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_navigation_history(self, c, conn, dry_run, verbose):
        """Keep only the most recent navigation state history."""
        c.execute('SELECT COUNT(*) FROM navigation_state_history')
        total = c.fetchone()[0]
        excess = max(0, total - self.navigation_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM navigation_state_history
                WHERE history_id NOT IN (
                    SELECT history_id FROM navigation_state_history
                    ORDER BY state_timestamp DESC
                    LIMIT {self.navigation_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_action_traces(self, c, conn, dry_run, verbose):
        """Keep only the most recent action traces."""
        c.execute('SELECT COUNT(*) FROM action_traces')
        total = c.fetchone()[0]
        excess = max(0, total - self.action_traces_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM action_traces
                WHERE id NOT IN (
                    SELECT id FROM action_traces
                    ORDER BY timestamp DESC
                    LIMIT {self.action_traces_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_sensation_events(self, c, conn, dry_run, verbose):
        """Keep only the most recent sensation learning events."""
        c.execute('SELECT COUNT(*) FROM sensation_learning_events')
        total = c.fetchone()[0]
        excess = max(0, total - self.sensation_events_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM sensation_learning_events
                WHERE event_id NOT IN (
                    SELECT event_id FROM sensation_learning_events
                    ORDER BY event_timestamp DESC
                    LIMIT {self.sensation_events_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_operating_modes(self, c, conn, dry_run, verbose):
        """Keep only the most recent agent operating modes."""
        c.execute('SELECT COUNT(*) FROM agent_operating_modes')
        total = c.fetchone()[0]
        excess = max(0, total - self.operating_modes_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM agent_operating_modes
                WHERE mode_id NOT IN (
                    SELECT mode_id FROM agent_operating_modes
                    ORDER BY assigned_timestamp DESC
                    LIMIT {self.operating_modes_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_weaving_reports(self, c, conn, dry_run, verbose):
        """Keep only the most recent decision weaving reports (Two-Streams)."""
        try:
            c.execute('SELECT COUNT(*) FROM decision_weaving_reports')
            total = c.fetchone()[0]
        except:
            if verbose:
                print('   Table does not exist (skip)')
            return {'found': 0, 'deleted': 0}
        
        excess = max(0, total - self.weaving_reports_retention)
        
        if verbose:
            print(f'   Total: {total:,}, Excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM decision_weaving_reports
                WHERE report_id NOT IN (
                    SELECT report_id FROM decision_weaving_reports
                    ORDER BY timestamp DESC
                    LIMIT {self.weaving_reports_retention}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _clean_cohort_wisdom(self, c, conn, dry_run, verbose):
        """Delete old role cohort wisdom cache (re-calculated on demand)."""
        try:
            cutoff = (datetime.now() - timedelta(days=self.cohort_wisdom_retention_days)).isoformat()
            c.execute('SELECT COUNT(*) FROM role_cohort_wisdom WHERE last_updated < ?', (cutoff,))
            count = c.fetchone()[0]
        except:
            if verbose:
                print('   Table does not exist (skip)')
            return {'found': 0, 'deleted': 0}
        
        if verbose:
            print(f'   Found: {count:,} old cache entries')
        
        if not dry_run and count > 0:
            c.execute('DELETE FROM role_cohort_wisdom WHERE last_updated < ?', (cutoff,))
            conn.commit()
            if verbose:
                print(f'   Deleted: {count:,} rows')
            return {'found': count, 'deleted': count}
        elif count > 0 and verbose:
            print(f'   Would delete: {count:,} rows')
        
        return {'found': count, 'deleted': 0}
    
    def _clean_failure_hypotheses(self, c, conn, dry_run, verbose):
        """Delete old/low-value failure hypotheses.
        
        Retention policy:
        - ALWAYS keep: validated_by_win = TRUE (proven correct)
        - ALWAYS keep: upvotes > downvotes (community approved)
        - Keep up to retention limit sorted by confidence + recency
        - Delete: old, low-confidence, unvalidated hypotheses
        """
        try:
            c.execute('SELECT COUNT(*) FROM network_failure_hypotheses')
            total_count = c.fetchone()[0]
        except:
            if verbose:
                print('   Table does not exist (skip)')
            return {'found': 0, 'deleted': 0}
        
        if total_count <= self.failure_hypotheses_retention:
            if verbose:
                print(f'   Found: {total_count:,} hypotheses (under limit of {self.failure_hypotheses_retention:,})')
            return {'found': 0, 'deleted': 0}
        
        # Count how many we'd delete
        # Keep: validated, upvoted, or top N by confidence
        c.execute('''
            SELECT COUNT(*) FROM network_failure_hypotheses
            WHERE validated_by_win = 0
            AND upvotes <= downvotes
            AND hypothesis_id NOT IN (
                SELECT hypothesis_id FROM network_failure_hypotheses
                WHERE validated_by_win = 0 AND upvotes <= downvotes
                ORDER BY confidence DESC, last_referenced DESC
                LIMIT ?
            )
        ''', (self.failure_hypotheses_retention,))
        to_delete = c.fetchone()[0]
        
        if verbose:
            print(f'   Found: {to_delete:,} low-value hypotheses to remove')
        
        if not dry_run and to_delete > 0:
            c.execute('''
                DELETE FROM network_failure_hypotheses
                WHERE validated_by_win = 0
                AND upvotes <= downvotes
                AND hypothesis_id NOT IN (
                    SELECT hypothesis_id FROM network_failure_hypotheses
                    WHERE validated_by_win = 0 AND upvotes <= downvotes
                    ORDER BY confidence DESC, last_referenced DESC
                    LIMIT ?
                )
            ''', (self.failure_hypotheses_retention,))
            conn.commit()
            if verbose:
                print(f'   Deleted: {to_delete:,} rows')
            return {'found': to_delete, 'deleted': to_delete}
        elif to_delete > 0 and verbose:
            print(f'   Would delete: {to_delete:,} rows')
        
        return {'found': to_delete, 'deleted': 0}
    
    # =========================================================================
    # SESSION 23: RAW OBSERVATION DATA CLEANUP
    # =========================================================================
    
    def _clean_raw_observation_data(self, c, conn, dry_run, verbose, 
                                     table: str, id_column: str, timestamp_column: str):
        """
        Clean raw observation data tables using PURE GENERATION-BASED retention.
        
        NO TIME-BASED LOGIC. The system measures its own computational progress
        (generations), not human wall-clock time. This makes it:
        - Asynchronous (no 24/7 requirement)
        - Portable (works on any hardware speed)
        - Self-referential (system measures itself)
        - Safe during pauses (nothing deleted until new generations run)
        
        Strategy:
        1. Get current generation from agents table (MAX(generation))
        2. Calculate cutoff = current_gen - retention_generations
        3. Delete raw data linked to games from generations < cutoff
        4. If generation link not available, fall back to COUNT-based (keep N most recent)
        
        The count-based fallback is also generation-agnostic - it just keeps
        the most recent N records regardless of when they were created.
        
        Args:
            table: Table name to clean
            id_column: Primary key column name  
            timestamp_column: Ignored (kept for API compatibility)
        """
        try:
            c.execute(f'SELECT COUNT(*) FROM {table}')
            total = c.fetchone()[0]
        except:
            if verbose:
                print(f'   Table {table} does not exist (skip)')
            return {'found': 0, 'deleted': 0}
        
        if total == 0:
            if verbose:
                print(f'   Table {table} is empty')
            return {'found': 0, 'deleted': 0}
        
        # Check if table has game_id column
        c.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in c.fetchall()}
        
        if 'game_id' not in columns:
            if verbose:
                print(f'   Table {table} has no game_id column (skip)')
            return {'found': 0, 'deleted': 0}
        
        # Get current generation (the system's own computational clock)
        try:
            c.execute('SELECT MAX(generation) FROM agents')
            row = c.fetchone()
            current_gen = int(row[0]) if row and row[0] else 0
        except:
            current_gen = 0
        
        if current_gen == 0:
            if verbose:
                print(f'   Cannot determine current generation (skip)')
            return {'found': 0, 'deleted': 0}
        
        cutoff_gen = current_gen - self.raw_data_generation_retention
        
        if cutoff_gen <= 0:
            if verbose:
                print(f'   Only {current_gen} generations run, keeping all data (retention={self.raw_data_generation_retention})')
            return {'found': 0, 'deleted': 0}
        
        # Try to link raw data -> game_results -> session -> agent -> generation
        # This requires game_results to have session_id which links to agents
        try:
            # Method 1: Direct generation link if game_results has generation column
            c.execute("PRAGMA table_info(game_results)")
            gr_columns = {row[1] for row in c.fetchall()}
            
            if 'generation' in gr_columns:
                # Direct link available
                c.execute(f'''
                    SELECT COUNT(*) FROM {table} t
                    WHERE EXISTS (
                        SELECT 1 FROM game_results g 
                        WHERE g.game_id = t.game_id 
                        AND g.generation < ?
                    )
                ''', (cutoff_gen,))
                old_count = c.fetchone()[0]
                
                if verbose:
                    print(f'   Total: {total:,}, From gens < {cutoff_gen} (of {current_gen}): {old_count:,}')
                
                if not dry_run and old_count > 0:
                    c.execute(f'''
                        DELETE FROM {table}
                        WHERE EXISTS (
                            SELECT 1 FROM game_results g 
                            WHERE g.game_id = {table}.game_id 
                            AND g.generation < ?
                        )
                    ''', (cutoff_gen,))
                    conn.commit()
                    if verbose:
                        print(f'   Deleted: {old_count:,} rows')
                    return {'found': old_count, 'deleted': old_count}
                elif old_count > 0 and verbose:
                    print(f'   Would delete: {old_count:,} rows')
                return {'found': old_count, 'deleted': 0}
            
            # Method 2: Link through sessions to agents (if available)
            if 'session_id' in gr_columns:
                c.execute(f'''
                    SELECT COUNT(*) FROM {table} t
                    WHERE EXISTS (
                        SELECT 1 FROM game_results g
                        JOIN agents a ON g.session_id = a.agent_id
                        WHERE g.game_id = t.game_id 
                        AND a.generation < ?
                    )
                ''', (cutoff_gen,))
                old_count = c.fetchone()[0]
                
                if verbose:
                    print(f'   Total: {total:,}, From gens < {cutoff_gen} (via agents): {old_count:,}')
                
                if not dry_run and old_count > 0:
                    c.execute(f'''
                        DELETE FROM {table}
                        WHERE EXISTS (
                            SELECT 1 FROM game_results g
                            JOIN agents a ON g.session_id = a.agent_id
                            WHERE g.game_id = {table}.game_id 
                            AND a.generation < ?
                        )
                    ''', (cutoff_gen,))
                    conn.commit()
                    if verbose:
                        print(f'   Deleted: {old_count:,} rows')
                    return {'found': old_count, 'deleted': old_count}
                elif old_count > 0 and verbose:
                    print(f'   Would delete: {old_count:,} rows')
                return {'found': old_count, 'deleted': 0}
                
        except Exception as e:
            if verbose:
                print(f'   Generation link failed: {e}')
        
        # FALLBACK: Count-based retention (also generation-agnostic)
        # Keep the most recent N records. This is still safe because:
        # - Recent records = recent generations (by definition)
        # - No time-based assumptions
        # - Works regardless of schema limitations
        #
        # Estimate: 30 gens * 150 games/gen * 1000 actions * 10 objects = 45M records
        # We'll keep 50M as a safe buffer
        retention_count = 50_000_000  # 50 million records
        
        # But also cap at a reasonable size based on current total
        # If table is small, just skip
        if total < retention_count:
            if verbose:
                print(f'   Total: {total:,}, under {retention_count:,} limit (skip)')
            return {'found': 0, 'deleted': 0}
        
        excess = total - retention_count
        
        if verbose:
            print(f'   Count-based fallback: Total {total:,}, keeping {retention_count:,}, excess: {excess:,}')
        
        if not dry_run and excess > 0:
            c.execute(f'''
                DELETE FROM {table}
                WHERE {id_column} NOT IN (
                    SELECT {id_column} FROM {table}
                    ORDER BY {id_column} DESC
                    LIMIT {retention_count}
                )
            ''')
            conn.commit()
            if verbose:
                print(f'   Deleted: {excess:,} rows')
            return {'found': excess, 'deleted': excess}
        elif excess > 0 and verbose:
            print(f'   Would delete: {excess:,} rows')
        
        return {'found': excess, 'deleted': 0}
    
    def _deprecate_stale_patterns(self, c, conn, dry_run, verbose, 
                                   table: str, use_confidence: bool = True):
        """
        Mark stale patterns as inactive (don't delete - game might return).
        
        Patterns become stale if:
        1. Not observed for pattern_staleness_generations (50+) generations
        2. Confidence dropped below threshold after min attempts
        
        This is like pariah decay - knowledge that's no longer relevant
        gets marked inactive, but isn't deleted in case it becomes
        relevant again.
        
        Args:
            table: Table name (must have is_active, last_observed columns)
            use_confidence: If True, also check confidence threshold
        """
        try:
            # Check if table has required columns
            c.execute(f"PRAGMA table_info({table})")
            columns = {row[1] for row in c.fetchall()}
            
            if 'is_active' not in columns:
                if verbose:
                    print(f'   Table {table} has no is_active column (skip)')
                return {'found': 0, 'deleted': 0, 'deprecated': 0}
                
        except Exception as e:
            if verbose:
                print(f'   Table {table} does not exist (skip)')
            return {'found': 0, 'deleted': 0, 'deprecated': 0}
        
        deprecated = 0
        
        # Get current generation from evolutionary_state
        try:
            c.execute('SELECT value FROM evolutionary_state WHERE key = "current_generation"')
            row = c.fetchone()
            current_gen = int(row[0]) if row else 0
        except:
            current_gen = 0
        
        staleness_cutoff = current_gen - self.pattern_staleness_generations
        
        # Count and deprecate stale patterns (not observed in 50+ generations)
        # Check if table has generation tracking
        if 'last_observed_generation' in columns:
            c.execute(f'''
                SELECT COUNT(*) FROM {table} 
                WHERE is_active = 1 AND last_observed_generation < ?
            ''', (staleness_cutoff,))
            stale_by_gen = c.fetchone()[0]
            
            if not dry_run and stale_by_gen > 0:
                c.execute(f'''
                    UPDATE {table} SET is_active = 0 
                    WHERE is_active = 1 AND last_observed_generation < ?
                ''', (staleness_cutoff,))
                deprecated += stale_by_gen
        else:
            stale_by_gen = 0
        
        # Also deprecate low-confidence patterns (if confidence tracking exists)
        stale_by_confidence = 0
        if use_confidence and 'confidence' in columns and 'occurrence_count' in columns:
            c.execute(f'''
                SELECT COUNT(*) FROM {table}
                WHERE is_active = 1 
                AND confidence < ?
                AND occurrence_count >= ?
            ''', (self.pattern_low_confidence_threshold, self.pattern_min_attempts_for_deprecation))
            stale_by_confidence = c.fetchone()[0]
            
            if not dry_run and stale_by_confidence > 0:
                c.execute(f'''
                    UPDATE {table} SET is_active = 0
                    WHERE is_active = 1 
                    AND confidence < ?
                    AND occurrence_count >= ?
                ''', (self.pattern_low_confidence_threshold, self.pattern_min_attempts_for_deprecation))
                deprecated += stale_by_confidence
        
        if not dry_run and deprecated > 0:
            conn.commit()
        
        total_stale = stale_by_gen + stale_by_confidence
        
        if verbose:
            print(f'   Stale by generation (>{self.pattern_staleness_generations} gens): {stale_by_gen:,}')
            print(f'   Low confidence (<{self.pattern_low_confidence_threshold} after {self.pattern_min_attempts_for_deprecation} attempts): {stale_by_confidence:,}')
            if dry_run and total_stale > 0:
                print(f'   Would deprecate: {total_stale:,} patterns')
            elif deprecated > 0:
                print(f'   Deprecated: {deprecated:,} patterns')
        
        return {'found': total_stale, 'deleted': 0, 'deprecated': deprecated if not dry_run else 0}

    def _apply_decay_scores(self, c, conn, dry_run, verbose, tables):
        """Update decay_score for telemetry tables using generation-based decay.

        Decay formula: max(0, 1 - (current_gen - last_observed_generation) / pattern_staleness_generations)
        Skips legacy rows (source_mode='LEGACY'). No deletions are performed.
        """
        updated_total = 0
        backfilled_total = 0

        try:
            c.execute('SELECT value FROM evolutionary_state WHERE key = "current_generation"')
            row = c.fetchone()
            current_gen = int(row[0]) if row else 0
        except Exception:
            current_gen = 0

        for table in tables:
            try:
                c.execute(f"PRAGMA table_info({table})")
                columns = {row[1] for row in c.fetchall()}
                if 'decay_score' not in columns or 'last_observed_generation' not in columns:
                    if verbose:
                        print(f'   Table {table} missing decay_score/last_observed_generation (skip)')
                    continue

                # Backfill missing last_observed_generation for non-legacy rows
                c.execute(
                    f'''
                    SELECT COUNT(*) FROM {table}
                    WHERE (source_mode IS NULL OR source_mode != 'LEGACY')
                    AND last_observed_generation = 0
                    '''
                )
                to_backfill = c.fetchone()[0]
                if not dry_run and to_backfill > 0:
                    c.execute(
                        f'''
                        UPDATE {table}
                        SET last_observed_generation = ?
                        WHERE (source_mode IS NULL OR source_mode != 'LEGACY')
                        AND last_observed_generation = 0
                        ''',
                        (current_gen,),
                    )
                    backfilled_total += to_backfill

                # Apply decay score for non-legacy rows with last_observed_generation > 0
                c.execute(
                    f'''
                    SELECT COUNT(*) FROM {table}
                    WHERE (source_mode IS NULL OR source_mode != 'LEGACY')
                    AND last_observed_generation > 0
                    '''
                )
                eligible = c.fetchone()[0]
                if not dry_run and eligible > 0:
                    c.execute(
                        f'''
                        UPDATE {table}
                        SET decay_score = CASE
                            WHEN (? - last_observed_generation) <= 0 THEN 1.0
                            WHEN (? - last_observed_generation) >= ? THEN 0.0
                            ELSE 1.0 - CAST((? - last_observed_generation) AS REAL) / ?
                        END
                        WHERE (source_mode IS NULL OR source_mode != 'LEGACY')
                        AND last_observed_generation > 0
                        ''',
                        (
                            current_gen,
                            current_gen,
                            self.pattern_staleness_generations,
                            current_gen,
                            self.pattern_staleness_generations,
                        ),
                    )
                    updated_total += eligible

                if dry_run and verbose:
                    print(f'   {table}: would backfill {to_backfill:,}, update decay for {eligible:,}')
            except Exception as exc:
                if verbose:
                    print(f'   Table {table} decay update skipped: {exc}')

        if not dry_run and (updated_total > 0 or backfilled_total > 0):
            conn.commit()

        if verbose:
            print(f'   Decay updated rows: {updated_total:,}, backfilled generations: {backfilled_total:,}')

        return {
            'found': updated_total + backfilled_total,
            'updated': updated_total,
            'backfilled': backfilled_total,
            'deleted': 0,
        }
    
    def verify_critical_data(self, verbose=True):
        """Verify that critical data is preserved."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Core winning sequences (CRITICAL)
        c.execute('SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1')
        sequences = c.fetchone()[0]
        
        # Active agents
        c.execute('SELECT COUNT(*) FROM agents WHERE is_active = 1')
        agents = c.fetchone()[0]
        
        # Positive-score games
        c.execute('SELECT COUNT(*) FROM game_results WHERE final_score > 0')
        good_games = c.fetchone()[0]
        
        # Session 23: Aggregated knowledge tables (PRESERVED, not deleted)
        aggregated_knowledge = {}
        
        # Interaction triggers (causal patterns)
        try:
            c.execute('SELECT COUNT(*) FROM interaction_triggers')
            aggregated_knowledge['interaction_triggers'] = c.fetchone()[0]
        except:
            aggregated_knowledge['interaction_triggers'] = 0
        
        # Trigger sequences (winning trigger orderings)
        try:
            c.execute('SELECT COUNT(*) FROM trigger_sequences')
            aggregated_knowledge['trigger_sequences'] = c.fetchone()[0]
        except:
            aggregated_knowledge['trigger_sequences'] = 0
        
        # Collision effects
        try:
            c.execute('SELECT COUNT(*) FROM collision_effects')
            aggregated_knowledge['collision_effects'] = c.fetchone()[0]
        except:
            aggregated_knowledge['collision_effects'] = 0
        
        # Selectability conditions
        try:
            c.execute('SELECT COUNT(*) FROM selectability_conditions')
            aggregated_knowledge['selectability_conditions'] = c.fetchone()[0]
        except:
            aggregated_knowledge['selectability_conditions'] = 0
        
        # Session 25: Perceptual primitives aggregated knowledge
        perceptual_knowledge = {}
        
        # Self-object identity mappings
        try:
            c.execute('SELECT COUNT(*) FROM self_object_identity')
            perceptual_knowledge['self_object_identity'] = c.fetchone()[0]
        except:
            perceptual_knowledge['self_object_identity'] = 0
        
        # Control transfer patterns
        try:
            c.execute('SELECT COUNT(*) FROM control_transfer_patterns')
            perceptual_knowledge['control_transfer_patterns'] = c.fetchone()[0]
        except:
            perceptual_knowledge['control_transfer_patterns'] = 0
        
        # Valence associations (positive/negative outcomes)
        try:
            c.execute('SELECT COUNT(*) FROM valence_associations')
            perceptual_knowledge['valence_associations'] = c.fetchone()[0]
        except:
            perceptual_knowledge['valence_associations'] = 0
        
        # Region classifications
        try:
            c.execute('SELECT COUNT(*) FROM grid_region_classification')
            perceptual_knowledge['grid_region_classification'] = c.fetchone()[0]
        except:
            perceptual_knowledge['grid_region_classification'] = 0
        
        # Goal state inferences
        try:
            c.execute('SELECT COUNT(*) FROM inferred_goal_states')
            perceptual_knowledge['inferred_goal_states'] = c.fetchone()[0]
        except:
            perceptual_knowledge['inferred_goal_states'] = 0
        
        conn.close()
        
        if verbose:
            print('\nCritical Data Preserved:')
            print(f'  Active sequences: {sequences:,} [OK]')
            print(f'  Active agents: {agents:,} [OK]')
            print(f'  Positive-score games: {good_games:,} [OK]')
            print('\nAggregated Knowledge (PERMANENT):')
            print(f'  Interaction triggers: {aggregated_knowledge["interaction_triggers"]:,}')
            print(f'  Trigger sequences: {aggregated_knowledge["trigger_sequences"]:,}')
            print(f'  Collision effects: {aggregated_knowledge["collision_effects"]:,}')
            print(f'  Selectability conditions: {aggregated_knowledge["selectability_conditions"]:,}')
            print('\nPerceptual Primitives Knowledge (Session 25):')
            print(f'  Self-object identity: {perceptual_knowledge["self_object_identity"]:,}')
            print(f'  Control transfer patterns: {perceptual_knowledge["control_transfer_patterns"]:,}')
            print(f'  Valence associations: {perceptual_knowledge["valence_associations"]:,}')
            print(f'  Grid region classifications: {perceptual_knowledge["grid_region_classification"]:,}')
            print(f'  Inferred goal states: {perceptual_knowledge["inferred_goal_states"]:,}')
        
        return {
            'sequences': sequences,
            'agents': agents,
            'good_games': good_games,
            'aggregated_knowledge': aggregated_knowledge,
            'perceptual_knowledge': perceptual_knowledge
        }


def safe_cleanup(dry_run=True):
    """
    Standalone cleanup function for command-line use.
    """
    print('='*60)
    print('SAFE DATABASE CLEANUP')
    print('='*60)
    print(f'\nMode: {"DRY RUN (no changes)" if dry_run else "EXECUTE"}')
    
    cleaner = SafeDatabaseCleaner()
    results = cleaner.cleanup(dry_run=dry_run, verbose=True)
    
    print('\n' + '='*60)
    print('SUMMARY')
    print('='*60)
    
    if not dry_run:
        print(f'Total rows deleted: {results["total_deleted"]:,}')
    else:
        total_would_delete = sum(r.get('found', 0) for r in results['tables_cleaned'].values())
        print(f'Would delete: {total_would_delete:,} rows')
        print('DRY RUN - No changes made')
        print('To execute cleanup, run: python safe_cleanup.py --execute')
    
    print('\n' + '='*60)
    print('VERIFICATION')
    print('='*60)
    cleaner.verify_critical_data(verbose=True)
    
    return results['total_deleted']


if __name__ == '__main__':
    import sys
    execute = '--execute' in sys.argv
    safe_cleanup(dry_run=not execute)
