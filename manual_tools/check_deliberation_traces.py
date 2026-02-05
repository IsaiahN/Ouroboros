"""
Check deliberation audit traces for decision analysis.

Run: python manual_tools/check_deliberation_traces.py [--game GAME_ID] [--limit N]
"""

import argparse
import json
import sqlite3
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Check deliberation traces')
    parser.add_argument('--game', help='Filter by game ID prefix')
    parser.add_argument('--limit', type=int, default=10, help='Number of records to show')
    parser.add_argument('--details', action='store_true', help='Show full alternatives')
    args = parser.parse_args()

    conn = sqlite3.connect('core_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deliberation_audit_log'")
    if not cursor.fetchone():
        print("[NO TABLE] deliberation_audit_log table doesn't exist yet.")
        print("This means the DeliberationAuditor hasn't been activated during gameplay.")
        conn.close()
        return

    # Count records
    cursor.execute("SELECT COUNT(*) FROM deliberation_audit_log")
    total = cursor.fetchone()[0]
    print(f"\n=== DELIBERATION AUDIT LOG ===")
    print(f"Total records: {total}")

    if total == 0:
        print("\n[EMPTY] No deliberation traces recorded.")
        print("The table exists but no decisions have been audited.")
        print("\nPossible reasons:")
        print("1. Using 'ladder' strategy (doesn't audit) vs 'weighted' strategy (audits)")
        print("2. Auditor disabled or database not connected")
        conn.close()
        return

    # Recent records
    query = """
        SELECT * FROM deliberation_audit_log
        ORDER BY timestamp DESC
    """
    if args.game:
        query = f"""
            SELECT * FROM deliberation_audit_log
            WHERE game_id LIKE '{args.game}%'
            ORDER BY timestamp DESC
        """

    cursor.execute(f"{query} LIMIT {args.limit}")
    rows = cursor.fetchall()

    print(f"\nShowing {len(rows)} most recent records" + (f" for game {args.game}*" if args.game else ""))
    print("-" * 80)

    for row in rows:
        print(f"\n[{row['timestamp']}] Game: {row['game_id'][:20]} | Type: {row['game_type']}")
        print(f"  Level {row['level_number']}, Action #{row['action_number']}")
        print(f"  CHOSE: {row['chosen_action']} (conf={row['chosen_confidence']:.2f}) via [{row['chosen_rung']}]")

        reason = row['chosen_reason'] or ''
        if len(reason) > 100:
            print(f"  Reason: {reason[:100]}...")
        else:
            print(f"  Reason: {reason}")

        outcome = row['outcome_type'] or 'unknown'
        score_change = row['score_change'] or 0
        print(f"  Outcome: {outcome} (score_change={score_change})")

        if args.details and row['alternatives']:
            try:
                alts = json.loads(row['alternatives'])
                if alts:
                    print(f"  ALTERNATIVES ({len(alts)}):")
                    for i, alt in enumerate(alts):
                        print(f"    {i+1}. {alt['action']} conf={alt['confidence']:.2f} via [{alt['rung']}]")
                        print(f"       {alt['reason'][:80]}..." if len(alt.get('reason', '')) > 80 else f"       {alt.get('reason', '')}")
            except json.JSONDecodeError:
                print(f"  Alternatives: (invalid JSON)")

    # Stats by rung
    print("\n" + "=" * 80)
    print("STATS BY WINNING RUNG:")
    cursor.execute("""
        SELECT chosen_rung, COUNT(*) as cnt, AVG(chosen_confidence) as avg_conf
        FROM deliberation_audit_log
        GROUP BY chosen_rung
        ORDER BY cnt DESC
        LIMIT 15
    """)
    for row in cursor.fetchall():
        print(f"  {row['chosen_rung']:40} | {row['cnt']:5} decisions | avg_conf={row['avg_conf']:.2f}")

    conn.close()


if __name__ == '__main__':
    main()
