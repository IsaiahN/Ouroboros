#!/usr/bin/env python
"""Quick telemetry check after evolution run."""
import sys
import os
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check last hour of telemetry
print("=== TELEMETRY CHECK (Last 1 Hour) ===\n")

result = db.execute_query("""
    SELECT 
        COUNT(*) as total_actions,
        SUM(CASE WHEN persona_proposal_count > 1 THEN 1 ELSE 0 END) as multi_proposal,
        SUM(CASE WHEN synthesis_enabled = 1 THEN 1 ELSE 0 END) as synthesis_enabled,
        SUM(CASE WHEN budget_spend > 0 THEN 1 ELSE 0 END) as budget_spent,
        SUM(CASE WHEN counterfactual_rollouts_used > 0 THEN 1 ELSE 0 END) as cf_used,
        AVG(COALESCE(persona_proposal_count, 0)) as avg_proposals,
        AVG(COALESCE(budget_spend, 0)) as avg_budget_spend
    FROM action_traces 
    WHERE created_at >= datetime('now', '-1 hour')
""")

if result and result[0]:
    r = result[0]
    total = r.get('total_actions', 0) or 0
    multi = r.get('multi_proposal', 0) or 0
    synth = r.get('synthesis_enabled', 0) or 0
    budget = r.get('budget_spent', 0) or 0
    cf = r.get('cf_used', 0) or 0
    avg_prop = r.get('avg_proposals', 0) or 0
    avg_spend = r.get('avg_budget_spend', 0) or 0
    
    print(f"Total Actions:      {total:,}")
    print(f"Multi-Proposal:     {multi:,} ({100*multi/total if total else 0:.1f}%)")
    print(f"Synthesis Enabled:  {synth:,} ({100*synth/total if total else 0:.1f}%)")
    print(f"Budget Spent > 0:   {budget:,} ({100*budget/total if total else 0:.1f}%)")
    print(f"Counterfactual Used:{cf:,} ({100*cf/total if total else 0:.1f}%)")
    print(f"Avg Proposals:      {avg_prop:.2f}")
    print(f"Avg Budget Spend:   {avg_spend:.4f}")
else:
    print("No data in last hour")

# Check persona_proposal_count distribution
print("\n=== PERSONA PROPOSAL COUNT DISTRIBUTION ===\n")
dist = db.execute_query("""
    SELECT persona_proposal_count, COUNT(*) as cnt
    FROM action_traces
    WHERE created_at >= datetime('now', '-1 hour')
    GROUP BY persona_proposal_count
    ORDER BY cnt DESC
    LIMIT 10
""")
if dist:
    for row in dist:
        val = row.get('persona_proposal_count')
        cnt = row.get('cnt', 0)
        print(f"  {val}: {cnt:,} actions")

# Check budget_spend distribution
print("\n=== BUDGET SPEND DISTRIBUTION ===\n")
budget_dist = db.execute_query("""
    SELECT 
        CASE 
            WHEN budget_spend IS NULL THEN 'NULL'
            WHEN budget_spend = 0 THEN '0'
            WHEN budget_spend > 0 AND budget_spend <= 0.1 THEN '0-0.1'
            WHEN budget_spend > 0.1 AND budget_spend <= 0.5 THEN '0.1-0.5'
            ELSE '>0.5'
        END as bucket,
        COUNT(*) as cnt
    FROM action_traces
    WHERE created_at >= datetime('now', '-1 hour')
    GROUP BY bucket
    ORDER BY cnt DESC
""")
if budget_dist:
    for row in budget_dist:
        bucket = row.get('bucket')
        cnt = row.get('cnt', 0)
        print(f"  {bucket}: {cnt:,} actions")

# Check game results
print("\n=== GAME RESULTS (Last 1 Hour) ===\n")
games = db.execute_query("""
    SELECT 
        COUNT(*) as total_games,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive_score,
        AVG(final_score) as avg_score,
        AVG(actions_taken) as avg_actions
    FROM game_results
    WHERE created_at >= datetime('now', '-1 hour')
""")

if games and games[0]:
    g = games[0]
    total = g.get('total_games', 0) or 0
    pos = g.get('positive_score', 0) or 0
    avg_score = g.get('avg_score', 0) or 0
    avg_actions = g.get('avg_actions', 0) or 0
    
    print(f"Total Games:        {total:,}")
    print(f"Positive Score:     {pos:,} ({100*pos/total if total else 0:.1f}%)")
    print(f"Avg Score:          {avg_score:.2f}")
    print(f"Avg Actions:        {avg_actions:.0f}")
else:
    print("No games in last hour")

print("\n=== COGNITIVE STAGES ===\n")
stages = db.execute_query("""
    SELECT current_stage, COUNT(*) as cnt 
    FROM agent_cognitive_stages 
    GROUP BY current_stage
""")
if stages:
    for row in stages:
        stage = row.get('current_stage', 'unknown')
        cnt = row.get('cnt', 0)
        print(f"  {stage:25} {cnt}")
