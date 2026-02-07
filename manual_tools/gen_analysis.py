"""Analyze generation results for knowledge transfer testing."""
import sqlite3
import sys

sys.dont_write_bytecode = True

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

# Current max generation
c.execute('SELECT MAX(generation) FROM game_results')
max_gen = c.fetchone()[0]
print(f'Current max generation: {max_gen}')

# Recent traces - transitions breakdown
c.execute("""SELECT initial_quadrant, final_quadrant, COUNT(*),
             AVG(iterations), AVG(final_confidence)
             FROM cognitive_routing_traces
             WHERE timestamp > datetime('now', '-2 days')
             GROUP BY initial_quadrant, final_quadrant
             ORDER BY COUNT(*) DESC
             LIMIT 20""")
rows = c.fetchall()
print('\nRecent transitions (last 2 days):')
for row in rows:
    avg_iter = round(row[3], 1) if row[3] else '?'
    avg_conf = round(row[4], 3) if row[4] else '?'
    print(f'  {row[0]} -> {row[1]}: count={row[2]}, avg_iters={avg_iter}, avg_conf={avg_conf}')

# Recent game results
c.execute("""SELECT generation, game_id, final_score, total_actions,
             level_completions, session_id
             FROM game_results WHERE generation >= ?
             ORDER BY generation""", (max(0, max_gen - 10),))
rows = c.fetchall()
print(f'\nRecent game results (gen {max(0, max_gen-10)}+):')
for row in rows:
    print(f'  Gen {row[0]}: game={row[1]}, score={row[2]}, actions={row[3]}, levels={row[4]}, agent={row[5]}')

# Check for any traces with generation info via timestamp correlation
c.execute("""SELECT t.initial_quadrant, t.final_quadrant, t.iterations,
             t.final_confidence, t.algorithm_used, t.game_id
             FROM cognitive_routing_traces t
             ORDER BY t.timestamp DESC LIMIT 20""")
rows = c.fetchall()
print('\nLast 20 traces:')
for row in rows:
    print(f'  {row[0]}->{row[1]}: iters={row[2]}, conf={row[3]}, algo={row[4]}, game={row[5]}')

# Check winning sequences
c.execute("SELECT COUNT(*) FROM winning_sequences")
ws = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM winning_sequences_full_game")
wsfg = c.fetchone()[0]
print(f'\nWinning sequences: partial={ws}, full_game={wsfg}')

# Agent knowledge - check if epistemic state persists
c.execute("""SELECT COUNT(*), AVG(final_score), AVG(total_actions)
             FROM game_results WHERE generation = ?""", (max_gen,))
row = c.fetchone()
print(f'\nLatest gen ({max_gen}): {row[0]} games, avg_score={row[1]}, avg_actions={row[2]}')

conn.close()
