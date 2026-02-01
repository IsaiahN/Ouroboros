"""Reactivate best sequences for games with missing or deactivated sequences."""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 100)
print("REACTIVATING BEST SEQUENCES FOR EACH GAME TYPE + LEVEL")
print("=" * 100)

# Find all game_type/level combinations with NO active sequences but HAVE inactive ones
c.execute("""
    SELECT
        game_type,
        level_number,
        COUNT(*) as total_seqs,
        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_seqs,
        MAX(success_rate_when_reused) as best_success,
        MAX(times_referenced) as max_refs
    FROM winning_sequences
    GROUP BY game_type, level_number
    HAVING active_seqs = 0 AND total_seqs > 0
    ORDER BY game_type, level_number
""")
needs_reactivation = c.fetchall()

print(f"\nFound {len(needs_reactivation)} game/level combos with NO active sequences:\n")

for combo in needs_reactivation:
    game_type = combo['game_type']
    level = combo['level_number']
    total = combo['total_seqs']
    best_success = combo['best_success']
    max_refs = combo['max_refs']

    print(f"\n{game_type} Level {level}: {total} inactive sequences (best success: {best_success}, max refs: {max_refs})")

    # Find the BEST sequence to reactivate
    # Priority: highest success_rate_when_reused, then most references, then fewest actions
    c.execute("""
        SELECT sequence_id, total_actions, total_score,
               COALESCE(success_rate_when_reused, 0) as success_rate,
               COALESCE(times_referenced, 0) as refs,
               flag_reason
        FROM winning_sequences
        WHERE game_type = ? AND level_number = ?
        ORDER BY
            COALESCE(success_rate_when_reused, 0) DESC,
            COALESCE(times_referenced, 0) DESC,
            total_actions ASC
        LIMIT 1
    """, (game_type, level))

    best = c.fetchone()
    if best:
        print(f"  -> Reactivating: {best['sequence_id'][:20]}... ({best['success_rate']*100:.0f}% success, {best['refs']} refs, {best['total_actions']} actions)")
        print(f"     Was deactivated because: {best['flag_reason']}")

        c.execute("""
            UPDATE winning_sequences
            SET is_active = 1,
                flag_reason = 'auto_reactivated_best_sequence'
            WHERE sequence_id = ?
        """, (best['sequence_id'],))

conn.commit()

# Summary
print("\n" + "=" * 100)
print("FINAL STATUS BY GAME TYPE")
print("=" * 100)

c.execute("""
    SELECT
        game_type,
        MAX(level_number) as max_level,
        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_seqs,
        COUNT(*) as total_seqs
    FROM winning_sequences
    GROUP BY game_type
    ORDER BY max_level DESC, game_type
""")

print(f"\n{'Game':<8} | {'Max Level':<10} | {'Active':<8} | {'Total'}")
print("-" * 50)
for r in c.fetchall():
    print(f"{r['game_type']:<8} | L{r['max_level']:<9} | {r['active_seqs']:<8} | {r['total_seqs']}")

# Check specifically for as66 and ls20
print("\n" + "=" * 100)
print("DETAILED STATUS FOR AS66 AND LS20")
print("=" * 100)

for game_type in ['as66', 'ls20']:
    print(f"\n{game_type.upper()}:")
    c.execute("""
        SELECT level_number,
               COUNT(*) as total,
               SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
               MAX(CASE WHEN is_active = 1 THEN success_rate_when_reused ELSE 0 END) as active_success
        FROM winning_sequences
        WHERE game_type = ?
        GROUP BY level_number
        ORDER BY level_number
    """, (game_type,))
    levels = c.fetchall()
    for lvl in levels:
        status = "OK" if lvl['active'] > 0 else "MISSING"
        success = f"{lvl['active_success']*100:.0f}%" if lvl['active_success'] else "N/A"
        print(f"  L{lvl['level_number']}: {lvl['active']} active / {lvl['total']} total [{status}] (success: {success})")

conn.close()
print("\nDone!")
