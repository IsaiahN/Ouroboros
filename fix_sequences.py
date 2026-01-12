"""Reactivate the BEST sequence per game/level where current active is suboptimal."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 100)
print("REACTIVATING BEST SEQUENCES WHERE NEEDED")
print("=" * 100)

# For each game_type/level, ensure the BEST sequence is active
# Best = highest success_rate, then most refs, then fewest actions

c.execute("""
    SELECT DISTINCT game_type, level_number
    FROM winning_sequences
    ORDER BY game_type, level_number
""")
game_levels = c.fetchall()

changes_made = 0

for gl in game_levels:
    game_type = gl['game_type']
    level = gl['level_number']
    
    # Get the absolute best sequence for this game/level
    c.execute("""
        SELECT sequence_id, is_active,
               COALESCE(success_rate_when_reused, 0) as success_rate,
               COALESCE(times_referenced, 0) as refs,
               total_actions,
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
    if not best:
        continue
    
    # Get current active sequence
    c.execute("""
        SELECT sequence_id,
               COALESCE(success_rate_when_reused, 0) as success_rate,
               COALESCE(times_referenced, 0) as refs,
               total_actions
        FROM winning_sequences
        WHERE game_type = ? AND level_number = ? AND is_active = 1
        ORDER BY 
            COALESCE(success_rate_when_reused, 0) DESC,
            COALESCE(times_referenced, 0) DESC
        LIMIT 1
    """, (game_type, level))
    
    current_active = c.fetchone()
    
    # Check if we need to swap
    need_swap = False
    reason = ""
    
    if not current_active:
        # No active sequence - definitely activate best
        need_swap = True
        reason = "No active sequence exists"
    elif best['sequence_id'] != current_active['sequence_id']:
        # Different sequence is best - check if it's actually better
        if best['success_rate'] > current_active['success_rate']:
            need_swap = True
            reason = f"Better success rate: {best['success_rate']*100:.0f}% vs {current_active['success_rate']*100:.0f}%"
        elif best['success_rate'] == current_active['success_rate'] and best['refs'] > current_active['refs'] * 2:
            need_swap = True
            reason = f"Same success, much more refs: {best['refs']} vs {current_active['refs']}"
    
    if need_swap and best['is_active'] == 0:
        print(f"\n{game_type} L{level}: {reason}")
        print(f"  Deactivating current: {current_active['sequence_id'][:16] if current_active else 'None'}...")
        print(f"  Activating best: {best['sequence_id'][:16]}... ({best['success_rate']*100:.0f}% success, {best['refs']} refs)")
        
        # Deactivate current active (if any)
        if current_active:
            c.execute("""
                UPDATE winning_sequences
                SET is_active = 0, flag_reason = 'replaced_by_better'
                WHERE sequence_id = ?
            """, (current_active['sequence_id'],))
        
        # Activate the best
        c.execute("""
            UPDATE winning_sequences
            SET is_active = 1, flag_reason = 'reactivated_best_in_class'
            WHERE sequence_id = ?
        """, (best['sequence_id'],))
        
        changes_made += 1

conn.commit()

print(f"\n\nTotal changes made: {changes_made}")

# Final summary
print("\n" + "=" * 100)
print("FINAL STATUS - ACTIVE SEQUENCES PER GAME/LEVEL")
print("=" * 100)

c.execute("""
    SELECT 
        game_type,
        level_number,
        sequence_id,
        COALESCE(success_rate_when_reused, 0) as success_rate,
        COALESCE(times_referenced, 0) as refs,
        total_actions
    FROM winning_sequences
    WHERE is_active = 1
    ORDER BY game_type, level_number
""")

print(f"\n{'Game':<6} | {'Lvl':<3} | {'Success':<8} | {'Refs':<6} | {'Actions':<8} | Sequence ID")
print("-" * 80)
for r in c.fetchall():
    success = f"{r['success_rate']*100:.0f}%" if r['success_rate'] else "N/A"
    print(f"{r['game_type']:<6} | L{r['level_number']:<2} | {success:<8} | {r['refs']:<6} | {r['total_actions']:<8} | {r['sequence_id'][:20]}")

conn.close()
print("\nDone!")
