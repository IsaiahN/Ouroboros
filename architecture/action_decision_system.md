# Action Decision System Architecture
**Version**: 1.1  
**Date**: January 29, 2026  
**Purpose**: Document all 42 features involved in gameplay action decision-making

---

## Overview

The action decision system in `core_gameplay.py` uses a **ladder-based priority system** where multiple decision sources are evaluated in order. The first source to produce a high-confidence action "wins" and short-circuits the rest.

**Total Features Documented**: 42
- Features 1-13: Main action selection ladder
- Features 14-28: External/supporting systems  
- Features 29-36: From console log analysis (Micro-CF, Q-Field, etc.)
- Features 37-42: From reasoning log analysis (Survey, Deliberation, Replay Learning, etc.)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ACTION DECISION FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ DISCOVERY       │ ◄── Highest priority (exploit recent      │
│  │ EXPLOITATION    │     discoveries immediately)               │
│  └────────┬────────┘                                            │
│           │ No pending discovery                                │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ DEATH AVOIDANCE │ ◄── Position-bucket based, graduated      │
│  │ (Filter Stage)  │     danger scores with time decay          │
│  └────────┬────────┘                                            │
│           │ Actions filtered                                    │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ EMBEDDING       │ ◄── Cross-game neural similarity          │
│  │ SUGGESTION      │     (conf >= 0.7 required)                 │
│  └────────┬────────┘                                            │
│           │ No high-conf match                                  │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ FRONTIER        │ ◄── Map topology for unexplored levels    │
│  │ TOPOLOGY        │     (systematic vs exploit mode)           │
│  └────────┬────────┘                                            │
│           │ Not frontier or no suggestion                       │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ EXPLORATION     │ ◄── Phase-based forced exploration        │
│  │ PHASE CHECK     │     (discovery/intermediate/final)         │
│  └────────┬────────┘                                            │
│           │ Not in exploration override                         │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ MAP INTEL       │ ◄── Obstacle avoidance with               │
│  │ COLLISION       │     graduated death avoidance (NEW)        │
│  └────────┬────────┘                                            │
│           │ No collision recovery needed                        │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ TWO-STREAMS     │ ◄── wA (private) vs wB (network)          │
│  │ PROPOSALS       │     conflict detection                     │
│  └────────┬────────┘                                            │
│           │ Proposals collected                                 │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ THEORY GATE     │ ◄── Working theory must score proposals   │
│  │ (Finalization)  │     CONTRADICTED = force exploration       │
│  └────────┬────────┘                                            │
│           │ Theory allows action                                │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ CODS ENGINE     │ ◄── Compositional operator suggestions    │
│  │                 │     (threshold typically 0.3-0.4)          │
│  └────────┬────────┘                                            │
│           │ No CODS suggestion above threshold                  │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ NETWORK WISDOM  │ ◄── Historical action traces              │
│  │ (action_traces) │     aggregated by game_type + level        │
│  └────────┬────────┘                                            │
│           │ Confidence < 0.4                                    │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ ABSTRACTION     │ ◄── Templates from winning sequences      │
│  │ TEMPLATES       │     Few-shot invariants                    │
│  └────────┬────────┘                                            │
│           │ No template matches                                 │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ MICRO-CF        │ ◄── Counterfactual "what if" rollouts     │
│  │ (Heuristic)     │     (probe salience, test actions)         │
│  └────────┬────────┘                                            │
│           │ No micro-CF above threshold                         │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ QUESTIONING     │ ◄── Q1-Q9 questions block on Q4/Q9/META   │
│  │ ENGINE (Q-FIELD)│     Forces exploration if theory fails     │
│  └────────┬────────┘                                            │
│           │ Not blocked by critical question                    │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ SMART ACTION    │ ◄── Fallback: strategy-based selection    │
│  │ SELECTION       │     (random with biases)                   │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Feature Documentation

### 1. Discovery Exploitation (Priority: HIGHEST)

**Location**: `_select_action()` lines ~9305-9340

**Purpose**: When an agent just discovered object control, use it IMMEDIATELY instead of going through all other decision logic.

**Trigger Conditions**:
- `self._last_discovery` is set (dict with action, controlled_color, reliability_score)
- Discovery has valid action info (`action.startswith('ACTION')`)

**Decision Logic**:
| Reliability | Behavior |
|-------------|----------|
| >= 0.6 OR validated | Use same action to continue progress |
| >= 0.3 | Test hypothesis again |
| < 0.3 | Skip, use normal selection |

**Output**: Returns action immediately, bypasses all other systems

---

### 2. Position-Bucket Death Avoidance (Priority: FILTER STAGE)

**Location**: `_select_action()` lines ~9349-9490

**Purpose**: Block actions that historically caused deaths at agent's current position.

**Data Source**: `position_death_patterns` table

**Key Columns**:
- `game_type`, `level_number`
- `bucket_x`, `bucket_y` (8x8 pixel buckets)
- `fatal_action`, `death_count`, `survival_count`
- `danger_score`, `generations_since_update`

**Query Logic**:
```sql
-- When position KNOWN: Query current bucket ± 1
SELECT fatal_action, death_count, survival_count, danger_score, generations_since_update
FROM position_death_patterns
WHERE game_type = ? AND level_number = ? AND is_active = 1
  AND bucket_x BETWEEN (current_x/8 - 1) AND (current_x/8 + 1)
  AND bucket_y BETWEEN (current_y/8 - 1) AND (current_y/8 + 1)

-- When position UNKNOWN: Query high-death buckets level-wide
SELECT fatal_action, SUM(death_count), AVG(danger_score)
FROM position_death_patterns  
WHERE game_type = ? AND level_number = ? AND death_count >= 20
GROUP BY fatal_action
```

**Graduated Danger Calculation** (NEW 2026-01-29):
```python
# Base danger from death/survival ratio
death_ratio = deaths / (deaths + survivals)

# Time decay: halves every 10 generations without update
time_decay = 0.5 ** (generations_since_update / 10.0)

# Survival signal: more survivals = lower danger
survival_dampening = 1.0 / (1.0 + survivals * 0.1)

# Sample confidence: low samples = lower confidence
sample_confidence = min(1.0, total / 20.0)

# Combined
danger = death_ratio * time_decay * survival_dampening * sample_confidence
```

**Probabilistic Avoidance** (NOT binary blocking):
| Danger Score | Avoidance Probability |
|--------------|----------------------|
| > 0.7 (HIGH) | 90% chance to avoid |
| 0.4-0.7 (MEDIUM) | 60% chance to avoid |
| 0.2-0.4 (LOW) | 30% chance to avoid |
| < 0.2 (MINIMAL) | Don't avoid |

**Output**: Populates `deadly_actions_for_frame` set, filters later choices

---

### 3. Embedding Suggestion (Priority: HIGH)

**Location**: `_select_action()` lines ~9500-9525

**Purpose**: Use neural frame embeddings to find similar past situations across ALL games.

**Trigger Conditions**:
- `self.self_model` exists
- Returns suggestion with `confidence >= 0.7`

**Query**:
```python
self.self_model.get_embedding_suggested_action(
    game_type=None,   # Search ALL games
    level=None,       # Search ALL levels
    current_frame=game_state.frame,
    top_k=10          # Cross-game voting
)
```

**Output**: Action with reasoning about similar_count, confidence, avg_outcome

---

### 4. Frontier Topology (Priority: HIGH)

**Location**: `_select_action()` lines ~9535-9600

**Purpose**: For frontier levels (unbeaten), use recorded frame transitions to suggest safe actions.

**Modes**:
| Mode | Confidence | Behavior |
|------|------------|----------|
| `exploit` | >= 0.5 | Prefer known-safe actions |
| `systematic` | 0.2-0.5 | Try untried actions from this frame |
| `random` | < 0.2 | Continue to normal selection |

**Data Source**: Frame transition records, exploration confidence calculations

---

### 5. Exploration Phase Override (Priority: HIGH)

**Location**: `_select_action()` lines ~9900-9960

**Purpose**: Force exploration based on action budget phases.

**Phases**:
| Phase | Budget Range | Behavior |
|-------|--------------|----------|
| `discovery` | 0-30% | Heavy exploration, try new things |
| `intermediate` | 30-70% | Balanced exploration/exploitation |
| `final` | 70-100% | Prefer exploitation, minimize risk |

**Override Triggers**:
- Phase is `discovery` AND coverage < 30%
- Regional stuck detected (repeating positions)
- Explicit explore reason from phase calculator

---

### 6. MAP-INTEL Collision Recovery (Priority: MEDIUM-HIGH)

**Location**: `_select_action()` lines ~9680-9880

**Purpose**: When last action caused no frame change (hit obstacle), route around it.

**Trigger**: `self._last_action_no_change == True` AND last action was directional (ACTION1-4)

**Decision Flow**:
1. Get map intelligence: `_get_map_intelligence(game_state, direction=last_action)`
2. Identify terrain type (wall, object, unknown)
3. Get alternative directions from map intel
4. Query position-bucket death patterns for current position
5. Calculate graduated danger scores (see Section 2)
6. Filter alternatives using probabilistic avoidance
7. If all alternatives risky: pick **least dangerous** (never fully block)

**Perpendicular Map**:
```python
perpendicular_map = {
    'ACTION1': ['ACTION3', 'ACTION4'],  # up failed -> try left/right
    'ACTION2': ['ACTION3', 'ACTION4'],  # down failed -> try left/right
    'ACTION3': ['ACTION1', 'ACTION2'],  # left failed -> try up/down
    'ACTION4': ['ACTION1', 'ACTION2'],  # right failed -> try up/down
}
```

---

### 7. Two-Streams Proposal Collection (Priority: MEDIUM)

**Location**: `_select_action()` lines ~10020-10130

**Purpose**: Collect proposals from private experience (Stream A) and network wisdom (Stream B).

**Stream A Sources** (Private Experience):
- Recent discoveries (`_last_discovery`)
- Contradicted actions (`_contradicted_actions`)
- Persona proposals (internal dialogue)

**Stream B Sources** (Network Wisdom):
- Network control hypotheses
- Peer failure patterns
- CODS candidates (if below threshold)

**Weights**:
- `wA` = Trust private experience (default 0.5)
- `wB` = Trust network wisdom (default 0.5)
- Modified by agent autobiography and novelty boost

**Conflict Detection**:
```python
stream_conflict = (
    stream_a_actions and 
    stream_b_actions and 
    stream_a_actions != stream_b_actions
)
```

---

### 8. Theory Gate (Priority: FINALIZER)

**Location**: `_finalize_ladder_and_return()` lines ~10280-10400

**Purpose**: Working theory MUST score every proposal. Contradicted theory blocks exploitation.

**Theory Stages**:
| Stage | Behavior |
|-------|----------|
| `contradicted` | ONLY allow exploration/revision actions |
| `speculating` | Boost exploration, slight penalty for exploitation |
| `exploring` | Normal operation |
| `confident` | Boost actions that use the theory |

**When Contradicted**:
- Block exploitation actions
- Force exploration (ACTION1-4) or click explore (ACTION6)
- Use primitive analysis to pick intelligent revision action

---

### 9. CODS Engine (Priority: MEDIUM)

**Location**: `_select_action()` lines ~13950-14030

**Purpose**: Compositional operator suggestions based on learned game patterns.

**Threshold**: Typically 0.3-0.4 confidence required

**Query**:
```python
cods_suggestion = self.cods_engine.suggest_action(
    game_context=cods_context,
    available_actions=['ACTION1'...'ACTION7']
)
```

**Output Fields**:
- `action`: Suggested action number
- `confidence`: 0.0-1.0
- `operator_name`: Name of the compositional operator
- `candidates`: List of all considered actions with scores

---

### 10. Network Action Wisdom (Priority: MEDIUM-LOW)

**Location**: `_get_network_action_wisdom()` lines ~28553-28750

**Purpose**: Abstract historical gameplay from ALL agents on this game_type + level.

**Data Source**: `action_traces` table

**Query**:
```sql
SELECT 
    action_number,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as successes,
    AVG(score_change) as avg_score_change
FROM action_traces
WHERE game_id LIKE '{game_type}-%' 
  AND level_number = {level}
  AND action_number IS NOT NULL
GROUP BY action_number
HAVING total_attempts >= 3
ORDER BY avg_score_change DESC
```

**Confidence Calculation**:
```python
success_rate = successes / total
sample_weight = min(total / 50.0, 1.0)
confidence = success_rate * 0.6 + avg_change * 0.2 + sample_weight * 0.2
```

**Mastery Boost** (NEW):
| Mastery Tier | Confidence Boost |
|--------------|------------------|
| expert | +0.15 |
| practitioner | +0.10 |
| apprentice | +0.05 |
| novice | +0.00 |

**Thresholds**:
| Confidence | Behavior |
|------------|----------|
| >= 0.4 | Use confidently |
| 0.2-0.4 + is_least_bad | Use as least-bad option |
| < 0.2 | Fall back to smart selection |

---

### 11. Abstraction Templates (Priority: LOW)

**Location**: `_select_action()` lines ~14120-14180

**Purpose**: Use pattern templates extracted from multiple winning sequences.

**Trigger**: `abstraction_engine.should_use_template(game_type, level)` returns True

**Query**:
```python
template_actions = abstraction_engine.get_template_for_replay(game_type, level)
```

**Usage**: Follow template action-by-action until template exhausted or fails

---

### 12. Few-Shot Invariants (Priority: LOW)

**Location**: `_select_action()` lines ~14180-14210

**Purpose**: Relational bias from few-shot control relations.

**Trigger**: `agent_self_model.get_few_shot_control_relations()` returns invariants with sample_size >= 2

**Output**: Action at specific position in sequence based on invariant patterns

---

### 13. Smart Action Selection (Priority: FALLBACK)

**Location**: `action_handler.smart_action_selection()`

**Purpose**: Final fallback when no other system has a suggestion.

**Strategies**:
| Strategy | Behavior |
|----------|----------|
| `balanced` | Even mix of exploration/exploitation |
| `exploration` | Prefer untried actions |
| `exploitation` | Prefer known-good actions |
| `unbeaten_exploration` | Heavy exploration for unbeaten games |

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐    │
│  │ position_death_ │     │ action_traces   │     │ level_mastery   │    │
│  │ patterns        │     │                 │     │                 │    │
│  │                 │     │ - action_number │     │ - mastery_tier  │    │
│  │ - bucket_x/y    │     │ - score_change  │     │ - total_score   │    │
│  │ - fatal_action  │     │ - level_number  │     │                 │    │
│  │ - death_count   │     │ - game_id       │     │                 │    │
│  │ - survival_cnt  │     │                 │     │                 │    │
│  │ - danger_score  │     │                 │     │                 │    │
│  │ - gens_since_   │     │                 │     │                 │    │
│  │   update        │     │                 │     │                 │    │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘    │
│           │                       │                       │              │
│           ▼                       ▼                       ▼              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    ACTION DECISION ENGINE                       │    │
│  │                                                                 │    │
│  │  death_avoidance ◄─────┤                                        │    │
│  │  network_wisdom  ◄─────┤ _select_action()                       │    │
│  │  mastery_boost   ◄─────┤                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    ADDITIONAL SOURCES                            │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ network_     │  │ viral_info_  │  │ winning_     │           │    │
│  │  │ object_      │  │ packages     │  │ sequences    │           │    │
│  │  │ control_     │  │              │  │              │           │    │
│  │  │ hypotheses   │  │ - strategy   │  │ - sequence   │           │    │
│  │  │              │  │ - virulence  │  │ - game_type  │           │    │
│  │  │ - hypothesis │  │ - success_   │  │ - level      │           │    │
│  │  │ - reliability│  │   rate       │  │              │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  │         │                 │                 │                    │    │
│  │         ▼                 ▼                 ▼                    │    │
│  │  Stream B         Pariah           Abstraction                   │    │
│  │  Proposals        Avoidance        Templates                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Known Issues & Gotchas

### Issue 1: Level-Wide Death Aggregation (FIXED 2026-01-29)

**Problem**: Death patterns were aggregated across ALL positions on a level, blocking actions everywhere even if only dangerous at specific locations.

**Fix**: Query by position bucket (`bucket_x`, `bucket_y`) with ±1 bucket fuzzy matching.

### Issue 2: Binary Blocking (FIXED 2026-01-29)

**Problem**: Actions were either "allowed" or "blocked" with no middle ground.

**Fix**: Graduated danger scores with probabilistic avoidance. Actions are never permanently off the table.

### Issue 3: No Time Decay

**Problem**: Old death patterns from 100+ generations ago carry same weight as recent data.

**Fix**: Time decay formula: `0.5^(generations/10)` - danger halves every 10 generations without update.

### Issue 4: Survival Signals Ignored

**Problem**: An action with 100 deaths and 50 survivals was treated same as 100 deaths and 0 survivals.

**Fix**: Survival dampening: `1.0 / (1.0 + survivals * 0.1)`

### Issue 5: Mastery Data Not Connected (PARTIAL)

**Problem**: `level_mastery` data (expert/practitioner/apprentice/novice) only gated sequence replay, didn't inform action choices.

**Fix**: Mastery tier now boosts network wisdom confidence by +0.05 to +0.15.

### Issue 6: All-Negative Network Wisdom Returns None (FIXED 2026-01-28)

**Problem**: When ALL actions have negative avg_score_change (frontier levels), confidence was too low and method returned None instead of "least bad" option.

**Fix**: Return least-bad suggestion with `is_least_bad=True` flag and lower confidence threshold (0.2).

---

## Debugging Guide

### Check Death Avoidance Status
```python
# In logs, look for:
[MAP-INTEL-DANGER] L{level} pos=(x,y): ACTION{n} danger=0.XX
[DEATH-AVOID] Position-bucket: blocking {set} at (x,y)
[DEATH-AVOID-FALLBACK] L{level}: Blocking {set} (position unknown)
```

### Check Network Wisdom Usage
```python
# In logs, look for:
[NETWORK] NETWORK WISDOM: ACTION{n} (confidence: X.XX)
[NETWORK] LEAST-BAD WISDOM: ACTION{n} (conf=X.XX)
[MASTERY-BOOST] L{level} tier=expert -> +0.15 confidence
```

### Check Two-Streams Conflict
```python
# In logs, look for:
[I-THREAD] {intensity} conflict: StreamA={actions}, StreamB={actions}, wA=X.XX wB=X.XX
```

### Check Theory Gate
```python
# In logs, look for:
[THEORY-GATE] Stage=contradicted, blocked {action} -> {revision_action}
```

---

## Configuration Points

| Config Key | Default | Effect |
|------------|---------|--------|
| `cods_threshold` | 0.3-0.4 | Minimum CODS confidence to use suggestion |
| `bucket_size` | 8 | Position bucket size for death patterns |
| `min_danger` | 0.6 | Minimum danger score to mark action as deadly |
| `network_wisdom_threshold` | 0.4 | Minimum confidence for network wisdom |
| `exploration_coverage_target` | 0.3 | Coverage % below which exploration is forced |

---

## External Systems That Affect Action Decisions

The following systems from OTHER files influence action decision-making but are not directly in the `_select_action()` ladder:

---

### 14. Three-Try Sequence Fallback System (GAME-LEVEL)

**Location**: `core_gameplay.py` lines ~4640-4990

**Purpose**: Before gameplay begins, try up to 3 ranked sequences to replay. If all fail, fall back to exploration.

**Flow**:
```
1. Get ranked sequences: _get_ranked_cumulative_sequences(game_id, limit=3)
2. For each sequence (try_num 1-3):
   a. Check reputation (successful_validations / total_validation_attempts)
   b. Attempt replay with _try_replay_sequence()
   c. If success: Use for rest of game
   d. If fail: Flag sequence, RESET GAME, try next
3. If all 3 fail:
   a. Try multi_stage_matching_pipeline.get_sequence_with_fallback()
   b. If still fail: Use abstraction_guidance for pure exploration
```

**Console Tags**: `[3-TRY]`, `[MULTI-STAGE]`

**Why This Matters**: Determines WHETHER the agent has a sequence to follow, which completely changes action selection behavior.

---

### 15. Multi-Stage Matching Pipeline (SEQUENCE RETRIEVAL)

**Location**: `multi_stage_matching_pipeline.py` class `MultiStageMatchingPipeline`

**Purpose**: Cascading sequence matching with 5 fallback strategies when 3-try fails.

**Cascade Stages**:
| Stage | Method | Confidence | Description |
|-------|--------|------------|-------------|
| exact | `_stage_1_exact_match` | 1.0 | Exact sequence for game+level |
| prefix | `_stage_2_prefix_match` | 0.8 | Start of a longer sequence |
| suffix | `_stage_3_suffix_match` | 0.7 | End portion of a sequence |
| subsequence | `_stage_4_subsequence_extraction` | 0.6 | Extract reusable segment |
| conceptual | `_stage_5_conceptual_match` | 0.5 | Similar pattern from other game |

**Cascade Order** (Dynamic by maturity):
- Cold Start/Early: exact → prefix → suffix → subsequence → conceptual
- Mature/Saturated: conceptual → subsequence → suffix → prefix → exact

---

### 16. Three-Layer Action Effectiveness Filter (FINALIZER)

**Location**: `core_gameplay.py` lines ~3480-3620, applied in `_finalize_ladder_and_return()`

**Purpose**: Meta-learning filter that prevents wasting actions on known-ineffective moves.

**Layers**:
| Layer | Method | What It Checks |
|-------|--------|----------------|
| 1 | `_action_filter_layer1_cache_check()` | Exact-match cache: did this action work at this position+frame before? |
| 2 | `_action_filter_layer2_object_prefilter()` | Object detection: is there an interactive object at position for click actions? |
| 3 | `_action_filter_layer3_pattern_predict()` | Pattern prediction: what's the success rate for similar visual contexts? |

**When Applied**: In `_finalize_ladder_and_return()` AFTER the ladder selects an action.

**Filter Decision**:
```python
should_skip = (
    layer1_cache_says_failed OR
    layer2_no_interactive_object OR
    layer3_success_probability < 0.15
)
```

---

### 17. Pariah Avoidance (NEGATIVE SELECTION)

**Location**: `core_gameplay.py` lines ~17063-17090, `viral_package_engine.py`

**Purpose**: Avoid actions that historically led to failures across the network.

**Data Source**: `pariahs` table

**Pariah Structure**:
```sql
pariahs (
  pariah_id, game_type, level_number,
  failed_action, toxicity, avoidance_success_rate,
  source_level_number, generations_since_trigger
)
```

**Role-Adjusted Penalties**:
| Role | Penalty Multiplier | Effect |
|------|-------------------|--------|
| pioneer | 0.3 (30%) | Ignore most pariahs on frontier |
| optimizer | 1.0 (100%) | Full penalty - avoid known failures |
| generalist | 0.7 (70%) | Moderate avoidance |
| exploiter | 0.5 (50%) | Balanced - sociopaths ignore more |

**Toxicity Decay**:
```
toxicity(t) = initial_toxicity × (1 - decay_rate × generations_since_trigger)
```

---

### 18. Frustration Detection & Quorum Sensing (NETWORK-LEVEL)

**Location**: `frustration_detector.py` class `FrustrationDetector`

**Purpose**: Detect when agents are stuck and trigger network-wide signals.

**Frustration Indicators**:
- Zero score improvement over N games
- Repeated failures on same game
- Action diversity collapse (spamming same actions)
- High action count with low results

**Dynamic Quorum Threshold**:
```python
threshold = base_threshold - (maturity_factor × (base - mature))
# Early generations: 80% must be frustrated
# Mature generations: 70% must be frustrated
```

**Action Impact**: When quorum reached, network emits stress signals that modify agent behavior.

---

### 19. Terminal Pattern Detector (FORESIGHT)

**Location**: `terminal_pattern_detector.py` class `TerminalPatternDetector`

**Purpose**: Recognize when approaching a terminal state (game_over) and avoid the fatal action.

**What It Tracks**:
- Pre-death frame signatures (hash of state before fatal action)
- Last N actions leading up to game_over
- The fatal action itself
- Death zones (spatial regions where game-overs happen)

**When Checked**: In last 30% of sequence or when stuck

**Tables Used**:
- `position_death_patterns` (primary - shared with death avoidance)
- `death_zones` (spatial danger regions)

---

### 20. Sensation Engine (EMOTIONAL INTELLIGENCE)

**Location**: `sensation_engine.py` class `SensationEngine`

**Purpose**: Add emotional context to actions 1-7. Agents learn "how to feel" about objects.

**Two Streams Implementation**:
- **Stream A (Private)**: Personal sensation mappings learned from direct experience
- **Stream B (Network)**: Network sensation mappings from CODS validation

**Key Methods**:
- `get_tetrahedral_sensation()`: Returns both streams + synthesis
- `query_personal_impression()`: Stream A query
- `query_network_wisdom()`: Stream B query

**Action Bias**:
```python
# High approach_score for object = bias toward moving to it
# High threat_level for object = bias away from it
# Synthesis = w_A * stream_a + w_B * stream_b
```

---

### 21. I-Thread (CONSCIOUSNESS WEAVER)

**Location**: `i_thread.py` class `IThread`

**Purpose**: Maintain persistent identity, weave Stream A and Stream B weights.

**Responsibilities**:
1. Maintain w_A/w_B weights (stored in `agents.self_network_bias`)
2. Learn from stream conflicts and outcomes
3. Track personality development over time
4. Compute surprise when streams conflict

**Death Personas**: When `cull_distance < 0.2`, agents spawn special personas:
| Role | Persona | Behavioral Shift |
|------|---------|------------------|
| pioneer | Legacy Hunter | maximum_novelty, exploration_weight=1.5 |
| optimizer | Final Polisher | maximum_efficiency, exploration_weight=0.3 |
| generalist | Bridge Builder | maximum_connection, exploration_weight=0.8 |

---

### 22. Near-Miss Analyzer (POST-HOC LEARNING)

**Location**: `near_miss_analyzer.py` class `NearMissAnalyzer`

**Purpose**: Learn from high-score failures (15-18/20 without winning).

**Categories**:
| Score Range | Category | Analysis Focus |
|-------------|----------|----------------|
| 15-20 | near_win | Minor mistake, missing final step |
| 10-15 | strong_partial | What worked, partial strategies |
| 5-10 | partial_progress | Identify working fragments |

**Tables**: `near_miss_games`, `near_miss_patterns`, `near_miss_insights`

---

### 23. Subgoal Planning Activator (HIERARCHICAL PLANNING)

**Location**: `subgoal_planning_activator.py` class `SubgoalPlanningActivator`

**Purpose**: Decompose complex levels into subgoals.

**Flow**:
```
Complex level → Generate subgoals → 
Reach subgoal 1 → Reach subgoal 2 → ... → Win level
```

**Integration**: Injected into core_gameplay via `inject_subgoal_planner()`

---

### 24. Breakthrough Budget Allocator (RESOURCE ALLOCATION)

**Location**: `breakthrough_budget_allocator.py` class `BreakthroughBudgetAllocator`

**Purpose**: Dynamic per-game action allocation based on breakthrough potential.

**Budget by Phase**:
| Phase | Condition | Per-Level | Total |
|-------|-----------|-----------|-------|
| DISCOVERY | 0 level wins | 400 | 2000 |
| EXPANSION | 1-2 level wins | 300 | 1500 |
| EXPLOITATION | 3+ level wins | 200 | 800 |

---

### 25. Regulatory Signal Engine (NETWORK HOMEOSTASIS)

**Location**: `regulatory_signal_engine.py` class `RegulatorySignalEngine`

**Purpose**: Network homeostasis through distributed signals (bacterial quorum sensing).

**Signal Types**:
| Signal | Target Parameter | Effect |
|--------|-----------------|--------|
| diversity_stress | knowledge_diversity_boost | +0.15 |
| metabolism_stress | action_budget_multiplier | +0.1 |
| exploration_need | mutation_rate | +0.05 |
| role_need | role_atp_adjustment | ±0.3 |

---

### 26. Visual Analyzer (FRAME ANALYSIS)

**Location**: `visual_analyzer.py` class `VisualAnalyzer` + `core_gameplay.py` ACTION6 targeting

**Purpose**: Analyze game frames to identify priority targets for ACTION6 clicks.

**Reasoning Log Fields**:
- `coordinate`: `{x: int, y: int}` - The (x,y) position clicked
- `visual_reason`: `str` - Human-readable explanation of why this target was selected

**Visual Reason Types** (priority order):
| visual_reason | Meaning |
|---------------|---------|
| `"Controlled color N"` | Clicking on agent's known-controlled color |
| `"Network-discovered interactable"` | Known interactable from network knowledge |
| `"Rare color N (X pixels)"` | Rare color exploration |
| `"Recovery: new color N"` | Recovery mode - trying new color |
| `"Changed position"` | Position that changed recently |
| `"Fallback center (...)"` | Emergency fallback to frame center |
| `"Grid exploration (X,Y)"` | Systematic grid scanning |

**Role-Specific Behavior**:
- Pioneer: More aggressive exploration, ignore some network priorities
- Optimizer: Follow known targets precisely
- Generalist: Balanced approach

**Dead Coordinates**: Tracks `(x,y) → failure_count` to avoid retrying 50+ times.

---

### 27. Scientific Method Engine (THEORY FORMATION)

**Location**: `scientific_method_engine.py` class `ScientificMethodEngine`

**Purpose**: Autonomous theory formation and testing - the CORE intelligence component.

**Scientific Method Loop**:
```
1. OBSERVE: Notice anomalies, patterns, unexplained events
2. HYPOTHESIZE: Form testable theory about WHY
3. PREDICT: What SHOULD happen if theory is true?
4. EXPERIMENT: Design and execute a test
5. ANALYZE: Did prediction match reality?
6. UPDATE: Strengthen or refute the theory
7. GENERALIZE: Abstract to broader principles
```

**Theory Stages** (affect Theory Gate in ladder):
| Stage | Action Selection Impact |
|-------|------------------------|
| contradicted | BLOCK exploitation, force exploration/revision |
| speculating | Boost exploration, penalize exploitation |
| exploring | Normal operation |
| confident | Boost actions that use the theory |

**Key Insight**: Agents spend ~20-30% of actions on DELIBERATE EXPERIMENTATION.

---

### 28. Resonance Detector (CROSS-ROLE PATTERN DISCOVERY)

**Location**: `resonance_detector.py` class `ResonanceDetector`

**Purpose**: Detect patterns that resonate across different agent roles as evidence of objective truth.

**Resonance Principle**: When Pioneers (blind exploration), Generalists (network-guided), and Exploiters (micro-optimization) ALL independently converge on the same abstract pattern, that's RESONANCE.

**Role Query Frequencies**:
| Role | Query Frequency | Rationale |
|------|----------------|-----------|
| pioneer | 15% | Frontier exploration needs network patterns |
| optimizer | 20% | When stuck or seeking inspiration |
| generalist | 30% | Consistency checks |
| exploiter | 10% | Occasional sanity checks |

**Integration**: High-resonance patterns → `concept_discovery_engine.py` for cross-game generalization.

---

### 29. Micro-Counterfactual (MICRO-CF) Rollouts (LADDER RUNG)

**Location**: `core_gameplay.py` lines ~11845-11905

**Purpose**: Lightweight heuristic rollouts that probe "what if I did X?" before committing.

**Console Tag**: `[MICRO-CF]`

**When It Runs**: As a ladder rung, after most exploration checks but before fallback.

**How It Works**:
1. `counterfactual_analyzer.generate_micro_rollouts()` produces 3-5 hypothetical action sequences
2. Checks `imagination_budget_remaining` to determine max rollouts
3. Returns best counterfactual proposal with action + reason

**Reason Strings** (from logs):
- `micro rollout: probe salience` - Testing if clicking salient pixel produces effect
- `micro counterfactual heuristic` - General CF-based suggestion

**Budget**: Each rollout costs 0.02 from imagination budget.

---

### 30. Questioning Engine With Teeth (Q-FIELD BLOCKING)

**Location**: `scientific_method_engine.py` class `QuestioningEngineWithTeeth` (lines ~1400-1600)

**Purpose**: Questions that FORCE agent to think, not just log. Critical questions BLOCK normal actions.

**Console Tag**: `[QUESTIONING]` e.g., `ACTION1 blocked by ['Q9'], substituting ACTION6`

**Core Questions** (Q1-Q9):
| Question | Query | Type | BLOCKS? |
|----------|-------|------|---------|
| Q1 | What is the teacher showing me? | lesson_content | No |
| Q2 | What changed between examples? | pattern_detection | No |
| Q3 | What lessons have I learned before? | prior_understanding | No |
| Q4 | What am I being asked to manipulate? | lesson_subject | **YES** |
| Q5 | What demonstrates understanding? | success_criteria | No |
| Q6 | What have my peers understood? | study_group_notes | No |
| Q7 | What conceptual tools do I have? | vocabulary | No |
| Q8 | What do I think this lesson is about? | interpretation | No |
| Q9 | Does my interpretation explain all examples? | self_test | **YES** |
| META | Why am I stuck? | metacognitive | **YES** |

**Blocking Questions** (Q4, Q9, META):
- When triggered, ONLY certain actions allowed
- Q4 blocks: Allows `exploration`, `discovery`, `ACTION1-4`
- Q9 blocks: Allows `revise_theory`, `test_alternative`, `ACTION5-7`
- META blocks: Allows `random`, `test_alternative`, `exploration`

**Score Modifier**: Blocked proposals get `score = 0.0`, allowed proposals get boosted (1.3-1.5x).

---

### 31. Coordinate Oscillation & Pseudo-Button Pathfinding (ACTION HANDLER)

**Location**: `action_handler.py` class `ActionHandler`

**Purpose**: Detect when agent is bouncing between 2-3 coordinates unproductively, and break the loop.

**Console Tags**: 
- `[WARN] Coordinate oscillation detected: {coords}`
- `[SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding`
- `[TARGET] Pathfinding target: (x, y)`

**Detection Logic**:
```python
# In last 6 clicks, only 2-3 unique coordinates used = oscillation
if len(unique_coords) <= 3 and max_count >= 3:
    result['oscillation_detected'] = True
    self.visual_analyzer.oscillation_detected = True
```

**Recovery**: When oscillation detected, tries "combination point" between oscillating targets.

**Pseudo-Button Exemption**: Known buttons (toggles, switches) exempt from oscillation detection.

---

### 32. Grid Exploration System (VISUAL ANALYZER)

**Location**: `visual_analyzer.py` method `_generate_grid_exploration_targets()`

**Purpose**: When stuck, systematically walk an 8x8 grid across the frame to find undiscovered targets.

**Console Tag**: `[GRID] Generated 5 grid exploration targets (index=N)`

**How It Works**:
1. Frame divided into 8x8 pixel grid
2. Walking index tracks position in grid
3. Returns 5 targets at a time, advances index by 5
4. Produces targets with type `grid_exploration` and reason like `Grid exploration (52,20) - systematic search`

**Trigger**: When visual analyzer has few/no targets and agent appears stuck.

---

### 33. Network Object Inventory (SELF-MODEL CONTEXT)

**Location**: `agent_self_model.py` method `get_network_object_inventory()`

**Purpose**: Query network knowledge about what objects are toggleable/moveable/interactable on this level.

**Console Tag**: `[NETWORK-INVENTORY] {game} L{level}: X toggleable, Y moveable, Z interactable positions`

**Data Returned**:
```python
{
    'toggleable': [list of colors that toggle],
    'moveable': [list of colors that move],
    'interactable': [list of (x,y) positions],
    'total_unique': count
}
```

**Integration**: Used to bias ACTION6 target selection toward known-interactable positions.

---

### 34. Metacognitive Prediction System (SELF-MODEL)

**Location**: `agent_self_model.py` class `AgentSelfModel`

**Purpose**: Make predictions about action outcomes and learn from correct/wrong predictions.

**Console Tags**:
- `[METACOG] PREDICTION: If 'theory' then ACTION should cause 'expected_effect'`
- `[METACOG] PREDICTION CORRECT: Theory 'X' confirmed!`
- `[METACOG] PREDICTION WRONG: Expected 'X', got 'Y'`
- `[METACOG] PREDICTION TYPE SUPPRESSED: 'type' failed Nx consecutively`
- `[METACOG] THEORY REVISED: 'old_theory' -> 'new_theory [failed: reason]'`

**Prediction Types**:
- `frame_change` - Expect frame to change
- `object_control` - Expect to discover object control
- `score_delta` - Expect score to change

**Suppression Mechanism**: After 50+ consecutive wrong predictions of same type, that type gets suppressed.

---

### 35. Primitive Stuck Detection (EXPLORATION TRIGGER)

**Location**: `core_gameplay.py` method calls to `primitive_helper.detect_stuck_pattern()`

**Purpose**: Use metacognition primitives to detect stuck state and trigger escape mode.

**Console Tag**: `[PRIMITIVE] Stuck pattern detected by primitives`

**Stuck Indicators**:
- Same position for N frames
- Same actions repeating
- No score change for extended period
- Low frame diversity

**Integration**: When primitive detects stuck, sets `self._is_stuck = True` which triggers:
1. Force exploration mode
2. Clear pattern queues
3. Emergency strategy change if 15+/20 frames stuck

---

### 36. Infinite Loop Breaker (EMERGENCY RECOVERY)

**Location**: `core_gameplay.py` lines ~11270-11360

**Purpose**: Detect pathological stuck loops (80+ stuck detections) and force dramatic action.

**Console Tag**: `[LOOP] INFINITE STUCK LOOP DETECTED! (N/20 frames stuck)`

**Trigger**: `recent_stuck_count >= 15` out of last 20 frames.

**Recovery Actions**:
1. Set `_force_exploration_mode = True`
2. Clear `_pattern_action_queue`
3. Clear `_meta_pattern_tracker`
4. Force symbolic analysis on current frame
5. Pick random exploration action using action filter
6. Return `"EMERGENCY: Breaking infinite stuck loop with random exploration"`

---

### 37. Survey System (CODS ENVIRONMENT SURVEY)

**Location**: `core_gameplay.py` method `_build_survey_context()` lines ~18424-18510

**Purpose**: At level start or when stuck, survey the visual environment using CODS primitives to detect game features and suggest appropriate primitives.

**Reasoning Log Section**: `9_survey`

**Fields**:
```python
{
    'surveyed': bool,           # Whether survey was run
    'trigger': str,             # 'level_start' | 'stuck_detected' | 'unknown'
    'game_signature': str,      # Detected game type pattern
    'detected_features': {
        'has_pipes': bool,      # Flow/pipe structures detected
        'has_containers': bool, # Enclosed regions detected
        'has_symmetry': bool,   # Symmetric patterns detected
        'has_templates': bool,  # Template objects detected
        'has_holes': bool,      # Holes/gaps detected
        'unique_colors': int,   # Color count
        'dominant_color': int,  # Most common color
        'rare_colors': [int],   # Least common colors
        'edge_density': float,  # Density measure
        'symmetry_axes': int    # Number of symmetry axes
    },
    'suggested_primitives': [   # Primitives suggested based on features
        {'primitive': str, 'reason': str, 'priority': int}
    ],
    'primitive_chains': [       # Multi-step primitive chains
        {'chain': [str], 'applies_to': str}
    ],
    'action_suggestions': [     # Concrete action suggestions
        {'action': str, 'reason': str, 'confidence': float}
    ],
    'strategy_hints': [str]     # High-level strategy hints
}
```

**Implementation Logic**:
1. Uses `detect_game_signature` primitive to analyze environment
2. If `has_pipes` → suggests pipe/flow/valve primitives
3. If `has_containers` → suggests container/pour primitives
4. Caches survey in `_current_level_survey` and `_current_primitive_suggestions`

**Integration**: Survey results populate reasoning log section 9, helping CODS focus on relevant primitives.

---

### 38. Deliberation System (TRM-INSPIRED REFINEMENT)

**Location**: `core_gameplay.py` method `_build_deliberation_context()` lines ~18617-18660

**Purpose**: Surface the iterative refinement process inspired by Test-Time Compute research. Tracks how many "thinking passes" were used and whether multiple action sources agreed.

**Reasoning Log Section**: `10_deliberation`

**Fields**:
```python
{
    'refinement_passes': int,       # How many thinking iterations
    'refinement_confidence': float, # Margin between #1 and #2 action (0-1)
    'consensus_actions': [str],     # Actions supported by 2+ sources
    'convergence_achieved': bool,   # Whether early convergence happened
    'time_budget_used': float       # Seconds spent deliberating
}
```

**Data Source**: `self._last_deliberation_result` dataclass from I-Thread deliberation engine

**Key Metrics**:
- `refinement_passes`: Number of proposal/counter-proposal cycles
- `refinement_confidence`: How clear the winner was (low = close race)
- `convergence_achieved`: If all sources agreed before max passes

**Integration**: When `convergence_achieved=True`, action selection bypasses tiebreakers. When `refinement_confidence < 0.2`, may trigger additional exploration.

---

### 39. Replay Learning System (PREDICTION-BASED LEARNING)

**Location**: `core_gameplay.py` method `_build_replay_learning_context()` lines ~18662-18720

**Purpose**: During sequence replay, track predictions about what each action will do. When predictions are wrong, infer new rules. When actions appear unnecessary, flag as "wasted."

**Reasoning Log Section**: `11_replay_learning`

**Fields**:
```python
{
    'is_replay': bool,              # Currently replaying a sequence
    'replay_sequence_id': str,      # Which sequence being replayed
    'prediction_accuracy': float,   # Correct predictions / total (0-1)
    'rules_inferred': int,          # Count of new rules discovered
    'wasted_actions': int,          # Actions flagged as redundant
    'current_prediction': {         # Active prediction for this action
        'action': str,              # Action being predicted
        'expected_effect': str,     # What we expect to happen
        'hypothesis': str           # Why we expect it (rule)
    }
}
```

**Data Source**: `self.replay_learning_engine._current_context` and `_current_prediction`

**Learning Flow**:
1. Before replaying action: Make prediction (action → expected effect)
2. After action: Compare prediction to reality
3. If wrong: Infer new rule, add to knowledge
4. If action had no effect: Flag as potentially wasted

**Output Rules Stored In**: Network knowledge tables for future agents

---

### 40. Imagination Budget System (QUESTION-TIER COMPUTE)

**Location**: `imagination_budget.py` + referenced in `_build_context_tier()` lines ~18258-18280

**Purpose**: Allocate computational budget for reasoning based on situation novelty. Novel situations get more "imagination" budget; familiar situations use cached responses.

**Reasoning Log Section**: Embedded in `5_context.imagination` block

**Fields**:
```python
{
    'budget_total': float,      # Starting budget for this frame
    'budget_spend': float,      # Budget used so far
    'context_mode': str,        # 'novel' | 'familiar' | 'critical'
    'grounding_score': float,   # How grounded in reality (0-1)
    'question_tier': str        # 'Q1' | 'Q2' | 'Q3' | 'Q4' priority
}
```

**Question Tier Hierarchy**:
| Tier | Questions | Budget Multiplier |
|------|-----------|-------------------|
| Q4 (Critical) | Rule explanation, generalization | 2.0x |
| Q3 (Exploration) | Salient variable testing | 1.5x |
| Q2 (Learning) | Reward/punishment mapping | 1.2x |
| Q1 (Basic) | What is changing | 1.0x |

**Budget Allocation**:
- Novel game: +50% budget
- Frontier level: +30% budget
- High surprise_score: +20% budget
- Known territory: -30% budget (fast path)

**Integration**: Higher budget allows more deliberation passes, more CODS operators, more micro-CF rollouts.

---

### 41. Completion Prediction System (STEPS ESTIMATION)

**Location**: Computed in environment context building

**Purpose**: Estimate how many more steps are needed to match a winning sequence, helping agents understand progress toward completion.

**Reasoning Log Section**: `6_environment.completion_prediction`

**Fields**:
```python
{
    'best_sequence_id': str,    # Closest matching sequence
    'steps_to_match': int,      # Actions remaining in sequence
    'match_progress': float,    # 0-1 progress through sequence
    'confidence': float         # How confident in this estimate
}
```

**Calculation**:
1. Find best-matching sequence for current game/level
2. Compare current position to sequence
3. Estimate remaining steps = total_steps - matched_position
4. `match_progress = matched_position / total_steps`

**Integration**: Guides exploration vs exploitation tradeoff. High progress → stay on sequence. Low progress → explore alternatives.

---

### 42. Network Exploration Stats (COVERAGE TRACKING)

**Location**: `network_exploration_tracker.py` + context building in `_build_environment_context()`

**Purpose**: Track population-level exploration coverage. Identifies under-explored "coldspots" and over-explored "hotspots" to distribute agent effort efficiently.

**Reasoning Log Section**: `6_environment.network_exploration`

**Fields**:
```python
{
    'coverage_percent': float,      # % of state space explored
    'unique_explorers': int,        # Distinct agents who've visited
    'exploration_hotspots': [       # Over-explored areas
        {'region': str, 'visits': int}
    ],
    'coldspots': [                  # Under-explored areas
        {'region': str, 'visits': int}
    ],
    'recommended_direction': str    # 'north' | 'south' | 'east' | 'west'
}
```

**Data Source**: `network_exploration_state` table

**Key Metrics**:
- `coverage_percent`: Ratio of visited states to estimated total states
- `exploration_hotspots`: Regions with 3+ agent visits (diminishing returns)
- `coldspots`: Regions with 0-1 visits (high value targets)
- `recommended_direction`: Suggests direction toward nearest coldspot

**Integration**: Agents bias exploration toward coldspots. Pioneer agents especially prioritize low-coverage regions.

---

## Dependency Map: What Affects What

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BEFORE GAMEPLAY STARTS                                 │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ 3-Try Sequence   │  │ Multi-Stage      │  │ Breakthrough     │        │
│  │ Fallback (14)    │→ │ Pipeline (15)    │  │ Budget (24)      │        │
│  │                  │  │                  │  │                  │        │
│  │ Determines:      │  │ Fallback for     │  │ Determines:      │        │
│  │ sequence to use  │  │ sequence lookup  │  │ action budget    │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    DURING EACH ACTION                                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                   ACTION SELECTION LADDER                         │    │
│  │     (Documented in main section: features 1-13 + 29-30)           │    │
│  │                                                                   │    │
│  │  1. Discovery Exploitation                                        │    │
│  │  2. Position-Bucket Death Avoidance                               │    │
│  │  3. Embedding Suggestion                                          │    │
│  │  4. Frontier Topology                                             │    │
│  │  5. Exploration Phase Override                                    │    │
│  │  6. MAP-INTEL Collision Recovery                                  │    │
│  │  7. Two-Streams Proposal Collection                               │    │
│  │  8. Theory Gate                                                   │    │
│  │  9. CODS Engine                                                   │    │
│  │  10. Network Action Wisdom                                        │    │
│  │  11. Abstraction Templates                                        │    │
│  │  12. Few-Shot Invariants                                          │    │
│  │  29. Micro-CF Rollouts                   (NEW FROM LOGS)          │    │
│  │  30. Q-Field Blocking (Q4/Q9/META)       (NEW FROM LOGS)          │    │
│  │  13. Smart Action Selection (Fallback)                            │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                   FINALIZATION FILTERS                            │    │
│  │                                                                   │    │
│  │  16. 3-Layer Action Effectiveness Filter                          │    │
│  │  17. Pariah Avoidance                                             │    │
│  │  19. Terminal Pattern Detector                                    │    │
│  │  31. Coordinate Oscillation Detection    (NEW FROM LOGS)          │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    RECOVERY / EMERGENCY SYSTEMS                           │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Primitive Stuck  │  │ Infinite Loop    │  │ Grid Exploration │        │
│  │ Detection (35)   │→ │ Breaker (36)     │  │ (32)             │        │
│  │                  │  │                  │  │                  │        │
│  │ Sets _is_stuck   │  │ Emergency reset  │  │ Systematic frame │        │
│  │ flag             │  │ when 15+/20 stuck│  │ scanning         │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND / CONTEXT                                   │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Sensation Engine │  │ I-Thread (21)    │  │ Regulatory       │        │
│  │ (20)             │  │                  │  │ Signals (25)     │        │
│  │                  │  │ Manages w_A/w_B  │  │                  │        │
│  │ Provides Stream  │  │ weights used in  │  │ Network-wide     │        │
│  │ A/B sensations   │  │ Two-Streams      │  │ param adjustments│        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Frustration      │  │ Near-Miss        │  │ Subgoal Planner  │        │
│  │ Detector (18)    │  │ Analyzer (22)    │  │ (23)             │        │
│  │                  │  │                  │  │                  │        │
│  │ Detects stuck    │  │ Post-hoc learn   │  │ Hierarchical     │        │
│  │ agents, quorum   │  │ from failures    │  │ goal planning    │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Network Inventory│  │ Metacog Predict  │  │ Visual Analyzer  │        │
│  │ (33)             │  │ (34)             │  │ (26)             │        │
│  │                  │  │                  │  │                  │        │
│  │ toggleable/      │  │ Make/evaluate    │  │ Identifies       │        │
│  │ moveable objects │  │ predictions      │  │ click targets    │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Survey System    │  │ Deliberation     │  │ Replay Learning  │        │
│  │ (37)             │  │ (38)             │  │ (39)             │        │
│  │                  │  │                  │  │                  │        │
│  │ CODS environ     │  │ TRM iterative    │  │ Prediction-based │        │
│  │ feature detect   │  │ refinement       │  │ rule inference   │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Imagination      │  │ Completion       │  │ Network Explor   │        │
│  │ Budget (40)      │  │ Prediction (41)  │  │ Stats (42)       │        │
│  │                  │  │                  │  │                  │        │
│  │ Question-tier    │  │ Steps to match   │  │ Coverage %,      │        │
│  │ compute alloc    │  │ estimation       │  │ coldspots        │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-29 | Added 6 more systems from reasoning log analysis (features 37-42) |
| 2026-01-29 | Documented Survey System, Deliberation, Replay Learning, Imagination Budget |
| 2026-01-29 | Documented Completion Prediction and Network Exploration Stats |
| 2026-01-29 | Added 8 more systems from console log analysis (features 29-36) |
| 2026-01-29 | Added MICRO-CF and Q-FIELD to main ladder diagram |
| 2026-01-29 | Added graduated position-aware death avoidance |
| 2026-01-29 | Fixed binary blocking -> probabilistic avoidance |
| 2026-01-29 | Added time decay and survival signals to danger calculation |
| 2026-01-29 | Added 13 external systems documentation (features 14-26) |
| 2026-01-28 | Added "least-bad" handling for all-negative network wisdom |
| 2026-01-28 | Added mastery tier confidence boost |

---

**END OF DOCUMENT**
