# Additive Migration Plan

Execution order and SQL sketches for the additive schema changes. Do not drop existing columns or tables; legacy rows may remain null for new columns.

## Phase 1: New Tables
- attempts
  - CREATE TABLE attempts (
    attempt_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    level INTEGER,
    agent_id TEXT,
    role TEXT NOT NULL,
    mode TEXT NOT NULL,
    generation INTEGER,
    actions_used INTEGER,
    actions_budget INTEGER,
    game_actions_used INTEGER,
    game_actions_budget INTEGER,
    levels_completed INTEGER,
    score REAL,
    time_ms INTEGER,
    succeeded INTEGER,
    source_sequence_id TEXT,
    source_mode TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  - Indices: attempts(mode), attempts(role), attempts(game_id, level), attempts(generation).

- hook_failures
  - CREATE TABLE hook_failures (
    id INTEGER PRIMARY KEY,
    attempt_id TEXT,
    hook_name TEXT,
    hook_phase TEXT,
    exception_type TEXT,
    message TEXT,
    stack_hash TEXT,
    auto_disabled_flag INTEGER,
    game_id TEXT,
    level INTEGER,
    agent_id TEXT,
    generation INTEGER,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
  );
  - Indices: hook_failures(stack_hash, hook_name), hook_failures(attempt_id).

- action_proposals_log
  - CREATE TABLE action_proposals_log (
    id INTEGER PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    step_idx INTEGER NOT NULL,
    available_actions TEXT,
    proposals TEXT,
    chosen_action TEXT,
    chosen_reason TEXT,
    mode TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  - Indices: action_proposals_log(attempt_id, step_idx), action_proposals_log(mode).

- lesson_interpretations
  - CREATE TABLE lesson_interpretations (
    id INTEGER PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    game_id TEXT,
    level INTEGER,
    interpretation TEXT,
    explains_examples INTEGER,
    fails_examples INTEGER,
    confidence REAL,
    contradictions TEXT,
    coverage_notes TEXT,
    source_mode TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
  - Indices: lesson_interpretations(attempt_id), lesson_interpretations(game_id, level).

## Phase 2: Additive Columns (provenance)
- ALTER TABLE sequences ADD COLUMN source_attempt_id TEXT;
- ALTER TABLE sequences ADD COLUMN source_mode TEXT;
- Repeat for viral_packages, hypotheses, prestige logs (table names per schema).
- Indices: add source_attempt_id/source_mode where write volume is high.

## Phase 3: Backfill and Defaults
- Backfill source_mode for legacy rows with 'UNKNOWN'; leave source_attempt_id NULL for legacy.
- Ensure application layer refuses writes without source_attempt_id/source_mode when mode == LIVE.

## Phase 4: Integrity Checks
- Add CHECK constraints where safe (mode in enum, succeeded in {0,1}, role in known roles).
- Validation queries post-migration: counts, null scans on required fields, index existence.

## Rollout Notes
- Execute migrations with WAL enabled; ensure backups before apply.
- Update data interfaces to write to new tables/columns before enforcing NOT NULL in future iterations.
- No log files; all migration logs go to database or console.
