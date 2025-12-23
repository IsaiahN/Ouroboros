# Societal Metrics Implementation Analysis

**Document Purpose**: Evaluate, rank, and prioritize metrics from the Societal Metrics List for the Ouroboros system.

**Date**: December 22, 2025

**Goals**:
1. Rank each metric by usefulness (1-5) and implementation difficulty (1-5)
2. Group metrics by which current problems they solve
3. Apply autopoiesis lens - which metrics enable self-regulation
4. Identify metrics for human spot-checks on frontier progress

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current System Problems](#current-system-problems)
3. [Tier 1: Critical Self-Regulation Metrics](#tier-1-critical-self-regulation-metrics)
4. [Tier 2: High-Value Performance Metrics](#tier-2-high-value-performance-metrics)
5. [Tier 3: Network Health Metrics](#tier-3-network-health-metrics)
6. [Tier 4: Advanced Emergence Metrics](#tier-4-advanced-emergence-metrics)
7. [Tier 5: Long-Term Civilizational Metrics](#tier-5-long-term-civilizational-metrics)
8. [Human Spot-Check Dashboard](#human-spot-check-dashboard)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Critical Design Constraints](#critical-design-constraints-feedback-integration) *(NEW)*
    - [Trigger Coupling & Feedback Resonance](#constraint-1-trigger-coupling--feedback-resonance)
    - [Stationarity Assumption](#constraint-2-stationarity-assumption)
    - [Human Spot-Checks as Boundary Condition](#constraint-3-human-spot-checks-as-boundary-condition)
    - [Second-Order Goodhart Risk](#constraint-4-second-order-goodhart-risk)
    - [Metric Confidence Meta-Metric](#constraint-5-metric-confidence-meta-metric-new---critical-addition)

---

## Executive Summary

### What Already Exists

The Ouroboros codebase already has substantial metric infrastructure:

| System | Location | What It Tracks |
|--------|----------|----------------|
| `network_intelligence_engine.py` | Network health | Knowledge diversity, information flow, resilience, metabolic health |
| `performance_analyzer.py` | Agent performance | Win rates, efficiency, trends, stagnation |
| `prestige_engine.py` | Social capital | Network enrichment, viral spread, persistence, validation |
| `viral_package_engine.py` | Knowledge transfer | Viral packages, pariahs, infection rates |
| `regulatory_signal_engine.py` | Homeostasis | Stress signals, quorum sensing, distributed regulation |
| `frustration_detector.py` | Stuck detection | Frustration levels, quorum thresholds |
| `adaptive_action_limits.py` | Resource allocation | ATP (metabolic budget), stagnation penalties |

### Key Insight: Gap Analysis

**What's Missing for Autopoiesis**:
1. **Boundary Integrity Metrics** - System identity drift detection
2. **Self-Maintenance Cost Tracking** - Overhead vs productive work ratio
3. **Emergence Gain Measurement** - Is network smarter than sum of agents?
4. **Phase Transition Detection** - When small changes cause big effects
5. **Metric Rotation System** - Preventing Goodhart's Law gaming

### Autopoiesis Principle

> "The system must observe itself, not just to improve, but to maintain its identity as a learning organism."

Metrics serve three purposes:
1. **Self-regulation** (system adjusts automatically)
2. **Human spot-checks** (infrequent verification of frontier progress)
3. **Emergence detection** (is collective intelligence emerging?)

---

## Current System Problems

Based on [progress.md](progress.md) and codebase analysis, these are the active problems:

### Problem 1: Sequence System Reliability
- Winning sequences sometimes fail on replay
- No abstraction layer (exact matching fragile)
- **Metrics Needed**: Sequence success rate, stale sequence detection, validation disagreement

### Problem 2: Agent Role Distribution
- Population ratios sometimes suboptimal
- Pioneers work on optimized games, Optimizers on frontier
- **Metrics Needed**: Role saturation, role appropriateness, underserved game detection

### Problem 3: Knowledge Transfer Bottlenecks
- Viral packages don't always propagate
- Good solutions stay localized
- **Metrics Needed**: Information velocity, cascade detection, hub fragility

### Problem 4: Stuck State Detection
- Agents oscillate without progress
- Escape mechanisms don't always trigger
- **Metrics Needed**: Loop detection, sensitivity to initial conditions, action diversity

### Problem 5: Optimization Plateau
- Diminishing returns on optimized games
- Exploiters not finding micro-improvements
- **Metrics Needed**: Improvement rate trend, saturation detection, compression yield

---

## Tier 1: Critical Self-Regulation Metrics

These metrics should be implemented first and run automatically to enable autopoiesis.

### 1.1 Emergence Gain (PRIORITY: CRITICAL)

**Formula**: `system_output - sum(agent_outputs)`

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 3/5 |
| Problem Solved | Validates if network intelligence > individual agents |
| Autopoiesis Role | Core identity metric - are we achieving emergence? |
| Existing Code | Partial in `network_intelligence_engine.py` |

**Implementation**:
```python
def calculate_emergence_gain(generation: int) -> float:
    """
    Compare network-level wins to what random individual agents would achieve.
    If emergence_gain > 1.0, collective intelligence is working.
    """
    # Network level: All wins using shared sequences
    network_wins = count_wins_using_shared_sequences(generation)
    
    # Individual level: What agents discovered alone (no viral packages)
    solo_discoveries = count_solo_discoveries(generation)
    
    # Emergence = network_wins / max(solo_discoveries, 1)
    return network_wins / max(solo_discoveries, 1)
```

**Trigger**: If emergence_gain < 1.0 for 5 generations, increase `viral_transmission_rate`.

---

### 1.2 Control Error (Cybernetics)

**Formula**: `delta(desired_state - actual_state)` over time

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 2/5 |
| Problem Solved | Detects if regulation is overshooting or lagging |
| Autopoiesis Role | Feedback loop health |
| Existing Code | Partial in `regulatory_signal_engine.py` |

**Implementation**:
```python
TARGET_FRONTIER_PROGRESS_PER_GEN = 0.5  # Expected new levels beaten per generation

def calculate_control_error(generation: int) -> float:
    actual = get_new_levels_beaten(generation)
    return TARGET_FRONTIER_PROGRESS_PER_GEN - actual
```

**Trigger**: If control_error persists positive for 10 generations, increase exploration parameters.

---

### 1.3 Sequence Success Rate (Already Exists - Enhance)

**Formula**: `successful_replays / total_replay_attempts`

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 1/5 (already tracked) |
| Problem Solved | Sequence system reliability (Problem 1) |
| Autopoiesis Role | Knowledge quality assurance |
| Existing Code | `winning_sequences.times_validated` |

**Enhancement Needed**:
```python
# Add rolling 7-day success rate
# Trigger sequence pruning if success_rate < 0.5
```

---

### 1.4 Role Saturation Index

**Formula**: `count(agents_in_role) / ideal_count_for_game_state`

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 2/5 |
| Problem Solved | Role distribution (Problem 2) |
| Autopoiesis Role | Population self-organization |
| Existing Code | `agent_operating_mode_system.py` has role assignment |

**Implementation**:
```python
def calculate_role_saturation(generation: int) -> Dict[str, float]:
    """
    Returns saturation for each role.
    > 1.0 = oversaturated (too many)
    < 1.0 = undersaturated (need more)
    """
    game_state = get_network_game_state()  # EXPLORATION or OPTIMIZATION
    
    ideal_ratios = {
        'EXPLORATION': {'pioneer': 0.60, 'optimizer': 0.25, 'generalist': 0.10, 'exploiter': 0.05},
        'OPTIMIZATION': {'pioneer': 0.00, 'optimizer': 0.70, 'generalist': 0.15, 'exploiter': 0.15}
    }
    
    actual = get_role_distribution(generation)
    ideal = ideal_ratios[game_state]
    
    return {role: actual[role] / max(ideal[role], 0.01) for role in actual}
```

**Trigger**: Auto-reassign agents when saturation > 1.5 or < 0.5.

---

### 1.5 Information Velocity

**Formula**: `useful_packages_propagated / time_since_discovery`

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 3/5 |
| Problem Solved | Knowledge transfer bottlenecks (Problem 3) |
| Autopoiesis Role | Metabolic efficiency |
| Existing Code | `viral_package_engine.py` tracks infections |

**Implementation**:
```python
def calculate_information_velocity(package_id: str) -> float:
    """
    How fast did this package spread to 50% of compatible agents?
    """
    discovery_gen = get_package_discovery_generation(package_id)
    half_infection_gen = get_half_infection_generation(package_id)
    
    if half_infection_gen is None:
        return 0.0  # Still spreading
    
    return 1.0 / max(half_infection_gen - discovery_gen, 1)
```

**Trigger**: If avg_velocity < 0.1, increase `transmission_rate`.

---

### 1.6 Loop Detection (Lyapunov-like Divergence)

**Formula**: `action_sequence_similarity` over rolling window

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 2/5 |
| Problem Solved | Stuck state detection (Problem 4) |
| Autopoiesis Role | Oscillation prevention |
| Existing Code | `core_gameplay.py` has `consecutive_no_frame_change` |

**Implementation**:
```python
def detect_action_loop(recent_actions: List[int], window: int = 20) -> float:
    """
    Returns 0.0 = no loop, 1.0 = perfect repetition.
    Uses Lempel-Ziv complexity as proxy.
    """
    if len(recent_actions) < window:
        return 0.0
    
    # Check for repeating subsequences
    for period in range(2, window // 2):
        if recent_actions[-period:] == recent_actions[-2*period:-period]:
            return 1.0 - (period / window)  # Shorter period = more loopy
    
    return 0.0
```

**Trigger**: If loop_score > 0.7, trigger escape mechanism.

---

### 1.7 Functional Identity Drift (Autopoiesis Core)

**Formula**: `current_goal_alignment - original_goal_alignment`

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 4/5 |
| Problem Solved | Prevents system from optimizing wrong things |
| Autopoiesis Role | Identity maintenance |
| Existing Code | None |

**Implementation**:
```python
# Original goal: Beat all levels of all games
# Track: Are we still optimizing for this?

def calculate_identity_drift(generation: int) -> float:
    """
    0.0 = Perfectly aligned with original goal
    1.0 = Completely drifted (optimizing proxies instead)
    """
    # Positive: Frontier levels beaten (actual progress)
    frontier_progress = count_new_frontier_levels_beaten(generation)
    
    # Negative: Metrics gaming signals
    # - Prestige without discoveries
    # - Actions without level progress
    # - Sequences created but never used
    prestige_without_value = count_high_prestige_low_contribution(generation)
    wasted_actions = count_zero_progress_games(generation)
    orphan_sequences = count_never_used_sequences(generation)
    
    drift = (prestige_without_value + wasted_actions + orphan_sequences) / max(frontier_progress, 1)
    return min(1.0, drift / 10.0)  # Normalize
```

**Trigger**: If drift > 0.3, reset metric weights, rotate evaluation criteria.

---

## Tier 2: High-Value Performance Metrics

These metrics directly improve agent performance.

### 2.1 Marginal Value per Action (MVA)

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Identifies efficient vs wasteful agents |
| Autopoiesis Role | Resource efficiency |
| Existing Code | Partial in `performance_analyzer.py` |

**Formula**: `(score_delta) / actions_taken`

---

### 2.2 Transfer Success Rate

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Measures generalization ability |
| Autopoiesis Role | Learning quality |
| Existing Code | Can be derived from `winning_sequences.times_validated` |

**Formula**: `successful_new_domain_wins / new_domain_attempts`

---

### 2.3 Strategy Abandonment Lag

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 3/5 |
| Problem Solved | Detects agents clinging to bad strategies |
| Autopoiesis Role | Adaptation speed |
| Existing Code | Partial in `frustration_detector.py` |

**Formula**: `games_with_failing_strategy_before_switch`

---

### 2.4 Confidence Calibration Error

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 4/5 |
| Problem Solved | Overconfident or underconfident action selection |
| Autopoiesis Role | Decision quality |
| Existing Code | None |

**Formula**: `|predicted_success_rate - actual_success_rate|`

---

### 2.5 High-Leverage Action Accuracy

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 3/5 |
| Problem Solved | Did agent make right choices at critical moments? |
| Autopoiesis Role | Peak performance |
| Existing Code | None |

**Formula**: `correct_actions_at_decision_points / total_decision_points`

Decision points = moments where action determines level win/loss.

---

### 2.6 Compression Yield (Abstraction Quality)

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 4/5 |
| Problem Solved | Are abstractions useful? (Problem 1) |
| Autopoiesis Role | Knowledge efficiency |
| Existing Code | Partial in `sequence_abstraction.py` |

**Formula**: `abstract_sequence_success_rate / exact_sequence_success_rate`

If > 1.0, abstractions are more robust than exact matches.

---

## Tier 3: Network Health Metrics

These metrics track the organism (network) rather than cells (agents).

### 3.1 Knowledge Half-Life

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Detects knowledge decay |
| Autopoiesis Role | Memory persistence |
| Existing Code | Can derive from `winning_sequences.last_used` |

**Formula**: `generations_until_sequence_usage_halves`

---

### 3.2 Hub Fragility

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 3/5 |
| Problem Solved | Single-point-of-failure in knowledge network |
| Autopoiesis Role | Resilience |
| Existing Code | None |

**Formula**: `max(viral_package_carrier_concentration)`

If one agent carries 50% of packages, network is fragile.

---

### 3.3 Coordination Cost per Decision

| Attribute | Value |
|-----------|-------|
| Usefulness | 3/5 |
| Difficulty | 3/5 |
| Problem Solved | Overhead efficiency |
| Autopoiesis Role | Self-maintenance cost |
| Existing Code | None |

**Formula**: `(signal_emissions + queries) / successful_decisions`

---

### 3.4 Downward Causation Index

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 4/5 |
| Problem Solved | Confirms network influences agents (not just aggregation) |
| Autopoiesis Role | True emergence |
| Existing Code | None |

**Formula**: `agent_behavior_change_after_network_signal / baseline_behavior_change`

If > 1.0, network is actually influencing agents.

---

### 3.5 Norm Drift Rate

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 3/5 |
| Problem Solved | Detects implicit rule changes |
| Autopoiesis Role | Stability |
| Existing Code | None |

**Formula**: `delta(successful_action_patterns) / generation`

---

### 3.6 Trust Concentration Index

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Prevents prestige vampires |
| Autopoiesis Role | Social balance |
| Existing Code | Can derive from `prestige_engine.py` |

**Formula**: Gini coefficient of prestige distribution

---

## Tier 4: Advanced Emergence Metrics

These are harder to implement but provide deep insights.

### 4.1 Phase Transition Proximity

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 5/5 |
| Problem Solved | Predicts when small changes cause big effects |
| Autopoiesis Role | Bifurcation detection |
| Existing Code | None |

**Signals**:
- Increased variance in performance
- Longer recovery times from perturbations
- Correlation breakdown between previously-linked metrics

---

### 4.2 Critical Slowing Down (Pre-Collapse Signal)

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 5/5 |
| Problem Solved | Early warning of system failure |
| Autopoiesis Role | Survival |
| Existing Code | None |

**Signals**:
- Recovery time from errors increasing
- Autocorrelation increasing
- Variance spiking

---

### 4.3 Multi-Scale Correlation

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 5/5 |
| Problem Solved | Detects patterns at different time scales |
| Autopoiesis Role | Deep structure |
| Existing Code | None |

**Formula**: Compare metrics at 1-gen, 10-gen, 100-gen windows.

---

### 4.4 Spontaneous Coordination Rate

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 4/5 |
| Problem Solved | Measures self-organization ability |
| Autopoiesis Role | Distributed intelligence |
| Existing Code | None |

**Formula**: `coordination_without_explicit_signals / total_coordination_events`

---

## Tier 5: Long-Term Civilizational Metrics

For tracking multi-hundred generation health.

### 5.1 Youth Integration Success

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Are new agents contributing? |
| Autopoiesis Role | Generational renewal |
| Existing Code | Youth bonus in `evolutionary_engine.py` |

**Formula**: `young_agent_contribution / young_agent_resources_consumed`

---

### 5.2 Institutional Ossification Rate

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 4/5 |
| Problem Solved | Detects rigid patterns resistant to change |
| Autopoiesis Role | Flexibility |
| Existing Code | None |

**Signals**:
- Winning sequences unchanged for 50+ generations
- Role distribution constant despite game state changes
- Same agents dominating for 100+ generations

---

### 5.3 Idea Birth/Death Rate

| Attribute | Value |
|-----------|-------|
| Usefulness | 4/5 |
| Difficulty | 2/5 |
| Problem Solved | Innovation health |
| Autopoiesis Role | Creative vitality |
| Existing Code | Can derive from `winning_sequences.discovered_at` |

**Formula**: 
- Birth: new sequences discovered per generation
- Death: sequences marked inactive per generation
- Healthy ratio: 1.5-3.0 births per death

---

### 5.4 Prestige-Power Coupling

| Attribute | Value |
|-----------|-------|
| Usefulness | 5/5 |
| Difficulty | 3/5 |
| Problem Solved | Prevents prestige from becoming autocratic |
| Autopoiesis Role | Power balance |
| Existing Code | Can derive from comparing `prestige_engine.py` and `adaptive_action_limits.py` |

**Formula**: `correlation(prestige, action_budget)`

Should be < 0.3 (weak correlation, as designed).

---

## Human Spot-Check Dashboard

For your infrequent reviews of system progress toward goals.

### Primary Metrics (Check Weekly)

| Metric | Target | Where to Query |
|--------|--------|----------------|
| **Frontier Levels Beaten** | +1/week | `SELECT COUNT(DISTINCT game_id, level_number) FROM winning_sequences WHERE is_active=1` |
| **Full Game Wins** | Track count | `SELECT COUNT(*) FROM winning_sequences_full_game` |
| **Emergence Gain** | > 1.0 | See implementation above |
| **Identity Drift** | < 0.3 | See implementation above |
| **Sequence Success Rate** | > 0.7 | `SELECT AVG(times_validated > 0) FROM winning_sequences` |

### Red Flags (Immediate Attention)

| Signal | Threshold | Meaning |
|--------|-----------|---------|
| Zero new frontier levels | 10 generations | System stuck |
| Identity drift > 0.5 | - | Optimizing wrong things |
| Emergence gain < 0.5 | 5 generations | Network not smarter than individuals |
| Sequence success rate < 0.4 | - | Knowledge corrupted |
| Same agent top prestige | 50 generations | Vampire risk |

### Query for Comprehensive Check

```sql
-- Quick health snapshot for human review
SELECT 
    (SELECT COUNT(DISTINCT game_id || '-' || level_number) 
     FROM winning_sequences WHERE discovered_at > datetime('now', '-7 days')) as new_levels_week,
    (SELECT COUNT(*) FROM agents WHERE is_active = 1) as active_agents,
    (SELECT AVG(final_score) FROM agent_arc_performance 
     WHERE game_timestamp > datetime('now', '-24 hours')) as avg_score_24h,
    (SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1) as total_sequences,
    (SELECT MAX(generation) FROM agents) as current_generation;
```

---

## Implementation Roadmap

### Phase 1: Core Self-Regulation (Week 1-2)

| Priority | Metric | File to Modify | Effort |
|----------|--------|----------------|--------|
| 1 | Emergence Gain | `network_intelligence_engine.py` | 4 hours |
| 2 | Control Error | `regulatory_signal_engine.py` | 2 hours |
| 3 | Role Saturation Index | `agent_operating_mode_system.py` | 3 hours |
| 4 | Loop Detection | `core_gameplay.py` (already partial) | 2 hours |

### Phase 2: Performance Metrics (Week 3-4)

| Priority | Metric | File to Modify | Effort |
|----------|--------|----------------|--------|
| 5 | Compression Yield | `sequence_abstraction.py` | 4 hours |
| 6 | Strategy Abandonment Lag | `frustration_detector.py` | 3 hours |
| 7 | Information Velocity | `viral_package_engine.py` | 3 hours |
| 8 | Hub Fragility | `viral_package_engine.py` | 2 hours |

### Phase 3: Identity & Emergence (Week 5-6)

| Priority | Metric | File to Modify | Effort |
|----------|--------|----------------|--------|
| 9 | Functional Identity Drift | New: `autopoiesis_monitor.py` | 6 hours |
| 10 | Downward Causation Index | `regulatory_signal_engine.py` | 4 hours |
| 11 | Trust Concentration Index | `prestige_engine.py` | 2 hours |
| 12 | Prestige-Power Coupling | New: `balance_monitor.py` | 2 hours |

### Phase 4: Advanced Diagnostics (Week 7+)

| Priority | Metric | File to Modify | Effort |
|----------|--------|----------------|--------|
| 13 | Phase Transition Proximity | New: `phase_detector.py` | 8 hours |
| 14 | Critical Slowing Down | New: `phase_detector.py` | 4 hours |
| 15 | Multi-Scale Correlation | `performance_analyzer.py` | 6 hours |

---

## Metric Rotation System (Anti-Goodhart)

> "Metrics must be ephemeral, not institutionalized."

### Implementation

```python
class MetricRotator:
    """
    Rotates which metrics are used for selection/rewards.
    Prevents agents from gaming specific metrics.
    """
    
    def __init__(self, rotation_period: int = 10):
        """Rotate metrics every N generations."""
        self.rotation_period = rotation_period
        
        self.metric_pools = {
            'efficiency': ['mva', 'actions_per_level', 'completion_time'],
            'social': ['viral_spread', 'teaching_events', 'validation_rate'],
            'exploration': ['novel_solutions', 'game_diversity', 'frontier_attempts'],
            'reliability': ['success_rate', 'consistency', 'recovery_speed']
        }
    
    def get_active_metrics(self, generation: int) -> List[str]:
        """Return currently active metrics (subset of total)."""
        phase = generation // self.rotation_period
        
        # Each phase uses 2 random metrics from each pool
        active = []
        for pool_name, pool_metrics in self.metric_pools.items():
            random.seed(phase + hash(pool_name))
            active.extend(random.sample(pool_metrics, min(2, len(pool_metrics))))
        
        return active
```

### Observation vs Optimization Separation

| Purpose | Metrics Used | Visibility |
|---------|--------------|------------|
| **Optimization** (rewards) | Rotating subset | Lagged 3 generations |
| **Observation** (health) | All metrics | Real-time |
| **Selection** (survival) | Performance + social blend | Current |

---

## Critical Design Constraints (Feedback Integration)

These constraints address fundamental cybernetic risks identified in the design.

### Constraint 1: Trigger Coupling & Feedback Resonance

**The Problem**: Single-metric triggers can create feedback loops.

```
Example cascade:
Emergence drops → transmission increases
Transmission increases → noise increases  
Noise increases → success rate drops
Success rate drops → Emergence drops further
→ RUNAWAY OSCILLATION
```

**Mitigations (Thermostat, Not Emergency Brake)**:

| Strategy | Implementation |
|----------|----------------|
| **Cooldowns** | Minimum 3 generations between same trigger firing |
| **Multi-metric corroboration** | Require 2+ metrics to agree before parameter shift |
| **Small nudges** | Max 10% parameter change per generation |
| **Damping factor** | Each consecutive trigger reduces magnitude by 50% |

```python
class TriggerController:
    """Prevents feedback resonance in metric-driven adjustments."""
    
    def __init__(self):
        self.last_fired: Dict[str, int] = {}  # trigger_name → generation
        self.consecutive_fires: Dict[str, int] = {}
        self.COOLDOWN_GENERATIONS = 3
        self.DAMPING_FACTOR = 0.5
        self.MAX_ADJUSTMENT = 0.10  # 10% max change
    
    def can_fire(self, trigger_name: str, generation: int) -> bool:
        """Check if trigger is allowed to fire (cooldown respected)."""
        last = self.last_fired.get(trigger_name, -999)
        return (generation - last) >= self.COOLDOWN_GENERATIONS
    
    def get_adjustment_magnitude(self, trigger_name: str, base_magnitude: float) -> float:
        """Apply damping for consecutive fires."""
        consecutive = self.consecutive_fires.get(trigger_name, 0)
        damped = base_magnitude * (self.DAMPING_FACTOR ** consecutive)
        return min(damped, self.MAX_ADJUSTMENT)
    
    def require_corroboration(self, primary_metric: float, 
                               secondary_metrics: List[float],
                               threshold: float = 0.5) -> bool:
        """Require multiple metrics to agree before major adjustment."""
        agreeing = sum(1 for m in secondary_metrics if m > threshold)
        return agreeing >= len(secondary_metrics) // 2
```

---

### Constraint 2: Stationarity Assumption

**The Problem**: Metrics assume comparable generations and stable environments.

**Reality**: The system evolves its own problem distribution:
- Early generations: Many frontier games
- Later generations: Mostly optimization
- Far future: Unknown task distribution

**Mitigations**:

| Strategy | Implementation |
|----------|----------------|
| **Rolling windows** | Already using 7-day windows |
| **Half-lives** | Metrics decay over time |
| **Relative comparisons** | Compare to recent baseline, not absolute targets |
| **Regime detection** | Detect when environment has fundamentally changed |

```python
def detect_regime_change(generation: int, window: int = 20) -> bool:
    """
    Detect if the system has entered a new regime where old metrics don't apply.
    
    Signals:
    - Task distribution shift (frontier → optimization)
    - Variance spike without performance change
    - Correlation breakdown between previously-linked metrics
    """
    # Get metric correlations for recent vs historical
    recent_corr = get_metric_correlations(generation - window, generation)
    historical_corr = get_metric_correlations(generation - 2*window, generation - window)
    
    # If correlations have changed significantly, regime has shifted
    correlation_delta = abs(recent_corr - historical_corr)
    
    if correlation_delta > 0.3:  # Significant shift
        return True
    
    # Check task distribution shift
    recent_frontier_ratio = get_frontier_game_ratio(generation - window, generation)
    historical_frontier_ratio = get_frontier_game_ratio(generation - 2*window, generation - window)
    
    if abs(recent_frontier_ratio - historical_frontier_ratio) > 0.2:
        return True
    
    return False
```

**When Regime Change Detected**:
1. Reset baseline metrics to current values
2. Increase metric uncertainty for 10 generations
3. Reduce trigger sensitivity by 50%
4. Log for human review

---

### Constraint 3: Human Spot-Checks as Boundary Condition

**Honest Assessment**: The Human Spot-Check Dashboard is currently serving as:

| Implicit Role | What It's Really Doing |
|---------------|------------------------|
| Value oracle | Defining what "success" means |
| Sanity check | Catching systematic errors |
| Identity anchor | Preventing goal drift |

**This is a feature, not a bug.**

> "Autopoiesis is bounded by the observer until values are irreversibly stable."

**The Closure Gradient**:

```
CURRENT STATE:
  Human ──────────────────────→ System
  (defines goals, spots errors)

INTERMEDIATE STATE:
  Human ──────→ System
  (rare spot-checks, emergency only)

THEORETICAL END STATE:
  Human ─┐
         └→ System (self-sustaining)
  (values embedded, no external input needed)
```

**We are at the CURRENT STATE.** Accept this dependency explicitly.

**What Must Remain Human-Visible**:
1. Frontier progress (the actual goal)
2. Identity drift (are we optimizing the right thing?)
3. Emergence gain (is collective intelligence working?)

**What Can Be Fully Automated**:
1. Role distribution
2. Resource allocation
3. Sequence pruning
4. Parameter tuning

---

### Constraint 4: Second-Order Goodhart Risk

**The Problem**: Even with metric rotation, agents can learn:
- Which *classes* of metrics matter
- When rotations tend to happen
- Which behaviors are always "safe"

This is **meta-gaming the rotation itself**.

**Mitigations (Biological Analogs)**:

| Strategy | Biological Analog | Implementation |
|----------|-------------------|----------------|
| **Skip rotations** | Environmental stability periods | 20% chance of no rotation |
| **One-time metrics** | Novel selection pressures | Introduce metrics that are never reused |
| **Deliberate inconsistency** | Random disasters | Occasional random evaluation |
| **Noise injection** | Mutation spikes | Add noise to metric calculations |

```python
class AntiGoodhartRotator(MetricRotator):
    """Extended rotator with second-order Goodhart protection."""
    
    def __init__(self, rotation_period: int = 10):
        super().__init__(rotation_period)
        self.one_time_metrics_used: Set[str] = set()
        self.SKIP_ROTATION_PROBABILITY = 0.20
        self.ONE_TIME_METRIC_PROBABILITY = 0.05
        self.NOISE_INJECTION_RANGE = 0.1
    
    def get_active_metrics(self, generation: int) -> List[str]:
        """Return currently active metrics with anti-Goodhart protections."""
        
        # 20% chance: Skip rotation entirely (use previous metrics)
        if random.random() < self.SKIP_ROTATION_PROBABILITY:
            return self._get_previous_metrics(generation)
        
        # Get base rotation
        metrics = super().get_active_metrics(generation)
        
        # 5% chance: Inject a one-time metric that will never be reused
        if random.random() < self.ONE_TIME_METRIC_PROBABILITY:
            one_time = self._generate_one_time_metric(generation)
            if one_time not in self.one_time_metrics_used:
                metrics.append(one_time)
                self.one_time_metrics_used.add(one_time)
        
        return metrics
    
    def apply_noise(self, metric_value: float) -> float:
        """Add noise to metric to prevent exact gaming."""
        noise = random.uniform(-self.NOISE_INJECTION_RANGE, self.NOISE_INJECTION_RANGE)
        return metric_value * (1 + noise)
    
    def _generate_one_time_metric(self, generation: int) -> str:
        """Generate a novel metric that will only be used once."""
        novel_metrics = [
            f"action_diversity_level_{random.randint(1,20)}",
            f"score_at_action_{random.randint(50,200)}",
            f"recovery_from_score_{random.randint(1,5)}",
            f"exploration_after_gen_{generation - random.randint(5,20)}"
        ]
        return random.choice(novel_metrics)
```

---

### Constraint 5: Metric Confidence Meta-Metric (NEW - Critical Addition)

**The Problem**: How do we know if a metric itself is trustworthy?

**Solution**: Track confidence in metrics, not just agents.

**Metric Confidence Signals**:

| Signal | Meaning | Action |
|--------|---------|--------|
| High contradiction rate | Metric disagrees with others | Lower its weight |
| Fast agent adaptation | Agents gaming this metric | Increase decay rate |
| Low predictive power | Doesn't predict long-term success | Consider removal |
| Too stable | May be measuring noise | Investigate |
| Too influential | Single-point-of-failure | Distribute weight |

```python
class MetricConfidenceTracker:
    """
    Track confidence in metrics themselves.
    Closes the final Goodhart loop.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.CONTRADICTION_THRESHOLD = 0.3
        self.ADAPTATION_SPEED_THRESHOLD = 5  # generations
        self.PREDICTIVE_POWER_THRESHOLD = 0.2
    
    def calculate_metric_confidence(self, metric_name: str, 
                                     generation: int) -> float:
        """
        Calculate confidence in a metric (0.0 = untrustworthy, 1.0 = highly reliable).
        
        When a metric becomes:
        - Too predictive
        - Too stable  
        - Too influential
        ...it should decay faster.
        """
        # Factor 1: Contradiction rate (does it agree with other metrics?)
        contradiction_score = self._calculate_contradiction_rate(metric_name, generation)
        
        # Factor 2: Agent adaptation speed (are agents gaming it?)
        adaptation_speed = self._calculate_adaptation_speed(metric_name, generation)
        
        # Factor 3: Predictive power (does it predict actual success?)
        predictive_power = self._calculate_predictive_power(metric_name, generation)
        
        # Factor 4: Influence concentration (is it too dominant?)
        influence_score = self._calculate_influence_concentration(metric_name, generation)
        
        # Combine into confidence score
        confidence = (
            (1.0 - contradiction_score) * 0.25 +  # Low contradiction = good
            (1.0 - adaptation_speed) * 0.25 +     # Slow adaptation = good
            predictive_power * 0.30 +              # High predictive = good
            (1.0 - influence_score) * 0.20         # Low influence = good
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_contradiction_rate(self, metric_name: str, generation: int) -> float:
        """How often does this metric disagree with the majority of other metrics?"""
        # Get this metric's ranking of agents
        this_ranking = self._get_agent_ranking(metric_name, generation)
        
        # Get rankings from all other metrics
        other_rankings = self._get_all_other_rankings(metric_name, generation)
        
        # Calculate average Kendall tau correlation
        correlations = [self._kendall_tau(this_ranking, other) for other in other_rankings]
        avg_correlation = sum(correlations) / len(correlations) if correlations else 0.5
        
        # High correlation = low contradiction
        return 1.0 - avg_correlation
    
    def _calculate_adaptation_speed(self, metric_name: str, generation: int) -> float:
        """How fast are agents improving on this specific metric?"""
        # Get metric values over last 10 generations
        history = self._get_metric_history(metric_name, generation - 10, generation)
        
        if len(history) < 5:
            return 0.5  # Neutral
        
        # Calculate improvement rate
        improvement_rate = (history[-1] - history[0]) / len(history)
        
        # Fast improvement suggests gaming
        # Normalize to 0-1 range (>20% per gen = very fast)
        return min(1.0, improvement_rate / 0.20)
    
    def _calculate_predictive_power(self, metric_name: str, generation: int) -> float:
        """Does high performance on this metric predict actual frontier success?"""
        # Get agents ranked high on this metric 10 generations ago
        past_top_agents = self._get_top_agents_for_metric(metric_name, generation - 10)
        
        # Check their actual frontier success since then
        frontier_successes = [
            self._count_frontier_wins(agent, generation - 10, generation)
            for agent in past_top_agents
        ]
        
        # Compare to random baseline
        random_baseline = self._get_random_baseline_success(generation - 10, generation)
        
        if random_baseline == 0:
            return 0.5
        
        avg_success = sum(frontier_successes) / len(frontier_successes) if frontier_successes else 0
        return min(1.0, avg_success / max(random_baseline, 0.01))
    
    def _calculate_influence_concentration(self, metric_name: str, generation: int) -> float:
        """Is this metric too dominant in selection decisions?"""
        # Get weight of this metric in recent selection events
        selection_weights = self._get_selection_weight_history(metric_name, generation)
        
        if not selection_weights:
            return 0.0
        
        avg_weight = sum(selection_weights) / len(selection_weights)
        
        # More than 40% weight = too influential
        return min(1.0, avg_weight / 0.40)
    
    def get_decay_multiplier(self, metric_name: str, generation: int) -> float:
        """
        Metrics with low confidence should decay faster.
        Returns multiplier for the metric's decay rate.
        """
        confidence = self.calculate_metric_confidence(metric_name, generation)
        
        # Low confidence (0.3) → 2x decay rate
        # High confidence (0.9) → 0.5x decay rate (slower decay)
        return 2.0 - (confidence * 1.5)
```

**Integration with Metric Rotation**:

```python
def apply_confidence_weighted_rotation(generation: int):
    """Use metric confidence to influence rotation and weighting."""
    confidence_tracker = MetricConfidenceTracker(db)
    
    for metric_name in get_all_metrics():
        confidence = confidence_tracker.calculate_metric_confidence(metric_name, generation)
        decay_multiplier = confidence_tracker.get_decay_multiplier(metric_name, generation)
        
        # Apply accelerated decay to low-confidence metrics
        current_weight = get_metric_weight(metric_name)
        new_weight = current_weight * (0.95 ** decay_multiplier)  # Base 5% decay * multiplier
        
        set_metric_weight(metric_name, new_weight)
        
        # Log for observability
        if confidence < 0.4:
            log_warning(f"Metric {metric_name} has low confidence ({confidence:.2f}), "
                       f"applying {decay_multiplier:.1f}x decay")
```

---

## Summary: Top 10 Metrics for Autopoiesis

| Rank | Metric | Type | Why Critical |
|------|--------|------|--------------|
| 1 | **Emergence Gain** | Identity | Proves network intelligence exists |
| 2 | **Functional Identity Drift** | Identity | Prevents goal corruption |
| 3 | **Sequence Success Rate** | Performance | Knowledge quality |
| 4 | **Role Saturation Index** | Self-organization | Population balance |
| 5 | **Information Velocity** | Metabolism | Knowledge flow health |
| 6 | **Control Error** | Feedback | Regulation accuracy |
| 7 | **Loop Detection** | Stuck prevention | Oscillation escape |
| 8 | **Hub Fragility** | Resilience | Single-point-of-failure |
| 9 | **Compression Yield** | Abstraction | Generalization quality |
| 10 | **Trust Concentration (Gini)** | Social balance | Vampire prevention |
| **NEW** | **Metric Confidence** | Meta-metric | Closes final Goodhart loop |

---

## Appendix: Metrics NOT Recommended

These metrics from the Societal Metrics List are lower priority for the current system:

| Metric | Reason to Deprioritize |
|--------|------------------------|
| Unemployment analogs | Agents always have games assigned |
| Inflation/deflation | Prestige already has decay mechanisms |
| Message volume per agent | No inter-agent messaging |
| Echo chamber formation | No communication channels to form echoes |
| Cultural Carrying Capacity | Too abstract for current scale |

---

**Document Status**: Ready for implementation  
**Next Action**: Implement Tier 1 metrics (Emergence Gain, Control Error, Role Saturation)  
**Review Frequency**: Update after each major metric implementation
