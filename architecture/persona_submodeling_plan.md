# Persona Submodeling Implementation Plan (Checklists)

> Source: persona_submodeling_proposal.md. Use these checkboxes to track rollout. Leave unchecked until fully implemented and validated.

## Phase 1: Observers + Scorer Upgrade
- [x] Add observer personas emitting structured `observer_flags` (stuckness_level, control_loss, confidence_trend, pattern_tag, suggested_approach, veto_unsafe).
- [x] Persist richer observer data (extend outcomes or add observer log table; DB-only).
- [x] Compute and log `surprise_score` (distance from habits/persona bias).
- [x] Upgrade scorer: weighted score over confidence, safety_flag, persona_reliability, problem_signature match, budget_pressure, novelty_if_stalled, observer alerts; safe tie-break when losing, novel when stalled.
- [x] Stage gating: enable observers/scorer upgrade at stage ≥2.

## Phase 2: Synthesis Layer
- [x] Add synthesis persona type; produces synthesized proposal from proposals + observer flags.
- [x] Implement interpolation synthesis first; add dialectical/compositional hooks.
- [x] Safety: observer veto/unsafe check on synthesis; fall back to best single proposal.
- [x] Log synthesis provenance (persona_id for synthesis) and observer flags in proposals/outcomes.
- [x] Stage gating: synthesis on at stage ≥3.

## Phase 3: Problem Signatures + Context Reliability
- [x] Enrich `problem_signature` with perception/abstraction tags (grid, object types/count, symmetry/pattern class, control ratio, world_model tag).
- [x] Feed enriched signatures into scorer and context reliability updates; cache per frame hash.
- [x] Add problem-type classifier/strategy evaluator personas; log their proposals/outcomes.

## Phase 4: Hindsight Relabeling & Counterfactual Credit
- [x] Hindsight loop for all proposals (chosen/unchosen) with reduced-rate reliability updates.
- [x] Surprise-driven attribution: boost personas that better explain high-surprise outcomes.
- [x] Observer calibration: compare predicted vs retrospective stuckness/control; adjust observer reliability.
- [x] Integrate micro-rollout (3–5 step) signals as counterfactual credit input.
- [x] Optional `hindsight_relabeling` table (bounded) for retrospective credit storage.

## Phase 5: Lifecycle Rules & Spawning
- [x] Enhance persistence_class: thresholds by reliability + context coverage + age; diversity guard (keep at least one high-novelty core slot).
- [x] Auto-spawn/mutate personas on uncertainty/stall (bias drift), including synthesis personas.
- [x] Prune experimental personas with low reliability/usage; enforce minimum ensemble size.
- [x] Stage gating: lifecycle/diversity rules active at stage ≥3.

## Phase 6: Provenance & Network Integration
- [x] Tag sequence_abstraction outputs with persona_id and world_model; consume on replay/operator choice.
- [x] CODS: register persona-conditioned operators; use persona reliability in operator selection; prune failing persona-conditioned operators.
- [x] Network replication: publish high-reliability bias vectors (not names); decay/prune weak ones.

## Phase 7: Safety, Mentoring, Regression
- [x] Observer-driven veto path wired into action selection; fallback to safest proposal.
- [x] Mentoring/regression hooks (optional): mature agents share bias vectors; controlled regression if performance collapses.

## Cross-Cutting Safeguards (apply to all phases)
- [x] DB-only persistence via database_logger; no file logs; honor PYTHONDONTWRITEBYTECODE.
- [x] Stage gating for advanced features to prevent premature activation.
- [x] Budget guards: cap hindsight/counterfactual compute; skip synthesis when proposal count small or safety risk high.
- [x] Monitoring: metrics for hindsight credit volume, observer calibration error, synthesis win rate vs solo, counterfactual budget usage, core_ratio and diversity.
