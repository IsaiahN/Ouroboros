"""Analyze decision system behavior."""
import sqlite3

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

print("=== TOP DECISION REASONS ===")
c.execute("""
    SELECT chosen_reason, COUNT(*) as cnt
    FROM action_proposals_log
    GROUP BY chosen_reason
    ORDER BY cnt DESC LIMIT 30
""")
for r in c.fetchall():
    reason = r[0][:80] if r[0] else "NULL"
    print(f"  {r[1]:6d}x  {reason}")

print("\n=== WHAT'S BEING LOGGED VS WHAT'S RUNNING ===")
# Check if decision system is being invoked at all
c.execute("SELECT COUNT(*) FROM action_proposals_log")
total_proposals = c.fetchone()[0]
print(f"  Total action proposals logged: {total_proposals}")

c.execute("SELECT COUNT(*) FROM action_proposals_log WHERE chosen_action LIKE 'ACTION%'")
action_count = c.fetchone()[0]
print(f"  Proposals with ACTION result: {action_count}")

c.execute("SELECT COUNT(*) FROM action_proposals_log WHERE chosen_action = 'DECOMPOSITION_HINT'")
hint_count = c.fetchone()[0]
print(f"  DECOMPOSITION_HINT entries: {hint_count}")

print("\n=== SAMPLE DECISION FLOW (one attempt) ===")
c.execute("""
    SELECT attempt_id FROM action_proposals_log
    WHERE chosen_action LIKE 'ACTION%'
    LIMIT 1
""")
row = c.fetchone()
if row:
    attempt_id = row[0]
    print(f"  Attempt: {attempt_id}")
    c.execute("""
        SELECT step_idx, chosen_action, chosen_reason, role_compliance
        FROM action_proposals_log
        WHERE attempt_id = ?
        ORDER BY step_idx
        LIMIT 20
    """, (attempt_id,))
    for r in c.fetchall():
        reason = r[2][:50] if r[2] else "N/A"
        print(f"    Step {r[0]:3d}: {r[1]:15s} role={r[3]} reason={reason}")

print("\n=== CHECKING CONTEXT BEING PASSED ===")
c.execute("""
    SELECT available_actions, proposals FROM action_proposals_log
    WHERE available_actions IS NOT NULL
    LIMIT 3
""")
for r in c.fetchall():
    print(f"  Available: {r[0]}")
    if r[1]:
        print(f"  Proposals: {r[1][:200]}")
    print()

conn.close()
