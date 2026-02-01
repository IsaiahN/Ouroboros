"""
Mastery System Migration Script
================================

Purpose: Initialize all existing sequences at NOVICE tier (hard reset).

This is a ONE-TIME migration that:
1. Creates mastery tables if they don't exist
2. Initializes ALL game-levels with existing sequences at NOVICE tier
3. Preserves existing sequences (they're just blocked from replay until mastery earned)

PHILOSOPHY: No grandfathering. If we're not willing to accept short-term cost,
we're not serious about fixing the cargo-cult problem. The network must
genuinely demonstrate understanding.

EXPECTED TIMELINE after migration:
- Generations 1-5: Win rate drops 30-50% (sequences can't be used)
- Generations 5-10: Some levels reach Apprentice (studying begins)
- Generations 10-20: First levels reach Practitioner (replay unlocked)
- Generations 20-30: Recovery to pre-migration performance
- Generations 30+: EXCEEDING pre-migration (genuine understanding)

Usage:
    python migrate_mastery_system.py          # Dry run (shows what would happen)
    python migrate_mastery_system.py --execute # Actually run the migration
    python migrate_mastery_system.py --status  # Check current status

Following Rule 1: PYTHONDONTWRITEBYTECODE=1
Following Rule 2: All data stored in database
Following Rule 11: No Unicode emojis
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1

import argparse
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description='Mastery System Migration - Initialize all sequences at NOVICE tier'
    )
    parser.add_argument('--execute', action='store_true',
                        help='Actually execute the migration (default is dry run)')
    parser.add_argument('--status', action='store_true',
                        help='Show current mastery system status')
    parser.add_argument('--force', action='store_true',
                        help='Force migration even if mastery data exists')

    args = parser.parse_args()

    # Import database interface
    try:
        from database_interface import DatabaseInterface
    except ImportError:
        print("[ERROR] Could not import DatabaseInterface - run from project root")
        sys.exit(1)

    db = DatabaseInterface()

    if args.status:
        show_status(db)
        return

    if args.execute:
        execute_migration(db, force=args.force)
    else:
        dry_run(db)


def show_status(db):
    """Show current mastery system status."""
    print("\n=== MASTERY SYSTEM STATUS ===\n")

    # Check if mastery tables exist
    tables = db.execute_query("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('level_mastery', 'ablation_test_results', 'sequence_improvements')
    """)

    existing_tables = [t['name'] for t in tables] if tables else []
    print(f"Tables: {', '.join(existing_tables) if existing_tables else 'NONE (not migrated yet)'}")

    if 'level_mastery' not in existing_tables:
        print("\n[INFO] Mastery system NOT initialized. Run migration with --execute")

        # Show what would be migrated
        sequences = db.execute_query("""
            SELECT COUNT(DISTINCT SUBSTR(game_id, 1, INSTR(game_id, '-') - 1) || '_' || level_number) as count
            FROM winning_sequences
            WHERE is_active = 1 AND game_id LIKE '%-%'
        """)
        if sequences and sequences[0]['count']:
            print(f"\n{sequences[0]['count']} game-levels would be initialized at NOVICE")
        return

    # Get mastery distribution
    try:
        from mastery_system import MasterySystem
        mastery = MasterySystem(db)
        report = mastery.get_mastery_report()

        print(f"\nTotal game-levels tracked: {report['total_levels']}")
        print("\nTier Distribution:")

        for tier in ['master', 'expert', 'practitioner', 'apprentice', 'novice']:
            count = report['tier_distribution'].get(tier, 0)
            avg = report['avg_scores'].get(tier, 0)
            if count > 0:
                pct = count / max(report['total_levels'], 1) * 100
                print(f"  {tier.upper():12} {count:4} levels ({pct:5.1f}%) avg={avg:.1f}")

        # Show ablation stats
        ablation_stats = db.execute_query("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN test_passed THEN 1 ELSE 0 END) as passed
            FROM ablation_test_results
        """)
        if ablation_stats and ablation_stats[0]['total']:
            total = ablation_stats[0]['total']
            passed = ablation_stats[0]['passed'] or 0
            rate = passed / total * 100 if total > 0 else 0
            print(f"\nAblation Tests: {total} total, {passed} passed ({rate:.1f}%)")

    except Exception as e:
        print(f"\n[ERROR] Could not get mastery report: {e}")


def dry_run(db):
    """Show what migration would do without executing."""
    print("\n=== MASTERY MIGRATION DRY RUN ===\n")
    print("This is a DRY RUN - no changes will be made.\n")

    # Count game-levels to migrate
    game_levels = db.execute_query("""
        SELECT DISTINCT
            SUBSTR(game_id, 1, INSTR(game_id, '-') - 1) as game_type,
            level_number,
            COUNT(*) as sequence_count
        FROM winning_sequences
        WHERE is_active = 1 AND game_id LIKE '%-%'
        GROUP BY SUBSTR(game_id, 1, INSTR(game_id, '-') - 1), level_number
        ORDER BY game_type, level_number
    """)

    if not game_levels:
        print("[INFO] No sequences found to migrate.")
        return

    # Group by game type
    by_game = {}
    for gl in game_levels:
        gt = gl['game_type']
        if gt not in by_game:
            by_game[gt] = []
        by_game[gt].append((gl['level_number'], gl['sequence_count']))

    print(f"Would initialize {len(game_levels)} game-levels at NOVICE tier:\n")

    for game_type in sorted(by_game.keys())[:20]:  # Show first 20 games
        levels = by_game[game_type]
        level_str = ', '.join(f"L{l[0]}({l[1]}seq)" for l in levels[:5])
        if len(levels) > 5:
            level_str += f", ... ({len(levels)} total levels)"
        print(f"  {game_type}: {level_str}")

    if len(by_game) > 20:
        print(f"  ... and {len(by_game) - 20} more game types")

    total_sequences = sum(gl['sequence_count'] for gl in game_levels)
    print(f"\nTotal: {len(game_levels)} game-levels, {total_sequences} sequences")
    print("\n[WARNING] All sequences will be BLOCKED from replay until mastery is earned!")
    print("\nTo execute migration, run: python migrate_mastery_system.py --execute")


def execute_migration(db, force=False):
    """Execute the mastery migration."""
    print("\n=== MASTERY MIGRATION ===\n")

    # Check if already migrated
    existing = db.execute_query("""
        SELECT COUNT(*) as count FROM sqlite_master
        WHERE type='table' AND name='level_mastery'
    """)

    if existing and existing[0]['count'] > 0 and not force:
        existing_count = db.execute_query("SELECT COUNT(*) as count FROM level_mastery")
        if existing_count and existing_count[0]['count'] > 0:
            print(f"[WARN] Mastery system already has {existing_count[0]['count']} entries.")
            print("Use --force to re-initialize all entries to NOVICE.")
            return

    print("Initializing mastery system with HARD RESET (all sequences at NOVICE)...\n")

    # Import and initialize mastery system
    try:
        from mastery_system import MasterySystem
        mastery = MasterySystem(db)

        # Run the migration
        count = mastery.initialize_migration()

        print(f"\n[OK] Migration complete!")
        print(f"     Initialized {count} game-levels at NOVICE tier")
        print(f"\n[INFO] Existing sequences are PRESERVED but replay is BLOCKED")
        print(f"       until agents demonstrate understanding through:")
        print(f"       - Diversity (multiple different winning strategies)")
        print(f"       - Robustness (winning despite skipped actions)")
        print(f"       - Consistency (sequences work for multiple agents)")
        print(f"       - Efficiency (sequences improving over time)")

        print(f"\n[EXPECT] Temporary regression for 5-10 generations")
        print(f"         Recovery by generation 20-30")
        print(f"         EXCEEDING pre-migration by generation 50+")

        # Show current status
        report = mastery.get_mastery_report()
        print(f"\nCurrent status: {report['total_levels']} levels, all at NOVICE")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
