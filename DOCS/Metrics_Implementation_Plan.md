# Metrics System Implementation Plan

**Document Purpose**: Detailed implementation plan for the Societal Metrics System  
**Date**: December 22, 2025  
**Reference**: [Societal_Metrics_Implementation_Analysis.md](Societal_Metrics_Implementation_Analysis.md)  
**Status**: Planning Phase

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [Pycache Enforcement](#pycache-enforcement-law)
3. [File Organization](#file-organization)
4. [Implementation Phases](#implementation-phases)
5. [Integration with Existing Code](#integration-with-existing-code)
6. [Testing Strategy](#testing-strategy)
7. [Database Schema Changes](#database-schema-changes)
8. [Rollback Strategy](#rollback-strategy)

---

## Architecture Principles

### Core Design Laws

| Law | Description | Enforcement |
|-----|-------------|-------------|
| **1. Pycache Disabled** | NEVER generate `.pyc` files | Every Python file starts with `os.environ['PYTHONDONTWRITEBYTECODE'] = '1'` |
| **2. Database-Only Storage** | No log files, all data in SQLite | Use `DatabaseLogHandler`, never `FileHandler` |
| **3. No Orphaned Code** | Every addition integrates with existing | PR checklist: "What existing code does this enhance?" |
| **4. Single Responsibility** | One class = one metric category | Separate files for distinct concerns |
| **5. Dependency Injection** | Pass `DatabaseInterface` to all classes | Never instantiate DB inside metric classes |

### Code Consistency Standards

```python
# TEMPLATE: Every new metric file MUST follow this structure

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # LAW: Always first line after imports

"""
[Module Name] - [One-line description]

Part of the Societal Metrics System.
See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class [MetricClassName]:
    """
    [Description of what this metric measures]
    
    Autopoiesis Role: [How this enables self-regulation]
    Problem Solved: [Which system problem this addresses]
    
    Usage:
        metric = [MetricClassName](db)
        value = metric.calculate(generation)
    """
    
    def __init__(self, db: DatabaseInterface):
        """Initialize with database interface (dependency injection)."""
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure required database tables/columns exist."""
        # Add schema migrations here
        pass
    
    def calculate(self, generation: int) -> float:
        """
        Calculate the metric value.
        
        Args:
            generation: Current evolution generation
            
        Returns:
            Metric value (typically 0.0 to 1.0, documented if different)
        """
        raise NotImplementedError
    
    def get_trigger_action(self, value: float, generation: int) -> Optional[Dict[str, Any]]:
        """
        Determine if metric value should trigger an action.
        
        Returns:
            Dict with action details if trigger fires, None otherwise
        """
        return None
```

---

## Pycache Enforcement (LAW)

### Why This Matters

1. **Version Control Cleanliness**: `.pyc` files pollute git status
2. **Deterministic Execution**: Source is always the truth
3. **LLM Context Management**: Prevents confusion about file states

### Enforcement Mechanisms

#### Mechanism 1: File-Level (MANDATORY)

Every Python file MUST start with:

```python
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
```

#### Mechanism 2: Process-Level (BELT AND SUSPENDERS)

In `autonomous_evolution_runner.py` and `run_evolution.py`:

```python
import sys
sys.dont_write_bytecode = True
```

#### Mechanism 3: Pre-Run Cleanup

The `cleanup_temp_files.py` already deletes pycache. Ensure it runs before every evolution:

```python
# In autonomous_evolution_runner.py __init__
from cleanup_temp_files import cleanup_temp_files
cleanup_temp_files()  # Delete any existing pycache
```

#### Mechanism 4: Git Enforcement

`.gitignore` already includes:

```
__pycache__/
*.py[cod]
*$py.class
```

#### Mechanism 5: Pre-Commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Fail if any pycache directories exist
if find . -type d -name "__pycache__" | grep -q .; then
    echo "ERROR: __pycache__ directories found. Run cleanup_temp_files.py"
    exit 1
fi
```

#### Mechanism 6: Validation in Tests

```python
def test_no_pycache_directive():
    """Every Python file must disable pycache."""
    import glob
    
    for filepath in glob.glob("**/*.py", recursive=True):
        if filepath.startswith("tests/"):
            continue
        with open(filepath, 'r') as f:
            content = f.read(500)  # First 500 chars
            assert "PYTHONDONTWRITEBYTECODE" in content, \
                f"{filepath} missing pycache disable directive"
```

---

## File Organization

### New Files to Create

```
BitterTruth-AI/
├── autopoiesis_monitor.py      # NEW: Emergence Gain, Identity Drift
├── metric_confidence.py        # NEW: Meta-metric confidence tracking
├── trigger_controller.py       # NEW: Prevents feedback resonance
├── metric_rotator.py           # NEW: Anti-Goodhart rotation system
└── tests/
    ├── test_autopoiesis.py     # NEW: Tests for autopoiesis metrics
    ├── test_metric_confidence.py
    ├── test_trigger_controller.py
    └── test_metric_integration.py  # Integration tests
```

### Files to Enhance (Not Replace)

| Existing File | Enhancements |
|---------------|--------------|
| `network_intelligence_engine.py` | Add `calculate_emergence_gain()` method |
| `regulatory_signal_engine.py` | Add `calculate_control_error()` method |
| `agent_operating_mode_system.py` | Add `calculate_role_saturation()` method |
| `viral_package_engine.py` | Add `calculate_information_velocity()`, `calculate_hub_fragility()` |
| `frustration_detector.py` | Add `calculate_strategy_abandonment_lag()` |
| `prestige_engine.py` | Add `calculate_trust_concentration()` method |
| `core_gameplay.py` | Enhance loop detection (already partial) |
| `performance_analyzer.py` | Add multi-scale correlation methods |

### Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    autonomous_evolution_runner.py                │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ AutopoiesisMonitor│  │ TriggerController│  │ MetricRotator  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘ │
│           │                     │                     │          │
│           ▼                     ▼                     ▼          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   MetricConfidenceTracker                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│           ┌──────────────────┼──────────────────┐               │
│           ▼                  ▼                  ▼               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐      │
│  │ network_intel  │ │ regulatory_sig │ │ viral_package  │      │
│  │ _engine.py     │ │ _engine.py     │ │ _engine.py     │      │
│  └────────────────┘ └────────────────┘ └────────────────┘      │
│                              │                                   │
│                              ▼                                   │
│                    ┌────────────────┐                           │
│                    │ DatabaseInterface│                          │
│                    └────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Goal**: Build the foundational classes that all metrics depend on.

#### 1.1 TriggerController (Day 1-2)

**File**: `trigger_controller.py`

```python
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
TriggerController - Prevents feedback resonance in metric-driven adjustments.

Implements Constraint 1 from Societal_Metrics_Implementation_Analysis.md:
- Cooldowns between trigger fires
- Multi-metric corroboration
- Small nudges, not emergency brakes
- Damping for consecutive fires
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from database_interface import DatabaseInterface


class TriggerController:
    """
    Manages metric triggers with anti-resonance protections.
    
    All parameter adjustments MUST go through this controller.
    """
    
    # Configuration constants
    COOLDOWN_GENERATIONS = 3
    DAMPING_FACTOR = 0.5
    MAX_ADJUSTMENT = 0.10  # 10% max change per generation
    CORROBORATION_THRESHOLD = 2  # Minimum metrics that must agree
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create trigger_history table if not exists."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS trigger_history (
                trigger_id TEXT PRIMARY KEY,
                trigger_name TEXT NOT NULL,
                generation INTEGER NOT NULL,
                fired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metric_value REAL,
                adjustment_magnitude REAL,
                corroborating_metrics TEXT,  -- JSON list
                was_damped BOOLEAN DEFAULT FALSE,
                consecutive_fire_count INTEGER DEFAULT 1
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_trigger_name_gen 
            ON trigger_history(trigger_name, generation)
        """)
    
    def can_fire(self, trigger_name: str, generation: int) -> bool:
        """Check if trigger is allowed to fire (cooldown respected)."""
        result = self.db.execute_query("""
            SELECT MAX(generation) as last_gen
            FROM trigger_history
            WHERE trigger_name = ?
        """, (trigger_name,))
        
        if not result or result[0]['last_gen'] is None:
            return True
        
        return (generation - result[0]['last_gen']) >= self.COOLDOWN_GENERATIONS
    
    def get_consecutive_fires(self, trigger_name: str, generation: int) -> int:
        """Count how many times this trigger has fired in recent generations."""
        result = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM trigger_history
            WHERE trigger_name = ?
              AND generation > ? - 10
        """, (trigger_name, generation))
        
        return result[0]['count'] if result else 0
    
    def calculate_damped_magnitude(self, trigger_name: str, 
                                    base_magnitude: float,
                                    generation: int) -> float:
        """Apply damping for consecutive fires."""
        consecutive = self.get_consecutive_fires(trigger_name, generation)
        damped = base_magnitude * (self.DAMPING_FACTOR ** consecutive)
        return min(damped, self.MAX_ADJUSTMENT)
    
    def require_corroboration(self, primary_value: float,
                               secondary_values: List[float],
                               threshold: float = 0.5) -> bool:
        """
        Check if multiple metrics agree before allowing adjustment.
        
        Returns True if enough metrics exceed threshold.
        """
        agreeing = sum(1 for v in secondary_values if v > threshold)
        return agreeing >= self.CORROBORATION_THRESHOLD
    
    def record_fire(self, trigger_name: str, generation: int,
                    metric_value: float, adjustment: float,
                    corroborating_metrics: List[str]) -> str:
        """Record that a trigger fired."""
        import uuid
        import json
        
        trigger_id = f"trig_{uuid.uuid4().hex[:12]}"
        consecutive = self.get_consecutive_fires(trigger_name, generation) + 1
        
        self.db.execute_query("""
            INSERT INTO trigger_history 
            (trigger_id, trigger_name, generation, metric_value, 
             adjustment_magnitude, corroborating_metrics, 
             was_damped, consecutive_fire_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trigger_id, trigger_name, generation, metric_value,
            adjustment, json.dumps(corroborating_metrics),
            consecutive > 1, consecutive
        ))
        
        return trigger_id
    
    def fire_with_safeguards(self, trigger_name: str,
                              generation: int,
                              primary_metric_value: float,
                              secondary_metric_values: Dict[str, float],
                              base_adjustment: float,
                              apply_func: callable) -> Optional[Dict[str, Any]]:
        """
        Attempt to fire a trigger with all safeguards applied.
        
        Args:
            trigger_name: Name of the trigger
            generation: Current generation
            primary_metric_value: Main metric that triggered this
            secondary_metric_values: Other metrics for corroboration
            base_adjustment: Desired adjustment magnitude
            apply_func: Function to call if trigger fires (takes adjustment as arg)
            
        Returns:
            Dict with results if fired, None if blocked
        """
        # Check cooldown
        if not self.can_fire(trigger_name, generation):
            return None
        
        # Check corroboration
        if not self.require_corroboration(
            primary_metric_value,
            list(secondary_metric_values.values())
        ):
            return None
        
        # Calculate damped adjustment
        actual_adjustment = self.calculate_damped_magnitude(
            trigger_name, base_adjustment, generation
        )
        
        # Apply the adjustment
        result = apply_func(actual_adjustment)
        
        # Record the fire
        trigger_id = self.record_fire(
            trigger_name, generation, primary_metric_value,
            actual_adjustment, list(secondary_metric_values.keys())
        )
        
        return {
            'trigger_id': trigger_id,
            'adjustment_applied': actual_adjustment,
            'was_damped': actual_adjustment < base_adjustment,
            'result': result
        }
```

**Tests**: `tests/test_trigger_controller.py`

```python
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
from trigger_controller import TriggerController
from database_interface import DatabaseInterface


@pytest.fixture
def db():
    """Create in-memory database for testing."""
    db = DatabaseInterface(":memory:")
    return db


@pytest.fixture
def controller(db):
    return TriggerController(db)


class TestTriggerController:
    
    def test_cooldown_blocks_immediate_refire(self, controller):
        """Trigger should not fire again within cooldown period."""
        # First fire should succeed
        controller.record_fire("test_trigger", 100, 0.8, 0.1, ["metric_a"])
        
        # Immediate refire should be blocked
        assert not controller.can_fire("test_trigger", 101)
        assert not controller.can_fire("test_trigger", 102)
        
        # After cooldown, should be allowed
        assert controller.can_fire("test_trigger", 103)
    
    def test_damping_reduces_magnitude(self, controller):
        """Consecutive fires should reduce adjustment magnitude."""
        # First fire: full magnitude
        mag1 = controller.calculate_damped_magnitude("test", 0.1, 100)
        
        # Record fire
        controller.record_fire("test", 100, 0.8, mag1, [])
        
        # Second fire: should be damped
        mag2 = controller.calculate_damped_magnitude("test", 0.1, 104)
        
        assert mag2 < mag1
        assert mag2 == pytest.approx(0.1 * 0.5)  # 50% damping
    
    def test_max_adjustment_cap(self, controller):
        """Adjustment should never exceed MAX_ADJUSTMENT."""
        mag = controller.calculate_damped_magnitude("test", 0.5, 100)
        assert mag <= controller.MAX_ADJUSTMENT
    
    def test_corroboration_requires_agreement(self, controller):
        """Should require multiple metrics to agree."""
        # Only primary high, secondaries low
        assert not controller.require_corroboration(0.8, [0.1, 0.2, 0.3])
        
        # Primary and 2+ secondaries high
        assert controller.require_corroboration(0.8, [0.6, 0.7, 0.3])
    
    def test_fire_with_safeguards_respects_all_checks(self, controller):
        """Full fire should check cooldown, corroboration, and damping."""
        applied = []
        
        result = controller.fire_with_safeguards(
            trigger_name="emergence_low",
            generation=100,
            primary_metric_value=0.3,  # Low emergence
            secondary_metric_values={
                "velocity_low": 0.6,
                "diversity_low": 0.7
            },
            base_adjustment=0.15,
            apply_func=lambda adj: applied.append(adj)
        )
        
        assert result is not None
        assert len(applied) == 1
        assert applied[0] <= 0.10  # Respects MAX_ADJUSTMENT
```

#### 1.2 MetricConfidenceTracker (Day 3-4)

**File**: `metric_confidence.py`

(Implementation as shown in the analysis document, with full test suite)

#### 1.3 MetricRotator (Day 5)

**File**: `metric_rotator.py`

(Implementation as shown in the analysis document)

---

### Phase 2: Core Metrics (Week 2)

**Goal**: Implement Tier 1 self-regulation metrics.

#### 2.1 Emergence Gain (Day 1-2)

**File**: Enhance `network_intelligence_engine.py`

```python
# Add to NetworkIntelligenceEngine class

def calculate_emergence_gain(self, generation: int) -> float:
    """
    Calculate if network intelligence exceeds sum of individual agents.
    
    Emergence Gain > 1.0 means collective intelligence is working.
    
    Formula:
        network_wins_using_shared_knowledge / solo_discoveries
    
    Where:
        network_wins = Levels beaten using sequences from other agents
        solo_discoveries = Levels beaten without any shared knowledge
    """
    # Network level: Wins where agent used sequence discovered by another
    network_wins = self.db.execute_query("""
        SELECT COUNT(*) as count
        FROM agent_arc_performance aap
        JOIN winning_sequences ws ON aap.game_id = ws.game_id 
                                   AND aap.level_reached >= ws.level_number
        WHERE ws.discovered_by_agent_id != aap.agent_id
          AND aap.game_timestamp > datetime('now', '-7 days')
          AND ws.times_referenced > 0
    """)[0]['count'] or 0
    
    # Individual level: Wins where agent discovered solution themselves
    solo_discoveries = self.db.execute_query("""
        SELECT COUNT(DISTINCT ws.sequence_id) as count
        FROM winning_sequences ws
        WHERE ws.discovered_at > datetime('now', '-7 days')
          AND ws.times_referenced = 0  -- Never shared/reused
    """)[0]['count'] or 1  # Avoid division by zero
    
    emergence_gain = network_wins / max(solo_discoveries, 1)
    
    # Store in ecosystem snapshot
    self._store_emergence_metric(generation, emergence_gain)
    
    return emergence_gain

def _store_emergence_metric(self, generation: int, emergence_gain: float):
    """Store emergence gain in database for tracking."""
    self.db.execute_query("""
        INSERT INTO ecosystem_metrics (metric_name, generation, value, measured_at)
        VALUES ('emergence_gain', ?, ?, datetime('now'))
        ON CONFLICT(metric_name, generation) DO UPDATE SET value = ?
    """, (generation, emergence_gain, emergence_gain))
```

**Test**: `tests/test_emergence_gain.py`

```python
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
from network_intelligence_engine import NetworkIntelligenceEngine
from database_interface import DatabaseInterface


@pytest.fixture
def db():
    db = DatabaseInterface(":memory:")
    # Create required tables
    db.execute_query("""
        CREATE TABLE agent_arc_performance (
            game_id TEXT, agent_id TEXT, level_reached INTEGER,
            game_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute_query("""
        CREATE TABLE winning_sequences (
            sequence_id TEXT PRIMARY KEY, game_id TEXT, level_number INTEGER,
            discovered_by_agent_id TEXT, times_referenced INTEGER DEFAULT 0,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute_query("""
        CREATE TABLE ecosystem_metrics (
            metric_name TEXT, generation INTEGER, value REAL, measured_at TIMESTAMP,
            PRIMARY KEY (metric_name, generation)
        )
    """)
    return db


@pytest.fixture
def engine(db):
    return NetworkIntelligenceEngine(db)


class TestEmergenceGain:
    
    def test_no_sharing_gives_emergence_1(self, db, engine):
        """When all discoveries are solo, emergence = 1.0."""
        # Insert solo discoveries
        db.execute_query("""
            INSERT INTO winning_sequences (sequence_id, game_id, level_number, 
                                           discovered_by_agent_id, times_referenced)
            VALUES ('seq1', 'game1', 1, 'agent1', 0),
                   ('seq2', 'game2', 1, 'agent2', 0)
        """)
        
        gain = engine.calculate_emergence_gain(100)
        assert gain == pytest.approx(1.0, rel=0.1)
    
    def test_high_sharing_gives_emergence_above_1(self, db, engine):
        """When agents reuse others' sequences, emergence > 1.0."""
        # Insert shared sequence
        db.execute_query("""
            INSERT INTO winning_sequences (sequence_id, game_id, level_number,
                                           discovered_by_agent_id, times_referenced)
            VALUES ('seq1', 'game1', 1, 'agent1', 5)
        """)
        
        # Insert performances using that sequence by OTHER agents
        for i in range(5):
            db.execute_query("""
                INSERT INTO agent_arc_performance (game_id, agent_id, level_reached)
                VALUES ('game1', ?, 1)
            """, (f'agent{i+2}',))  # Different agents
        
        gain = engine.calculate_emergence_gain(100)
        assert gain > 1.0
    
    def test_emergence_stored_in_db(self, db, engine):
        """Emergence metric should be stored for tracking."""
        engine.calculate_emergence_gain(100)
        
        result = db.execute_query("""
            SELECT value FROM ecosystem_metrics 
            WHERE metric_name = 'emergence_gain' AND generation = 100
        """)
        assert len(result) == 1
```

#### 2.2 Control Error (Day 2)

**File**: Enhance `regulatory_signal_engine.py`

#### 2.3 Role Saturation (Day 3)

**File**: Enhance `agent_operating_mode_system.py`

#### 2.4 Loop Detection Enhancement (Day 4)

**File**: Enhance `core_gameplay.py`

#### 2.5 Identity Drift (Day 5)

**File**: New `autopoiesis_monitor.py`

---

### Phase 3: Performance Metrics (Week 3)

- Information Velocity
- Hub Fragility
- Compression Yield
- Strategy Abandonment Lag

---

### Phase 4: Integration (Week 4)

- Wire all metrics into `autonomous_evolution_runner.py`
- Add to dashboard output
- Create human spot-check queries

---

## Integration with Existing Code

### Pattern: Enhance, Don't Replace

For each metric, follow this integration pattern:

```python
# WRONG: Creating new standalone file that duplicates functionality
# File: my_new_emergence_tracker.py
class EmergenceTracker:
    def __init__(self):
        self.db = DatabaseInterface("core_data.db")  # BAD: Creates own DB
    ...

# RIGHT: Enhancing existing file
# File: network_intelligence_engine.py (already exists)
class NetworkIntelligenceEngine:
    def __init__(self, db: DatabaseInterface):  # GOOD: Receives DB
        self.db = db
        ...
    
    # ADD new method to existing class
    def calculate_emergence_gain(self, generation: int) -> float:
        ...
```

### Integration Checklist

For each new metric, verify:

- [ ] Does a class already exist that handles related functionality?
- [ ] Am I using dependency injection (receiving `db`, not creating it)?
- [ ] Have I added the method to an existing class where possible?
- [ ] If new file needed: Does it follow the template?
- [ ] Have I added pycache disable as first line?
- [ ] Have I updated the imports in `autonomous_evolution_runner.py`?

### Existing Code to Reuse

| Need | Use This Existing Code |
|------|------------------------|
| Database access | `DatabaseInterface` from `database_interface.py` |
| Logging | `setup_database_logging()` from `database_logger.py` |
| Agent queries | Methods in `agent_operating_mode_system.py` |
| Sequence queries | Methods in `viral_package_engine.py` |
| Performance data | Methods in `performance_analyzer.py` |
| Prestige calculations | Methods in `prestige_engine.py` |
| Ecosystem snapshots | Methods in `network_intelligence_engine.py` |

---

## Testing Strategy

### Test Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Pyramid                             │
│                                                              │
│                          ▲                                   │
│                         /│\                                  │
│                        / │ \       Integration Tests         │
│                       /  │  \      (test_metric_integration) │
│                      /   │   \                               │
│                     /────┼────\                              │
│                    /     │     \   Component Tests           │
│                   /      │      \  (test_trigger_controller) │
│                  /       │       \                           │
│                 /────────┼────────\                          │
│                /         │         \  Unit Tests             │
│               /          │          \ (individual methods)   │
│              /───────────┴───────────\                       │
└─────────────────────────────────────────────────────────────┘
```

### Test Types

#### 1. Unit Tests (Per Method)

**Location**: `tests/test_[module_name].py`

```python
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest

class TestEmergenceGainCalculation:
    """Unit tests for emergence gain calculation logic."""
    
    def test_division_by_zero_prevented(self):
        """Should return 1.0 when no solo discoveries."""
        ...
    
    def test_high_sharing_returns_above_one(self):
        """Network wins > solo should give emergence > 1.0."""
        ...
```

#### 2. Component Tests (Per Class)

**Location**: `tests/test_[class_name].py`

```python
class TestTriggerController:
    """Component tests for TriggerController class."""
    
    def test_full_fire_workflow(self):
        """Test complete trigger fire with all safeguards."""
        ...
    
    def test_state_persists_across_instances(self):
        """Trigger history should persist in database."""
        ...
```

#### 3. Integration Tests

**Location**: `tests/test_metric_integration.py`

```python
class TestMetricIntegration:
    """Test metrics working together in the evolution loop."""
    
    def test_emergence_triggers_transmission_increase(self):
        """Low emergence should trigger viral transmission increase."""
        ...
    
    def test_trigger_controller_prevents_cascade(self):
        """Metrics should not create feedback loops."""
        ...
    
    def test_confidence_decay_affects_rotation(self):
        """Low-confidence metrics should rotate out faster."""
        ...
```

#### 4. Regression Tests

**Location**: `tests/test_regression.py`

```python
class TestRegression:
    """Regression tests for previously fixed bugs."""
    
    def test_pycache_disabled_in_all_files(self):
        """All Python files must disable pycache."""
        import glob
        for path in glob.glob("**/*.py", recursive=True):
            if "tests/" in path or "__pycache__" in path:
                continue
            with open(path, 'r') as f:
                content = f.read(500)
            assert "PYTHONDONTWRITEBYTECODE" in content, f"Missing in {path}"
    
    def test_no_unicode_emojis(self):
        """Rule 11: No unicode emojis in code."""
        import glob
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F]')  # Emoticons
        for path in glob.glob("**/*.py", recursive=True):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            assert not emoji_pattern.search(content), f"Emoji found in {path}"
```

#### 5. Property-Based Tests

**Location**: `tests/test_properties.py`

```python
from hypothesis import given, strategies as st

class TestMetricProperties:
    """Property-based tests for metric invariants."""
    
    @given(st.floats(min_value=0, max_value=1))
    def test_confidence_always_in_range(self, value):
        """Confidence must always be in [0, 1]."""
        confidence = normalize_confidence(value * 10)  # Scale up
        assert 0.0 <= confidence <= 1.0
    
    @given(st.integers(min_value=0, max_value=1000))
    def test_damping_always_reduces_magnitude(self, consecutive_fires):
        """More consecutive fires = smaller adjustment."""
        controller = TriggerController(db)
        mag = controller.calculate_damped_magnitude("test", 0.1, 100)
        
        # Simulate fires
        for i in range(consecutive_fires):
            controller.record_fire("test", 100 + i*4, 0.5, 0.05, [])
        
        new_mag = controller.calculate_damped_magnitude("test", 0.1, 100 + consecutive_fires*4 + 4)
        
        if consecutive_fires > 0:
            assert new_mag <= mag
```

### Test Execution

#### Run All Tests

```bash
# From project root
python -m pytest tests/ -v --tb=short
```

#### Run Specific Category

```bash
python -m pytest tests/test_trigger_controller.py -v
python -m pytest tests/ -k "regression" -v
python -m pytest tests/ -k "integration" -v
```

#### Run Before Commit

```bash
# This should be mandatory before any commit
python -m pytest tests/ --tb=short -q
```

### Test Coverage Requirements

| Category | Minimum Coverage |
|----------|------------------|
| Core infrastructure (trigger, confidence) | 90% |
| Tier 1 metrics | 80% |
| Tier 2-3 metrics | 70% |
| Integration | 60% |

```bash
# Generate coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

---

## Database Schema Changes

### New Tables Required

```sql
-- Trigger history for feedback prevention
CREATE TABLE IF NOT EXISTS trigger_history (
    trigger_id TEXT PRIMARY KEY,
    trigger_name TEXT NOT NULL,
    generation INTEGER NOT NULL,
    fired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_value REAL,
    adjustment_magnitude REAL,
    corroborating_metrics TEXT,  -- JSON list
    was_damped BOOLEAN DEFAULT FALSE,
    consecutive_fire_count INTEGER DEFAULT 1
);

-- Metric confidence tracking
CREATE TABLE IF NOT EXISTS metric_confidence (
    metric_name TEXT NOT NULL,
    generation INTEGER NOT NULL,
    confidence_score REAL NOT NULL,
    contradiction_rate REAL,
    adaptation_speed REAL,
    predictive_power REAL,
    influence_concentration REAL,
    decay_multiplier REAL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_name, generation)
);

-- Metric rotation history
CREATE TABLE IF NOT EXISTS metric_rotation_history (
    rotation_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    active_metrics TEXT NOT NULL,  -- JSON list
    was_skipped BOOLEAN DEFAULT FALSE,
    one_time_metrics_added TEXT,  -- JSON list
    rotation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ecosystem metrics (generalized)
CREATE TABLE IF NOT EXISTS ecosystem_metrics (
    metric_name TEXT NOT NULL,
    generation INTEGER NOT NULL,
    value REAL NOT NULL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON for additional context
    PRIMARY KEY (metric_name, generation)
);
```

### Migration Strategy

Each new file uses `_ensure_schema()` pattern:

```python
def _ensure_schema(self):
    """Idempotent schema creation - safe to call multiple times."""
    self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS [table_name] (...)
    """)
    
    # Add columns if missing (for upgrades)
    try:
        self.db.execute_query("SELECT [new_column] FROM [table_name] LIMIT 1")
    except Exception:
        self.db.execute_query("ALTER TABLE [table_name] ADD COLUMN [new_column] ...")
```

---

## Rollback Strategy

### If Metrics Cause Problems

1. **Disable Trigger Controller** (immediate)

```python
# In autonomous_evolution_runner.py
USE_TRIGGER_CONTROLLER = False  # Flip this to disable
```

2. **Revert to Previous Behavior**

```python
# Metrics still calculate, but don't trigger actions
if USE_TRIGGER_CONTROLLER:
    result = controller.fire_with_safeguards(...)
else:
    # Old behavior: direct parameter adjustment
    apply_adjustment(base_magnitude)
```

3. **Database Cleanup**

```sql
-- If needed, remove metric history
DELETE FROM trigger_history WHERE generation > [problem_generation];
DELETE FROM metric_confidence WHERE generation > [problem_generation];
```

### Version Tags

After each phase completion, create a git tag:

```bash
git tag -a "metrics-phase-1-complete" -m "TriggerController, MetricConfidence implemented"
git push origin --tags
```

This allows easy rollback:

```bash
git checkout metrics-phase-1-complete
```

---

## Summary: Implementation Order

| Week | Day | Task | File | Test File |
|------|-----|------|------|-----------|
| 1 | 1-2 | TriggerController | `trigger_controller.py` | `test_trigger_controller.py` |
| 1 | 3-4 | MetricConfidenceTracker | `metric_confidence.py` | `test_metric_confidence.py` |
| 1 | 5 | MetricRotator | `metric_rotator.py` | `test_metric_rotator.py` |
| 2 | 1-2 | Emergence Gain | `network_intelligence_engine.py` | `test_emergence_gain.py` |
| 2 | 2 | Control Error | `regulatory_signal_engine.py` | `test_control_error.py` |
| 2 | 3 | Role Saturation | `agent_operating_mode_system.py` | `test_role_saturation.py` |
| 2 | 4 | Loop Detection | `core_gameplay.py` | `test_loop_detection.py` |
| 2 | 5 | Identity Drift | `autopoiesis_monitor.py` | `test_identity_drift.py` |
| 3 | 1-5 | Tier 2-3 metrics | Various | Various |
| 4 | 1-3 | Integration | `autonomous_evolution_runner.py` | `test_metric_integration.py` |
| 4 | 4-5 | Documentation, Cleanup | - | `test_regression.py` |

---

## Checklist Before Each Implementation

- [ ] Pycache disabled (`os.environ['PYTHONDONTWRITEBYTECODE'] = '1'`)
- [ ] Using existing code where possible
- [ ] Dependency injection for database
- [ ] `_ensure_schema()` for database migrations
- [ ] Unit tests written BEFORE implementation
- [ ] Tests pass locally
- [ ] No unicode emojis (Rule 11)
- [ ] Integration point identified in `autonomous_evolution_runner.py`

---

**Document Status**: Ready for implementation  
**First Task**: Create `trigger_controller.py` with tests  
**Review Frequency**: Update after each phase completion
