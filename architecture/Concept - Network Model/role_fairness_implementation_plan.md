# Role Fairness Implementation Plan

**Created**: December 9, 2025  
**Status**: Planning  
**Priority**: High (Fixes fundamental thermodynamic imbalance)

---

## Executive Summary

Implement the Agent Role Fairness Protocol to create a **growth-based meritocracy** where agents are evaluated against their own starting positions, not absolute performance. This aligns with the AGI Unified Theory's principles of dual economy, voluntary choice, and emergent network intelligence.

---

## Implementation Phases

### Phase 1: Immediate (This Session)
**Goal**: Fix the fundamental ATP imbalance and add growth tracking

| Task | File(s) | Estimated Lines | Priority |
|------|---------|-----------------|----------|
| 1.1 Dynamic Role ATP Multipliers | `adaptive_action_limits.py` | ~80 | CRITICAL |
| 1.2 Track `initial_w_B_for_role` | `agent_operating_mode_system.py`, schema | ~60 | CRITICAL |
| 1.3 Growth-Based Progress Score | `adaptive_action_limits.py` | ~50 | HIGH |

### Phase 2: Short-Term (Next Session)
**Goal**: Soft role transitions and asymmetric expectations

| Task | File(s) | Estimated Lines | Priority |
|------|---------|-----------------|----------|
| 2.1 Soft Role Transition System | `agent_operating_mode_system.py` | ~100 | HIGH |
| 2.2 Asymmetric Stagnation Penalties | `adaptive_action_limits.py` | ~60 | HIGH |
| 2.3 Learning Tax for Failed Transitions | `agent_operating_mode_system.py` | ~40 | MEDIUM |

### Phase 3: Vision (Future Sessions)
**Goal**: Internal motivation and full dual-economy protection

| Task | File(s) | Estimated Lines | Priority |
|------|---------|-----------------|----------|
| 3.1 Curiosity/Boredom Modeling | `agents` table, new fields | ~120 | MEDIUM |
| 3.2 Network-State-Responsive ATP | `regulatory_signal_engine.py` | ~80 | MEDIUM |
| 3.3 Dual Economy Audit | All salary/prestige code | ~40 | LOW |

---

## Detailed Implementation Specifications

### 1.1 Dynamic Role ATP Multipliers

**Location**: `adaptive_action_limits.py` → `calculate_agent_salary()`

**Current State**:
```python
# Budget multiplier based on percentile rank only
if percentile < 0.25:
    budget_multiplier = 0.5 + (percentile / 0.25) * 0.5
elif percentile < 0.75:
    budget_multiplier = 1.0 + ((percentile - 0.25) / 0.50) * 0.5
else:
    budget_multiplier = 1.5 + ((percentile - 0.75) / 0.25) * 1.5
```

**Target State**:
```python
# Base ATP by role (exploration is expensive)
ROLE_BASE_ATP = {
    'pioneer': 1.5,      # High - exploration is expensive and uncertain
    'generalist': 1.2,   # Medium-high - validation across domains
    'optimizer': 1.0,    # Baseline - working with known solutions
    'exploiter': 0.8     # Low - just replaying proven sequences
}

# Get network need adjustment from regulatory signals
network_need_adjustment = self._get_network_role_need(agent_role)  # ±0.3

# Final role multiplier
role_multiplier = ROLE_BASE_ATP.get(agent_role, 1.0) + network_need_adjustment

# Combine with performance percentile (reduced weight)
performance_bonus = (percentile - 0.5) * 0.5  # -0.25 to +0.25

budget_multiplier = role_multiplier + performance_bonus
```

**New Helper Method**:
```python
def _get_network_role_need(self, agent_role: str) -> float:
    """
    Query regulatory signals for current network needs.
    Returns adjustment between -0.3 and +0.3.
    
    When network needs more exploration → Pioneer adjustment ↑
    When network needs refinement → Optimizer adjustment ↑
    """
    # Query regulatory_signals table for role_need signals
    signals = self.db.execute_query("""
        SELECT signal_value FROM regulatory_signals
        WHERE signal_type = 'role_need_adjustment'
        AND target_role = ?
        AND is_active = TRUE
        ORDER BY timestamp DESC LIMIT 1
    """, (agent_role,))
    
    if signals and signals[0]['signal_value']:
        return max(-0.3, min(0.3, signals[0]['signal_value']))
    return 0.0
```

---

### 1.2 Track `initial_w_B_for_role`

**Location**: `agent_operating_mode_system.py` → `_record_mode_assignment()`

**Database Schema Change** (add to `agent_operating_modes` table):
```sql
ALTER TABLE agent_operating_modes ADD COLUMN initial_w_B_for_role REAL DEFAULT 0.5;
ALTER TABLE agent_operating_modes ADD COLUMN current_w_B REAL DEFAULT 0.5;
ALTER TABLE agent_operating_modes ADD COLUMN progress_score REAL DEFAULT 0.0;
```

**Current State** in `_record_mode_assignment()`:
```python
def _record_mode_assignment(self, agent_id, game_id, generation, mode, reason):
    mode_id = f"mode_{uuid.uuid4().hex[:16]}"
    params = self.MODE_PARAMETERS[mode]
    
    self.db.execute_query("""
        INSERT INTO agent_operating_modes (
            mode_id, agent_id, game_id, generation,
            operating_mode, mode_reason,
            mutation_multiplier, action_diversity, novelty_seeking
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (...))
```

**Target State**:
```python
def _record_mode_assignment(self, agent_id, game_id, generation, mode, reason):
    mode_id = f"mode_{uuid.uuid4().hex[:16]}"
    params = self.MODE_PARAMETERS[mode]
    
    # Get agent's current self_network_bias (w_B)
    agent_data = self.db.execute_query("""
        SELECT self_network_bias FROM agents WHERE agent_id = ?
    """, (agent_id,))
    
    current_w_B = agent_data[0]['self_network_bias'] if agent_data else 0.5
    
    # Record with initial w_B snapshot
    self.db.execute_query("""
        INSERT INTO agent_operating_modes (
            mode_id, agent_id, game_id, generation,
            operating_mode, mode_reason,
            mutation_multiplier, action_diversity, novelty_seeking,
            initial_w_B_for_role, current_w_B, progress_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0)
    """, (mode_id, agent_id, game_id, generation, mode, reason,
          params['mutation_multiplier'], params['action_diversity'],
          params['novelty_seeking'], current_w_B, current_w_B))
```

---

### 1.3 Growth-Based Progress Score

**Location**: `adaptive_action_limits.py` → new method `_calculate_progress_score()`

**New Method**:
```python
def _calculate_progress_score(self, agent_id: str, current_role: str) -> Dict[str, float]:
    """
    Calculate growth-based progress score for agent in current role.
    
    Progress = (current_w_B - initial_w_B_for_role) × resource_efficiency
    
    Returns:
        Dict with progress_score, initial_w_B, current_w_B, efficiency
    """
    # Get initial w_B when agent was assigned this role
    role_data = self.db.execute_query("""
        SELECT initial_w_B_for_role, current_w_B
        FROM agent_operating_modes
        WHERE agent_id = ? AND operating_mode = ?
        ORDER BY assigned_timestamp DESC
        LIMIT 1
    """, (agent_id, current_role))
    
    if not role_data:
        return {'progress_score': 0.0, 'initial_w_B': 0.5, 'current_w_B': 0.5, 'efficiency': 1.0}
    
    initial_w_B = role_data[0]['initial_w_B_for_role']
    
    # Get CURRENT w_B from agents table
    agent_data = self.db.execute_query("""
        SELECT self_network_bias, score_efficiency FROM agents WHERE agent_id = ?
    """, (agent_id,))
    
    current_w_B = agent_data[0]['self_network_bias'] if agent_data else 0.5
    efficiency = agent_data[0]['score_efficiency'] if agent_data else 1.0
    efficiency = max(0.1, min(2.0, efficiency))  # Clamp to reasonable range
    
    # Progress = growth × efficiency
    w_B_growth = current_w_B - initial_w_B
    progress_score = w_B_growth * efficiency
    
    # Update current_w_B in mode record
    self.db.execute_query("""
        UPDATE agent_operating_modes 
        SET current_w_B = ?, progress_score = ?
        WHERE agent_id = ? AND operating_mode = ?
        AND assigned_timestamp = (
            SELECT MAX(assigned_timestamp) FROM agent_operating_modes
            WHERE agent_id = ? AND operating_mode = ?
        )
    """, (current_w_B, progress_score, agent_id, current_role, agent_id, current_role))
    
    return {
        'progress_score': progress_score,
        'initial_w_B': initial_w_B,
        'current_w_B': current_w_B,
        'efficiency': efficiency
    }
```

**Integration into `calculate_agent_salary()`**:
```python
def calculate_agent_salary(self, agent_id: str, generation: int) -> Dict[str, Any]:
    # ... existing code ...
    
    # Get agent's current role
    agent_role = self._get_agent_role(agent_id)
    
    # Calculate progress score
    progress_data = self._calculate_progress_score(agent_id, agent_role)
    progress_score = progress_data['progress_score']
    
    # ATP boost for low-start agents (per fairness protocol)
    initial_w_B = progress_data['initial_w_B']
    if initial_w_B < 0.4:
        low_start_boost = (0.4 - initial_w_B) * 0.5  # Up to +0.2 for lowest starters
    else:
        low_start_boost = 0.0
    
    # Progress bonus (rewards growth)
    progress_bonus = max(0, progress_score) * 0.3  # Up to +0.3 for strong growth
    
    # Combine all factors
    budget_multiplier = (
        role_multiplier +           # Base by role (0.8 - 1.5)
        performance_bonus +         # Percentile adjustment (-0.25 to +0.25)
        low_start_boost +           # Help for low-starters (0 to +0.2)
        progress_bonus              # Reward for growth (0 to +0.3)
    )
    
    # ... rest of salary calculation ...
```

---

### 2.1 Soft Role Transition System (Phase 2)

**Location**: `agent_operating_mode_system.py` → new method `attempt_role_transition()`

```python
def attempt_role_transition(self, agent_id: str, target_role: str, generation: int) -> Dict[str, Any]:
    """
    Attempt a voluntary role transition with probabilistic success.
    
    Success probability = skill_match × (1 + progress_score) × network_need
    
    Failed transitions:
    - Cost 10% ATP (learning tax)
    - Are ALWAYS allowed (preserve voluntary choice)
    - Build skill for future attempts
    
    Returns:
        Dict with success, new_role, probability, atp_cost
    """
    current_role = self._get_agent_current_role(agent_id)
    
    # Can't transition to same role
    if current_role == target_role:
        return {'success': True, 'new_role': target_role, 'probability': 1.0, 'atp_cost': 0}
    
    # Calculate skill match (how good is agent at target role based on history?)
    skill_match = self._calculate_role_skill_match(agent_id, target_role)
    
    # Get progress score
    progress_data = self._calculate_progress_score(agent_id, current_role)
    progress_bonus = 1.0 + max(0, progress_data['progress_score'])
    
    # Get network need for target role
    network_need = self._get_network_role_demand(target_role)
    
    # Calculate success probability
    success_probability = min(0.95, skill_match * progress_bonus * network_need)
    
    # Roll for success
    import random
    roll = random.random()
    success = roll < success_probability
    
    if success:
        # Successful transition
        self._record_mode_assignment(agent_id, None, generation, target_role, 
                                    f"voluntary_transition_from_{current_role}")
        atp_cost = 0
        logger.info(f"[TRANSITION] Agent {agent_id[:8]} {current_role} -> {target_role} SUCCESS "
                   f"(prob={success_probability:.2f}, roll={roll:.2f})")
    else:
        # Failed transition - stay in current role but pay learning tax
        atp_cost = 0.10  # 10% ATP penalty
        
        # Record failed attempt for skill building
        self._record_transition_attempt(agent_id, current_role, target_role, 
                                        success_probability, generation)
        
        logger.info(f"[TRANSITION] Agent {agent_id[:8]} {current_role} -> {target_role} FAILED "
                   f"(prob={success_probability:.2f}, roll={roll:.2f}, tax=10%)")
    
    return {
        'success': success,
        'new_role': target_role if success else current_role,
        'probability': success_probability,
        'atp_cost': atp_cost
    }
```

---

### 2.2 Asymmetric Stagnation Penalties (Phase 2)

**Location**: `adaptive_action_limits.py` → integrate into `calculate_agent_salary()`

```python
def _calculate_stagnation_penalty(self, agent_id: str, agent_role: str, 
                                   progress_data: Dict) -> float:
    """
    Calculate penalty for high-start agents who stagnate.
    
    Graduated curve:
    - progress < 0 (regression): -0.30 penalty
    - progress < 0.05 (stagnant): -0.15 penalty
    - progress < 0.10 (slow): -0.05 penalty
    - progress >= 0.10 (growing): +0.10 × progress bonus
    
    Only applies to agents with initial_w_B >= 0.5 (high-starters)
    """
    initial_w_B = progress_data['initial_w_B']
    progress_score = progress_data['progress_score']
    
    # Low-starters get no stagnation penalty (they get ATP boost instead)
    if initial_w_B < 0.5:
        return 0.0
    
    # Higher expectations for higher starters
    expected_progress = initial_w_B * 0.15  # 0.5 start → expect 0.075 progress
    adjusted_progress = progress_score - expected_progress
    
    if adjusted_progress < -0.1:  # Significant regression
        penalty = -0.30
        logger.debug(f"[PENALTY] Agent regressing: {penalty}")
    elif adjusted_progress < 0.0:  # Mild regression
        penalty = -0.15
    elif adjusted_progress < 0.05:  # Stagnant
        penalty = -0.05
    else:  # Growing as expected or better
        penalty = 0.10 * adjusted_progress  # Bonus for exceeding expectations
    
    return penalty
```

---

## Database Schema Changes

### New Columns for `agent_operating_modes` table:

```sql
-- Add to complete_database_schema.sql or run directly

ALTER TABLE agent_operating_modes ADD COLUMN IF NOT EXISTS initial_w_B_for_role REAL DEFAULT 0.5;
ALTER TABLE agent_operating_modes ADD COLUMN IF NOT EXISTS current_w_B REAL DEFAULT 0.5;
ALTER TABLE agent_operating_modes ADD COLUMN IF NOT EXISTS progress_score REAL DEFAULT 0.0;

-- New table for transition attempts (skill building)
CREATE TABLE IF NOT EXISTS role_transition_attempts (
    attempt_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    from_role TEXT NOT NULL,
    to_role TEXT NOT NULL,
    success_probability REAL NOT NULL,
    was_successful BOOLEAN NOT NULL,
    generation INTEGER NOT NULL,
    attempt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX IF NOT EXISTS idx_transition_agent ON role_transition_attempts(agent_id);
CREATE INDEX IF NOT EXISTS idx_transition_roles ON role_transition_attempts(from_role, to_role);
```

### New Signal Type for `regulatory_signals` table:

```sql
-- Role need adjustment signals (emitted by regulatory_signal_engine.py)
-- signal_type = 'role_need_adjustment'
-- target_role = 'pioneer' | 'optimizer' | 'generalist' | 'exploiter'
-- signal_value = -0.3 to +0.3 (ATP adjustment)
```

---

## Testing Plan

### Unit Tests (automated)

1. **ATP Calculation Tests**:
   - Pioneer gets higher base ATP than Exploiter
   - Low-start agents get ATP boost
   - High-start stagnant agents get penalty
   - Network need adjustment applies correctly

2. **Progress Score Tests**:
   - Correctly calculates w_B growth
   - Efficiency multiplier applied
   - Initial snapshot preserved across updates

3. **Role Transition Tests**:
   - Probability formula correct
   - Failed transitions charge 10% ATP
   - Skill builds with repeated attempts

### Integration Tests (live evolution)

1. Run 5 generations, verify:
   - Pioneer ATP > Optimizer ATP > Exploiter ATP
   - Agents with positive progress get bonuses
   - Stagnant high-starters get penalties

2. Check database:
   - `initial_w_B_for_role` populated on role assignment
   - `progress_score` updated correctly
   - `role_transition_attempts` records failed attempts

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Pioneer budget starvation | Common | Rare | Count of Pioneers hitting budget limit early |
| Exploiter budget surplus | Common | Rare | Avg unused budget for Exploiters |
| Growth correlation with resources | None | Positive | Correlation(progress_score, budget_multiplier) |
| Role transition attempts | N/A | Tracked | Count in `role_transition_attempts` |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing salary calculation | Add new factors incrementally; old factors still apply |
| Schema migration errors | Use IF NOT EXISTS; handle missing columns gracefully |
| Performance regression | All new queries use existing indexed columns |
| Dual economy fusion | Explicit separation in code; prestige never affects ATP |

---

## Implementation Order

1. **Schema changes** (add columns, create table)
2. **`_calculate_progress_score()`** (new method)
3. **`_record_mode_assignment()`** (capture initial_w_B)
4. **`ROLE_BASE_ATP`** constant + `_get_network_role_need()`
5. **Update `calculate_agent_salary()`** with all new factors
6. **`_calculate_stagnation_penalty()`** (for high-starters)
7. **Test with live evolution** (verify no regressions)
8. **Phase 2: `attempt_role_transition()`** (next session)

---

## Alignment with AGI Theory

| Principle | How This Implements It |
|-----------|----------------------|
| **Dual Economy** | ATP based on role + growth, prestige stays separate |
| **Database-as-Organism** | Progress tracked in database, outlives individual games |
| **Voluntary Choice** | Soft transitions (probabilistic), always allowed |
| **Evolutionary Dynamics** | Low-starters get chance to grow, high-starters must continue |
| **Free Will** | Agent can attempt any transition, system doesn't prevent "bad" choices |

---

**Next Step**: Begin Phase 1 implementation starting with schema changes.
