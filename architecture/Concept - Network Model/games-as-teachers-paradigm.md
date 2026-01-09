# Games as Teachers Paradigm
**Status**: TABLED - Implement if current changes don't breakthrough levels  
**Date Conceived**: December 29, 2025  
**Purpose**: Fundamental reframe from "solving puzzles" to "extracting lessons"

---

## Core Insight

ARC-AGI puzzles aren't puzzles to solve - they're **demonstrations of principles**. Each game is a worked example saying "here's a concept - can you recognize it?"

The win condition isn't arbitrary - it's the **assessment** of whether you grasped what was being taught.

---

## Paradigm Comparison

### Current Paradigm
```
ORACLE (Authority) -> oversees -> NETWORK -> guides -> AGENTS -> play -> GAMES
```

### Flipped Paradigm
```
GAMES (Teachers) -> teach -> AGENTS (Students) <- facilitate <- ORACLE (TA)
```

---

## Why This Works

| Current Framing | Flipped Framing |
|-----------------|-----------------|
| "What objects exist in frame?" | "What is the teacher showing me?" |
| "What can I do?" | "What is the teacher asking me to understand?" |
| "I died" | "I misunderstood the lesson" |
| "I won" | "I demonstrated understanding" |
| "Copy winning sequence" | "Learn from peer who understood the lesson" |
| "Random exploration" | "Re-reading the lesson with fresh eyes" |

---

## The Pedagogical Structure Already Present

Every game has:
- **Examples** (initial frames showing the pattern)
- **Practice problems** (levels that test the same concept with variations)
- **Assessment** (win condition that requires demonstrating understanding)

The oracle saying "I can't tell you the answer" isn't a limitation - it's **pedagogically correct**.

---

## Implementation Plan

### 1. REASONING LOGS (Q1-Q8) Reframe

**Current:**
```
Q1: "What is happening?" (observe state)
Q2: "What changed?" (detect deltas)
Q3: "Who am I?" (autobiography)
Q4: "What do I control?" (self-model)
Q5: "What causes score changes?" (goal variables)
Q6: "What does network know?" (wA/wB)
Q7: "What operators are available?" (CODS)
Q8: "What am I assuming?" (metacognitive)
```

**Reframed as Student Questions:**
```
Q1: "What is the teacher showing me?" (lesson content)
Q2: "What changed between examples?" (pattern detection)
Q3: "What lessons have I learned before?" (prior understanding)
Q4: "What am I being asked to manipulate?" (lesson subject)
Q5: "What demonstrates understanding?" (success criteria)
Q6: "What have my peers understood?" (study group notes)
Q7: "What conceptual tools do I have?" (vocabulary)
Q8: "What do I think this lesson is about?" (interpretation)
```

**Add Q9:** "Does my interpretation explain all examples?" (self-test)

---

### 2. METACOGNITIVE ENGINE Reframe

**Current:**
```python
make_prediction("If I take ACTION3, score should increase")
evaluate_prediction(actual_outcome)
revise_theory("Theory was wrong, update it")
```

**Reframed:**
```python
interpret_lesson("I think the teacher is showing: enclosed regions fill")
test_interpretation("If my interpretation is right, clicking here should fill")
refine_interpretation("Example 3 contradicts my reading - what did I miss?")
```

**Win Reflection Change:**
```python
# Current
def generate_win_reflection(self, actions_taken, key_context):
    return f"Won by taking {actions_taken} actions"

# Reframed
def extract_lesson(self, game_type, level, key_context):
    """What was the teacher demonstrating?"""
    return f"Lesson: {concept} - demonstrated by {transformation_pattern}"
```

---

### 3. CODS SYSTEM Reframe

**Current Purpose:** "What operators can I use to play?"  
**Reframed Purpose:** "What conceptual vocabulary do I have to describe the lesson?"

- CODS isn't "tools to solve puzzles"
- CODS is "vocabulary to describe what teacher is showing"
- An agent without `flood_fill` concept can't even *describe* a containment lesson
- Unlocking primitives = expanding conceptual vocabulary

**CODS-TEACHER becomes CURRICULUM-TRACKER:**
- "What concepts have been demonstrated across games?"
- "What vocabulary does the network have for this game type?"
- "What concepts are we missing vocabulary for?"

---

### 4. WINNING SEQUENCES TABLE Reframe

**Current Schema:**
```sql
winning_sequences (
    sequence_id,
    game_type,
    action_sequence,  -- THE ANSWER
    action_count
)
```

**Reframed Schema:**
```sql
demonstrated_lessons (
    lesson_id,
    game_type,
    lesson_interpretation,  -- "Teacher showed containment fills on boundary touch"
    supporting_evidence,     -- The action sequence that demonstrated understanding
    concept_tags,           -- ['containment', 'flood_fill', 'boundary']
    generalization_level,   -- Does this apply to all levels? All similar games?
    validated_by_transfer   -- Did interpretation work on variation?
)
```

Action sequences become **evidence of understanding**, not the understanding itself.

---

### 5. NETWORK HYPOTHESIS TABLES Reframe

**Current:**
```sql
network_object_control_hypotheses (
    hypothesis: "ACTION1 moves color_3 up"
    reliability_score: 0.75
)
```

**Reframed:**
```sql
network_lesson_interpretations (
    interpretation: "The teacher is showing directional control of colored objects"
    supporting_observations: ["ACTION1 moved color_3 up 3 times"]
    concept_category: "object_control"
    explains_examples: [1, 2, 3]  -- Which levels/examples does this explain?
    fails_to_explain: [4]         -- Where does interpretation break down?
    confidence: 0.75
)
```

**Critical Addition:** Track "Explains vs Fails to Explain" - a good interpretation explains ALL examples.

---

### 6. PRESTIGE SYSTEM Reframe

**Current:**
```python
prestige = wins * 0.5 + sequences_used * 0.3 + ...
```

**Reframed:**
```python
prestige = (
    lessons_extracted * 0.3 +           # How many concepts identified
    interpretations_adopted * 0.4 +     # Did peers use your understanding
    transfer_success_rate * 0.3         # Did understanding generalize
)
```

Incentivizes **teachable understanding**, not just winning.

---

### 7. AGENT ROLES Reframe

**Current:**
| Role | Purpose |
|------|---------|
| Pioneer | Explore unbeaten games |
| Optimizer | Refine winning sequences |
| Generalist | Play anywhere |
| Exploiter | Micro-optimize |

**Reframed:**
| Role | Purpose |
|------|---------|
| Explorer | "What is this new teacher showing?" (first interpretation) |
| Validator | "Does the interpretation explain all examples?" (stress test) |
| Tutor | "Share understanding with struggling peers" (knowledge transfer) |
| Synthesizer | "Find common lessons across teachers" (concept unification) |

---

### 8. WIN DETECTION Reframe

**Current:**
```python
if game_state.state == "WIN":
    self._capture_winning_sequence()
```

**Reframed:**
```python
if game_state.state == "WIN":
    lesson = self._extract_lesson_from_demonstration(
        initial_frames=self._level_initial_frames,
        win_frames=game_state.frame,
        actions_taken=self._action_history
    )
    self._record_demonstrated_understanding(lesson, evidence=self._action_history)
```

Not "what did I do?" but "what did I demonstrate understanding of?"

---

### 9. FAILURE HANDLING Reframe

**Current:**
- Death = bad action, avoid
- Stuck = try random things
- Game over = lost

**Reframed:**
- Death = "I misunderstood the lesson"
- Stuck = "I haven't grasped what's being shown"
- Game over = "Need to re-read the examples"

```python
# Reframed failure recording
def record_misunderstanding(interpretation, contradiction):
    # "My interpretation (containment) was contradicted by example 4"
    # "Need to revise: maybe teacher showing deletion, not filling"
```

---

### 10. ORACLE'S ROLE as Teaching Assistant

| TA Does | TA Doesn't |
|---------|------------|
| "Your interpretation doesn't explain example 3" | "The answer is ACTION4" |
| "Compare your understanding with Agent X" | "Copy Agent X's sequence" |
| "What concept might unify examples 1-4?" | "The concept is containment" |
| "Your test didn't isolate the variable" | "Test ACTION2 instead" |

---

### 11. AUTOBIOGRAPHICAL SYSTEM Reframe

**Current:**
- wA = trust self (based on win rates)
- wB = trust network (based on experience)

**Reframed:**
- wA = "My interpretations have been accurate"
- wB = "Peer interpretations have helped me understand"

```python
# Current
if my_win_rate > network_win_rate:
    trust_self()

# Reframed  
if my_interpretations_transferred_successfully:
    trust_self()
if peer_interpretations_helped_me_understand_new_games:
    trust_network()
```

The metric isn't wins - it's **understanding that transfers**.

---

### 12. NEW DATABASE TABLES

```sql
-- What lessons have been extracted from each game type
CREATE TABLE lesson_catalog (
    lesson_id TEXT PRIMARY KEY,
    game_type TEXT NOT NULL,
    concept_demonstrated TEXT,          -- "containment", "symmetry", etc.
    supporting_examples TEXT,           -- JSON of level:interpretation pairs
    contradicting_examples TEXT,        -- Where interpretation fails
    confidence REAL DEFAULT 0.5,
    contributed_by TEXT,                -- Agent who first articulated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cross-game concept unification
CREATE TABLE concept_ontology (
    concept_name TEXT PRIMARY KEY,      -- 'containment', 'symmetry', 'transformation'
    game_types_demonstrating TEXT,      -- JSON array of game types
    vocabulary_required TEXT,           -- CODS primitives needed to recognize
    transfer_success_rate REAL,         -- How well does knowing this help on new games
    examples_count INTEGER DEFAULT 0
);

-- Agent comprehension tracking
CREATE TABLE agent_understanding (
    agent_id TEXT NOT NULL,
    game_type TEXT NOT NULL,
    current_interpretation TEXT,
    examples_explained TEXT,            -- JSON array of levels explained
    examples_not_explained TEXT,        -- JSON array of levels NOT explained
    last_updated TIMESTAMP,
    PRIMARY KEY (agent_id, game_type)
);
```

---

### 13. FUNDAMENTAL METRIC CHANGE

**Current Success Metric:**
- Win rate
- Games completed
- Levels beaten

**Reframed Success Metric:**
- **Transfer rate**: Does understanding on game A help on unseen game B?
- **Explanation coverage**: What % of examples does interpretation explain?
- **Peer adoption**: Do other agents succeed using your interpretation?

---

## Implementation Priority (When Activated)

1. **Lesson extraction at win** - Change `generate_win_reflection()` to extract concepts, not sequences
2. **Interpretation tables** - Add schema for storing interpretations alongside sequences
3. **Reframe Q8** - Make metacognitive engine ask "what is the lesson?" not "what should I do?"
4. **Transfer testing** - Validate interpretations by testing on variations
5. **Prestige on transfer** - Reward understanding that generalizes, not just winning

---

## The Deepest Implication

This framing suggests that **the current system is optimizing for the wrong objective**.

- Current: Maximize win rate
- Should be: Maximize lesson extraction rate

An agent that loses but articulates "I think the teacher was showing X, but example 3 suggests I'm wrong about Y" is **more valuable** than an agent that wins by copying a sequence.

The first agent is learning. The second is cheating.

---

## Trigger Condition

**Implement this paradigm if:**
- Current metacognitive + wA/wB changes don't lead to level breakthroughs
- Agents continue to plateau at same levels despite system improvements
- Sequence copying dominates over genuine learning

**Success indicators that we DON'T need this:**
- Agents start beating previously unbeaten levels
- New game types get solved faster (transfer happening)
- Win reflections start containing conceptual insights naturally

---

## References

- [reframing learning teaching.md](reframing%20learning%20teaching.md) - Original concept articulation
- [how to reason.md](how%20to%20reason.md) - Metacognitive framework (compatible with this paradigm)
- `.github/copilot-instructions.md` - Master ruleset (would need updates if implemented)
