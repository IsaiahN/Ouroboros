"""Check all game types for sequences that should be reactivated."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 110)
print("ANALYSIS: HIGH-VALUE SEQUENCES THAT WERE DEACTIVATED")
print("=" * 110)

# Find deactivated sequences with high success rates or many references
c.execute("""
    SELECT 
        game_type,
        level_number,
        sequence_id,
        COALESCE(success_rate_when_reused, 0) as success_rate,
        COALESCE(times_referenced, 0) as refs,
        total_actions,
        flag_reason,
        is_active
    FROM winning_sequences
    WHERE is_active = 0 
      AND (
          COALESCE(success_rate_when_reused, 0) >= 0.5  -- 50%+ success rate
          OR COALESCE(times_referenced, 0) >= 20        -- Used 20+ times
      )
    ORDER BY 
        game_type, 
        level_number,
        COALESCE(success_rate_when_reused, 0) DESC,
        COALESCE(times_referenced, 0) DESC
""")

high_value_deactivated = c.fetchall()

print(f"\nFound {len(high_value_deactivated)} HIGH-VALUE deactivated sequences:\n")
print(f"{'Game':<6} | {'Lvl':<3} | {'Success':<8} | {'Refs':<5} | {'Actions':<8} | Flag Reason")
print("-" * 110)

current_game_level = None
for seq in high_value_deactivated:
    key = (seq['game_type'], seq['level_number'])
    if key != current_game_level:
        if current_game_level:
            print()  # Blank line between game/levels
        current_game_level = key
    
    success = f"{seq['success_rate']*100:.0f}%" if seq['success_rate'] else "N/A"
    flag = (seq['flag_reason'] or 'None')[:50]
    print(f"{seq['game_type']:<6} | L{seq['level_number']:<2} | {success:<8} | {seq['refs']:<5} | {seq['total_actions']:<8} | {flag}")

# Check current active count per game/level
print("\n" + "=" * 110)
print("CURRENT ACTIVE SEQUENCE COUNT PER GAME/LEVEL")
print("=" * 110)

c.execute("""
    SELECT 
        game_type,
        level_number,
        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
        COUNT(*) as total,
        MAX(CASE WHEN is_active = 1 THEN success_rate_when_reused ELSE NULL END) as best_active_success,
        MAX(CASE WHEN is_active = 0 THEN success_rate_when_reused ELSE NULL END) as best_inactive_success
    FROM winning_sequences
    GROUP BY game_type, level_number
    ORDER BY game_type, level_number
""")

print(f"\n{'Game':<6} | {'Lvl':<3} | {'Active':<7} | {'Total':<6} | {'Best Active':<12} | {'Best Inactive':<13} | Status")
print("-" * 90)

for r in c.fetchall():
    active_success = f"{r['best_active_success']*100:.0f}%" if r['best_active_success'] else "N/A"
    inactive_success = f"{r['best_inactive_success']*100:.0f}%" if r['best_inactive_success'] else "N/A"
    
    # Flag if there's a better inactive sequence
    status = ""
    if r['best_inactive_success'] and r['best_active_success']:
        if r['best_inactive_success'] > r['best_active_success']:
            status = "BETTER INACTIVE EXISTS!"
    elif r['best_inactive_success'] and not r['best_active_success']:
        status = "NO ACTIVE, HAS INACTIVE"
    elif r['active'] == 0:
        status = "NO ACTIVE SEQUENCES"
        
    print(f"{r['game_type']:<6} | L{r['level_number']:<2} | {r['active']:<7} | {r['total']:<6} | {active_success:<12} | {inactive_success:<13} | {status}")

# Find cases where we should swap - inactive is better than active
print("\n" + "=" * 110)
print("SEQUENCES TO POTENTIALLY REACTIVATE (better than current active)")
print("=" * 110)

c.execute("""
    WITH active_best AS (
        SELECT game_type, level_number, 
               MAX(COALESCE(success_rate_when_reused, 0)) as best_success,
               MAX(COALESCE(times_referenced, 0)) as best_refs
        FROM winning_sequences
        WHERE is_active = 1
        GROUP BY game_type, level_number
    )
    SELECT 
        ws.game_type,
        ws.level_number,
        ws.sequence_id,
        COALESCE(ws.success_rate_when_reused, 0) as success_rate,
        COALESCE(ws.times_referenced, 0) as refs,
        ws.total_actions,
        ws.flag_reason,
        ab.best_success as current_best_success,
        ab.best_refs as current_best_refs
    FROM winning_sequences ws
    LEFT JOIN active_best ab ON ws.game_type = ab.game_type AND ws.level_number = ab.level_number
    WHERE ws.is_active = 0
      AND (
          -- Inactive has better success rate than current active
          COALESCE(ws.success_rate_when_reused, 0) > COALESCE(ab.best_success, 0)
          -- OR no active exists but this one has good metrics
          OR (ab.best_success IS NULL AND (
              COALESCE(ws.success_rate_when_reused, 0) >= 0.5 
              OR COALESCE(ws.times_referenced, 0) >= 10
          ))
      )
    ORDER BY 
        ws.game_type,
        ws.level_number,
        COALESCE(ws.success_rate_when_reused, 0) DESC
""")

to_reactivate = c.fetchall()
print(f"\nFound {len(to_reactivate)} sequences that could improve coverage:\n")

if to_reactivate:
    print(f"{'Game':<6} | {'Lvl':<3} | {'Its Success':<12} | {'Curr Best':<10} | {'Refs':<5} | Flag Reason")
    print("-" * 90)
    for seq in to_reactivate:
        success = f"{seq['success_rate']*100:.0f}%" if seq['success_rate'] else "N/A"
        curr = f"{seq['current_best_success']*100:.0f}%" if seq['current_best_success'] else "None"
        flag = (seq['flag_reason'] or 'None')[:40]
        print(f"{seq['game_type']:<6} | L{seq['level_number']:<2} | {success:<12} | {curr:<10} | {seq['refs']:<5} | {flag}")
else:
    print("No sequences found that would improve current active set.")

conn.close()
