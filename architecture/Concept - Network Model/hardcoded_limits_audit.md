# Hardcoded Limits Audit - core_gameplay.py
**Generated**: January 8, 2026
**Purpose**: Comprehensive list of all hardcoded limits, thresholds, and special modes that may impact gameplay, reasoning, discovery, and growth

---

## Table of Contents
1. [Action & Game Budget Limits](#action--game-budget-limits)
2. [Stuck State Detection Thresholds](#stuck-state-detection-thresholds)
3. [Escape Mode & Recovery Limits](#escape-mode--recovery-limits)
4. [API & Error Thresholds](#api--error-thresholds)
5. [Confidence & Reliability Thresholds](#confidence--reliability-thresholds)
6. [Discovery & Learning Limits](#discovery--learning-limits)
7. [History Window Sizes](#history-window-sizes)
8. [Sequence System Limits](#sequence-system-limits)
9. [Hypothesis & Self-Model Limits](#hypothesis--self-model-limits)
10. [Random Chance Thresholds](#random-chance-thresholds)
11. [Special Modes & Conditions](#special-modes--conditions)
12. [CODS & Abstraction Thresholds](#cods--abstraction-thresholds)
13. [Prestige & Social Thresholds](#prestige--social-thresholds)

---

## Action & Game Budget Limits

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L1556 | `max_actions_per_level` | **250** | Max actions allowed per level | [MEDIUM] May be too low for complex levels |
| L1557 | `max_total_actions` | **2000** | Max actions across all levels (was 7000) | [HIGH] Reduced for "fail fast" - may prevent complex exploration |
| L1558 | `action_timeout` | **30.0** | Seconds per action timeout | [LOW] |
| L4340 | `max_action_history` | **1000** | Prevent memory leaks in long games | [LOW] |
| L1566 | `hypothesis_warmup_actions` | **5** | Actions before hypothesis can influence decisions | [MEDIUM] May delay smart action selection |
| L1570 | `max_repeats_per_game` | **5** | Limit game repetition in diversity mode | [LOW] Only in diversity mode |

---

## Stuck State Detection Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L5054 | `STUCK_STATE_THRESHOLD` | **200** | No-frame-change actions before stuck detection (was 15) | [MEDIUM] Raised from 15 - good |
| L5055 | `STUCK_STATE_THRESHOLD_FRONTIER` | **200** | Same for frontier levels (was 30) | [MEDIUM] Raised from 30 - good |
| L6225 | `cycle_trigger_threshold` | **200** | Must have 200 no-frame-change + cycle to trigger early | [MEDIUM] Raised from 15 - good |
| L5059 | `CYCLE_DETECTION_WINDOW` | **8** | Check last 8 actions for oscillation cycles | [LOW] |
| L257 | Score stagnant detection | **last 5** scores identical | Score stagnation threshold | [LOW] |
| L258 | Action repeating detection | **last 10** actions, **≤2** unique | Action repetition threshold | [LOW] |

---

## Escape Mode & Recovery Limits

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L5065 | `ESCAPE_ATTEMPTS_STAGE1` | **7** | Intelligent escape with CODS | [MEDIUM] |
| L5066 | `ESCAPE_ATTEMPTS_STAGE2` | **7** | After resetting biases | [MEDIUM] |
| L5067 | `ESCAPE_ATTEMPTS_STAGE3` | **7** | Pure random exploration | [MEDIUM] |
| L5068 | `ESCAPE_ATTEMPTS_MAX` | **21** | Total escape attempts (7+7+7) | [HIGH] 21 may be too few for complex situations |
| L6409 | Escape mode reset | **STUCK_STATE_THRESHOLD - 10** | Allow 10 more tries after escape action | [LOW] |

---

## API & Error Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L5049 | `MAX_API_RESETS_PER_LEVEL` | **2** | Max API resets allowed per level | [MEDIUM] May be too restrictive |
| L5050 | `API_RESET_THRESHOLD` | **1000** | No-progress actions before API reset (optimizer) | [LOW] Increased for exploration |
| L5083 | `MAX_CONSECUTIVE_API_ERRORS` | **5** | Break out after 5 consecutive API errors | [LOW] |

---

## Confidence & Reliability Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L1939 | Sequence success rate threshold | **>0.5** = promote, **<0.3** = demote | Sequence validation rating | [MEDIUM] |
| L3317, L6725 | Self-model control confidence | **>0.3** | Threshold to report controlled objects | [LOW] |
| L6049 | Control learning confidence | ~~>0.5~~ **>0.3** | Threshold for learning from movement | [FIXED] Lowered to capture weaker correlations |
| L9309 | Control confidence for goal tracking | **≥0.5** | Use self-model for goal navigation | [MEDIUM] |
| L9959 | Competence threshold | **≥0.6** | Trust competence for action selection | [MEDIUM] |
| L10132 | Hypothesis confidence threshold | **>0.5** | Use hypothesis for action selection | [MEDIUM] |
| L10350 | Pattern confidence threshold | **>0.5** | Trust meta-learned patterns | [MEDIUM] |
| L15092 | High reliability indicator | **>0.8** | Flag highly reliable hypotheses | [LOW] |
| L18138 | Low reliability warning | **<0.3** | Flag unreliable sequences | [LOW] |
| L18465 | Reliability indicator cutoff | **<0.5** | Show "?" for uncertain sequences | [LOW] |
| L16910, L16926 | Hypothesis retirement | confidence **<0.2**, downvotes **>5** | Soft retirement threshold | [LOW] |

---

## Discovery & Learning Limits

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| ~~L11256, L11438~~ | ~~Discovery phase~~ | ~~**first 20 actions**~~ | **REMOVED** - Discovery now runs always | [FIXED] |
| L15353-15363 | "425 Too Early" resolution | ~~20 frames~~ **10 frames** | Force resolution after 10 frames | [FIXED] Reduced to enter speculation mode faster |
| L13335-13339 | Forced hypothesis commitment | ~~30 frames~~ **100 frames** | Commit to best hypothesis after 100 frames | [FIXED] Allow natural theory evolution |
| L13355 | Heuristic guess commitment | ~~50 frames~~ **150 frames** | Guess at controlled object after 150 frames | [FIXED] Last resort only |
| L10329-10330 | Pattern abandonment | **10 applications** | Abandon pattern if no progress after 10 uses | [MEDIUM] |
| L5902 | Metacog failure threshold | **≥3 failures** | Trigger recovery after 3 failures | [LOW] |
| L1885, L4727 | Multi-stage pipeline trigger | **3 failures** | Fall back to multi-stage matching | [LOW] |

---

## History Window Sizes

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L11732 | `_score_history` | **last 20** | Keep last 20 scores | [LOW] |
| L11737 | `_action_history` | **last 20** | Keep last 20 actions | [LOW] |
| L2826 | `_recent_actions` | **last 9** | Keep last 9 actions for reasoning | [LOW] |
| L15411 | Frame diff coordinates | **limit 20** | Analyze up to 20 frame changes | [LOW] |
| L3335, L3348 | Objects for impression | **top 3** for level wins | Form semantic impressions | [LOW] |
| L3861 | Objects for impressions (game end) | **top 5** | Form impressions at game end | [LOW] |
| L9371, L9426 | Direction history limit | **>10** = trim | Keep direction history manageable | [LOW] |

---

## Sequence System Limits

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L1924, L4738 | 3-Try system | **3 sequences** | Try top 3 sequences before giving up | [MEDIUM] May miss good sequences |
| L1937, L4751 | Validation attempts minimum | **≥3 attempts** | Require 3 validations for rating | [LOW] |
| L18320 | L1-L2 deactivation threshold | **15 failures** | Deactivate after 15 consecutive failures | [LOW] |
| L18278 | L3+ deactivation threshold | **10 failures** | Deactivate after 10 failures (with redundancy) | [LOW] |
| L19556, L19561 | Quick deactivation | **3 failures** | Deactivate after 3 consecutive failures | [HIGH] May be too aggressive |
| L20212-20213 | L1-L2 quick deactivation | **12 failures** | Deactivate after 12 failures | [MEDIUM] |
| L20224 | Flagging threshold | **6 failures** | Flag (not deactivate) after 6 failures | [LOW] |
| L18731 | Stuck threshold in replay | **sequence_length + 10** | Allow 10 extra actions in replay | [LOW] |
| L18880-18893 | Protected zone in replay | **last 10%**, **last 5 actions**, or **progress ≥0.90** | Don't deviate near end | [LOW] |
| L20555 | Sequence match ratio | **≥0.90** (was 0.95) | Required match for "slip into sequence" | [MEDIUM] |

---

## Hypothesis & Self-Model Limits

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L13267, L13493 | Controlled objects limit | **10** | Max objects in reasoning JSON | [LOW] |
| L14640 | Perceived objects limit | **10** | Max objects in API calls | [LOW] |
| L17446 | Object detection limit | **10** | Limit objects for performance | [LOW] |
| L2621 | Contradiction threshold | **20 actions** | Contradict hypothesis after 20 no-improvement actions | [MEDIUM] |
| L6038 | Control pattern analysis | ~~every 5 actions~~ **every action** | Analyze control patterns per consciousness loop | [FIXED] Runs every frame now |
| L6097 | Network contribution | **every 50 actions** | Share with network every 50 actions | [LOW] |
| L2580 | Session logging | **every 50 actions** | Log session state | [LOW] |
| L2703 | Frontier contribution | **every 10 actions** | Contribute to network | [LOW] |

---

## Random Chance Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L9130 | wA influence | **random < wA** | Apply action bias based on wA | [LOW] |
| L9192, L9229 | wB influence | **random < wB** | Apply behavior bias based on wB | [LOW] |
| L9381, L9383 | Oscillation escape | **random < 0.5** | 50/50 direction change on oscillation | [LOW] |
| L9931 | Random action chance | **random < 0.5** | 50% chance of random action in some modes | [MEDIUM] |
| L19178 | Wait action chance | **random < 0.4** | 40% chance to try ACTION5 (wait) | [LOW] |
| L19197 | Direction variation | **random < 0.6** | 60% chance to vary direction | [LOW] |
| L21446 | Strategy switch | **random < 0.3** | 30% chance to try different strategy | [LOW] |

---

## Special Modes & Conditions

### 1. ESCAPE MODE (L5060-5075)
**Trigger**: `consecutive_no_frame_change >= STUCK_STATE_THRESHOLD` (200)
**Stages**:
- Stage 1 (attempts 1-7): Intelligent escape using CODS, Q1-Q5, network wisdom
- Stage 2 (attempts 8-14): Reset biases, try different strategies
- Stage 3 (attempts 15-21): Pure random exploration (last resort)

**Flags**:
- `in_escape_mode = True` when stuck detected
- `pure_exploration_mode = True` after all 21 attempts fail

### 2. LEARNING MODES (L1563)
**Options**: `'exploit'`, `'explore'`, `'smart_exploration'` (default)
**Impact**: Determines sequence replay behavior and exploration strategy

### 3. FRONTIER LOCK MODE (L4635)
**Trigger**: Game marked as frontier-only
**Effect**: Skips sequence replay/validation, exploration-only

### 4. DIVERSITY MODE (L1568-1572)
**Options**:
- `diversity_mode: False` (default)
- `max_repeats_per_game: 5`
- `enforce_game_diversity: False`
- `novel_game_priority: 1.0`

**Effect**: Prevents overfitting to specific games

### 5. SPECULATION MODE (L15363)
**Trigger**: After 20 frames with no confirmed data
**Effect**: Changes from "425 Too Early" to:
- `"SPECULATING: Object control not yet confirmed"`
- `"EXPLORING: Testing game mechanics"`
- `"UNVALIDATED: Insufficient correlation data"`

### 6. PERSONA SPAWN CONDITIONS (L6240-6260)
**Trigger**: Stuck state detected
- **Early spawn**: 30 frames no progress (NEW - investigation mode)
- **Escape mode spawn**: 200 frames (when escape mode activates)

**Persona**: `stuckness_detector` spawned to investigate

### 7. AGENT ROLES (L4633)
**Modes**: `'optimizer'`, `'generalist'`, `'pioneer'`, `'exploiter'`
**Impact**: Determines sequence replay behavior and game selection

### 8. ALLOWED SPINE MODES (L1091)
**Values**: `{'LIVE', 'REPLAY_VALIDATION', 'EVAL', 'LEGACY'}`
**Purpose**: Validate mode parameter for spine writes

### 9. COGNITIVE STAGE PROGRESSION (L8302-8303)
**Conditions**:
- `allow_observers`: stage_numeric >= 2
- `allow_synthesis`: stage_numeric >= 3

---

## CODS & Abstraction Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L10451 | Frontier CODS threshold | **0.35** | Lower threshold for frontier exploration | [LOW] |
| L10454 | Exploration CODS threshold | **0.30** | Even lower when exploring on its own | [LOW] |
| L10457 | Standard CODS threshold | **0.55** | Standard threshold for beaten levels | [MEDIUM] May be too strict |
| L10528 | CODS confidence for use | **≥0.4** | Threshold to use CODS discovery | [MEDIUM] |
| L12666 | CODS confidence for action | **≥0.5** | Use CODS for action selection | [MEDIUM] |
| L2062 | Abstraction threshold | **0.7** | Risk tolerance for abstraction | [LOW] |
| L1431 | Relational patterns harvest | **max 150 rows** | Limit pattern harvest for performance | [LOW] |
| L8908 | Click exploration radius | **20** | Wide exploration radius for clicks | [LOW] |

---

## Prestige & Social Thresholds

| Location | Limit | Value | Purpose | Concern Level |
|----------|-------|-------|---------|---------------|
| L10218 | Frustrated emotion threshold | **emotional_network < 0.3** | Trigger exploration on frustration | [LOW] |
| L10227 | Semantic network threshold | **> 0.7** | High network trust for action | [LOW] |
| L10238 | Self-trust bias threshold | **> 0.6** | Trust self over network | [LOW] |
| L10801 | Net influence threshold | **> 0.3** | Apply network influence to decisions | [LOW] |
| L17287 | Preferred role confidence | **> 0.6** | Apply role preference | [LOW] |
| L6488, L6779 | Self-network bias boost | **+0.25** | Boost on successful discovery | [LOW] |

---

## Summary of High-Concern Limits

### FIXED (2025-01-08)
1. **`Forced hypothesis commitment`** - Changed 30→100 frames, allows natural theory evolution
2. **`Heuristic guess commitment`** - Changed 50→150 frames, last resort only
3. **`Control learning confidence`** - Changed >0.5→>0.3, captures weaker correlations
4. **`Pattern analysis frequency`** - Changed every 5→every 1 action, consciousness runs every frame
5. **`Early persona spawn`** - Added at 30 frames (before 200 escape mode)
6. **`"425 Too Early" resolution`** - Changed 20→10 frames, enter speculation mode faster
7. **`Discovery phase limit`** - REMOVED, discovery runs always now

### REMAINING CRITICAL (Should Review/Remove)
1. **`max_total_actions: 2000`** - Reduced from 7000, may prevent complex exploration
2. **`ESCAPE_ATTEMPTS_MAX: 21`** - May be insufficient for complex stuck situations
3. **Quick deactivation after 3 failures** - Too aggressive, may kill good sequences

### MEDIUM (Consider Adjusting)
1. **`max_actions_per_level: 250`** - May be too low for complex levels
2. **`hypothesis_warmup_actions: 5`** - May delay smart action selection
3. **Control learning confidence > 0.5** - May be too strict
4. **Contradiction after 20 actions** - May contradict too early
5. **3-Try system limit** - May miss good sequences ranked 4+
6. **Pattern abandonment after 10 uses** - May abandon working patterns
7. **"425 Too Early" resolution at 20 frames** - May need game-specific tuning

---

## Recommendations

1. **Make key limits configurable** via `game_config` or environment variables
2. **Add adaptive limits** that scale with game complexity
3. **Log limit triggers** to database for analysis of whether limits help or hurt
4. **Consider removing or raising**:
   - max_total_actions back to 7000 for complex games
   - Escape attempts to 42+ (double current)
   - Forced commitment thresholds to 100+ frames
5. **Consider lowering**:
   - Control learning confidence to 0.4
   - CODS standard threshold to 0.45
6. **Add game-type-specific overrides** for known complex games

---

**END OF AUDIT**
