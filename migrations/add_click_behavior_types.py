"""Migration: Add click behavior classification columns to object_selection_state."""
import sqlite3

conn = sqlite3.connect('core_data.db')

# Check current columns
cols = [c[1] for c in conn.execute('PRAGMA table_info(object_selection_state)').fetchall()]
print('Current columns:', cols)

# Add new columns if missing
new_cols = [
    ('click_behavior_type', "TEXT DEFAULT 'unknown'"),
    ('is_self_toggle', 'BOOLEAN DEFAULT FALSE'),
    ('is_trigger', 'BOOLEAN DEFAULT FALSE'),
    ('affects_objects', 'TEXT'),
    ('state_changes_observed', 'INTEGER DEFAULT 0'),
    ('movement_verified', 'BOOLEAN DEFAULT FALSE'),
    ('movement_test_count', 'INTEGER DEFAULT 0'),
]

for col_name, col_def in new_cols:
    if col_name not in cols:
        try:
            conn.execute(f'ALTER TABLE object_selection_state ADD COLUMN {col_name} {col_def}')
            print(f'  Added: {col_name}')
        except Exception as e:
            print(f'  Skip {col_name}: {e}')

conn.commit()
conn.close()
print('[OK] Schema updated')
