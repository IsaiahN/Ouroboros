# LEARNING FAILURE DIAGNOSTIC REPORT
**Date**: January 9, 2026  
**Based On**: Console logs and reasoning payloads from ft09 and vc33 gameplay sessions  
**Problem Statement**: Agents are not getting smarter despite 300+ generations of evolution

---

## EXECUTIVE SUMMARY

After analyzing actual gameplay logs, **agents are fundamentally not learning**. They have sophisticated reasoning payloads with all the right fields, but the values show:

1. **No actual learning is occurring** - Generation 303/304 agents still in "Preoperational exploration"
2. **CODS/Oracle is logging, not deciding** - Operators listed but not influencing action selection
3. **Network wisdom is returning empty defaults** - "No agent data - using defaults"
4. **Predictions consistently failing** - 143+ consecutive wrong predictions with no adaptation
5. **Hypotheses accumulating without effect** - 732 failure hypotheses but actions don't change

**Root Cause**: The cognitive systems are **observing** the game but not **controlling** decisions.

---

## SYMPTOM-BY-SYMPTOM ANALYSIS

### SYMPTOM 1: "PREDICTION WRONG" - 143 Consecutive Failures

**Console Evidence:**
```
[METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
[METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 143x consecutively
```

**What This Means:**
- Agent keeps predicting the same thing despite it failing 143 times
- The "suppression" just skips the prediction - doesn't learn a new strategy
- After suppression, agent continues doing the same actions

**What SHOULD Happen:**
- After ~10 failures, agent should REVISE the theory, not just suppress
- Learning should propagate: "frame_change predictions don't work for this game type"
- Network should receive "frame_change is unreliable for game X"

**Code Problem Location:**
- `agent_self_model.py`: Prediction suppression doesn't trigger theory revision
- No learning pathway from "suppressed prediction" → "revised strategy"

---

### SYMPTOM 2: "Theory Stage: Confident" BUT "SPECULATING" Everywhere

**Reasoning Payload (Frame 452):**
```json
"working_theory": "I control 1 objects and move with directional actions",
"theory_stage": "confident",
"control_confidence": 0.2,
"self_model_update": "SPECULATING: Object control not yet confirmed",
"theory_validation": "UNVALIDATED: Insufficient correlation data"
```

**The Contradiction:**
- `theory_stage = "confident"` (claims certainty)
- `control_confidence = 0.2` (20% confidence)
- `theory_validation = "UNVALIDATED"` (not confirmed)
- `control_source = "heuristic_guess"` (just guessing)

**What This Means:**
- The "confident" status is a LIE - the agent doesn't actually know anything
- Theory stage is not computed from actual validation
- Agent claims confidence while admitting it's speculating

**What SHOULD Happen:**
- `theory_stage` should be COMPUTED from `control_confidence` and `theory_validation`
- If `control_confidence < 0.5` AND `validation = UNVALIDATED` → `theory_stage = "exploring"`
- No claiming "confident" without evidence

**Code Problem Location:**
- `agent_self_model.py`: `theory_stage` is set independently from actual metrics
- No feedback loop: theory validation → stage revision

---

### SYMPTOM 3: "No Agent Data - Using Defaults"

**Reasoning Payload:**
```json
"4_network_wisdom": {
  "private_memory": 0.3,
  "network_strength": 0,
  "self_trust_bias": 0.5,
  "decision_weight": 0.5,
  "conflict_detected": false,
  "two_streams_narrative": "No agent data - using defaults"
}
```

**What This Means:**
- Stream A/B architecture is NOT working
- Network has ZERO strength (`network_strength: 0`)
- All decisions use hardcoded defaults (0.5 bias, 0.5 weight)
- No collective intelligence being accessed

**What SHOULD Happen:**
- After 300+ generations, network should have TONS of data
- `network_strength` should be high for beaten games/levels
- Stream A (private) should have actual memories
- Stream B (collective) should influence decisions

**Code Problem Location:**
- `network_intelligence_engine.py`: Not populating network wisdom properly
- Query returns empty, falls back to defaults
- Knowledge is stored but not retrieved

---

### SYMPTOM 4: Discoveries Made but Not Used

**Console Evidence:**
```
[DISCOVERY] Found control: obj_9 responds to ACTION4
[DISCOVERY] ACTION4 controls obj_9 (shared to network for ls20 L2)
[FRAME->SELF] ACTION4 caused color_9 to move right
```

**But Then:**
```
[MICRO-CF] micro rollout: probe salience
ACTION6 at (60, 12): micro rollout: probe salience | Visual: Grid exploration
```

**What This Means:**
- Agent DISCOVERS that ACTION4 controls obj_9
- Agent LOGS the discovery to network
- Agent immediately goes back to random probe salience with ACTION6
- Discovery has ZERO impact on behavior

**What SHOULD Happen:**
- Discovery → Immediate exploitation of new knowledge
- "I found ACTION4 controls obj_9" → "Let me USE ACTION4 to move obj_9"
- Discovery should change strategy, not just log

**Code Problem Location:**
- `agent_self_model.py`: `learn_from_movement_correlation()` stores but doesn't return to caller
- `core_gameplay.py`: Doesn't use discovery to override next action
- No pathway: Discovery → Action Selection

---

### SYMPTOM 5: 732 Failure Hypotheses But No Change

**Reasoning Payload:**
```json
"decision_contributors": {
  "cods_engine": 5,
  "failure_hypotheses": 732
}
```

**But Action Selection:**
```json
"reasoning": "Standard balanced strategy | ACTION6 salience target",
"based_on": "fallback_error"
```

**What This Means:**
- Agent has accumulated 732 failure hypotheses
- CODS engine contributed 5 operators
- But final action is "Standard balanced strategy" based on "fallback_error"
- All 732 hypotheses have ZERO influence on the decision

**What SHOULD Happen:**
- If 732 hypotheses exist, they should FILTER action choices
- "These 50 actions failed, avoid them" should constrain selection
- CODS operators should generate the action, not "salience target"

**Code Problem Location:**
- `core_gameplay.py`: Action selection ignores `failure_hypotheses`
- `cods_engine.py`: Operators logged but not integrated into decision
- Fallback path always wins

---

### SYMPTOM 6: Stuck Detection With No Recovery

**Reasoning Payload:**
```json
"active_beliefs": [
  {
    "id": "stuck_detection",
    "type": "stuckness", 
    "confidence": 0.9,
    "content": "Actions not causing frame changes for 47 frames"
  }
]
```

**What This Means:**
- Agent KNOWS it's stuck (0.9 confidence!)
- Agent has been stuck for 47 frames
- Agent continues doing the same thing

**What SHOULD Happen:**
- `stuck_detection.confidence > 0.7` → DRASTIC strategy change
- "I'm stuck" → Try completely different actions
- Stuck = signal to break pattern, not continue it

**Code Problem Location:**
- Stuck detection is computed but not acted upon
- No `if stuck_detected: change_strategy()`

---

### SYMPTOM 7: Optimizer Just Replays Blindly

**ft09 Reasoning Payload (All 63 Frames):**
```json
"reasoning": "OPTIMIZER replaying proven sequence seq_93f0 (target: L1)",
"role_compliance": "optimizer following sequence script"
```

**What This Means:**
- Optimizer is a "playback machine" - no actual thinking
- All 63 frames have identical reasoning
- No adaptation if replay fails
- No optimization happening, just replay

**What SHOULD Happen:**
- Optimizer should VALIDATE during replay
- If replay diverges from expected, adapt
- Track whether replay is actually optimal or just old

**Code Problem Location:**
- `core_gameplay.py`: Optimizer mode is pure replay
- No validation during replay
- No learning during optimization

---

## ROOT CAUSE ANALYSIS

### Problem 1: LOGGING vs LEARNING Confusion

The codebase conflates **logging** with **learning**:
- `[DISCOVERY] Found control` → Logged to database
- `[METACOG] PREDICTION WRONG` → Logged but not learned
- `[CODS] Testing operators` → Logged but not used for action

**Fix Required**: Learning must flow BACK to action selection, not just forward to storage.

### Problem 2: All Roads Lead to Fallback

Every decision path eventually hits a fallback:
```
try:
    sophisticated_decision()
except:
    return "fallback_error", default_action()
```

The "sophisticated" paths fail silently, fallback always executes.

**Fix Required**: Trace WHY sophisticated paths fail. Don't swallow errors.

### Problem 3: Metrics Computed But Not Used

Every frame computes:
- `control_confidence`
- `stuck_detection`
- `failure_hypotheses`
- `network_wisdom`
- `cods_operators`

But action selection uses: `"Standard balanced strategy | salience target"`

**Fix Required**: Decision function must be GATED by these metrics.

### Problem 4: No Feedback Loops

Knowledge flows in one direction:
```
Discovery → Database → (nothing)
Prediction → Wrong → Suppress → (continue same behavior)
Stuck → Detected → (ignore it)
```

**Fix Required**: Close the loops. Database → Query → Action. Wrong → Revise → Different action.

---

## SYMPTOM → CODE LOCATION MAP

| Symptom | File | Function | Problem |
|---------|------|----------|---------|
| 143 wrong predictions | `agent_self_model.py` | `_record_prediction_outcome()` | Suppresses but doesn't revise |
| Confident but speculating | `agent_self_model.py` | `_build_working_theory()` | Stage not computed from evidence |
| No agent data | `network_intelligence_engine.py` | `get_network_wisdom()` | Query returns empty |
| Discovery not used | `core_gameplay.py` | `_run_single_action()` | Doesn't use discovery result |
| 732 hypotheses ignored | `core_gameplay.py` | `_select_action()` | Fallback ignores hypotheses |
| Stuck but continues | `core_gameplay.py` | `_run_single_action()` | Stuck detection not checked |
| Optimizer blind replay | `core_gameplay.py` | `_run_optimizer_replay()` | No validation during replay |

---

## PRIORITY FIXES

### FIX 1: Discovery → Immediate Exploitation (CRITICAL)

When `learn_from_movement_correlation()` finds control:
1. RETURN the discovery to caller
2. Override next action to USE the discovery
3. Don't wait for next frame

### FIX 2: Prediction Failure → Strategy Revision (CRITICAL)

When prediction fails 10+ times:
1. Don't just suppress the prediction type
2. REVISE the theory that generated it
3. Try fundamentally different approach

### FIX 3: Stuck Detection → Recovery Mode (HIGH)

When `stuck_detection.confidence > 0.7`:
1. BREAK current strategy
2. Try random unexplored actions
3. Mark stuck state in network to warn others

### FIX 4: Network Wisdom Must Have Data (HIGH)

Query returns "No agent data" after 300 generations:
1. Debug why query is empty
2. Ensure knowledge is being RETRIEVED not just stored
3. Fall back to network defaults, not hardcoded 0.5

### FIX 5: Theory Stage Must Match Evidence (MEDIUM)

`theory_stage` must be computed:
```python
if control_confidence < 0.3:
    theory_stage = "exploring"
elif validation == "UNVALIDATED":
    theory_stage = "hypothesizing"  
elif validation == "VALIDATED":
    theory_stage = "confident"
```

---

## TESTING PROTOCOL

After each fix:
1. Run 2-3 games manually
2. Check reasoning payload shows DIFFERENT behavior
3. Verify: Discovery → Used, Stuck → Recovery, Hypothesis → Action
4. Only then commit to git

---

## CONCLUSION

The agents have all the **sensors** but none of the **actuators** are wired up. They can:
- ✅ Detect they're stuck
- ✅ Discover object control
- ✅ Accumulate failure hypotheses
- ✅ Compute network wisdom
- ✅ Run CODS operators

But they CANNOT:
- ❌ USE stuck detection to change behavior
- ❌ EXPLOIT discoveries immediately
- ❌ FILTER actions by failure hypotheses
- ❌ ACCESS network wisdom for decisions
- ❌ LET CODS operators select actions

**The cognitive architecture is observation-only. It needs to become decision-controlling.**

---

**Report Compiled By**: Autonomous Oracle (Claude)  
**Next Action**: Prioritize FIX 1 (Discovery → Exploitation) as it has clearest symptom and fix path
