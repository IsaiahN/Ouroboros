# Integration Plan (Unified Theory Safe)

Scope: integrate recent ideas (action viability layer, hierarchical hypotheses, cross-domain transfer/resonance, ambiguity handling, parallel multi-domain learning, significance loop, problem decomposition heuristic) without violating AGI Unified Theory rules.

## Non-Negotiable Guardrails (from unified theory)
- Database is the organism: all persistence in SQLite (`core_data.db`); no log files; agents stateless/ephemeral.
- Dual economies: action budgets separate from prestige/trust; no coupling of resource access to prestige.
- Viral exchange: knowledge flows as portable packages (strategies/operators/concepts) with credibility and decay; avoid central controllers.
- Forgetting/compression: decay stale packages; favor abstraction and relevance to prevent bloat.
- Roles/adaptive populations: explorers/optimizers/generalists/exploiters mix; regulatory signals adjust ratios, not manual pinning.
- Pycache off: `PYTHONDONTWRITEBYTECODE=1` / `python -B`; no `__pycache__`; DB-only outputs.

## Integration Items (kept compliant)
- Action Viability Layer (pre-concept reflex): add fast “does anything happen?” gate before CODS; no ontology writes; DB-only telemetry; respects dual economies; no frame logs.
- Hierarchical hypothesis promotion: enforce simple→complex hypothesis ladder with promotion to beliefs and reuse; record in metacog tables; decay unused hypotheses to honor forgetting.
- Cross-domain pattern transfer: capture rotations/translations/progressions/containment as operators/meta-packages; tag resonance across domains; store as viral packages with decay/credibility.
- Significance hypothesis loop: “hypothesize significance → test across examples → promote to belief → guide search” wired into metacog experiment flow; no shortcutting dual economies.
- Problem decomposition heuristic: prioritize lowest-variability subproblems first; record as planner hint; DB-only; no hard-coded solutions.
- Multi-modal ambiguity resolution: use cross-constraints (vision/physics/motor/language) to resolve ambiguity; surface consensus vs accuracy metrics in dashboards; no extra writes beyond telemetry tables.
- Parallel multi-domain learning: scheduler encourages concurrent mixed-domain batches to promote transfer; still honors budgets/roles and avoids simulation/mocking.

## Work Plan
1) Action Viability Layer
- Add pre-CODS reflex module (affordance/heuristic mask) in core_gameplay loop; gate exploration when "no effect" predicted.
- Telemetry: record viability checks in action_proposals_log (DB-only); no ontology/concept writes.
- Guard: disabled in REPLAY_VALIDATION when pointers already defined; respects dual economies and mode gates.

2) Metacog Hypothesis Ladder
- Update metacog experiment logging: track simple hypotheses, promotions to beliefs, and decay of stale ones.
- Add dashboard slices for promotion rates and decay outcomes (no writes).
- Ensure viral package format used for shared hypotheses with relevance decay.

3) Cross-Domain Operators & Resonance
- Define operator templates for rotation/translation/progression/containment as meta-packages; store lineage/credibility/decay.
- Tag resonance across domains in action_proposals_log and dashboards; no log files.
- Compression: cluster similar operators when DB pressure rises; retain lineage to avoid orphaning.

4) Ambiguity & Multi-Modal Constraints
- Record parallel interpretations + consensus/dissent in observability-only paths; add consensus vs accuracy metrics to dashboards.
- Use existing resonance_tags/ladder traces—no new write-heavy tables; keep DB-only.

5) Problem Decomposition Heuristic
- Add planner hint to prefer lowest-variability subproblems first (optimizer/replay flows); log hint usage to DB.
- Ensure heuristic does not override dual economies or role guards.

6) Scheduler for Parallel Multi-Domain Learning
- Adjust scheduler to mix domains within budgeted slots; preserve role ratios and action budgets; no simulation.
- Monitor transfer via replay_health/reviewer dashboards; block if guard drift exceeds thresholds.

7) Governance & Safety Checks
- Mode gates: LIVE-only for writes (replay_index, world_model, sequences); observability-only elsewhere.
- Decay/forgetting: ensure new packages/hypotheses register decay fields; hook into safe_cleanup and compression routines.
- Pycache/log hygiene: rely on existing conftest guard; keep DB-only outputs; no file logs.

## Exit Criteria
- [x] Action viability layer present and mode-gated; no ontology/log-file writes.
- [x] Metacog ladder + significance loop captured in DB with decay; dashboards show promotion/decay metrics.
- [x] Cross-domain operator templates and resonance tags active without drift in guard/attempt metrics.
- [x] Ambiguity metrics (consensus vs accuracy) visible in dashboards; no extra write paths beyond telemetry.
- [x] Scheduler supports mixed-domain batches without breaking role/action budget rules or dual economies.
- [x] No __pycache__, no log files, database size within limits, decay/compression active.
