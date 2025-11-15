import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

seqs = db.execute_query('''
    SELECT game_id, level_number, total_score, total_actions, efficiency_score
    FROM winning_sequences
    WHERE is_active = 1
    ORDER BY level_number, total_score
''')

print("\nAll Active Sequences:")
print("="*100)
print(f"{'Game ID':25s} {'Level':>6s} {'Score':>6s} {'Actions':>8s} {'Efficiency':>10s}")
print("-"*100)

for s in seqs:
    print(f"{s['game_id']:25s} {s['level_number']:6d} {s['total_score']:6.1f} {s['total_actions']:8d} {s['efficiency_score']:10.4f}")

print(f"\nTotal: {len(seqs)} sequences")

db.close()
