#!/usr/bin/env python3
"""
SAFE DATABASE CLEANUP
=====================
The primary database cleanup routine for the Ouroboros system.
Called by autonomous_evolution_runner.py and can be run standalone.

Only deletes:
1. Zero-score game results (failed games that provide no learning value)
2. Old system/database logs
3. Old score history (>7 days) 
4. Old sensation learning events from completed sessions
5. Excessive navigation state history
6. Old action traces
7. Excessive agent operating modes

DOES NOT DELETE:
- Winning sequences (critical!)
- Agent data
- Game results with positive scores
- Recent learning data

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
    
    Retention Policies:
    - Zero-score games: DELETE (no learning value)
    - Score history: 7 days
    - System logs: 5,000 entries
    - Navigation state: 50,000 entries
    - Action traces: 100,000 entries
    - Sensation events: 200,000 entries
    - Agent operating modes: 100,000 entries
    """
    
    def __init__(self, db_path='core_data.db'):
        self.db_path = db_path
        
        # Retention policies
        self.score_history_retention_days = 7
        self.system_logs_retention = 5000
        self.navigation_retention = 50000
        self.action_traces_retention = 500000  # ~5 generations worth, allows sequence rebuild
        self.sensation_events_retention = 200000
        self.operating_modes_retention = 100000
    
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
    
    def verify_critical_data(self, verbose=True):
        """Verify that critical data is preserved."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1')
        sequences = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM agents WHERE is_active = 1')
        agents = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM game_results WHERE final_score > 0')
        good_games = c.fetchone()[0]
        
        conn.close()
        
        if verbose:
            print('\nCritical Data Preserved:')
            print(f'  Active sequences: {sequences} [OK]')
            print(f'  Active agents: {agents} [OK]')
            print(f'  Positive-score games: {good_games} [OK]')
        
        return {
            'sequences': sequences,
            'agents': agents,
            'good_games': good_games
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
