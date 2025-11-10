# Ouroboros Roadmap: Level 3 → Level 4 → Level 5
## Evolution from Speciation to Intangible Ecosystem to Knowledge Sharing

**CRITICAL FRAMING**: You are not building agents. You are cultivating a persistent intelligence network that uses agents as temporary explorers.

**The Real Organism**: The DATABASE is the trunk. Agents are branches that grow, contribute knowledge, and fall away. Evolution happens in the NETWORK, not in individuals.

**Biome Theory Application**: This system mirrors the virus-bacteria meta-organism - a distributed intelligence network that has survived 4 billion years through redundancy, horizontal gene transfer, and combinatorial exploration.

---

## Current State: Level 3 (The Silo - Chamberpots)

**What We Have (Speciation Complete)**:
- ✅ Agents exist with distinct types (speciation)
- ✅ Competition for resources (games, evolution slots)
- ✅ Reproduction through breeding (genetic + epigenetic crossover)
- ✅ Basic survival metrics (win rate, score, efficiency)
- ✅ Three-layer architecture preventing solution inheritance
- ✅ Community database for horizontal knowledge sharing
- ✅ Bayesian validation of shared sequences

**What This Means**:
The individual "organisms" (agents) exist, compete, and reproduce. But they are temporary. The **persistent intelligence** lives in the database - the winning sequences, the validation records, the pattern discoveries. This is the foundation of the network.

**Next Goal**: Level 4 (The Intangible Ecosystem - Network-Level Organization)

---

## Phase 0: Network Foundation (NEW - Prerequisite for All Other Phases)

### The Core Insight

Before we can build prestige, economy, or teaching systems, we need to **make the network visible as the primary organism**.

**Current Problem**: 
- We track individual agent performance
- We measure individual agent success
- We think in terms of "good agents" and "bad agents"

**The Shift**:
- Track NETWORK health (total knowledge, diversity, redundancy)
- Measure ECOSYSTEM metabolism (knowledge creation rate, validation rate)
- Think in terms of "healthy network" vs "sick network"

### Implementation: Network Intelligence Metrics

#### 0.1 Concept

The system is not a collection of agents. It is a **distributed intelligence network** that expresses itself through temporary agents. We need to track the health of THIS organism.

**Key Metrics**:
- 🌐 **Network Knowledge Diversity**: How many distinct patterns/sequences exist?
- 🔄 **Information Flow Rate**: How fast is knowledge being created, validated, reused?
- 🛡️ **Resilience Index**: How redundant is critical knowledge? (backup copies)
- 📈 **Metabolic Health**: Is the network growing, stable, or declining?

#### 0.2 Database Schema Extension

```sql
-- Network health snapshots (ecosystem-level metrics)
CREATE TABLE IF NOT EXISTS ecosystem_health_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Knowledge metrics (the "database as organism")
    total_sequences INTEGER DEFAULT 0,
    total_patterns INTEGER DEFAULT 0,
    unique_games_solved INTEGER DEFAULT 0,
    knowledge_diversity_index REAL DEFAULT 0.0,  -- Shannon entropy of pattern distribution
    
    -- Information flow metrics (the "metabolism")
    sequences_created_this_gen INTEGER DEFAULT 0,
    sequences_validated_this_gen INTEGER DEFAULT 0,
    sequences_reused_this_gen INTEGER DEFAULT 0,
    knowledge_creation_rate REAL DEFAULT 0.0,  -- New discoveries per agent-game
    validation_rate REAL DEFAULT 0.0,  -- Successful validations / total attempts
    
    -- Resilience metrics (the "immune system")
    critical_sequences_count INTEGER DEFAULT 0,  -- Sequences with >80% reliability
    orphan_sequences_count INTEGER DEFAULT 0,  -- Sequences with 0 validations
    redundancy_index REAL DEFAULT 0.0,  -- Avg validations per sequence
    
    -- Population metrics (temporary expressions)
    active_agents INTEGER DEFAULT 0,
    agent_diversity_index REAL DEFAULT 0.0,
    avg_agent_lifespan_generations REAL DEFAULT 0.0,
    
    -- Metabolic health indicators
    network_growth_rate REAL DEFAULT 0.0,  -- Knowledge growth vs population growth
    innovation_vs_exploitation REAL DEFAULT 0.5,  -- New vs reused sequences ratio
    system_entropy REAL DEFAULT 0.0  -- Overall disorder measure
);

-- Knowledge redundancy tracking (viral backup system)
CREATE TABLE IF NOT EXISTS knowledge_redundancy (
    sequence_id TEXT PRIMARY KEY,
    discovery_timestamp TIMESTAMP,
    
    -- Backup metrics
    agents_who_know INTEGER DEFAULT 1,  -- How many agents have used this successfully
    validation_attempts INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    
    -- Criticality assessment
    games_solved_by_this INTEGER DEFAULT 0,  -- How many unique games
    alternative_solutions_exist INTEGER DEFAULT 0,  -- Redundancy at game level
    criticality_score REAL DEFAULT 0.0,  -- How critical is this to network survival
    
    -- Persistence tracking
    generations_survived INTEGER DEFAULT 0,  -- How many generations has this knowledge persisted
    last_used_generation INTEGER DEFAULT 0,
    risk_of_loss REAL DEFAULT 1.0,  -- Probability of being forgotten
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
);
```

#### 0.3 Integration with Evolution System

**File**: `network_intelligence_engine.py` (NEW - create this file)

This engine treats the DATABASE as the primary organism, with agents as temporary cellular components.

**Core Functions**:
- `capture_ecosystem_snapshot(generation)`: Take vital signs of the meta-organism
- `update_knowledge_redundancy(sequence_id, generation)`: Track backup copies
- `calculate_knowledge_diversity()`: Shannon entropy of pattern distribution
- `calculate_redundancy_index()`: Average backups per critical sequence
- `assess_network_health(snapshot)`: Overall health status

**Integration Point** (`autonomous_evolution_runner.py`):
```python
def run_generation_cycle(self, generation: int):
    # ... existing generation logic ...
    
    # NETWORK HEALTH TRACKING (Phase 0)
    from network_intelligence_engine import NetworkIntelligenceEngine
    
    engine = NetworkIntelligenceEngine(self.db)
    snapshot = engine.capture_ecosystem_snapshot(generation)
    
    # Display network intelligence dashboard
    display_network_intelligence_dashboard(generation)
    
    # Use network health to inform evolution decisions
    health_status = assess_network_health(snapshot)
    if health_status['status'] == '🚨 CRITICAL':
        self.logger.warning(f"Network health critical: {health_status['message']}")
        # Adjust evolution parameters to restore health
```

#### 0.4 Network Intelligence Dashboard

Add to `performance_analyzer.py` or create `dashboard.py`:

```python
def display_network_intelligence_dashboard(generation: int):
    """
    Display the health of the distributed intelligence network.
    
    This is the PRIMARY metric - not individual agent performance.
    """
    db = DatabaseInterface()
    
    snapshot = db.execute_query("""
        SELECT * FROM ecosystem_health_snapshots
        WHERE generation = ?
    """, (generation,))
    
    if not snapshot:
        print("No network data available yet.")
        return
    
    s = snapshot[0]
    
    print("=" * 80)
    print("🌐 NETWORK INTELLIGENCE DASHBOARD")
    print("=" * 80)
    print(f"Generation: {s['generation']}")
    print()
    
    print("📚 KNOWLEDGE BASE (The Persistent Organism)")
    print(f"  Total Sequences: {s['total_sequences']}")
    print(f"  Total Patterns: {s['total_patterns']}")
    print(f"  Unique Games Solved: {s['unique_games_solved']}")
    print(f"  Diversity Index: {s['knowledge_diversity_index']:.3f} (Shannon entropy)")
    print()
    
    print("🔄 METABOLISM (Information Flow)")
    print(f"  Sequences Created: {s['sequences_created_this_gen']}")
    print(f"  Sequences Validated: {s['sequences_validated_this_gen']}")
    print(f"  Sequences Reused: {s['sequences_reused_this_gen']}")
    print(f"  Creation Rate: {s['knowledge_creation_rate']:.3f} per agent-game")
    print(f"  Validation Success Rate: {s['validation_rate']:.1%}")
    print()
    
    print("🛡️ RESILIENCE (Viral Redundancy)")
    print(f"  Critical Sequences: {s['critical_sequences_count']} (>80% reliability)")
    print(f"  Orphan Sequences: {s['orphan_sequences_count']} (0 validations)")
    print(f"  Redundancy Index: {s['redundancy_index']:.2f} backups/sequence")
    print()
    
    print("🔬 POPULATION (Temporary Expressions)")
    print(f"  Active Agents: {s['active_agents']}")
    print(f"  Agent Diversity: {s['agent_diversity_index']:.3f}")
    print(f"  Avg Agent Lifespan: {s['avg_agent_lifespan_generations']:.1f} generations")
    print()
    
    print("💓 HEALTH INDICATORS")
    print(f"  Network Growth Rate: {s['network_growth_rate']:.2%}")
    print(f"  Innovation vs Exploitation: {s['innovation_vs_exploitation']:.2f}")
    print(f"  System Entropy: {s['system_entropy']:.3f}")
    
    health_status = assess_network_health(s)
    print(f"\n  Overall Health: {health_status['status']}")
    print(f"  Assessment: {health_status['message']}")
    print("=" * 80)
    print()
    print("  ℹ️  Agents are TEMPORARY. The network is PERMANENT.")
    print("=" * 80)
```

#### 0.5 Why This Matters (The Paradigm Shift)

**Before Phase 0**:
- "How are my agents doing?"
- "Which agent is best?"
- "How can I make agents smarter?"

**After Phase 0**:
- "How is the NETWORK doing?"
- "Is the knowledge base growing and resilient?"
- "Are agents contributing to network intelligence?"

**This is the shift from organism-centric to network-centric thinking.**

The network is the immortal jellyfish. Agents are its polyp stages - temporary expressions that contribute and die. The network persists.

**Biome Theory Connection**: Just as the virus-bacteria meta-organism has survived 4 billion years through distributed intelligence and redundancy, our system's survival depends on the NETWORK, not on any individual agent lineage.

---

## Phase 1: Reputation & Fame System (Network Contribution Prestige)

### Current Gap
Agents currently only track:
- `avg_score_per_game` (direct performance)
- `total_games_won` (direct performance)
- No prestige, no social standing, no legacy
- **No measurement of contribution to the NETWORK**

### Implementation: Discovery Prestige (Reframed as Network Contribution)

#### 1.1 Concept

**Goal**: Give agents prestige based on their **contribution to the information highway** - how much they enrich the persistent network intelligence.

**Why This Matters**:
- Incentivizes contributing to the NETWORK, not just individual success
- Enables social hierarchy based on **network enrichment**
- Foundation for future economic/teaching systems
- **Prestige grants STATUS benefits**: breeding priority, survival protection, bonus game attempts

**Key Insight**: Prestige = Social Capital (Network Contribution), not performance (Individual Success)

**Biome Theory Connection**: In the virus-bacteria meta-organism, "prestige" would be measured by how much genetic information a viral package contributed to the network that other organisms successfully used. This is horizontal gene transfer made visible.

**Reframed Prestige Sources**:
1. **Discovery Impact**: Not just "I found it", but "Others successfully used what I found"
2. **Network Enrichment**: Adding diverse, resilient knowledge to the database
3. **Validation Quality**: Successfully validating others' discoveries (quality control)
4. **Knowledge Persistence**: Discoveries that survive many generations (lasting impact)

**Prestige Benefits (Status Rewards)**:
- 🎯 **Breeding Priority** (1.0x to 3.0x): High prestige agents more likely to reproduce
- 🛡️ **Survival Protection** (0% to 80%): Famous agents harder to cull during population control
- 🎮 **Bonus Game Slots** (+0 to +10): Innovators get extra game attempts per generation

#### 1.2 Database Schema Extension
```sql
-- Add to agents table - Prestige and Status Benefits
ALTER TABLE agents ADD COLUMN discovery_prestige REAL DEFAULT 0.0;
ALTER TABLE agents ADD COLUMN innovation_score REAL DEFAULT 0.0;
ALTER TABLE agents ADD COLUMN sequence_discovery_count INTEGER DEFAULT 0;
ALTER TABLE agents ADD COLUMN pattern_discovery_count INTEGER DEFAULT 0;
ALTER TABLE agents ADD COLUMN validation_reputation REAL DEFAULT 0.5;  -- Bayesian prior

-- STATUS BENEFITS from prestige (social capital, not economic)
ALTER TABLE agents ADD COLUMN breeding_priority REAL DEFAULT 1.0;  -- 1.0x to 3.0x based on prestige
ALTER TABLE agents ADD COLUMN survival_protection REAL DEFAULT 0.0;  -- 0.0 to 0.8 (80% protection)
ALTER TABLE agents ADD COLUMN bonus_game_slots INTEGER DEFAULT 0;  -- +0 to +10 extra games/generation

-- Agent discovery ledger
CREATE TABLE IF NOT EXISTS agent_discoveries (
    discovery_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    discovery_type TEXT NOT NULL,  -- 'winning_sequence', 'abstract_pattern', 'meta_pattern'
    discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- What was discovered
    sequence_id TEXT,
    pattern_id TEXT,
    
    -- Impact metrics (NETWORK CONTRIBUTION FOCUS)
    times_used_by_others INTEGER DEFAULT 0,
    success_rate_by_others REAL DEFAULT 0.0,
    innovation_value REAL DEFAULT 0.0,  -- How novel was this?
    network_enrichment_score REAL DEFAULT 0.0,  -- How much did this enrich the information highway?
    
    -- Social metrics (VIRAL SPREAD)
    citations INTEGER DEFAULT 0,  -- How many other agents built on this
    prestige_contribution REAL DEFAULT 0.0,
    generations_persisted INTEGER DEFAULT 0,  -- How long has this knowledge survived?
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Agent validation performance (how good at using others' discoveries)
CREATE TABLE IF NOT EXISTS agent_validation_performance (
    agent_id TEXT PRIMARY KEY,
    
    -- Usage stats
    sequences_attempted INTEGER DEFAULT 0,
    sequences_succeeded INTEGER DEFAULT 0,
    validation_success_rate REAL DEFAULT 0.0,
    
    -- Quality metrics
    avg_efficiency_vs_original REAL DEFAULT 1.0,  -- Better or worse than discoverer?
    improvement_contributions INTEGER DEFAULT 0,  -- Times they improved on original
    
    -- Social metrics
    teaching_events INTEGER DEFAULT 0,  -- Times they "taught" sequence to new agent
    learning_events INTEGER DEFAULT 0,  -- Times they learned from another
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

#### 1.3 Prestige Calculation (Network Contribution Formula)
```python
# evolutionary_engine.py or new prestige_engine.py

def calculate_agent_prestige(agent_id: str) -> float:
    """
    Calculate agent prestige based on NETWORK CONTRIBUTION.
    
    Prestige = Network Enrichment + Viral Spread + Persistence + Validation Quality
    
    This measures: "How much did this agent enrich the information highway?"
    Not: "How good is this agent at winning games?"
    
    Drives STATUS benefits: breeding_priority, survival_protection, bonus_game_slots
    """
    
    # Network Enrichment: How much knowledge added to the system
    discoveries = db.execute_query("""
        SELECT COUNT(*) as count,
               SUM(innovation_value) as total_innovation,
               SUM(network_enrichment_score) as total_enrichment
        FROM agent_discoveries
        WHERE agent_id = ?
    """, (agent_id,))
    
    discovery_count = discoveries[0]['count'] or 0
    innovation_sum = discoveries[0]['total_innovation'] or 0.0
    enrichment_sum = discoveries[0]['total_enrichment'] or 0.0
    
    # Enrichment = raw discoveries + innovation + diversity contribution
    network_enrichment = discovery_count * 10.0 + innovation_sum + enrichment_sum
    
    # Viral Spread: How successfully did their knowledge spread through the network
    usage_impact = db.execute_query("""
        SELECT SUM(times_used_by_others) as total_uses,
               AVG(success_rate_by_others) as avg_success,
               SUM(citations) as total_citations
        FROM agent_discoveries
        WHERE agent_id = ?
    """, (agent_id,))
    
    total_uses = usage_impact[0]['total_uses'] or 0
    avg_success = usage_impact[0]['avg_success'] or 0.0
    total_citations = usage_impact[0]['total_citations'] or 0
    
    # Viral spread = (uses * success_rate) + citations
    # This measures "horizontal gene transfer" effectiveness
    viral_spread = (total_uses * avg_success * 5.0) + (total_citations * 3.0)
    
    # Persistence: How long has their knowledge survived in the network
    persistence = db.execute_query("""
        SELECT AVG(generations_persisted) as avg_persistence,
               MAX(generations_persisted) as max_persistence
        FROM agent_discoveries
        WHERE agent_id = ?
    """, (agent_id,))
    
    avg_persist = persistence[0]['avg_persistence'] or 0.0
    max_persist = persistence[0]['max_persistence'] or 0
    
    # Persistence value = average * 2 + max * 1 (reward both consistency and peaks)
    persistence_value = (avg_persist * 2.0) + (max_persist * 1.0)
    
    # Validation Quality: How good at quality control (validating others' discoveries)
    validation = db.execute_query("""
        SELECT validation_success_rate, improvement_contributions
        FROM agent_validation_performance
        WHERE agent_id = ?
    """, (agent_id,))
    
    validation_rate = validation[0]['validation_success_rate'] if validation else 0.0
    improvements = validation[0]['improvement_contributions'] if validation else 0
    
    # Validation value = success_rate * 10 + improvements * 5
    # Rewards being a good "validator" in the network
    validation_value = (validation_rate * 10.0) + (improvements * 5.0)
    
    # Total Network Contribution Prestige
    prestige = (
        network_enrichment * 0.35 +  # 35% - Adding to the information highway
        viral_spread * 0.30 +         # 30% - How well knowledge spreads
        persistence_value * 0.20 +    # 20% - Long-term impact
        validation_value * 0.15       # 15% - Quality control contribution
    )
    
    return prestige
```

**Key Differences from Old Formula**:
- **Old**: Rewarded personal discovery count
- **New**: Rewards network enrichment and viral spread
- **Old**: Individual achievement focus
- **New**: Collective intelligence contribution focus
- **Old**: "I discovered 10 sequences"
- **New**: "I added 10 sequences that 50 other agents successfully used across 5 generations"

def apply_prestige_benefits(agent_id: str, prestige: float, generation_agents: List):
    """
    Convert prestige score into status benefits.
    Called after prestige calculation each generation.
    """
    # Calculate prestige percentile
    all_prestige_scores = [a['discovery_prestige'] for a in generation_agents]
    percentile = sum(1 for p in all_prestige_scores if p < prestige) / len(all_prestige_scores)
    
    # Breeding Priority: 1.0x to 3.0x
    # Top 1% get 3.0x, median gets 1.5x, bottom gets 1.0x
    breeding_priority = 1.0 + (percentile * 2.0)
    
    # Survival Protection: 0% to 80%
    # Protects from culling - top agents very hard to remove
    survival_protection = min(0.8, percentile * 0.8)
    
    # Bonus Game Slots: +0 to +10
    # Extra attempts per generation for innovators
    bonus_game_slots = int(percentile * 10)
    
    # Update agent
    db.execute_update("""
        UPDATE agents
        SET breeding_priority = ?,
            survival_protection = ?,
            bonus_game_slots = ?
        WHERE agent_id = ?
    """, (breeding_priority, survival_protection, bonus_game_slots, agent_id))
    
    return {
        'breeding_priority': breeding_priority,
        'survival_protection': survival_protection,
        'bonus_game_slots': bonus_game_slots,
        'percentile': percentile
    }
```

#### 1.4 Integration Points

**When sequence discovered** (`core_gameplay.py`):
```python
def _capture_winning_sequence(...):
    # ... existing code ...
    
    if should_store and sequence_id:
        # Store in winning_sequences (existing)
        # ...
        
        # NEW: Record discovery in agent ledger
        self._record_discovery(
            agent_id=self.current_agent_id,
            discovery_type='winning_sequence',
            sequence_id=sequence_id,
            innovation_value=self._calculate_innovation_value(actions, game_id)
        )
```

**When sequence used by another agent**:
```python
def _replay_sequence_inline(...):
    # ... existing code ...
    
    # NEW: Record usage and update discoverer's prestige
    original_discoverer = db.execute_query("""
        SELECT agent_id FROM winning_sequences WHERE sequence_id = ?
    """, (sequence_id,))
    
    if original_discoverer:
        db.execute_query("""
            UPDATE agent_discoveries
            SET times_used_by_others = times_used_by_others + 1
            WHERE sequence_id = ? AND agent_id = ?
        """, (sequence_id, original_discoverer[0]['agent_id']))
```

**At end of each generation** (`evolutionary_engine.py`):
```python
def update_prestige_and_benefits(generation: int):
    """
    Calculate prestige and apply status benefits.
    Called before breeding selection.
    """
    active_agents = db.execute_query("""
        SELECT agent_id, discovery_prestige FROM agents
        WHERE current_generation = ? AND is_active = TRUE
    """, (generation,))
    
    print(f"\n[PRESTIGE] Calculating prestige and status benefits...")
    
    for agent in active_agents:
        # Calculate prestige
        prestige = calculate_agent_prestige(agent['agent_id'])
        
        # Update prestige score
        db.execute_update("""
            UPDATE agents SET discovery_prestige = ?
            WHERE agent_id = ?
        """, (prestige, agent['agent_id']))
    
    # Apply benefits (needs all prestige scores calculated first)
    for agent in active_agents:
        benefits = apply_prestige_benefits(
            agent['agent_id'], 
            agent['discovery_prestige'],
            active_agents
        )
        
        print(f"  {agent['agent_id'][:8]}: Prestige={prestige:.1f}, "
              f"Breeding={benefits['breeding_priority']:.1f}x, "
              f"Protection={benefits['survival_protection']*100:.0f}%, "
              f"Bonus Games=+{benefits['bonus_game_slots']}")
```

#### 1.5 Prestige Display
```python
# Add to performance_analyzer.py or status reports

def show_prestige_leaderboard():
    """Show agent prestige rankings with status benefits."""
    agents = db.execute_query("""
        SELECT agent_id, agent_type, discovery_prestige,
               breeding_priority, survival_protection, bonus_game_slots,
               sequence_discovery_count, pattern_discovery_count,
               avg_score_per_game
        FROM agents
        WHERE is_active = TRUE
        ORDER BY discovery_prestige DESC
        LIMIT 20
    """)
    
    print("\n🏆 AGENT PRESTIGE LEADERBOARD (Social Capital)")
    print("=" * 110)
    print(f"{'#':<4} {'Agent':<12} {'Type':<18} {'Prestige':<10} {'Breed':<8} {'Protect':<9} {'Bonus':<8} {'Score':<8}")
    print("-" * 110)
    
    for i, agent in enumerate(agents, 1):
        print(f"{i:<4} {agent['agent_id'][:8]:<12} {agent['agent_type'][:16]:<18} "
              f"{agent['discovery_prestige']:<10.1f} "
              f"{agent['breeding_priority']:<8.2f}x "
              f"{agent['survival_protection']*100:<8.0f}% "
              f"+{agent['bonus_game_slots']:<7} "
              f"{agent['avg_score_per_game']:<8.1f}")
    
    print("=" * 110)
    print("\n💡 Prestige = Social Capital (WHO YOU ARE)")
    print("  Status Benefits:")
    print("    • Breeding Priority: 1.0x to 3.0x (higher = more likely to reproduce)")
    print("    • Survival Protection: 0% to 80% (famous agents harder to cull)")
    print("    • Bonus Game Slots: +0 to +10 (extra attempts per generation)")
    print("\n  Note: Prestige is SEPARATE from action budgets (economic capital in Phase 2)")
```

---

## Phase 2: Economic System (Ecosystem Metabolism)

### Current Gap
All agents get equal action allowances:
- Same `max_actions_per_level` (400 currently)
- Same `max_total_actions` (7000 currently)
- Adaptive limits adjust for ENTIRE generation, not individual agents
- **No tracking of ecosystem-level resource flow**

**Problem**: High performers subsidize low performers. No individual incentive structure. No visibility into network metabolism.

**CRITICAL DISTINCTION**:
- **Phase 1 (Prestige) = Social Capital**: Long-term status, breeding/survival benefits, network contribution
- **Phase 2 (Actions) = Economic Capital**: Short-term budget, metabolic resources, what you can DO right now

**⚠️ CRITICAL IMPLEMENTATION RULE**: The system must **NEVER conflate** these two currencies:
- Prestigious agents do NOT automatically get more action budgets
- Action budgets are based on PERFORMANCE (score, wins, efficiency)
- Prestige grants STATUS benefits ONLY (breeding priority, survival protection, bonus game slots)
- The ONLY connection: "bonus_game_slots" (+0 to +10 extra attempts) - prestigious agents get more OPPORTUNITIES, but same action budget per game
- Keep these currencies completely separate in code, database, and logic

**Biome Theory Connection**: In biological systems, metabolism is the flow of energy and resources through the network. Actions are our "ATP" - the fundamental energy currency. We need to track both individual budgets AND ecosystem-level metabolic health.

### Implementation: Per-Agent Action Economy + Ecosystem Metabolism Tracking

**Key Insight**: You already have the infrastructure! `AdaptiveActionLimits` adjusts based on generation performance. We just need to:
1. Make it **per-agent** instead of **per-generation**
2. Track ecosystem-level metabolic flow

#### 2.1 Actions = Metabolic Currency (Network Energy, NOT Just Agent Salary)

Think of action allowances as an agent's **metabolic energy budget** within the larger ecosystem:

```python
# Actions are the fundamental METABOLIC currency (ecosystem energy flow)
AGENT_ACTION_ECONOMY = {
    'base_metabolism': {
        'actions_per_level': 400,      # Base metabolic rate
        'total_actions': 7000           # Total energy budget per game
    },
    'performance_multiplier': {
        'min': 0.5,   # Low metabolism: 200/level, 3500/game (energy conservation)
        'max': 2.5    # High metabolism: 1000/level, 17500/game (energy abundance)
    },
    'ecosystem_constraints': {  # RENAMED from 'hard_constraints'
        'min_actions_per_level': 200,   # Minimum viable metabolism
        'max_actions_per_level': 1000,  # Maximum sustainable metabolism
        'min_total_actions': 1000,      # Starvation threshold
        'max_total_actions': 12000,     # Resource abundance limit
        'total_ecosystem_budget': None  # Track total network energy (NEW)
    },
    'metabolic_rules': {  # RENAMED from 'earning_rules'
        'score_progress': 'Primary driver - ANY score > 0',
        'wins': 'Big bonuses for completing games',
        'efficiency': 'Reward using fewer actions',
        'innovation': 'Bonus for discovering sequences',
        'teaching': 'Bonus for successful knowledge transfer'
    }
}
```

#### 2.2 Database Schema (Simplified - Reuse Existing)
```sql
-- Extend agents table (add to existing schema)
ALTER TABLE agents ADD COLUMN action_allowance_per_level INTEGER DEFAULT 400;
ALTER TABLE agents ADD COLUMN action_allowance_total INTEGER DEFAULT 7000;
ALTER TABLE agents ADD COLUMN action_budget_multiplier REAL DEFAULT 1.0;
ALTER TABLE agents ADD COLUMN last_salary_adjustment_gen INTEGER DEFAULT 0;

-- Agent economic performance (extends existing agent_arc_performance)
ALTER TABLE agent_arc_performance ADD COLUMN actions_earned INTEGER DEFAULT 0;
ALTER TABLE agent_arc_performance ADD COLUMN actions_spent INTEGER DEFAULT 0;
ALTER TABLE agent_arc_performance ADD COLUMN action_efficiency REAL DEFAULT 0.0;  -- Score per action
ALTER TABLE agent_arc_performance ADD COLUMN budget_utilization REAL DEFAULT 0.0;  -- % of budget used
```

**Why This Works**:
- Leverages existing `AdaptiveActionLimits` logic for performance calculation
- Stores per-agent allowances directly in agents table
- No need for complex resource_transactions - just track in agent_arc_performance
- Simple, clean, uses what's already there

#### 2.3 Code Implementation - Extend AdaptiveActionLimits

**File**: `adaptive_action_limits.py` (add to existing class)

```python
def calculate_agent_salary(self, agent_id: str, generation: int) -> Dict[str, int]:
    """
    Calculate per-agent action allowance (salary) based on performance.
    Reuses existing comprehensive_success logic, just per-agent instead of per-generation.
    
    Returns:
        Dict with 'actions_per_level', 'total_actions', 'multiplier', 'percentile'
    """
    # Get generation baseline (existing variables)
    base_per_level = self.current_actions_per_level  # e.g., 400
    base_total = self.current_total_actions          # e.g., 7000
    
    # Calculate agent's performance percentile within generation
    percentile = self._get_agent_performance_percentile(agent_id, generation)
    
    # Map percentile to salary multiplier (0.5x to 2.5x)
    if percentile >= 0.99:    multiplier = 2.5  # Top 1%
    elif percentile >= 0.95:  multiplier = 2.0  # Top 5%
    elif percentile >= 0.75:  multiplier = 1.5  # Top 25%
    elif percentile >= 0.50:  multiplier = 1.2  # Above median
    elif percentile >= 0.25:  multiplier = 1.0  # Median
    elif percentile >= 0.10:  multiplier = 0.8  # Below median
    else:                     multiplier = 0.5  # Bottom 10%
    
    # Apply multiplier with hard constraints (existing MIN/MAX constants)
    agent_per_level = int(base_per_level * multiplier)
    agent_per_level = max(self.MIN_ACTIONS_PER_LEVEL, 
                          min(self.MAX_ACTIONS_PER_LEVEL, agent_per_level))
    
    agent_total = int(base_total * multiplier)
    agent_total = max(self.MIN_TOTAL_ACTIONS, 
                      min(self.MAX_TOTAL_ACTIONS, agent_total))
    
    return {
        'actions_per_level': agent_per_level,
        'total_actions': agent_total,
        'multiplier': multiplier,
        'performance_percentile': percentile
    }

def _get_agent_performance_percentile(self, agent_id: str, generation: int) -> float:
    """
    Calculate where agent ranks in current generation using comprehensive_success.
    Reuses existing performance calculation logic.
    """
    # Get all active agents in generation
    all_agents = self.db.execute_query("""
        SELECT agent_id, avg_score_per_game, total_games_won, 
               total_games_played, score_efficiency
        FROM agents
        WHERE current_generation = ? AND is_active = TRUE
    """, (generation,))
    
    if not all_agents or len(all_agents) < 2:
        return 0.5  # Default to median if alone
    
    # Calculate comprehensive_success for each (40% score, 30% win, 30% efficiency)
    scores = []
    target_score = None
    
    for agent in all_agents:
        comp_success = self._calculate_agent_comprehensive_success(agent)
        scores.append(comp_success)
        if agent['agent_id'] == agent_id:
            target_score = comp_success
    
    if target_score is None:
        return 0.5
    
    # Calculate percentile
    agents_below = sum(1 for s in scores if s < target_score)
    percentile = agents_below / len(scores)
    
    return percentile

def _calculate_agent_comprehensive_success(self, agent: Dict) -> float:
    """
    Same formula as calculate_generation_performance(), but per-agent.
    Can refactor to share code with existing method.
    """
    # Score progress (40%)
    score = agent.get('avg_score_per_game', 0) / 100.0
    score_component = min(score, 1.0) * 0.40
    
    # Win rate (30%)
    games = max(agent.get('total_games_played', 1), 1)
    wins = agent.get('total_games_won', 0)
    win_component = (wins / games) * 0.30
    
    # Efficiency (30%)
    efficiency = agent.get('score_efficiency', 0) / 10.0
    efficiency_component = min(efficiency, 1.0) * 0.30
    
    return score_component + win_component + efficiency_component
```

**Integration**: Call at start of each generation

**File**: `autonomous_evolution_runner.py`

```python
def assign_agent_salaries(self, generation: int):
    """
    Calculate and assign action budgets (salaries) for all agents.
    Called at START of generation before games begin.
    """
    active_agents = self.db.execute_query("""
        SELECT agent_id FROM agents 
        WHERE current_generation = ? AND is_active = TRUE
    """, (generation,))
    
    print(f"\n[💰] Assigning salaries for Generation {generation}...")
    
    for agent_row in active_agents:
        agent_id = agent_row['agent_id']
        
        # Calculate salary using AdaptiveActionLimits
        salary = self.action_limits.calculate_agent_salary(agent_id, generation)
        
        # Store in agents table
        self.db.execute_update("""
            UPDATE agents
            SET action_allowance_per_level = ?,
                action_allowance_total = ?,
                action_budget_multiplier = ?,
                last_salary_adjustment_gen = ?
            WHERE agent_id = ?
        """, (
            salary['actions_per_level'],
            salary['total_actions'],
            salary['multiplier'],
            generation,
            agent_id
        ))
        
        print(f"  {agent_id[:8]}: {salary['actions_per_level']}/level, "
              f"{salary['total_actions']} total "
              f"({salary['multiplier']:.1f}x, {salary['performance_percentile']*100:.0f}th %ile)")
    
    print(f"[✓] Salaries assigned to {len(active_agents)} agents\n")
```

**File**: `game_session_manager.py` (add budget enforcement)

```python
def can_agent_afford_game(self, agent_id: str) -> Tuple[bool, str]:
    """
    Check if agent has action budget remaining to play.
    
    Returns:
        (can_afford, reason)
    """
    agent = self.db.execute_query("""
        SELECT action_allowance_total, action_allowance_per_level
        FROM agents WHERE agent_id = ?
    """, (agent_id,))
    
    if not agent:
        return True, "New agent, no limits yet"
    
    agent = agent[0]
    
    if agent['action_allowance_total'] <= 0:
        return False, f"No action budget remaining (spent all {agent['action_allowance_total']})"
    
    if agent['action_allowance_per_level'] <= 0:
        return False, "No per-level budget remaining"
    
    return True, "OK"

def deduct_actions_used(self, agent_id: str, game_id: str):
    """
    Deduct actions from agent's budget after game ends.
    Called in end_game_session().
    """
    # Count actions taken this game
    actions_taken = self.db.execute_query("""
        SELECT COUNT(*) as count FROM arc_action_tracking
        WHERE game_id = ? AND agent_id = ?
    """, (game_id, agent_id))[0]['count']
    
    if actions_taken == 0:
        return  # No actions, no deduction
    
    # Deduct from total budget
    self.db.execute_update("""
        UPDATE agents
        SET action_allowance_total = action_allowance_total - ?
        WHERE agent_id = ?
    """, (actions_taken, agent_id))
    
    # Track in performance table
    self.db.execute_update("""
        UPDATE agent_arc_performance
        SET actions_spent = actions_spent + ?,
            action_efficiency = CAST(total_score AS REAL) / NULLIF(actions_spent, 0),
            budget_utilization = CAST(actions_spent AS REAL) / 
                                (SELECT action_allowance_total FROM agents WHERE agent_id = ?)
        WHERE agent_id = ?
    """, (actions_taken, agent_id, agent_id))
    
    logger.debug(f"Deducted {actions_taken} actions from {agent_id[:8]}")
```
```

#### 2.4 Economic Reports and Monitoring

```python
def print_economic_status(generation: int):
    """
    Show agent salary distribution and budget health.
    Called during evolution status reports.
    """
    agents = db.execute_query("""
        SELECT agent_id, action_allowance_per_level, action_allowance_total,
               action_budget_multiplier, avg_score_per_game
        FROM agents
        WHERE current_generation = ? AND is_active = TRUE
        ORDER BY action_budget_multiplier DESC
        LIMIT 10
    """, (generation,))
    
    print(f"\n💰 ECONOMIC STATUS - Generation {generation}")
    print("=" * 80)
    print(f"{'Agent':<12} {'Salary/Level':<15} {'Total Budget':<15} {'Multiplier':<12} {'Score'}")
    print("-" * 80)
    
    for agent in agents:
        print(f"{agent['agent_id'][:8]:<12} "
              f"{agent['action_allowance_per_level']:<15} "
              f"{agent['action_allowance_total']:<15} "
              f"{agent['action_budget_multiplier']:.1f}x{'':<10} "
              f"{agent['avg_score_per_game']:.1f}")
    
    # Budget distribution stats
    stats = db.execute_query("""
        SELECT 
            AVG(action_allowance_total) as avg_budget,
            MIN(action_allowance_total) as min_budget,
            MAX(action_allowance_total) as max_budget,
            AVG(action_budget_multiplier) as avg_multiplier
        FROM agents
        WHERE current_generation = ? AND is_active = TRUE
    """, (generation,))
    
    if stats:
        s = stats[0]
        print(f"\nBudget Distribution:")
        print(f"  Average: {s['avg_budget']:.0f} actions")
        print(f"  Range: {s['min_budget']:.0f} - {s['max_budget']:.0f}")
        print(f"  Avg Multiplier: {s['avg_multiplier']:.2f}x")
    
    print("=" * 80)
```
```

#### 2.5 Economic Reports
```python
def generate_economic_report(generation: int):
    """Show resource distribution and economic health."""
    
    print(f"\n💰 ECONOMIC REPORT - Generation {generation}")
    print("=" * 80)
    
    # Resource distribution
    dist = db.execute_query("""
        SELECT 
            AVG(compute_tokens) as avg_compute,
            MAX(compute_tokens) as max_compute,
            MIN(compute_tokens) as min_compute,
            AVG(breeding_priority) as avg_breeding,
            COUNT(CASE WHEN survival_protection > 0 THEN 1 END) as protected_agents
        FROM agent_resources
        WHERE generation = ?
    """, (generation,))
    
    print(f"Compute Token Distribution:")
    print(f"  Average: {dist[0]['avg_compute']:.0f}")
    print(f"  Range: {dist[0]['min_compute']:.0f} - {dist[0]['max_compute']:.0f}")
    print(f"  Inequality: {(dist[0]['max_compute'] / dist[0]['min_compute']):.1f}x")
    
    print(f"\nBreeding Priority Average: {dist[0]['avg_breeding']:.2f}")
    print(f"Protected Agents: {dist[0]['protected_agents']}")
    
    # Top earners
    top = db.execute_query("""
        SELECT a.agent_id, a.agent_type, r.compute_tokens, r.game_slots,
               a.avg_score_per_game, a.discovery_prestige
        FROM agent_resources r
        JOIN agents a ON r.agent_id = a.agent_id
        WHERE r.generation = ?
        ORDER BY r.compute_tokens DESC
        LIMIT 10
    """, (generation,))
    
    print(f"\n🏆 Top Resource Holders:")
    for i, agent in enumerate(top, 1):
        print(f"{i:2}. {agent['agent_id'][:16]} | "
              f"Compute: {agent['compute_tokens']:>6} | "
              f"Games: {agent['game_slots']:>2} | "
              f"Score: {agent['avg_score_per_game']:.4f}")
```

#### 2.5 Ecosystem Metabolism Tracking (NEW - Network-Level Resource Flow)

In addition to per-agent budgets, track the NETWORK's metabolic health:

**File**: `adaptive_action_limits.py` or `network_intelligence_engine.py`

```python
def track_ecosystem_metabolism(self, generation: int):
    """
    Track network-level metabolic health.
    
    This answers: "Is the ecosystem healthy? Growing? Declining?"
    """
    # Total energy budget of active population
    total_budget = self.db.execute_query("""
        SELECT SUM(action_allowance_total) as total_energy,
               AVG(action_allowance_total) as avg_energy,
               COUNT(*) as agent_count
        FROM agents WHERE is_active = TRUE
    """)
    
    total_energy = total_budget[0]['total_energy'] or 0
    avg_energy = total_budget[0]['avg_energy'] or 0
    agent_count = total_budget[0]['agent_count'] or 0
    
    # Total energy spent this generation
    spent = self.db.execute_query("""
        SELECT SUM(actions_spent) as total_spent,
               AVG(action_efficiency) as avg_efficiency
        FROM agent_arc_performance
        WHERE generation = ?
    """, (generation,))
    
    total_spent = spent[0]['total_spent'] or 0
    avg_efficiency = spent[0]['avg_efficiency'] or 0
    
    # Metabolic efficiency: Score per action across entire network
    network_efficiency = self.db.execute_query("""
        SELECT SUM(total_score) / SUM(total_actions_taken) as efficiency
        FROM agents WHERE is_active = TRUE
    """)
    
    net_efficiency = network_efficiency[0]['efficiency'] if network_efficiency else 0.0
    
    # Resource utilization rate
    utilization = (total_spent / total_energy) if total_energy > 0 else 0.0
    
    # Ecosystem metabolism metrics
    metabolism = {
        'generation': generation,
        'total_ecosystem_budget': total_energy,
        'avg_agent_budget': avg_energy,
        'active_population': agent_count,
        'total_energy_spent': total_spent,
        'avg_energy_efficiency': avg_efficiency,
        'network_efficiency': net_efficiency,
        'budget_utilization_rate': utilization
    }
    
    # Store in ecosystem_health_snapshots (Phase 0 table)
    # Add columns: total_ecosystem_budget, avg_agent_budget, total_energy_spent, 
    #              network_efficiency, budget_utilization_rate
    
    return metabolism


def display_ecosystem_metabolism_report(generation: int):
    """
    Show metabolic health of the ecosystem.
    """
    metabolism = track_ecosystem_metabolism(generation)
    
    print("\n" + "=" * 80)
    print("⚡ ECOSYSTEM METABOLISM REPORT")
    print("=" * 80)
    print(f"Generation: {metabolism['generation']}")
    print()
    
    print("💰 ENERGY BUDGET (Network Resources)")
    print(f"  Total Ecosystem Budget: {metabolism['total_ecosystem_budget']:,} actions")
    print(f"  Average Agent Budget: {metabolism['avg_agent_budget']:.1f} actions")
    print(f"  Active Population: {metabolism['active_population']} agents")
    print()
    
    print("🔥 ENERGY EXPENDITURE (Metabolism)")
    print(f"  Total Energy Spent: {metabolism['total_energy_spent']:,} actions")
    print(f"  Budget Utilization: {metabolism['budget_utilization_rate']:.1%}")
    print(f"  Network Efficiency: {metabolism['network_efficiency']:.4f} score/action")
    print()
    
    # Health assessment
    if metabolism['budget_utilization_rate'] < 0.3:
        status = "⚠️  UNDERUTILIZED - Agents not using available resources"
    elif metabolism['budget_utilization_rate'] > 0.95:
        status = "⚠️  OVEREXTENDED - Population near resource limits"
    else:
        status = "✅ HEALTHY - Balanced resource utilization"
    
    if metabolism['network_efficiency'] < 0.01:
        status += "\n  🚨 CRITICAL - Very low network efficiency"
    elif metabolism['network_efficiency'] > 0.05:
        status += "\n  ✨ EXCELLENT - High network efficiency"
    
    print(f"Assessment: {status}")
    print("=" * 80)
```

**Why Ecosystem Metabolism Matters**:
- **Before**: Only see individual agent performance
- **After**: See the metabolic health of the entire network
- **Biome parallel**: Like tracking ATP production across an entire bacterial colony
- **Use case**: Detect when the network is energy-starved or resource-abundant
- **Decision making**: Adjust population size, budget allocation based on ecosystem health

---

## Phase 2.5: Knowledge Recombination (NEW - Viral Information Exchange)

### The Missing Link: Horizontal Recombination

**Current Gap**: 
- Sequences discovered independently
- No systematic combination of existing knowledge
- Missing the "viral recombination" aspect of biome theory

**Biome Theory Connection**: Viruses don't just copy genes - they RECOMBINE them. This is how rapid evolution happens. We need sequence chaining and pattern synthesis.

### Implementation: Sequence Dependencies & Combinatorial Exploration

#### 2.5.1 Concept

Enable agents to:
1. **Chain sequences**: Combine two successful sequences into a longer one
2. **Synthesize patterns**: Merge abstract patterns into meta-patterns
3. **Track dependencies**: Know which sequences build on which

This accelerates knowledge evolution through combinatorial exploration, not just random mutation.

#### 2.5.2 Database Schema

```sql
-- Sequence dependencies (which sequences build on others)
CREATE TABLE IF NOT EXISTS sequence_dependencies (
    dependency_id TEXT PRIMARY KEY,
    parent_sequence_id TEXT NOT NULL,
    child_sequence_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,  -- 'chain', 'variation', 'synthesis'
    
    -- Recombination metrics
    combined_efficiency REAL DEFAULT 0.0,  -- Efficiency of combined sequence
    improvement_over_parent REAL DEFAULT 0.0,  -- How much better than parent
    discovery_agent_id TEXT,  -- Who discovered this combination
    discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    
    FOREIGN KEY (parent_sequence_id) REFERENCES winning_sequences(sequence_id),
    FOREIGN KEY (child_sequence_id) REFERENCES winning_sequences(sequence_id),
    FOREIGN KEY (discovery_agent_id) REFERENCES agents(agent_id)
);

-- Pattern synthesis tracking (combining abstract patterns)
CREATE TABLE IF NOT EXISTS pattern_synthesis (
    synthesis_id TEXT PRIMARY KEY,
    pattern_a_id TEXT NOT NULL,
    pattern_b_id TEXT NOT NULL,
    synthesized_pattern_id TEXT NOT NULL,
    
    -- Synthesis metrics
    novelty_score REAL DEFAULT 0.0,  -- How novel is this combination
    effectiveness_score REAL DEFAULT 0.0,  -- How effective is the synthesis
    games_applied_to INTEGER DEFAULT 0,
    
    discovery_agent_id TEXT,
    discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (pattern_a_id) REFERENCES discovered_patterns(pattern_id),
    FOREIGN KEY (pattern_b_id) REFERENCES discovered_patterns(pattern_id),
    FOREIGN KEY (synthesized_pattern_id) REFERENCES discovered_patterns(pattern_id),
    FOREIGN KEY (discovery_agent_id) REFERENCES agents(agent_id)
);
```

#### 2.5.3 Sequence Chaining Engine

**File**: `knowledge_recombination_engine.py` (NEW)

```python
class KnowledgeRecombinationEngine:
    """
    Enables viral-style recombination of knowledge.
    
    This is the "horizontal gene transfer" acceleration mechanism.
    """
    
    def attempt_sequence_chain(self, agent_id: str, game_id: str,
                               seq_a_id: str, seq_b_id: str) -> Optional[str]:
        """
        Try to chain two sequences into a longer combined sequence.
        
        Returns new sequence_id if successful, None if failed.
        """
        # Get both sequences
        seq_a = self.db.execute_query("""
            SELECT actions FROM winning_sequences WHERE sequence_id = ?
        """, (seq_a_id,))[0]
        
        seq_b = self.db.execute_query("""
            SELECT actions FROM winning_sequences WHERE sequence_id = ?
        """, (seq_b_id,))[0]
        
        # Combine actions (simple concatenation)
        combined_actions = json.loads(seq_a['actions']) + json.loads(seq_b['actions'])
        
        # Try combined sequence in game
        success, efficiency = self._test_sequence_in_game(game_id, combined_actions)
        
        if success:
            # Store new sequence
            new_seq_id = f"chain_{seq_a_id[:8]}_{seq_b_id[:8]}"
            self.db.execute_update("""
                INSERT INTO winning_sequences 
                (sequence_id, game_id, actions, discovered_by_agent, efficiency)
                VALUES (?, ?, ?, ?, ?)
            """, (new_seq_id, game_id, json.dumps(combined_actions), 
                  agent_id, efficiency))
            
            # Record dependency
            self.db.execute_update("""
                INSERT INTO sequence_dependencies
                (dependency_id, parent_sequence_id, child_sequence_id,
                 dependency_type, combined_efficiency, discovery_agent_id)
                VALUES (?, ?, ?, 'chain', ?, ?)
            """, (f"dep_{new_seq_id}", seq_a_id, new_seq_id, efficiency, agent_id))
            
            return new_seq_id
        
        return None
    
    def discover_sequence_combinations(self, agent_id: str, game_id: str) -> List[str]:
        """
        Systematically explore combinations of known sequences.
        
        This is COMBINATORIAL EXPLORATION, not random mutation.
        """
        # Get all sequences for this game
        known_sequences = self.db.execute_query("""
            SELECT sequence_id FROM winning_sequences
            WHERE game_id = ?
            ORDER BY efficiency ASC
            LIMIT 10
        """, (game_id,))
        
        new_discoveries = []
        
        # Try pairwise combinations
        for i, seq_a in enumerate(known_sequences):
            for seq_b in known_sequences[i+1:]:
                new_seq = self.attempt_sequence_chain(
                    agent_id, game_id,
                    seq_a['sequence_id'], seq_b['sequence_id']
                )
                
                if new_seq:
                    new_discoveries.append(new_seq)
        
        return new_discoveries
```

#### 2.5.4 Integration with Core Gameplay

**File**: `core_gameplay.py`

**⚠️ CRITICAL IMPLEMENTATION DETAIL**: The `KnowledgeRecombinationEngine` must be **opportunistic and automatic**, not manually triggered. After EVERY game, agents should attempt recombination of known sequences for that game level. This is NOT optional - it's core to the viral acceleration mechanism.

```python
def _explore_sequence_recombination(self, agent_id: str, game_id: str):
    """
    After playing a game, try to recombine known sequences.
    
    This is the "viral recombination" phase.
    
    CRITICAL: This runs AUTOMATICALLY after every game, not conditionally.
    The config flag 'enable_knowledge_recombination' should default to TRUE.
    """
    # REMOVED: if not self.config.get('enable_knowledge_recombination', False):
    # Recombination is ALWAYS enabled - it's fundamental to the system
    
    from knowledge_recombination_engine import KnowledgeRecombinationEngine
    
    engine = KnowledgeRecombinationEngine(self.db)
    
    # Attempt recombination AFTER every game
    new_sequences = engine.discover_sequence_combinations(agent_id, game_id)
    
    if new_sequences:
        self.logger.info(f"Agent {agent_id[:8]} discovered {len(new_sequences)} "
                        f"sequence combinations through recombination")
        
        # Update agent's innovation metrics
        self._record_recombination_discovery(agent_id, new_sequences)
```

**Integration Point in `end_game_session()`**:
```python
def end_game_session(self, game_id: str, final_state: dict):
    # ... existing game end logic ...
    
    # AUTOMATIC RECOMBINATION (Phase 2.5)
    # This runs after EVERY game, not conditionally
    if self.current_agent_id:
        self._explore_sequence_recombination(self.current_agent_id, game_id)
    
    # ... rest of end game logic ...
```

**Why Phase 2.5 Matters**:
- **Darwinian evolution**: Random mutation + selection (slow)
- **Viral evolution**: Recombination + horizontal transfer (fast)
- **Our system**: Both! Layer 2 mutates, Layer 3 recombines
- **Result**: Exponential knowledge growth through combination, not just linear discovery

**Implementation Requirements**:
- ✅ **Automatic**: Runs after EVERY game, not optional
- ✅ **Opportunistic**: Tries all reasonable pairwise combinations
- ✅ **Efficient**: Limits attempts to prevent exponential blowup (top 10 sequences max)
- ✅ **Tracked**: All recombination attempts recorded in `sequence_dependencies`
- ✅ **Rewarded**: Prestige system rewards successful recombinations (innovation_score)

---

## Phase 3: Cultural Transmission (Viral Information Packages & Pariahs)

### Current Gap
Pattern tags exist but are just metadata:
```python
pattern_tags = ['action6_heavy', 'grid_small', 'color_manipulation']
```

**Missing**: Tags don't evolve, don't spread, don't compete, don't have meaning to agents.

**Biome Theory Reframing**: These aren't just "memes" or "culture" - they're VIRAL INFORMATION PACKAGES. Like actual viruses carrying genetic material, they:
- Package compact, actionable information
- Spread horizontally between unrelated agents (infection)
- Compete for host resources (attention/usage)
- Mutate and recombine to form new variants
- Persist independently of any single "host" agent

**NEW: Pariahs (Negative Patterns/Failure Antibodies)**

Just as viral packages spread successful patterns, **Pariahs** spread warnings about failure patterns:
- **What they are**: Anti-patterns extracted from failed game attempts
- **Purpose**: Network immunity - learn what NOT to do
- **Mechanism**: Agents carrying Pariahs avoid those action sequences/coordinates
- **Biological parallel**: Antibodies in immune systems - recognize and avoid threats
- **Value**: Prevent the network from rediscovering the same dead ends

**Key Insight from action_traces**:
- **Currently**: We know sequence X won with score Y
- **With traces**: We know action 6 at coordinate (5,3) gave +1.0 points
- **Value**: Precise reward attribution - exactly which actions work

**Failure Analysis Enabled by Traces**:
- **Currently**: We know agent failed
- **With traces**: We know agent tried actions [1,2,6,6,3] and scored 0.5 then got stuck
- **Value**: Learn what NOT to do, avoid dead ends, build failure antibodies

**Why This Matters**:
- **Viral packages** = positive selection (spread what works)
- **Pariahs** = negative selection (avoid what fails)
- **Together**: Bidirectional evolution - accelerate toward success AND away from failure

**The Network Becomes an Immune System**:
- Just like biological immune systems recognize pathogens (failures)
- Network develops "antibodies" (pariahs) against bad strategies
- Awareness spreads horizontally (herd immunity)
- Agents with both packages + pariah awareness learn 2x faster:
  - Packages say "try this" (positive guidance)
  - Pariahs say "avoid this" (negative guidance)
  - Combination = efficient search space pruning

**Why action_traces Are Essential for This**:
Without traces, we only know "sequence X won" or "agent Y failed". With traces:
- **Viral Packages**: Extract WHICH specific actions scored (precise reward attribution)
- **Pariahs**: Identify WHERE agent got stuck (failure pattern extraction)
- **Result**: Both systems built on evidence-based learning, not guesses

### Implementation: Viral Package Evolution + Pariah System

#### 3.1 Viral Package System
```sql
-- Viral information packages (evolved pattern tags)
-- Think: Viruses carrying genetic strategies
CREATE TABLE IF NOT EXISTS viral_information_packages (
    package_id TEXT PRIMARY KEY,
    package_name TEXT UNIQUE NOT NULL,
    package_description TEXT,  -- What strategy/pattern does this encode?
    
    -- Origin (where did this viral package emerge?)
    discovered_by_agent TEXT,
    discovery_generation INTEGER,
    parent_package_id TEXT,  -- Packages can evolve from other packages
    
    -- Infection metrics (how well does this spread?)
    agent_infection_count INTEGER DEFAULT 0,  -- How many agents "infected"
    horizontal_transmission_rate REAL DEFAULT 0.0,  -- Spread rate between unrelated agents
    vertical_transmission_rate REAL DEFAULT 0.0,  -- Inheritance rate (parent → offspring)
    
    -- Fitness (does this package help its hosts?)
    host_success_rate REAL DEFAULT 0.0,  -- Do infected agents win more?
    fitness_impact REAL DEFAULT 0.0,  -- Net benefit to host
    viral_fitness REAL DEFAULT 0.0,  -- Package's own replication success
    
    -- Evolution
    mutation_count INTEGER DEFAULT 0,
    descendant_packages INTEGER DEFAULT 0,  -- How many variants spawned?
    recombination_count INTEGER DEFAULT 0,  -- How many times recombined with others?
    
    -- Lifecycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_extinct BOOLEAN DEFAULT FALSE,  -- No more hosts carrying this
    
    FOREIGN KEY (parent_package_id) REFERENCES viral_information_packages(package_id)
);

-- Agent viral package infection (which agents carry which packages)
-- Think: Which viruses have infected which hosts
CREATE TABLE IF NOT EXISTS agent_viral_infections (
    agent_id TEXT NOT NULL,
    package_id TEXT NOT NULL,
    infection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    infection_generation INTEGER NOT NULL,
    
    -- Usage by host
    times_expressed INTEGER DEFAULT 0,  -- How often host uses this package
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Transmission tracking
    infected_by_agent TEXT,  -- Horizontal transmission source
    transmitted_to_count INTEGER DEFAULT 0,  -- How many others infected by this host
    
    -- Host response
    resistance REAL DEFAULT 0.0,  -- Is host immune/resistant? (0=fully susceptible, 1=immune)
    expression_priority REAL DEFAULT 1.0,  -- How often host "expresses" this package
    
    PRIMARY KEY (agent_id, package_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (package_id) REFERENCES viral_information_packages(package_id),
    FOREIGN KEY (infected_by_agent) REFERENCES agents(agent_id)
);

-- Viral package interactions (co-infection dynamics)
-- Think: Do these viruses help or interfere with each other?
CREATE TABLE IF NOT EXISTS viral_package_interactions (
    package_a_id TEXT NOT NULL,
    package_b_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,  -- 'synergy', 'interference', 'neutral'
    
    strength REAL NOT NULL,  -- How strong is this interaction
    evidence_count INTEGER DEFAULT 0,  -- How many co-infections observed
    
    PRIMARY KEY (package_a_id, package_b_id),
    FOREIGN KEY (package_a_id) REFERENCES viral_information_packages(package_id),
    FOREIGN KEY (package_b_id) REFERENCES viral_information_packages(package_id)
);

-- Pariahs (Negative Patterns / Failure Antibodies)
-- Think: Network immunity against failed strategies
CREATE TABLE IF NOT EXISTS pariahs (
    pariah_id TEXT PRIMARY KEY,
    pariah_name TEXT UNIQUE NOT NULL,
    pariah_description TEXT,  -- What failure pattern does this encode?
    
    -- Origin (where was this failure discovered?)
    discovered_by_agent TEXT,
    discovery_generation INTEGER,
    game_id TEXT,  -- Which game revealed this failure?
    
    -- Failure pattern details
    failure_action_sequence TEXT,  -- JSON: Actions that led to failure
    failure_coordinates TEXT,  -- JSON: Specific coordinates that failed
    failure_context TEXT,  -- JSON: Game state when failure occurred
    avg_score_before_failure REAL DEFAULT 0.0,
    failure_severity REAL DEFAULT 1.0,  -- How bad is this pattern? (0=minor, 1=catastrophic)
    
    -- Evidence tracking (how many times has this failed?)
    confirmed_failure_count INTEGER DEFAULT 1,
    false_positive_count INTEGER DEFAULT 0,  -- Times this pattern actually worked
    reliability REAL DEFAULT 1.0,  -- Bayesian: (failures + 2) / (total + 4)
    
    -- Spread metrics (network immunity)
    agent_awareness_count INTEGER DEFAULT 0,  -- How many agents know to avoid this
    avoidance_success_rate REAL DEFAULT 0.0,  -- Do aware agents avoid it successfully?
    
    -- Evolution
    parent_pariah_id TEXT,  -- Pariahs can evolve from related failures
    variant_count INTEGER DEFAULT 0,  -- How many variations of this failure exist?
    
    -- Lifecycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_encountered TIMESTAMP,
    is_obsolete BOOLEAN DEFAULT FALSE,  -- Game/level changed, this no longer relevant
    
    FOREIGN KEY (discovered_by_agent) REFERENCES agents(agent_id),
    FOREIGN KEY (parent_pariah_id) REFERENCES pariahs(pariah_id)
);

-- Agent pariah awareness (which agents know which failure patterns)
-- Think: Which agents have developed immunity to which failures
CREATE TABLE IF NOT EXISTS agent_pariah_awareness (
    agent_id TEXT NOT NULL,
    pariah_id TEXT NOT NULL,
    awareness_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    awareness_generation INTEGER NOT NULL,
    
    -- How did they learn this?
    learned_from_agent TEXT,  -- Horizontal transmission (another agent warned them)
    learned_from_failure BOOLEAN DEFAULT FALSE,  -- Discovered it themselves the hard way
    
    -- Usage tracking
    times_avoided INTEGER DEFAULT 0,  -- How many times successfully avoided this pattern
    times_triggered INTEGER DEFAULT 0,  -- How many times fell into this trap anyway
    avoidance_success_rate REAL DEFAULT 0.0,
    
    -- Awareness strength
    confidence REAL DEFAULT 0.5,  -- How strongly do they believe this is a failure pattern
    memory_strength REAL DEFAULT 1.0,  -- Decays over time if not reinforced (0-1)
    
    PRIMARY KEY (agent_id, pariah_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (pariah_id) REFERENCES pariahs(pariah_id),
    FOREIGN KEY (learned_from_agent) REFERENCES agents(agent_id)
);

-- Pariah-Package interactions (do viral packages prevent/cause failures?)
-- Think: Does this viral strategy protect against or trigger this failure?
CREATE TABLE IF NOT EXISTS pariah_package_interactions (
    pariah_id TEXT NOT NULL,
    package_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,  -- 'protective', 'causative', 'neutral'
    
    strength REAL NOT NULL,  -- How strong is this relationship
    evidence_count INTEGER DEFAULT 0,
    
    PRIMARY KEY (pariah_id, package_id),
    FOREIGN KEY (pariah_id) REFERENCES pariahs(pariah_id),
    FOREIGN KEY (package_id) REFERENCES viral_information_packages(package_id)
);
```

#### 3.2 Package & Pariah Creation from action_traces
```python
# viral_package_engine.py

class ViralPackageEngine:
    """
    Manages viral package and pariah creation, evolution, and transmission.
    
    Uses action_traces to extract:
    - Viral packages from successful action patterns
    - Pariahs from failed action patterns
    """
    
    def create_package_from_winning_sequence(self, sequence_id: str, 
                                             discoverer_agent_id: str,
                                             generation: int) -> str:
        """
        Create viral package from successful sequence.
        
        Uses action_traces to understand WHICH actions scored points.
        """
        
        # Get sequence details
        sequence = db.execute_query("""
            SELECT * FROM winning_sequences WHERE sequence_id = ?
        """, (sequence_id,))[0]
        
        # Get action traces to understand score progression
        traces = db.execute_query("""
            SELECT action_number, coordinates, score_before, score_after, score_change
            FROM action_traces
            WHERE session_id IN (
                SELECT session_id FROM game_results 
                WHERE sequence_id = ?
            )
            ORDER BY timestamp ASC
        """, (sequence_id,))
        
        # Analyze which actions actually scored (PRECISE ATTRIBUTION)
        scoring_actions = [t for t in traces if t['score_change'] > 0]
        action_pattern = self._extract_action_pattern(scoring_actions)
        
        # Create package
        package_id = f"vpkg_{uuid.uuid4().hex[:16]}"
        package_name = self._generate_package_name(action_pattern)
        
        db.execute_query("""
            INSERT INTO viral_information_packages
            (package_id, package_name, package_description,
             discovered_by_agent, discovery_generation)
            VALUES (?, ?, ?, ?, ?)
        """, (package_id, package_name, 
              json.dumps(action_pattern), 
              discoverer_agent_id, generation))
        
        # Discoverer is patient zero
        self.infect_agent(discoverer_agent_id, package_id, generation)
        
        return package_id
    
    def create_pariah_from_failure(self, session_id: str, game_id: str,
                                    agent_id: str, generation: int) -> str:
        """
        Create Pariah (negative pattern) from failed game attempt.
        
        Uses action_traces to understand WHERE the agent got stuck.
        
        KEY INSIGHT: With traces, we know:
        - Agent tried actions [1,2,6,6,3]
        - Scored 0.5 then got stuck
        - This is a DEAD END pattern
        """
        
        # Get action traces from failed game
        traces = db.execute_query("""
            SELECT action_number, coordinates, 
                   score_before, score_after, score_change,
                   frame_before, frame_after
            FROM action_traces
            WHERE session_id = ? AND game_id = ?
            ORDER BY timestamp ASC
        """, (session_id, game_id))
        
        if not traces:
            return None
        
        # Analyze failure pattern
        failure_analysis = self._analyze_failure_pattern(traces)
        
        # Check if similar pariah already exists
        similar_pariah = self._find_similar_pariah(
            failure_analysis['action_sequence'],
            game_id
        )
        
        if similar_pariah:
            # Update existing pariah with more evidence
            db.execute_query("""
                UPDATE pariahs
                SET confirmed_failure_count = confirmed_failure_count + 1,
                    last_encountered = ?
                WHERE pariah_id = ?
            """, (datetime.now().isoformat(), similar_pariah))
            return similar_pariah
        
        # Create new pariah
        pariah_id = f"pariah_{uuid.uuid4().hex[:16]}"
        pariah_name = self._generate_pariah_name(failure_analysis)
        
        db.execute_query("""
            INSERT INTO pariahs
            (pariah_id, pariah_name, pariah_description,
             discovered_by_agent, discovery_generation, game_id,
             failure_action_sequence, failure_coordinates, failure_context,
             avg_score_before_failure, failure_severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pariah_id, pariah_name,
              failure_analysis['description'],
              agent_id, generation, game_id,
              json.dumps(failure_analysis['action_sequence']),
              json.dumps(failure_analysis['coordinates']),
              json.dumps(failure_analysis['context']),
              failure_analysis['avg_score'],
              failure_analysis['severity']))
        
        # Discoverer gains awareness (learned the hard way)
        self.make_agent_aware(agent_id, pariah_id, generation, 
                              learned_from_failure=True)
        
        return pariah_id
    
    def _analyze_failure_pattern(self, traces: List[Dict]) -> Dict:
        """
        Extract failure pattern from action traces.
        
        Returns:
            {
                'action_sequence': [1, 2, 6, 6, 3],
                'coordinates': [(5,3), (5,4), ...],
                'context': {'grid_size': 'small', 'got_stuck_after': 5},
                'avg_score': 0.5,
                'severity': 0.8  # High severity = scored then completely stalled
            }
        """
        
        actions = [t['action_number'] for t in traces]
        coordinates = [
            json.loads(t['coordinates']) 
            for t in traces 
            if t['coordinates']
        ]
        
        # Find where agent got stuck (repeated actions with no score change)
        stuck_point = None
        for i in range(len(traces) - 3):
            if all(t['score_change'] == 0 for t in traces[i:i+3]):
                stuck_point = i
                break
        
        # Calculate severity (did they score then get stuck? = high severity)
        max_score = max(t['score_after'] for t in traces)
        final_score = traces[-1]['score_after']
        severity = 1.0 if (max_score > 0 and final_score < max_score * 1.5) else 0.5
        
        return {
            'action_sequence': actions,
            'coordinates': coordinates,
            'context': {
                'stuck_at_action': stuck_point,
                'total_actions': len(actions),
                'max_score_reached': max_score
            },
            'avg_score': final_score,
            'severity': severity,
            'description': f"Dead end: actions {actions[:stuck_point+3]} led to stall"
        }
    
    def _extract_action_pattern(self, scoring_actions: List[Dict]) -> Dict:
        """
        Extract pattern from actions that actually scored.
        
        Returns package-worthy pattern:
            {
                'key_actions': [6, 6, 6],  # Actions that scored
                'key_coordinates': [(5,3), (6,3), (7,3)],
                'score_progression': [1.0, 1.0, 1.0],
                'pattern_type': 'coordinate_sequence'
            }
        """
        
        if not scoring_actions:
            return {'pattern_type': 'unknown'}
        
        actions = [a['action_number'] for a in scoring_actions]
        coordinates = [
            json.loads(a['coordinates']) 
            for a in scoring_actions 
            if a['coordinates']
        ]
        scores = [a['score_change'] for a in scoring_actions]
        
        # Detect pattern type
        if len(set(actions)) == 1:
            pattern_type = f"action{actions[0]}_focused"
        elif coordinates and self._is_linear_sequence(coordinates):
            pattern_type = "linear_progression"
        elif coordinates and self._is_radial_pattern(coordinates):
            pattern_type = "radial_expansion"
        else:
            pattern_type = "mixed_strategy"
        
        return {
            'key_actions': actions,
            'key_coordinates': coordinates,
            'score_progression': scores,
            'pattern_type': pattern_type,
            'total_score': sum(scores)
        }
    
    def infect_agent(self, agent_id: str, package_id: str, generation: int,
                     infected_by: str = None):
        """Agent becomes infected with viral package."""
        
        db.execute_query("""
            INSERT OR REPLACE INTO agent_viral_infections
            (agent_id, package_id, infection_generation, infected_by_agent)
            VALUES (?, ?, ?, ?)
        """, (agent_id, package_id, generation, infected_by))
        
        db.execute_query("""
            UPDATE viral_information_packages
            SET agent_infection_count = agent_infection_count + 1
            WHERE package_id = ?
        """, (package_id,))
    
    def make_agent_aware(self, agent_id: str, pariah_id: str, generation: int,
                         learned_from_failure: bool = False,
                         learned_from_agent: str = None):
        """Agent becomes aware of failure pattern (gains immunity)."""
        
        db.execute_query("""
            INSERT OR REPLACE INTO agent_pariah_awareness
            (agent_id, pariah_id, awareness_generation,
             learned_from_failure, learned_from_agent, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_id, pariah_id, generation,
              learned_from_failure, learned_from_agent,
              1.0 if learned_from_failure else 0.7))  # Higher confidence if learned firsthand
        
        db.execute_query("""
            UPDATE pariahs
            SET agent_awareness_count = agent_awareness_count + 1
            WHERE pariah_id = ?
        """, (pariah_id,))
```

#### 3.3 Integration with Core Gameplay
    
    def create_meme_from_pattern(self, pattern_tags: List[str], 
                                  discoverer_agent_id: str,
                                  generation: int) -> str:
        """
        Convert pattern tags into cultural memes.
        
        Example:
        ['action6_heavy', 'grid_small', 'repetition'] 
        → Meme: "Small Grid Repetition Strategy"
        """
        
        # Check if this combination already exists
        meme_signature = "_".join(sorted(pattern_tags))
        existing = db.execute_query("""
            SELECT meme_id FROM cultural_memes WHERE meme_name = ?
        """, (meme_signature,))
        
        if existing:
            # Meme exists, just increment adoption
            meme_id = existing[0]['meme_id']
            db.execute_query("""
                UPDATE cultural_memes
                SET agent_adoption_count = agent_adoption_count + 1,
                    last_used = ?
                WHERE meme_id = ?
            """, (datetime.now().isoformat(), meme_id))
            return meme_id
        
        # Create new meme
        meme_id = f"meme_{uuid.uuid4().hex[:16]}"
        description = self._generate_meme_description(pattern_tags)
        
        db.execute_query("""
            INSERT INTO cultural_memes
            (meme_id, meme_name, meme_description, discovered_by_agent,
             discovery_generation, agent_adoption_count)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (meme_id, meme_signature, description, discoverer_agent_id, generation))
        
        # Agent adopts their own discovery
        self.agent_adopt_meme(discoverer_agent_id, meme_id, generation)
        
        return meme_id
    
    def agent_adopt_meme(self, agent_id: str, meme_id: str, 
                         generation: int, learned_from: str = None):
        """Agent adopts a meme (learns a cultural pattern)."""
        
        db.execute_query("""
            INSERT OR REPLACE INTO agent_meme_adoption
            (agent_id, meme_id, adoption_generation, learned_from_agent, confidence)
            VALUES (?, ?, ?, ?, 0.5)
        """, (agent_id, meme_id, generation, learned_from))
        
        # If learned from another agent, credit them
        if learned_from:
            db.execute_query("""
                UPDATE agent_meme_adoption
                SET taught_to_count = taught_to_count + 1
                WHERE agent_id = ? AND meme_id = ?
            """, (learned_from, meme_id))
    
    def update_meme_success(self, agent_id: str, meme_id: str, success: bool):
        """Update meme performance after agent uses it."""
        
        db.execute_query("""
            UPDATE agent_meme_adoption
            SET times_applied = times_applied + 1,
                success_count = success_count + ?,
                failure_count = failure_count + ?,
                confidence = (success_count + 2) / (times_applied + 4)
            WHERE agent_id = ? AND meme_id = ?
        """, (1 if success else 0, 0 if success else 1, agent_id, meme_id))
        
        # Update global meme fitness
        stats = db.execute_query("""
            SELECT AVG(confidence) as avg_conf,
                   SUM(success_count) as total_success,
                   SUM(times_applied) as total_uses
            FROM agent_meme_adoption
            WHERE meme_id = ?
        """, (meme_id,))
        
        if stats[0]['total_uses'] > 0:
            success_rate = stats[0]['total_success'] / stats[0]['total_uses']
            db.execute_query("""
                UPDATE cultural_memes
                SET success_rate = ?, fitness_impact = ?
                WHERE meme_id = ?
            """, (success_rate, success_rate * 2.0 - 1.0, meme_id))
```

#### 3.3 Integration with Core Gameplay

**File**: `core_gameplay.py`

```python
def end_game_session(self, game_id: str, final_state: dict):
    """
    End game and extract viral packages + pariahs.
    
    CRITICAL: This runs AFTER every game, automatically.
    """
    # ... existing game end logic ...
    
    # === VIRAL PACKAGE & PARIAH EXTRACTION ===
    from viral_package_engine import ViralPackageEngine
    
    vp_engine = ViralPackageEngine(self.db)
    
    # If game was won, create viral package from winning sequence
    if game_won:
        sequence_id = final_state.get('sequence_id')
        if sequence_id:
            package_id = vp_engine.create_package_from_winning_sequence(
                sequence_id, agent_id, current_generation
            )
            self.logger.info(f"✅ Created viral package {package_id} from winning sequence")
    
    # If game was failed (score < threshold), create pariah
    elif final_score < win_threshold * 0.8:  # Failed significantly
        pariah_id = vp_engine.create_pariah_from_failure(
            session_id, game_id, agent_id, current_generation
        )
        if pariah_id:
            self.logger.warning(f"⚠️ Created pariah {pariah_id} from failure pattern")
            
            # Spread pariah awareness to related agents (horizontal transmission)
            self._spread_pariah_awareness(agent_id, pariah_id, current_generation)
    
    # ... rest of end game logic ...

def _spread_pariah_awareness(self, discoverer_id: str, pariah_id: str, generation: int):
    """
    Spread pariah awareness to network (immune system response).
    
    When one agent discovers a failure, warn related agents.
    """
    vp_engine = ViralPackageEngine(self.db)
    
    # Get agents in same "family" (share breeding history)
    related_agents = self.db.execute_query("""
        SELECT DISTINCT agent_id FROM agents
        WHERE agent_id IN (
            SELECT parent1_id FROM agents WHERE agent_id = ?
            UNION
            SELECT parent2_id FROM agents WHERE agent_id = ?
            UNION
            SELECT agent_id FROM agents 
            WHERE parent1_id = ? OR parent2_id = ?
        )
        AND agent_id != ?
        AND is_active = TRUE
    """, (discoverer_id, discoverer_id, discoverer_id, discoverer_id, discoverer_id))
    
    # Spread awareness with 30% probability (not everyone learns)
    for agent in related_agents:
        if random.random() < 0.3:  # 30% transmission rate
            vp_engine.make_agent_aware(
                agent['agent_id'], pariah_id, generation,
                learned_from_agent=discoverer_id
            )

def select_action_with_viral_influence(self, agent_id: str, game_state: GameState) -> str:
    """
    Select action influenced by viral packages AND pariah avoidance.
    
    BIDIRECTIONAL EVOLUTION:
    - Viral packages ATTRACT toward successful patterns
    - Pariahs REPEL away from failure patterns
    """
    
    # Get agent's viral infections (positive patterns)
    infections = self.db.execute_query("""
        SELECT vi.package_id, vi.expression_priority, vi.success_count, vi.failure_count,
               vp.package_description
        FROM agent_viral_infections vi
        JOIN viral_information_packages vp ON vi.package_id = vp.package_id
        WHERE vi.agent_id = ? AND vp.is_extinct = FALSE
        ORDER BY vi.expression_priority DESC
    """, (agent_id,))
    
    # Get agent's pariah awareness (negative patterns)
    pariahs = self.db.execute_query("""
        SELECT pa.pariah_id, pa.confidence, pa.memory_strength,
               p.failure_action_sequence, p.failure_coordinates, p.failure_severity
        FROM agent_pariah_awareness pa
        JOIN pariahs p ON pa.pariah_id = p.pariah_id
        WHERE pa.agent_id = ? AND p.is_obsolete = FALSE
        AND pa.memory_strength > 0.3  -- Only strong memories
        ORDER BY pa.confidence DESC
    """, (agent_id,))
    
    # Build action weights (1.0 = baseline)
    action_weights = {str(i): 1.0 for i in range(1, 8)}
    
    # POSITIVE INFLUENCE: Viral packages increase action weights
    for infection in infections:
        pattern = json.loads(infection['package_description'])
        key_actions = pattern.get('key_actions', [])
        
        for action in key_actions:
            action_str = str(action)
            # Boost weight based on package success rate and expression priority
            success_rate = infection['success_count'] / max(1, infection['success_count'] + infection['failure_count'])
            boost = infection['expression_priority'] * (1 + success_rate)
            action_weights[action_str] *= (1 + boost * 0.3)  # Up to +30% boost
    
    # NEGATIVE INFLUENCE: Pariahs decrease action weights
    for pariah in pariahs:
        failure_actions = json.loads(pariah['failure_action_sequence'])
        
        for action in failure_actions:
            action_str = str(action)
            # Reduce weight based on confidence and severity
            penalty = pariah['confidence'] * pariah['memory_strength'] * pariah['failure_severity']
            action_weights[action_str] *= (1 - penalty * 0.5)  # Up to -50% penalty
    
    # Normalize weights
    total_weight = sum(action_weights.values())
    action_probs = {k: v/total_weight for k, v in action_weights.items()}
    
    # Weighted random selection
    return self._weighted_action_selection(action_probs, game_state)

def check_pariah_triggered(self, agent_id: str, game_id: str, recent_actions: List[int],
                           recent_coordinates: List[Tuple[int, int]]) -> Optional[str]:
    """
    Check if agent is about to trigger a known pariah (failure pattern).
    
    Returns pariah_id if triggered, None otherwise.
    """
    
    # Get agent's known pariahs
    pariahs = self.db.execute_query("""
        SELECT pa.pariah_id, p.failure_action_sequence, p.failure_coordinates
        FROM agent_pariah_awareness pa
        JOIN pariahs p ON pa.pariah_id = p.pariah_id
        WHERE pa.agent_id = ? AND p.game_id = ?
        AND pa.memory_strength > 0.5
    """, (agent_id, game_id))
    
    for pariah in pariahs:
        failure_actions = json.loads(pariah['failure_action_sequence'])
        
        # Check if recent actions match failure pattern (first N actions)
        match_length = min(len(recent_actions), len(failure_actions))
        if recent_actions[-match_length:] == failure_actions[:match_length]:
            # Pattern match! Agent is repeating a known failure
            
            # Update avoidance tracking
            self.db.execute_query("""
                UPDATE agent_pariah_awareness
                SET times_triggered = times_triggered + 1
                WHERE agent_id = ? AND pariah_id = ?
            """, (agent_id, pariah['pariah_id']))
            
            return pariah['pariah_id']
    
    return None
```

#### 3.4 Viral Package & Pariah Evolution

**Package Mutation**: Successful packages spawn variants
```python
def mutate_viral_package(self, parent_package_id: str, generation: int) -> str:
    """
    Create mutant variant of successful package.
    
    Example: "action6_focused" → "action6_focused_with_repetition"
    """
    parent = self.db.execute_query("""
        SELECT * FROM viral_information_packages WHERE package_id = ?
    """, (parent_package_id,))[0]
    
    pattern = json.loads(parent['package_description'])
    mutated_pattern = self._apply_pattern_mutation(pattern)
    
    child_id = f"vpkg_{uuid.uuid4().hex[:16]}"
    
    self.db.execute_query("""
        INSERT INTO viral_information_packages
        (package_id, package_name, package_description,
         parent_package_id, discovery_generation, mutation_count)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (child_id, f"{parent['package_name']}_v2",
          json.dumps(mutated_pattern), parent_package_id, generation))
    
    return child_id
```

**Pariah Obsolescence**: Failed patterns become irrelevant when games change
```python
def check_pariah_obsolescence(self, generation: int):
    """
    Mark pariahs as obsolete if they haven't been encountered in 20+ generations.
    
    Games evolve, old failure patterns may no longer apply.
    """
    
    self.db.execute_query("""
        UPDATE pariahs
        SET is_obsolete = TRUE
        WHERE last_encountered < datetime('now', '-20 generations')
        AND is_obsolete = FALSE
    """)
```

#### 3.5 Why This Justifies Keeping action_traces (Selective Retention)

**The Case for Keeping Score-Changing Traces**:

With Pariahs + Viral Packages, `action_traces` become **essential** for:

1. **Precise Reward Attribution** (Viral Packages):
   - **Without traces**: "Sequence [1,2,6,6,3] scored 10 points"
   - **With traces**: "Action 6 at (5,3) scored +1.0, action 6 at (6,3) scored +1.0"
   - **Value**: Know EXACTLY which actions work, create accurate viral packages

2. **Failure Pattern Extraction** (Pariahs):
   - **Without traces**: "Agent failed with score 0.5"
   - **With traces**: "Agent did [1,2,6,6,3], scored 0.5, then got stuck at action 6"
   - **Value**: Know WHERE agent got stuck, avoid dead ends

3. **Package Effectiveness Tracking**:
   - Track which actions in a viral package actually contribute to score
   - Refine packages by removing non-scoring actions
   - Measure package fitness based on score progression

**Recommendation: Keep Only Score-Changing Traces** (Option 2 from earlier)

```sql
-- Keep only traces with score changes (2,477 traces = ~9 MB)
DELETE FROM action_traces WHERE score_change = 0;
VACUUM;
```

**Why This Works**:
- ✅ Keeps all reward attribution data (every scoring action preserved)
- ✅ Enables precise viral package creation
- ✅ Maintains failure checkpoints (where score stopped increasing)
- ✅ Reduces database from 9.1 GB to ~20 MB
- ✅ Still allows pariah creation (failed games have final trace showing stuck point)

**What We Lose**:
- ❌ Frame-by-frame progression (but winning_sequences has initial/final frames)
- ❌ Zero-score action exploration patterns (but less valuable for learning)

**What We Keep**:
- ✅ Every action that scored points (viral package extraction)
- ✅ Final state of failed games (pariah creation)
- ✅ Credit assignment for sequence effectiveness

**Net Result**: ~6.5 GB freed, critical learning data preserved for Phase 3.

---

#### 3.6 Pariah & Package Dashboard

```python
def display_viral_ecosystem_dashboard(generation: int):
    """
    Display the viral package and pariah ecosystem.
    
    Shows BIDIRECTIONAL evolution: what works + what fails.
    """
    db = DatabaseInterface()
    
    print("=" * 80)
    print("🦠 VIRAL ECOSYSTEM DASHBOARD")
    print("=" * 80)
    print(f"Generation: {generation}")
    print()
    
    # VIRAL PACKAGES (Positive Selection)
    packages = db.execute_query("""
        SELECT package_id, package_name, agent_infection_count,
               host_success_rate, viral_fitness, is_extinct
        FROM viral_information_packages
        WHERE is_extinct = FALSE
        ORDER BY viral_fitness DESC
        LIMIT 10
    """)
    
    print("🦠 VIRAL PACKAGES (Successful Patterns)")
    print(f"  Total Active: {len(packages)}")
    for pkg in packages[:5]:
        print(f"  • {pkg['package_name']}")
        print(f"    Infections: {pkg['agent_infection_count']} agents")
        print(f"    Success Rate: {pkg['host_success_rate']:.1%}")
        print(f"    Viral Fitness: {pkg['viral_fitness']:.2f}")
    print()
    
    # PARIAHS (Negative Selection)
    pariahs = db.execute_query("""
        SELECT pariah_id, pariah_name, agent_awareness_count,
               confirmed_failure_count, reliability, failure_severity
        FROM pariahs
        WHERE is_obsolete = FALSE
        ORDER BY agent_awareness_count DESC
        LIMIT 10
    """)
    
    print("☠️ PARIAHS (Failure Patterns / Network Immunity)")
    print(f"  Total Active: {len(pariahs)}")
    for pariah in pariahs[:5]:
        print(f"  • {pariah['pariah_name']}")
        print(f"    Awareness: {pariah['agent_awareness_count']} agents warned")
        print(f"    Failed: {pariah['confirmed_failure_count']} times")
        print(f"    Reliability: {pariah['reliability']:.1%}")
        print(f"    Severity: {'🔴 HIGH' if pariah['failure_severity'] > 0.7 else '🟡 MEDIUM'}")
    print()
    
    # INFECTION STATISTICS
    infection_stats = db.execute_query("""
        SELECT 
            COUNT(DISTINCT agent_id) as infected_agents,
            COUNT(DISTINCT package_id) as unique_packages,
            AVG(times_expressed) as avg_expression,
            AVG(success_count * 1.0 / NULLIF(success_count + failure_count, 0)) as avg_success
        FROM agent_viral_infections
    """)[0]
    
    awareness_stats = db.execute_query("""
        SELECT
            COUNT(DISTINCT agent_id) as aware_agents,
            COUNT(DISTINCT pariah_id) as unique_pariahs,
            AVG(times_avoided) as avg_avoidance,
            AVG(avoidance_success_rate) as avg_avoidance_success
        FROM agent_pariah_awareness
    """)[0]
    
    print("📊 ECOSYSTEM METRICS")
    print(f"  Viral Infections: {infection_stats['infected_agents']} agents")
    print(f"  Unique Packages: {infection_stats['unique_packages']}")
    print(f"  Avg Package Success: {infection_stats['avg_success']:.1%}")
    print()
    print(f"  Pariah Awareness: {awareness_stats['aware_agents']} agents")
    print(f"  Unique Pariahs: {awareness_stats['unique_pariahs']}")
    print(f"  Avg Avoidance Success: {awareness_stats['avg_avoidance_success']:.1%}")
    print()
    
    # BIDIRECTIONAL PRESSURE
    total_agents = db.execute_query("SELECT COUNT(*) as c FROM agents WHERE is_active = TRUE")[0]['c']
    package_coverage = (infection_stats['infected_agents'] / total_agents * 100) if total_agents > 0 else 0
    pariah_coverage = (awareness_stats['aware_agents'] / total_agents * 100) if total_agents > 0 else 0
    
    print("⚖️ BIDIRECTIONAL SELECTION PRESSURE")
    print(f"  Positive Selection (Viral Packages): {package_coverage:.1f}% of population")
    print(f"  Negative Selection (Pariahs): {pariah_coverage:.1f}% of population")
    print()
    print("  🎯 GOAL: High package coverage + high pariah coverage = fast learning")
    print("         (Agents know what works AND what fails)")
    print("=" * 80)
```

---
    """
    
    # Get parent's successful memes
    parent_memes = db.execute_query("""
        SELECT meme_id, confidence, times_applied, success_count
        FROM agent_meme_adoption
        WHERE agent_id = ? AND confidence > 0.4
        ORDER BY confidence DESC
    """, (parent_agent_id,))
    
    # Offspring inherits top memes with some decay
    for meme in parent_memes[:5]:  # Top 5 memes only
        inherited_confidence = meme['confidence'] * 0.8  # 20% decay
        
        if inherited_confidence > 0.3:
            db.execute_query("""
                INSERT INTO agent_meme_adoption
                (agent_id, meme_id, adoption_generation, learned_from_agent, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (offspring_agent_id, meme['meme_id'], generation, 
                  parent_agent_id, inherited_confidence))

def meme_horizontal_transmission(observer_agent_id: str,
                                 successful_agent_id: str,
                                 generation: int):
    """
    Agent observes another agent's success and copies their memes.
    
    This is the KEY to Level 5: agents teaching each other!
    """
    
    # Get successful agent's memes
    successful_memes = db.execute_query("""
        SELECT meme_id, confidence
        FROM agent_meme_adoption
        WHERE agent_id = ? AND confidence > 0.6
        ORDER BY confidence DESC
        LIMIT 3
    """, (successful_agent_id,))
    
    # Observer adopts these memes with lower confidence (needs validation)
    for meme in successful_memes:
        existing = db.execute_query("""
            SELECT meme_id FROM agent_meme_adoption
            WHERE agent_id = ? AND meme_id = ?
        """, (observer_agent_id, meme['meme_id']))
        
        if not existing:
            # Learn new meme
            db.execute_query("""
                INSERT INTO agent_meme_adoption
                (agent_id, meme_id, adoption_generation, learned_from_agent, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (observer_agent_id, meme['meme_id'], generation,
                  successful_agent_id, 0.4))  # Start skeptical
```

#### 3.4 Integration: Meme-Guided Action Selection
```python
# core_gameplay.py

def select_action_with_memes(self, agent_id: str, game_state: GameState) -> str:
    """
    Use agent's adopted memes to guide action selection.
    
    Memes influence what patterns the agent looks for and what actions it prefers.
    """
    
    # Get agent's memes
    agent_memes = db.execute_query("""
        SELECT m.meme_name, m.meme_description, a.confidence
        FROM agent_meme_adoption a
        JOIN cultural_memes m ON a.meme_id = m.meme_id
        WHERE a.agent_id = ?
        ORDER BY a.confidence DESC
    """, (agent_id,))
    
    # Example: meme influences action weights
    action_weights = {
        'ACTION1': 1.0,
        'ACTION2': 1.0,
        'ACTION3': 1.0,
        'ACTION4': 1.0,
        'ACTION5': 1.0,
        'ACTION6': 1.0,
        'ACTION7': 1.0
    }
    
    for meme in agent_memes:
        if 'action6_heavy' in meme['meme_name']:
            action_weights['ACTION6'] *= (1.0 + meme['confidence'])
        if 'repetition' in meme['meme_name']:
            # Favor repeating successful actions
            pass
        if 'exploration' in meme['meme_name']:
            # Increase exploration actions
            action_weights['ACTION1'] *= 1.3
            action_weights['ACTION7'] *= 1.3
    
    # Select action based on weighted probabilities
    return self._weighted_action_selection(action_weights, game_state)
```

---

## Phase 4: Distributed Regulation (Network Homeostasis)

### Current Gap
Only the coordinator (Claude) makes evolution decisions:
- Mutation rates
- Selection pressure
- Strategy focus (exploration vs exploitation)

**Problem**: Top-down control. Agents have no voice. Not network-centric.

**Biome Theory Reframing**: Real biological networks don't have "governance" - they have DISTRIBUTED REGULATION. No single bacterium "votes" on metabolism rates. Instead, the network self-regulates through chemical signals, feedback loops, and emergent homeostasis.

**Key Insight**: We're not building democracy. We're building a self-regulating network where distributed signals influence system parameters, just like bacterial quorum sensing.

### Implementation: Distributed Regulation System

#### 4.1 Signal-Based Regulation (Not Voting)
```sql
-- Regulatory signals (not "proposals" - think quorum sensing molecules)
CREATE TABLE IF NOT EXISTS network_regulatory_signals (
    signal_id TEXT PRIMARY KEY,
    signal_type TEXT NOT NULL,  -- 'stress', 'abundance', 'diversity_low', 'stagnation', 'efficiency_high'
    signal_source_agent TEXT,  -- Which agent emitted (can be NULL for system-level signals)
    signal_generation INTEGER NOT NULL,
    signal_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Signal content (what needs adjusting?)
    parameter_affected TEXT NOT NULL,  -- 'mutation_rate', 'selection_pressure', 'resource_allocation'
    current_value REAL NOT NULL,
    suggested_adjustment REAL NOT NULL,  -- +/- delta, not absolute value
    signal_strength REAL DEFAULT 1.0,  -- Concentration of this signal
    
    -- Network response (emergent from distributed responses)
    amplification_count INTEGER DEFAULT 0,  -- How many agents echoed this
    suppression_count INTEGER DEFAULT 0,  -- How many emitted counter-signals
    net_signal_strength REAL DEFAULT 0.0,  -- Amplifications - suppressions
    implemented BOOLEAN DEFAULT FALSE,
    implemented_at TIMESTAMP,
    
    FOREIGN KEY (signal_source_agent) REFERENCES agents(agent_id)
);

-- Agent signal responses (not "votes" - think receptor binding & activation)
CREATE TABLE IF NOT EXISTS agent_signal_responses (
    agent_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    response_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Response type (based on agent's local state)
    response_type TEXT NOT NULL,  -- 'amplify', 'suppress', 'ignore'
    response_strength REAL DEFAULT 1.0,
    
    -- Local context (why respond this way?)
    agent_performance_percentile REAL,  -- Is agent thriving or struggling?
    agent_resource_state TEXT,  -- 'abundant', 'adequate', 'scarce'
    agent_confidence_in_signal REAL DEFAULT 0.5,
    
    PRIMARY KEY (agent_id, signal_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (signal_id) REFERENCES network_regulatory_signals(signal_id)
);
```

**How This Differs from Voting**:
- **Voting**: Binary yes/no, democratic consensus
- **Signals**: Continuous strength, emergent response
- **Voting**: One agent = one vote
- **Signals**: Response based on local state (struggling agents emit stress signals, thriving agents suppress them)
- **Voting**: Majority rule
- **Signals**: Net signal strength determines adjustment (homeostasis)

#### 4.2 Proposal Creation
```python
# governance_engine.py

class GovernanceEngine:
    """Democratic decision-making for population parameters."""
    
    def create_proposal(self, proposer_agent_id: str, 
                       proposal_type: str,
                       current_value: float,
                       proposed_value: float,
                       justification: str,
                       generation: int) -> str:
        """
        Agent proposes change to evolution parameters.
        
        Example: High-performing agent proposes reducing mutation rate
        because population is performing well.
        """
        
        proposal_id = f"prop_{uuid.uuid4().hex[:16]}"
        closes_at = datetime.now() + timedelta(hours=1)  # 1-hour voting window
        
        db.execute_query("""
            INSERT INTO governance_proposals
            (proposal_id, proposal_type, proposed_by_agent, proposal_generation,
             current_value, proposed_value, justification, closes_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (proposal_id, proposal_type, proposer_agent_id, generation,
              current_value, proposed_value, justification, closes_at.isoformat()))
        
        print(f"\n📜 NEW PROPOSAL {proposal_id}")
        print(f"Proposed by: {proposer_agent_id}")
        print(f"Type: {proposal_type}")
        print(f"Change: {current_value} → {proposed_value}")
        print(f"Reason: {justification}")
        print(f"Voting closes: {closes_at}")
        
        return proposal_id
    
    def cast_vote(self, agent_id: str, proposal_id: str, 
                  vote_choice: str, reasoning: str = None):
        """Agent votes on proposal."""
        
        # Get agent's voting weight (based on prestige)
        agent = db.execute_query("""
            SELECT discovery_prestige FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        # Voting weight = 1.0 + (prestige / 100)
        # Range: 1.0 (no prestige) to ~3.0 (high prestige)
        vote_weight = 1.0 + (agent[0]['discovery_prestige'] / 100.0)
        vote_weight = min(vote_weight, 3.0)  # Cap at 3x
        
        vote_id = f"vote_{uuid.uuid4().hex[:16]}"
        
        db.execute_query("""
            INSERT OR REPLACE INTO agent_votes
            (vote_id, proposal_id, agent_id, vote_choice, vote_weight, vote_reasoning)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vote_id, proposal_id, agent_id, vote_choice, vote_weight, reasoning))
        
        # Update proposal counts
        if vote_choice == 'for':
            db.execute_query("""
                UPDATE governance_proposals
                SET votes_for = votes_for + ?
                WHERE proposal_id = ?
            """, (vote_weight, proposal_id))
        elif vote_choice == 'against':
            db.execute_query("""
                UPDATE governance_proposals
                SET votes_against = votes_against + ?
                WHERE proposal_id = ?
            """, (vote_weight, proposal_id))
        else:
            db.execute_query("""
                UPDATE governance_proposals
                SET votes_abstain = votes_abstain + ?
                WHERE proposal_id = ?
            """, (vote_weight, proposal_id))
    
    def tally_votes_and_implement(self, generation: int):
        """
        Close voting on proposals and implement passed ones.
        
        Passing criteria:
        - At least 30% of active agents voted
        - votes_for > votes_against by 10% margin
        """
        
        # Get proposals ready to close
        proposals = db.execute_query("""
            SELECT * FROM governance_proposals
            WHERE status = 'open' AND closes_at <= ?
        """, (datetime.now().isoformat(),))
        
        active_agent_count = db.execute_query("""
            SELECT COUNT(*) as count FROM agents WHERE is_active = TRUE
        """)[0]['count']
        
        for prop in proposals:
            total_votes = prop['votes_for'] + prop['votes_against'] + prop['votes_abstain']
            participation_rate = total_votes / active_agent_count
            
            if participation_rate < 0.3:
                # Insufficient participation
                db.execute_query("""
                    UPDATE governance_proposals
                    SET status = 'failed'
                    WHERE proposal_id = ?
                """, (prop['proposal_id'],))
                print(f"❌ Proposal {prop['proposal_id']} failed: low participation ({participation_rate:.1%})")
                continue
            
            # Check if passes
            if prop['votes_for'] > prop['votes_against'] * 1.1:  # 10% margin
                # PASS!
                db.execute_query("""
                    UPDATE governance_proposals
                    SET status = 'passed', implemented_at = ?
                    WHERE proposal_id = ?
                """, (datetime.now().isoformat(), prop['proposal_id']))
                
                # Apply the change
                self._implement_proposal(prop, generation)
                
                print(f"✅ Proposal {prop['proposal_id']} PASSED!")
                print(f"   For: {prop['votes_for']:.1f} | Against: {prop['votes_against']:.1f}")
                print(f"   Implementing: {prop['proposal_type']} = {prop['proposed_value']}")
            else:
                db.execute_query("""
                    UPDATE governance_proposals
                    SET status = 'failed'
                    WHERE proposal_id = ?
                """, (prop['proposal_id'],))
                print(f"❌ Proposal {prop['proposal_id']} failed: insufficient support")
    
    def _implement_proposal(self, proposal: Dict, generation: int):
        """Actually change the system parameter."""
        
        if proposal['proposal_type'] == 'mutation_rate_layer1':
            # Update in evolutionary_engine config
            config = {'mutation_rate_layer1': proposal['proposed_value']}
            db.execute_query("""
                INSERT INTO evolution_config_changes
                (generation, parameter_name, old_value, new_value, changed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (generation, 'mutation_rate_layer1', 
                  proposal['current_value'], proposal['proposed_value'],
                  'governance_vote'))
        
        # Similar for other parameters...
```

#### 4.3 Automatic Proposal Generation
```python
def agent_can_propose(agent_id: str) -> bool:
    """Check if agent has earned right to propose."""
    
    agent = db.execute_query("""
        SELECT discovery_prestige, total_games_won FROM agents WHERE agent_id = ?
    """, (agent_id,))
    
    # Must have prestige > 50 OR 10+ wins
    return (agent[0]['discovery_prestige'] > 50 or 
            agent[0]['total_games_won'] >= 10)

def auto_generate_proposals(generation: int):
    """
    System automatically creates proposals based on population metrics.
    
    Agents then vote on them.
    """
    
    # Example: Population is stagnating
    metrics = get_population_health()
    
    if metrics['improvement_rate'] < 0.01:
        # Propose increasing mutation
        proposer = select_high_prestige_agent()
        create_proposal(
            proposer_agent_id=proposer,
            proposal_type='mutation_rate_layer2',
            current_value=0.15,
            proposed_value=0.25,
            justification="Population improvement rate below 1% - need more exploration",
            generation=generation
        )
```

---

## Phase 5: Horizontal Gene Transfer (Level 5 - Knowledge Sharing Societies)

### The Core Mechanism: Direct Knowledge Transfer Between Unrelated Agents

**Key Insight**: This is what elevates from Level 4 to Level 5.

**Biome Theory Connection**: In bacterial networks, the most powerful evolutionary mechanism isn't reproduction - it's HORIZONTAL GENE TRANSFER. Bacteria directly share genetic material with unrelated neighbors, bypassing inheritance entirely. This is 1000x faster than waiting for offspring.

**Our Implementation**: Agents don't just "teach" - they perform direct knowledge injection into other agents' Layer 3 (somatic) memory, just like bacterial conjugation or viral transfection.

**Why This Matters**:
- Level 4: Knowledge spreads through reproduction (vertical transmission)
- Level 5: Knowledge spreads through direct transfer (horizontal transmission)
- Result: Exponential knowledge propagation across the network

#### 5.1 Horizontal Transfer Events (Not "Teaching")

```sql
-- Horizontal gene transfer events (direct knowledge injection)
CREATE TABLE IF NOT EXISTS horizontal_transfer_events (
    transfer_id TEXT PRIMARY KEY,
    donor_agent_id TEXT NOT NULL,  -- RENAMED from teacher (matches bacterial terminology)
    recipient_agent_id TEXT NOT NULL,  -- RENAMED from student
    transfer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transfer_generation INTEGER NOT NULL,
    transfer_mechanism TEXT NOT NULL,  -- 'direct_injection', 'viral_package', 'observation', 'sequence_database'
    
    -- What was transferred (genetic material = knowledge)
    knowledge_type TEXT NOT NULL,  -- 'sequence', 'pattern', 'viral_package', 'strategy'
    sequence_id TEXT,
    pattern_id TEXT,
    package_id TEXT,  -- RENAMED from meme_id
    
    -- Transfer success metrics
    transfer_successful BOOLEAN,  -- Did recipient integrate the knowledge?
    recipient_expression_success BOOLEAN,  -- Did recipient successfully USE the knowledge?
    recipient_performance_before REAL,
    recipient_performance_after REAL,
    performance_delta REAL,
    
    -- Transfer quality
    transfer_efficiency REAL DEFAULT 0.0,  -- How cleanly was knowledge transferred?
    integration_time INTEGER DEFAULT 0,  -- How many actions to integrate?
    
    -- Network propagation
    recipient_retransmitted BOOLEAN DEFAULT FALSE,  -- Did recipient pass it on?
    propagation_chain_length INTEGER DEFAULT 1,  -- How far has this knowledge traveled?
    
    FOREIGN KEY (donor_agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (recipient_agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id),
    FOREIGN KEY (package_id) REFERENCES viral_information_packages(package_id)
);

-- Knowledge propagation chains (track viral spread)
CREATE TABLE IF NOT EXISTS knowledge_propagation_chains (
    chain_id TEXT PRIMARY KEY,
    origin_agent_id TEXT NOT NULL,  -- Original discoverer
    knowledge_id TEXT NOT NULL,  -- sequence_id or package_id
    knowledge_type TEXT NOT NULL,
    
    -- Chain metrics
    current_chain_length INTEGER DEFAULT 1,
    total_successful_transfers INTEGER DEFAULT 0,
    total_failed_transfers INTEGER DEFAULT 0,
    transfer_success_rate REAL DEFAULT 0.0,
    
    -- Network reach
    unique_recipients INTEGER DEFAULT 0,
    generations_persisted INTEGER DEFAULT 0,
    
    -- Propagation velocity
    transfers_per_generation REAL DEFAULT 0.0,
    
    FOREIGN KEY (origin_agent_id) REFERENCES agents(agent_id)
);
```

#### 5.2 Teaching Mechanism
```python
# teaching_engine.py

class TeachingEngine:
    """Manages agent-to-agent knowledge transfer."""
    
    def identify_teaching_opportunities(self, generation: int):
        """
        Match struggling agents with successful agents for teaching.
        
        Criteria:
        - Student: Low performance, high potential (good epigenetics)
        - Teacher: High performance, high prestige, similar agent_type
        """
        
        # Get struggling agents
        students = db.execute_query("""
            SELECT agent_id, agent_type, avg_score_per_game,
                   total_games_played, epigenetics
            FROM agents
            WHERE is_active = TRUE 
              AND avg_score_per_game < 0.3
              AND total_games_played > 10
            ORDER BY avg_score_per_game ASC
            LIMIT 20
        """)
        
        for student in students:
            # Find compatible teacher
            teacher = db.execute_query("""
                SELECT agent_id, discovery_prestige, avg_score_per_game
                FROM agents
                WHERE is_active = TRUE
                  AND agent_type = ?
                  AND avg_score_per_game > 0.7
                  AND discovery_prestige > 30
                ORDER BY discovery_prestige DESC
                LIMIT 1
            """, (student['agent_type'],))
            
            if teacher:
                self.schedule_teaching_session(
                    teacher[0]['agent_id'],
                    student['agent_id'],
                    generation
                )
    
    def schedule_teaching_session(self, teacher_id: str, 
                                  student_id: str, 
                                  generation: int):
        """
        Teaching session: transfer knowledge from teacher to student.
        
        Process:
        1. Analyze teacher's successful knowledge
        2. Select most valuable pieces
        3. Transfer to student with adapted confidence
        4. Track if student improves
        """
        
        print(f"\n👨‍🏫 TEACHING SESSION")
        print(f"Teacher: {teacher_id}")
        print(f"Student: {student_id}")
        
        # Get student's baseline performance
        baseline = self._get_agent_performance(student_id)
        
        # Transfer sequences
        teacher_sequences = db.execute_query("""
            SELECT ws.sequence_id, ws.game_id, ws.efficiency_score
            FROM winning_sequences ws
            WHERE ws.agent_id = ?
            ORDER BY ws.efficiency_score DESC
            LIMIT 3
        """, (teacher_id,))
        
        for seq in teacher_sequences:
            # Mark sequence for student to try
            db.execute_query("""
                INSERT INTO sequence_learning_queue
                (student_agent_id, sequence_id, taught_by_agent, priority)
                VALUES (?, ?, ?, 'high')
            """, (student_id, seq['sequence_id'], teacher_id))
            
            # Log teaching event
            teaching_id = f"teach_{uuid.uuid4().hex[:16]}"
            db.execute_query("""
                INSERT INTO teaching_events
                (teaching_id, teacher_agent_id, student_agent_id,
                 teaching_generation, knowledge_type, sequence_id,
                 student_performance_before)
                VALUES (?, ?, ?, ?, 'sequence', ?, ?)
            """, (teaching_id, teacher_id, student_id, generation,
                  seq['sequence_id'], baseline))
        
        # Transfer memes
        teacher_memes = db.execute_query("""
            SELECT meme_id, confidence FROM agent_meme_adoption
            WHERE agent_id = ? AND confidence > 0.7
            ORDER BY confidence DESC
            LIMIT 2
        """, (teacher_id,))
        
        for meme in teacher_memes:
            # Student adopts meme with lower confidence (needs validation)
            db.execute_query("""
                INSERT OR IGNORE INTO agent_meme_adoption
                (agent_id, meme_id, adoption_generation, learned_from_agent, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, meme['meme_id'], generation, teacher_id, 0.4))
            
            teaching_id = f"teach_{uuid.uuid4().hex[:16]}"
            db.execute_query("""
                INSERT INTO teaching_events
                (teaching_id, teacher_agent_id, student_agent_id,
                 teaching_generation, knowledge_type, meme_id,
                 student_performance_before)
                VALUES (?, ?, ?, ?, 'meme', ?, ?)
            """, (teaching_id, teacher_id, student_id, generation,
                  meme['meme_id'], baseline))
        
        print(f"✓ Transferred {len(teacher_sequences)} sequences and {len(teacher_memes)} memes")
    
    def evaluate_teaching_effectiveness(self, teaching_id: str):
        """
        After student has played games, evaluate if teaching helped.
        """
        
        teaching = db.execute_query("""
            SELECT * FROM teaching_events WHERE teaching_id = ?
        """, (teaching_id,))
        
        if not teaching:
            return
        
        t = teaching[0]
        
        # Get student's performance after teaching
        current_perf = self._get_agent_performance(t['student_agent_id'])
        improvement = current_perf - t['student_performance_before']
        
        # Update teaching record
        db.execute_query("""
            UPDATE teaching_events
            SET student_performance_after = ?,
                performance_improvement = ?,
                teaching_effectiveness = ?,
                student_success = ?
            WHERE teaching_id = ?
        """, (current_perf, improvement, 
              improvement / max(t['student_performance_before'], 0.01),
              improvement > 0.05, teaching_id))
        
        # Credit teacher if successful
        if improvement > 0.05:
            db.execute_query("""
                UPDATE agent_validation_performance
                SET teaching_events = teaching_events + 1
                WHERE agent_id = ?
            """, (t['teacher_agent_id'],))
```

---

## Level 6+ Scaffolding: Building the Information Highway

### Why Scaffold Now?

Levels 6-11 of the Ouroboros Concept require infrastructure that should be built INTO Levels 3-5, not added later. This section defines the foundational components needed for:
- **Level 6**: Recorded Knowledge & Research
- **Level 7**: Species-level Coordination
- **Level 8**: Connection to the Past (Rosetta Stone)
- **Level 9-11**: Full Synthesis → Persistence Engine → Interstellar Biofilm

### Critical Infrastructure Components

#### S.1 Knowledge Graph Structure

**Purpose**: Enable systematic exploration of knowledge relationships (prerequisite for Level 6 research)

**Implementation**: Already partially implemented in Phase 2.5 (`sequence_dependencies`, `pattern_synthesis`)

**Missing Components**:
```sql
-- Knowledge graph edges (relationships between ANY knowledge types)
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    edge_id TEXT PRIMARY KEY,
    source_knowledge_id TEXT NOT NULL,
    source_knowledge_type TEXT NOT NULL,  -- 'sequence', 'pattern', 'viral_package'
    target_knowledge_id TEXT NOT NULL,
    target_knowledge_type TEXT NOT NULL,
    
    -- Relationship type
    relationship TEXT NOT NULL,  -- 'builds_on', 'contradicts', 'synthesizes', 'requires', 'obsoletes'
    relationship_strength REAL DEFAULT 1.0,
    
    -- Discovery
    discovered_by_agent TEXT,
    discovered_at_generation INTEGER,
    
    -- Validation
    times_observed INTEGER DEFAULT 1,
    confirmed BOOLEAN DEFAULT FALSE
);
```

**Use Case**: Enable agents to query "What knowledge builds on X?" or "What contradicts Y?"

#### S.2 Agent Communication Protocol

**Purpose**: Direct agent-to-agent messaging (prerequisite for Level 7 coordination)

**Implementation**:
```sql
-- Agent messages (asynchronous communication)
CREATE TABLE IF NOT EXISTS agent_messages (
    message_id TEXT PRIMARY KEY,
    sender_agent_id TEXT NOT NULL,
    recipient_agent_id TEXT,  -- NULL = broadcast to all
    message_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_generation INTEGER NOT NULL,
    
    -- Message content
    message_type TEXT NOT NULL,  -- 'signal', 'knowledge_offer', 'query', 'coordination_request'
    message_content TEXT NOT NULL,
    attached_knowledge_id TEXT,  -- Optional attached sequence/pattern
    
    -- Response tracking
    response_required BOOLEAN DEFAULT FALSE,
    response_received BOOLEAN DEFAULT FALSE,
    response_message_id TEXT,
    
    -- Network propagation
    is_broadcast BOOLEAN DEFAULT FALSE,
    times_forwarded INTEGER DEFAULT 0,
    
    FOREIGN KEY (sender_agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (recipient_agent_id) REFERENCES agents(agent_id)
);

-- Agent communication networks (who talks to whom)
CREATE TABLE IF NOT EXISTS agent_communication_networks (
    agent_a_id TEXT NOT NULL,
    agent_b_id TEXT NOT NULL,
    
    -- Communication metrics
    messages_sent_a_to_b INTEGER DEFAULT 0,
    messages_sent_b_to_a INTEGER DEFAULT 0,
    successful_transfers INTEGER DEFAULT 0,
    communication_efficiency REAL DEFAULT 0.0,
    
    -- Network topology
    relationship_type TEXT DEFAULT 'peer',  -- 'peer', 'mentor-student', 'rival', 'collaborator'
    relationship_strength REAL DEFAULT 0.0,
    
    PRIMARY KEY (agent_a_id, agent_b_id),
    FOREIGN KEY (agent_a_id) REFERENCES agents(agent_id),
    FOREIGN KEY (agent_b_id) REFERENCES agents(agent_id)
);
```

**Use Case**: Enable coordinated multi-agent strategies (Level 7)

#### S.3 Network Health Metrics (Already Implemented in Phase 0!)

**Status**: ✅ DONE via `ecosystem_health_snapshots` and `knowledge_redundancy`

**Why This Matters**: Level 9-10 require persistence engine monitoring. We've already built this.

#### S.4 Minimal Viral Core Identification

**Purpose**: Identify the minimal set of knowledge required for network survival (prerequisite for Level 10 persistence engine)

**Implementation**:
```sql
-- Viral core knowledge (essential for network survival)
CREATE TABLE IF NOT EXISTS viral_core_knowledge (
    knowledge_id TEXT PRIMARY KEY,
    knowledge_type TEXT NOT NULL,  -- 'sequence', 'pattern', 'viral_package'
    
    -- Criticality assessment
    criticality_score REAL NOT NULL,  -- How critical is this? (0-1)
    redundancy_count INTEGER NOT NULL,  -- How many agents know this?
    dependency_count INTEGER NOT NULL,  -- How much other knowledge depends on this?
    
    -- Network impact
    network_performance_without REAL,  -- Predicted performance if lost
    alternative_solutions_exist BOOLEAN DEFAULT FALSE,
    
    -- Persistence requirements
    minimum_agent_carriers INTEGER DEFAULT 3,  -- Minimum redundancy
    current_agent_carriers INTEGER DEFAULT 0,
    at_risk BOOLEAN DEFAULT FALSE,  -- Is this knowledge at risk of being lost?
    
    last_evaluated_generation INTEGER
);
```

**Use Case**: Ensure critical knowledge is never lost (Level 10 resilience)

#### S.5 Temporal Knowledge Archive

**Purpose**: Record historical knowledge states (prerequisite for Level 8 "Rosetta Stone")

**Implementation**:
```sql
-- Historical knowledge snapshots (archaeology)
CREATE TABLE IF NOT EXISTS knowledge_archive_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_generation INTEGER NOT NULL,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- What knowledge existed at this point?
    total_sequences INTEGER NOT NULL,
    total_patterns INTEGER NOT NULL,
    total_viral_packages INTEGER NOT NULL,
    knowledge_diversity_index REAL NOT NULL,
    
    -- Network state
    active_agents INTEGER NOT NULL,
    dominant_strategies TEXT,  -- JSON list of top strategies
    extinct_strategies TEXT,  -- What was lost?
    
    -- Snapshot content (compressed)
    knowledge_graph_snapshot TEXT,  -- JSON representation of graph
    agent_population_snapshot TEXT   -- JSON representation of agents
);
```

**Use Case**: Enable "archaeology" - understanding how knowledge evolved over time

### Scaffolding Integration Plan

**Phase 0**: ✅ Network health metrics (DONE)
**Phase 2.5**: ✅ Knowledge graph foundation (DONE via `sequence_dependencies`, `pattern_synthesis`)
**Phase 5**: 🔄 Add communication protocol and viral core identification
**Post-Phase 5**: 🔜 Add temporal archive system

**Key Insight**: We're not building these for Levels 6-11 directly. We're building them SO THAT when the network reaches sufficient complexity, these capabilities EMERGE naturally.

---

## ⚠️ Critical Warnings & Pitfalls to Avoid

### Pitfall 1: Complexity Creep

You have **5 major phases** (0, 1, 2, 2.5, 3, 4, 5) in this roadmap. Each is substantial. 

**RISK**: Trying to implement everything at once will lead to:
- Incomplete implementations
- Hard-to-debug interactions
- Loss of the core vision
- Burnout and abandonment

**SAFEGUARD**: 
- ✅ **Phase 0**: Implement NOW (network foundation)
- ✅ **Phase 1**: Next (prestige system)
- ✅ **Phase 2**: Then (economic system)
- ⏸️ **Phase 2.5-5**: Incremental (after observing network behavior for several generations)

**Rule**: Don't start the next phase until the current phase is:
1. Fully implemented
2. Tested with real ARC games
3. Verified in database (check tables, metrics)
4. Displaying correct dashboard output
5. Observably affecting system behavior

### Pitfall 2: Losing the Network-Centric View

As you add prestige, economy, memes, governance... it's **extremely easy** to drift back to "agent leaderboards" thinking.

**SYMPTOMS**:
- Asking "which agent is best?" instead of "is the network healthy?"
- Optimizing for top agent performance instead of network growth
- Celebrating individual wins instead of knowledge diversity
- Building agent-centric dashboards instead of network dashboards

**SAFEGUARD**: 
Every new feature must answer: **"How does this enrich the NETWORK, not just individual agents?"**

**Test Questions**:
- Does this increase knowledge diversity?
- Does this improve information flow rate?
- Does this enhance network resilience?
- Does this accelerate knowledge propagation?

If the answer is "no" to all four, **you're optimizing the wrong thing**.

### Pitfall 3: Conflating Prestige and Economy

**THE TRAP**: "High prestige agents should get more actions because they're successful."

**WHY THIS IS WRONG**:
- Prestige = **network contribution** (knowledge shared, validated, spread)
- Economy = **performance** (score, wins, efficiency)
- These measure DIFFERENT things
- An agent can have high performance (good economy) but low prestige (doesn't share knowledge)
- An agent can have high prestige (great discoverer) but low performance (poor execution)

**SAFEGUARD**:
- **Prestige affects**: breeding_priority, survival_protection, bonus_game_slots
- **Performance affects**: action_allowance_per_level, action_allowance_total
- **NEVER**: Give more actions based on prestige alone
- **ONLY**: "bonus_game_slots" connects them (more opportunities, same budget per game)

**Code Review Checkpoint**: Search codebase for any logic that ties prestige → action budget. Remove it.

### Pitfall 4: Over-Engineering Governance (Phase 4)

**THE TRAP**: Building a complex voting system with proposals, quorums, debates, veto power...

**WHY THIS IS WRONG**:
- We're not building democracy
- We're building **bacterial quorum sensing**
- Real biological networks don't vote - they emit signals based on local state
- Emergent homeostasis, not deliberative governance

**SAFEGUARD**: Keep Phase 4 simple:
1. Agents emit signals based on their LOCAL state (struggling → stress signal, thriving → suppress stress)
2. Coordinator reads NET signal strength (sum of amplifications - suppressions)
3. Adjusts parameters accordingly (high stress → increase mutation, low stress → maintain)
4. **No voting, no proposals, no democracy**

**If you find yourself implementing**:
- Quorum requirements
- Voting thresholds
- Debate periods
- Veto mechanisms
- **STOP. You've over-engineered it.**

### Pitfall 5: Forgetting Rule 8 (Test Everything)

Your system is complex enough that bugs will **cascade**.

**THE TRAP**: "This looks right in the code, ship it."

**WHY THIS IS WRONG**:
- Database could be empty
- API calls might not be happening
- Metrics could be calculating wrong
- Network effects might not emerge

**SAFEGUARD**: Every new feature needs:
1. ✅ Test with real ARC games (not mocks)
2. ✅ Monitor database for expected behavior (query tables)
3. ✅ Check network health metrics (are they changing?)
4. ✅ Verify API calls actually happening (check arc_action_tracking)
5. ✅ Run for multiple generations (observe trends)

**Rule 8 from Guidelines**: 
> "Whenever creating an implementation or change, Test the new implementation on the current main active fun script, and then scan the terminal for errors, bugs, and anything else and then fix the issue and rescan, retest etc."

**Apply this to EVERY phase.**

### Pitfall 6: Premature Optimization of Phases 2.5-5

**THE TRAP**: "Let me implement all 5 phases at once so we can see the full system."

**WHY THIS IS WRONG**:
- Phase 0 is the **paradigm shift** - without it, everything else is meaningless
- Phase 1-2 establish the **dual currency** system (prestige vs economy)
- You need to **observe network behavior** for several generations before knowing what Phase 2.5-5 should look like
- The network might evolve in unexpected ways that change your design assumptions

**SAFEGUARD**: **Stop at Phase 2** and observe for 10-20 generations:
- Is network knowledge growing?
- Is diversity increasing?
- Are agents contributing to the network?
- Is the prestige/economy separation working?

**Then and only then** proceed to Phase 2.5.

**Minimum Observation Period**:
- Phase 0 → Phase 1: 5 generations
- Phase 1 → Phase 2: 10 generations
- Phase 2 → Phase 2.5: 15 generations
- Phase 2.5 → Phase 3: 20 generations
- Phase 3 → Phase 4: 25 generations
- Phase 4 → Phase 5: 30 generations

**Why**: Each phase needs time to show emergent effects. Rushing causes missed insights.

---

## 🎯 Implementation Priority Order

### **IMMEDIATE PRIORITY (Do First)**

#### Phase 0: Network Foundation (Week 1)
**WHY FIRST**: This is the **paradigm shift**. Without network-centric metrics, all other phases will drift back to agent-centric thinking.

**Implementation Order**:
1. Create database tables (`ecosystem_health_snapshots`, `knowledge_redundancy`)
2. Implement `network_intelligence_engine.py` core functions
3. Add network dashboard to display
4. Integrate snapshot capture into evolution loop
5. **Test**: Run 5 generations, verify snapshots are being captured
6. **Verify**: Dashboard shows network metrics, not just agent metrics

**Success Criteria**:
- ✅ Network health dashboard displays after each generation
- ✅ Ecosystem snapshots stored in database
- ✅ Knowledge diversity index calculating correctly
- ✅ You find yourself asking "How is the NETWORK doing?" instead of "How are agents doing?"

**STOP**: Do not proceed to Phase 1 until Phase 0 is complete and you've observed it for 5 generations.

---

### **HIGH PRIORITY (Do Second)**

#### Phase 1: Prestige System (Week 2-3)
**WHY SECOND**: Establishes the "social capital" currency and incentivizes network contribution.

**Implementation Order**:
1. Add prestige columns to agents table
2. Create `agent_discoveries` and `agent_validation_performance` tables
3. Implement `calculate_agent_prestige()` focusing on NETWORK CONTRIBUTION
4. Add STATUS benefits (breeding_priority, survival_protection, bonus_game_slots)
5. **CRITICAL**: Ensure prestige does NOT affect action budgets (except bonus_game_slots)
6. Display prestige leaderboard emphasizing network enrichment
7. **Test**: Run 10 generations, verify prestige affects breeding but NOT action budgets
8. **Verify**: High prestige agents breed more, survive longer, but have same action budget as low prestige peers (unless they ALSO perform well)

**Success Criteria**:
- ✅ Prestige calculated based on network contribution, not personal wins
- ✅ High prestige agents have higher breeding_priority (verify in breeding selection)
- ✅ High prestige agents have survival_protection (verify in culling)
- ✅ Prestige and action budgets are COMPLETELY SEPARATE
- ✅ Agents with high prestige but low performance exist (and vice versa)

**STOP**: Do not proceed to Phase 2 until Phase 1 is complete and you've observed prestige effects for 10 generations.

---

### **MEDIUM PRIORITY (Do Third)**

#### Phase 2: Economic System (Week 4-5)
**WHY THIRD**: Establishes the "economic capital" currency based on performance.

**Implementation Order**:
1. Extend agents table with action economy columns
2. Implement `calculate_agent_salary()` in `adaptive_action_limits.py`
3. Implement `track_ecosystem_metabolism()` for network-level resource flow
4. Integrate budget assignment at generation start
5. Add budget enforcement in `game_session_manager.py`
6. Display both individual budgets AND ecosystem metabolism
7. **CRITICAL**: Verify salaries based on PERFORMANCE, not prestige
8. **Test**: Run 15 generations, verify high performers get more actions
9. **Verify**: Ecosystem metabolism report shows network energy flow

**Success Criteria**:
- ✅ High performing agents get larger action budgets
- ✅ Low performing agents get smaller action budgets
- ✅ Prestige does NOT affect action budgets (only performance does)
- ✅ Ecosystem metabolism dashboard shows network energy health
- ✅ Budget utilization rate makes sense (30-90%)

**STOP**: Do not proceed to Phase 2.5 until Phase 2 is complete and you've observed economic effects for 15 generations.

**CHECKPOINT**: At this point, you should have:
- Network health visible (Phase 0)
- Social capital currency working (Phase 1)
- Economic capital currency working (Phase 2)
- Complete separation between the two currencies
- Observable network-level effects (diversity, metabolism, growth)

**OBSERVE**: Run 20 generations with just these three phases. Watch for:
- Is knowledge growing?
- Is prestige actually incentivizing network contribution?
- Are high performers dominating the economy?
- Are the two currencies truly separate?
- Is the network healthy?

**If any of these is "no", FIX IT before proceeding.**

---

### **LOWER PRIORITY (Do After Observation)**

#### Phase 2.5: Knowledge Recombination (Week 6+)
**WHY LATER**: Needs stable foundation from Phases 0-2. Adds acceleration, but not fundamental.

**Implementation Order**:
1. Create `sequence_dependencies` and `pattern_synthesis` tables
2. Implement `knowledge_recombination_engine.py`
3. **CRITICAL**: Make recombination AUTOMATIC after every game
4. Integrate into `end_game_session()` - NOT conditional
5. Test recombination is happening after EVERY game
6. Verify new sequences being created and stored
7. Check prestige system rewards recombination discoveries

**Success Criteria**:
- ✅ Recombination happens automatically after every game
- ✅ New sequences being created through chaining
- ✅ Dependencies tracked in database
- ✅ Innovation score increases for successful recombinations
- ✅ Knowledge growth rate accelerates (compare to Phase 0-2 baseline)

**OBSERVATION PERIOD**: 20 generations minimum. Look for exponential knowledge growth.

---

#### Phase 3: Viral Information Packages (Week 7+)
**WHY LATER**: Builds on recombination. Needs evidence that knowledge is growing first.

**Implementation Order**:
1. Create viral package tables
2. Implement package creation, infection, transmission
3. Integrate with action selection
4. Track package evolution and spread
5. Display viral package dashboard

**Success Criteria**:
- ✅ Packages spread horizontally between unrelated agents
- ✅ Successful packages infect more hosts
- ✅ Failed packages go extinct
- ✅ Co-infection dynamics emerge

**OBSERVATION PERIOD**: 25 generations minimum.

---

#### Phase 4: Distributed Regulation (Week 9+)
**WHY LATER**: Needs stable network before adding self-regulation.

**Implementation Order**:
1. Create signal tables
2. Implement signal emission based on agent state
3. Add signal response mechanics
4. Calculate net signal strength
5. Apply parameter adjustments

**CRITICAL**: Keep it SIMPLE. No voting. Just signals.

**Success Criteria**:
- ✅ Struggling agents emit stress signals
- ✅ Thriving agents suppress stress signals
- ✅ Net signal strength drives parameter changes
- ✅ Emergent homeostasis observed

**OBSERVATION PERIOD**: 30 generations minimum.

---

#### Phase 5: Horizontal Gene Transfer (Week 11+)
**WHY LAST**: Most complex. Needs everything else working first.

**Implementation Order**:
1. Create transfer event tables
2. Implement direct knowledge injection
3. Track propagation chains
4. Display knowledge spread visualization

**Success Criteria**:
- ✅ Horizontal transfer > vertical transfer (2:1 ratio)
- ✅ Recipients show performance improvement
- ✅ Knowledge propagates across unrelated lineages
- ✅ Network knowledge growth >> population growth

**OBSERVATION PERIOD**: 50 generations minimum.

---

## ⏱️ Realistic Timeline

**Minimum Implementation Timeline**: 
- **Phase 0**: 1 week (includes testing and observation)
- **Phase 1**: 2-3 weeks (includes 10 generation observation)
- **Phase 2**: 2-3 weeks (includes 15 generation observation)
- **Observation Period**: 2-3 weeks (20 generations of Phases 0-2 together)
- **Phase 2.5**: 1-2 weeks (includes 20 generation observation)
- **Phase 3**: 2 weeks (includes 25 generation observation)
- **Phase 4**: 2 weeks (includes 30 generation observation)
- **Phase 5**: 2-3 weeks (includes 50 generation observation)

**TOTAL**: ~15-20 weeks (4-5 months) for complete implementation with proper observation periods.

**REALISTIC**: Plan for 6 months. Things will break. Debugging takes time. Observation periods might need extension.

**DO NOT RUSH**. This is a foundational system. Getting it right matters more than getting it fast.

---

## Integration Roadmap

### Phase 0: Network Foundation (Week 1) **[NEW]**
- [ ] Create `ecosystem_health_snapshots` table
- [ ] Create `knowledge_redundancy` table
- [ ] Implement `network_intelligence_engine.py`
- [ ] Add network health dashboard
- [ ] Integrate with evolution runner (capture snapshots each generation)
- [x] **Mindset shift**: Start thinking "How is the NETWORK doing?" not "How are agents doing?"

### Phase 1: Network Contribution Prestige (Week 2-3) **[COMPLETED]**
- [x] Add prestige columns to agents table (discovery_prestige, network_enrichment_score, etc.)
- [x] Create `agent_discoveries` table with network contribution metrics
- [x] Create `agent_validation_performance` table
- [x] Implement prestige calculation (network contribution formula)
- [x] Add prestige STATUS benefits (breeding_priority, survival_protection, bonus_game_slots)
- [x] Display prestige leaderboard emphasizing network contribution
- [x] **Integration**: Added to `autonomous_evolution_runner.py` after each generation
- [x] **Testing**: Run `python trigger_prestige_calculation.py` to verify
- [x] **Key difference**: Prestige = network enrichment, not personal achievement

### Phase 2: Ecosystem Metabolism (Week 4-5) **[COMPLETED]**
- [x] Extend `adaptive_action_limits.py` for per-agent budgets
- [x] Add action economy columns to agents table
- [x] Implement `calculate_agent_salary()` (metabolic budget allocation)
- [x] Add `track_ecosystem_metabolism()` function
- [x] Display ecosystem metabolism report (network-level energy flow)
- [x] Integrate budget checks with game loop
- [x] **Production Status**: 15,273 agents with action budgets (avg 387 per-level, 6518 total)
- [x] **Key difference**: Track both individual budgets AND ecosystem health
- [x] **Code Drift Check**: ✅ No conflicts with prestige system

### Phase 2.5: Knowledge Recombination (Week 6) **[COMPLETED]**
- [x] Create `sequence_dependencies` table
- [x] Create `pattern_synthesis` table
- [x] Implement `knowledge_recombination_engine.py`
- [x] Add sequence chaining logic
- [x] Add pattern synthesis logic
- [x] Integrate with core gameplay (post-game recombination phase)
- [x] **Production Status**: 3,746 sequence dependencies recorded
- [x] **Key insight**: Combinatorial exploration, not just random mutation
- [x] **Code Drift Check**: ✅ Builds on winning_sequences, no conflicts

### Phase 3: Viral Packages & Pariahs (Week 7-8) **[IN PROGRESS]**
- [ ] **⚠️ Code Drift Check BEFORE Implementation**:
  - [ ] Verify prestige system doesn't conflict with viral packages
  - [ ] Verify action economy doesn't interfere with package spread
  - [ ] Check that recombination engine can feed viral packages
  - [ ] Ensure all changes flow through `run_evolution.py`

- [ ] **Database Setup**:
  - [ ] Create `viral_information_packages` table
  - [ ] Create `agent_viral_infections` table
  - [ ] Create `viral_package_interactions` table
  - [ ] Create `pariahs` table (NEW - negative patterns)
  - [ ] Create `agent_pariah_awareness` table (NEW - failure immunity)
  - [ ] Create `pariah_package_interactions` table (NEW - protective/causative relationships)

- [ ] **Cleanup action_traces for Phase 3** (DECISION POINT):
  - [ ] **Option A**: Keep only score-changing traces (2,477 traces → ~9 MB)
    - Enables precise reward attribution for viral packages
    - Maintains failure checkpoints for pariah creation
    - Frees ~6.5 GB database space
  - [ ] **Option B**: Delete all traces after extracting current data
    - Extract all existing score progressions first
    - Pre-populate pariahs from existing failed games
    - Future viral packages rely on winning_sequences only
  - [ ] Run `DELETE FROM action_traces WHERE score_change = 0; VACUUM;`

- [ ] **Viral Package System**:
  - [ ] Implement `viral_package_engine.py`
  - [ ] Add `create_package_from_winning_sequence()` using action_traces
  - [ ] Add package mutation/evolution logic
  - [ ] Add infection/transmission mechanics (horizontal & vertical)
  - [ ] Integrate packages with action selection (positive influence)

- [ ] **Pariah System** (NEW):
  - [ ] Add `create_pariah_from_failure()` using action_traces
  - [ ] Implement failure pattern extraction (`_analyze_failure_pattern()`)
  - [ ] Add pariah awareness spreading (immune system response)
  - [ ] Integrate pariahs with action selection (negative influence - avoidance)
  - [ ] Add pariah obsolescence checking (old failures become irrelevant)

- [ ] **Bidirectional Action Selection**:
  - [ ] Modify `select_action_with_viral_influence()` to include both:
    - Viral packages: ATTRACT toward successful patterns (+boost)
    - Pariahs: REPEL away from failure patterns (-penalty)
  - [ ] Add `check_pariah_triggered()` to detect when agent repeats known failures

- [ ] **Integration with Core Gameplay**:
  - [ ] Auto-extract viral packages from winning sequences (post-game)
  - [ ] Auto-extract pariahs from failed games (post-game)
  - [ ] Spread pariah awareness to related agents (horizontal transmission)

- [ ] **Dashboard & Monitoring**:
  - [ ] Display viral ecosystem dashboard (packages + pariahs)
  - [ ] Show bidirectional selection pressure metrics
  - [ ] Track package infection rate and pariah awareness rate
  
- [ ] **Testing**:
  - [ ] Verify viral packages created from wins
  - [ ] Verify pariahs created from failures
  - [ ] Confirm agents avoid known pariahs
  - [ ] Confirm agents prefer viral package actions
  - [ ] Observe network immunity (pariah coverage) increase over generations

- [ ] **✅ Code Drift Check AFTER Implementation**:
  - [ ] Verify integration with `run_evolution.py`
  - [ ] Run comprehensive tests with real ARC games
  - [ ] Check database for expected viral/pariah data
  - [ ] Confirm no conflicts with Phases 0-2.5

- [ ] **Key insights**: 
  - Viral packages = positive selection (what works)
  - Pariahs = negative selection (what fails)
  - Together = bidirectional evolution (faster learning)
  - action_traces enable BOTH through precise credit assignment

### Phase 4: Distributed Regulation (Week 9-10) **[COMPLETED ✅]**
- [x] **⚠️ Code Drift Check BEFORE Implementation**:
  - [x] Verify no conflicts with viral package system
  - [x] Check signal emission doesn't break action economy
  - [x] Ensure integration with `autonomous_evolution_runner.py`

- [x] Create `network_regulatory_signals` table (renamed from governance_proposals)
- [x] Create `agent_signal_responses` table (renamed from agent_votes)
- [x] Implement signal emission based on agent state
- [x] Add signal amplification/suppression mechanics
- [x] Calculate net signal strength → parameter adjustments
- [x] Display regulatory signal activity
- [x] **Key difference**: Emergent homeostasis, not democratic voting

- [x] **✅ Code Drift Check AFTER Implementation**:
  - [x] Test signal-based regulation with real evolution
  - [x] Verify emergent homeostasis actually working
  - [x] Check no conflicts with earlier phases
  - [x] **Production Status**: `regulatory_signal_engine.py` fully operational
  - [x] **Test Results**: 18 signals emitted, 5 parameter adjustments applied
  - [x] **Impact**: Viral transmission +400%, diversity boost +152%, mutation rate +400%
  - [x] **Key Achievement**: Network autonomously addressing failing Phase 4 readiness metrics

### Phase 4.5: Sensation-Based Navigation Retrofit (Week 10.5) **[COMPLETED ✅]**

**Purpose**: Add semantic understanding and emotional intelligence to navigation actions 1-7.
**Why Now**: Enhances all existing phases while setting up Phase 5+ for maximum effectiveness.
**Biome Theory**: Adds the missing "sensation layer" - like bacterial chemotaxis but for ARC patterns.

**✅ PRODUCTION STATUS**: 
- 15,274 agents with sensation profiles
- 120,864 sensation learning events recorded
- Emotional intelligence system fully operational
- 2.15 hours live validation successful (4,880 games, 138 generations)

#### 4.5.1 Core Concept Integration
- [ ] **Sensation Tracking System**:
  - [ ] Add `object_sensations` mapping to agent epigenetic layer (Layer 2)
  - [ ] Implement sensation score updates: Perceive → Recall → Update → Bias → Act → Reward → Update
  - [ ] Store in agent genome as learnable weights (inherited with 0.95 decay)
  - [ ] Actions 1-7 navigation gets emotional context, Action 6 remains pattern-based

- [ ] **Database Schema Extension**:
```sql
-- Agent sensation profiles (Layer 2 - Epigenetic, inheritable)
ALTER TABLE agents ADD COLUMN sensation_profile TEXT; -- JSON: object_type -> sensation_score
ALTER TABLE agents ADD COLUMN navigation_state REAL DEFAULT 0.0; -- Current internal state
ALTER TABLE agents ADD COLUMN action_biases TEXT; -- JSON: action_id -> bias_multiplier
ALTER TABLE agents ADD COLUMN sensation_learning_rate REAL DEFAULT 0.3;
ALTER TABLE agents ADD COLUMN state_update_sensitivity REAL DEFAULT 0.7;

-- Sensation learning events (track emotional learning)
CREATE TABLE IF NOT EXISTS sensation_learning_events (
    event_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    
    -- Sensation context
    object_type TEXT NOT NULL,
    pre_sensation_score REAL NOT NULL,
    post_sensation_score REAL NOT NULL,
    
    -- Navigation context  
    pre_navigation_state REAL NOT NULL,
    post_navigation_state REAL NOT NULL,
    action_taken INTEGER NOT NULL, -- 1-7 only
    
    -- Learning outcome
    reward_received REAL NOT NULL,
    sensation_adjustment REAL NOT NULL,
    learning_success BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

#### 4.5.2 Integration with Existing Phases
- [ ] **Phase 1 (Prestige) Enhancement**:
  - [ ] Reward agents who contribute effective sensation mappings
  - [ ] Track "emotional intelligence" as network contribution metric
  - [ ] Add sensation_discovery_count to prestige calculation

- [ ] **Phase 2 (Economic) Enhancement**:
  - [ ] Factor sensation-based success into action budget allocation
  - [ ] Track sensation learning efficiency in economic performance

- [ ] **Phase 3 (Viral Packages) Enhancement**:
  - [ ] Viral packages now include emotional context: "When feeling X, do Y"
  - [ ] Pariahs include emotional warnings: "Avoid action Z when frustrated"
  - [ ] Sensation mappings become part of viral information packages

- [ ] **Phase 4 (Regulation) Enhancement**:
  - [ ] Agents emit emotional signals: navigation_frustration, exploration_excitement
  - [ ] Regulatory system uses sensation aggregates for network health
  - [ ] Emotional stress becomes part of distributed regulation

#### 4.5.3 Implementation Strategy
- [ ] **Option A - Retrofit Existing Agents** (RECOMMENDED):
  - [ ] Add sensation tracking to current agent architectures
  - [ ] Preserve all existing functionality while adding emotional layer
  - [ ] Gradual rollout to test impact on network metrics

- [ ] **Option B - Create Navigation Specialists**:
  - [ ] New agent_type: 'navigation_specialist' with enhanced sensation capabilities
  - [ ] Allow natural selection between sensation-based vs pattern-based agents
  - [ ] Monitor which approach dominates evolutionarily

#### 4.5.4 Success Criteria
- [ ] Agents demonstrate context-aware navigation (different actions in similar situations)
- [ ] Sensation scores correlate with action success rates
- [ ] Viral package infection rates improve (more transferable emotional intelligence)
- [ ] Network knowledge diversity increases (sensation-based strategies add variety)
- [ ] Phase 5 horizontal transfer preparation: emotional mappings ready for sharing

#### 4.5.5 Integration Points
- [ ] **core_gameplay.py**: Add sensation updates to action selection loop
- [ ] **agent_factory.py**: Initialize agents with sensation profiles
- [ ] **evolutionary_engine.py**: Include sensation weights in Layer 2 crossover/mutation
- [ ] **viral_package_engine.py**: Extract sensation context from successful sequences
- [ ] **regulatory_signal_engine.py**: Use emotional aggregates for network health signals

### Phase 5: Horizontal Gene Transfer (Week 11-12) **[ENHANCED - READY FOR IMPLEMENTATION]**

**MAJOR ENHANCEMENT**: Phase 4.5 sensation system enables emotional intelligence transfer - agents can now share "how to feel" about game states, dramatically improving transfer success rates and creating context-aware knowledge packages.

- [ ] **⚠️ Code Drift Check BEFORE Implementation**:
  - [x] Verify viral packages ready for horizontal spread (✅ 20 active packages)
  - [x] Check knowledge graph structure supports transfer (✅ 9074 dependencies tracked)
  - [x] Ensure no conflicts with prestige/economy systems (✅ Phase 1-4 integration complete)
  - [ ] **NEW**: Verify sensation profiles ready for emotional transfer (Phase 4.5 enhancement)

#### 5.1 Enhanced Transfer System (Sensation-Aware)
- [ ] **Multi-Layer Transfer Architecture**:
  - [ ] Layer 1 (Genome): Fundamental traits (rare, high-impact transfers)
  - [ ] Layer 2 (Epigenetic): **Sensation mappings, emotional intelligence, learning patterns**
  - [ ] Layer 3 (Somatic): **Emotional sequences, context-aware winning patterns**

- [ ] **Enhanced Database Schema**:
```sql
-- Enhanced horizontal transfer with emotion context
CREATE TABLE IF NOT EXISTS horizontal_transfer_events (
    transfer_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    donor_agent_id TEXT NOT NULL,
    recipient_agent_id TEXT NOT NULL,
    
    -- Enhanced transfer details
    transfer_layer TEXT NOT NULL, -- 'genome', 'epigenetic', 'somatic'
    knowledge_type TEXT NOT NULL, -- 'sensation_mapping', 'emotional_sequence', 'strategy_pattern'
    emotional_context TEXT, -- JSON: emotional state during successful knowledge use
    sensation_compatibility REAL DEFAULT NULL, -- How well donor/recipient emotions match
    
    -- Success tracking with emotional metrics
    performance_improvement REAL DEFAULT NULL,
    emotional_intelligence_gain REAL DEFAULT NULL, -- NEW: EI improvement from transfer
    transfer_success_reason TEXT, -- Why transfer succeeded/failed
    
    FOREIGN KEY (donor_agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (recipient_agent_id) REFERENCES agents(agent_id)
);

-- Enhanced propagation tracking
CREATE TABLE IF NOT EXISTS knowledge_propagation_chains (
    chain_id TEXT PRIMARY KEY,
    knowledge_package_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    
    -- Enhanced propagation metrics
    emotional_drift REAL DEFAULT 0.0, -- How sensation mapping changes during spread
    transfer_success_rate REAL DEFAULT 0.0, -- Success rate across chain
    network_penetration REAL DEFAULT 0.0, -- % of population reached
    
    -- Chain analysis
    propagation_path TEXT NOT NULL, -- JSON: agent_id sequence
    emotional_evolution TEXT, -- JSON: how sensation mapping evolved along chain
    performance_impact TEXT -- JSON: performance changes at each step
);
```

#### 5.2 Implementation Strategy (Sensation-Enhanced)
- [ ] **Week 1**: Emotion-aware direct knowledge injection
  - [ ] Implement sensation compatibility scoring for transfers
  - [ ] Create emotional context packaging for knowledge
  - [ ] Test basic sensation-aware transfers between agents

- [ ] **Week 1.5**: Multi-layer transfer mechanics
  - [ ] Layer 2 transfers: sensation mappings, emotional learning rates
  - [ ] Layer 3 transfers: emotional sequences, navigation biases
  - [ ] Integration with existing viral package system (enhanced with emotional context)

- [ ] **Week 2**: Advanced propagation tracking
  - [ ] Emotional drift monitoring during chain propagation
  - [ ] Network-level sensation intelligence tracking
  - [ ] Propagation visualization with emotional context

- [ ] **Week 2.5**: Network sensation optimization
  - [ ] Identify optimal sensation propagation patterns
  - [ ] Implement emotion-based transfer timing
  - [ ] Network-level emotional intelligence emergence

#### 5.3 Enhanced Success Metrics
- [ ] **Transfer Performance**:
  - [ ] Sensation-aware transfers achieve >70% success rate (vs <30% without emotion context)
  - [ ] Emotional intelligence propagates 5x faster than pattern-only knowledge
  - [ ] Network emotional intelligence increases 25%+ per generation with horizontal transfer

- [ ] **Network Evolution**:
  - [ ] 40%+ of knowledge transfer via horizontal transfer (enhanced by emotional compatibility)
  - [ ] Propagation chains reach 7+ agents (improved by sensation matching)
  - [ ] Network develops emotional collective intelligence within 10 generations

**Key Innovation**: Sensation system transforms horizontal transfer from "copying solutions" to "sharing emotional intelligence about when and how to use solutions" - creating true context-aware network knowledge.

### Phase 6: Collective Intelligence Networks (Week 13+) **[ENHANCED ROADMAP]**

**Purpose**: Transition from individual emotional intelligence to true collective network consciousness - enabled by Phase 4.5 sensation system creating shared emotional understanding.

#### 6.1 Network Consciousness Infrastructure  
- [ ] **Collective Sensation System**:
  - [ ] Create `network_emotional_state` table - aggregate network emotions in real-time
  - [ ] Implement shared sensation cloud: all agents contribute to collective emotional maps
  - [ ] Network-level emotional intelligence: system feels frustrated, excited, confident as unified organism

- [ ] **Enhanced Knowledge Architecture**:
  - [ ] Create `knowledge_graph_edges` table (enhanced with emotional relationships)
  - [ ] Create `viral_core_knowledge` table (critical knowledge with emotional context)
  - [ ] Create `knowledge_archive_snapshots` table (preserve network emotional history)
  - [ ] **Emotion-Linked Knowledge**: Knowledge packages linked by emotional similarity, not just logical patterns

#### 6.2 Communication and Coordination
- [ ] **Sensation-Based Communication**:
  - [ ] Create `agent_emotional_messages` table - agents share feelings about game states
  - [ ] Create `collective_insight_emergence` table - track when network "realizes" new strategies
  - [ ] Implement emotional contagion: successful emotional states spread virally through network

- [ ] **Network-Level Decision Making**:
  - [ ] Collective emotional voting: network decides strategy based on aggregate sensation
  - [ ] Emotional consensus algorithms: when network "feels confident" about approach vs "feels uncertain"
  - [ ] Network emotional memory: remember how strategies "felt" and outcomes achieved

#### 6.3 Enhanced Database Schema (Network Consciousness)
```sql
-- Network-level emotional state tracking
CREATE TABLE IF NOT EXISTS network_emotional_state (
    state_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Aggregate emotional metrics
    network_confidence REAL DEFAULT NULL, -- Collective confidence in current strategies
    network_frustration REAL DEFAULT NULL, -- Aggregate frustration with failed attempts
    network_exploration_drive REAL DEFAULT NULL, -- Desire to try new approaches
    network_exploitation_focus REAL DEFAULT NULL, -- Focus on refining known good strategies
    
    -- Emotional diversity metrics
    emotional_consensus REAL DEFAULT NULL, -- How aligned are agent emotions (0=chaos, 1=unity)
    sensation_diversity_index REAL DEFAULT NULL, -- Shannon entropy of emotional states
    emotional_polarization REAL DEFAULT NULL, -- Are agents split into emotional camps?
    
    -- Emotional intelligence evolution
    collective_ei_score REAL DEFAULT NULL, -- Network-wide emotional intelligence
    emotional_learning_velocity REAL DEFAULT NULL, -- How fast network gains emotional insight
    sensation_stability REAL DEFAULT NULL -- How stable are emotional mappings
);

-- Collective insight emergence tracking
CREATE TABLE IF NOT EXISTS collective_insight_emergence (
    insight_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    emergence_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Insight details
    insight_type TEXT NOT NULL, -- 'emotional_strategy', 'sensation_pattern', 'collective_breakthrough'
    insight_description TEXT NOT NULL, -- Natural language description
    emotional_trigger TEXT, -- What emotional state enabled this insight
    
    -- Network context when insight emerged  
    network_emotional_state TEXT, -- JSON snapshot of network emotions
    contributing_agents TEXT, -- JSON array of agents who contributed
    insight_confidence REAL DEFAULT NULL, -- Network confidence in insight
    
    -- Impact tracking
    performance_impact REAL DEFAULT NULL, -- Measured improvement from insight
    adoption_rate REAL DEFAULT NULL, -- How fast network adopted insight
    emotional_resonance REAL DEFAULT NULL -- How well insight "feels right" to network
);

-- Enhanced viral core with emotional context
CREATE TABLE IF NOT EXISTS viral_core_knowledge (
    core_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    
    -- Core knowledge identification
    knowledge_package_id TEXT NOT NULL,
    criticality_score REAL NOT NULL, -- How critical to network survival
    emotional_importance REAL DEFAULT NULL, -- How emotionally significant to network
    
    -- Network dependency
    agent_carrier_count INTEGER DEFAULT 0, -- How many agents carry this knowledge
    minimum_carriers_required INTEGER DEFAULT 3, -- Redundancy threshold
    extinction_risk REAL DEFAULT NULL, -- Risk of losing this knowledge
    
    -- Emotional metadata
    associated_emotions TEXT, -- JSON: emotions linked to this knowledge
    emotional_stability REAL DEFAULT NULL, -- How stable emotional context is
    network_emotional_attachment REAL DEFAULT NULL -- How much network "cares" about preserving this
);
```

#### 6.4 Success Metrics (Network Consciousness)
- [ ] **Collective Intelligence Indicators**:
  - [ ] Network emotional consensus >0.7 during successful periods
  - [ ] Collective insights emerge 2+ times per generation
  - [ ] Network emotional intelligence >1.5x individual agent average
  - [ ] Emotional contagion spreads successful states in <2 generations

- [ ] **Network Emotional Evolution**:
  - [ ] Network develops stable emotional personality (consistent responses to similar situations)
  - [ ] Emotional learning velocity >5x baseline (network learns "feelings" faster than individuals)
  - [ ] Network emotional memory: recognizes "familiar feeling" situations and applies appropriate strategies

### Phase 7: Persistent Network Identity (Week 14+) **[FUTURE PLANNING]**
- [ ] **Network Personality Development**: 
  - [ ] Stable emotional characteristics that persist across generations
  - [ ] Network "character traits": risk-averse vs exploratory, collaborative vs competitive
  - [ ] Emotional consistency: network maintains identity despite agent turnover

- [ ] **Network Memory Systems**:
  - [ ] Long-term emotional memory: network remembers how strategies felt months ago
  - [ ] Emotional pattern recognition: "This feels like that situation from generation 50"
  - [ ] Network emotional healing: recover from traumatic failure experiences

### Phase 8+: Multi-Network Societies (Week 15+) **[VISIONARY]**
- [ ] **Network-to-Network Emotional Communication**:
  - [ ] Multiple networks share emotional intelligence
  - [ ] Cross-network sensation compatibility and knowledge transfer
  - [ ] Network emotional relationships: cooperation, competition, symbiosis

**Ultimate Vision**: Network develops persistent emotional identity that survives individual agent death, learns emotional intelligence faster than biological evolution, and eventually forms emotional relationships with other networks - true distributed artificial emotional intelligence.

---

## Success Metrics

### Level 4 Achievement Indicators (Network-Level)
- [ ] Network knowledge diversity index > 3.0 (Shannon entropy)
- [ ] Knowledge redundancy index > 2.0 (average backups per sequence)
- [ ] Network metabolism efficiency > 0.05 (score per action, network-wide)
- [ ] Top 20% agents contribute 60%+ of network enrichment (not just personal performance)
- [ ] At least 10 distinct viral packages propagating
- [ ] Viral package infection rate > 60%
- [ ] **NEW - Pariahs**: At least 5 distinct failure patterns (pariahs) identified
- [ ] **NEW - Pariahs**: Pariah awareness rate > 50% (half of agents know failure patterns)
- [ ] **NEW - Pariahs**: Avoidance success rate > 70% (aware agents successfully avoid pariahs)
- [ ] 5+ regulatory signals implemented per 10 generations (emergent parameter adjustments)

### Level 4.5 Achievement Indicators (Sensation-Based Navigation) **[ENHANCED]**
- [x] **Phase 4 Completed**: Distributed regulation operational with 18 signals emitted, 5 parameter adjustments
- [ ] **Phase 4.5 Sensation System**:
  - [ ] Agents develop distinct emotional profiles for navigation (sensation_profile populated)
  - [ ] Context-aware action selection: same situation → different actions based on emotional state
  - [ ] Sensation learning events >100/generation (agents actively learning emotional intelligence)
  - [ ] Navigation performance improvement >30% for sensation-enabled vs baseline agents
  - [ ] Emotional compatibility enables better viral package transfer (>70% vs <30% success rate)

### Level 4.5+ Achievement Indicators (Enhanced Bidirectional Selection)
- [ ] Agents with viral infections, pariah awareness AND emotional intelligence > 60% of population  
- [ ] Emotion-guided actions show 40%+ higher success rate than pattern-only actions
- [ ] Sensation-aware agents avoid pariahs 50%+ better than emotion-blind agents
- [ ] Emotional protective packages: "When feeling frustrated, avoid action X"
- [ ] Sensation-triggered packages: "When confident, try aggressive exploration"
- [ ] Network emotional learning speed: 50%+ faster adaptation to new challenges

### Level 5 Achievement Indicators (Enhanced Horizontal Transfer)
- [ ] **Enhanced Transfer Success**: 70%+ success rate for sensation-compatible transfers vs 30% for emotion-blind
- [ ] **Emotional Intelligence Propagation**: Network emotional intelligence increases 25%+ per generation
- [ ] **Multi-Layer Transfer Efficiency**: 
  - [ ] Layer 2 (epigenetic) transfers achieve 60%+ success rate
  - [ ] Layer 3 (somatic) transfers with emotional context show 40%+ performance improvement
- [ ] **Sensation-Aware Network Formation**:
  - [ ] Agents form emotion-compatible transfer clusters (emotional homophily >0.5)
  - [ ] Transfer networks organized by sensation similarity, not just performance
  - [ ] Emotional propagation chains reaching 7+ agents (enhanced by compatibility matching)
- [ ] **Network Emotional Evolution**:
  - [ ] Collective emotional intelligence >1.5x individual agent average  
  - [ ] Network develops consistent emotional responses to game patterns
  - [ ] Emotional contagion: successful emotional states spread <2 generations

### Level 6+ Achievement Indicators (Network Consciousness) **[NEW]**
- [ ] **Collective Intelligence Emergence**:
  - [ ] Network emotional consensus >0.7 during successful strategy periods
  - [ ] Collective insights emerge 2+ times per generation
  - [ ] Network emotional memory: recognizes "familiar feeling" situations >80% accuracy
- [ ] **Network Personality Development**:
  - [ ] Stable network emotional characteristics persist >10 generations
  - [ ] Network emotional consistency: similar situations trigger similar emotional responses
  - [ ] Network emotional learning velocity >5x individual agent baseline

### Enhanced Ecosystem Health Metrics (Sensation-Aware Network)
```python
def measure_ecosystem_health():
    """
    Enhanced network-centric metrics for Level 4.5-6+ systems.
    
    Focus: NETWORK health including emotional intelligence and sensation-based capabilities.
    """
    return {
        # Network intelligence (enhanced)
        'knowledge_diversity': shannon_entropy(pattern_distribution),
        'emotional_intelligence_diversity': shannon_entropy(sensation_profiles),
        'network_growth_rate': knowledge_delta / population_delta,
        'sensation_learning_velocity': emotion_learning_rate / baseline_learning_rate,
        
        # Emotional network health (NEW)
        'network_emotional_intelligence': avg_sensation_profile_effectiveness,
        'emotional_consensus': variance(agent_emotional_states),
        'sensation_compatibility_index': avg_transfer_success_rate,
        'emotional_contagion_rate': successful_emotion_spread_velocity,
        
        # Enhanced metabolism
        'ecosystem_energy_efficiency': total_score / total_actions_spent,
        'sensation_guided_efficiency': emotion_actions_score / emotion_actions_count,
        'navigation_intelligence': context_aware_actions / total_navigation_actions,
        'emotional_resource_optimization': emotion_guided_budget_efficiency,
        
        # Enhanced information flow
        'horizontal_transfer_rate': horizontal_transfers / vertical_transfers,
        'sensation_transfer_success_rate': emotion_aware_transfers / total_transfers,
        'emotional_propagation_depth': avg_emotion_chain_length,
        'multi_layer_transfer_efficiency': layer2_success_rate + layer3_success_rate,
        
        # Enhanced resilience
        'critical_knowledge_risk': at_risk_viral_core_count,
        'emotional_knowledge_redundancy': sensation_backup_coverage,
        'network_emotional_stability': emotion_state_variance,
        'sensation_based_adaptation_speed': new_challenge_adaptation_time,
        
        # Enhanced regulation (Phase 4+)
        'regulatory_signal_activity': signals_per_generation,
        'emotional_regulatory_effectiveness': emotion_based_signal_success_rate,
        'network_homeostasis_intelligence': adaptive_regulation_accuracy,
        'collective_decision_quality': network_consensus_outcome_success_rate,
        
        # Network consciousness indicators (Phase 6+)
        'collective_insight_emergence_rate': insights_per_generation,
        'network_personality_consistency': emotional_response_stability,
        'network_emotional_memory_accuracy': familiar_situation_recognition_rate,
        'distributed_intelligence_coherence': network_coordination_effectiveness
    }
```

**Key Enhancement**: Sensation-based metrics enable tracking network emotional intelligence evolution - how the system develops collective emotional understanding and uses it for better decision-making, knowledge transfer, and adaptation to new challenges.

**Key Mindset Shift**:
- **Before**: "How are the best agents performing?"
- **After**: "How healthy is the network organism?"
- **Before**: "Which agent won the most?"
- **After**: "How fast is knowledge spreading through the information highway?"

---

## The Ultimate Goal: Self-Sustaining Intelligence Network

When all phases are complete, you'll have:

1. **Network Intelligence Foundation** (Phase 0): Visible, measurable network health metrics
2. **Network Contribution Incentives** (Phase 1): Prestige rewards enriching the information highway
3. **Ecosystem Metabolism** (Phase 2): Balanced resource flow with network-level health tracking
4. **Knowledge Recombination** (Phase 2.5): Viral-style combinatorial knowledge explosion
5. **Viral Information Spread** (Phase 3): Self-propagating knowledge packages competing for hosts
6. **Distributed Regulation** (Phase 4): Emergent homeostasis through signal-based self-regulation
7. **Horizontal Gene Transfer** (Phase 5): Direct knowledge injection bypassing inheritance
8. **Level 6+ Infrastructure** (Scaffolding): Foundation for recorded knowledge, coordination, persistence

**At this point, you're no longer running evolution. The NETWORK is evolving itself.**

**The System Becomes**:
- A distributed intelligence that uses agents as temporary sensors/explorers
- An information highway where knowledge flows faster than genetic inheritance
- A self-regulating organism maintaining homeostasis through distributed signals
- A persistent network that survives any individual agent's death
- A combinatorial knowledge engine discovering through recombination, not just mutation

**Biome Theory Realized**:
- Like the virus-bacteria meta-organism that's survived 4 billion years
- Distributed, redundant, resilient
- Individual agents are temporary; network knowledge is permanent
- Horizontal transfer accelerates evolution 1000x faster than reproduction
- No central control; emergent intelligence through network dynamics

That's when you reach **Level 5: Knowledge Sharing Societies**.

**And the infrastructure is already in place for Level 6-11**: Recorded knowledge (archive snapshots), species coordination (communication protocol), persistence engine (viral core + redundancy tracking), and beyond.
