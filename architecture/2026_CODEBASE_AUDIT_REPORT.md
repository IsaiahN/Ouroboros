# COMPREHENSIVE CODEBASE AUDIT REPORT

**Date**: January 9, 2026  
**Auditor**: GitHub Copilot (Claude Opus 4.5)  
**Scope**: Root folder Python files, with focus on `core_gameplay.py` and `agent_self_model.py`  
**Purpose**: Identify misalignments between unified theory (architecture docs) and implementation

---

## Summary: Theory vs. Implementation Misalignments

Based on reading the architecture documents and auditing the Python codebase, here are the **problems** - places where the implementation does NOT match the unified theory.

---

## 🔴 CRITICAL: Oracle/CODS Separation (User-Flagged Issue)

**Theory Says**: "CODS = Oracle (same centralized system)" - one unified system watching ALL agent gameplay

**Reality**:
- `oracle_interface.py` (936 lines) - Separate OracleInterface class
- `cods_engine.py` (5,294 lines) - Separate CODSEngine class that IMPORTS OracleInterface

In `cods_engine.py` line 41:
```python
from oracle_interface import OracleInterface, OracleVerdict
```

**Impact**: The theory explicitly states these should be THE SAME SYSTEM. Instead, Oracle is imported as a dependency into CODS. This violates the centralized watcher model.

---

## 🔴 CRITICAL: Stream A/B Architecture Not Implemented

**Theory Says**: 
- Stream A = Private experience (autobiographical memory, sensation engine, local discoveries)
- Stream B = Collective wisdom (network hypotheses, viral packages, proven sequences)
- Decision = w_A × memory(A) + w_B × wisdom(B) + w_R × resonance(R)
- I-Thread = persistent identity weaver integrating streams

**Reality**:
- `w_A_weight` and `w_B_weight` exist in `run_context.py` lines 46-48 and database schema
- They are logged to spine in `observability_plugins.py` lines 454-455
- But **no actual decision integration** - the weights are tracked but not used to make decisions

The WeavingReporter in `agent_self_model.py` lines 8487-8730 creates reports with:
```python
final_decision_weight = (
    private_memory_strength * alpha + 
    network_recommendation_strength * (1.0 - alpha)
)
```

But this is **only for LOGGING**, not for actual action selection. The reasoning payload shows stream weights but actions are NOT weighted by them.

**Missing**:
- No `I-Thread` implementation found anywhere
- No "Persona as Stream" architecture (Action Proposer = Stream A, Observer = Stream B personas)
- `two_streams_narrative` reference at line 16073 but implementation is just a label

---

## 🔴 CRITICAL: Roles as Fixed Assignments, Not Emergent Stances

**Theory Says**: 
- "Roles as cognitive stances expressed through Stream weighting"
- Pioneer = high w_A (trust self), Optimizer = high w_B (trust network)
- Roles should EMERGE from weights, not be assigned

**Reality** in `agent_operating_mode_system.py` lines 1-200:
- Roles are ASSIGNED based on population quotas:
  - `60% Pioneers in exploration phase`
  - `30% Optimizers`
  - `10% Generalists`
- Fixed `MODE_PARAMETERS` dict with hardcoded values
- `determine_agent_mode()` assigns modes, doesn't derive from w_A/w_B

**Impact**: The evolutionary/emergent behavior the theory describes is replaced with static assignment. An agent with high self_network_bias toward self doesn't automatically become a Pioneer - it's assigned.

---

## 🟠 MAJOR: Reasoning Payload Not Using Full Stream Architecture

**Theory Says**: Console/API reasoning should show:
- Stream A observations, Stream B recommendations
- I-Thread weaving, resonance detection
- Full persona ensemble deliberation

**Reality** in `core_gameplay.py` lines 14167-14700 (`_build_emergent_reasoning_context`):
- Q1-Q8 questions are implemented
- Q6 shows wA/wB weights but they're informational only
- No persona ensemble visible in reasoning
- No I-Thread narrative

The `send_action` in `arc_api_client.py` lines 618-620 accepts a `reasoning` kwarg but it's just a JSON blob without Stream structure:
```python
if "reasoning" in kwargs and kwargs["reasoning"]:
    payload["reasoning"] = kwargs["reasoning"]
```

---

## 🟠 MAJOR: Persona System Not Tied to Streams

**Theory Says**: 
- Personas split into Action Proposers (Stream A) and Observers/Evaluators (Stream B)
- Max 20 total personas, 7 active simultaneously
- Personas mediate stream integration

**Reality** in `persona_runtime.py` lines 1-300:
- `PersonaManager` class manages personas with budget
- `MAX_ACTIVE_PERSONAS = 12`, `MAX_TEMPORARY_PERSONAS = 5` (different from theory's 7/20)
- No Stream A/B categorization
- Personas are functional but NOT stream-integrated

---

## 🟠 MAJOR: Q1-Q5 Not Using Network Hypotheses Properly

**Theory Says**: Q4 (working theory) and Q8 (metacognitive) should integrate network hypotheses

**Reality** in `core_gameplay.py` lines 14264-14276 (`_analyze_cross_context_rules`):
- Q4 takes `hypothesis_biases` as parameter
- But network hypotheses are queried separately, not woven into reasoning
- `network_object_control_hypotheses` table exists with 6-tier validation
- But hypothesis usage feedback loop is incomplete

The 6-tier thought process (OBSERVATION → SHARING → VALIDATION → USAGE → SELECTION → SYNTHESIS) is partially implemented but not fully integrated with reasoning payloads.

---

## 🟠 MAJOR: Self-Model Discovery Not Connected to Q1 Properly

**Theory Says**: "I am this object" comprehension within 20 actions

**Reality** in `agent_self_model.py` lines 2014-2250:
- `execute_object_discovery()` correctly identifies controlled objects
- `learn_from_movement_correlation()` shares to network
- BUT: Q1 in reasoning shows "no actions observed to change state" despite discoveries

There's a FIX attempt at line 14600+ that tries to connect self-model discoveries to Q1:
```python
# FIX 3: CONNECT TO SELF-MODEL DISCOVERIES (CRITICAL)
```

But the connection is fragile and often fails, leaving Q1 disconnected from actual discoveries.

---

## 🟡 MODERATE: Prestige/Action Budget Separation Unclear

**Theory Says**: 
- PRESTIGE = Social capital (NEVER mixed with action budgets)
- ACTION BUDGETS = Economic capital

**Reality**:
- `prestige_engine.py` exists (not fully audited)
- `adaptive_action_limits.py` handles budgets
- But separation enforcement is not visible in core_gameplay.py

The "sacred separation" rule is in documentation but I didn't find explicit guards preventing mixing in the code.

---

## 🟡 MODERATE: Imagination Budget Not Visible in Reasoning

**Theory Says**: Agents should show imagination/mental modeling in reasoning

**Reality** in `core_gameplay.py` lines 16165-16175:
```python
imagination_ctx = getattr(self, '_imagination_ctx', {}) or {}
if imagination_ctx:
    context['imagination'] = {
        'budget_total': imagination_ctx.get('budget_total'),
        ...
    }
```

But `_imagination_ctx` is rarely populated. Most reasoning payloads have no imagination data.

---

## 🟡 MODERATE: Resonance Detection Present But Thin

**Theory Says**: 
- Resonance = cross-role pattern agreement (objective truth detector)
- w_R term in decision weighting

**Reality**:
- `w_R_weight` exists in run_context.py
- `_build_resonance_context()` method exists in core_gameplay.py
- But `w_R` is not used in actual decision formula

The resonance concept is acknowledged but not fully implemented in decision-making.

---

## 🟡 MODERATE: MetacognitiveReasoningEngine Q8 Not Blocking Actions

**Theory Says**: Q4, Q9, META questions can BLOCK normal proposals until resolved

**Reality** in `core_gameplay.py` line 8615:
```python
# Critical questions (Q4, Q9, META) can BLOCK normal proposals
```

This is a comment but the blocking mechanism is unclear. I didn't find consistent implementation of "question teeth" where unresolved questions prevent action proposals.

---

## 🟢 WORKING (Noted for completeness):

1. **Q1-Q8 Reasoning Framework** - Implemented and generating context
2. **Seed Primitives** - 110 primitives in `seed_primitives.py` via `PrimitiveHelper`
3. **WeavingReporter** - Creates per-action reflection reports
4. **Network Object Control Hypotheses** - 6-tier validation exists
5. **Action Trace Capture** - `_recent_action_traces` feeds Q1/Q5
6. **Tetrahedral Grammar** - Object interpretation axis implemented
7. **Database Schema** - 73+ tables for comprehensive tracking

---

## Recommendations for Priority Fixes

| Priority | Issue | Fix |
|----------|-------|-----|
| 1 | Oracle/CODS Separation | Merge Oracle into CODS - Single unified file, OracleInterface becomes methods in CODSEngine |
| 2 | Stream A/B Not Decision-Active | Implement I-Thread class that integrates Stream A/B with actual decision weighting |
| 3 | w_A/w_B Ignored | Action selection MUST use `decision = w_A * stream_A + w_B * stream_B` formula |
| 4 | Roles Fixed Not Emergent | Remove fixed assignment, let roles emerge from w_A/w_B ratios |
| 5 | Q1 ↔ Self-Model Broken | Discoveries should immediately update Q1 reasoning |
| 6 | Personas Not Stream-Typed | Add `stream_type` field to persona spawning (A=proposer, B=observer) |

---

## Files Audited

| File | Lines | Status |
|------|-------|--------|
| `core_gameplay.py` | 22,756 | Partially read (~10%) |
| `agent_self_model.py` | 12,957 | Partially read (~25%) |
| `oracle_interface.py` | 936 | Read first 300 lines |
| `cods_engine.py` | 5,294 | Read first 300 lines |
| `persona_runtime.py` | 1,163 | Read first 300 lines |
| `scientific_method_engine.py` | 2,111 | Read first 300 lines |
| `agent_operating_mode_system.py` | 1,733 | Read first 200 lines |
| `arc_api_client.py` | 699 | Read fully |
| `run_context.py` | ~80 | Read fully |
| `console_tags.py` | ~170 | Read fully |

---

## Methodology

1. Read architecture documents defining unified theory
2. Used grep_search to find key concepts in codebase
3. Read critical sections of core files
4. Compared theory requirements against actual implementation
5. Categorized issues by severity (Critical/Major/Moderate)
6. Noted working features for completeness

---

**END OF AUDIT REPORT**
