#!/usr/bin/env python3
"""
Intelligent Historical Data Cleanup System
==========================================

Implements generational garbage collection for sensation_learning_events and score_history.

PROBLEM:
1. sensation_learning_events: 4M+ events (773 MB) - ALL from Generation 0
   - Used for emotional learning (object→sensation mapping)
   - Once learned, individual events become redundant
   
2. score_history: 5.5M+ scores (787 MB) - From 816 sessions over 16 days
   - Tracks every score change during gameplay
   - Older sessions no longer needed once agents evolved

SOLUTION:
- Sensation events: Keep recent N generations, aggregate older data
- Score history: Keep recent sessions + active agent sessions, delete old

Rule 2 Compliance: All data in database, intelligent retention policy
Rule 10: Enhance existing system, don't replace
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HistoricalDataCleaner:
    """
    Intelligent cleanup for sensation_learning_events and score_history.
    
    Prevents database bloat while preserving critical learning data.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # Retention policies
        # INCREASED from 5 to 100 generations due to many bug fixes causing early forgetting
        # Sensation data is critical for learning - don't lose it during debugging phase
        self.sensation_retention_generations = 100  # Keep last 100 generations of raw events
        self.score_history_retention_days = 7  # Keep last 7 days of score history
        self.min_records_to_clean = 100000  # Only clean if >100k records to delete
        
    def analyze_sensation_events(self) -> dict:
        """Analyze sensation_learning_events table."""
        stats = {}
        
        # Total count by generation
        gen_counts = self.db.execute_query('''
            SELECT generation, COUNT(*) as cnt
            FROM sensation_learning_events
            GROUP BY generation
            ORDER BY generation DESC
        ''')
        stats['by_generation'] = {g['generation']: g['cnt'] for g in gen_counts} if gen_counts else {}
        
        # Total events
        total = self.db.execute_query('SELECT COUNT(*) as cnt FROM sensation_learning_events')
        stats['total_events'] = total[0]['cnt'] if total else 0
        
        # Current generation
        current_gen = self.db.execute_query('SELECT MAX(generation) as max_gen FROM sensation_learning_events')
        stats['current_generation'] = current_gen[0]['max_gen'] if current_gen and current_gen[0]['max_gen'] else 0
        
        # Cleanable events (older than retention period)
        if stats['current_generation'] >= self.sensation_retention_generations:
            cutoff_gen = stats['current_generation'] - self.sensation_retention_generations
            cleanable = self.db.execute_query('''
                SELECT COUNT(*) as cnt
                FROM sensation_learning_events
                WHERE generation < ?
            ''', (cutoff_gen,))
            stats['cleanable_events'] = cleanable[0]['cnt'] if cleanable else 0
        else:
            stats['cleanable_events'] = 0
            
        return stats
    
    def analyze_score_history(self) -> dict:
        """Analyze score_history table."""
        stats = {}
        
        # Total scores
        total = self.db.execute_query('SELECT COUNT(*) as cnt FROM score_history')
        stats['total_scores'] = total[0]['cnt'] if total else 0
        
        # Date range
        date_range = self.db.execute_query('''
            SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest
            FROM score_history
        ''')
        if date_range:
            stats['oldest_timestamp'] = date_range[0]['oldest']
            stats['newest_timestamp'] = date_range[0]['newest']
        
        # Session count
        sessions = self.db.execute_query('SELECT COUNT(DISTINCT session_id) as cnt FROM score_history')
        stats['total_sessions'] = sessions[0]['cnt'] if sessions else 0
        
        # Cleanable scores (older than retention period)
        cutoff_date = (datetime.now() - timedelta(days=self.score_history_retention_days)).isoformat()
        cleanable = self.db.execute_query('''
            SELECT COUNT(*) as cnt
            FROM score_history
            WHERE timestamp < ?
        ''', (cutoff_date,))
        stats['cleanable_scores'] = cleanable[0]['cnt'] if cleanable else 0
        
        return stats
    
    def clean_sensation_events(self, dry_run=True) -> dict:
        """
        Clean old sensation learning events.
        
        Strategy: Keep last N generations, delete older.
        These are individual learning events - once sensation mapping is learned
        and stored in agent epigenetics, raw events are no longer needed.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dict with cleanup stats
        """
        stats = self.analyze_sensation_events()
        
        if stats['cleanable_events'] < self.min_records_to_clean:
            return {
                'action': 'skipped',
                'reason': f"Only {stats['cleanable_events']} cleanable events (min {self.min_records_to_clean})",
                **stats
            }
        
        cutoff_gen = stats['current_generation'] - self.sensation_retention_generations
        
        if dry_run:
            return {
                'action': 'dry_run',
                'would_delete': stats['cleanable_events'],
                'cutoff_generation': cutoff_gen,
                'retention_generations': self.sensation_retention_generations,
                **stats
            }
        
        # Execute cleanup
        conn = self.db._get_connection()
        cursor = conn.execute('''
            DELETE FROM sensation_learning_events
            WHERE generation < ?
        ''', (cutoff_gen,))
        deleted = cursor.rowcount
        conn.commit()
        
        logger.info(f"Deleted {deleted} sensation learning events older than generation {cutoff_gen}")
        
        return {
            'action': 'cleaned',
            'deleted': deleted,
            'cutoff_generation': cutoff_gen,
            **stats
        }
    
    def clean_score_history(self, dry_run=True) -> dict:
        """
        Clean old score history.
        
        Strategy: Keep last N days of score history.
        Score history is per-session tracking - once session complete and
        performance recorded in agent_arc_performance, raw scores not needed.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dict with cleanup stats
        """
        stats = self.analyze_score_history()
        
        if stats['cleanable_scores'] < self.min_records_to_clean:
            return {
                'action': 'skipped',
                'reason': f"Only {stats['cleanable_scores']} cleanable scores (min {self.min_records_to_clean})",
                **stats
            }
        
        cutoff_date = (datetime.now() - timedelta(days=self.score_history_retention_days)).isoformat()
        
        if dry_run:
            return {
                'action': 'dry_run',
                'would_delete': stats['cleanable_scores'],
                'cutoff_date': cutoff_date,
                'retention_days': self.score_history_retention_days,
                **stats
            }
        
        # Execute cleanup
        conn = self.db._get_connection()
        cursor = conn.execute('''
            DELETE FROM score_history
            WHERE timestamp < ?
        ''', (cutoff_date,))
        deleted = cursor.rowcount
        conn.commit()
        
        logger.info(f"Deleted {deleted} score history records older than {cutoff_date}")
        
        return {
            'action': 'cleaned',
            'deleted': deleted,
            'cutoff_date': cutoff_date,
            **stats
        }
    
    def cleanup_all(self, dry_run=True) -> dict:
        """
        Run all cleanup operations.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dict with all cleanup stats
        """
        results = {
            'sensation_events': self.clean_sensation_events(dry_run=dry_run),
            'score_history': self.clean_score_history(dry_run=dry_run),
            'dry_run': dry_run
        }
        
        if not dry_run:
            # Vacuum database after cleanup
            conn = self.db._get_connection()
            conn.execute('VACUUM')
            conn.commit()
            results['vacuumed'] = True
        
        return results


if __name__ == "__main__":
    import sys
    
    db = DatabaseInterface()
    cleaner = HistoricalDataCleaner(db)
    
    # Check if --execute flag present
    execute = '--execute' in sys.argv
    
    print("="*80)
    print("HISTORICAL DATA CLEANUP ANALYSIS")
    print("="*80)
    
    results = cleaner.cleanup_all(dry_run=not execute)
    
    print("\nSENSATION LEARNING EVENTS:")
    print(f"  Total events: {results['sensation_events'].get('total_events', 0):,}")
    print(f"  Current generation: {results['sensation_events'].get('current_generation', 0)}")
    print(f"  Retention: {cleaner.sensation_retention_generations} generations")
    
    if results['sensation_events']['action'] == 'dry_run':
        print(f"  Would delete: {results['sensation_events']['would_delete']:,} events")
    elif results['sensation_events']['action'] == 'cleaned':
        print(f"  Deleted: {results['sensation_events']['deleted']:,} events ✓")
    else:
        print(f"  {results['sensation_events'].get('reason', 'No action needed')}")
    
    print("\nSCORE HISTORY:")
    print(f"  Total scores: {results['score_history'].get('total_scores', 0):,}")
    print(f"  Total sessions: {results['score_history'].get('total_sessions', 0)}")
    print(f"  Retention: {cleaner.score_history_retention_days} days")
    print(f"  Date range: {results['score_history'].get('oldest_timestamp', 'N/A')} to {results['score_history'].get('newest_timestamp', 'N/A')}")
    
    if results['score_history']['action'] == 'dry_run':
        print(f"  Would delete: {results['score_history']['would_delete']:,} scores")
    elif results['score_history']['action'] == 'cleaned':
        print(f"  Deleted: {results['score_history']['deleted']:,} scores ✓")
    else:
        print(f"  {results['score_history'].get('reason', 'No action needed')}")
    
    if execute:
        print("\n✓ Cleanup executed and database vacuumed")
    else:
        print("\n⚠ DRY RUN - No data deleted. Use --execute to perform cleanup")
    
    print("="*80)
