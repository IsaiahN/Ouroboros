import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*80)
print("[BACKFILL] Updating generation_discovered for existing sequences")
print("="*80)

# Get all winning sequences
sequences = db.execute_query("""
    SELECT sequence_id, agent_id, generation_discovered
    FROM winning_sequences
""")

print(f"\nFound {len(sequences)} winning sequences")

updated = 0
skipped = 0

for seq in sequences:
    sequence_id = seq['sequence_id']
    agent_id = seq['agent_id']
    current_gen = seq['generation_discovered']
    
    # If already has generation, skip
    if current_gen and current_gen > 0:
        skipped += 1
        continue
    
    # Get agent's generation
    if agent_id and agent_id != 'core_agent' and agent_id != 'unknown':
        agent_data = db.execute_query(
            "SELECT generation FROM agents WHERE agent_id = ?", (agent_id,)
        )
        
        if agent_data:
            generation = agent_data[0]['generation']
            
            db.execute_query("""
                UPDATE winning_sequences 
                SET generation_discovered = ? 
                WHERE sequence_id = ?
            """, (generation, sequence_id))
            
            updated += 1
            print(f"  Updated {sequence_id[:16]}: agent {agent_id[:8]} → Gen {generation}")
    else:
        # core_agent or unknown - leave as 0
        skipped += 1

print("\n" + "="*80)
print(f"[✓] Backfill complete:")
print(f"    Updated: {updated} sequences")
print(f"    Skipped: {skipped} sequences (already set or no agent)")
print("="*80 + "\n")
