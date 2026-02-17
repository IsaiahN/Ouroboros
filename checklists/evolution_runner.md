# Evolution Runner -- runs trials on branches
# Absorbs: copilot-instructions Rules 6,7,12, Appendix A

## Immutable Rules
- NEVER mock/simulate ARC games -- always use real API (Rule 6)
- Verify real actions sent to ARC games -- monitor API calls (Rule 7)
- Run SafeDatabaseCleaner every 10 generations (Rule 12)
- PYTHONDONTWRITEBYTECODE=1 always (Rule 1)

## Process
- [ ] Activate .venv before execution
- [ ] Run evolution: python evolution_runner.py --mode offline --max-generations=K
- [ ] Monitor via get_terminal_output (NEVER send commands to active terminal)
- [ ] After completion: collect all 5 benchmark metrics
- [ ] Verify game_results table has new rows
- [ ] Return structured results to orchestrator
