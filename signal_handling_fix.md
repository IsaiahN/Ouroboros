# Signal Handling Fix - November 25, 2025

## Problem Identified
Games were starting but immediately aborting with 0-1 actions, no levels completed.

**Root Cause**: Signal handlers in `game_session_manager.py` were setting `is_shutting_down = True` when SIGINT was received, causing all active game loops to exit immediately (checked on every iteration in `core_gameplay.py` line 466).

## Evidence
- All game results showed: status="failed", total_actions=0-1, level_completions=0
- Pattern matched user's reported ARC scorecards exactly
- Timestamps showed games completing within seconds of starting

## Fix Applied
1. **game_session_manager.py**: Disabled signal handlers that were interfering with evolution-level signal handling
   - Commented out `_setup_signal_handlers()` call
   - Made the method a no-op with documentation explaining why

2. **core_gameplay.py**: Made game loop shutdown check less aggressive
   - Removed `or self.session_manager.is_shutting_down` from line 466
   - Only checks `is_running` flag now
   - `is_shutting_down` was being set by signal handlers that should not affect individual games

## Rationale
- The evolution runner (`autonomous_evolution_runner.py`) already has proper signal handling
- Child components (session manager) should not intercept signals meant for parent process
- Each game should complete unless explicitly stopped by evolution runner via `is_running = False`

## Testing Note
When testing in VS Code terminals, running additional commands sends SIGINT to background processes in the same terminal session. For clean testing, evolution must run uninterrupted in its own terminal.
