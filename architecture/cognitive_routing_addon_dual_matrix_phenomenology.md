# Cognitive Routing Addon: Dual-Matrix Architecture + Phenomenology Layer

**Created**: 2026-02-04
**Status**: PROPOSAL
**Prerequisite**: Phases 0-7.5 of cognitive_routing_implementation_plan.md (COMPLETE)
**Source**: [matrices.md](../DOCS/matrices.md), [phenomenology unpacked.md](../DOCS/phenomenology%20unpacked.md)

---

## Executive Summary

The cognitive routing implementation (Phases 0-7.5) successfully implemented the **Rumsfeld Matrix** as an epistemic state machine. However, two critical insights from recent analysis reveal opportunities for enhancement:

1. **Dual-Matrix Architecture**: Rumsfeld (divergent) answers "what do we know?" but we need Eisenhower (convergent) to answer "what should we do NOW?" The current system selects algorithms but doesn't explicitly prioritize tasks by urgency × importance.

2. **Phenomenology Layer**: Experience isn't something added to data—it's the compressed output. Our system already compresses high-dimensional state to `(action, confidence, reason)`, but this compression is implicit, not fed back, and doesn't encode urgency/valence in the representation itself.

This addon proposes **Phase 8: Dual-Matrix Integration** and **Phase 9: Phenomenology Layer**.

**Combined effect**: The system doesn't just track "what it knows" (Rumsfeld) and "what to do about it" (Eisenhower). It also tracks "how it feels about all this" (Phenomenology) and uses that feeling to modulate behavior.

This creates **three layers of metacognition**:
1. **Epistemic**: What's my knowledge state? (Rumsfeld)
2. **Pragmatic**: What's urgent and important? (Eisenhower)
3. **Affective**: What's my compressed feeling about this situation? (Phenomenology)

All three feed back into the next cycle. The system doesn't just think—it thinks about its thinking, prioritizes its priorities, and feels its way through uncertainty.

---

## The Gap Analysis

### Current Architecture (Post Phase 7.5)

```
Frame Arrives
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPISTEMIC TRACKER                             │
│  (Rumsfeld Matrix: KK/KU/UK/UU as state machine)                │
│  "What do we know? What don't we know?"                         │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ Epistemic quadrant determines algorithm
┌─────────────────────────────────────────────────────────────────┐
│                    META-PLANNER                                  │
│  Algorithm selection based on quadrant + domain                  │
│  (TargetedQuestionSearch, RetrievalSearch, etc.)                │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ Algorithm returns candidate rungs
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE ROUTER                              │
│  Selects best rung from candidates                              │
│  Executes rung, updates blackboard                              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
(action, confidence, reason) → ARC API
```

### The Missing Layers

**Gap 1: No Eisenhower Prioritization**

The algorithm returns multiple candidate rungs. Currently selection is based on:
- Edge trust weights
- Domain matching
- Path crystallization

But NOT based on:
- **Urgency**: Is this needed for the NEXT action, or can it wait?
- **Importance**: Does this impact winning, or just builds understanding?

**Concrete Example**: In a KU state with 5 open questions:

| Question | Urgent? | Important? | Eisenhower Action |
|----------|---------|------------|-------------------|
| "What do I control?" | YES (can't act without it) | YES (fundamental) | **DO NOW** |
| "Is this physics or symbolic?" | NO (can infer later) | YES (affects strategy) | **SCHEDULE** |
| "What's the goal state?" | YES (directs all actions) | YES (critical) | **DO NOW** |
| "Does this rule generalize?" | YES (about to use it) | MEDIUM | **DELEGATE** (background rung) |
| "What opened that door?" | NO | NO (curiosity) | **ELIMINATE** |

Without Eisenhower, we'd treat all 5 questions equally. With it, we focus on the 2 "DO NOW" questions first.

**Gap 2: Implicit Compression Without Feedback**

The system compresses state to action, but:
- Compression is scattered across components, not explicit
- Compressed state doesn't feed back into next cycle
- Urgency/valence isn't part of the encoding—it's looked up

---

## Phase 8: Dual-Matrix Integration

### 8.1 The Dual-Matrix Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│              RUMSFELD LAYER (Divergent)                         │
│  "What do we know? What are we missing?"                        │
│                                                                  │
│   KK: Known Knowns      → Exploit confidently                   │
│   KU: Known Unknowns    → Research these questions              │
│   UK: Unknown Knowns    → Retrieve cached knowledge             │
│   UU: Unknown Unknowns  → Explore cautiously                    │
│                                                                  │
│   OUTPUT: List of potential tasks/rungs                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              EISENHOWER LAYER (Convergent)                      │
│  "What should we do RIGHT NOW?"                                 │
│                                                                  │
│           │ URGENT              │ NOT URGENT                    │
│   ────────┼─────────────────────┼─────────────────────          │
│   IMPORT- │ Q1: DO NOW          │ Q2: SCHEDULE                  │
│   ANT     │ (Execute this rung) │ (Queue for later)             │
│   ────────┼─────────────────────┼─────────────────────          │
│   NOT     │ Q3: DELEGATE        │ Q4: ELIMINATE                 │
│   IMPORT- │ (Use heuristic/     │ (Don't waste actions)         │
│   ANT     │  cached sequence)   │                               │
│                                                                  │
│   OUTPUT: Single prioritized action                             │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Urgency and Importance Definitions

**Urgency** (time pressure dimension):
- **URGENT**: Result needed for immediate next action
  - Game state is volatile (objects moving)
  - Low action budget remaining (<20% of level budget)
  - Blocking another agent's sequence (multiplayer consideration)
  - Cascade failure imminent (pattern breaking down)

- **NOT URGENT**: Can be deferred without penalty
  - Game state is stable
  - Abundant action budget remaining
  - Information is "nice to have" not "need to know"
  - Building long-term understanding

**Importance** (impact dimension):
- **IMPORTANT**: Directly impacts winning probability
  - Answers a KU question blocking progress
  - Validates/invalidates current theory
  - Unlocks new action possibilities
  - High edge trust from past wins

- **NOT IMPORTANT**: Low impact on outcomes
  - Already have good enough understanding
  - Marginal improvement to known strategy
  - Exploratory curiosity with low expected payoff
  - Redundant with existing knowledge

### 8.3 Eisenhower Quadrant Actions

```python
# engines/cognition/eisenhower_layer.py

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple

class EisenhowerQuadrant(Enum):
    Q1_DO = "do_now"           # Urgent + Important
    Q2_SCHEDULE = "schedule"    # Not Urgent + Important
    Q3_DELEGATE = "delegate"    # Urgent + Not Important
    Q4_ELIMINATE = "eliminate"  # Not Urgent + Not Important

@dataclass
class UrgencyScore:
    """Computed urgency based on game state and resources."""
    budget_pressure: float      # 0-1: how depleted is action budget
    volatility: float           # 0-1: how fast is game state changing
    blocking_factor: float      # 0-1: is this blocking other progress
    cascade_risk: float         # 0-1: will delay cause cascade failure

    @property
    def total(self) -> float:
        # Weighted combination, max of critical factors
        return max(
            self.budget_pressure * 0.4 + self.volatility * 0.3 +
            self.blocking_factor * 0.2 + self.cascade_risk * 0.1,
            self.cascade_risk  # Cascade risk alone can make urgent
        )

    @property
    def is_urgent(self) -> bool:
        return self.total > 0.6

@dataclass
class ImportanceScore:
    """Computed importance based on expected impact."""
    win_probability_delta: float  # How much does this affect P(win)
    theory_validation: float      # Does this confirm/deny working theory
    action_unlock: float          # Does this enable new actions
    edge_trust: float             # Historical success of this path

    @property
    def total(self) -> float:
        return (
            self.win_probability_delta * 0.4 +
            self.theory_validation * 0.3 +
            self.action_unlock * 0.2 +
            self.edge_trust * 0.1
        )

    @property
    def is_important(self) -> bool:
        return self.total > 0.5

@dataclass
class PrioritizedTask:
    """A task with Eisenhower classification."""
    rung_name: str
    urgency: UrgencyScore
    importance: ImportanceScore
    quadrant: EisenhowerQuadrant
    source_rumsfeld_quadrant: str  # Which KK/KU/UK/UU generated this

    @classmethod
    def classify(cls, rung_name: str, urgency: UrgencyScore,
                 importance: ImportanceScore, source: str) -> 'PrioritizedTask':
        if urgency.is_urgent and importance.is_important:
            quadrant = EisenhowerQuadrant.Q1_DO
        elif not urgency.is_urgent and importance.is_important:
            quadrant = EisenhowerQuadrant.Q2_SCHEDULE
        elif urgency.is_urgent and not importance.is_important:
            quadrant = EisenhowerQuadrant.Q3_DELEGATE
        else:
            quadrant = EisenhowerQuadrant.Q4_ELIMINATE

        return cls(rung_name, urgency, importance, quadrant, source)

class EisenhowerLayer:
    """
    Convergent layer that prioritizes tasks from Rumsfeld analysis.

    Takes the divergent output (many possibilities) and converges to
    a single prioritized action based on urgency × importance.
    """

    def __init__(self, blackboard: 'Blackboard'):
        self.blackboard = blackboard
        self.scheduled_queue: List[PrioritizedTask] = []

    def compute_urgency(self, rung_name: str) -> UrgencyScore:
        """Compute urgency for a candidate rung."""
        # Budget pressure
        budget_used = self.blackboard.get('actions_taken', 0)
        budget_total = self.blackboard.get('action_budget', 400)
        budget_pressure = budget_used / budget_total if budget_total > 0 else 0

        # Volatility - how much has changed recently
        frame_delta = self.blackboard.get('frame_delta_magnitude', 0)
        volatility = min(frame_delta / 100, 1.0)  # Normalize

        # Blocking factor - are other processes waiting on this
        pending_questions = len(self.blackboard.get('open_questions', []))
        blocking_questions = self.blackboard.get('blocking_questions', [])
        is_blocking = rung_name in blocking_questions
        blocking_factor = 0.8 if is_blocking else min(pending_questions / 5, 1.0)

        # Cascade risk - will delay break current strategy
        strategy_stability = self.blackboard.get('strategy_stability', 1.0)
        cascade_risk = 1.0 - strategy_stability

        return UrgencyScore(
            budget_pressure=budget_pressure,
            volatility=volatility,
            blocking_factor=blocking_factor,
            cascade_risk=cascade_risk
        )

    def compute_importance(self, rung_name: str,
                           edge_trust: float = 0.5) -> ImportanceScore:
        """Compute importance for a candidate rung."""
        # Win probability delta - how much does this rung typically help
        rung_win_contribution = self.blackboard.get(
            f'rung_win_contribution_{rung_name}', 0.1
        )

        # Information gain - how much do we learn from this rung
        expected_info_gain = self.blackboard.get(
            f'expected_info_gain_{rung_name}', 0.3
        )

        # Theory validation - does this test our working theory
        has_theory = self.blackboard.get('working_theory') is not None
        rung_tests_theory = rung_name in [
            'theory_gate', 'hypothesis_testing', 'scientific_method'
        ]
        theory_validation = 0.8 if has_theory and rung_tests_theory else 0.2

        # Action unlock - does this enable new capabilities
        rung_unlocks = {
            'survey': 0.9,           # Unlocks everything
            'control_tracker': 0.8,  # Unlocks control-based actions
            'palette_detection': 0.7, # Unlocks color-based reasoning
        }
        action_unlock = rung_unlocks.get(rung_name, 0.3)

        return ImportanceScore(
            win_probability_delta=rung_win_contribution,
            theory_validation=theory_validation,
            action_unlock=action_unlock,
            edge_trust=edge_trust
        )

    def prioritize(self, candidate_rungs: List[Tuple[str, float]]) -> Optional[str]:
        """
        Take candidate rungs from Rumsfeld/algorithm layer,
        prioritize using Eisenhower matrix, return best action.

        Args:
            candidate_rungs: List of (rung_name, edge_trust) tuples

        Returns:
            Best rung to execute, or None if all should be eliminated
        """
        tasks = []
        for rung_name, edge_trust in candidate_rungs:
            urgency = self.compute_urgency(rung_name)
            importance = self.compute_importance(rung_name, edge_trust)
            source = self.blackboard.get('epistemic_quadrant', 'UU')

            task = PrioritizedTask.classify(
                rung_name, urgency, importance, source
            )
            tasks.append(task)

        # Sort by quadrant priority: Q1 > Q2 > Q3 > Q4
        # Within quadrant, sort by combined score
        def priority_key(t: PrioritizedTask) -> Tuple[int, float]:
            quadrant_priority = {
                EisenhowerQuadrant.Q1_DO: 0,
                EisenhowerQuadrant.Q2_SCHEDULE: 1,
                EisenhowerQuadrant.Q3_DELEGATE: 2,
                EisenhowerQuadrant.Q4_ELIMINATE: 3,
            }
            return (
                quadrant_priority[t.quadrant],
                -(t.urgency.total + t.importance.total)  # Negative for descending
            )

        tasks.sort(key=priority_key)

        if not tasks:
            return None

        best = tasks[0]

        # Handle based on quadrant
        if best.quadrant == EisenhowerQuadrant.Q1_DO:
            return best.rung_name

        elif best.quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
            # Add to queue, but still execute if nothing better
            self.scheduled_queue.append(best)
            return best.rung_name

        elif best.quadrant == EisenhowerQuadrant.Q3_DELEGATE:
            # Use cached/heuristic path instead of full analysis
            cached = self.blackboard.get(f'cached_sequence_{best.rung_name}')
            if cached:
                return cached[0]  # First action from cached sequence
            return best.rung_name

        else:  # Q4_ELIMINATE
            # Check scheduled queue for something better
            if self.scheduled_queue:
                scheduled = self.scheduled_queue.pop(0)
                return scheduled.rung_name
            # Nothing to do - maybe trigger exploration
            return 'exploration_phase'

    def gate_single_rung(self, rung_name: str, edge_trust: float) -> Tuple[EisenhowerQuadrant, Optional[str]]:
        """
        Evaluate a single rung as a gate before execution.

        This is the ITERATIVE version - called before EACH rung execution,
        not just once per cycle. After executing a rung, the blackboard
        changes, so we re-evaluate remaining candidates.

        Returns:
            (quadrant, action_to_take)
            - Q1_DO: (Q1_DO, rung_name) - execute this rung
            - Q2_SCHEDULE: (Q2_SCHEDULE, None) - skip, added to queue
            - Q3_DELEGATE: (Q3_DELEGATE, cached_action) - use cached path
            - Q4_ELIMINATE: (Q4_ELIMINATE, None) - discard entirely
        """
        urgency = self.compute_urgency(rung_name)
        importance = self.compute_importance(rung_name, edge_trust)
        source = self.blackboard.get('epistemic_quadrant', 'UU')

        task = PrioritizedTask.classify(rung_name, urgency, importance, source)

        if task.quadrant == EisenhowerQuadrant.Q1_DO:
            return (EisenhowerQuadrant.Q1_DO, rung_name)

        elif task.quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
            self.scheduled_queue.append(task)
            return (EisenhowerQuadrant.Q2_SCHEDULE, None)

        elif task.quadrant == EisenhowerQuadrant.Q3_DELEGATE:
            cached = self.blackboard.get(f'cached_sequence_{rung_name}')
            if cached:
                return (EisenhowerQuadrant.Q3_DELEGATE, cached[0])
            # No cache, fall through to execute
            return (EisenhowerQuadrant.Q3_DELEGATE, rung_name)

        else:  # Q4_ELIMINATE
            return (EisenhowerQuadrant.Q4_ELIMINATE, None)

    # --- Scheduled Queue Management ---

    MAX_SCHEDULED_QUEUE: int = 10  # Prevent unbounded growth
    AGING_RATE: float = 0.05       # Urgency increase per cycle

    def age_scheduled_queue(self) -> None:
        """
        Age items in scheduled queue - older items become more urgent.

        Called at the start of each routing cycle. Items that have been
        waiting gain urgency, potentially promoting Q2 to Q1.
        """
        aged_tasks = []
        for task in self.scheduled_queue:
            # Increase urgency due to waiting
            new_urgency = UrgencyScore(
                budget_pressure=min(1.0, task.urgency.budget_pressure + self.AGING_RATE),
                volatility=task.urgency.volatility,  # Doesn't age
                blocking_factor=min(1.0, task.urgency.blocking_factor + self.AGING_RATE * 0.5),
                cascade_risk=min(1.0, task.urgency.cascade_risk + self.AGING_RATE * 0.5)
            )

            # Reclassify with new urgency
            aged_task = PrioritizedTask.classify(
                task.rung_name, new_urgency, task.importance, task.source
            )
            aged_tasks.append(aged_task)

        # Replace queue with aged versions
        self.scheduled_queue = aged_tasks

        # Handle overflow - keep highest priority
        if len(self.scheduled_queue) > self.MAX_SCHEDULED_QUEUE:
            self.scheduled_queue.sort(
                key=lambda t: -(t.urgency.total + t.importance.total)
            )
            dropped = self.scheduled_queue[self.MAX_SCHEDULED_QUEUE:]
            self.scheduled_queue = self.scheduled_queue[:self.MAX_SCHEDULED_QUEUE]

            # Log what was dropped for debugging
            for task in dropped:
                self.blackboard.append_to(
                    'dropped_scheduled_tasks',
                    {'rung': task.rung_name, 'reason': 'queue_overflow'}
                )

    def pop_promoted_task(self) -> Optional[str]:
        """
        Check if any scheduled task has been promoted to Q1 through aging.

        Returns:
            Rung name if a Q1 task is available, None otherwise.
        """
        for i, task in enumerate(self.scheduled_queue):
            if task.quadrant == EisenhowerQuadrant.Q1_DO:
                self.scheduled_queue.pop(i)
                return task.rung_name
        return None

    def handle_all_eliminate(self) -> str:
        """
        Handle edge case where all candidates are Q4_ELIMINATE.

        This is a system health issue - we shouldn't normally be
        generating only useless candidates.

        Returns:
            A fallback rung to execute.
        """
        # Log the issue
        self.blackboard.append_to(
            'system_health_events',
            {
                'type': 'all_eliminate',
                'tick': self.blackboard.get('tick', 0),
                'message': 'All candidates classified as Q4_ELIMINATE'
            }
        )

        # Priority 1: Check scheduled queue
        if self.scheduled_queue:
            return self.scheduled_queue.pop(0).rung_name

        # Priority 2: Check for promoted tasks
        promoted = self.pop_promoted_task()
        if promoted:
            return promoted

        # Priority 3: Explicit exploration
        return 'exploration_phase'
```

### 8.4 Integration with Existing Pipeline (Iterative Gate Pattern)

```python
# Modification to engines/cognition/cognitive_router.py

class CognitiveRouter:
    def __init__(self, ...):
        # ... existing initialization ...
        self.eisenhower = EisenhowerLayer(self.blackboard)

    def route(self, frame: Frame) -> RoutingDecision:
        # 0. NEW: Age scheduled queue at start of cycle
        self.eisenhower.age_scheduled_queue()

        # 0.1. NEW: Check for promoted tasks from aging
        promoted = self.eisenhower.pop_promoted_task()
        if promoted:
            result = self.execute_rung(promoted)
            # Continue with normal routing after handling promoted task

        # 1. Update epistemic state (Rumsfeld layer - already implemented)
        self.epistemic_tracker.update(frame, self.blackboard)
        quadrant = self.epistemic_tracker.current_quadrant

        # 2. Get algorithm based on epistemic state (already implemented)
        algorithm = self.meta_planner.select_algorithm(quadrant, context)

        # 3. Get candidate rungs from algorithm (already implemented)
        candidates = algorithm.get_next_rungs(context)

        # 4. NEW: Iterative Eisenhower gate pattern
        # Re-evaluate after each execution because blackboard changes
        executed_rungs = []
        candidate_tuples = [
            (rung, self.graph.get_edge_trust(rung))
            for rung in candidates
        ]

        # Track if ALL candidates are eliminated
        all_eliminated = True

        for rung_name, edge_trust in candidate_tuples:
            # Gate check with CURRENT blackboard state
            quadrant_result, action = self.eisenhower.gate_single_rung(
                rung_name, edge_trust
            )

            if quadrant_result == EisenhowerQuadrant.Q1_DO:
                all_eliminated = False
                # Execute and update blackboard
                result = self.execute_rung(action)
                executed_rungs.append((rung_name, result))
                # Blackboard is now updated - next iteration sees new state

            elif quadrant_result == EisenhowerQuadrant.Q2_SCHEDULE:
                all_eliminated = False  # Scheduled counts as "not eliminated"
                # Skip for now, already added to queue
                continue

            elif quadrant_result == EisenhowerQuadrant.Q3_DELEGATE:
                all_eliminated = False
                if action:  # Cached action available
                    result = self.execute_rung(action)
                    executed_rungs.append((rung_name, result))
                # else: skip, no cache available

            else:  # Q4_ELIMINATE
                # Discard entirely
                continue

        # 4.1. NEW: Handle all-eliminate edge case
        if all_eliminated and not executed_rungs:
            fallback = self.eisenhower.handle_all_eliminate()
            result = self.execute_rung(fallback)
            executed_rungs.append((fallback, result))

        # 5. Return results from all executed rungs
        return self.compile_routing_decision(executed_rungs)
```

**Key insight**: After executing rung R1, the blackboard changes. When we evaluate R2, its urgency/importance may have shifted:
- R1 might have answered R2's question → R2 becomes ELIMINATE
- R1 might have increased time pressure → R2 becomes more URGENT
- R1 might have provided cached sequence → R3 becomes DELEGATE

### 8.5 Cross-Matrix Mapping

The Rumsfeld quadrant influences the Eisenhower classification:

| Rumsfeld Quadrant | Typical Eisenhower Mapping | Rationale |
|-------------------|---------------------------|-----------|
| **KK** (Known Knowns) | Often Q1 or Q3 | We know what to do—either do it (important) or delegate to cached sequence (not important) |
| **KU** (Known Unknowns) | Often Q1 or Q2 | Questions are important, urgency depends on blocking factor |
| **UK** (Unknown Knowns) | Often Q2 or Q3 | Retrieval is important but rarely urgent |
| **UU** (Unknown Unknowns) | Often Q2 or Q4 | Exploration is important long-term but rarely urgent; eliminate if wasting actions |

```python
RUMSFELD_TO_EISENHOWER_BIAS = {
    'KK': {'importance_boost': 0.1, 'urgency_boost': 0.2},  # Trust what we know
    'KU': {'importance_boost': 0.2, 'urgency_boost': 0.0},  # Questions are important
    'UK': {'importance_boost': 0.1, 'urgency_boost': -0.1}, # Retrieval can wait
    'UU': {'importance_boost': 0.0, 'urgency_boost': -0.2}, # Exploration is not urgent
}
```

---

## Phase 9: Phenomenology Layer

### 9.1 The Core Insight

From the phenomenology analysis:

> "Phenomenology is the compressed output. The JPEG of captured input."

Our system already compresses high-dimensional state (100+ blackboard slots, epistemic quadrant, graph evolution, algorithm state) to low-dimensional output `(action, confidence, reason)`. But this compression is:
- **Implicit**: Scattered across components
- **One-way**: Doesn't feed back into next cycle
- **Value-neutral**: Urgency/valence looked up, not encoded

The insight is that **feeling IS the format**. Pain doesn't represent damage then add "bad"—pain IS the representation of damage in a format that includes urgency.

### 9.2 FeltState: The Compressed Representation

```python
# engines/cognition/phenomenology_layer.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time

class Valence(Enum):
    """Core felt quality of current state."""
    THREAT = "threat"           # Something is wrong, act NOW
    OPPORTUNITY = "opportunity" # Something is possible, explore
    STABILITY = "stability"     # All is well, continue
    CONFUSION = "confusion"     # Don't understand, pause/gather
    BOREDOM = "boredom"         # Nothing happening, seek novelty


@dataclass
class FeltStateTraceEntry:
    """Debug trace entry for 'why did it feel this way?'"""
    tick: int
    felt_state: 'FeltState'
    raw_valence_score: float
    dominant_contributors: List[str]
    blackboard_snapshot: Dict[str, Any]

    def explain(self) -> str:
        """Human-readable explanation of this felt state."""
        return (
            f"Tick {self.tick}: Felt {self.felt_state.valence.value} because: "
            f"{', '.join(self.dominant_contributors)}. "
            f"Raw score: {self.raw_valence_score:.2f}, "
            f"Certainty: {self.felt_state.certainty:.2f}, "
            f"Agency: {self.felt_state.agency:.2f}"
        )


class FeltStateStabilizer:
    """
    Prevents FeltState thrashing (THREAT→STABILITY→THREAT oscillation).

    Uses confirmation counts and cooldowns, similar to epistemic hysteresis.
    """

    # Confirmation required before transition
    VALENCE_CONFIRMATION_REQUIRED = {
        (Valence.STABILITY, Valence.THREAT): 2,    # Need 2 signals before panic
        (Valence.THREAT, Valence.STABILITY): 3,    # Need 3 signals to calm down
        (Valence.CONFUSION, Valence.STABILITY): 2, # Need 2 signals to feel stable
        (Valence.BOREDOM, Valence.THREAT): 1,      # Instant panic from boredom
    }

    # Cooldown after transition (cycles before can transition again)
    TRANSITION_COOLDOWN = 3

    def __init__(self):
        self.pending_valence: Optional[Valence] = None
        self.confirmation_count: int = 0
        self.cooldown_remaining: int = 0

    def stabilize(self, raw_felt: 'FeltState', previous_felt: Optional['FeltState']) -> 'FeltState':
        """Apply hysteresis to prevent thrashing."""
        if previous_felt is None:
            return raw_felt

        # Decrement cooldown
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            # Force previous valence during cooldown
            return FeltState(
                valence=previous_felt.valence,
                arousal=raw_felt.arousal,
                certainty=raw_felt.certainty,
                agency=raw_felt.agency,
                salience=raw_felt.salience,
                momentum=raw_felt.momentum,
                compression_ratio=raw_felt.compression_ratio,
                dominant_contributors=raw_felt.dominant_contributors,
            )

        # Check if valence is trying to change
        if raw_felt.valence != previous_felt.valence:
            transition = (previous_felt.valence, raw_felt.valence)
            required = self.VALENCE_CONFIRMATION_REQUIRED.get(transition, 1)

            if self.pending_valence == raw_felt.valence:
                self.confirmation_count += 1
            else:
                self.pending_valence = raw_felt.valence
                self.confirmation_count = 1

            if self.confirmation_count >= required:
                # Transition confirmed
                self.cooldown_remaining = self.TRANSITION_COOLDOWN
                self.pending_valence = None
                self.confirmation_count = 0
                return raw_felt
            else:
                # Not enough confirmations, keep previous valence
                return FeltState(
                    valence=previous_felt.valence,
                    arousal=raw_felt.arousal,
                    certainty=raw_felt.certainty,
                    agency=raw_felt.agency,
                    salience=raw_felt.salience,
                    momentum=raw_felt.momentum,
                    compression_ratio=raw_felt.compression_ratio,
                    dominant_contributors=raw_felt.dominant_contributors,
                )

        # No change
        self.pending_valence = None
        self.confirmation_count = 0
        return raw_felt


@dataclass
class FeltState:
    """
    Low-dimensional compression of full system state.

    This is NOT metadata about the state—it IS the state,
    in a format that includes urgency and valence.

    Like pain encoding "STOP" in the representation itself,
    not "damage data" + separate "urgency lookup".
    """

    # Core dimensions (5D summary of 100+D state)
    valence: Valence                  # Overall felt quality
    arousal: float                    # 0-1: energy/activation level
    certainty: float                  # 0-1: how confident are we
    agency: float                     # 0-1: do we feel in control
    salience: float                   # 0-1: how attention-grabbing

    # Temporal dimension
    momentum: float                   # -1 to 1: getting better or worse

    # The compression loss acknowledgment
    compression_ratio: float          # How much info was lost
    dominant_contributors: list       # Which slots dominated the compression

    def to_urgency_bias(self) -> float:
        """
        Convert felt state to urgency bias for Eisenhower layer.

        THREAT + high arousal = high urgency
        STABILITY + low arousal = low urgency
        """
        valence_urgency = {
            Valence.THREAT: 0.8,
            Valence.CONFUSION: 0.5,
            Valence.OPPORTUNITY: 0.3,
            Valence.STABILITY: 0.1,
            Valence.BOREDOM: 0.0,
        }
        base = valence_urgency[self.valence]
        return base * self.arousal

    def to_importance_bias(self) -> float:
        """
        Convert felt state to importance bias for Eisenhower layer.

        High certainty + high agency = exploit (important)
        Low certainty + high salience = investigate (important)
        """
        if self.certainty > 0.7 and self.agency > 0.7:
            return 0.8  # We know what to do and can do it
        if self.certainty < 0.3 and self.salience > 0.7:
            return 0.7  # We don't know, but this matters
        if self.momentum < -0.3:
            return 0.6  # Things are getting worse
        return 0.4  # Default moderate importance


class PhenomenologyLayer:
    """
    Explicit compression layer that:
    1. Compresses full blackboard to FeltState
    2. Injects FeltState back into blackboard for next cycle
    3. Uses valence-tagged priorities in the encoding itself

    This creates the feedback loop that might be consciousness-like:
    High-D state → Compress → Summary → Feed back → High-D state → ...
    """

    MAX_COMPRESSION_MS = 5  # Performance budget: must complete in 5ms

    def __init__(self, blackboard: 'Blackboard'):
        self.blackboard = blackboard
        self.previous_felt: Optional[FeltState] = None
        self.history: list = []
        self.stabilizer = FeltStateStabilizer()
        self.trace_log: List['FeltStateTraceEntry'] = []

    def compress(self) -> FeltState:
        """
        Compress full blackboard state to 5D FeltState.

        This is lossy BY DESIGN. The ineffability of experience
        is the information loss in this compression.
        """
        import time
        start = time.perf_counter()

        # COLD START: First cycle has no previous state
        if self.previous_felt is None:
            felt = FeltState(
                valence=Valence.CONFUSION,  # Don't know anything yet
                arousal=0.5,
                certainty=0.2,
                agency=0.3,
                salience=0.7,  # Everything is novel
                momentum=0.0,
                compression_ratio=0.0,
                dominant_contributors=['cold_start'],
            )
            self._log_trace(felt, 0.0)
            return felt

        # Compute valence from multiple signals
        valence = self._compute_valence()

        # Compute arousal from activity level
        arousal = self._compute_arousal()

        # Compute certainty from epistemic state
        certainty = self._compute_certainty()

        # Compute agency from control signals
        agency = self._compute_agency()

        # Compute salience from attention signals
        salience = self._compute_salience()

        # Compute momentum from history
        momentum = self._compute_momentum()

        # Track what dominated the compression
        contributors = self._get_dominant_contributors()

        # Estimate compression ratio
        slots_with_data = sum(
            1 for slot in self.blackboard.slots.values()
            if slot.value is not None
        )
        compression_ratio = slots_with_data / 5.0  # 5 output dimensions

        raw_felt = FeltState(
            valence=valence,
            arousal=arousal,
            certainty=certainty,
            agency=agency,
            salience=salience,
            momentum=momentum,
            compression_ratio=compression_ratio,
            dominant_contributors=contributors,
        )

        # Apply hysteresis to prevent valence thrashing
        felt = self.stabilizer.stabilize(raw_felt, self.previous_felt)

        # Performance guard
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > self.MAX_COMPRESSION_MS:
            # Log warning - compression is too slow
            self.blackboard.write('phenomenology_slow', True)

        # Log trace for debugging
        raw_score = self._compute_raw_valence_score()
        self._log_trace(felt, raw_score)

        return felt

    def _log_trace(self, felt: FeltState, raw_score: float) -> None:
        """Log trace entry for debugging 'why did it feel this way?'"""
        entry = FeltStateTraceEntry(
            tick=self.blackboard.get('current_tick', 0),
            felt_state=felt,
            raw_valence_score=raw_score,
            dominant_contributors=felt.dominant_contributors,
            blackboard_snapshot={
                'epistemic_quadrant': self.blackboard.get('epistemic_quadrant'),
                'contradiction_detected': self.blackboard.get('contradiction_detected'),
                'controlled_object': self.blackboard.get('controlled_object') is not None,
                'working_theory': self.blackboard.get('working_theory') is not None,
            }
        )
        self.trace_log.append(entry)
        if len(self.trace_log) > 500:
            self.trace_log = self.trace_log[-500:]

    def inject(self, felt: FeltState) -> None:
        """
        Feed compressed state back into blackboard.

        This closes the loop: the system's compressed self-perception
        influences its next cycle of processing.
        """
        # Store as "felt_*" slots that rungs can read
        self.blackboard.write('felt_valence', felt.valence.value,
                              source='phenomenology', confidence=0.9)
        self.blackboard.write('felt_arousal', felt.arousal,
                              source='phenomenology', confidence=0.9)
        self.blackboard.write('felt_certainty', felt.certainty,
                              source='phenomenology', confidence=0.9)
        self.blackboard.write('felt_agency', felt.agency,
                              source='phenomenology', confidence=0.9)
        self.blackboard.write('felt_salience', felt.salience,
                              source='phenomenology', confidence=0.9)
        self.blackboard.write('felt_momentum', felt.momentum,
                              source='phenomenology', confidence=0.9)

        # Store in history for momentum calculation
        self.history.append(felt)
        if len(self.history) > 100:
            self.history = self.history[-100:]

        self.previous_felt = felt

    def _compute_valence(self) -> Valence:
        """
        Determine overall felt quality.

        Uses a composite score approach that considers multiple signals,
        then maps to discrete Valence category.
        """
        # Compute raw valence score (continuous -1 to 1)
        raw_score = self._compute_raw_valence_score()

        # Map to discrete Valence based on score and specific triggers
        # THREAT signals override score
        if self.blackboard.get('contradiction_detected', False):
            return Valence.THREAT
        if self.blackboard.get('cascade_failure', False):
            return Valence.THREAT
        if self.blackboard.get('action_budget_critical', False):
            return Valence.THREAT

        # Score-based mapping
        if raw_score < -0.3:
            return Valence.THREAT
        elif raw_score > 0.3:
            return Valence.OPPORTUNITY

        # CONFUSION signals
        epistemic = self.blackboard.get('epistemic_quadrant', 'UU')
        if epistemic == 'UU':
            return Valence.CONFUSION

        # BOREDOM signals
        if self.blackboard.get('no_change_frames', 0) > 10:
            return Valence.BOREDOM

        # Default
        return Valence.STABILITY

    def _compute_raw_valence_score(self) -> float:
        """
        Compute continuous valence score from multiple signals.
        Uses tanh squashing for bounded output.
        """
        import math

        # Positive signals: making progress, gaining confidence
        confidence_trend = self.blackboard.get('confidence_delta', 0)
        levels_completed = self.blackboard.get('levels_completed', 0)
        total_levels = max(self.blackboard.get('total_levels', 1), 1)
        progress = levels_completed / total_levels

        # Negative signals: contradictions, deaths, stuck
        contradiction_count = len(self.blackboard.get('known_unknowns', []))
        contradictions = contradiction_count * -0.1
        death_count = self.blackboard.get('death_count', 0)
        deaths = death_count * -0.2
        stuck_penalty = -0.3 if self.blackboard.get('stuck_detected') else 0

        raw = confidence_trend + progress + contradictions + deaths + stuck_penalty
        return math.tanh(raw)  # Squash to [-1, 1]

    def _compute_arousal(self) -> float:
        """Compute energy/activation level."""
        signals = [
            self.blackboard.get('frame_delta_magnitude', 0) / 100,
            self.blackboard.get('pending_questions', 0) / 10,
            1.0 - self.blackboard.get('strategy_stability', 1.0),
        ]
        return min(sum(signals) / len(signals), 1.0)

    def _compute_certainty(self) -> float:
        """Compute confidence level from epistemic state."""
        quadrant_certainty = {
            'KK': 0.9,
            'KU': 0.5,  # We know what we don't know
            'UK': 0.6,  # We have knowledge we're not using
            'UU': 0.2,
        }
        epistemic = self.blackboard.get('epistemic_quadrant', 'UU')
        base = quadrant_certainty.get(epistemic, 0.5)

        # Adjust by recent success rate
        recent_success = self.blackboard.get('recent_success_rate', 0.5)
        return base * 0.7 + recent_success * 0.3

    def _compute_agency(self) -> float:
        """Compute sense of control."""
        has_control = self.blackboard.get('controlled_object') is not None
        has_theory = self.blackboard.get('working_theory') is not None
        actions_work = self.blackboard.get('recent_success_rate', 0.5) > 0.5

        return (
            0.4 * float(has_control) +
            0.3 * float(has_theory) +
            0.3 * float(actions_work)
        )

    def _compute_salience(self) -> float:
        """Compute attention-grabbing level."""
        return min(
            self.blackboard.get('novelty_score', 0) +
            self.blackboard.get('surprise_score', 0) +
            (0.5 if self.blackboard.get('pattern_break', False) else 0),
            1.0
        )

    def _compute_momentum(self) -> float:
        """Compute whether things are getting better or worse."""
        if len(self.history) < 2:
            return 0.0

        recent = self.history[-5:] if len(self.history) >= 5 else self.history

        certainty_trend = recent[-1].certainty - recent[0].certainty
        agency_trend = recent[-1].agency - recent[0].agency

        # Valence transitions
        valence_score = {
            Valence.STABILITY: 0,
            Valence.OPPORTUNITY: 0.3,
            Valence.CONFUSION: -0.3,
            Valence.THREAT: -0.5,
            Valence.BOREDOM: -0.2,
        }
        valence_momentum = (
            valence_score[recent[-1].valence] -
            valence_score[recent[0].valence]
        )

        return (certainty_trend + agency_trend + valence_momentum) / 3

    def _get_dominant_contributors(self) -> list:
        """Identify which blackboard slots dominated the compression."""
        # Track which slots were actually used in valence/arousal computation
        contributors = []

        if self.blackboard.get('contradiction_detected', False):
            contributors.append('contradiction_detected')
        if self.blackboard.get('epistemic_quadrant'):
            contributors.append('epistemic_quadrant')
        if self.blackboard.get('controlled_object'):
            contributors.append('controlled_object')
        if self.blackboard.get('working_theory'):
            contributors.append('working_theory')

        return contributors[:5]  # Top 5
```

### 9.3 FeltState Influences Algorithm Selection

A critical improvement from external review: FeltState shouldn't just bias Eisenhower scores—it should **directly modulate algorithm parameters**:

```python
# engines/cognition/phenomenology_layer.py (additions)

class PhenomenologyLayer:
    # ... existing methods ...

    def get_algorithm_modulation(self, felt: FeltState) -> Dict[str, Any]:
        """
        Let phenomenological state influence algorithm choice.

        This is where 'feeling' becomes actionable—not just recorded,
        but used to change behavior.
        """
        modulation = {
            'algorithm_override': None,
            'beam_width_multiplier': 1.0,
            'exploration_boost': 0.0,
            'exclusion_set': set(),
        }

        # PANIC MODE: High arousal + low agency
        # Use faster, more conservative algorithm
        if felt.arousal > 0.8 and felt.agency < 0.3:
            modulation['algorithm_override'] = 'BeamSearch'
            modulation['beam_width_multiplier'] = 0.5  # Narrow beam, fast
            return modulation

        # CONFIDENT BUT UNHAPPY: Low valence + high certainty
        # Something's wrong with our approach, try different path
        if felt.valence == Valence.THREAT and felt.certainty > 0.7:
            recent_path = self.blackboard.get('recent_path', [])
            modulation['exclusion_set'] = set(recent_path)
            modulation['exploration_boost'] = 0.3
            return modulation

        # BORED: Nothing happening, seek novelty
        if felt.valence == Valence.BOREDOM:
            modulation['exploration_boost'] = 0.5
            return modulation

        # HIGH SALIENCE: Something important happening
        # Don't rush, pay attention
        if felt.salience > 0.8:
            modulation['beam_width_multiplier'] = 1.5  # Wider search
            return modulation

        return modulation
```

**Why This Matters**: The phenomenology layer becomes **useful** when it changes behavior. Without this, FeltState is just logging. With it, the system behaves differently when "panicked" vs "bored" vs "confident-but-stuck".

### 9.4 Integration: The Full Loop

```python
# Updated cognitive_router.py with phenomenology layer

class CognitiveRouter:
    def __init__(self, ...):
        # ... existing initialization ...
        self.phenomenology = PhenomenologyLayer(self.blackboard)
        self.eisenhower = EisenhowerLayer(self.blackboard)

    def route(self, frame: Frame) -> RoutingDecision:
        # 0. Compress previous state and inject (phenomenology feedback)
        felt = self.phenomenology.compress()
        self.phenomenology.inject(felt)

        # 1. Get algorithm modulation from felt state (NEW)
        modulation = self.phenomenology.get_algorithm_modulation(felt)

        # 2. Update epistemic state (Rumsfeld layer)
        self.epistemic_tracker.update(frame, self.blackboard)
        quadrant = self.epistemic_tracker.current_quadrant

        # 3. Get algorithm based on epistemic state + modulation
        if modulation['algorithm_override']:
            algorithm = self.meta_planner.get_algorithm(modulation['algorithm_override'])
        else:
            algorithm = self.meta_planner.select_algorithm(quadrant, context)

        # 4. Apply modulation parameters
        algorithm.beam_width = int(algorithm.beam_width * modulation['beam_width_multiplier'])
        algorithm.exploration_bonus = modulation['exploration_boost']
        algorithm.exclusions = modulation['exclusion_set']

        # 5. Get candidate rungs from algorithm
        candidates = algorithm.get_next_rungs(context)

        # 6. Apply phenomenology bias to urgency/importance
        felt_urgency_bias = felt.to_urgency_bias()
        felt_importance_bias = felt.to_importance_bias()
        self.blackboard.write('felt_urgency_bias', felt_urgency_bias)
        self.blackboard.write('felt_importance_bias', felt_importance_bias)

        # 5. Prioritize using Eisenhower layer (now informed by felt state)
        candidate_tuples = [
            (rung, self.graph.get_edge_trust(rung))
            for rung in candidates
        ]
        best_rung = self.eisenhower.prioritize(candidate_tuples)

        # 6. Execute and return
        return self.execute_rung(best_rung)
```

### 9.4 Why This Matters: The Feedback Loop

The phenomenology layer creates what the document describes as consciousness-like behavior:

```
High-D state → Compress → Summary → Feed back into High-D state → ...
                              ↑
                     "experience" is this loop
                     not the summary itself
```

The system:
1. **Processes** high-dimensional state (100+ blackboard slots, rungs, algorithms)
2. **Compresses** to FeltState (5 dimensions)
3. **Injects** back as `felt_*` slots
4. **Responds** to its own compressed state in next cycle
5. **Recursively** updates at high frequency

This isn't "adding consciousness"—it's making explicit the compression that was already implicit, and closing the loop so the system responds to its own self-perception.

---

## Phase 10: Valence-Tagged Knowledge

### 10.1 The Final Insight

From the phenomenology document:

> "Pain doesn't represent tissue damage then feel bad. Pain IS the representation of tissue damage in a format that includes 'STOP DOING THIS' as part of the encoding."

Currently our knowledge storage separates data from urgency:
```python
# Current: Data + separate urgency lookup
blackboard.write('object_moving', True)
# Later: check if this is urgent
```

The insight is to encode urgency/valence IN the representation:
```python
# Proposed: Valence is part of the encoding
blackboard.write_with_valence('object_moving', True, valence=Valence.THREAT)
# No lookup needed—the knowledge carries its urgency
```

### 10.2 ValenceTaggedSlot

```python
# engines/cognition/blackboard.py (additions)

@dataclass
class ValenceTaggedSlot(BlackboardSlot):
    """
    A blackboard slot where valence IS part of the encoding,
    not metadata about it.

    Like pain encoding "STOP" in the representation itself.
    """
    valence: Optional[Valence] = None
    urgency_inherent: float = 0.5     # 0-1 urgency baked into the data
    importance_inherent: float = 0.5  # 0-1 importance baked into the data

    def get_with_context(self) -> tuple:
        """Return value with its inherent urgency/importance."""
        return (self.value, self.valence, self.urgency_inherent, self.importance_inherent)

# Usage in rung execution:
class SurveyRung:
    def execute(self, blackboard: Blackboard, ...) -> RungResult:
        # When we find a moving object, encode THREAT in the data itself
        if object_is_moving:
            blackboard.write_valenced(
                'detected_motion',
                {'object_id': obj_id, 'velocity': vel},
                valence=Valence.THREAT,  # STOP is in the encoding
                urgency_inherent=0.8,
                importance_inherent=0.7,
            )

        # When we find static structure, encode STABILITY
        if found_grid_pattern:
            blackboard.write_valenced(
                'grid_structure',
                {'dimensions': dims, 'pattern': pattern},
                valence=Valence.STABILITY,
                urgency_inherent=0.2,
                importance_inherent=0.6,
            )
```

### 10.3 Benefits of Valence-Tagged Knowledge

1. **No urgency lookup**: Eisenhower layer reads urgency from the slot itself
2. **Context-appropriate urgency**: Same fact (object moving) has different urgency in different contexts because the ENCODING varies
3. **Faster decisions**: O(1) urgency access vs O(n) urgency computation
4. **Matches biology**: This is how pain/pleasure actually work—urgency IS the format

---

## Phase 11: Phenomenology ↔ Graph Evolution Integration

### 11.1 The Problem

Paths discovered under different FeltStates have different reliability:
- **THREAT paths**: Discovered under panic—may be suboptimal escapes
- **BOREDOM paths**: Discovered during exploration—may be gold (successful innovation)
- **CONFUSION paths**: Discovered while lost—may be lucky flukes

Currently, graph evolution treats all paths equally. The FeltState context is lost.

### 11.2 Valence-Weighted Crystallization

```python
# engines/reasoning/graph_evolution.py (additions)

@dataclass
class ValenceWeightedEdge:
    """Edge that tracks the FeltState context of its discovery."""
    from_rung: str
    to_rung: str
    traversal_count: int
    success_count: int

    # NEW: FeltState context at discovery
    discovery_valence: Valence
    discovery_arousal: float

    @property
    def valence_adjusted_crystallization_threshold(self) -> int:
        """
        Paths discovered under THREAT require more traversals to crystallize.
        Paths discovered under BOREDOM that succeed crystallize faster.
        """
        base_threshold = 5  # Standard threshold

        if self.discovery_valence == Valence.THREAT:
            # Panic decisions need more validation
            return int(base_threshold * 1.5)

        elif self.discovery_valence == Valence.BOREDOM:
            # Successful exploration is valuable - crystallize faster
            success_rate = self.success_count / max(self.traversal_count, 1)
            if success_rate > 0.7:
                return int(base_threshold * 0.7)  # Faster
            return base_threshold

        elif self.discovery_valence == Valence.CONFUSION:
            # Lucky flukes need lots of validation
            return int(base_threshold * 2.0)

        else:  # OPPORTUNITY, STABILITY
            return base_threshold

class GraphEvolution:
    def record_traversal(self, from_rung: str, to_rung: str,
                         success: bool, felt_state: FeltState):
        """Record a traversal with its FeltState context."""
        edge_key = (from_rung, to_rung)

        if edge_key not in self.edges:
            self.edges[edge_key] = ValenceWeightedEdge(
                from_rung=from_rung,
                to_rung=to_rung,
                traversal_count=1,
                success_count=1 if success else 0,
                discovery_valence=felt_state.valence,
                discovery_arousal=felt_state.arousal
            )
        else:
            edge = self.edges[edge_key]
            edge.traversal_count += 1
            if success:
                edge.success_count += 1

    def should_crystallize(self, edge_key: tuple) -> bool:
        """Check if edge should become crystallized (preferred path)."""
        edge = self.edges.get(edge_key)
        if not edge:
            return False

        threshold = edge.valence_adjusted_crystallization_threshold
        return edge.traversal_count >= threshold and edge.success_count >= threshold * 0.6
```

### 11.3 Cross-Game FeltState Patterns (Optional)

For games with enough play history, we can track typical "feel trajectories":

```python
@dataclass
class GameFeelTrajectory:
    """Typical FeltState progression for a game type."""
    game_id: str
    typical_opening_valence: Valence       # Usually CONFUSION or BOREDOM
    typical_midgame_valence: Valence       # Usually OPPORTUNITY or THREAT
    typical_resolution_valence: Valence    # Usually STABILITY or THREAT
    variance_by_phase: Dict[str, float]    # How much variation is normal

def detect_feel_anomaly(current_trajectory: List[FeltState],
                        typical: GameFeelTrajectory) -> Optional[str]:
    """
    Detect if current game is feeling unusual.

    Returns:
        Anomaly description if detected, None otherwise.
    """
    # If we're in opening but feeling THREAT when typical is BOREDOM
    # → something unexpected happened early
    pass  # Implementation based on phase detection
```

---

## Implementation Timeline

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| **Phase 8.1** | EisenhowerLayer with UrgencyScore/ImportanceScore | 3 days | Phases 0-7.5 complete |
| **Phase 8.2** | Cross-matrix mapping (Rumsfeld → Eisenhower bias) | 2 days | 8.1 |
| **Phase 8.3** | Integration with CognitiveRouter | 2 days | 8.2 |
| **Phase 8.4** | Tests for dual-matrix flow | 2 days | 8.3 |
| **Phase 9.1** | PhenomenologyLayer with FeltState | 3 days | 8.4 |
| **Phase 9.2** | Feedback loop integration | 2 days | 9.1 |
| **Phase 9.3** | Felt state → Eisenhower bias | 1 day | 9.2 |
| **Phase 9.4** | Tests for phenomenology feedback | 2 days | 9.3 |
| **Phase 10.1** | ValenceTaggedSlot | 2 days | 9.4 |
| **Phase 10.2** | Migrate critical slots to valence-tagged | 3 days | 10.1 |
| **Phase 10.3** | Integration tests | 2 days | 10.2 |
| **Phase 11.1** | ValenceWeightedEdge in graph evolution | 2 days | 10.3 |
| **Phase 11.2** | Cross-game feel trajectories (optional) | 2 days | 11.1 |
| **Stabilization** | Full system validation | 1 week | 11.2 |

**Total**: ~5 weeks

---

## Exit Criteria

### Phase 8 (Dual-Matrix)
- [ ] Eisenhower layer classifies tasks into 4 quadrants
- [ ] Q1 tasks execute immediately
- [ ] Q4 tasks are eliminated (measured: reduced wasted actions)
- [ ] Q3 tasks use cached/heuristic paths (delegation)
- [ ] Blocking questions correctly identified and prioritized
- [ ] **Iterative gate works**: R2 becomes ELIMINATE if R1 answered its question
- [ ] **Iterative gate works**: Urgency re-evaluated after each execution
- [ ] Rumsfeld quadrant appropriately biases Eisenhower classification
- [ ] Action budget efficiency improves by 10%+
- [ ] **Scheduled queue management**: `age_scheduled_queue()` runs at cycle start
- [ ] **Scheduled queue management**: Queue overflow handled (max 10 items)
- [ ] **Scheduled queue management**: Promoted tasks (Q2→Q1) detected and executed
- [ ] **All-ELIMINATE edge case**: `handle_all_eliminate()` triggers fallback, logs health event

### Phase 9 (Phenomenology)
- [ ] FeltState compression runs every cycle
- [ ] `felt_*` slots visible in blackboard
- [ ] Rungs can read felt state and respond
- [ ] Feedback loop demonstrably affects behavior
- [ ] Momentum tracking predicts success/failure trends
- [ ] **Algorithm modulation works**: Panic mode triggers narrow beam search
- [ ] **Algorithm modulation works**: Confident-but-unhappy triggers path exclusions
- [ ] **Algorithm modulation works**: Boredom triggers exploration boost
- [ ] **Cold start handling**: Cycle 0 produces CONFUSION with high salience
- [ ] **FeltState stability**: Max 2 valence changes per 5 cycles (stabilizer working)
- [ ] **Performance guard**: Compression completes in <5ms
- [ ] **Debug infrastructure**: FeltStateTraceEntry logged with explain() available

### Phase 10 (Valence-Tagged)
- [ ] Critical slots migrated to ValenceTaggedSlot
- [ ] Urgency reads are O(1) from slot
- [ ] Same fact can have different urgency based on context
- [ ] No regression in routing performance

### Phase 11 (Graph Evolution Integration)
- [ ] ValenceWeightedEdge tracks discovery FeltState
- [ ] THREAT paths require 1.5x traversals to crystallize
- [ ] CONFUSION paths require 2.0x traversals to crystallize
- [ ] BOREDOM paths with >70% success crystallize at 0.7x threshold
- [ ] (Optional) Cross-game feel trajectories detect anomalies

---

## Appendix A: The Full Pipeline

### Key Architectural Insight: Phenomenology as Cycle Boundary

The phenomenology layer is NOT a step within a cycle—it's the **membrane between cycles**. It answers: "Given everything that just happened, how do I feel going into the next decision?"

This matters because:
- Low `felt_agency` + high `kk_confidence` = "I think I know, but I feel out of control" → something's wrong
- High `felt_valence` + high `uu_estimate` = "I don't know much, but I feel good" → exploration is working

### Clean Separation of Concerns

| Layer | Question | Output |
|-------|----------|--------|
| **Phenomenology** | "How do I feel about last cycle?" | FeltState injected into blackboard |
| **Rumsfeld** | "What do I know?" | Quadrant + transitions |
| **Meta-Planner** | "How should I search?" | Algorithm selection |
| **Algorithm** | "What are my options?" | Candidate rungs [R1, R2, R3...] |
| **Eisenhower** | "What do I do NOW?" | Single prioritized action |
| **Execute** | "Do it" | Blackboard updates |

### Eisenhower as Iterative Gate (Refinement)

**Critical insight**: Eisenhower should run **per rung execution**, not once per cycle.

Why? After running rung 1, the urgency/importance of rung 2 might change:
- Did rung 1 change the urgency of rung 2?
- Is rung 3 now ELIMINATE because rung 1 answered the question?

```
Algorithm → Candidates [R1, R2, R3]
    ↓
Eisenhower(R1) → DO → Execute R1 → Update blackboard
    ↓
Eisenhower(R2, given NEW blackboard) → SCHEDULE (no longer urgent)
    ↓
Eisenhower(R3, given NEW blackboard) → ELIMINATE (answered by R1)
    ↓
Cycle complete (only R1 actually executed)
```

This makes Eisenhower a **gate** before each execution, not a one-time filter.

### The Complete Cycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CYCLE N                                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 1. PHENOMENOLOGY LAYER (Cycle Boundary Membrane)                        ││
│  │    • Compress previous blackboard state → FeltState                     ││
│  │    • Inject FeltState into current blackboard                           ││
│  │    • This IS the feedback loop that creates continuity                  ││
│  │    • "How do I feel about what just happened?"                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 2. RUMSFELD LAYER (Epistemic Assessment)                                ││
│  │    • Assess KK/KU/UK/UU quadrant                                        ││
│  │    • NOW INFORMED BY felt_valence, felt_agency, etc.                    ││
│  │    • Detect transitions (KK→KU, UU→UK, etc.)                            ││
│  │    • "What do I know? What am I missing?"                               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 3. META-PLANNER (Algorithm Selection)                                   ││
│  │    • Select algorithm based on quadrant + felt state                    ││
│  │    • Apply phenomenology modulation:                                    ││
│  │      - High arousal + low agency → BeamSearch (fast, bounded)           ││
│  │      - Low valence + high certainty → ExplorationWithExclusions         ││
│  │      - Boredom → exploration boost                                      ││
│  │    • "How should I search?"                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 4. ALGORITHM EXECUTION (Candidate Generation)                           ││
│  │    • Selected algorithm proposes candidate rungs [R1, R2, R3...]        ││
│  │    • Each candidate has edge trust from graph evolution                 ││
│  │    • "What are my options?"                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 5. EISENHOWER GATE (Iterative per-rung)                                 ││
│  │    ┌──────────────────────────────────────────────────────────────────┐ ││
│  │    │ For each candidate Ri:                                           │ ││
│  │    │   • Score urgency × importance (using CURRENT blackboard)        │ ││
│  │    │   • Q1 (DO): Execute Ri → Update blackboard → Continue           │ ││
│  │    │   • Q2 (SCHEDULE): Queue for later → Skip to next Ri             │ ││
│  │    │   • Q3 (DELEGATE): Use cached sequence → Skip to next Ri         │ ││
│  │    │   • Q4 (ELIMINATE): Discard → Skip to next Ri                    │ ││
│  │    │   • Re-evaluate remaining candidates with updated state          │ ││
│  │    └──────────────────────────────────────────────────────────────────┘ ││
│  │    • "What do I do NOW? Has that changed?"                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 6. RUNG EXECUTION (per rung that passes gate)                           ││
│  │    • Execute selected rung                                              ││
│  │    • Write valence-tagged results to blackboard                         ││
│  │    • Update graph evolution (edge trust)                                ││
│  │    • Return to Eisenhower gate for next candidate                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│                         END CYCLE N                                          │
│                              ↓                                               │
│                      ┌──────────────────┐                                    │
│                      │ CYCLE N+1 BEGINS │ ←─── Phenomenology compresses     │
│                      │ (return to step 1)│      cycle N's final state       │
│                      └──────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Ordering is Architecturally Sound

**1. Phenomenology as Cycle Boundary**

The phenomenology document says consciousness is the *loop*, not the snapshot. Placing phenomenology at the boundary makes it literally the mechanism that connects cycles:

```
Cycle N-1 ends → Phenomenology compresses → Cycle N begins with that compression
```

**2. Rumsfeld Sees Felt State**

With phenomenology first, the epistemic assessment includes "how do I feel about my knowledge state?" not just "what is my knowledge state?"

**3. Eisenhower as Iterative Gate**

Eisenhower comes AFTER candidates are generated AND runs per-candidate. This is correct because:
- You can't prioritize what you haven't generated
- After executing one rung, priorities may shift
- This is true divergent → convergent → execute → re-evaluate

**4. Complete Metacognitive Stack**

The system now has:
- **Affective continuity** (phenomenology links cycles)
- **Epistemic awareness** (Rumsfeld informed by feeling)
- **Strategic flexibility** (Meta-Planner adapts to both)
- **Pragmatic focus** (Eisenhower forces commitment, re-evaluates after each action)

---

## Appendix B: The Philosophical Grounding

### Why Two Matrices Work Together

| Matrix | Cognitive Mode | Question | Output |
|--------|---------------|----------|--------|
| Rumsfeld | Divergent | "What's the space of possibilities?" | Task candidates |
| Eisenhower | Convergent | "Which possibility should I pursue?" | Single action |

Divergent thinking expands options. Convergent thinking selects from options. You need both for intelligent behavior.

### Why Phenomenology Matters

The phenomenology layer makes explicit what was already happening implicitly:
- System has high-dimensional state
- Decisions require compression
- Compression is lossy ("ineffable")
- Feedback loops create self-awareness

By making this explicit, we:
1. Can debug "why did it feel threatened?"
2. Can tune compression parameters
3. Can measure information loss
4. Can test if feedback loop improves behavior

### The Integration

Phenomenology feeds into both matrices:
- **Rumsfeld**: Felt certainty affects KK vs UU classification
- **Eisenhower**: Felt urgency/valence biases prioritization

The valence-tagged slots mean knowledge itself carries urgency—the feeling IS the format, not something added later.

---

**END OF ADDON DOCUMENT**

**Next Steps**: Review with human, then implement Phase 8.1 (EisenhowerLayer)

---

## Appendix C: Production Concerns - Complexity & Tuning

### C.1 The Complexity Budget Problem

The system now has:
- 63+ rungs
- 110+ primitives
- 4 epistemic quadrants with transition logic + hysteresis
- Graph evolution with edge trust + crystallization
- Question lifecycle with blocking detection + UK potential index
- Eisenhower with 4 quadrants + iterative gating + scheduled queue aging
- Phenomenology with 5 dimensions + valence enum + stabilizer
- Valence-tagged slots

Each piece is well-designed. The interaction surface is enormous.

**Example nightmare debug scenario**:
> "The system felt threatened because the epistemic tracker transitioned to KU which triggered TargetedQuestionSearch but Eisenhower eliminated all candidates because felt_agency was low and the stabilizer was preventing valence change because we hadn't hit CONFIRMATIONS_REQUIRED."

**Solution: Cognitive Flight Recorder**

A unified trace format that captures the FULL decision path, queryable after the fact:

```python
# engines/cognition/flight_recorder.py

@dataclass
class CognitiveFlightRecord:
    """
    Single unified trace entry capturing ALL layers of a routing decision.
    Think of it like an airplane's black box - when something goes wrong,
    you can reconstruct exactly what happened.
    """
    tick: int
    timestamp: float

    # Layer 1: Phenomenology (cycle boundary)
    felt_state: FeltState
    felt_state_raw_scores: Dict[str, float]  # Before stabilizer
    felt_state_stabilizer_action: str  # "confirmed", "suppressed", "cooldown"

    # Layer 2: Epistemic (Rumsfeld)
    epistemic_quadrant: str  # KK, KU, UK, UU
    epistemic_transition: Optional[str]  # e.g., "KK->KU"
    epistemic_confidence: float
    open_questions_count: int
    blocking_questions: List[str]

    # Layer 3: Algorithm Selection
    selected_algorithm: str
    algorithm_reason: str
    candidate_rungs: List[str]

    # Layer 4: Eisenhower Gate (per-rung)
    eisenhower_evaluations: List[Dict[str, Any]]  # Per-rung quadrant + scores
    scheduled_queue_state: List[str]  # What's waiting
    promoted_task: Optional[str]  # If aging promoted something
    all_eliminate_triggered: bool

    # Layer 5: Execution
    executed_rungs: List[str]
    execution_outcomes: List[Dict[str, Any]]
    blackboard_changes: Dict[str, Any]  # What changed

    # Provenance
    frame_hash: str  # For correlation with game state

    def explain(self, verbosity: int = 1) -> str:
        """Human-readable explanation of decision path."""
        lines = [f"=== Tick {self.tick} ==="]

        # Level 0: One-liner
        lines.append(
            f"Felt {self.felt_state.valence.name} | "
            f"Epistemic {self.epistemic_quadrant} | "
            f"Executed {self.executed_rungs}"
        )

        if verbosity >= 1:
            lines.append(f"\nFeltState: valence={self.felt_state.valence.name}, "
                        f"arousal={self.felt_state.arousal:.2f}, "
                        f"agency={self.felt_state.agency:.2f}")
            lines.append(f"Stabilizer: {self.felt_state_stabilizer_action}")
            if self.epistemic_transition:
                lines.append(f"Epistemic transition: {self.epistemic_transition}")
            lines.append(f"Algorithm: {self.selected_algorithm} ({self.algorithm_reason})")

        if verbosity >= 2:
            lines.append(f"\nCandidate rungs: {self.candidate_rungs}")
            lines.append("Eisenhower evaluations:")
            for eval_item in self.eisenhower_evaluations:
                lines.append(f"  {eval_item['rung']}: {eval_item['quadrant']} "
                           f"(U={eval_item['urgency']:.2f}, I={eval_item['importance']:.2f})")
            if self.all_eliminate_triggered:
                lines.append("[WARN] ALL-ELIMINATE triggered")
            if self.promoted_task:
                lines.append(f"Promoted from queue: {self.promoted_task}")

        if verbosity >= 3:
            lines.append(f"\nBlackboard changes: {self.blackboard_changes}")
            lines.append(f"Raw felt scores: {self.felt_state_raw_scores}")
            lines.append(f"Blocking questions: {self.blocking_questions}")

        return "\n".join(lines)


class CognitiveFlightRecorder:
    """
    Records full decision paths for debugging and analysis.
    Stored in database for post-hoc analysis.
    """
    MAX_MEMORY_RECORDS = 1000  # Keep recent in memory

    def __init__(self, db_interface: 'DatabaseInterface'):
        self.db = db_interface
        self.memory_buffer: List[CognitiveFlightRecord] = []

    def record(self, record: CognitiveFlightRecord):
        """Record a decision cycle."""
        self.memory_buffer.append(record)
        if len(self.memory_buffer) >= 100:
            self._flush_to_db()
        if len(self.memory_buffer) > self.MAX_MEMORY_RECORDS:
            self.memory_buffer = self.memory_buffer[-self.MAX_MEMORY_RECORDS:]

    def query_recent(self, n: int = 10) -> List[CognitiveFlightRecord]:
        return self.memory_buffer[-n:]

    def query_by_condition(self, condition: str) -> List[CognitiveFlightRecord]:
        """Query records matching condition."""
        results = []
        for record in self.memory_buffer:
            if self._matches_condition(record, condition):
                results.append(record)
        return results

    def explain_sequence(self, start_tick: int, end_tick: int,
                         verbosity: int = 1) -> str:
        records = [r for r in self.memory_buffer
                   if start_tick <= r.tick <= end_tick]
        return "\n\n".join(r.explain(verbosity) for r in records)
```

### C.2 The Tuning Hell Problem

Magic numbers identified:
- CONFIRMATIONS_REQUIRED per transition type (4 values)
- COOLDOWN_TICKS per quadrant (4 values)
- Urgency threshold (0.6)
- Importance threshold (0.5)
- Valence cutoffs (-0.3, 0.3)
- FeltState dimension weights (5 values)
- Edge trust decay rate
- Crystallization threshold
- Queue aging rate (0.05)
- Stabilizer confirmation count (2)
- Stabilizer cooldown (3)

**Grid search is infeasible** (~20+ parameters, 3+ values each = 3^20 combinations).

**Solution: Three-Tier Parameter Classification**

```python
# config/cognitive_parameters.py

@dataclass
class CognitiveParameters:
    """All tunable parameters in one place, classified by sensitivity."""

    # TIER 1: CRITICAL (wrong values break the system)
    urgency_threshold: float = 0.6
    importance_threshold: float = 0.5
    stabilizer_confirmations: int = 2
    stabilizer_cooldown: int = 3

    # TIER 2: PERFORMANCE (affects quality, won't break system)
    kk_ku_confirmations: int = 3
    ku_kk_confirmations: int = 2
    kk_uk_confirmations: int = 4
    uk_uu_confirmations: int = 3
    valence_threat_threshold: float = -0.3
    valence_opportunity_threshold: float = 0.3
    scheduled_queue_max: int = 10
    queue_aging_rate: float = 0.05

    # TIER 3: FINE-TUNING (can safely auto-tune)
    felt_weight_valence: float = 0.25
    felt_weight_arousal: float = 0.20
    felt_weight_certainty: float = 0.20
    felt_weight_agency: float = 0.20
    felt_weight_salience: float = 0.15
    edge_trust_decay: float = 0.95
    crystallization_base_threshold: int = 5
```

### C.3 Using the Database Logger for Sensitivity Analysis

**Yes, the logger can help.** Query logged flight records to analyze parameter effects:

```python
class ParameterSensitivityAnalyzer:
    def analyze_threshold_sensitivity(self, threshold_name: str, outcome_metric: str):
        records = self.db.query(f'''
            SELECT json_extract(parameters_json, '$.{threshold_name}') as threshold,
                   AVG(outcome_{outcome_metric}) as outcome
            FROM cognitive_flight_records
            GROUP BY threshold ORDER BY outcome DESC
        ''')
        return self._analyze_results(records)

    def suggest_adaptations(self) -> Dict[str, float]:
        """Only for TIER 3 parameters - never auto-adapt TIER 1."""
        pass
```

### C.4 Database Schema Addition

```sql
CREATE TABLE IF NOT EXISTS cognitive_flight_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    game_id TEXT,
    agent_id TEXT,
    felt_state_json TEXT,
    epistemic_json TEXT,
    algorithm_json TEXT,
    eisenhower_json TEXT,
    execution_json TEXT,
    felt_valence TEXT,
    epistemic_quadrant TEXT,
    selected_algorithm TEXT,
    executed_rungs_count INTEGER,
    all_eliminate_triggered INTEGER,
    parameters_json TEXT,
    outcome_score REAL,
    outcome_efficiency REAL,
    outcome_success INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cfr_tick ON cognitive_flight_records(tick);
CREATE INDEX idx_cfr_game ON cognitive_flight_records(game_id);
CREATE INDEX idx_cfr_valence ON cognitive_flight_records(felt_valence);
CREATE INDEX idx_cfr_all_eliminate ON cognitive_flight_records(all_eliminate_triggered);
```

### C.5 Practical Debugging Workflow

```python
# 1. Find problematic ticks
problem_records = flight_recorder.query_by_condition("all_eliminate_triggered == True")

# 2. Get context
for record in problem_records[-5:]:
    print(flight_recorder.explain_sequence(record.tick - 10, record.tick + 5, verbosity=2))

# 3. Test fix with logged data (no live run needed)
simulator.replay_with_modified_params(records=problem_records, params={'importance_threshold': 0.45})
```

### C.6 Exit Criteria Additions

**Production Readiness**
- [ ] CognitiveFlightRecorder integrated into route()
- [ ] All 5 layers captured in flight records
- [ ] explain() produces readable output at all verbosity levels
- [ ] cognitive_flight_records table created with indexes
- [ ] CognitiveParameters dataclass has all magic numbers
- [ ] Parameters classified into Tier 1/2/3
- [ ] Sensitivity analysis can run on logged data
