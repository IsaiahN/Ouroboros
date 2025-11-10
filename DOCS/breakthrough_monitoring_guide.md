# Breakthrough Systems - Quick Monitoring Guide

## Check System Status

```python
from database_interface import DatabaseInterface
db = DatabaseInterface()

# 1. Active subgoal plans
plans = db.execute_query("""
    SELECT agent_id, game_id, main_objective, status
    FROM subgoal_plans
    WHERE status = 'active'
    ORDER BY created_at DESC
    LIMIT 10
""")
print(f"Active Plans: {len(plans)}")

# 2. Population frustration levels
frustration = db.execute_query("""
    SELECT current_state, COUNT(*) as count
    FROM agent_frustration_states
    GROUP BY current_state
""")
print(f"Frustration States: {frustration}")

# 3. Recent near-misses
near_misses = db.execute_query("""
    SELECT game_id, final_score, gap_to_victory
    FROM near_miss_games
    ORDER BY analyzed_at DESC
    LIMIT 10
""")
print(f"Recent Near-Misses: {len(near_misses)}")

# 4. Collective sessions
collective = db.execute_query("""
    SELECT game_id, reasoning_mode, completed_at
    FROM collective_reasoning_sessions
    ORDER BY started_at DESC
    LIMIT 10
""")
print(f"Collective Sessions: {len(collective)}")

# 5. Counterfactual learnings
learnings = db.execute_query("""
    SELECT learning_type, COUNT(*) as count
    FROM counterfactual_learnings
    GROUP BY learning_type
""")
print(f"Counterfactual Learnings: {learnings}")
```

## Watch for These Indicators

### Positive Signs
- ✅ Subgoal plans being created (shows agents using hierarchical planning)
- ✅ Frustration states mostly 'normal' or 'mild' (population healthy)
- ✅ Near-miss insights generating improvement suggestions
- ✅ Collective sessions resolving difficult games
- ✅ Counterfactual learnings accumulating (knowledge base growing)

### Warning Signs
- ⚠️ Frustration quorum events (30%+ agents stuck - triggers desperation)
- ⚠️ Zero subgoal plans (agents not using planning system)
- ⚠️ High ratio of 'critical' frustration states
- ⚠️ No collective sessions (no difficult games identified)
- ⚠️ Low counterfactual learning confidence scores

## Integration Checkpoints

### During Evolution Run

Watch terminal output for:
- `[✓] Breakthrough systems initialized` - Systems loaded successfully
- `[!] Frustration quorum reached` - Desperation mode activated
- `[>] Near-miss analysis recorded` - High-score failure analyzed
- `[ENSEMBLE] Collective reasoning session started` - Hard game collaboration
- `[?] Counterfactual: X alternative strategies identified` - Learning from failure
- `📋 Following subgoal plan: ACTIONX` - Agent using hierarchical planning
- `📋 Created hierarchical plan for game...` - New plan generated

### Post-Run Analysis

```bash
# Check if systems activated
python quick_analysis.py

# Full evolution status
python evolution_status_report.py

# Specific system queries
python -c "
from database_interface import DatabaseInterface
db = DatabaseInterface()

# Frustration quorum events
events = db.execute_query('SELECT COUNT(*) FROM frustration_quorum_events')
print(f'Quorum Events: {events[0][\"COUNT(*)\"]}'

# Plans created per generation
plans_per_gen = db.execute_query('''
    SELECT generation, COUNT(*) as plan_count
    FROM subgoal_plans
    GROUP BY generation
    ORDER BY generation DESC
    LIMIT 10
''')
for row in plans_per_gen:
    print(f'Gen {row[\"generation\"]}: {row[\"plan_count\"]} plans')
"
```

## System Triggers

| System | Trigger Condition | Expected Frequency |
|--------|------------------|-------------------|
| Subgoal Planning | Score > 0 but < 20 in game | 40-60% of games |
| Frustration Detection | Every game completion | 100% of games |
| Near-Miss Analysis | Final score 15-18 (75-90%) | 5-15% of games |
| Collective Reasoning | Game attempted 3+ times without win | 10-20% of games |
| Counterfactual Analysis | Score < 15 and not won | 60-80% of games |

## Expected Timeline

| Generation Range | Expected Breakthrough System Activity |
|-----------------|--------------------------------------|
| 1-10 | Baseline - Systems learning population behavior |
| 11-20 | Subgoal plans start showing effectiveness |
| 21-30 | Frustration quorum events decrease (population adapting) |
| 31-40 | Near-miss conversion improves (learning from 15-18 scores) |
| 41-50 | Collective reasoning shows synergy on hard games |
| 50+ | Counterfactual insights drive strategic evolution |

## Troubleshooting

### "No subgoal plans being created"
- Check: `SELECT COUNT(*) FROM subgoal_plans WHERE generation = <current>`
- Likely cause: Agents not reaching score > 0 (still struggling with basics)
- Solution: Wait for population to reach baseline competence

### "Frustration quorum constantly triggering"
- Check: `SELECT current_state, COUNT(*) FROM agent_frustration_states GROUP BY current_state`
- Likely cause: Population truly stuck, desperation mode working as intended
- Solution: Review desperation signal effectiveness in regulatory_signal_engine

### "Zero near-miss analyses"
- Check: `SELECT COUNT(*) FROM near_miss_games`
- Likely cause: No games reaching 15-18 score range
- Solution: This is expected if population still at low performance - system will activate when agents improve

### "Collective reasoning not triggering"
- Check: `SELECT game_id, COUNT(*) as attempts FROM agent_arc_performance WHERE win_detected = FALSE GROUP BY game_id HAVING attempts >= 3`
- Likely cause: Games not being repeated 3+ times
- Solution: Ensure game selection allows retries (diversity mode may prevent this)

### "Counterfactual learnings not accumulating"
- Check: `SELECT COUNT(*) FROM counterfactual_learnings`
- Likely cause: analyze_failure() encountering errors
- Solution: Review system_logs table for counterfactual analysis errors

## Manual System Invocation (Testing)

```python
from database_interface import DatabaseInterface
from subgoal_planner import SubgoalPlanner

db = DatabaseInterface()
planner = SubgoalPlanner(db)

# Manually create a plan (for testing)
plan_id = planner.create_plan(
    agent_id="test_agent_id",
    game_id="test_game_id",
    session_id="test_session_id",
    current_frame=[[0]*10 for _ in range(10)],  # Dummy 10x10 frame
    current_score=5.0,
    generation=1
)
print(f"Created test plan: {plan_id}")

# Manually check frustration
from frustration_detector import FrustrationDetector
frustration = FrustrationDetector(db)

frustration.update_agent_frustration(
    agent_id="test_agent_id",
    game_id="test_game_id",
    score_achieved=3.0,
    previous_best_score=5.0,  # Regression!
    actions_taken=150,
    generation=1
)
print("Frustration state updated")

# Check if quorum reached
event_id = frustration.check_frustration_quorum(generation=1)
if event_id:
    print(f"Quorum event triggered: {event_id}")
```

## Success Indicators (30-50 Generations)

| Metric | Baseline (Gen 1-10) | Target (Gen 30-50) | Breakthrough Indicator |
|--------|-------------------|-------------------|----------------------|
| Subgoal Plans Created | 0-5 per gen | 20-40 per gen | Agents learning to plan |
| Frustration Quorum Events | 5-10 per gen | 0-2 per gen | Population adapting |
| Near-Miss → Win Conversion | 0% | 10-25% | Learning from near-wins |
| Collective Sessions | 0-2 per gen | 5-15 per gen | Hard games being tackled |
| Counterfactual Insights | 0-20 total | 100-300 total | Knowledge accumulation |

**When breakthrough happens:** Expect to see near-miss analysis → subgoal plan creation → win within 2-5 game attempts. This cycle indicates systems are synergizing effectively.
