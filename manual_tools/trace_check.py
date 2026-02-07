"""Quick trace analysis to find gen 5013 traces."""
import sqlite3

c = sqlite3.connect('core_data.db').cursor()

# Check game_id variety in traces
c.execute('SELECT game_id, COUNT(*) FROM cognitive_routing_traces GROUP BY game_id')
print('Trace game_ids:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check trace time range
c.execute('SELECT MIN(timestamp), MAX(timestamp) FROM cognitive_routing_traces')
t = c.fetchone()
print(f'\nTrace time range: {t[0]} -> {t[1]}')

# Gen 5013 time range
c.execute('SELECT MIN(created_at), MAX(created_at) FROM game_results WHERE generation = 5013')
t = c.fetchone()
print(f'Gen 5013 game_results range: {t[0]} -> {t[1]}')

# Total traces
c.execute('SELECT COUNT(*) FROM cognitive_routing_traces')
print(f'Total traces: {c.fetchone()[0]}')

# Traces in gen5013 window (log showed 17:34-17:39)
c.execute("SELECT COUNT(*) FROM cognitive_routing_traces WHERE timestamp BETWEEN '2026-02-06T17:34:00' AND '2026-02-06T17:40:00'")
print(f'Traces in 17:34-17:40 window: {c.fetchone()[0]}')

# Check what the 6hr offset looks like
c.execute("SELECT COUNT(*) FROM cognitive_routing_traces WHERE timestamp BETWEEN '2026-02-06T23:34:00' AND '2026-02-06T23:40:00'")
print(f'Traces in 23:34-23:40 window: {c.fetchone()[0]}')

# Sample recent traces
c.execute('SELECT timestamp, game_id, initial_quadrant, final_quadrant, iterations FROM cognitive_routing_traces ORDER BY id DESC LIMIT 10')
print('\nLast 10 traces:')
for r in c.fetchall():
    print(f'  {r[0]} | {r[1]} | {r[2]}->{r[3]} | iters={r[4]}')
