"""Check game_id patterns in winning_sequences."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 100)
print("AS66 - Game IDs and Deactivation Analysis")
print("=" * 100)

c.execute("""
    SELECT game_id, game_type, level_number, is_active, flag_reason, sequence_id,
           success_rate_when_reused, times_referenced
    FROM winning_sequences
    WHERE game_type = 'as66'
    ORDER BY level_number, is_active DESC
    LIMIT 30
""")
rows = c.fetchall()

print(f"{'game_id':<25} | {'level':<5} | {'active':<6} | {'success':<7} | {'refs':<5} | flag_reason")
print("-" * 100)
for r in rows:
    game_id = r['game_id'][:24] if r['game_id'] else 'None'
    flag = (r['flag_reason'] or '')[:40]
    success = f"{r['success_rate_when_reused']*100:.0f}%" if r['success_rate_when_reused'] else 'N/A'
    refs = r['times_referenced'] or 0
    print(f"{game_id:<25} | L{r['level_number']:<4} | {r['is_active']:<6} | {success:<7} | {refs:<5} | {flag}")

print("\n" + "=" * 100)
print("LS20 - Game IDs and Deactivation Analysis")
print("=" * 100)

c.execute("""
    SELECT game_id, game_type, level_number, is_active, flag_reason, sequence_id,
           success_rate_when_reused, times_referenced
    FROM winning_sequences
    WHERE game_type = 'ls20'
    ORDER BY level_number, is_active DESC
    LIMIT 30
""")
rows = c.fetchall()

print(f"{'game_id':<25} | {'level':<5} | {'active':<6} | {'success':<7} | {'refs':<5} | flag_reason")
print("-" * 100)
for r in rows:
    game_id = r['game_id'][:24] if r['game_id'] else 'None'
    flag = (r['flag_reason'] or '')[:40]
    success = f"{r['success_rate_when_reused']*100:.0f}%" if r['success_rate_when_reused'] else 'N/A'
    refs = r['times_referenced'] or 0
    print(f"{game_id:<25} | L{r['level_number']:<4} | {r['is_active']:<6} | {success:<7} | {refs:<5} | {flag}")

# Check if there are ANY higher level sequences for ls20
print("\n" + "=" * 100)
print("LS20 - Level Distribution")
print("=" * 100)
c.execute("""
    SELECT level_number, COUNT(*) as cnt,
           SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
    FROM winning_sequences
    WHERE game_type = 'ls20'
    GROUP BY level_number
    ORDER BY level_number
""")
for r in c.fetchall():
    print(f"Level {r['level_number']}: {r['cnt']} total, {r['active']} active")

# Check deactivation reasons distribution
print("\n" + "=" * 100)
print("Deactivation Reason Distribution (all games)")
print("=" * 100)
c.execute("""
    SELECT flag_reason, COUNT(*) as cnt
    FROM winning_sequences
    WHERE is_active = 0 AND flag_reason IS NOT NULL
    GROUP BY flag_reason
    ORDER BY cnt DESC
    LIMIT 15
""")
for r in c.fetchall():
    print(f"{r['cnt']:>6} | {r['flag_reason']}")

conn.close()
