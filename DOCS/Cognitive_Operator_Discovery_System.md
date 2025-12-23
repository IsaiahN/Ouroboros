# Cognitive Operator Discovery System (CODS)

**Version**: 1.0  
**Date**: 2025-12-23  
**Purpose**: Self-evolving cognitive vocabulary through compositional primitives and RLVR validation  
**Status**: Implementation Guide

---

## Overview

The Cognitive Operator Discovery System enables Ouroboros to **evolve its own cognitive vocabulary** by:
1. Composing low-level primitives into higher-level operators
2. Testing operators with RLVR (real game performance)
3. Promoting/decaying operators based on effectiveness
4. Querying an Oracle for interpretation (human/LLM/automated - system doesn't know or care)

### The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COGNITIVE PRIMITIVES LIBRARY                      │
│                                                                       │
│  Low-level operations on frames: split, compare, transform, count   │
│  Domain-agnostic, composable, measurable                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OPERATOR COMPOSER                                 │
│                                                                       │
│  Combines primitives into operators (compositions)                   │
│  Evolutionary search over composition space                          │
│  Tests operators against stuck games with RLVR                       │
│  Promotes what works, decays what doesn't                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORACLE INTERFACE                                  │
│                                                                       │
│  Queries for interpretation (system-agnostic)                        │
│  Receives optimizations from external knowledge                      │
│  Handles admin directives as environmental signals                   │
│  System doesn't know what's behind the Oracle                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. Oracle-Agnostic Design
The system queries an Oracle but doesn't know or care if it's:
- Human reviewing reports
- LLM interpreting compositions
- Automated knowledge matcher
- Any combination

The Oracle is just an API. Today it's you + me. Tomorrow it could be fully automated.

### 2. RLVR as Sole Validator
Operators are judged **only** by real game performance:
- Does this operator help level 2+ completion?
- Does it reduce action count?
- Does it transfer to other games?

No operator survives based on "looking good" - only empirical results.

### 3. Anti-Goodhart Protections
Per the RLVR safety framework:
- Operators get pre-allocated testing budgets (not earned)
- Success in Game A doesn't buy priority in Game B
- Failed operators decay, don't permanently stigmatize
- Forced novelty quotas (must test N new compositions per M generations)

---

## Database Schema Additions

```sql
-- Cognitive primitives library (static, admin-managed)
CREATE TABLE IF NOT EXISTS cognitive_primitives (
    primitive_id TEXT PRIMARY KEY,
    primitive_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'spatial', 'color', 'topology', 'geometry', 'temporal', 'relational'
    description TEXT,
    input_spec JSON,         -- Expected inputs
    output_spec JSON,        -- What it returns
    implementation_ref TEXT, -- Function reference in cognitive_primitives.py
    is_active BOOLEAN DEFAULT TRUE,
    added_generation INTEGER
);

-- Discovered operators (compositions of primitives)
CREATE TABLE IF NOT EXISTS discovered_operators (
    operator_id TEXT PRIMARY KEY,
    composition JSON NOT NULL,       -- Array of {primitive_id, args}
    discovery_generation INTEGER,
    discovered_by_agent TEXT,        -- Agent that first used this successfully
    
    -- Performance metrics (RLVR results)
    games_tested JSON,               -- Array of game_ids
    total_tests INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    level_improvement REAL DEFAULT 0.0,
    action_efficiency REAL DEFAULT 1.0,
    transfer_score REAL DEFAULT 0.0, -- How well it transfers to other games
    
    -- Lifecycle
    status TEXT DEFAULT 'TESTING',   -- TESTING, VALIDATED, PROMOTED, DECAYED, RETIRED
    is_active BOOLEAN DEFAULT TRUE,
    activation_count INTEGER DEFAULT 0,
    last_used_generation INTEGER,
    decay_score REAL DEFAULT 0.0,
    
    -- Oracle interpretation (filled asynchronously)
    interpretation_status TEXT DEFAULT 'PENDING',  -- PENDING, QUERIED, ANSWERED, VALIDATED
    oracle_query_id TEXT,
    interpretation TEXT,
    known_analog BOOLEAN,
    optimized_composition JSON,
    novelty_flag BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (oracle_query_id) REFERENCES oracle_queries(query_id)
);

-- Oracle queries (system-generated, oracle-answered)
CREATE TABLE IF NOT EXISTS oracle_queries (
    query_id TEXT PRIMARY KEY,
    query_type TEXT NOT NULL,        -- 'interpret', 'optimize', 'validate_novelty', 'guidance'
    target_operator_id TEXT,
    query_data JSON NOT NULL,
    priority TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'critical'
    
    -- Query lifecycle
    created_generation INTEGER,
    created_timestamp TEXT,
    status TEXT DEFAULT 'PENDING',   -- PENDING, ANSWERED, TIMEOUT, CANCELLED
    
    -- Response (filled by oracle - human/LLM/automated)
    response_data JSON,
    response_timestamp TEXT,
    responder_id TEXT DEFAULT 'oracle',  -- System doesn't interpret this
    
    FOREIGN KEY (target_operator_id) REFERENCES discovered_operators(operator_id)
);

-- Admin directives (environmental signals)
CREATE TABLE IF NOT EXISTS admin_directives (
    directive_id TEXT PRIMARY KEY,
    directive_type TEXT NOT NULL,    -- 'focus', 'pause', 'inject', 'retire', 'boost', 'guide'
    target TEXT,                     -- operator_id, primitive_id, game_type, or 'global'
    directive_data JSON,
    priority INTEGER DEFAULT 5,      -- 1-10, higher = more urgent
    
    -- Lifecycle
    issued_timestamp TEXT,
    expires_timestamp TEXT,          -- NULL = never expires
    executed BOOLEAN DEFAULT FALSE,
    executed_timestamp TEXT,
    execution_result JSON
);

-- Operator test results (detailed RLVR logs)
CREATE TABLE IF NOT EXISTS operator_test_results (
    test_id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    generation INTEGER,
    
    -- Test conditions
    level_before INTEGER,
    score_before REAL,
    
    -- Results
    level_after INTEGER,
    score_after REAL,
    actions_used INTEGER,
    operator_fired BOOLEAN,          -- Did the operator's condition trigger?
    operator_influenced_action BOOLEAN,  -- Did firing change the action taken?
    
    -- Outcome
    success BOOLEAN,                 -- Did level improve?
    improvement_delta REAL,
    
    test_timestamp TEXT,
    
    FOREIGN KEY (operator_id) REFERENCES discovered_operators(operator_id)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_operators_status ON discovered_operators(status, is_active);
CREATE INDEX IF NOT EXISTS idx_operators_performance ON discovered_operators(level_improvement DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_pending ON oracle_queries(status) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_directives_pending ON admin_directives(executed) WHERE executed = FALSE;
CREATE INDEX IF NOT EXISTS idx_test_results_operator ON operator_test_results(operator_id, generation);
```

---

## Module Specifications

### 1. cognitive_primitives.py

**Purpose**: Library of composable low-level operations on frames

**Primitives by Category**:

| Category | Primitive | Description | Inputs | Output |
|----------|-----------|-------------|--------|--------|
| **Spatial** | `split` | Divide frame into regions | frame, axis, position | [region_a, region_b] |
| **Spatial** | `crop` | Extract subregion | frame, x, y, w, h | region |
| **Spatial** | `transform` | Rotate, flip, shift | frame, operation | transformed_frame |
| **Spatial** | `overlay` | Combine two regions | frame_a, frame_b, method | combined |
| **Color** | `count_color` | Count pixels of color | frame, color | int |
| **Color** | `filter_color` | Keep only specified color | frame, color | filtered_frame |
| **Color** | `dominant_color` | Most common color in region | frame | color |
| **Color** | `color_histogram` | Distribution of colors | frame | dict[color, count] |
| **Topology** | `flood_fill` | Find connected region | frame, x, y | region_mask |
| **Topology** | `detect_edges` | Find color boundaries | frame | edge_map |
| **Topology** | `find_regions` | Segment into connected regions | frame | [regions] |
| **Topology** | `is_enclosed` | Check if region is bounded | frame, region | bool |
| **Geometry** | `center_of_mass` | Centroid of color | frame, color | (x, y) |
| **Geometry** | `bounding_box` | Smallest box containing color | frame, color | (x, y, w, h) |
| **Geometry** | `distance` | Distance between points | point_a, point_b | float |
| **Geometry** | `direction` | Direction vector | point_a, point_b | (dx, dy) |
| **Temporal** | `diff` | What changed between frames | frame_t, frame_t_minus_1 | diff_mask |
| **Temporal** | `motion_vector` | Direction of change | frame_t, frame_t_minus_1 | (dx, dy) |
| **Relational** | `compare` | Similarity between regions | region_a, region_b | float (0-1) |
| **Relational** | `adjacent` | Check if regions touch | region_a, region_b | bool |
| **Relational** | `contains` | Check if region contains another | outer, inner | bool |
| **Relational** | `count_neighbors` | Count adjacent cells of color | frame, x, y, color | int |

**Class Interface**:
```python
class CognitivePrimitivesLibrary:
    def execute(self, primitive_name: str, args: dict, context: dict) -> Any
    def get_primitive_spec(self, primitive_name: str) -> dict
    def list_primitives(self, category: Optional[str] = None) -> List[str]
    def validate_args(self, primitive_name: str, args: dict) -> bool
```

### 2. operator_composer.py

**Purpose**: Combine primitives into operators, evolve compositions, test with RLVR

**Key Classes**:

```python
class Operator:
    """A composition of primitives that produces a decision signal."""
    operator_id: str
    composition: List[dict]  # [{primitive_id, args}, ...]
    
    def execute(self, context: dict) -> OperatorResult
    def mutate(self) -> 'Operator'
    def crossover(self, other: 'Operator') -> 'Operator'

class OperatorComposer:
    """Manages operator lifecycle: creation, testing, promotion, decay."""
    
    def generate_random_operator(self, max_depth: int = 5) -> Operator
    def test_operator(self, operator: Operator, game_context: dict) -> TestResult
    def evolve_operators(self, generation: int, population_size: int = 20)
    def promote_successful(self, threshold: float = 0.15)
    def decay_unused(self, generations_threshold: int = 10)
    def get_active_operators(self, game_type: Optional[str] = None) -> List[Operator]

class OperatorIntegration:
    """Integrates operators into gameplay decision-making."""
    
    def evaluate_operators(self, frame: np.ndarray, context: dict) -> List[OperatorSignal]
    def apply_operator_biases(self, action_weights: dict, signals: List[OperatorSignal]) -> dict
```

**Evolution Strategy**:
1. Each generation, allocate N test slots to operators
2. Randomly generate new operators (forced novelty quota)
3. Mutate/crossover existing operators
4. Test all in RLVR conditions
5. Promote high performers, decay low performers
6. Query Oracle for top performers interpretation

### 3. oracle_interface.py

**Purpose**: Oracle-agnostic API for interpretation and directives

**Key Classes**:

```python
class OracleInterface:
    """System-facing interface to the Oracle. System doesn't know what's behind it."""
    
    def query_interpretation(self, operator: Operator, metrics: dict) -> str  # Returns query_id
    def query_optimization(self, operator_id: str) -> str
    def query_novelty_validation(self, operator_id: str) -> str
    def get_pending_responses(self) -> List[OracleResponse]
    def process_response(self, query_id: str, response: OracleResponse)

class DirectiveProcessor:
    """Processes admin directives as environmental signals."""
    
    def get_pending_directives(self) -> List[Directive]
    def execute_directive(self, directive: Directive) -> ExecutionResult
    def check_expired_directives(self)

class OracleQueryGenerator:
    """Auto-generates queries when operators cross thresholds."""
    
    def check_query_conditions(self, operator: Operator) -> bool
    def generate_query(self, operator: Operator, query_type: str) -> OracleQuery
```

---

## Integration Points

### 1. With core_gameplay.py

Operators influence action selection:

```python
# In GameplayEngine.select_action()
if self.operator_integration:
    signals = self.operator_integration.evaluate_operators(frame, context)
    action_weights = self.operator_integration.apply_operator_biases(action_weights, signals)
```

### 2. With autonomous_evolution_runner.py

Operator evolution runs each generation:

```python
# In AutonomousEvolutionRunner._run_generation()
if self.operator_composer and generation % self.operator_evolution_interval == 0:
    self.operator_composer.evolve_operators(generation)
    self.oracle_interface.process_pending_queries()
    self.directive_processor.execute_pending()
```

### 3. With viral_package_engine.py

High-performing operators can become viral packages:

```python
# When operator crosses promotion threshold
if operator.level_improvement > 0.20:
    viral_engine.create_viral_package_from_operator(operator)
```

---

## Testing Strategy

### Unit Tests (tests/test_cognitive_*.py)

| Test File | Coverage |
|-----------|----------|
| `test_cognitive_primitives.py` | All primitives execute correctly, edge cases handled |
| `test_operator_composer.py` | Composition, mutation, crossover, lifecycle |
| `test_oracle_interface.py` | Query generation, response processing, directives |

### Integration Tests

| Test | What It Validates |
|------|-------------------|
| Operator-gameplay integration | Operators influence action selection |
| RLVR feedback loop | Test results update operator metrics |
| Oracle async flow | System continues without oracle response |
| Directive execution | Admin signals modify system behavior |

### RLVR Validation

| Metric | Target | Measurement |
|--------|--------|-------------|
| Level 2+ improvement | >10% after 20 generations | Compare before/after operator introduction |
| Action efficiency | No degradation | Actions per level should not increase |
| Transfer learning | >0 on at least 2 game types | Same operator helps multiple games |

---

## Configuration

```python
# In autonomous_evolution_runner.py or config
OPERATOR_CONFIG = {
    'evolution_interval': 5,         # Evolve operators every N generations
    'population_size': 30,           # Operators under test
    'max_composition_depth': 6,      # Max primitives per operator
    'novelty_quota': 0.20,           # 20% must be new random compositions
    'promotion_threshold': 0.15,     # Level improvement to promote
    'decay_generations': 15,         # Generations unused before decay
    'oracle_query_threshold': 0.18,  # Performance threshold to query oracle
    'test_budget_per_operator': 10,  # Games per operator per generation
}
```

---

## Rollout Phases

### Phase 1: Primitives Library (This PR)
- Implement all primitives
- Unit tests for each
- No integration yet

### Phase 2: Operator Composer
- Composition, mutation, crossover
- Database storage
- Evolution loop (standalone, not integrated)

### Phase 3: Oracle Interface
- Query/response infrastructure
- Directive processing
- CLI tool for human responses

### Phase 4: Gameplay Integration
- Operators influence action selection
- RLVR feedback loop
- Full end-to-end testing

### Phase 5: Viral Integration
- Operators become viral packages
- Cross-agent operator sharing
- Network-level operator intelligence

---

## Files to Create

| File | Purpose |
|------|---------|
| `cognitive_primitives.py` | Primitives library |
| `operator_composer.py` | Composition and evolution |
| `oracle_interface.py` | Oracle-agnostic API |
| `tests/test_cognitive_primitives.py` | Primitive tests |
| `tests/test_operator_composer.py` | Composer tests |
| `tests/test_oracle_interface.py` | Oracle tests |

---

## Success Criteria

1. **Operators emerge** that correlate with level 2+ success
2. **System continues** without oracle responses (no blocking)
3. **Novelty preserved** through forced quotas
4. **Transfer learning** visible (operators help multiple games)
5. **Interpretability** maintained (compositions are human-readable)

---

**END OF IMPLEMENTATION GUIDE**
