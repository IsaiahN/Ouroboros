# Ouroboros Re-Architecture Overview

This plan synthesizes all DOCS materials (master rulesets, AGI Unified Theory, CODS, Games-as-Teachers, refactor plans, coherence reports, role fairness, operational philosophy, and reasoning logs). ARC API wiring and frame recovery remain unchanged. Database, sequence system, agent roles, and network substrate are preserved; gameplay control and learning flow are redesigned.

## Narrative Cohesion (what the system wants to be)
- Network is the organism; agents are temporary vessels. Knowledge lives in the database (viral packages, sequences, hypotheses, lessons).
- Generality emerges from a society of specialized agents (Two-Streams: w_A private memory, w_B collective wisdom). Self-determination requires explicit weighting per decision.
- Games are teachers: each level is a lesson to interpret, not a puzzle to memorize. Success = demonstrating understanding (transfer, abstraction), not just replay.
- CODS is the cognitive vocabulary: operators are earned, validated (RLVR), and proposed as action options; they are not inline heuristics.
- Dual economies: action budgets (metabolic) and prestige (social) stay separate. Roles gate permissions (pioneer, optimizer, generalist, exploiter) and action budgets.
- Evolution is the algorithm: variation/selection/heredity over knowledge packages and sequences; forgetting/decay preserves signal.

## Problems to Fix (from code reviews and logs)
- Monolith and exception soup hide failures; learning hooks silently fail.
- Replay contaminates live learning; mode separation is missing.
- Agents lack explicit w_A/w_B weighting and self-determination signals in action choice.
- Action selection mixes heuristics, logging, learning side-effects inline.
- Optimizer end-sequence gap; full-game sequences unused; sequence abstraction weak.
- Hook failures, operator usage, and lesson interpretations not recorded as data.
- Reasoning logs verbose but shallow; nulls instead of interpretations.

## Design Pillars
- Event-first architecture: gameplay loop emits events; plugins react and write to DB. No learning side-effects inline.
- Run modes: LIVE (writes learning), REPLAY_VALIDATION (validation-only), EVAL (telemetry-only). Enforced at plugin level.
- Proposal-based action selection: policies emit ActionProposal {action, weight_delta, evidence, source, w_A, w_B, mode_guard}; combiner samples; side-effects occur via events.
- Lesson-first telemetry: reasoning logs framed as student questions; lesson interpretations recorded with coverage/contradictions.
- Data-first governance: attempts table is the authoritative fitness record; hook_failures table for self-diagnosis; all artifacts reference attempt_id and mode.
- Preserve working pieces: ARC API, frame recovery, sequence retrieval reputation, database schema (extended only), agent roles/themes, network knowledge synthesis.

## Reliability Goals (airline-grade)
- Deterministic traces: every action and decision has attempt_id, step, mode, role, w_A, w_B, proposal sources, and ARC request/response recorded. No silent paths.
- Fail-fast with attribution: narrow exception scopes; all failures emit HookFailureDetected events and persist to hook_failures with stack_hash for bucketing and auto-disable logic.
- Dual-run hygiene: LIVE is the only mode allowed to write learning; REPLAY_VALIDATION and EVAL cannot mutate state, preventing contamination.
- Degraded but safe: if a plugin fails, it auto-disables and the core loop continues with minimal capability; safety rails (action budget guards, mode guards, role permissions) stay active.
- Watchdogs and heartbeats: per-attempt heartbeats (step counters) and per-plugin health checks; missing heartbeats trigger safe abort and hook_failure entries.
- Data invariants as contracts: DB constraints + code assertions on mode/tag presence, action budgets, and optimizer end-sequence completion; any violation becomes a recorded failure.

## Redundancy & Degrade Paths
- Action sources redundancy: if sequence replay unavailable, fall back to CODS operators; if CODS unavailable, fall back to heuristic/escape; if all fail, deterministic noop exit with recorded reason.
- Logging redundancy: action_proposals_log captures chosen and unchosen proposals; reasoning logs capture lesson framing; failures captured in hook_failures. Absence of any log is itself detectable via heartbeats.
- Data lineage redundancy: source_attempt_id/source_mode tags on sequences, packages, hypotheses, and lessons allow reconstruction even if one store is partial.
- Safety nets: budget guard, mode guard, role guard, and frame-diff sanity checks run independently; any guard triggering emits an event and records to hook_failures.
- Recovery: auto-disabled plugins can be re-enabled via DB flags after fixes; replay validation can be run against the same attempt payload to confirm fixes.

## Architecture Folder Map
- architecture/overview.md — top-level narrative and phases.
- architecture/diagrams.md — mermaid diagrams for runtime, events, data lineage, Two-Streams, lessons.
- architecture/runtime/README.md — loop split (init/step/post_step/finalize), event taxonomy, RunContext, heartbeats, mode guards.
- architecture/runtime/events.md — event payload schemas, guard codes, and expectations for bus consumers.
- architecture/runtime/side-effects-map.md — behavior-parity mapping of play_single_game side-effects to plugins/guards/events.
- architecture/data-contracts/README.md — additive tables (attempts, hook_failures, action_proposals_log, lesson_interpretations), invariants, source tags.
- architecture/data-contracts/migrations.md — additive migration plan, indices, rollout notes.
- architecture/reliability/README.md — failure modes, redundancy, degrade modes, watchdogs, operational playbooks.
- architecture/nfrs/README.md — NFR mapping (availability, reliability, performance, security, observability, governance, deployment).
- architecture/traceability/README.md — codebase responsibility map and alignment to architect questions.
- architecture/traceability/adr-index.md — tracked architecture decisions with status and consequences.
- architecture/code-disposition.md — keep/refactor/consolidate/retire map for root and manual_tools.
- architecture/refactor-plan.md — sequenced refactor steps from migrations to deprecation.
- Testing & Pycache: see architecture/refactor-plan.md for per-phase testing gates and python -B/PYTHONDONTWRITEBYTECODE requirements; reliability/README.md for operational checks against __pycache__.
- architecture/ci-pycache-testing.md — CI/runtime enforcement patterns for python -B, env flags, pycache scanning, and test commands.

## Core Artifacts to Add (additive migrations only)
- attempts: attempt_id, game_id, level, agent_id, role, mode, actions_used, levels_completed, score, time_ms, succeeded.
- hook_failures: hook_name, game_id, agent_id, generation, exception_type, message, stack_hash, timestamp, auto_disabled_flag.
- action_proposals_log: attempt_id, step, proposals (with w_A, w_B), chosen, available_actions, mode.
- lesson_interpretations: interpretation, explains_examples, fails_examples, confidence, source_attempt_id, game_id, level.
- Tag existing artifacts with source_attempt_id and source_mode (sequences, viral packages, hypotheses).

## Target Runtime Flow (high level)
- Orchestrator (thin): INIT → STEP → POST_STEP → FINALIZE; emits events only.
- Event bus: in-process dispatcher; no blocking. Plugins subscribe and write to DB.
- Plugins (toggleable via DB flags): Sequence, Viral, CODS, Hypothesis/Metacog, Prestige/Budget, HookFailureMonitor, Sensation/Self-Model.
- Action pipeline: proposal sources (sequence replay, CODS operator, heuristic/escape, role priors, random) → combiner → ACTION_CHOSEN event → execute via existing ARC API handler → ACTION_EXECUTED/FRAME_CHANGED events.
- Modes guard writes: only LIVE can mutate learning artifacts; REPLAY_VALIDATION logs validation only; EVAL logs telemetry only.

## Role & Two-Streams Enforcement
- Every decision logs w_A, w_B, role, mode, available_actions, chosen action, proposal sources.
- Roles keep permissions (pioneers frontier, optimizers beaten games, exploiters require sequences, generalists balanced with sensation).
- Dual economies remain separate; budgets computed per role; prestige affects trust, not access.

## Games-as-Teachers Integration
- Reframe Q1–Q9: "What is the teacher showing?" "What changed between examples?" "What am I asked to manipulate?" "Does my interpretation explain all examples?" (add Q9 self-test).
- Lesson interpretations stored per level/game; sequences become evidence, not the lesson itself.
- Win reflection → extract_lesson artifact linked to attempt_id.

## CODS Alignment
- Operators as vocabulary; proposals carry operator_id and validation status.
- RLVR validation recorded against attempt_id; unlocks gated by evidence.
- Curriculum tracker: per-game-type concept coverage and missing operators.

## Safety & Diagnostics
- Hook failures treated as data; auto-disable noisy hooks via DB flags after N failures.
- No bare except; narrow exception scopes; log to hook_failures.
- Replay hygiene: no learning writes in REPLAY_VALIDATION/EVAL.

## Phased Delivery (no code yet)
1) Instrumentation: add tables (attempts, hook_failures, action_proposals_log, lesson_interpretations); plumb mode in state.
2) Loop split: carve play_single_game into init/step/post_step/finalize; add event emission points; behavior-parity.
3) Action pipeline: proposal combiner; log proposals and w_A/w_B.
4) Mode enforcement + replay hygiene; tag artifacts with attempt_id and mode.
5) Plugin extraction; move side-effects out of core; hook auto-disable.
6) Games-as-Teachers reframing; lesson interpretations; reasoning log trim.
7) CODS curriculum wiring; operator usage telemetry; unlock gating via attempts.
8) Stabilize tests; regression on sequences, optimizer ends, full-game wins.

## What Stays Unchanged
- ARC API request/response handling and frame recovery.
- Existing sequence retrieval reputation logic (extended with source tags).
- Database core schema (only additive changes).
- Agent role definitions and budgets philosophy.

## References Mapped
- Master rulesets: `.github/copilot-instructions.md`, Ouroboros_Master_Ruleset.md
- AGI Unified Theory & Two-Streams: agi_unified_theory.md, two-streams.md
- CODS: Cognitive_Operator_Discovery_System.md
- Games-as-Teachers: games-as-teachers-paradigm.md
- Refactor & coherence: core_gameplay_refactor_plan.md, SYSTEM_COHERENCE_REPORT.md
- Operational priorities: operational_philosophy_and_10_questions.md, role_fairness_implementation_plan.md
- Reviews: code review.md, code review 2.md, code review 3.md
- Logs: [LOG] as66/ft09/lp85/ls20/sp80/vc33 reasoning logs
