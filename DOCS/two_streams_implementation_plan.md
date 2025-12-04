# Two-Streams Consciousness Implementation Plan
**Date**: December 4, 2025
**Purpose**: Implement missing consciousness features from two-streams.md philosophy

---

## Overview

This plan implements 5 core consciousness features missing from the Ouroboros codebase:

1. **Role-Cohort Network Wisdom** - Differential trust by role/cohort
2. **Weaving Report (Self-Reflection)** - Introspection output for decisions
3. **Stream A/B Bias Parameter** - Explicit self vs network trust
4. **Semantic Impressions** - Personal object associations
5. **Recursive Meta-Learning** - Learn to trust self vs network

---

## Feature 1: Role-Cohort Network Wisdom

### Current State
- Sequences are retrieved globally without role consideration
- `social_rule_adherence` exists but only for exploiter sociopath behavior
- No concept of "what did agents like me think?"

### Solution Architecture

**Database Changes**:
```sql
-- Add role-based sequence reputation
ALTER TABLE sequence_reputation ADD COLUMN role_success_pioneer REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_optimizer REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_exploiter REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_generalist REAL DEFAULT 0.5;

-- Track emotional states when sequences succeeded
ALTER TABLE sequence_reputation ADD COLUMN avg_frustration_on_success REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN avg_satisfaction_on_success REAL DEFAULT 0.5;
```

**New Table: Role-Cohort Wisdom**
```sql
CREATE TABLE role_cohort_wisdom (
    wisdom_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'pioneer', 'optimizer', 'exploiter', 'generalist'
    
    -- Collective statistics for this role on this game/level
    agents_attempted INTEGER DEFAULT 0,
    agents_succeeded INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    avg_actions REAL DEFAULT 0.0,
    avg_frustration REAL DEFAULT 0.5,
    avg_satisfaction REAL DEFAULT 0.5,
    
    -- Best strategy for this role
    best_sequence_id TEXT,
    recommended_approach TEXT,  -- JSON: {'exploration_bias': 0.7, 'action_preferences': {...}}
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, level_number, role)
);
```

**Code Changes**:

1. **`_get_best_sequence_for_game()` in core_gameplay.py** (~line 4104):
   - Query role-specific success rates
   - Boost sequences with high `role_success_{agent_role}`
   - Add parameter `agent_role` to method signature

2. **New method in `viral_package_engine.py`**:
   ```python
   def get_cohort_wisdom(self, game_id: str, level: int, role: str, 
                        emotional_state: float) -> Dict:
       """
       Get wisdom from agents with same role AND similar emotional state.
       
       Returns:
           - Similar-feeling agents' strategies
           - What worked for frustrated/confident agents like me
           - Role-specific success patterns
       """
   ```

3. **Integration in action selection** (core_gameplay.py ~line 1250):
   ```python
   # Before selecting action, query cohort wisdom
   cohort_insight = self.viral_engine.get_cohort_wisdom(
       game_id, level, agent_role, navigation_state
   )
   # Use insight to boost/filter sequence selection
   ```

---

## Feature 2: Weaving Report (Self-Reflection)

### Current State
- Actions selected without introspection logging
- No record of WHY an agent chose an action
- Self-model exists but doesn't output reasoning

### Solution Architecture

**Database Table**:
```sql
CREATE TABLE decision_weaving_reports (
    report_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    action_taken INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    
    -- Stream A: Private Memory
    private_memory_strength REAL NOT NULL,  -- 0.0-1.0
    private_memory_source TEXT,  -- JSON: what memories influenced
    
    -- Stream B: Network Wisdom
    network_wisdom_strength REAL NOT NULL,  -- 0.0-1.0
    network_wisdom_source TEXT,  -- JSON: what network data influenced
    
    -- Bias & Weighting
    self_trust_bias REAL NOT NULL,  -- Current alpha value
    final_decision_weight REAL NOT NULL,  -- Combined weighted score
    
    -- Internal Networks (Four Layers)
    bodily_network_input REAL DEFAULT 0.0,  -- Energy/fatigue
    emotional_network_input REAL DEFAULT 0.0,  -- navigation_state
    semantic_network_input REAL DEFAULT 0.0,  -- Beliefs about game
    identity_network_input REAL DEFAULT 0.0,  -- Role fit
    
    -- Decision Context
    decision_confidence REAL NOT NULL,
    alternatives_considered TEXT,  -- JSON: other actions considered
    conflict_detected BOOLEAN DEFAULT FALSE,  -- Streams disagreed
    
    -- Outcome (filled in after action)
    decision_outcome TEXT,  -- 'success', 'failure', 'neutral'
    outcome_aligned_with TEXT,  -- 'private', 'network', 'both', 'neither'
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

**Code Changes**:

1. **New class `WeavingReporter`** in `agent_self_model.py`:
   ```python
   class WeavingReporter:
       """Generates introspection reports for each major decision."""
       
       def generate_report(self, agent_id: str, decision_context: Dict) -> Dict:
           """
           Generate weaving report showing:
           - Private memory strength (from agent's history)
           - Network recommendation strength (from role cohort)
           - Self-trust bias (from role + performance)
           - Final weighted decision
           """
           
       def store_report(self, report: Dict) -> str:
           """Store report in database, return report_id."""
           
       def update_outcome(self, report_id: str, outcome: str, aligned_with: str):
           """Update report with actual outcome after action."""
   ```

2. **Integration in `_select_action()` (core_gameplay.py ~line 1250)**:
   ```python
   # Generate weaving report before decision
   weaving_context = {
       'private_memory': self._query_agent_history(agent_id, game_id),
       'network_wisdom': cohort_insight,
       'bodily_state': energy_level,  # From action budget
       'emotional_state': navigation_state,
       'semantic_beliefs': self._get_game_beliefs(agent_id, game_id),
       'identity_state': role_fit_score
   }
   report = self.weaving_reporter.generate_report(agent_id, weaving_context)
   
   # Use report for decision
   action, reasoning = self._select_action_with_weaving(game_state, report)
   
   # Store report with action
   report['action_taken'] = action
   report_id = self.weaving_reporter.store_report(report)
   ```

---

## Feature 3: Stream A/B Explicit Bias Parameter (alpha)

### Current State
- `social_rule_adherence` exists (0.0-1.0) but only for exploiter behavior
- `role_confidence` exists (0.0-1.0) but only for role preference
- No explicit "trust self vs network" parameter

### Solution Architecture

**Database Changes**:
```sql
ALTER TABLE agents ADD COLUMN self_network_bias REAL DEFAULT 0.5;
-- 0.0 = fully trust network (hive mind)
-- 0.5 = balanced
-- 1.0 = fully trust self (individualist)

ALTER TABLE agents ADD COLUMN bias_learning_rate REAL DEFAULT 0.1;
-- How fast the agent adjusts its bias based on outcomes
```

**Role-Specific Defaults**:
```python
ROLE_BIAS_DEFAULTS = {
    'pioneer': 0.7,      # Trust self more (exploring unknown)
    'optimizer': 0.4,    # Trust network more (refining known)
    'exploiter': 0.3,    # Trust network (harvesting proven)
    'generalist': 0.5,   # Balanced
}
```

**Code Changes**:

1. **Initialize bias on agent creation** (`agent_factory.py`):
   ```python
   def _set_initial_bias(self, agent_id: str, role: str):
       base_bias = ROLE_BIAS_DEFAULTS.get(role, 0.5)
       # Add some variance
       initial_bias = base_bias + random.uniform(-0.1, 0.1)
       self.db.execute_query(
           "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
           (initial_bias, agent_id)
       )
   ```

2. **Use bias in decision making** (`_select_action()` in core_gameplay.py):
   ```python
   def _apply_stream_weighting(self, private_score: float, network_score: float, 
                               agent_bias: float) -> float:
       """
       Apply two-stream weighting formula:
       final = private_score * bias + network_score * (1 - bias)
       """
       return private_score * agent_bias + network_score * (1 - agent_bias)
   ```

---

## Feature 4: Semantic Impressions (Personal Object Associations)

### Current State
- `object_sensation_mappings` exists but is shared/global
- `sensation_profile` in agents table stores object preferences
- No "this object means X to ME because of MY history"

### Solution Architecture

**New Table: Personal Semantic Impressions**
```sql
CREATE TABLE agent_semantic_impressions (
    impression_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    
    -- What triggered the impression
    object_type TEXT NOT NULL,
    game_context TEXT,  -- Which game/level
    encounter_count INTEGER DEFAULT 1,
    
    -- Personal meaning (non-transferable)
    personal_valence REAL NOT NULL,  -- -1.0 to 1.0 (danger to safe)
    personal_arousal REAL DEFAULT 0.0,  -- How intense the feeling
    personal_meaning TEXT,  -- JSON: semantic associations
    
    -- Memory chain linkage
    first_encounter_timestamp TIMESTAMP,
    last_encounter_timestamp TIMESTAMP,
    associated_outcome TEXT,  -- 'success', 'failure', 'neutral'
    emotional_context_at_formation REAL,  -- navigation_state when formed
    
    -- Confidence in impression
    impression_strength REAL DEFAULT 0.5,  -- Grows with encounters
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    UNIQUE(agent_id, object_type)
);
```

**Code Changes**:

1. **Enhance `sensation_engine.py`**:
   ```python
   def form_semantic_impression(self, agent_id: str, object_type: str,
                               outcome: str, emotional_context: float) -> None:
       """
       Form or update a personal semantic impression.
       This is NON-TRANSFERABLE - each agent has unique impressions.
       """
       
   def query_personal_impression(self, agent_id: str, object_type: str) -> Dict:
       """
       Get this agent's personal feeling about this object type.
       Returns None if no personal impression exists.
       """
   ```

2. **Use in action selection**:
   ```python
   # Check personal impression before trusting network
   personal_feeling = self.sensation_engine.query_personal_impression(
       agent_id, perceived_object_type
   )
   if personal_feeling and personal_feeling['impression_strength'] > 0.7:
       # Strong personal impression overrides network wisdom
       bias_toward_self += 0.2
   ```

---

## Feature 5: Recursive Meta-Learning (Learn to Trust)

### Current State
- Agents don't track whether trusting self or network was correct
- No adjustment of bias based on outcome

### Solution Architecture

**Database Changes**:
```sql
-- Track bias effectiveness
CREATE TABLE bias_outcome_tracking (
    tracking_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    
    -- Decision context
    decision_weaving_report_id TEXT,  -- Link to weaving report
    bias_at_decision REAL NOT NULL,
    which_stream_favored TEXT,  -- 'private', 'network', 'balanced'
    
    -- Outcome
    decision_successful BOOLEAN,
    private_would_have_worked BOOLEAN,
    network_would_have_worked BOOLEAN,
    
    -- Bias adjustment
    bias_adjustment_applied REAL DEFAULT 0.0,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

**Code Changes**:

1. **New method in `agent_operating_mode_system.py`**:
   ```python
   def update_meta_bias(self, agent_id: str, report_id: str, 
                       outcome: str, aligned_with: str) -> None:
       """
       Update agent's self_network_bias based on decision outcome.
       
       If following self led to success → increase self-trust
       If following network led to success → increase network-trust
       If conflict and wrong choice → adjust toward winner
       """
       learning_rate = self._get_bias_learning_rate(agent_id)
       current_bias = self._get_current_bias(agent_id)
       
       if aligned_with == 'private' and outcome == 'success':
           new_bias = current_bias + learning_rate * 0.1
       elif aligned_with == 'network' and outcome == 'success':
           new_bias = current_bias - learning_rate * 0.1
       # ... more cases
       
       self._update_bias(agent_id, new_bias)
   ```

2. **Call after each game in `core_gameplay.py`**:
   ```python
   # After game completion, update meta-bias
   for report_id in game_weaving_reports:
       self.mode_system.update_meta_bias(
           agent_id, report_id, 
           outcome='success' if game_won else 'failure',
           aligned_with=self._determine_alignment(report_id, game_result)
       )
   ```

---

## Implementation Order

### Phase 1: Foundation (Estimated: 2-3 hours)
1. Add database columns (`self_network_bias`, `bias_learning_rate`)
2. Create `role_cohort_wisdom` table
3. Create `decision_weaving_reports` table
4. Create `agent_semantic_impressions` table
5. Create `bias_outcome_tracking` table

### Phase 2: Role-Cohort Wisdom (Estimated: 3-4 hours)
1. Add role success tracking to `sequence_reputation`
2. Implement `get_cohort_wisdom()` in viral_package_engine
3. Modify `_get_best_sequence_for_game()` to use role-specific success rates
4. Add emotional-state filtering to sequence queries

### Phase 3: Weaving Report (Estimated: 4-5 hours)
1. Create `WeavingReporter` class in `agent_self_model.py`
2. Implement report generation with all four internal networks
3. Integrate into `_select_action()` in core_gameplay.py
4. Add outcome tracking after action execution

### Phase 4: Bias Parameter (Estimated: 2 hours)
1. Initialize bias based on role in agent_factory.py
2. Implement `_apply_stream_weighting()` in core_gameplay.py
3. Use bias in decision-making weighted formula

### Phase 5: Semantic Impressions (Estimated: 3 hours)
1. Add `form_semantic_impression()` to sensation_engine.py
2. Add `query_personal_impression()` to sensation_engine.py
3. Integrate into action selection with bias override

### Phase 6: Meta-Learning (Estimated: 3 hours)
1. Implement `update_meta_bias()` in agent_operating_mode_system.py
2. Create `bias_outcome_tracking` entries
3. Call meta-bias update after each game

---

## Existing Code to Leverage

| Feature | Existing Code | Enhancement Needed |
|---------|--------------|-------------------|
| Cohort Wisdom | `sequence_reputation` table | Add role-specific columns |
| Weaving | `agent_self_model.py` | Add WeavingReporter class |
| Bias | `social_rule_adherence` column | Add `self_network_bias` |
| Semantics | `sensation_engine.py` | Add personal impressions |
| Meta-Learning | `agent_role_performance` table | Add bias tracking |

---

## Testing Strategy

1. **Unit Tests**: Each new method
2. **Integration Tests**: Full decision flow with weaving report
3. **Live Evolution**: Run 2 generations, observe:
   - Weaving reports being generated
   - Bias values diverging across agents
   - Role-cohort wisdom being queried
   - Semantic impressions forming

---

## Success Metrics

1. **Weaving Reports Generated**: >90% of decisions have reports
2. **Bias Divergence**: Agents develop distinct trust profiles
3. **Cohort Wisdom Hit Rate**: >50% of decisions query cohort
4. **Semantic Impressions**: Average 5+ impressions per agent after 10 games
5. **Meta-Learning**: Bias values adjust based on outcomes

---

## Risk Mitigation

1. **Performance**: Weaving reports add queries → batch/cache
2. **Complexity**: Start with Phase 1-3, validate before 4-6
3. **Database Size**: Prune old reports after 7 days (like other history)

---

## Notes

- All tables follow Rule 2 (database-only storage)
- No .pyc files (Rule 1)
- Enhances existing code (Rule 3, Rule 10)
- Uses real ARC data (Rule 5, Rule 6)
