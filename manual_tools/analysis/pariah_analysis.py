#!/usr/bin/env python3
"""
Pariah Analysis Tool
====================
Analyzes pariah system effectiveness and potential analysis paralysis issues.
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
from pathlib import Path


def analyze_pariahs():
    db_path = Path(__file__).parent.parent / 'core_data.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("=" * 70)
    print("PARIAH SYSTEM ANALYSIS")
    print("=" * 70)

    # 1. Active pariahs count
    c.execute('SELECT COUNT(*) as cnt FROM pariahs WHERE is_active = 1')
    print(f"\nActive Pariahs: {c.fetchone()['cnt']}")

    # 2. Pariah details
    print("\n--- ACTIVE PARIAHS ---")
    c.execute('''
        SELECT pariah_id, pariah_name, source_game_id, toxicity, trigger_count,
               discovery_generation, last_triggered_generation, avoidance_success_rate
        FROM pariahs
        WHERE is_active = 1
        ORDER BY trigger_count DESC
        LIMIT 15
    ''')
    pariahs = c.fetchall()
    if pariahs:
        for p in pariahs:
            gen_diff = (p['last_triggered_generation'] or 0) - (p['discovery_generation'] or 0)
            print(f"  {p['pariah_name'][:30]:30} | Game: {(p['source_game_id'] or '?')[:8]:8} | "
                  f"Toxicity: {p['toxicity']:.2f} | Triggers: {p['trigger_count']} | "
                  f"Gen: {p['discovery_generation']} -> {p['last_triggered_generation']} (diff: {gen_diff})")
    else:
        print("  No active pariahs")

    # 3. Agent pariah awareness
    print("\n--- AGENT PARIAH AWARENESS ---")
    c.execute('SELECT COUNT(*) as cnt FROM agent_pariah_awareness WHERE is_active = 1')
    print(f"Total awareness records: {c.fetchone()['cnt']}")

    c.execute('''
        SELECT agent_id, COUNT(pariah_id) as pariah_count,
               AVG(awareness_level) as avg_awareness,
               AVG(avoidance_priority) as avg_priority
        FROM agent_pariah_awareness
        WHERE is_active = 1
        GROUP BY agent_id
        ORDER BY pariah_count DESC
        LIMIT 10
    ''')
    awareness = c.fetchall()
    if awareness:
        for a in awareness:
            print(f"  {a['agent_id'][:25]:25} | Pariahs: {a['pariah_count']} | "
                  f"Awareness: {a['avg_awareness']:.2f} | Priority: {a['avg_priority']:.2f}")
    else:
        print("  No agent pariah awareness records")

    # 4. lp85 game analysis
    print("\n--- lp85 GAME LEVEL DISTRIBUTION ---")
    c.execute('''
        SELECT level_completions, COUNT(*) as count, AVG(final_score) as avg_score
        FROM game_results
        WHERE game_id LIKE 'lp85%'
        GROUP BY level_completions
        ORDER BY level_completions
    ''')
    lp85_levels = c.fetchall()
    if lp85_levels:
        total = sum(r['count'] for r in lp85_levels)
        for r in lp85_levels:
            pct = (r['count'] / total * 100) if total > 0 else 0
            print(f"  Level {r['level_completions']}: {r['count']} games ({pct:.1f}%) | Avg Score: {r['avg_score']:.2f}")
    else:
        print("  No lp85 games found")

    # 5. Frozen state / dead end failures
    print("\n--- FROZEN STATE FAILURES ---")
    try:
        c.execute('''
            SELECT game_id, level_number, hypothesis_text, generation
            FROM failure_hypotheses
            WHERE hypothesis_text LIKE '%frozen%' OR hypothesis_text LIKE '%dead end%'
            ORDER BY generation DESC
            LIMIT 10
        ''')
        frozen = c.fetchall()
        if frozen:
            for f in frozen:
                print(f"  {f['game_id'][:20]:20} L{f['level_number']} | Gen {f['generation']} | {f['hypothesis_text'][:50]}")
        else:
            print("  No frozen state failures recorded")
    except sqlite3.OperationalError:
        print("  Table failure_hypotheses not found - checking system_logs instead")
        try:
            c.execute('''
                SELECT message, COUNT(*) as cnt
                FROM system_logs
                WHERE message LIKE '%frozen%' OR message LIKE '%dead end%'
                GROUP BY SUBSTR(message, 1, 80)
                ORDER BY cnt DESC
                LIMIT 10
            ''')
            logs = c.fetchall()
            if logs:
                for l in logs:
                    print(f"  ({l['cnt']}x) {l['message'][:70]}")
            else:
                print("  No frozen state logs found")
        except sqlite3.OperationalError:
            print("  No relevant logs table found")

    # 6. Check for pariah decay mechanism
    print("\n--- PARIAH DECAY CHECK ---")
    c.execute('''
        SELECT discovery_generation, last_triggered_generation,
               (SELECT MAX(generation) FROM agents WHERE is_active = 1) as current_gen
        FROM pariahs
        WHERE is_active = 1
    ''')
    decay_check = c.fetchall()
    if decay_check:
        current_gen = decay_check[0]['current_gen'] or 0
        old_pariahs = 0
        for p in decay_check:
            last_trig = p['last_triggered_generation'] or p['discovery_generation'] or 0
            age = current_gen - last_trig
            if age > 50:  # Pariahs older than 50 generations without trigger
                old_pariahs += 1
        print(f"  Current generation: {current_gen}")
        print(f"  Pariahs not triggered in 50+ generations: {old_pariahs}")
        if old_pariahs > 0:
            print("  [WARNING] Old pariahs may be causing paralysis - consider decay")

    # 7. Role-based pariah tolerance check
    print("\n--- ROLE-BASED ANALYSIS ---")
    c.execute('''
        SELECT social_rule_adherence, COUNT(*) as cnt
        FROM agents
        WHERE is_active = 1 AND social_rule_adherence IS NOT NULL
        GROUP BY ROUND(social_rule_adherence, 1)
        ORDER BY social_rule_adherence
    ''')
    adherence = c.fetchall()
    if adherence:
        for a in adherence:
            print(f"  social_rule_adherence {a['social_rule_adherence']:.1f}: {a['cnt']} agents")
    else:
        print("  No social_rule_adherence data (pariah tolerance not implemented)")

    conn.close()
    print("\n" + "=" * 70)

if __name__ == '__main__':
    analyze_pariahs()
