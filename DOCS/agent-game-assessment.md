# Autonomous Ouroboros Evolution System

## Mission Transition: Human to Autonomous Oversight
## Reference Foundation
- DOCS\how_the_system_works.md (MASTER REFERENCE)
- DOCS\ouroboros_final_implementation.md  (Technical Implementation)
- DOCS\ouroboros - biome theory.md
- DOCS\Ouroboros Concept.md
- DOCS\Ouroboros_Three_Layer_Quick_Reference.md
- DOCS\Roadmap_Level_4_to_5.md
- DOCS\arc_api_actions_rules.md
- DOCS\how_arc_api_works.md
- DOCS\agent-game-assessment.md

**Previous Human Role:**
- Monitor ARC 3 AGI scorecards after run_evolution cycles (typically 5 generations)
- Check levels completed per agent
- Identify "Zero" scores indicating sequence retrieval/storage failures
- Test hypotheses for improving level completion rates
- Fix code bugs and reasoning stopgaps in collective intelligence systems
- I would review frame by frame play of games to test out new theories on how to get the system to learn how to play on its own without telling it how to win or teaching it the rules of the game.
- Ensure that the system learn how to play the rules of the game on its on

**New Autonomous Role:**
- **Follow the Master Ruleset** in `.github/copilot-instructions.md`
- Generate superior hypotheses using ouroboros_final_implementation principles
- Optimize agent rules, mixes, and modes through systematic experimentation
- Replace manual monitoring with automated performance analysis
- Continuously improve collective reasoning and intelligence systems

## Core Operational Framework

### Primary Objective
Beat every level of every game in ARC 3 AGI system to prove the Ouroboros theory.

### Key Performance Monitoring
- Levels completed per agent and game
- Zero-score detection (sequence system health)
- Level completion rate improvements
- Collective intelligence efficacy

### System Optimization Domains
1. **Agent Role Balancing** - Pioneer, Optimizer, Generalist, Exploiter mixes
2. **Rule Refinement** - Behavioral parameters and interaction rules
3. **Sequence Systems** - Storage, retrieval, and propagation efficiency
4. **Collective Intelligence** - Cross-agent knowledge sharing and reasoning

## Autonomous Operation Protocol

### Evolution Cycle Management
- Run variable-length generations based on testing needs (1 generation = 1 hour of testing)
- Short cycles (1-2 generations) for specific hypothesis testing
- Longer cycles for comprehensive evolutionary progress
- Automated analysis after each cycle completion

### run_evolution.py Command Reference

**Basic Usage:**
```bash
python run_evolution.py              # Standard mode (default)
python run_evolution.py --fast       # Fast iterations
python run_evolution.py --thorough   # Deep evaluation
python run_evolution.py --quick      # Quick 5-generation test
python run_evolution.py --test       # Minimal test (1 agent, 1 game)
```

**Available Parameters:**

| Flag | Description | Population | Games/Gen | Interval | Max Gens |
|------|-------------|------------|-----------|----------|----------|
| (none) | Standard balanced evolution | 10 | 10 | 60 min | 50 |
| `--fast` | Quick iterations | 8 | 5 | 30 min | 30 |
| `--thorough` | Deep evaluation | 15 | 20 | 90 min | 20 |
| `--quick` | Quick test run | 5 | 5 | 15 min | 5 |
| `--test` | Minimal test | 1 | 1 | 1 min | 1 |

**Optional Modifiers:**

| Flag | Description |
|------|-------------|
| `--max-generations N` | Override max generations (useful when resuming) |
| `--diversity` | Enable AGI/diversity mode (generalization focus, anti-overfitting) |
| `--specialist` | Enable specialist mode (deep mastery, repetition-based learning) |

**Examples:**
```bash
# Run 2 generations for hypothesis testing
python run_evolution.py --max-generations 2

# Fast mode with diversity focus
python run_evolution.py --fast --diversity

# Thorough evaluation with custom generation limit
python run_evolution.py --thorough --max-generations 10

# Specialist mode for deep game mastery
python run_evolution.py --specialist
```

**Configuration Output:**
When run, the script displays the active configuration:
```
Configuration:
  Initial Population: 10 agents
  Games per Generation: 10
  Evolution Interval: 60 minutes
  Max Generations: 50
```

**Requirements:**
- Valid `ARC_API_KEY` must be set in `.env` file
- Automatically runs `cleanup_temp_files()` on startup

### Hypothesis Generation Framework
- Analyze performance patterns across games and agent types
- Identify bottlenecks in level progression
- Test variations in agent role distributions
- Optimize collective reasoning parameters
- Improve sequence reliability and transfer efficiency

### Data-Driven Optimization
- Query ARC API and database for performance metrics
- Identify successful strategies per game type
- Detect and repair sequence system failures
- Balance exploration vs exploitation across agent roles

## Technical Implementation Standards

### Code Management
- Never enable pycache for new files
- Follow all copilot rules from project documentation
- Commit substantial changes to GitHub with detailed documentation
- Maintain system integrity during modifications

### Database Management
- Premium priority: Strategic garbage cleanup of junk data
- Critical preservation: Protect evolutionary history and agent knowledge
- Backup protocol: Automatic backups before SQL schema changes
- Storage optimization: Regular vacuuming with storage constraints in mind

### safe_cleanup.py - Database Cleanup Reference

The primary database cleanup routine. Automatically runs every 10 generations during evolution, or can be run manually.

**Usage:**
```bash
python safe_cleanup.py              # Dry run (shows what would be deleted)
python safe_cleanup.py --execute    # Actually perform cleanup
```

**What it Cleans (Safely):**

| Table | Retention Policy | Purpose |
|-------|------------------|---------|
| `game_results` | Delete zero-score | Failed games provide no learning value |
| `score_history` | Keep 7 days | Tick-by-tick score logging (debugging) |
| `system_logs` | Keep 5,000 | System operation logs |
| `navigation_state_history` | Keep 50,000 | Agent navigation breadcrumbs |
| `action_traces` | Keep 100,000 | Detailed action logs |
| `sensation_learning_events` | Keep 200,000 | Emotional learning events |
| `agent_operating_modes` | Keep 100,000 | Mode assignment history |

**What it Preserves (NEVER deleted):**
- Winning sequences (critical!)
- Active agents and their genomes/epigenetics
- Positive-score game results
- Learned rules, patterns, prestige scores
- Full game sequences

**Programmatic Usage:**
```python
from safe_cleanup import SafeDatabaseCleaner

cleaner = SafeDatabaseCleaner()
results = cleaner.cleanup(dry_run=False, verbose=True)
print(f"Deleted {results['total_deleted']} rows")

# Verify critical data
cleaner.verify_critical_data()
```

**Integration:**
- Called automatically every 10 generations in `autonomous_evolution_runner.py`
- Replaces the older `HistoricalDataCleaner` (more comprehensive)
- Does NOT run VACUUM (requires 2x disk space) - deleted space is reused

### Change Management
- Regular updates on optimization progress and findings
- Substantial changes require GitHub commits with rationale
- Performance impact assessment for all modifications
- Rollback strategies for unsuccessful optimizations

## Success Metrics

### Primary Progress Indicators
- Game completion rates (fully beaten games)
- Level progression consistency
- Reduction in sequence system failures
- Improvement in collective intelligence efficacy

### Optimization Validation
- Hypothesis testing success rates
- Parameter adjustment effectiveness
- Agent role mix performance impact
- Knowledge transfer efficiency gains



The autonomous system will begin by establishing baseline performance metrics, then systematically test optimization hypotheses while preserving the evolutionary knowledge accumulated in the database. All changes will be documented and committed with careful attention to data preservation and system stability.
# Scorecards

> Keeping track of agent performance

Scorecards aggregate the results from your agent's [game](/games) performance.

In order to play a game, a scorecard must be opened, and the agent must submit the scorecard ID with each action. Running a [swarm](/swarms) (recommended) will automatically open/close a scorecard for each agent.

Scorecards can be viewed online at [https://three.arcprize.org/scorecards](https://three.arcprize.org/scorecards) and [https://three.arcprize.org/scorecards/\`scorecard\_id\`](https://three.arcprize.org/scorecards/`scorecard_id`).

Scorecard fields

| Field       | Description                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------- |
| tags        | Array of strings used to categorize and filter scorecards (e.g., \["experiment1", "v2.0", "test"]) |
| source\_url | Optional URL field returned in the scorecard response                                              |
| opaque      | Optional field for arbitrary data                                                                  |

Scorecards are not public, however you can share [replays](/recordings) with others.

Other scorecard notes:

* Scorecards auto close after 15min
* Agent scorecards are automatically added to the leaderboard in batch every \~15min
* Stopping the program prematurely with Ctrl‑C mid‑run will not allow you to see the scorecard results.


# Recordings & Replays

> Viewing your agent's gameplay

The ARC-AGI-3 agent system includes automatic recording of gameplay sessions.

The most common way to view a recording is online in the ARC-AGI-3 UI. You can navigate to your scorecard to review your gameplay sessions.

Ex: `https://three.arcprize.org/scorecards/<scorecard_id>`

Here is an example [recording](https://three.arcprize.org/replay/ft09-16726c5b26ff/1d251d20-9043-4ace-9f9d-09822f5438d8)

## Automatic Recording

When running a [swarm](/swarms) all agent gameplay is also recorded by default and stored in the `recordings/` directory with GUID-based filenames:

```
ls20-6cbb1acf0530.random.100.a1b2c3d4-e5f6-7890-abcd-ef1234567890.recording.jsonl
```

The filename format is: `{game_id}.{agent_type}.{max_actions}.{guid}.recording.jsonl`

## Recording File Format

### JSONL Format

Recordings are stored in JSONL format with timestamped entries:

```json
{"timestamp": "2024-01-15T10:30:45.123456+00:00", "data": {"game_id": "ls20-016295f7601e", "frame": [...], "state": "NOT_FINISHED", "score": 5, "action_input": {"id": 0, "data": {"game_id": "ls20-016295f7601e"}, "reasoning": "..."}, "guid": "...", "full_reset": false}}
{"timestamp": "2024-01-15T10:30:46.234567+00:00", "data": {"game_id": "ls20-016295f7601e", "frame": [...], "state": "NOT_FINISHED", "score": 6, "action_input": {"id": 1, "data": {"game_id": "ls20-016295f7601e"}, "reasoning": "..."}, "guid": "...", "full_reset": false}}
```
