# Ouroboros Three-Layer Architecture - Quick Reference

## Overview

The Ouroboros system uses a three-layer architecture inspired by biological evolution to prevent overfitting while enabling rapid learning.

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: STATIC GENOME (Nature, DNA)                   │
│ The fundamental "hardware" of the agent                 │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: EPIGENETIC (Nurture, Learning Capacity)       │
│ How the agent learns, not what it learned              │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: SOMATIC (Experience, Learned Knowledge)       │
│ What the agent learned (NOT inherited)                 │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: Static Genome (Nature)

**What it is**: The fundamental agent architecture

**Contains**:
- `agent_type`: 'pattern_specialist', 'score_optimizer', 'exploration_agent', 'win_focused_agent'
- `base_architecture`: Core decision-making structure

**Evolution**:
- Mutation rate: 1-2% per generation
- Inheritance: Full genetic crossover
- Stability: HIGH (changes slowly)

**Purpose**: Define what kind of agent this is

**Example**:
```python
genome = {
    'agent_type': 'pattern_specialist',
    'base_architecture': 'visual_pattern_matcher'
}
```

**Analogy**: Like your body type - tall, short, athletic build, etc. Inherited from parents, hard to change.

---

## Layer 2: Epigenetic (Nurture)

**What it is**: Learning capacity and biases

**Contains**:
```python
epigenetics = {
    'feature_attention_weights': {
        'edges': 1.3,              # How much attention to edges
        'symmetry': 1.1,           # How much attention to symmetry
        'color_patterns': 0.9,     # How much attention to colors
        'spatial_relations': 1.4   # How much attention to spatial relationships
    },
    'learning_rate_modifiers': {
        'visual_learning': 1.2,    # How fast to learn visual patterns
        'symbolic_learning': 0.8,  # How fast to learn symbolic patterns
        'motor_learning': 1.0      # How fast to learn actions
    },
    'exploration_settings': {
        'exploration_ratio': 0.5,  # Explore vs exploit balance
        'novelty_seeking': 0.6,    # How much to seek new strategies
        'risk_tolerance': 0.4      # Willingness to try risky moves
    },
    'meta_capacities': {
        'problem_decomposition_tendency': 1.1,  # Break problems into parts
        'abstraction_capacity': 1.3,            # Generalize patterns
        'transfer_learning_ability': 0.9        # Apply old knowledge to new problems
    },
    'inheritance_strength': 1.0,   # How strongly this is inherited
    'generation_depth': 3,         # How many generations old
    'decay_rate': 0.95            # Decay per generation
}
```

**Evolution**:
- Mutation rate: 10-20% per generation
- Inheritance: FITNESS-WEIGHTED with 0.95 decay
- Stability: MEDIUM (adapts each generation)

**Inheritance Formula**:
```python
offspring_feature = (
    parent1_feature * (parent1_fitness / total_fitness) +
    parent2_feature * (parent2_fitness / total_fitness)
) * 0.95  # Decay
```

**Purpose**: Define HOW the agent learns, not WHAT it learned

**Example Inheritance**:
```
Parent A (fitness 0.7): edges=1.4, symmetry=1.0
Parent B (fitness 0.3): edges=0.9, symmetry=1.3

Total fitness = 1.0
Parent A weight = 0.7, Parent B weight = 0.3

Offspring edges = (1.4 * 0.7 + 0.9 * 0.3) * 0.95 = (0.98 + 0.27) * 0.95 = 1.19
Offspring symmetry = (1.0 * 0.7 + 1.3 * 0.3) * 0.95 = (0.70 + 0.39) * 0.95 = 1.04
```

**Analogy**: Like your learning style - visual vs auditory learner, fast vs slow reader, risk-taker vs cautious. Partially inherited (you're somewhat like your parents), but adapts to your environment.

---

## Layer 3: Somatic (Experience)

**What it is**: Actual learned knowledge and experiences

**Contains**:
- `winning_sequences`: Action sequences that won games
- `discovered_patterns`: Visual/symbolic patterns learned
- `action_memories`: Specific experiences from gameplay
- `game_experiences`: Results from playing games

**Evolution**:
- Mutation rate: N/A (not inherited)
- Inheritance: NONE
- Storage: Community database (shared)
- Stability: VOLATILE (changes constantly)

**Purpose**: Store actual learned solutions

**Example**:
```python
winning_sequence = {
    'sequence_id': 123,
    'game_id': 'abc-def-123',
    'actions': [
        {'action_type': 'ACTION1', 'coordinate': [0, 0]},
        {'action_type': 'ACTION2', 'coordinate': [1, 1]},
        # ... more actions ...
    ],
    'efficiency': 30.0,  # Actions per win
    'discovery_agent': 'agent_abc123'
}
```

**Storage**: Database tables
- `winning_sequences`: All discovered sequences
- `sequence_validation_attempts`: Who tried what, success/failure
- `sequence_reputation`: Bayesian reliability scores

**Community Memory**: All agents can query and validate sequences

**Analogy**: Like specific skills you learned - riding a bike, playing piano, memorizing phone numbers. NOT inherited genetically, but can be taught to others.

---

## Why Three Layers?

### Problem: Overfitting
Traditional evolution inherits solutions directly:
```
Parent wins game with sequence X
→ Offspring inherits sequence X
→ Offspring wins game with sequence X
→ Grandchild inherits sequence X
→ Eventually, everyone has sequence X
→ No learning happening, just copying
```

### Solution: Three Layers
Ouroboros separates hardware, capacity, and knowledge:
```
Parent discovers sequence X (Layer 3 - NOT inherited)
Parent has good learning capacity (Layer 2 - inherited with decay)
Parent has stable architecture (Layer 1 - inherited stable)

→ Offspring inherits learning capacity (Layer 2)
→ Offspring queries sequence X from database (Layer 3)
→ Offspring must validate sequence X works for them
→ Offspring may discover new sequence Y (Layer 3)
→ Offspring's learning capacity evolves (Layer 2)

→ Result: Continuous learning, not copying
```

---

## Learning Speed Fitness

The fitness formula rewards agents that learn fast, not agents that inherit solutions.

**Formula**:
```
fitness = (level_wins^1.5 / log(games_played + 1)) * execution_efficiency * consistency
```

**Components**:

1. **level_wins^1.5**: Exponential reward for wins
   - 1 win: 1.0x
   - 2 wins: 2.8x
   - 3 wins: 5.2x
   - 5 wins: 11.2x

2. **log(games_played + 1)**: Age penalty
   - 5 games: ÷1.79 (558% of fitness)
   - 10 games: ÷2.40 (417% of fitness)
   - 20 games: ÷3.04 (329% of fitness)
   - 50 games: ÷3.93 (255% of fitness)
   - 100 games: ÷4.62 (217% of fitness)

3. **execution_efficiency**: Score per action
   - Higher score with fewer actions = better

4. **consistency**: 1 / (1 + coefficient_of_variation)
   - Low variance in performance = better

**Example Comparison**:

**Fast Learner** (3 wins / 5 games):
```
level_wins^1.5 = 3^1.5 = 5.196
age_penalty = log(5 + 1) = 1.792
discovery_speed = 5.196 / 1.792 = 2.900

efficiency = 45 / 90 = 0.500
consistency = 0.95

fitness = 2.900 * 0.500 * 0.95 = 1.378
```

**Slow Learner** (2 wins / 20 games):
```
level_wins^1.5 = 2^1.5 = 2.828
age_penalty = log(20 + 1) = 3.045
discovery_speed = 2.828 / 3.045 = 0.929

efficiency = 40 / 110 = 0.364
consistency = 0.80

fitness = 0.929 * 0.364 * 0.80 = 0.270
```

**Advantage**: 1.378 / 0.270 = **5.1x fitness advantage for fast learner!**

**With more games**: If slow learner takes 100 games for 3 wins:
```
age_penalty = log(100 + 1) = 4.62
discovery_speed = 5.196 / 4.62 = 1.125
fitness = 1.125 * 0.364 * 0.80 = 0.327

Advantage: 1.378 / 0.327 = 4.2x (and getting worse)
```

---

## Community Memory System

Layer 3 (Somatic) knowledge is stored in a shared database with validation tracking.

### Workflow

1. **Discovery**:
   ```python
   Agent discovers winning sequence for game X
   → Stored in winning_sequences table
   → Initial reputation: 1.0 (Bayesian prior)
   ```

2. **Query**:
   ```python
   Other agents query sequences for game X
   → Ranked by reliability_score (Bayesian)
   → Filter out sequences with reliability < 0.3
   ```

3. **Validation**:
   ```python
   Agent attempts sequence
   → Success/failure recorded in sequence_validation_attempts
   → Reputation updated with Bayesian formula
   ```

4. **Reputation Update** (Bayesian):
   ```python
   reliability = (success_count + 2) / (total_attempts + 4)
   success_rate = success_count / max(total_attempts, 1)
   ```

5. **Filtering**:
   ```python
   if reliability_score < 0.3:
       # Don't show this sequence to agents
       # It's been downvoted by community
   ```

### Bayesian Scoring Examples

**New Sequence** (0 attempts):
```
reliability = (0 + 2) / (0 + 4) = 0.5  # Neutral prior
```

**1 Success** (1 attempt):
```
reliability = (1 + 2) / (1 + 4) = 0.6  # Good start
```

**3 Successes, 2 Failures** (5 attempts):
```
reliability = (3 + 2) / (5 + 4) = 0.556  # Decent reliability
success_rate = 3 / 5 = 0.60
```

**0 Successes, 4 Failures** (4 attempts):
```
reliability = (0 + 2) / (4 + 4) = 0.25  # FILTERED OUT (< 0.3)
success_rate = 0 / 4 = 0.0
```

**10 Successes, 2 Failures** (12 attempts):
```
reliability = (10 + 2) / (12 + 4) = 0.75  # Highly reliable
success_rate = 10 / 12 = 0.833
```

### Why Bayesian?

**Problem with raw success rate**:
- Sequence with 1/1 success = 100% success rate (unreliable sample)
- Sequence with 8/10 success = 80% success rate (more reliable)
- Should prefer 8/10 over 1/1

**Bayesian solution**:
- Add prior successes (+2) and prior attempts (+4)
- 1/1 becomes 3/5 = 0.6 (tempered confidence)
- 8/10 becomes 10/14 = 0.714 (close to actual)
- Prevents overfitting to lucky sequences

---

## Epigenetic Inheritance Details

### Calculation Process

1. **Get parent performance**:
   ```python
   parent1_fitness = calculate_learning_speed_fitness(parent1)
   parent2_fitness = calculate_learning_speed_fitness(parent2)
   total_fitness = parent1_fitness + parent2_fitness
   ```

2. **Calculate weights**:
   ```python
   parent1_weight = parent1_fitness / total_fitness
   parent2_weight = parent2_fitness / total_fitness
   ```

3. **Inherit features**:
   ```python
   for feature in epigenetic_features:
       offspring_feature = (
           parent1_feature * parent1_weight +
           parent2_feature * parent2_weight
       ) * decay_rate  # 0.95
       
       # Add mutation
       mutation = random.uniform(-0.1, 0.1)
       offspring_feature = max(0.5, min(1.6, offspring_feature + mutation))
   ```

4. **Update metadata**:
   ```python
   offspring.epigenetics['inheritance_strength'] = base_strength * 0.95
   offspring.epigenetics['generation_depth'] = max(
       parent1.epigenetics['generation_depth'],
       parent2.epigenetics['generation_depth']
   ) + 1
   ```

### Example: Feature Attention Inheritance

**Parents**:
```python
Parent A (fitness 0.85):
  edges: 1.4
  symmetry: 1.0
  
Parent B (fitness 0.45):
  edges: 0.9
  symmetry: 1.3
```

**Weights**:
```python
total_fitness = 0.85 + 0.45 = 1.30
parent_a_weight = 0.85 / 1.30 = 0.654
parent_b_weight = 0.45 / 1.30 = 0.346
```

**Inheritance**:
```python
edges_inherited = (1.4 * 0.654 + 0.9 * 0.346) * 0.95
                = (0.916 + 0.311) * 0.95
                = 1.227 * 0.95
                = 1.165

# Add mutation (e.g., +0.05)
edges_final = 1.165 + 0.05 = 1.215

symmetry_inherited = (1.0 * 0.654 + 1.3 * 0.346) * 0.95
                   = (0.654 + 0.450) * 0.95
                   = 1.104 * 0.95
                   = 1.049

# Add mutation (e.g., -0.03)
symmetry_final = 1.049 - 0.03 = 1.019
```

**Result**:
```python
Offspring:
  edges: 1.215  # Closer to Parent A (higher fitness)
  symmetry: 1.019  # Weighted average, slight mutation
```

---

## Evolution Strategy Decision Making

The coordinator analyzes population performance and adjusts evolution parameters.

### Strategy Types

#### 1. Exploration
**When**: `avg_win_rate < 0.1`

**Parameters**:
- Layer 1 mutation: 30%
- Layer 2 mutation: 20%
- Epigenetic inheritance: 1.2 (increased)
- Selection pressure: 0.4 (low)

**Reason**: Need diverse strategies, pass down learning capacity strongly

#### 2. Diversification
**When**: `genetic_diversity < 0.3`

**Parameters**:
- Layer 1 mutation: 40% (highest)
- Layer 2 mutation: 25% (highest)
- Epigenetic inheritance: 0.8 (decreased)
- Selection pressure: 0.3 (lowest)

**Reason**: Population too homogeneous, reduce inheritance to increase diversity

#### 3. Exploitation
**When**: `improvement_rate > 0.05`

**Parameters**:
- Layer 1 mutation: 10% (lowest)
- Layer 2 mutation: 10% (lowest)
- Epigenetic inheritance: 1.0 (standard)
- Selection pressure: 0.7 (highest)

**Reason**: Good strategies working, refine and preserve

#### 4. Balanced
**When**: Default

**Parameters**:
- Layer 1 mutation: 20%
- Layer 2 mutation: 15%
- Epigenetic inheritance: 1.0
- Selection pressure: 0.5

**Reason**: Maintain current approach

### Learning Speed Override

**When**: `avg_learning_speed < 0.15`

**Action**: Switch to exploration strategy, increase Layer 2 mutation by 5%

**Reason**: Population learning slowly, need more exploration

---

## Implementation Files

### Core Components

1. **ouroboros_coordinator.py** (813 lines)
   - Central LLM coordinator
   - Evolution strategy decisions
   - Epigenetic parameter management
   - Reference implementation

2. **evolutionary_engine.py** (1047 lines)
   - `calculate_epigenetic_inheritance()` (lines 702-874)
   - `_calculate_learning_speed_fitness()` (lines 181-289)
   - `_calculate_specialist_fitness()` (lines 291-424)

3. **core_gameplay.py** (2192 lines)
   - `_record_sequence_validation()` (lines 1133-1175)
   - `_update_sequence_reputation()` (lines 1177-1261)
   - `_get_best_sequence_for_game()` (lines 876-954)
   - `_replay_sequence_inline()` (lines 1005-1065)

4. **agent_factory.py** (250 lines)
   - Epigenetic layer initialization
   - Agent creation with defaults
   - Serialization to JSON

5. **ouroboros_database_extension.sql** (713 lines)
   - Epigenetic layer schema
   - Community memory tables
   - Validation tracking

---

## Quick Usage Examples

### Check Learning Speed
```python
from database_interface import DatabaseInterface
db = DatabaseInterface()

agents = db.execute_query("""
    SELECT agent_id, total_games_won, total_games_played
    FROM agents WHERE is_active = TRUE
""")

for agent in agents:
    wins = agent['total_games_won']
    games = agent['total_games_played']
    
    discovery_speed = (wins ** 1.5) / math.log(games + 1)
    print(f"Agent {agent['agent_id']}: discovery_speed = {discovery_speed:.3f}")
```

### Check Community Memory
```python
sequences = db.execute_query("""
    SELECT s.sequence_id, s.game_id, 
           r.reliability_score, r.success_rate
    FROM winning_sequences s
    JOIN sequence_reputation r ON s.sequence_id = r.sequence_id
    WHERE r.reliability_score > 0.5
    ORDER BY r.reliability_score DESC
""")

for seq in sequences:
    print(f"Game {seq['game_id']}: reliability={seq['reliability_score']:.3f}")
```

### Check Epigenetic Inheritance
```python
import json

agents = db.execute_query("""
    SELECT agent_id, epigenetics
    FROM agents WHERE is_active = TRUE AND epigenetics IS NOT NULL
""")

for agent in agents:
    epi = json.loads(agent['epigenetics'])
    print(f"Agent {agent['agent_id']}:")
    print(f"  Edges attention: {epi['feature_attention_weights']['edges']:.3f}")
    print(f"  Inheritance strength: {epi['inheritance_strength']:.3f}")
    print(f"  Generation depth: {epi['generation_depth']}")
```

---

## Key Takeaways

1. **Layer 1 (Genome)**: What you ARE - stable, 1-2% mutation
2. **Layer 2 (Epigenetic)**: How you LEARN - adaptive, 10-20% mutation, fitness-weighted inheritance
3. **Layer 3 (Somatic)**: What you LEARNED - not inherited, community database

4. **Learning Speed Fitness**: Rewards innovation over solution inheritance (28x-56x advantage)

5. **Community Memory**: Validated knowledge sharing with Bayesian reputation

6. **Epigenetic Inheritance**: Fitness-weighted with 0.95 decay prevents overfitting

7. **Adaptive Strategy**: Coordinator adjusts evolution based on population needs

**Result**: A system that continuously learns instead of copying solutions.
