#!/usr/bin/env python3
"""
AGI Unified Theory Verification Script
Checks database and system alignment with agi_unified_theory.md principles
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
from pathlib import Path

def main():
    db_path = Path(__file__).parent / "core_data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    print("=" * 70)
    print("AGI UNIFIED THEORY ALIGNMENT VERIFICATION")
    print("=" * 70)
    
    # 1. Two-Stream Consciousness Check
    print("\n1. TWO-STREAM CONSCIOUSNESS (Private Memory vs Network Wisdom)")
    print("   Theory: 'Every agent integrates two data streams'")
    
    # Stream A: Private Memory (sensation_mappings)
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM sensation_mappings").fetchone()[0]
        print(f"   [OK] sensation_mappings: {cnt} rows (STREAM A - Private)")
    except:
        print("   [CRITICAL] sensation_mappings table MISSING (Stream A broken)")
    
    # Stream B: Network Wisdom (viral_packages)
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM viral_packages").fetchone()[0]
        print(f"   [OK] viral_packages: {cnt} rows (STREAM B - Network)")
    except:
        print("   [CRITICAL] viral_packages table MISSING (Stream B broken)")
    
    # 2. Dual Economy Check
    print("\n2. DUAL ECONOMY (Prestige vs Action Budgets - MUST BE SEPARATE)")
    print("   Theory: 'Metabolic resources must be separated from social capital'")
    try:
        agents = conn.execute(
            "SELECT prestige_score, action_budget FROM agents WHERE is_active = 1 LIMIT 5"
        ).fetchall()
        print("   Sample agents (prestige should NOT determine action_budget):")
        for a in agents:
            budget = a['action_budget'] if a['action_budget'] else "NULL"
            print(f"      Prestige: {a['prestige_score']:.2f}, Budget: {budget}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Network Knowledge Transfer (Layer 3 - Somatic)
    print("\n3. NETWORK KNOWLEDGE TRANSFER (Layer 3 - Somatic)")
    print("   Theory: 'Somatic layer = WHAT agent learned, NOT inherited'")
    try:
        seqs = conn.execute(
            "SELECT COUNT(*) as cnt, AVG(efficiency_score) as avg_eff FROM winning_sequences WHERE is_active = 1"
        ).fetchone()
        avg = seqs['avg_eff'] if seqs['avg_eff'] else 0
        print(f"   Active winning sequences: {seqs['cnt']}, Avg efficiency: {avg:.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Evolutionary Forgetting (Pariah Decay)
    print("\n4. EVOLUTIONARY FORGETTING (Relevance Decay)")
    print("   Theory: 'Forgetting is not a bug - it's essential for intelligence'")
    try:
        decay_check = conn.execute("""
            SELECT toxicity, COUNT(*) as cnt 
            FROM pariahs 
            GROUP BY ROUND(toxicity, 1)
            ORDER BY cnt DESC
        """).fetchall()
        print("   Pariah toxicity distribution:")
        for p in decay_check:
            marker = "[STALE!]" if p['toxicity'] == 1.0 else ""
            print(f"      Toxicity {p['toxicity']:.2f}: {p['cnt']} pariahs {marker}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Agent Role Distribution
    print("\n5. AGENT ROLE DISTRIBUTION (Last 24h)")
    print("   Theory: 'Role distribution adapts dynamically'")
    try:
        roles = conn.execute("""
            SELECT agent_mode, COUNT(*) as cnt 
            FROM agent_operating_modes 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY agent_mode
            ORDER BY cnt DESC
        """).fetchall()
        if roles:
            total = sum(r['cnt'] for r in roles)
            for r in roles:
                pct = (r['cnt'] / total * 100) if total > 0 else 0
                print(f"      {r['agent_mode']}: {r['cnt']} ({pct:.1f}%)")
        else:
            print("   [WARNING] No role data in last 24h")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 6. Level Progression Reality
    print("\n6. LEVEL PROGRESSION (Last 24h)")
    print("   Theory: System should show learning progress across levels")
    try:
        levels = conn.execute("""
            SELECT level_completions, COUNT(*) as cnt 
            FROM game_results 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY level_completions
            ORDER BY level_completions
        """).fetchall()
        if levels:
            total = sum(l['cnt'] for l in levels)
            for l in levels:
                pct = (l['cnt'] / total * 100) if total > 0 else 0
                marker = "[STUCK]" if l['level_completions'] == 0 and pct > 80 else ""
                print(f"      Level {l['level_completions']}: {l['cnt']} games ({pct:.1f}%) {marker}")
        else:
            print("   [WARNING] No game results in last 24h")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 7. Network Failure Hypotheses
    print("\n7. NETWORK FAILURE HYPOTHESES")
    print("   Theory: 'Network learns from failures via hypothesis generation'")
    try:
        hyp = conn.execute("""
            SELECT hypothesis_type, validation_status, COUNT(*) as cnt 
            FROM network_failure_hypotheses 
            GROUP BY hypothesis_type, validation_status
        """).fetchall()
        for h in hyp:
            print(f"      {h['hypothesis_type']}: {h['validation_status']} ({h['cnt']} entries)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 8. Agent Self-Model
    print("\n8. AGENT SELF-MODEL ('I am this object')")
    print("   Theory: 'Agents need self-model in each level'")
    try:
        sm = conn.execute("SELECT COUNT(*) FROM agent_self_model").fetchone()[0]
        print(f"   [OK] agent_self_model: {sm} entries")
    except:
        print("   [CRITICAL] agent_self_model table MISSING")
    
    # 9. Game Diversity
    print("\n9. GAME DIVERSITY (Anti-concentration)")
    print("   Theory: 'System should explore all games, not concentrate on few'")
    try:
        games = conn.execute("""
            SELECT game_id, COUNT(*) as cnt 
            FROM game_results 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY game_id
            ORDER BY cnt DESC
            LIMIT 5
        """).fetchall()
        if games:
            total = conn.execute(
                "SELECT COUNT(*) FROM game_results WHERE timestamp > datetime('now', '-1 day')"
            ).fetchone()[0]
            for g in games:
                pct = (g['cnt'] / total * 100) if total > 0 else 0
                marker = "[OVER-CONCENTRATED]" if pct > 30 else ""
                print(f"      {g['game_id'][:30]}: {g['cnt']} plays ({pct:.1f}%) {marker}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 10. Missing Tables Summary
    print("\n10. CRITICAL TABLE CHECK")
    required_tables = [
        ('viral_packages', 'Network wisdom storage'),
        ('agent_self_model', 'Object control identification'),
        ('sensation_mappings', 'Private memory stream'),
        ('prestige_discoveries', 'Network contribution tracking'),
    ]
    for table, purpose in required_tables:
        try:
            conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
            print(f"   [OK] {table}: {purpose}")
        except:
            print(f"   [MISSING] {table}: {purpose}")
    
    print("\n" + "=" * 70)
    print("SUMMARY: Check [CRITICAL], [MISSING], [STALE!], [STUCK] markers above")
    print("=" * 70)
    
    conn.close()

if __name__ == "__main__":
    main()
