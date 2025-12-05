# Emergent Reasoning Framework (Compressed)

> **Note:** The classic "make a peanut butter sandwich" assignment shows how ambiguous human instructions require massive explicit code if you brute-force every detail, but a few reasoning filters can collapse it into minimal logic. It's like taking a leg away from a four-legged chair, but rearranging the remaining three to keep it functional.

---

## The Four Core Questions

The lengthy and arduous system for reasoning can be compressed down to four questions:

### 1. What is changing vs. what is fixed?
*Pattern detection + invariance mapping*

- Identifies variables (potential levers)
- Identifies invariants (constraints/rules)

### 2. What punishes me and what rewards me?
*Value grounding + hypothesis priming*

- Maps objects/actions to outcomes without explicit causal modeling
- Identifies goal-relevant and dangerous elements immediately

### 3. What happens if I interact with the most salient variable?
*Targeted experimentation + causal inference*

> "What happens when I act upon the interesting/unusual thing - testing all actions and monitoring outcomes?"

- One intelligent intervention tests multiple hypotheses at once

### 4. What rule explains this across contexts?
*Abstraction + transfer readying*

> "What's the simple principle that would work everywhere, not just here?"

- Extracts the minimal portable principle from observed cause-effect-value triples
- Enables generalization without building full relational graphs

---

## Comprehensive Reference

*The below is for reference only*

---

# Universal Emergent Reasoning Framework
**For Any Agent in Any Domain**

## Core Problem

Current agents detect objects and relate them to "self," but lack causal theories about how object relationships lead to goal states across diverse problem domains.

---

## THE FIVE-STAGE REASONING CYCLE

### STAGE 1: SALIENCE DETECTION (Pattern Seeking)

**What to detect:**

- **Common elements:** What appears consistently? (colors, shapes, patterns, sizes, positions, quantities, sequences, relationships)
- **Rare elements:** What's unusual or unique? (outliers, asymmetries, special markers, rare combinations)
- **Structural invariants:** What remains constant across instances? (grids, boundaries, hierarchies, groupings)

**Cross-domain questions:**

- **Within single environment:** What structures persist level-to-level?
- **Across different environments:** What abstract patterns recur? (containers, keys, goals, obstacles, resources)
- **Temporal:** What changes vs. what stays static?

**Formula:** `Salience = f(rarity, structure, consistency)`

**Output:** Ranked list of "things worth investigating"

---

### STAGE 2: HYPOTHESIS GENERATION (Wondering)

**Generate multiple competing theories:**

**Analogical sources:**
- Past levels in same environment (vertical transfer)
- Different game types with similar structure (horizontal transfer)
- Abstract problem classes (locks/keys, resource management, path-finding, constraint satisfaction)

**Hypothesis templates to consider:**

| Template | Example |
|----------|---------|
| Functional roles | "X might be a [goal/obstacle/tool/resource/constraint]" |
| Causal relationships | "Action A on X might cause effect E" |
| Compositional rules | "Combining X + Y might produce Z" |
| Spatial relationships | "Position of X relative to Y might matter" |
| Temporal sequences | "Order of actions might be critical" |
| Meta-information | "X might be encoding rules about Y" |
| State transitions | "X might transform into Y under conditions C" |

**Formula:** Analogical Mapping + Combinatorial Enumeration

**Key principle:** Generate diverse hypotheses, not just the most likely one

- Include null hypothesis ("X is irrelevant")
- Include inverse relationships ("Maybe I should avoid X, not collect it")
- Include meta-hypotheses ("Maybe the rules change mid-game")

**Output:** Probability distribution over hypothesis space

---

### STAGE 3: ACTIVE EXPERIMENTATION (Testing & Subgoal Generation)

**Experimental design principles:**

1. **Isolation:** Change ONE variable, observe outcome
2. **Discrimination:** Design tests that distinguish between competing hypotheses
3. **Efficiency:** Maximize information gain per action
4. **Safety:** Test in ways that preserve ability to continue (don't immediately lose)

**Intervention types:**

- **Direct manipulation:** Act on object X
- **Compositional:** Combine objects in different ways
- **Spatial:** Move objects to different positions
- **Temporal:** Vary timing/sequence of actions
- **Boundary testing:** Push system to extremes

**Observation protocol:**

- What changed immediately?
- What changed after delay?
- What else changed (side effects)?
- What did NOT change (constraints)?

**Subgoal generation:**
```
If hypothesis H requires condition C:
  -> Generate subgoal: "Achieve condition C"
  -> Generate sub-subgoals: "Steps to reach C"
```

**Formula:** Bayesian Experiment Design + Causal Intervention

**Output:** Updated belief probabilities for each hypothesis

---

### STAGE 4: STRUCTURAL CORRESPONDENCE (Relational Understanding)

**Build explicit mappings between domains:**

**Correspondence types:**

| Type | Example |
|------|---------|
| Object-to-object | "Red button in domain A <-> Lever in domain B" |
| Relationship-to-relationship | "Adjacent-to in A <-> Connected-to in B" |
| Process-to-process | "Collecting in A <-> Unlocking in B" |
| Constraint-to-constraint | "Can't stack in A <-> Weight limit in B" |

**Construct relational graph:**

- **Node:** Object/concept
- **Edge:** Relationship type (causal, spatial, temporal, hierarchical)
- **Properties:** Strength, confidence, conditions

**Key insight extraction:**

- What relationships are **necessary** for success?
- What relationships are **prohibited** (lead to failure)?
- What relationships are **conditional** (context-dependent)?

**Formula:** Relational Alignment + Graph Isomorphism

**Example mappings:**

| Source | Target |
|--------|--------|
| Small pattern | Large pattern (your puzzle) |
| Minimap | Full map (navigation games) |
| Recipe | Meal (cooking) |
| Blueprint | Building (construction) |
| Code | Execution (programming) |

**Output:** Explicit causal/relational model of domain

---

### STAGE 5: GENERALIZATION & TRANSFER (Abstraction)

**Extract domain-independent principles:**

**Perturbation testing (counterfactual reasoning):**

- What if objects were arranged differently?
- What if certain objects were removed?
- What if new objects were added?
- What if quantities changed?
- What if relationships reversed?

**Template extraction:**

```
Specific instance: "Click red buttons to move blocks left"
         |
         v
Object-level rule: "Action buttons control entity movement"
         |
         v
Abstract principle: "Interface elements encode control mappings"
         |
         v
Meta-principle: "Understand symbols before manipulating world"
```

**Transfer predictions:**

- **To new levels:** "This principle should still apply"
- **To new games:** "Similar structure -> similar solution approach"
- **To entirely new domains:** "This is a constraint satisfaction problem"

**Formula:** Template Abstraction + Analogical Projection

**Abstraction hierarchy:**

| Level | Description |
|-------|-------------|
| 0 | Raw perceptual data |
| 1 | Object identification |
| 2 | Relationship detection |
| 3 | Causal models |
| 4 | Problem class recognition |
| 5 | Universal principles |

**Output:** Transferable knowledge schemas

---

## THE EMERGENCE FORMULA

```
UNDERSTANDING = (Salience Detection) 
              x (Hypothesis Generation) 
              x (Experimental Validation)
              x (Structural Correspondence)
              x (Generalization)
```

**But crucially: These stages form a FEEDBACK LOOP, not a pipeline**

### The Feedback Cycle

```
See pattern -> Generate hypotheses -> Test via experiments
     ^                                        |
     |                                        v
     |                          Build relational model
     |                                        |
     |                                        v
     |                          Abstract principles
     |                                        |
     +----------------------------------------+
                         |
                         v
          Notice DEEPER patterns (informed by principles)
                         |
                         v
          Generate BETTER hypotheses (constrained by model)
                         |
                         v
          Design CLEVERER experiments (targeted by abstraction)
                         |
                         v
          Build RICHER models (incorporating new data)
                         |
                         v
                  ... SPIRAL UPWARD ...
```

