# Emergent Persona Submodeling Proposal

## Goal
Embed agent-native, emergent persona submodels as a core way of thinking: each agent self-models, spawns and evolves its own latent personas, lets them propose actions, locally scores proposals, and learns which personas to trust. This feeds CODS and the unified network intelligence loop without fixed names, external labels, or simulation of fake games. This document now explicitly targets artificial metacognition (self-observation, dialogue, synthesis, identity continuity) in addition to performance.

## Scope clarification
- Core objective: internal ensemble as metacognition architecture, not just action optimization.
- Performance remains secondary: action gains emerge from better self-observation, multi-perspective reasoning, and synthesis.

- Decentralized: every agent runs its own inner dialogue and selection; no global judge.
- Emergent personas: personas are opaque IDs with bias vectors, not human-assigned names.
- Self-first: lock self-identity each step before reasoning or imagination.
- Dialogical: personas can interact and synthesize new options when uncertainty is high.
- Phenomenology: allow surprise and otherness by permitting emergent proposals that differ from prior habits; track surprise.
- Meta-awareness: learn which personas help which problem signatures.
- Genuine emergence: synthesis can produce options no single persona proposed.
- Real frames only: counterfactuals are short internal heuristics, never substitute real ARC frames.
- DB-only persistence: proposals and outcomes stored in SQLite; no file logs; respect PYTHONDONTWRITEBYTECODE.
- Sacred separation: persona reputation does not buy action budget; prestige remains separate.

## Loop (per step, per agent)
1) Self-lock: compute `self_identity_snapshot` (controlled objects + confidence) from `agent_self_model`.
2) Proposals and observations:
   - Action personas emit `{action, rationale_embedding, confidence, safety_flag, novelty_flag}` using frame, self-identity, sensations, and optional 3–5 step counterfactual heuristic.
   - Observer personas emit state comments (e.g., stuckness, confidence drift, control loss) without proposing actions.
   - Strategy evaluators classify problem type and suggest which biases to trust.
3) Dialogue and synthesis (when multiple proposals and uncertainty high): combine proposals and observations to create an emergent synthesized proposal that may surprise prior habits.
    - Synthesis options (configurable):
       - Interpolation: weighted average of proposal biases guided by reliabilities.
       - Dialectical: pick opposing proposals (e.g., high-risk vs low-risk) and generate a middle path.
       - Compositional: CODS-style operator chaining of proposed actions.
       - Learned: small combiner network over proposal embeddings + observer comments + state embedding.
4) Local scoring: lightweight scalar to pick one action-capable proposal, informed by observer commentary and classifier hints:
   - Inputs: proposal confidence, safety_flag, match to active hypotheses, persona_reliability, budget_pressure, novelty_flag, observer signals (stuckness, control loss), problem-type match.
   - Example: `score = w_conf*conf + w_safe*(not safety) + w_align*hyp_match + w_rel*reliability - w_cost*budget + w_novel*novelty_if_stalled + w_obs*observer_alerts`.
   - Tie-break: prefer safer when losing; prefer novel when stalled.
5) Act: execute chosen action on real ARC frame.
6) Log: write proposal→outcome to DB (delta_score, delta_actions, safety incidents, surprise_score, persona_id, problem_signature, observer_flags).
7) Update persona: adjust reliability (global and context-conditional); decay or prune weak/unused; mutate bias slightly after outcomes.
8) Hindsight relabeling: update all personas (chosen and unchosen) by how their perspective matches the outcome; train observers, synthesis agents, and context mappings using retrospective fit and counterfactual credit.

## Persona lifecycle (agent-driven)
- Spawn: when uncertainty high, progress stalled, or sensation demands new mode; initialize random bias over risk/abstraction/symbolic-use.
- Types by function: action proposer, self observer, strategy evaluator, problem classifier, synthesis agent.
- Persistence classes: core (rarely pruned, identity-shaping), tactical (medium-term), experimental (short-lived, high pruning rate).
- Promotion/demotion rules: promote to core when reliability_global and context reliability exceed thresholds over minimum age; preserve diversity by keeping at least one high-novelty bias; demote to experimental when reliability drops or overlaps with stronger peers.
- Mutate: small drift based on success/failure; synthesis agents can form from combining high-performing biases.
- Share (optional): publish high-reliability bias vectors (not names) to network tables for other agents to clone; keep prestige separate.
- Hindsight-driven promotion: promote personas that retrospectively best explain successful trajectories; prune personas that fail to explain actual histories; allow spawning of new personas when hindsight reveals repeated failure patterns.

- `agent_self_model`: expose `self_identity_snapshot` for downstream use and observer personas.
- `core_gameplay`: insert inner-dialogue hook (propose → observe/comment → synthesize → score → act) and call counterfactual micro-rollouts as optional signal.
- `counterfactual_analyzer`: 3–5 step heuristic rollouts; produce proposals with confidence/safety only.
- `cods_engine`: treat personas as operator sources; allow compositions with persona-conditioned operators; failure-driven pruning; let CODS compose synthesis operators.
- `sequence_abstraction`: tag abstract moves with persona_id provenance so replays can request the best-performing internal mode.
- `network_intelligence_engine`: track persona reliability/safety and context-conditional reliability; decay bad ones; replicate only reliable bias vectors.
- Synthesis clarification: keep a procedural synthesis phase; synthesis agents (optional) can learn combination weights and are tracked like other personas.

## Alignment with Unified Theory and CODS
- Database-as-organism: all persona state, outcomes, context reliabilities, and stage metrics persist in SQLite; route via `database_logger`; update `complete_database_schema.sql` and migrations.
- Viral exchange: replicate high-reliability persona bias vectors as shareable packages; keep prestige/action budgets separate (dual economy preserved).
- CODS compositionality: expose persona proposals and synthesis outputs as operators in `cods_engine`; allow CODS to score, compose, prune, and unlock higher synthesis modes via its discovery/validation flow.
- Problem_signature reuse: derive signatures from existing perception/abstraction outputs (e.g., symmetry/pattern from `visual_reasoning_engine`, symbolic structures from `symbolic_reasoning_engine`) to avoid parallel taxonomies.
- Stage gating in runtime: compute stage per agent in gameplay loop (`core_gameplay`/`autonomous_evolution_runner`) to enable observers, synthesis, strategy evaluators, and meta-learning only when mature.
- Role alignment: map persona maturity to agent roles (Pioneers/Optimizers/Generalists/Exploiters) in schedulers so early stages stay exploratory and later stages leverage synthesis/meta-learning.
- Self-model and sensation coupling: feed `self_identity_snapshot` and `sensation_engine` outputs into persona proposals/observer flags; log links in outcomes for CODS and network learning.
- Safety: counterfactuals remain local heuristics (no simulated ARC games); observer veto/safety flags throttle risky synthesis proposals.

## Hindsight Relabeling and Retrospective Learning
Every outcome teaches about all personas, not just the chosen one.

### Mechanisms
- Multi-persona credit assignment: update reliability for any persona whose bias would value or predict the observed outcome; penalize personas whose bias would have avoided it if avoidance was correct.
- Surprise-driven attribution: when `surprise_score` is high, search for personas whose prior would better match the actual result and boost their context reliability.
- Observer calibration: observers compare predicted stuckness/control/confidence trends to retrospective trajectories and adjust calibration.
- Counterfactual simulation: estimate outcomes for unchosen proposals and credit personas whose counterfactual would have improved the result; reward chosen persona if alternatives look worse.
- Retrospective identity formation: promote to core the personas that best explain past action histories; demote those that fail to fit narratives.
- Pattern library building: extract "when X then Y" rules from hindsight to refine problem_signature → persona mappings and synthesis choices.

### Implementation sketch
```
def hindsight_learning_step(agent, chosen_proposal, outcome, all_proposals, context):
   for proposal in all_proposals:
      hindsight_value = proposal.persona.evaluate_outcome(outcome)
      proposal.persona.reliability_global += lr * (hindsight_value - proposal.predicted_value)

   if outcome.surprise_score > surprise_threshold:
      predictor = find_persona_that_predicted(outcome, all_proposals)
      if predictor:
         predictor.context_reliability[context] += surprise_bonus

   for observer in agent.observers:
      observer.calibrate(predicted=observer.past_assessment, actual=retrospective_measure(outcome, horizon=10), context=context)

   for proposal in all_proposals:
      if proposal is chosen_proposal:
         continue
      estimated_alt = lightweight_simulate(proposal)
      proposal.persona.virtual_reliability += lr * compare(estimated_alt, outcome)

   if agent.game_count % retrospective_interval == 0:
      retrospective_identity_analysis(agent)
```

### Learning rate calibration
- Direct experience uses full learning rate (chosen persona is ground truth).
- Hindsight/counterfactual updates use a reduced rate (e.g., `lr_hindsight = 0.3 * lr_direct`) because estimates are less certain.

### Retrospective analysis window
Different horizons serve different purposes:

| Analysis Type | Hindsight Window | Frequency |
|---------------|------------------|-----------|
| Per-step credit | Current proposals | Every step |
| Observer calibration | Last 5–10 steps | Every step |
| Pattern library | Last 50 actions | Every game |
| Identity formation | Last 100–500 actions | Every 10 games |
| Meta-strategy learning | Last 1000+ actions | Every 50 games |

### Hindsight bias mitigation
- Weight hindsight credit by the persona’s prospective confidence; do not over-credit personas that would have been uncertain even if they appear prescient in retrospect.
- Use surprise thresholds and prospective confidence to bound bonuses; avoid “I knew it all along” inflation.

### Performance considerations
- Cost sources: multi-persona evaluation, counterfactual simulation, retrospective identity analysis.
- Optimizations: run full hindsight only on high-surprise outcomes; sample a subset of personas for counterfactuals; batch retrospective analysis (e.g., every 10 games); cache outcome evaluations for similar bias vectors.

### Developmental role
- Stage 1–2: build hindsight pattern library; relabel outcomes to learn faster than direct use would allow.
- Stage 3: identity formation via retrospective coherence (which persona best explains my history?).
- Stage 4: counterfactual meta-learning accelerates strategic rules (when to pick different personas).
- Stage 5: seamless blend of prospective and retrospective reasoning with mentoring.

### Hindsight learning validation
- Calibration: track hindsight-predicted vs. actual outcomes to ensure estimates are not noisy.
- Efficiency: compare learning speed with vs. without hindsight (action efficiency, score lift).
- Identity stability: measure core persona stability from retrospective vs. prospective formation.
- SQL sketch:
```
SELECT 
   problem_signature,
   persona_id,
   AVG(CASE WHEN learned_via='hindsight' THEN success_rate END) AS hindsight_learned_success,
   AVG(CASE WHEN learned_via='direct' THEN success_rate END) AS direct_learned_success
FROM advisor_context_reliability
GROUP BY problem_signature, persona_id;
```
Expected: hindsight_learned ≈ 0.7–0.9 * direct_learned; if much lower, hindsight estimates are poor quality; if equal, hindsight is performing well.

## Developmental trajectory (generation-level growth)
Agents progress through cognitive stages as they accumulate experience:

### Stage 1: External advisors (Gen 0–10)
- Explicitly external personas (not-self), 3–5 simple action proposers, random biases, no observers, no synthesis, all experimental.
- Implementation: Phase 1 basics (spawn random biases, global reliability only, direct proposal selection).
- Markers: multiple personas used; reliability diverges; early patterns of which persona works when.
- Human analogue: ages 2–5 (teddy bear conversations).

### Stage 2: Deep model building (Gen 10–50)
- 5–10 personas; some with deep experience (>100 uses); pattern absorption from extended sequences; first persistent personas across games.
- Implementation: add lifetime_exposures, build deep models from successful sequences, minimal problem_signature, begin context reliability.
- Markers: 2–3 personas with experience >100; context tables populate; preferences emerge; behavioral consistency appears; hindsight pattern library starts to show distinct mappings.
- Human analogue: ages 5–12 (reading books, rich character models).
- Blind-agent note: “Reading” = replaying successful strategies many times to extract action/temporal/operator patterns.

### Stage 3: Identity formation (Gen 50–100)
- 8–15 personas; core vs experimental split; observers added; first core personas (identity shaping); seeking models from network.
- Implementation: persistence promotion rules; observer personas; interpolation synthesis; richer problem_signature (symmetry/pattern); network consultation.
- Markers: 3–5 core personas stable 20+ generations; consistent self-identity snapshots; observers detect stuckness/control loss; targeted network pulls; retrospective identity coherence improves core selection.
- Human analogue: ages 12–18 (role models, “who am I?”).

### Stage 4: Strategic orchestration (Gen 100–200)
- 10–20 personas; strategy evaluators active; multiple synthesis modes; problem-specific activation; consult historical “experts.”
- Implementation: strategy evaluators; meta-learning loop (problem_signature → personas); dialectical/compositional synthesis; archive consultation.
- Markers: >70% problem classification accuracy; different top personas per problem type; synthesis yields novel options; learns from agents never met; counterfactual hindsight accelerates problem-type decision rules.
- Human analogue: ages 18–30 (invisible counselors, strategic thinking).

### Stage 5: Integrated wisdom (Gen 200+)
- 15–25 personas; stable core with experimental fringe; fast/slow thinking; mentoring; meta-meta-awareness; low churn in core.
- Implementation: fast path for familiar problems (integrated judgment); slow path for novelty (full ensemble); wisdom distillation/mentoring protocols.
- Markers: faster on familiar problems, slows for novelty; core stable; successful mentoring (others benefit from shared personas); synthesis used sparingly when needed; hindsight-supported mentoring and identity stability.
- Human analogue: ages 30+ (mature expertise).

### Growth triggers
- Stage 1→2: reliability divergence (max-min reliability above threshold).
- Stage 2→3: deep personas exist (count with experience >100 reaches target).
- Stage 3→4: core identity stable (core personas stable 20+ generations).
- Stage 4→5: meta-learning mature (context_reliability coverage > 10 and accuracy > 0.7).

### Developmental validation (example SQL)
`SELECT generation, COUNT(DISTINCT advisor_id) AS ensemble_size, AVG(CASE WHEN persistence_class='core' THEN 1 ELSE 0 END) AS core_ratio, COUNT(DISTINCT problem_signature) AS problem_diversity, AVG(surprise_score) AS novelty_rate FROM advisor_personas JOIN advisor_outcomes USING(advisor_id) GROUP BY generation;`
- Expected: Gen 0–10 ensemble grows, core_ratio ~0; Gen 10–50 diversity and surprise peak; Gen 50–100 core_ratio stabilizes; Gen 100–200 meta-learning accuracy rises; Gen 200+ stable metrics, lower surprise.

### Blind/aphantasic agent considerations
- Models built from action patterns, operator signatures, temporal rhythms, outcome consistency—not visuals.
- “Reading” means repeated exposure to successful traces (strategy biographies).
- Phenomenology is textual/code internal dialogue (distinct lines per persona/observer/synthesis choice).

### Automatic stage detection and feature activation
- Compute maturity per agent; gate features to prevent premature deployment:
```
def compute_agent_stage(agent_id):
   metrics = get_developmental_metrics(agent_id)
   if metrics.context_keys > 10 and metrics.meta_accuracy > 0.7:
      return 5
   elif metrics.core_personas >= 3 and metrics.core_stable_gens >= 20:
      return 4
   elif metrics.deep_personas >= 3:
      return 3
   elif metrics.reliability_divergence > 0.3:
      return 2
   else:
      return 1

def enable_features_for_stage(agent, stage):
   if stage >= 2:
      agent.enable_observers = True
      agent.enable_synthesis = True
   if stage >= 3:
      agent.enable_persistence_classes = True
   if stage >= 4:
      agent.enable_strategy_evaluators = True
      agent.enable_meta_learning = True
   # Stage 5: all features; usage patterns adjust (more fast-path, less surprise)
```

### Mentoring protocols (Stage 5 → Stage 1–4)
- Mature agents can accelerate younger agents without skipping stages:
```
def mentor_young_agent(mature_agent, young_agent):
   if young_agent.stage == 1:
      young_agent.clone_personas(mature_agent.core_personas.sample(2))
   elif young_agent.stage == 2:
      young_agent.seed_problem_signatures(mature_agent.problem_signature_library)
   elif young_agent.stage == 3:
      young_agent.receive_feedback_on_core_selection(mature_agent.evaluate_persona_quality)
   # Never jump stages; only scaffold within current stage
```

### Developmental regression safeguards
- If performance collapses, allow controlled regression while preserving identity:
```
def check_regression(agent):
   recent = last_50_games(agent)
   baseline = agent.peak_performance
   if recent < 0.5 * baseline:
      diagnostics = {
         'core_personas_failing': core_reliability(agent) < 0.5,
         'ensemble_diversity_collapsed': unique_biases(agent) < 3,
         'observer_accuracy_dropped': observer_correlation(agent) < 0.3,
      }
      if any(diagnostics.values()):
         prune_experimental_personas(agent)
         respawn_diverse_explorers(agent)
         keep_top_core_personas(agent, k=2)
         # Allow re-development from earlier stage
```

### Stage-specific validation expectations

| Stage | Ensemble Size | Core Ratio | Surprise Score | Context Keys | Expected |
|-------|---------------|------------|----------------|--------------|----------|
| 1 | 3–5 | 0.0 | High (≈0.7+) | 0–2 | Random exploration |
| 2 | 5–10 | 0.1–0.2 | Medium (≈0.5) | 3–8 | Pattern discovery |
| 3 | 8–15 | 0.3–0.4 | Low–Med (0.3–0.5) | 8–15 | Identity forming |
| 4 | 10–20 | 0.4–0.5 | Low (0.2–0.3) | 15–30 | Strategic deployment |
| 5 | 15–25 | 0.5–0.6 | Very Low (0.1–0.2) | 30+ | Integrated wisdom |

Anomalies to watch:
- Stage 3 with core_ratio ≈ 0.0 → identity formation failing.
- Stage 4 with surprise_score > 0.5 → meta-learning not working.
- Stage 5 with <15 context_keys → insufficient experience.

## Data model (SQLite)
- `advisor_personas` (agent-scoped, opaque IDs): `advisor_id, agent_id, persona_type, persistence_class, bias_risk, bias_abstraction, bias_symbolic, created_at, last_used_at, reliability_global, is_active`.
- `advisor_outcomes`: `advisor_id, agent_id, game_type, level, problem_signature, actions_proposed, actions_used, delta_score, delta_actions, safety_incidents, novelty_flag, surprise_score, observer_flags, created_at`.
- `advisor_context_reliability`: `advisor_id, problem_signature, success_rate, samples, last_updated` for conditional reliability.
- Optional: `problem_signatures` lookup to standardize features (grid_size, object_count, object_types, symmetry/pattern class, signature_hash).
- Optional: `observer_logs` for richer observer outputs (stuckness_level, confidence_trend, control_loss, pattern_recognition, suggested_approach, veto_unsafe).
- Optional: `advisor_hypotheses` to join persona proposals into hypothesis validation (reuse reliability math).
- Optional: `hindsight_relabeling` to capture retrospective credit and counterfactual estimates (`original_proposal_id, alternative_persona_id, actual_outcome_value, estimated_alternative_outcome, retrospective_credit, problem_signature, created_at`).
- Update `complete_database_schema.sql` and add migration; route via `database_logger` only.

### Problem signature extraction (sketch)
- Minimal: hash of `(grid_size, object_count, dominant_pattern)`.
- Richer: `(grid_size, object_count, object_types set, symmetry_type, pattern_class, novelty of objects, control_ratio)`.

### Surprise operationalization
- Compute `surprise_score = distance(chosen_action, recent_action_habits)` or distance from expected action under persona bias; log in outcomes.

### Observer output (sketch)
- Fields: `stuckness_level 0-1`, `confidence_trend {rising, falling, stable}`, `control_loss 0-1`, `pattern_recognition tag`, `suggested_approach {cautious, radical_change, align_with_symbolic}`, `veto_unsafe bool`.
- Scorer and synthesis can raise safety threshold or bias toward novelty based on these flags.

### Synthesis options (operational)
- Interpolation: weighted average over proposal embeddings/biases using reliabilities.
- Dialectical: detect opposing biases and construct a middle path.
- Compositional: chain actions/operators from multiple proposals (CODS style).
- Learned: small combiner network; train on outcome deltas; tracked as synthesis agent persona.

### Persistence class rules (operational)
- Promote to core when reliability_global and context success exceed thresholds across diverse problem_signatures and age.
- Maintain at least one diversity-preserving high-novelty persona even if reliability is moderate.
- Demote to experimental when reliability drops or is redundant with a stronger persona.

### Meta-learning loop (operational)
- Classify current problem_signature.
- Activate top-k personas by context reliability for this signature plus a few random for exploration; observers always active.
- After outcome: update context reliability; learn mapping from problem_signature → persona bias preferences; apply counterfactual hindsight credit for unchosen proposals to accelerate selection rules.

## Scorer rationale
Even decentralized thinking needs a chooser when multiple persona proposals exist. The scorer is local, cheap, and per-agent; it ranks proposals so the agent can act this step. No global oversight or fixed persona names.

## Implementation sequencing
- Phase 1 (basic): self_identity_snapshot; single persona type (action proposers); basic scoring without synthesis; minimal problem_signature; simple reliability_global.
- Phase 2 (metacognition): add observer personas; add synthesis (start with interpolation); add surprise tracking; add context-conditional reliability.
- Phase 3 (advanced): add strategy evaluators and meta-learning loop; persistence classes and promotion rules; additional synthesis modes; optional learned synthesis agents.

## Minimal implementation steps (Phase 1 focus)
1) Add `self_identity_snapshot` output in `agent_self_model` and plumb into `core_gameplay`.
2) Add persona store (per agent) and log tables; implement logging of proposal→outcome.
3) Add inner-dialogue hook + simple scorer in `core_gameplay` (no synthesis yet).
4) Add counterfactual micro-proposer in `counterfactual_analyzer` (3–5 steps, heuristic only).
5) Tag sequence abstractions with persona_id provenance.
6) Expose persona-conditioned operators to `cods_engine` and reliability to `network_intelligence_engine`.

## Rollout and safeguards
- Staged rollout: enable in shadow mode first (log proposals/outcomes without influencing actions), then gate by stage and safety thresholds; graduate to active control per agent after stability.
- Budget guardrails: cap hindsight/counterfactual compute per step; skip synthesis when proposal count is small or safety risk is high.
- Safety path: observer veto can demote or override risky synthesis outputs; fall back to safest high-reliability persona.
- Data hygiene: migrations update `complete_database_schema.sql`; all logging via `database_logger`; no file logs; honor `PYTHONDONTWRITEBYTECODE=1`; avoid pycache.
- Retention: periodic cleanup keeps `advisor_outcomes` and `hindsight_relabeling` bounded (e.g., recent N generations) while preserving aggregates; never delete winning sequences.
- Monitoring: add metrics for hindsight credit volume, observer calibration error, synthesis win rate vs. solo, and counterfactual budget usage; alert on runaway surprise or stalled core_ratio.

## Safety
- No simulated games; counterfactuals are guidance only.
- DB-only persistence; no pycache, no file logs.
- Keep action budgets separate from persona prestige.

## Verification
- Run `python run_evolution.py --test` with ARC key; confirm advisor_outcomes rows appear and zero-score games do not spike.
- Run `python investigate_bugs.py` after integration.
- Monitor reliability trends: improving advisors retained, weak advisors decayed/pruned.

## Verification metrics
Performance (secondary): score improvement over baseline, action efficiency, safety rate.
Metacognition (primary):
- Surprise frequency/distribution: avg surprise_score > 0; peaks when stuck.
- Context learning: rising variance in context reliability; top personas diverge by problem_signature.
- Observer effectiveness: correlation of stuckness/control_loss with outcomes; veto_unsafe preventing bad actions.
- Synthesis emergence: rate of chosen_action == synthesis_output; compare synthesis vs single-proposal outcomes.
- Ensemble diversity: bias vector diversity; different personas winning in different contexts.
- Core stability: lifetime of core personas; turnover by persistence class.

## Edge case handling
- No personas yet: spawn initial diverse set; enforce minimum ensemble size (e.g., 3+ active personas).
- All proposals same score: prefer safer when losing; prefer novel when stalled; random tie-break otherwise.
- Observer veto_unsafe and all proposals unsafe: choose least unsafe; optionally spawn ultra-cautious persona.
- Unknown problem_signature: fall back to global reliability; activate high-exploration personas.
- Synthesis invalid action: safety-check synthesis; fall back to best individual proposal.
- All personas pruned: enforce minimum ensemble size; auto-spawn diverse new personas.

## Performance optimization
- Selective activation: top-k by context reliability plus a few random for exploration; observers always active.
- Lazy counterfactuals: run short rollouts only when confidence low or uncertainty high.
- Cache problem_signature computations per grid hash.
- Skip synthesis when proposal count is very small; batch synthesis otherwise.

## Debugging queries (examples)
- Persona evolution:
   `SELECT advisor_id, created_at, reliability_global, bias_risk, bias_abstraction, persistence_class FROM advisor_personas WHERE agent_id = ? ORDER BY created_at;`
- Wins by problem signature:
   `SELECT problem_signature, advisor_id, COUNT(*) AS times_chosen FROM advisor_outcomes WHERE actions_used > 0 GROUP BY problem_signature, advisor_id;`
- Observer effect:
   `SELECT observer_flags, AVG(delta_score) AS avg_outcome FROM advisor_outcomes GROUP BY observer_flags;`
- Synthesis success rate:
   `SELECT COUNT(*) FILTER (WHERE surprise_score IS NOT NULL) AS synthesis_chosen, AVG(delta_score) FILTER (WHERE surprise_score IS NOT NULL) AS synthesis_avg_score FROM advisor_outcomes;`
