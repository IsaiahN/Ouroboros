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

## Database Schema Assessment

### Already Exists (Reusable)

| Column/Table | Location | Current Use | Two-Streams Use |
|-------------|----------|-------------|-----------------|
| `social_rule_adherence` | agents | Exploiter sociopath (0.0-1.0) | **Extend** to general self/network bias |
| `navigation_state` | agents | Emotional state (-1.0 to 1.0) | **Emotional Network** |
| `sensation_profile` | agents | JSON object sensations | **Semantic Network** (object impressions) |
| `role_confidence` | agents | Role preference strength | **Identity Network** |
| `emotional_intelligence_score` | agents | EI metric | Informs bias calculation |
| `avg_frustration` / `avg_satisfaction` | agent_role_performance | Per-role emotional averages | Role-cohort filtering |
| `object_sensation_mappings` | table | Agent-object associations | **Foundation for semantic impressions** |
| `sensation_learning_events` | table | Learning history | Track bias effectiveness |

### Minimal Changes Required

| Change Type | Count | Tables Affected |
|-------------|-------|-----------------|
| New columns in existing tables | 11 | agents (2), sequence_reputation (6), object_sensation_mappings (2), sensation_learning_events (1) |
| New tables | 2 | decision_weaving_reports, role_cohort_wisdom |

---

## Feature 1: Role-Cohort Network Wisdom

### Current State
- Sequences are retrieved globally without role consideration
- `social_rule_adherence` exists but only for exploiter sociopath behavior
- No concept of "what did agents like me think?"
- **EXISTING**: `agent_role_performance` already tracks per-role stats (can be leveraged)

### Solution Architecture

**Database Changes to `sequence_reputation`** (6 new columns):
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

**New Table: Role-Cohort Wisdom** (aggregates from agent_role_performance):
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
    avg_frustration REAL DEFAULT 0.5,
    avg_satisfaction REAL DEFAULT 0.5,
    best_sequence_id TEXT,
    
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
- **EXISTING**: `agent_self_model.py` tracks controlled objects (extend this)
- **EXISTING**: `agent_emotional_state` table exists (can leverage)

### Solution Architecture

**New Table: Decision Weaving Reports** (simplified from original):
```sql
CREATE TABLE decision_weaving_reports (
    report_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    level_number INTEGER DEFAULT 1,
    action_taken INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    
    -- Stream weights
    private_memory_strength REAL NOT NULL,  -- 0.0-1.0
    network_wisdom_strength REAL NOT NULL,  -- 0.0-1.0
    self_trust_bias REAL NOT NULL,  -- Current alpha value
    final_decision_weight REAL NOT NULL,  -- Combined weighted score
    
    -- Three internal networks (using existing data sources)
    emotional_input REAL DEFAULT 0.0,  -- From navigation_state
    semantic_input REAL DEFAULT 0.0,  -- From sensation_profile / object_sensation_mappings
    identity_input REAL DEFAULT 0.0,  -- From role_confidence + role_fit_score
    
    -- Context
    conflict_detected BOOLEAN DEFAULT FALSE,  -- Streams disagreed
    decision_outcome TEXT,  -- 'success', 'failure', 'neutral'
    outcome_aligned_with TEXT,  -- 'private', 'network', 'both', 'neither'
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Index for efficient queries
CREATE INDEX idx_weaving_agent_game ON decision_weaving_reports(agent_id, game_id);
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
       
       def format_for_api_reasoning(self, report: Dict) -> Dict:
           """Format weaving report for inclusion in API reasoning payload."""
   ```

2. **Integration in `_select_action()` (core_gameplay.py ~line 1250)**:
   ```python
   # Generate weaving report before decision
   weaving_context = {
       'private_memory': self._query_agent_history(agent_id, game_id),
       'network_wisdom': cohort_insight,
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

3. **API Reasoning Payload Enhancement** (core_gameplay.py in action execution):
   
   The existing reasoning dict gets a new `self_reflection` key with weaving data:
   
   ```python
   # Current reasoning structure (enhanced)
   reasoning = {
       "action": "ACTION5",
       "reasoning": "PIONEER mode | Score: 0.0",
       "level": 1,
       "score": 0,
       "timestamp": "2025-12-04T10:48:11.670743",
       "agent_id": "offspring_6ce165ae",
       "agent_mode": "pioneer",
       "generation": 269,
       
       # NEW: Self-reflection weaving data
       "self_reflection": {
           "private_memory_strength": 0.73,
           "private_memory_source": "agent historical game data",
           "network_wisdom_strength": 0.85,
           "network_wisdom_source": "role cohort + sequence reputation",
           "self_trust_bias": 0.65,
           "bias_source": "pioneer role default + meta-learning adjustment",
           "final_decision_weight": 0.772,  # 0.73*0.65 + 0.85*0.35
           "formula": "private*bias + network*(1-bias)",
           "internal_networks": {
               "emotional": 0.15,   # navigation_state (-1 to 1 mapped to 0-1)
               "semantic": 0.45,    # avg sensation scores from object impressions
               "identity": 0.70     # role_confidence + role_fit_score
           },
           "conflict_detected": False,
           "decision_confidence": 0.77
       },
       
       "self_model": {
           "objects_agent_controls": [],
           "control_confidence": 0,
           "object_dependencies": []
       },
       "world_model": { ... },
       "strategy": "balanced",
       "learning_mode": "smart_exploration"
   }
   ```

4. **Implementation in `_build_reasoning_dict()` method** (core_gameplay.py):
   ```python
   def _build_reasoning_dict(self, action: int, game_state: GameState, 
                             weaving_report: Optional[Dict] = None) -> Dict:
       """Build reasoning dict for API call, including self-reflection."""
       
       reasoning = {
           "action": f"ACTION{action}",
           "reasoning": f"{self.agent_mode.upper()} mode | Score: {game_state.score}",
           "level": game_state.current_level,
           "score": game_state.score,
           "timestamp": datetime.now().isoformat(),
           "agent_id": self.game_config.get('agent_id'),
           "agent_mode": self.agent_mode,
           "generation": self.game_config.get('generation', 0),
           # ... existing fields ...
       }
       
       # Add self-reflection if weaving report available
       if weaving_report:
           reasoning["self_reflection"] = {
               "private_memory_strength": weaving_report.get('private_memory_strength', 0.5),
               "private_memory_source": "agent historical game data",
               "network_wisdom_strength": weaving_report.get('network_wisdom_strength', 0.5),
               "network_wisdom_source": "role cohort + sequence reputation",
               "self_trust_bias": weaving_report.get('self_trust_bias', 0.5),
               "bias_source": f"{self.agent_mode} role + meta-learning",
               "final_decision_weight": weaving_report.get('final_decision_weight', 0.5),
               "formula": "private*bias + network*(1-bias)",
               "internal_networks": {
                   "emotional": weaving_report.get('emotional_input', 0.5),
                   "semantic": weaving_report.get('semantic_input', 0.5),
                   "identity": weaving_report.get('identity_input', 0.5)
               },
               "conflict_detected": weaving_report.get('conflict_detected', False),
               "decision_confidence": weaving_report.get('decision_confidence', 0.5)
           }
       
       return reasoning
   ```

---

## Example API Reasoning Payload with Self-Reflection

After implementation, every action sent to the ARC API will include self-reflection weaving data:

```json
{
  "action": "ACTION5",
  "reasoning": "PIONEER mode | Score: 0.0",
  "level": 1,
  "score": 0,
  "timestamp": "2025-12-04T10:48:11.670743",
  "agent_id": "offspring_6ce165ae",
  "agent_mode": "pioneer",
  "generation": 269,
  
  "self_reflection": {
    "private_memory_strength": 0.73,
    "private_memory_source": "agent historical game data (3 prior attempts on this game)",
    "network_wisdom_strength": 0.85,
    "network_wisdom_source": "pioneer cohort: 12 agents attempted, 4 succeeded, avg_score=2.3",
    "self_trust_bias": 0.65,
    "bias_source": "pioneer role default (0.7) + meta-learning adjustment (-0.05)",
    "final_decision_weight": 0.772,
    "formula": "0.73 * 0.65 + 0.85 * 0.35 = 0.772",
    "internal_networks": {
      "emotional": 0.15,
      "emotional_source": "navigation_state: slightly frustrated",
      "semantic": 0.45,
      "semantic_source": "object impressions: color_14=danger(-0.3), color_11=neutral(0.0)",
      "identity": 0.70,
      "identity_source": "role_confidence: 0.70, role_fit_score: 0.65"
    },
    "conflict_detected": false,
    "conflict_reason": null,
    "decision_confidence": 0.77,
    "alternative_considered": "ACTION3 (network suggested, weight=0.68)"
  },
  
  "self_model": {
    "objects_agent_controls": [],
    "control_confidence": 0,
    "object_dependencies": []
  },
  "world_model": {
    "obstacles": [
      {"position": [0, 31], "color": 14},
      {"position": [29, 31], "color": 12},
      {"position": [17, 21], "color": 9},
      {"position": [55, 21], "color": 11},
      {"position": [55, 45], "color": 11}
    ],
    "goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "strategy": "balanced",
  "learning_mode": "smart_exploration"
}
```

### Human-Readable Self-Reflection Summary

The `self_reflection` block can be summarized as:

```
=== SELF-REFLECTION ===
Private memory strength: 0.73 (based on recall of my personal agent historical data)
Network recommendation strength: 0.85 (based on pioneer cohort wisdom)
My bias (trust self): 0.65 (pioneer role default + meta-learning adjustment)
Final decision weight: 0.73 * 0.65 + 0.85 * 0.35 = 0.772

Internal Networks:
  - Emotional: 0.15 (slightly frustrated - navigation_state low)
  - Semantic:  0.45 (mixed impressions - some objects feel dangerous)
  - Identity:  0.70 (confident in pioneer role)

Decision: ACTION5 (confidence: 77%)
Alternative: ACTION3 was considered (network preferred, but private memory stronger)
```

---

## Feature 3: Stream A/B Explicit Bias Parameter (alpha)

### Current State
- **EXISTING**: `social_rule_adherence` (0.0-1.0) - currently only for exploiter behavior
- **EXISTING**: `role_confidence` (0.0-1.0) - for role preference
- **EXISTING**: `sensation_learning_rate` (0.3 default) - can inform bias learning
- No explicit "trust self vs network" parameter

### Solution Architecture

**Database Changes to `agents`** (2 new columns):
```sql
ALTER TABLE agents ADD COLUMN self_network_bias REAL DEFAULT 0.5;
-- 0.0 = fully trust network (hive mind)
-- 0.5 = balanced
-- 1.0 = fully trust self (individualist)

ALTER TABLE agents ADD COLUMN bias_learning_rate REAL DEFAULT 0.1;
-- How fast the agent adjusts its bias based on outcomes
-- Can inherit from sensation_learning_rate as base
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
- **EXISTING**: `object_sensation_mappings` table - already per-agent!
  - Has: `agent_id`, `object_type`, `sensation_score`, `success_count`, `failure_count`
  - Missing: personal meaning, impression strength, emotional context
- **EXISTING**: `sensation_profile` in agents table (JSON)
- No "this object means X to ME because of MY history"

### Solution Architecture

**Database Changes to `object_sensation_mappings`** (2 new columns - NO new table needed!):
```sql
-- Extend existing table instead of creating new one
ALTER TABLE object_sensation_mappings ADD COLUMN personal_meaning TEXT;
-- JSON: {'association': 'danger', 'memory': 'failed here 3 times'}

ALTER TABLE object_sensation_mappings ADD COLUMN impression_strength REAL DEFAULT 0.5;
-- 0.0-1.0: grows with encounters, strong impressions override network wisdom
```

**NOTE**: The existing `object_sensation_mappings` table already has:
- `mapping_id`, `agent_id`, `generation`, `object_type`
- `sensation_score`, `confidence_level`, `learn_count`
- `success_count`, `failure_count`, `first_learned`, `last_updated`

This is 90% of what we need for semantic impressions!

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
- **EXISTING**: `sensation_learning_events` table tracks learning outcomes
- **EXISTING**: `agent_meta_learning` table exists! (can extend)
- Agents don't track whether trusting self or network was correct
- No adjustment of bias based on outcome

### Solution Architecture

**Database Changes to `sensation_learning_events`** (1 new column):
```sql
-- Track which stream the decision aligned with
ALTER TABLE sensation_learning_events ADD COLUMN aligned_with_stream TEXT;
-- Values: 'private', 'network', 'balanced'
```

**NOTE**: Instead of creating `bias_outcome_tracking` table, we extend the existing 
`sensation_learning_events` which already tracks:
- `agent_id`, `game_id`, `generation`
- `action_taken`, `reward_received`, `learning_success`
- `pre/post_sensation_score`, `pre/post_navigation_state`

This provides the foundation for meta-learning without a new table.

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

## Complete Schema Changes Summary

### Agents Table (2 new columns)
```sql
ALTER TABLE agents ADD COLUMN self_network_bias REAL DEFAULT 0.5;
ALTER TABLE agents ADD COLUMN bias_learning_rate REAL DEFAULT 0.1;
```

### Sequence Reputation Table (6 new columns)
```sql
ALTER TABLE sequence_reputation ADD COLUMN role_success_pioneer REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_optimizer REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_exploiter REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN role_success_generalist REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN avg_frustration_on_success REAL DEFAULT 0.5;
ALTER TABLE sequence_reputation ADD COLUMN avg_satisfaction_on_success REAL DEFAULT 0.5;
```

### Object Sensation Mappings Table (2 new columns)
```sql
ALTER TABLE object_sensation_mappings ADD COLUMN personal_meaning TEXT;
ALTER TABLE object_sensation_mappings ADD COLUMN impression_strength REAL DEFAULT 0.5;
```

### Sensation Learning Events Table (1 new column)
```sql
ALTER TABLE sensation_learning_events ADD COLUMN aligned_with_stream TEXT;
```

### NEW: Decision Weaving Reports Table
```sql
CREATE TABLE IF NOT EXISTS decision_weaving_reports (
    report_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    level_number INTEGER DEFAULT 1,
    action_taken INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    private_memory_strength REAL NOT NULL,
    network_wisdom_strength REAL NOT NULL,
    self_trust_bias REAL NOT NULL,
    final_decision_weight REAL NOT NULL,
    emotional_input REAL DEFAULT 0.0,
    semantic_input REAL DEFAULT 0.0,
    identity_input REAL DEFAULT 0.0,
    conflict_detected BOOLEAN DEFAULT FALSE,
    decision_outcome TEXT,
    outcome_aligned_with TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
CREATE INDEX IF NOT EXISTS idx_weaving_agent_game ON decision_weaving_reports(agent_id, game_id);
```

### NEW: Role Cohort Wisdom Table
```sql
CREATE TABLE IF NOT EXISTS role_cohort_wisdom (
    wisdom_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    agents_attempted INTEGER DEFAULT 0,
    agents_succeeded INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    avg_frustration REAL DEFAULT 0.5,
    avg_satisfaction REAL DEFAULT 0.5,
    best_sequence_id TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, level_number, role)
);
CREATE INDEX IF NOT EXISTS idx_cohort_game_role ON role_cohort_wisdom(game_id, role);
```

---

## Implementation Order (Revised)

### Phase 1: Database Foundation (30 minutes)
1. Run all ALTER TABLE statements
2. Create 2 new tables with indexes
3. Verify schema with `PRAGMA table_info()`

### Phase 2: Bias Parameter (1-2 hours)
1. Initialize `self_network_bias` based on role in agent_factory.py
2. Implement `_apply_stream_weighting()` in core_gameplay.py
3. Use bias in decision-making weighted formula

### Phase 3: Weaving Report (3-4 hours)
1. Create `WeavingReporter` class in `agent_self_model.py`
2. Generate reports using existing data sources:
   - `emotional_input` = (navigation_state + 1) / 2 (map -1..1 to 0..1)
   - `semantic_input` = avg(sensation_scores from object_sensation_mappings)
   - `identity_input` = (role_confidence + role_fit_score) / 2
3. Integrate into `_select_action()` in core_gameplay.py
4. Add outcome tracking after action execution

### Phase 4: Role-Cohort Wisdom (2-3 hours)
1. Implement `get_cohort_wisdom()` in viral_package_engine.py
2. Update `sequence_reputation` when sequences succeed/fail by role
3. Modify `_get_best_sequence_for_game()` to use role-specific success rates

### Phase 5: Semantic Impressions (2 hours)
1. Add `form_semantic_impression()` to sensation_engine.py
2. Add `query_personal_impression()` to sensation_engine.py
3. Integrate into action selection with bias override

### Phase 6: Meta-Learning (2 hours)
1. Track `aligned_with_stream` in sensation_learning_events
2. Implement `update_meta_bias()` in agent_operating_mode_system.py
3. Call meta-bias update after each game

**Total Estimated Time**: 10-14 hours (down from 17-20)

---

## Existing Code to Leverage

| Feature | Existing Code | Enhancement Needed |
|---------|--------------|-------------------|
| Cohort Wisdom | `agent_role_performance` table | Aggregate into `role_cohort_wisdom` |
| Cohort Wisdom | `sequence_reputation` table | Add 6 role-specific columns |
| Weaving | `agent_self_model.py` | Add `WeavingReporter` class |
| Weaving | `agent_emotional_state` table | Use as data source |
| Bias | `social_rule_adherence` column | Add `self_network_bias` (similar concept) |
| Bias | `sensation_learning_rate` column | Use as base for `bias_learning_rate` |
| Semantics | `object_sensation_mappings` table | Add 2 columns (already per-agent!) |
| Semantics | `sensation_engine.py` | Add 2 new methods |
| Meta-Learning | `sensation_learning_events` table | Add 1 column |
| Meta-Learning | `agent_meta_learning` table | Exists! Can extend |

---

## Data Flow Diagram

```
                    ┌─────────────────────────────────────────┐
                    │           DECISION POINT                │
                    └─────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │   STREAM A    │        │   WEIGHTING   │        │   STREAM B    │
    │ Private Memory│        │   (alpha)     │        │Network Wisdom │
    └───────────────┘        └───────────────┘        └───────────────┘
            │                         │                         │
            │    self_network_bias    │                         │
            │    (0.0-1.0)            │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │ - Game history│        │ final_weight =│        │ - Cohort stats│
    │ - Sensations  │───────▶│ A*bias +      │◀───────│ - Role success│
    │ - Impressions │        │ B*(1-bias)    │        │ - Sequences   │
    └───────────────┘        └───────────────┘        └───────────────┘
                                      │
                                      ▼
                            ┌───────────────┐
                            │WEAVING REPORT │
                            │ - 3 networks  │
                            │ - conflict?   │
                            │ - confidence  │
                            └───────────────┘
                                      │
                                      ▼
                            ┌───────────────┐
                            │   ACTION      │
                            └───────────────┘
                                      │
                                      ▼
                            ┌───────────────┐
                            │   OUTCOME     │
                            └───────────────┘
                                      │
                                      ▼
                            ┌───────────────┐
                            │ META-LEARNING │
                            │ Update bias   │
                            │ based on      │
                            │ outcome       │
                            └───────────────┘
```

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
2. **Bias Divergence**: Agents develop distinct trust profiles (stddev > 0.1)
3. **Cohort Wisdom Hit Rate**: >50% of decisions query cohort
4. **Semantic Impressions**: Average 5+ impressions per agent after 10 games
5. **Meta-Learning**: Bias values adjust based on outcomes (observable drift)

---

## Risk Mitigation

1. **Performance**: Weaving reports add queries → batch/cache common queries
2. **Complexity**: Start with Phase 1-3, validate before 4-6
3. **Database Size**: Prune old weaving reports after 7 days (add to safe_cleanup.py)

---

## Cleanup Integration (safe_cleanup.py)

Add to SafeDatabaseCleaner:
```python
# Decision weaving reports - keep 50,000 most recent
('decision_weaving_reports', 'timestamp', 50000, 'Decision weaving reports'),
```

---

## Notes

- All tables follow Rule 2 (database-only storage)
- No .pyc files (Rule 1)
- Enhances existing code (Rule 3, Rule 10)
- Uses real ARC data (Rule 5, Rule 6)
- Leverages 90+ existing tables instead of creating unnecessary new ones
