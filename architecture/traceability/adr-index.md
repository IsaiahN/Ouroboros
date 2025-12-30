# ADR Index (Architecture Decisions)

Decisions tracked to keep the refactor intentional and auditable. Status values: PROPOSED, ACCEPTED, REVISIT.

- ADR-001: Event Bus vs Inline Side-Effects — Status: ACCEPTED.
  - Decision: Use in-process publish/subscribe bus; orchestrator emits events; plugins handle side-effects.
  - Consequences: Lower coupling, clearer failure attribution; requires guard codes and idempotent plugins.

- ADR-002: Action Source Ladder — Status: ACCEPTED.
  - Decision: Sequence → CODS → Heuristic/Escape → Deterministic Noop Exit; every skip logged with reason.
  - Consequences: Deterministic degrade path; ensures no silent stalls; telemetry captures ladder position.

- ADR-003: Mode Hygiene — Status: ACCEPTED.
  - Decision: Only LIVE may write learning artifacts; REPLAY_VALIDATION/EVAL are telemetry-only; mode required on all writes.
  - Consequences: Prevents replay contamination; needs guard enforcement and MODE_VIOLATION events.

- ADR-004: Behavior-Parity Refactor Boundary — Status: PROPOSED.
  - Decision: Split play_single_game into INIT/STEP/POST_STEP/FINALIZE without changing decision logic; move side-effects behind bus incrementally.
  - Consequences: Safer migration; requires side-effect map and phased toggles.

- ADR-005: Data Provenance Tags — Status: ACCEPTED.
  - Decision: Add source_attempt_id/source_mode to sequences, viral packages, hypotheses, prestige logs.
  - Consequences: Enables lineage, replay validation, and blame assignment; requires additive migrations and interface updates.

- ADR-006: Guard Codes Canonical Set — Status: ACCEPTED.
  - Decision: Use standardized guard codes (BUDGET_EXHAUSTED, ROLE_VIOLATION, MODE_WRITE_BLOCKED, HEARTBEAT_LOST, ACTION_SOURCE_EMPTY, FRAME_SANITY_FAIL).
  - Consequences: Consistent telemetry, easier bucketed analysis; plugins must emit these codes.
