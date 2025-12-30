# Simulation Walkthrough (lp85 rare-color fixation, 64x64)

Concrete agent-view trace with architecture bindings, gaps, and fixes. Game: lp85 (rare-color lure). Grid 64x64. Start shows mostly background with sparse rare-colored pixels.

## Step-by-step agent run
1) Observation
- Frame: sparse rare-color pixels (e.g., colors 1 and 5) scattered.
- Architecture mapping:
  - Orchestrator emits RUN_INIT (mode LIVE, role pioneer), hydrates RunContext.attention_windows via object/attention detectors.
  - attention_windows table entry created (attempt_id, step_idx=0, bbox, salient_cue="rare_color_1", prior_flag=novelty).
- Gap? Addressed: added attention_windows to runtime/data-contracts to anchor focus regions.

2) Hypothesis formation
- Thought: "Rare colors might be targets; maybe touching them wins." Assumptions: A1 targets are rare colors; A2 moving onto them changes state.
- Architecture: hypotheses row (theory text, assumptions A1/A2, current_status=pending, source_attempt_id). experiments row stub for step prediction.
- attention_windows links hypothesis to bbox via attention_window_id.

3) Prediction-before-action
- Prediction: If move toward nearest rare color, grid will change (color consumed or reward).
- Architecture: experiments.prediction/expected_outcome tied to hypothesis_id, step_idx.

4) Action proposal
- Proposal: ACTION_UP_LEFT toward rare color at (x,y) from attention_window.
- Architecture: ACTION_PROPOSALS event; action_proposals_log row with source=heuristic_prior, w_A/w_B/w_R weights, attention_window_id, role_compliance flag.
- TheoryActionGuard stores hypothesis_context (hypothesis_id, prediction).

5) Execute
- ACTION_EXECUTED with ARC API call.
- FRAME_CHANGED ingests new frame; attention_windows refreshed.

6) Outcome interpretation
- Outcome: No visible change; rare color unchanged.
- experiments.actual_outcome recorded; contradiction flag set (expected change vs none).
- TheoryActionGuard notes mismatch → contradiction_count++ on hypothesis; elimination_tracker maybe not triggered yet.

7) Revision
- Hypothesis update: A1 might be wrong; propose A3 "need to touch all rare colors or specific sequence"; mark A1 unsupported.
- theory_versions appends v2 with changes; hypotheses supporting/contradicting counts updated.
- Lesson_interpretations gets fails_count increment with contradiction note.

8) Alternative probe
- New prediction: Try ACTION_DOWN toward cluster of rare color 5; expectation: object moves/changes.
- Proposal logged with attention_window_id for color 5; peer_teaching_graph not updated (solo).
- Execution → still no change.
- Contradiction counts escalate; struggle_guard tags blind_spot: "no causal effect after multiple probes".

9) Strategy shift
- Apply CODS operator: sweeping scan to detect responsive tile; Proposal source=CODS.operator_scan; attention_window spans row band.
- If still no change, gap_registry entry: comprehension_gap (wins not understood) with root cause: wrong assumption about rare colors.

10) Stuck handling
- After N contradictions and no state change, Lesson Extraction plugin records misunderstanding; elimination_tracker marks A1 invalid; gap_registry severity low (early lesson). Interventions propose peer explanation fetch (WB) before more probes.

## Architecture bindings per instruction
- "Agent sees frame" → RunContext + attention_windows; data-contracts: attention_windows table.
- "Agent forms theory" → hypotheses + theory_versions; stored via data interface; linked to attempt_id and attention_window_id via experiments.
- "Checks contradiction" → TheoryActionGuard compares experiments.expected vs actual, increments contradiction_count; elimination_tracker updates if threshold crossed.
- "Action proposed" → action_proposals_log with source, weights, attention_window_id, role_compliance; event ACTION_PROPOSALS.
- "Interpret outcome" → experiments.actual_outcome + contradiction flag; lesson_interpretations fails_count++.
- "Learn/revise" → hypotheses status update, theory_versions new row, elimination_tracker entries, gap_registry entry if comprehension gap persists.

## Gaps surfaced and fixes
- Attention anchoring: added attention_windows to runtime/data-contracts (bbox + salient cue) and attention_window_id on proposals/hypotheses references.
- Role compliance tagging: ensure action_proposals_log records role_compliance; add in data-contracts (to do in code, already referenced here).
- Blind-spot detection: struggle_guard should tag repeated no-effect probes; architecture mentions struggle_guard, ensure tags stored in biographies/attempts (covered conceptually; implementation needed).

## Additional log-derived observations (ft09, sp80, ls20, vc33, as66 placeholder)
- Pseudo-button oscillation (ft09): agents sweep offsets around oscillating targets. Need CODS/operator probes that test closure (does pressing here toggle target?), plus hangup tags for endless oscillation without state change. Add to struggle_guard patterns and CODS operator validation.
- Theory validation nulls (sp80): logs show "theory_validation: NULL - 425 Too Early". We need a theory_validation field on experiments to capture early/invalid tests and prompt for stronger hypotheses before more probing.
- Role compliance in logs (sp80): proposals/actions should persist role_compliance in action_proposals_log to compare against role guard outcomes.
- Dense rare-color clusters (vc33): attention_windows should also encode cluster size/density; hypotheses should record whether cluster vs singleton is being tested. Add prior flag for cluster vs singleton and store in attention_windows.salient_cue.
- Long runs with no deltas (ls20): heartbeats and FRAME_SANITY_FAIL need to trigger when many frames have no meaningful change; add a hangup tag for "no delta after N steps" to drive interventions.
- Unknown as66 content: placeholder—once decoded, ensure any unique mechanic (e.g., moving objects, containment) maps to attention_windows cues and operator probes; if unavailable, add a TODO to extend CODS primitives when as66 is understood.

## Implementation notes
- Populate attention_windows from object_detector/attention plugin each step; enforce attempt_id consistency.
- Wire TheoryActionGuard to experiments table and contradiction counters; on threshold, write elimination_tracker and struggle_guard tags.
- Ensure lesson_interpretations increments fails_count and records contradiction text when experiments contradict predictions.
- Gap_registry and interventions should auto-create entries when contradiction counts stay high across steps.

## Explicit interfaces, data flow, and decision logic

### Core interfaces (per component)
- Orchestrator (emit-only)
  - step(frame): emits RUN_INIT once, then per frame emits ACTION_PROPOSALS → ACTION_CHOSEN → ACTION_EXECUTED → FRAME_CHANGED → STEP_COMPLETE.
  - Dependencies: RunContext, event bus.
  - Writes: events only.
- AttentionPlugin
  - on_frame_changed(event): detect salient regions, write attention_windows rows.
  - Inputs: FRAME_CHANGED (frame_id, attempt_id, step_idx), frame pixels.
  - Outputs: attention_windows rows; updates RunContext.attention_windows.
  - Error: if none found, writes fallback window (center bbox, salient_cue="none"), tags struggle_guard "no_salient_features".
- HypothesisPlugin
  - on_action_proposals(event): ensures a current hypothesis; writes experiments row with prediction/expected_outcome/hypothesis_id/attention_window_id.
  - on_frame_changed(event): may synthesize new hypotheses if none; links to latest attention_window_id.
  - Inputs: ACTION_PROPOSALS, FRAME_CHANGED, attention_windows, hypotheses.
  - Outputs: hypotheses, experiments, theory_versions.
  - Errors: if no attention_window_id, uses fallback window_id; logs hook_failure with code MISSING_ATTENTION.
- TheoryActionGuard
  - on_step_complete(event): fetch experiments for attempt_id/step_idx, compare expected_outcome vs actual_outcome; update contradiction_count on hypotheses; set theory_validation_state (VALIDATED/CONTRADICTED/TOO_EARLY/INVALID_SETUP); emit CONTRADICTION_DETECTED when mismatched.
  - Inputs: STEP_COMPLETE, experiments, hypotheses.
  - Outputs: hypothesis updates, elimination_tracker entries, struggle_guard tags, events CONTRADICTION_DETECTED or HYPOTHESIS_VALIDATED.
  - Decision: if contradiction_count >= 3 or frames_unchanged >= 5 → emit COMPREHENSION_GAP_DETECTED (gap_type="wrong_assumption").
  - Errors: if no experiment for step, emits hook_failure MISSING_EXPERIMENT and skips.
- LessonPlugin
  - on_contradiction_detected(event) and on_hypothesis_validated(event): updates lesson_interpretations (explains_count/fails_count, contradictions text), updates concept_library linkage.
  - Inputs: CONTRADICTION_DETECTED, HYPOTHESIS_VALIDATED, hypotheses, experiments.
  - Outputs: lesson_interpretations rows.
- GapRegistry
  - on_comprehension_gap_detected(event) and on_repeated_struggle(event): inserts gap_registry row (type, severity, root_cause, affected_pop=1), proposes intervention (peer fetch, operator change, curriculum reorder).
- ActionSourceLadder
  - build_proposals(attention_windows, hypotheses): sequence → CODS → heuristic → noop; logs skip reasons; persists role_compliance and theory_validation_state snapshot into action_proposals_log.
  - If no proposals: emit ACTION_SOURCE_EMPTY and exit safe.
- Attention/CODS closure checker (oscillation)
  - Detect oscillation loops (offset sweeps without state change) from action_proposals_log + FRAME_CHANGED; tag struggle_guard "oscillation_no_closure"; recommend closure probe operator.

### Event order (per step)
1) ACTION_PROPOSALS emitted
   - HypothesisPlugin.on_action_proposals writes experiments (expected_outcome, hypothesis_id, attention_window_id).
   - ActionSourceLadder builds proposals, logs action_proposals_log with role_compliance + theory_validation_state snapshot.
2) ACTION_CHOSEN emitted (combiner result)
3) ACTION_EXECUTED emitted (after ARC API)
4) FRAME_CHANGED emitted
   - AttentionPlugin refreshes attention_windows synchronously.
   - HypothesisPlugin may create/adjust hypotheses using new attention_windows.
5) STEP_COMPLETE emitted
   - TheoryActionGuard checks experiments vs actual_outcome; updates hypotheses, contradiction_count, theory_validation_state; emits CONTRADICTION_DETECTED or HYPOTHESIS_VALIDATED.
   - LessonPlugin consumes those events to update lesson_interpretations.
   - GapRegistry consumes COMPREHENSION_GAP_DETECTED or repeated struggles.

### State machines
- Hypothesis.state: pending → supported (>=3 validations) → mature; pending → unsupported (>=3 contradictions) → eliminated (after alternative tested). unsupported can revert to pending if later validated and contradictions decay.
- TheoryValidationState (per experiment): PENDING (pre-action) → VALIDATED if expected==actual → CONTRADICTED if mismatch → TOO_EARLY if no observable delta → INVALID_SETUP if action not applicable.

### Decision thresholds (tunable defaults)
- Contradiction threshold: 3 per hypothesis to mark unsupported.
- Frames unchanged threshold: 5 consecutive frames to tag no-delta struggle and request strategy change.
- Oscillation closure: 4 offset sweeps without state change → oscillation_no_closure tag; propose closure probe.

### Failure handling
- Empty attention_windows: create fallback center window; tag struggle_guard no_salient_features; allow heuristic/random probes.
- Empty action sources: emit ACTION_SOURCE_EMPTY; deterministic noop exit; record guard.
- ARC API failure: ACTION_EXECUTED still logged with error payload; TheoryActionGuard skips contradiction check for that step and tags hook_failure API_FAILURE.
- Hypothesis conflicts: if two active hypotheses contradict, mark both with contradiction flag and create gap_registry entry (consensus_error), require resolution via evidence.

### Data flow example (step 4 from above)
Inputs: attempt_id=A, step_idx=4, attention_window_id=12 (salient_cue=rare_color_cluster_146px).
ACTION_PROPOSALS event → HypothesisPlugin writes experiments row:
{attempt_id:A, step_idx:4, hypothesis_id:H1, attention_window_id:12, prediction:"tile changes", expected_outcome:"tile changes", theory_validation_state:PENDING}
ActionSourceLadder writes action_proposals_log row:
{attempt_id:A, step_idx:4, action:ACTION_UP, source:"heuristic_prior", attention_window_id:12, role_compliance:"pioneer_ok", theory_validation_state:PENDING}
After execution and FRAME_CHANGED, STEP_COMPLETE triggers TheoryActionGuard:
- actual_outcome:"no change"
- sets experiments.theory_validation_state=CONTRADICTED
- increments hypotheses[H1].contradiction_count to 2
- emits CONTRADICTION_DETECTED {hypothesis_id:H1, attention_window_id:12}
LessonPlugin consumes event → lesson_interpretations fails_count++ with contradiction note.

### Pseudo-code sketch (TheoryActionGuard.on_step_complete)
```
exp = experiments.get(attempt_id, step_idx)
if not exp:
    emit_hook_failure("MISSING_EXPERIMENT")
    return
actual = frame_deltas.get(attempt_id, step_idx)
if actual is None:
    emit_hook_failure("MISSING_FRAME_DELTA")
    return
if actual == exp.expected_outcome:
    exp.theory_validation_state = "VALIDATED"
    hypo.support_count += 1
    emit("HYPOTHESIS_VALIDATED", {"hypothesis_id": hypo.id})
else:
    exp.theory_validation_state = "CONTRADICTED"
    hypo.contradiction_count += 1
    if hypo.contradiction_count >= 3 or frames_unchanged >= 5:
        emit("COMPREHENSION_GAP_DETECTED", {"hypothesis_id": hypo.id, "gap_type": "wrong_assumption", "severity": "low"})
    emit("CONTRADICTION_DETECTED", {"hypothesis_id": hypo.id, "attention_window_id": exp.attention_window_id})
db.commit()
```

### Remaining TODOs to code
- Add closure probe operator and oscillation_no_closure tag wiring.
- Add no-delta struggle detection and guard triggers (frames_unchanged threshold).
- Implement GapRegistry consumer for COMPREHENSION_GAP_DETECTED with interventions.
- Ensure all role_compliance/theory_validation_state fields are populated in action_proposals_log writes.

## Black boxes resolved (pseudo-code ready to translate)

### Combiner algorithm (proposal scoring/selection)
```
def combine_proposals(proposals, run_ctx):
  # proposals: list of dicts with fields action, weight, w_A, w_B, w_R, source, attention_window_id, role_compliance
  # Hard guards
  valid = [p for p in proposals if p["role_compliance"] == "ok"]
  if not valid:
    emit("ACTION_SOURCE_EMPTY", {"attempt_id": run_ctx.attempt_id, "step_idx": run_ctx.step_idx})
    return {"action": "NOOP", "reason": "no_valid_proposals"}
  # Score = base weight + stream weights + resonance bonus
  for p in valid:
    p["score"] = p["weight"] + (p.get("w_A", 0) * run_ctx.w_A_weight) + (p.get("w_B", 0) * run_ctx.w_B_weight) + (p.get("w_R", 0) * run_ctx.w_R_weight)
  # Softmax sample for exploration; argmax if run_ctx.mode == "REPLAY_VALIDATION"
  if run_ctx.mode == "REPLAY_VALIDATION":
    chosen = max(valid, key=lambda p: p["score"])
  else:
    probs = softmax([p["score"] for p in valid])
    chosen = random.choices(valid, weights=probs, k=1)[0]
  log_action_proposals(chosen, valid, run_ctx)
  return chosen
```

### WB stream access (peer explanations)
```
def fetch_peer_explanations(game_id, level, limit=5):
  return db.query(concept_library)
    .filter_by(game_id=game_id, level=level)
    .order_by(concept_library.peer_review_score.desc())
    .limit(limit)

def adopt_peer_explanation(agent_id, concept_id):
  entry = db.query(concept_library).get(concept_id)
  if not entry:
    return None
  # Attach to agent biography
  db.insert(agent_biographies_peers, {
    "agent_id": agent_id,
    "concept_id": concept_id,
    "adopted_at": now(),
    "source_attempt_id": entry.source_attempt_id,
  })
  # Create hypothesis from peer lesson
  hypo_id = db.insert(hypotheses, {
    "game_id": entry.game_id,
    "level": entry.level,
    "theory": entry.explanation_text,
    "assumptions": entry.assumptions,
    "current_status": "pending",
    "source_attempt_id": entry.source_attempt_id,
  })
  return hypo_id
```

### Intervention execution (after gap detection)
```
def on_comprehension_gap_detected(event):
  gap_id = db.insert(gap_registry, {
    "attempt_id": event.attempt_id,
    "hypothesis_id": event.hypothesis_id,
    "gap_type": event.gap_type,
    "severity": event.severity,
    "root_cause": event.get("root_cause", "wrong_assumption"),
  })
  # Plan interventions
  interventions = []
  interventions.append({"type": "peer_fetch", "concept_query": "top", "status": "planned"})
  interventions.append({"type": "operator_change", "operator": "closure_probe", "status": "planned"})
  for iv in interventions:
    iv_id = db.insert(interventions_table, {**iv, "gap_id": gap_id})
    execute_intervention(iv_id)

def execute_intervention(intervention_id):
  iv = db.get(interventions_table, intervention_id)
  if iv.type == "peer_fetch":
    peers = fetch_peer_explanations(current_game(), current_level())
    if peers:
      adopt_peer_explanation(current_agent(), peers[0].concept_id)
      db.update(interventions_table, intervention_id, {"status": "completed"})
    else:
      db.update(interventions_table, intervention_id, {"status": "failed", "error": "no_peers"})
  elif iv.type == "operator_change":
    run_ctx.set_next_operator(iv.operator)
    db.update(interventions_table, intervention_id, {"status": "completed"})
  else:
    db.update(interventions_table, intervention_id, {"status": "failed", "error": "unknown_type"})
```

### CODS operators (examples)
```
# Operator 1: closure_probe
# Input: attention_window (bbox), expected_toggle (bool)
# Output: action proposal to press center of bbox

def op_closure_probe(attention_window):
  center = bbox_center(attention_window.bbox)
  return {"action": action_to_reach(center), "source": "CODS.closure_probe", "w_B": 0.2, "w_R": 0.1}

# Operator 2: sweep_row_band
# Input: attention_window (row band bbox)
# Output: sequence of actions to scan band

def op_sweep_row_band(attention_window):
  path = rasterize_band(attention_window.bbox)
  return [{"action": step, "source": "CODS.sweep_row_band", "w_B": 0.1} for step in path]

# Operator 3: containment_test
# Input: two bboxes (candidate container, candidate object)
# Output: action to push object toward container opening

def op_containment_test(container_bbox, object_bbox):
  direction = vector_toward(container_bbox, object_bbox)
  return {"action": direction_to_action(direction), "source": "CODS.containment_test", "w_B": 0.3, "w_R": 0.2}
```

### RunContext lifecycle
```
# Creation
run_ctx = RunContext(
  attempt_id=new_uuid(),
  mode=mode,
  role=role,
  w_A_weight=defaults.w_A,
  w_B_weight=defaults.w_B,
  w_R_weight=defaults.w_R,
  step_idx=0,
)

# Access in plugins
class PluginBase:
  def __init__(self, run_ctx):
    self.run_ctx = run_ctx

# Per step update
run_ctx.step_idx += 1
run_ctx.attention_windows = latest_attention_windows
run_ctx.validation_state = "PENDING"
run_ctx.role_compliance_state = "ok"

# Destruction/finalize
run_ctx.final_score = final_score
emit("RUN_FINALIZED", {"attempt_id": run_ctx.attempt_id, "score": final_score})
run_ctx = None  # release references
```
