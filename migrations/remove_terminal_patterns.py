"""
Migration: Remove terminal_patterns table and migrate useful data to position_death_patterns

Background:
- Two separate death tracking systems were causing inconsistencies
- terminal_patterns: frame_hash based (required EXACT pixel match - rarely triggered)
- position_death_patterns: bucket-based fuzzy matching (8x8 pixel regions)

Decision: Consolidate to position_death_patterns ONLY because:
- Fuzzy position matching works even when frame pixels differ slightly
- Has survival_count for danger_score decay
- Position-bucket semantics are more intuitive ("near spawn point")

This migration:
1. Migrates unique death data from terminal_patterns -> position_death_patterns
2. Drops the terminal_patterns table
3. Drops the idx_terminal_patterns_lookup_v2 index
"""

import os
import sqlite3
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Execute the migration to remove terminal_patterns table."""

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_data.db')

    if not os.path.exists(db_path):
        print("[MIGRATE] Database not found, skipping migration")
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check if terminal_patterns table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terminal_patterns'")
        if not cursor.fetchone():
            print("[MIGRATE] terminal_patterns table doesn't exist, nothing to migrate")
            return True

        # Check if position_death_patterns exists (target table)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='position_death_patterns'")
        if not cursor.fetchone():
            print("[MIGRATE] position_death_patterns table doesn't exist, cannot migrate")
            print("[MIGRATE] Please run the system first to create the table, then re-run migration")
            return False

        # Get count of terminal_patterns records
        cursor.execute("SELECT COUNT(*) FROM terminal_patterns")
        tp_count = cursor.fetchone()[0]
        print(f"[MIGRATE] Found {tp_count} records in terminal_patterns")

        # Get count of position_death_patterns records before migration
        cursor.execute("SELECT COUNT(*) FROM position_death_patterns")
        pdp_count_before = cursor.fetchone()[0]
        print(f"[MIGRATE] Found {pdp_count_before} records in position_death_patterns")

        # Migrate useful data from terminal_patterns to position_death_patterns
        # We use bucket_size=8 (default) and compute bucket positions from frame_hash context
        # Since terminal_patterns doesn't have position info, we aggregate by game_type/level/action
        print("[MIGRATE] Migrating terminal_patterns data to position_death_patterns...")

        # First, aggregate terminal_patterns by game_type, level, fatal_action
        cursor.execute("""
            SELECT
                game_type,
                level_number,
                fatal_action,
                SUM(confirmed_lethal) as total_deaths,
                MAX(confidence) as max_confidence,
                MIN(created_at) as first_seen
            FROM terminal_patterns
            WHERE is_active = 1
            GROUP BY game_type, level_number, fatal_action
            HAVING total_deaths >= 3
        """)

        aggregated = cursor.fetchall()
        print(f"[MIGRATE] Found {len(aggregated)} unique (game_type, level, action) combinations with 3+ deaths")

        # For each aggregated entry, create a position_death_pattern at bucket (0,0)
        # This represents "level-wide" death knowledge (position unknown from frame_hash)
        migrated_count = 0
        for row in aggregated:
            import hashlib
            pattern_id = f"migrated_{row['game_type']}_{row['level_number']}_{row['fatal_action']}"
            pattern_id = hashlib.md5(pattern_id.encode()).hexdigest()[:16]

            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO position_death_patterns (
                        pattern_id,
                        game_type,
                        level_number,
                        bucket_x,
                        bucket_y,
                        bucket_size,
                        fatal_action,
                        death_count,
                        survival_count,
                        danger_score,
                        last_death_at,
                        discovered_at,
                        discovered_by_agent,
                        is_active
                    ) VALUES (?, ?, ?, 0, 0, 8, ?, ?, 0, ?, ?, ?, 'migration', 1)
                """, (
                    pattern_id,
                    row['game_type'],
                    row['level_number'],
                    row['fatal_action'],
                    row['total_deaths'],
                    min(0.95, 0.5 + row['total_deaths'] * 0.05),  # danger_score
                    row['first_seen'],
                    row['first_seen']
                ))

                if cursor.rowcount > 0:
                    migrated_count += 1
            except Exception as e:
                print(f"[MIGRATE] Warning: Could not migrate {row['game_type']} L{row['level_number']} A{row['fatal_action']}: {e}")

        print(f"[MIGRATE] Migrated {migrated_count} new patterns to position_death_patterns")

        # Now drop the terminal_patterns table
        print("[MIGRATE] Dropping terminal_patterns table...")
        cursor.execute("DROP TABLE IF EXISTS terminal_patterns")

        # Drop the index too (should be dropped with table, but be explicit)
        cursor.execute("DROP INDEX IF EXISTS idx_terminal_patterns_lookup_v2")

        conn.commit()

        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terminal_patterns'")
        if not cursor.fetchone():
            print("[MIGRATE] SUCCESS: terminal_patterns table removed")
        else:
            print("[MIGRATE] WARNING: terminal_patterns table still exists!")
            return False

        # Get final count
        cursor.execute("SELECT COUNT(*) FROM position_death_patterns")
        pdp_count_after = cursor.fetchone()[0]
        print(f"[MIGRATE] position_death_patterns now has {pdp_count_after} records (+{pdp_count_after - pdp_count_before})")

        print("[MIGRATE] Migration complete!")
        return True

    except Exception as e:
        print(f"[MIGRATE] Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
