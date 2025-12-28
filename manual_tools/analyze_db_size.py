#!/usr/bin/env python3
"""
Database Size Analysis Tool
Analyzes which tables and columns are consuming the most space.
"""
import sqlite3
import os

db_path = 'core_data.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print(f"Database: {db_path}")
print(f"File size: {os.path.getsize(db_path) / (1024**3):.2f} GB\n")

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in c.fetchall()]

print("="*80)
print("ESTIMATING TABLE SIZES (sampling first row per table)")
print("="*80)

results = []
for table in tables:
    try:
        c.execute(f'SELECT COUNT(*) FROM "{table}"')
        row_count = c.fetchone()[0]
        
        if row_count == 0:
            continue
            
        # Get one row to estimate size
        c.execute(f'SELECT * FROM "{table}" LIMIT 1')
        row = c.fetchone()
        if row:
            col_names = [d[0] for d in c.description]
            sample_size = sum(len(str(v)) if v else 0 for v in row)
            est_total_gb = sample_size * row_count / (1024**3)
            
            # Track large columns
            large_cols = []
            for col, val in zip(col_names, row):
                if val and len(str(val)) > 500:
                    large_cols.append((col, len(str(val))))
            
            results.append({
                'table': table,
                'rows': row_count,
                'sample_bytes': sample_size,
                'est_gb': est_total_gb,
                'large_cols': large_cols
            })
    except Exception as e:
        print(f"Error with {table}: {e}")

# Sort by estimated size
results.sort(key=lambda x: x['est_gb'], reverse=True)

print(f"\n{'Table':<45} {'Rows':>12} {'Sample':>10} {'Est. GB':>10}")
print("-" * 80)
for r in results[:30]:
    print(f"{r['table']:<45} {r['rows']:>12,} {r['sample_bytes']:>10,} {r['est_gb']:>10.2f}")
    for col, size in r['large_cols']:
        print(f"  -> {col}: {size:,} bytes per row")

# Summary
total_est = sum(r['est_gb'] for r in results)
print(f"\n{'TOTAL ESTIMATED':<45} {'':<12} {'':<10} {total_est:>10.2f} GB")

# Now check specific large-data columns more thoroughly
print("\n" + "="*80)
print("CHECKING SPECIFIC HIGH-VOLUME COLUMNS (SUM of actual data)")
print("="*80)

high_volume_checks = [
    ('action_traces', ['frame_before', 'frame_after', 'frame_changes', 'action_context']),
    ('winning_sequences', ['action_sequence', 'cumulative_actions', 'frame_context']),
    ('sensation_learning_events', ['state_context']),
    ('agent_discoveries', ['discovery_data']),
    ('game_results', ['session_context']),
    ('recombination_attempts', ['parent_sequences', 'result_sequence']),
    ('sequence_dependencies', ['dependency_data']),
]

for table, columns in high_volume_checks:
    try:
        c.execute(f'SELECT COUNT(*) FROM "{table}"')
        row_count = c.fetchone()[0]
        print(f"\n{table} ({row_count:,} rows):")
        
        for col in columns:
            try:
                # Use LIMIT to avoid long query times
                c.execute(f'SELECT AVG(LENGTH("{col}")) FROM (SELECT "{col}" FROM "{table}" LIMIT 10000)')
                avg_len = c.fetchone()[0]
                if avg_len:
                    est_mb = (avg_len * row_count) / (1024*1024)
                    est_gb = est_mb / 1024
                    print(f"  {col}: avg {avg_len:.0f} bytes x {row_count:,} = ~{est_gb:.2f} GB")
            except Exception as e:
                print(f"  {col}: Error - {e}")
    except Exception as e:
        print(f"{table}: Error - {e}")

conn.close()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
