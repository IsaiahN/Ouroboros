"""Check what selectable objects exist for sp80."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check object_selection_state for sp80
print("=== object_selection_state for sp80 ===")
r = conn.execute("SELECT * FROM object_selection_state WHERE game_type='sp80' ORDER BY level_number, object_color").fetchall()
print(f"SP80 selectable objects: {len(r)} rows")
for row in r[:20]:
    print(dict(row))

print("\n=== network_object_control_hypotheses for sp80 ===")
r2 = conn.execute("SELECT * FROM network_object_control_hypotheses WHERE game_type='sp80' ORDER BY level_number").fetchall()
print(f"SP80 control hypotheses: {len(r2)} rows")
for row in r2[:10]:
    print(dict(row))

conn.close()
