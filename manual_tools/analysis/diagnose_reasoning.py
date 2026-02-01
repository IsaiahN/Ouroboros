#!/usr/bin/env python3
"""
Diagnostic script for agent consciousness and reasoning systems.
Identifies why primitives/reasoning aren't working effectively.

Rule 1: No pycache
Rule 2: Database-only storage
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
from datetime import datetime, timedelta

from database_interface import DatabaseInterface


def diagnose():
    """Run comprehensive diagnostics on reasoning systems."""
    db = DatabaseInterface()
    issues_found = []

    print("=" * 70)
    print("AGENT CONSCIOUSNESS & REASONING DIAGNOSTIC REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # =========================================================================
    # 1. CHECK HYPOTHESIS SYSTEM HEALTH
    # =========================================================================
    print("\n[1] NETWORK HYPOTHESIS SYSTEM")
    print("-" * 50)

    hyp_stats = db.execute_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN validation_attempts > 0 THEN 1 ELSE 0 END) as validated_any,
            SUM(CASE WHEN validation_attempts >= 3 THEN 1 ELSE 0 END) as validated_3plus,
            SUM(CASE WHEN validated_by_win = 1 THEN 1 ELSE 0 END) as win_validated,
            AVG(reliability_score) as avg_reliability,
            MAX(validation_attempts) as max_attempts
        FROM network_object_control_hypotheses
        WHERE is_active = 1
    """)

    if hyp_stats and hyp_stats[0]:
        stats = hyp_stats[0]
        print(f"  Total active hypotheses: {stats.get('total', 0)}")
        print(f"  With any validation: {stats.get('validated_any', 0)}")
        print(f"  With 3+ validations: {stats.get('validated_3plus', 0)}")
        print(f"  Win-validated: {stats.get('win_validated', 0)}")
        print(f"  Average reliability: {stats.get('avg_reliability', 0):.3f}")
        print(f"  Max validation attempts: {stats.get('max_attempts', 0)}")

        if stats.get('total', 0) > 0 and stats.get('validated_any', 0) == 0:
            issues_found.append({
                'severity': 'CRITICAL',
                'system': 'Hypothesis System',
                'problem': 'Hypotheses exist but NONE have been validated',
                'meaning': 'Tier 4 (Usage) is broken - hypotheses not being used in gameplay',
                'fix': 'Check that get_network_control_hypotheses() is being called during action selection'
            })
    else:
        print("  No hypothesis data found!")
        issues_found.append({
            'severity': 'CRITICAL',
            'system': 'Hypothesis System',
            'problem': 'No hypotheses in database',
            'meaning': 'Discovery phase not executing or not storing results',
            'fix': 'Check execute_object_discovery() and learn_from_movement_correlation()'
        })

    # =========================================================================
    # 2. CHECK PRIMITIVE USAGE
    # =========================================================================
    print("\n[2] PRIMITIVE SYSTEM STATUS")
    print("-" * 50)

    try:
        from seed_primitives import get_seed_primitives
        registry = get_seed_primitives()
        primitives = registry.list_all() if hasattr(registry, 'list_all') else []
        print(f"  Seed primitives loaded: {len(primitives) if primitives else 'Unknown'}")
        print(f"  Registry available: YES")

        # Check categories by getting actual primitive objects
        categories = set()
        for name in (primitives or []):
            prim = registry.get(name) if hasattr(registry, 'get') else None
            if prim and hasattr(prim, 'category'):
                categories.add(str(prim.category))
        print(f"  Categories available: {len(categories)}")
    except Exception as e:
        print(f"  [ERROR] Primitive system not loading: {e}")
        issues_found.append({
            'severity': 'CRITICAL',
            'system': 'Primitive System',
            'problem': f'Failed to load: {e}',
            'meaning': 'Baby-derived cognitive primitives unavailable',
            'fix': 'Check seed_primitives.py imports and initialization'
        })

    # =========================================================================
    # 3. CHECK ACTION TRACE CONTEXT
    # =========================================================================
    print("\n[3] ACTION TRACE REASONING CONTEXT")
    print("-" * 50)

    trace_stats = db.execute_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN context_mode IS NOT NULL THEN 1 ELSE 0 END) as has_context,
            SUM(CASE WHEN question_tier IS NOT NULL THEN 1 ELSE 0 END) as has_tier,
            SUM(CASE WHEN persona_proposal_count > 0 THEN 1 ELSE 0 END) as has_personas
        FROM action_traces
        WHERE created_at > datetime('now', '-24 hours')
    """)

    if trace_stats and trace_stats[0]:
        stats = trace_stats[0]
        total = stats.get('total', 0)
        print(f"  Actions in last 24h: {total}")
        print(f"  With context_mode: {stats.get('has_context', 0)} ({100*stats.get('has_context', 0)/max(1,total):.1f}%)")
        print(f"  With question_tier: {stats.get('has_tier', 0)} ({100*stats.get('has_tier', 0)/max(1,total):.1f}%)")
        print(f"  With persona proposals: {stats.get('has_personas', 0)} ({100*stats.get('has_personas', 0)/max(1,total):.1f}%)")

        if total > 0:
            if stats.get('has_context', 0) == 0:
                issues_found.append({
                    'severity': 'HIGH',
                    'system': 'Action Selection',
                    'problem': 'No actions have context_mode set',
                    'meaning': 'Reasoning modes (Q1-Q6) not being recorded',
                    'fix': 'Check _select_action() is setting context_mode in traces'
                })
            if stats.get('has_tier', 0) == 0:
                issues_found.append({
                    'severity': 'HIGH',
                    'system': 'Questioning Engine',
                    'problem': 'No actions have question_tier set',
                    'meaning': 'Q-fields not being generated during gameplay',
                    'fix': 'Check QuestioningEngineWithTeeth is being called'
                })
    else:
        print("  No recent action traces!")

    # =========================================================================
    # 4. CHECK DISCOVERY FLOW
    # =========================================================================
    print("\n[4] DISCOVERY -> ACTION FLOW")
    print("-" * 50)

    # Check if discoveries are being made
    disc_stats = db.execute_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN validation_successes > 0 THEN 1 ELSE 0 END) as with_success,
            COUNT(DISTINCT game_type) as game_types
        FROM network_object_control_hypotheses
    """)

    if disc_stats and disc_stats[0]:
        stats = disc_stats[0]
        print(f"  Total discoveries stored: {stats.get('total', 0)}")
        print(f"  Game types covered: {stats.get('game_types', 0)}")
        print(f"  With validation successes: {stats.get('with_success', 0)}")

    # =========================================================================
    # 5. CHECK SELF-MODEL STATUS
    # =========================================================================
    print("\n[5] AGENT SELF-MODEL (I-am-this-object)")
    print("-" * 50)

    control_stats = db.execute_query("""
        SELECT COUNT(*) as total, COUNT(DISTINCT agent_id) as agents
        FROM agent_object_control
    """)

    if control_stats and control_stats[0]:
        stats = control_stats[0]
        print(f"  Object control records: {stats.get('total', 0)}")
        print(f"  Agents with self-models: {stats.get('agents', 0)}")

        if stats.get('total', 0) == 0:
            issues_found.append({
                'severity': 'CRITICAL',
                'system': 'Self-Model',
                'problem': 'No object control records found',
                'meaning': 'Agents not learning which objects they control',
                'fix': 'Check learn_object_control() is being called during gameplay'
            })

    # =========================================================================
    # 6. CHECK TWO STREAMS (Network Wisdom)
    # =========================================================================
    print("\n[6] TWO STREAMS ARCHITECTURE (Stream A/B)")
    print("-" * 50)

    agent_stats = db.execute_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN self_network_bias IS NOT NULL THEN 1 ELSE 0 END) as has_bias,
            AVG(self_network_bias) as avg_bias
        FROM agents
        WHERE is_active = 1
    """)

    if agent_stats and agent_stats[0]:
        stats = agent_stats[0]
        print(f"  Active agents: {stats.get('total', 0)}")
        print(f"  With self_network_bias set: {stats.get('has_bias', 0)}")
        print(f"  Average w_A/w_B bias: {stats.get('avg_bias', 0.5):.3f}")

        if stats.get('total', 0) > 0 and stats.get('has_bias', 0) == 0:
            issues_found.append({
                'severity': 'HIGH',
                'system': 'Two Streams',
                'problem': 'No agents have self_network_bias set',
                'meaning': 'Stream A/B weighting not being computed',
                'fix': 'Check store_agent() is saving Two-Streams columns'
            })

    # =========================================================================
    # 7. CHECK GAME RESULTS QUALITY
    # =========================================================================
    print("\n[7] GAME PERFORMANCE METRICS")
    print("-" * 50)

    game_stats = db.execute_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN total_actions = 0 THEN 1 ELSE 0 END) as zero_actions,
            AVG(total_actions) as avg_actions,
            AVG(final_score) as avg_score
        FROM game_results
        WHERE created_at > datetime('now', '-24 hours')
    """)

    if game_stats and game_stats[0]:
        stats = game_stats[0]
        total = stats.get('total', 0)
        print(f"  Games in last 24h: {total}")
        print(f"  With positive score: {stats.get('positive', 0)} ({100*stats.get('positive', 0)/max(1,total):.1f}%)")
        print(f"  With zero actions: {stats.get('zero_actions', 0)} ({100*stats.get('zero_actions', 0)/max(1,total):.1f}%)")
        print(f"  Average actions: {stats.get('avg_actions', 0):.1f}")
        print(f"  Average score: {stats.get('avg_score', 0):.2f}")

        if stats.get('zero_actions', 0) > total * 0.3:
            issues_found.append({
                'severity': 'CRITICAL',
                'system': 'Gameplay',
                'problem': f'{stats.get("zero_actions")} games have 0 actions',
                'meaning': 'Games failing before any actions taken (API or sequence issues)',
                'fix': 'Check API connectivity and sequence retrieval'
            })

    # =========================================================================
    # 8. CHECK PERSONA SYSTEM
    # =========================================================================
    print("\n[8] PERSONA SYSTEM")
    print("-" * 50)

    try:
        persona_stats = db.execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT agent_id) as agents_with_personas
            FROM persona_profiles
        """)

        if persona_stats and persona_stats[0]:
            stats = persona_stats[0]
            print(f"  Total personas: {stats.get('total', 0)}")
            print(f"  Agents with personas: {stats.get('agents_with_personas', 0)}")
        else:
            print("  No persona data found")
    except Exception as e:
        print(f"  [ERROR] Persona table issue: {e}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)

    if not issues_found:
        print("\n[OK] No critical issues detected!")
        print("If reasoning still seems broken, run with verbose logging to trace execution.")
    else:
        print(f"\n[!] Found {len(issues_found)} issues:\n")

        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. [{issue['severity']}] {issue['system']}")
            print(f"   Problem: {issue['problem']}")
            print(f"   Meaning: {issue['meaning']}")
            print(f"   Fix: {issue['fix']}")
            print()

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    print("\n" + "-" * 70)
    print("RECOMMENDED NEXT STEPS")
    print("-" * 70)

    critical_count = sum(1 for i in issues_found if i['severity'] == 'CRITICAL')
    high_count = sum(1 for i in issues_found if i['severity'] == 'HIGH')

    if critical_count > 0:
        print("""
1. Fix CRITICAL issues first - these block all learning
2. Run a short evolution (2-3 generations) with DEBUG logging
3. Check console for [DISCOVERY], [HYPOTHESIS], [PRIMITIVE] prefixes
4. Verify discoveries are flowing: Discovery -> Storage -> Retrieval -> Use
""")
    elif high_count > 0:
        print("""
1. Address HIGH priority issues for reasoning to work
2. The reasoning pipeline exists but isn't connected end-to-end
3. Trace the data flow from action -> discovery -> hypothesis -> next action
""")
    else:
        print("""
1. System appears structurally sound
2. Enable DEBUG logging and run evolution
3. Look for logic errors in specific reasoning functions
4. Check if fallback paths are always being taken
""")

    return issues_found


if __name__ == "__main__":
    issues = diagnose()
    sys.exit(1 if any(i['severity'] == 'CRITICAL' for i in issues) else 0)
