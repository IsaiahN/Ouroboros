"""Deep dive into gen 5013 KK->UK regressions."""
import sqlite3

c = sqlite3.connect('core_data.db').cursor()
T1 = '2026-02-06T17:34:00'
T2 = '2026-02-06T17:40:00'

# Check quadrant_transitions column for KK->UK traces
c.execute("""SELECT quadrant_transitions, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    GROUP BY quadrant_transitions ORDER BY cnt DESC LIMIT 10""", (T1, T2))
print('Quadrant transition chains:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check rumsfeld_assessment
c.execute("""SELECT rumsfeld_assessment, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    GROUP BY rumsfeld_assessment ORDER BY cnt DESC LIMIT 10""", (T1, T2))
print('\nRumsfeld assessments:')
for r in c.fetchall():
    val = r[0][:120] if r[0] else 'NULL'
    print(f'  {val}: {r[1]}')

# Check outcome_reason
c.execute("""SELECT outcome_reason, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    GROUP BY outcome_reason ORDER BY cnt DESC LIMIT 10""", (T1, T2))
print('\nOutcome reasons:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check outcome_score distribution
c.execute("""SELECT outcome_score, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    GROUP BY outcome_score ORDER BY cnt DESC LIMIT 10""", (T1, T2))
print('\nOutcome scores:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check final_action distribution
c.execute("""SELECT final_action, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    GROUP BY final_action ORDER BY cnt DESC LIMIT 10""", (T1, T2))
print('\nFinal actions:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Sample a full trace to understand the path
c.execute("""SELECT path, algorithms_history, quadrant_transitions,
    initial_quadrant, final_quadrant, iterations, final_confidence
    FROM cognitive_routing_traces
    WHERE timestamp >= ? AND timestamp <= ?
    AND initial_quadrant = 'KK'
    LIMIT 3""", (T1, T2))
print('\nSample KK->UK traces (full detail):')
for i, r in enumerate(c.fetchall()):
    print(f'\n  Trace {i+1}:')
    print(f'    path: {r[0][:200] if r[0] else "NULL"}')
    print(f'    algorithms_history: {r[1][:200] if r[1] else "NULL"}')
    print(f'    quadrant_transitions: {r[2][:200] if r[2] else "NULL"}')
    print(f'    {r[3]}->{r[4]}, iters={r[5]}, conf={r[6]}')
