"""
Emergency Sequence Cleanup
==========================
Cleans corrupted and bloated sequences from database.

Phase 0 of Implementation Plan.

Following Rule 2: Database-Only Storage
Following Rule 8: Test Before Commit
"""

import sys
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).parent / "core_data.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def backup_sequences_to_archive():
    """Archive sequences before deletion (per Rule 2 - keep in database)."""
    with get_connection() as conn:
        # Create archive table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archived_sequences (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_sequence_id TEXT,
                game_id TEXT,
                level_number INTEGER,
                total_actions INTEGER,
                archive_reason TEXT,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Archive table ready")


def get_pre_cleanup_stats():
    """Get stats before cleanup."""
    with get_connection() as conn:
        stats = {
            'total_sequences': conn.execute(
                "SELECT COUNT(*) FROM winning_sequences"
            ).fetchone()[0],
            
            'lp85_sequences': conn.execute(
                "SELECT COUNT(*) FROM winning_sequences WHERE game_id LIKE 'lp85%'"
            ).fetchone()[0],
            
            'sequences_by_game': dict(conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game, COUNT(*) as cnt
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()),
            
            'avg_actions_by_level': dict(conn.execute("""
                SELECT level_number, ROUND(AVG(total_actions), 0) as avg
                FROM winning_sequences
                GROUP BY level_number
            """).fetchall()),
        }
        
        # Get bloat stats
        bloat_query = conn.execute("""
            WITH level_mins AS (
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       level_number,
                       MIN(total_actions) as min_actions
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4), level_number
            )
            SELECT COUNT(*) as bloated_count,
                   MAX(CAST(s.total_actions AS FLOAT) / m.min_actions) as max_ratio
            FROM winning_sequences s
            JOIN level_mins m ON SUBSTR(s.game_id, 1, 4) = m.game_type 
                              AND s.level_number = m.level_number
            WHERE m.min_actions > 0
              AND CAST(s.total_actions AS FLOAT) / m.min_actions > 10
        """).fetchone()
        
        stats['bloated_count'] = bloat_query['bloated_count']
        stats['max_bloat_ratio'] = bloat_query['max_ratio']
        
        return stats


def archive_and_delete_lp85():
    """Archive and delete all lp85 sequences (21.5% validation = corrupt)."""
    with get_connection() as conn:
        # Archive first
        conn.execute("""
            INSERT INTO archived_sequences 
            (original_sequence_id, game_id, level_number, total_actions, archive_reason)
            SELECT sequence_id, game_id, level_number, total_actions, 
                   'lp85_corrupt_21.5pct_validation'
            FROM winning_sequences
            WHERE game_id LIKE 'lp85%'
        """)
        
        # Count before delete
        count = conn.execute(
            "SELECT COUNT(*) FROM winning_sequences WHERE game_id LIKE 'lp85%'"
        ).fetchone()[0]
        
        # Delete
        conn.execute("DELETE FROM winning_sequences WHERE game_id LIKE 'lp85%'")
        
        # Also clean validation attempts
        conn.execute(
            "DELETE FROM sequence_validation_attempts WHERE game_id LIKE 'lp85%'"
        )
        
        conn.commit()
        print(f"Archived and deleted {count} lp85 sequences")
        return count


def archive_and_delete_bloated():
    """Archive and delete sequences with >10x bloat ratio."""
    with get_connection() as conn:
        # Find bloated sequences
        bloated = conn.execute("""
            WITH level_mins AS (
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       level_number,
                       MIN(total_actions) as min_actions
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4), level_number
            )
            SELECT s.sequence_id, s.game_id, s.level_number, s.total_actions,
                   CAST(s.total_actions AS FLOAT) / m.min_actions as bloat_ratio
            FROM winning_sequences s
            JOIN level_mins m ON SUBSTR(s.game_id, 1, 4) = m.game_type 
                              AND s.level_number = m.level_number
            WHERE m.min_actions > 0
              AND CAST(s.total_actions AS FLOAT) / m.min_actions > 10
        """).fetchall()
        
        if not bloated:
            print("No bloated sequences found")
            return 0
        
        # Archive
        for seq in bloated:
            conn.execute("""
                INSERT INTO archived_sequences 
                (original_sequence_id, game_id, level_number, total_actions, archive_reason)
                VALUES (?, ?, ?, ?, ?)
            """, (
                seq['sequence_id'], 
                seq['game_id'], 
                seq['level_number'], 
                seq['total_actions'],
                f"bloated_{seq['bloat_ratio']:.1f}x"
            ))
        
        # Delete
        seq_ids = [s['sequence_id'] for s in bloated]
        placeholders = ','.join(['?' for _ in seq_ids])
        conn.execute(
            f"DELETE FROM winning_sequences WHERE sequence_id IN ({placeholders})",
            seq_ids
        )
        
        conn.commit()
        print(f"Archived and deleted {len(bloated)} bloated sequences")
        return len(bloated)


def get_post_cleanup_stats():
    """Get stats after cleanup."""
    return get_pre_cleanup_stats()


def run_cleanup():
    """Execute full cleanup."""
    print("=" * 60)
    print("EMERGENCY SEQUENCE CLEANUP")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Pre-cleanup stats
    print("PRE-CLEANUP STATS:")
    print("-" * 40)
    pre_stats = get_pre_cleanup_stats()
    print(f"  Total sequences: {pre_stats['total_sequences']}")
    print(f"  lp85 sequences: {pre_stats['lp85_sequences']}")
    print(f"  Bloated (>10x): {pre_stats['bloated_count']}")
    print(f"  Max bloat ratio: {pre_stats['max_bloat_ratio']:.1f}x")
    print(f"  Sequences by game: {pre_stats['sequences_by_game']}")
    print()
    
    # Create archive
    print("Creating archive table...")
    backup_sequences_to_archive()
    print()
    
    # Cleanup lp85
    print("STEP 1: Cleaning lp85 sequences...")
    lp85_deleted = archive_and_delete_lp85()
    print()
    
    # Cleanup bloated
    print("STEP 2: Cleaning bloated sequences...")
    bloated_deleted = archive_and_delete_bloated()
    print()
    
    # Post-cleanup stats
    print("POST-CLEANUP STATS:")
    print("-" * 40)
    post_stats = get_post_cleanup_stats()
    print(f"  Total sequences: {post_stats['total_sequences']}")
    print(f"  lp85 sequences: {post_stats['lp85_sequences']}")
    print(f"  Bloated (>10x): {post_stats['bloated_count']}")
    if post_stats['max_bloat_ratio']:
        print(f"  Max bloat ratio: {post_stats['max_bloat_ratio']:.1f}x")
    else:
        print(f"  Max bloat ratio: N/A (no bloated sequences)")
    print(f"  Sequences by game: {post_stats['sequences_by_game']}")
    print()
    
    # Summary
    print("=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"  lp85 sequences deleted: {lp85_deleted}")
    print(f"  Bloated sequences deleted: {bloated_deleted}")
    print(f"  Total deleted: {lp85_deleted + bloated_deleted}")
    print(f"  Remaining sequences: {post_stats['total_sequences']}")
    print()
    print("All deleted sequences archived to 'archived_sequences' table")
    print("Run 'python test_critical_systems.py' to verify improvements")
    print("=" * 60)
    
    return {
        'pre': pre_stats,
        'post': post_stats,
        'deleted': lp85_deleted + bloated_deleted
    }


if __name__ == "__main__":
    run_cleanup()
