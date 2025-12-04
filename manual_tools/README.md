# Manual Tools

**Purpose**: Standalone scripts meant to be run manually for debugging, testing, analysis, and one-time operations.  
**Note**: These are NOT integrated into the main evolution loop - they are developer utilities.

---

## Debug Utilities

| File | Purpose | Usage |
|------|---------|-------|
| `check_db.py` | Quick database health check | `python check_db.py` |
| `inspect_db.py` | Detailed database inspection | `python inspect_db.py` |
| `dump_logs.py` | Export logs from database | `python dump_logs.py` |
| `list_sequences.py` | List all winning sequences | `python list_sequences.py` |
| `list_tables.py` | List all database tables | `python list_tables.py` |
| `get_replay_url.py` | Get ARC game replay URL | `python get_replay_url.py <game_id>` |
| `reproduce_0_actions.py` | Debug games with 0 actions | `python reproduce_0_actions.py` |
| `action_analyzer.py` | Analyze action patterns | `python action_analyzer.py` |

## Review/Analysis Tools

| File | Purpose | Usage |
|------|---------|-------|
| `review_agent_roles.py` | Analyze agent role assignments | `python review_agent_roles.py` |
| `review_scorecards.py` | Review game scorecards | `python review_scorecards.py` |
| `review_sequence_system.py` | Full sequence system review | `python review_sequence_system.py` |
| `review_test_evolution.py` | Review evolution test results | `python review_test_evolution.py` |
| `audit_prestige_system.py` | Audit prestige calculations | `python audit_prestige_system.py` |
| `assess_results.py` | Quick result assessment | `python assess_results.py` |

## Monitoring Tools

| File | Purpose | Usage |
|------|---------|-------|
| `monitor_game_results.py` | Monitor game results | `python monitor_game_results.py` |
| `monitor_sequence_validation.py` | Monitor sequence validation rates | `python monitor_sequence_validation.py` |
| `hypothesis_monitoring.py` | Track hypothesis tests | `python hypothesis_monitoring.py` |
| `system_status_report.py` | Generate system status report | `python system_status_report.py` |
| `readiness_check.py` | Check system readiness | `python readiness_check.py` |
| `real_progress_check.py` | Check actual progress | `python real_progress_check.py` |

## Cleanup/Recovery Tools

| File | Purpose | Usage |
|------|---------|-------|
| `aggressive_cleanup.py` | Aggressive database cleanup | `python aggressive_cleanup.py` |

| `emergency_sequence_cleanup.py` | Emergency sequence cleanup | `python emergency_sequence_cleanup.py` |
| `historical_data_cleanup.py` | Clean historical data | `python historical_data_cleanup.py` |
| `sequence_recovery_tool.py` | Recover sequences from traces | `python sequence_recovery_tool.py` |
| `rebuild_database.py` | Rebuild database from schema | `python rebuild_database.py` |
| `rebuild_sequences.py` | Rebuild sequence table | `python rebuild_sequences.py` |
| `remove_emojis.py` | Remove Unicode emojis from code | `python remove_emojis.py` |

## Simulation/Validation Tools

| File | Purpose | Usage |
|------|---------|-------|
| `simulate_pruning_logic.py` | Test pruning logic without executing | `python simulate_pruning_logic.py` |
| `track_references_over_time.py` | Track sequence usage trends | `python track_references_over_time.py` |
| `run_validation_cycle.py` | Run sequence validation cycle | `python run_validation_cycle.py` |

## Alternative Entry Points

| File | Purpose | Usage |
|------|---------|-------|


---

## Running From This Folder

These tools reference the parent directory's modules. Run them with:

```bash
# Option 1: Run from manual_tools folder with parent in path
cd manual_tools
$env:PYTHONPATH = ".."
python check_db.py

# Option 2: Run from project root
python manual_tools/check_db.py
```

---

**Note**: Unit tests have been moved to `/tests` folder.
