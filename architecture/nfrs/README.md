# NFR Alignment and Quality Attributes

Mapping the architecture to non-functional requirements using the airline-grade reliability stance and the Think-Like-an-Architect steps.

## Business and Functional Context
- Mission: beat ARC 3 levels with real API calls (no mocks), preserving ARC wiring and frame recovery.
- Core functions: sequence discovery/replay, CODS operator discovery/validation, lesson interpretation, prestige/budget governance, role-based play (pioneer/optimizer/generalist/exploiter), and database-centric knowledge sharing.

## NFR Priorities and Implementation Hooks
- Availability and Reliability
  - Event-first loop with guards and heartbeats (see architecture/runtime).
  - hook_failures + auto-disable for noisy plugins; bounded retries on ARC API.
  - Safe abort on guard/heartbeat failure; deterministic noop exit when no safe action source.
- Scalability and Performance
  - In-process bus for minimal latency; plugins isolated to avoid blocking.
  - Data indices on attempts, hook_failures, action_proposals_log for fast analytics.
  - Sequence retrieval reputation stays cacheable; proposal pipeline is O(#sources) per step.
- Security and Trust
  - Modes enforce write permissions: only LIVE mutates learning; REPLAY_VALIDATION/EVAL are read-only.
  - Role guards prevent frontier access by optimizers/exploiters; prestige never mixed with budgets.
  - No log files; all telemetry stored in SQLite with provenance tags; PYTHONDONTWRITEBYTECODE=1.
- Observability
  - Deterministic traces via attempts + action_proposals_log; every event references attempt_id/mode/role/w_A/w_B.
  - Heartbeats per step; HOOK_FAILURE_DETECTED and MODE_VIOLATION events raise visibility.
  - Lesson interpretations capture coverage/contradictions; missing data is detectable.
- Maintainability and Evolvability
  - Behavior-parity refactor splits play_single_game into phases with plugins; side-effects removed from core.
  - Additive migrations only; source tags on all artifacts prevent drift.
  - ADR-style records can be added in architecture/traceability for decisions.
- Data Integrity and Governance
  - Invariants: budgets non-negative; chosen_action in available_actions; mode required on writes; optimizer sequences end in win actions.
  - Source_attempt_id/source_mode required for new artifacts; legacy rows tolerated but not produced.
- Deployment and Infrastructure (future-facing)
  - SQLite remains single source; WAL + vacuum via safe_cleanup; no file logs.
  - CI hooks should run investigate_bugs.py and replay validations before promotion.
  - Containerization/K8s out of scope now; bus and plugins are in-process to minimize operational complexity.
- API Contracts and Communication
  - ARC API client unchanged; contract is preserved.
  - Internal contract: orchestrator publishes events; plugins subscribe; no plugin may throw through bus.
  - RunContext is the API for phases; includes mode, role, budgets, w_A/w_B weights, sequence/operator sources.
- Documentation and Communication
  - architecture folder holds overview, diagrams, runtime, data-contracts, reliability, traceability (code map), and this NFR mapping.
  - Diagrams: see architecture/diagrams.md; add ADRs as decisions solidify.
- Iteration and Continuous Improvement
  - Phased delivery with behavior-parity first; replay validation for regressions; hook bucket analysis drives fixes; lessons/coverage track learning quality.
