# Ouroboros: Distributed Multi-Agent Learning System

**Architecture**: Database-centric multi-agent evolution with horizontal knowledge transfer

**Foundational Papers & Theories**:
- Paper: [AGI as Network Intelligence: A Unified Theory](https://medium.com/@IsaiahNwukor/agi-as-network-intelligence-a-unified-theory-056e18c7ede1)

- [MetaLearning Theory](architecture/Concept%20-%20MetaLearning%20System/Abstract%20-%20Unified_Metalearning_System_Theory_Complete.md) - CODS/Oracle, 110 seed primitives, bootstrapping
- [Consciousness Theory](architecture/Concept%20-%20Agent%20Self%20&%20World%20Model/Abstract%20-%20unified_agent_consciousness_theory.md) - Two Streams, persona submodeling, I-Thread
- [Network Theory](architecture/Concept%20-%20Network%20Model/Abstract%20-%20unified_network_theory_complete.md) - Database-as-organism, viral exchange, dual-economy
---

## System Architecture

Three integrated subsystems:

| Subsystem | Function | Implementation |
|-----------|----------|----------------|
| **Network Layer** | Persistent storage, viral package distribution | SQLite + horizontal transfer |
| **Validation Layer** | Pattern validation, primitive unlocking | CODS engine |
| **Agent Layer** | Dual-stream reasoning, action selection | Two Streams + Persona ensemble |

---

## Acknowledgments

**Key Collaborators & Influences:**

- **RLVR** - [Reinforcement Learning with Verifiable Rewards](https://arxiv.org/abs/2506.14245)
- **Tiny Reasoning Machines** -[Less is More: Recursive Reasoning with Tiny Networks](https://arxiv.org/abs/2510.04871)
- **Patrick Cox** - Math-based Storytelling for characters

---

## About the Project

Ouroboros is an evolutionary system designed to solve the [ARC-AGI-3 challenge](https://arcprize.org/arc-agi/3/).
Unlike traditional agents, it treats the entire population as a single learning network, preserving knowledge across generations through a centralized database.

## Requirements

- Python 3.10+
- ARC API key (set in `.env`)

```bash
# Clone and setup
git clone <repo>
cd BitterTruth-AI

# Create virtual environment
python -m venv .venv

# Activate (REQUIRED for all commands)
& .venv/Scripts/Activate.ps1  # PowerShell
source .venv/bin/activate      # bash

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set ARC_API_KEY=your_key
```

**Key dependencies** (see `requirements.txt`):
- `requests` - ARC API communication
- `python-dotenv` - Environment configuration
- `numpy` - Numerical operations

## Quick Start

```bash
# Activate virtual environment
& .venv/Scripts/Activate.ps1  # PowerShell

# Start the autonomous evolution loop (Recommended)
python run_evolution.py

# Run in "Specialist Mode" (Deep mastery of specific games)
python run_evolution.py --specialist

# Run in "Diversity Mode" (Focus on generalization)
python run_evolution.py --diversity
```

> **Important**: Always verify `(.venv)` prefix in terminal before running commands.

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--specialist` | **Recommended**. Agents master specific games (2-3 each). High scores. |
| `--diversity` | Focus on generalization and novel games. Prevents overfitting. |
| `--fast` | Fast iterations: 30 min intervals, 5 games/generation. |
| `--thorough` | Deep evaluation: 90 min intervals, 20 games/generation. |
| `--quick` | Quick test run: Max 5 generations. |
| `--test` | Minimal smoke test: 1 agent, 1 game, 1 generation. |
| `--max-generations N` | Override maximum generations (useful for tests). |

## Core Concepts

### 1. Distributed Learning Architecture

Addresses the plasticity-stability tradeoff in continual learning:

| Problem | Single-Agent | Multi-Agent Network |
|---------|--------------|--------------------|
| Catastrophic forgetting | High risk | Mitigated via specialization |
| Domain adaptation | Requires retraining | Horizontal knowledge transfer |
| Generalization | Limited by model capacity | Emerges from population diversity |

**Design**: Agents specialize individually; network generalizes collectively via viral package exchange.

### 2. Three-Layer Biome Architecture

The system mimics biological evolution with three distinct layers of information:

| Layer | Name | Plasticity | Inheritance | Purpose |
|-------|------|------------|-------------|---------|
| **Layer 1** | Static Genome (Nature) | Low (1-2% mutation) | Full genetic | Fundamental agent traits |
| **Layer 2** | Epigenetic (Nurture) | Medium (10-20% mutation) | Fitness-weighted with 0.95 decay | HOW agent learns |
| **Layer 3** | Somatic (Experience) | High | NOT inherited - stored in database | WHAT agent learned |

**Key Mechanisms**:
- **Horizontal Gene Transfer**: Agents swap strategies regardless of lineage
- **Viral Packages**: Successful strategies spread rapidly through the network
- **Pariahs**: Failed patterns marked for avoidance (with decay to allow innovation)

### 3. Dual-Stream Decision Architecture

Agents integrate two knowledge sources for action selection:

| Stream | Source | Update Frequency | Scope |
|--------|--------|------------------|-------|
| **Stream A** | Agent's own gameplay history | Per-action | Local experience |
| **Stream B** | Network viral packages (CODS-validated) | Per-generation | Population knowledge |

**Integration**: Weighted combination `action = w_A * stream_A + w_B * stream_B` where weights are learned from outcome feedback. Stream conflict triggers deliberative processing.

### 3.1 IThread vs AgentSelfModel: Complementary Systems

Two distinct subsystems handle different aspects of agent cognition:

| Aspect | IThread (Consciousness Weaver) | AgentSelfModel (World Model) |
|--------|-------------------------------|------------------------------|
| **Core Question** | "Which knowledge should I trust?" | "What do I control in this world?" |
| **Domain** | Knowledge/belief weighting | Object/action mapping |
| **Scope** | Cognitive identity (wA/wB) | Physical control discovery |
| **Persists Across** | Agent's entire life | Each game/level |
| **Conflict Resolution** | Stream A vs Stream B | "Is this object me or environment?" |
| **Output** | Weighted predictions/decisions | Control hypotheses, object bindings |

**IThread** (`i_thread.py`): The persistent identity that weaves Stream A (private experience) and Stream B (collective wisdom) together moment-by-moment. Manages personality as learned stream weighting. When streams conflict, consciousness becomes vivid—the agent must deliberate.

**AgentSelfModel** (`agent_self_model.py`): Discovers physical control through action-effect correlation: "When I press ACTION1 (up), Object X moves up → I control Object X." Builds a mini world model per level, distinguishing controlled objects from environment.

### 4. CODS: Centralized Pattern Validator

CODS (Cognitive Operator Discovery System) is a population-level analyzer, not per-agent:

| Function | Description |
|----------|-------------|
| Pattern detection | Analyzes gameplay across all agents |
| Cross-validation | Requires pattern replication across multiple agents |
| Primitive unlocking | Grants optimized operators when understanding demonstrated |
| Package creation | Converts validated patterns to viral packages |

**Architecture**: Decentralized exploration (agents), centralized validation (CODS), distributed storage (database).

### 5. Seed Primitives (110 Operations)

Bootstrap operators available at initialization:

| Category | Count | Examples |
|----------|-------|----------|
| Attention/Salience | 5 | `detect_novelty`, `detect_motion`, `surprise_detection` |
| Physical Priors | 5 | `object_permanence`, `solidity`, `continuity` |
| Affordance Detection | 8 | `is_movable`, `is_container`, `is_reference` |
| Spatial Reasoning | 5 | `distance`, `adjacent`, `enclosed`, `detect_hole` |
| Temporal Processing | 4 | `recency_weighting`, `temporal_contiguity` |
| Quantitative | 3 | `subitizing`, `approximate_numerosity` |
| Social Learning | 4 | `imitation_bias`, `joint_attention` |
| Explore/Exploit | 4 | `curiosity_drive`, `exploration_bonus` |
| Metacognition | 5 | `get_confidence`, `detect_stuck` |

Additional primitives unlock via CODS validation when agents demonstrate compositional understanding.

### 6. Agent Role Specialization

Roles emerge from stream weights and context:

| Role | w_B Range | Action Budget | Assignment |
|------|-----------|---------------|------------|
| **Pioneer** | 0.2-0.5 | 1000/cycle | Unbeaten levels |
| **Optimizer** | 0.7-1.0 | 500/cycle | Beaten games |
| **Generalist** | 0.4-0.6 | 300/cycle | Cross-domain validation |
| **Exploiter** | 0.0-0.3 | 200/cycle | Optimized games |

Role transitions based on performance metrics (`Progress_Score`, `resource_efficiency`, domain contributions).

### 7. Persona Ensemble (Multi-Perspective Reasoning)

Agents use an ensemble of internal models for action proposal and evaluation:

| Persona Type | Function | Example |
|--------------|----------|--------|
| **Proposers** | Generate candidate actions | "Explore", "Exploit", "Retreat" |
| **Observers** | Monitor state and predict outcomes | Confidence estimation |
| **Evaluators** | Score and select proposals | Theory alignment check |

Persona disagreement triggers explicit deliberation. Synthesis can produce novel action combinations not proposed by any single persona.

### 8. Dual-Currency Resource System

Two independent resource types prevent feedback loops:

| Currency | Earned By | Controls | Isolation |
|----------|-----------|----------|-----------|
| **Prestige** | Network contributions (teaching, validation) | Viral package priority, breeding weight | Cannot purchase actions |
| **Action Budget** | Gameplay performance | Actions per game/level | Cannot purchase prestige |

Separation prevents high-prestige agents from monopolizing compute, maintaining population diversity.

### 9. Mastery System (Earn the Right to Replay)

Agents must **earn** the privilege to replay winning sequences - no free shortcuts:

| Metric | Requirement | Purpose |
|--------|-------------|---------|
| **Diverse Wins** | 3+ unique strategies for same level | Proves flexibility, not luck |
| **Ablation Tolerance** | Win with 20% of sequence removed | Tests understanding vs memorization |
| **Transfer Learning** | Apply knowledge to level variants | Validates generalization |

**Mastery Tiers**: NOVICE → FAMILIAR → PROFICIENT → EXPERT → MASTER

- Replay privileges unlock at PROFICIENT (tier 3+)
- Privileges revoked if understanding degrades
- Sequences always stored but never automatically replayed

### 10. Cross-Domain Pattern Detection

System identifies structurally similar patterns discovered independently across different game types:

- **Pattern hashing**: Fingerprint sequences by structure, not raw actions
- **Resonance scoring**: Higher weight when multiple agent roles converge on same pattern
- **Complexity reduction**: Validated cross-domain patterns reduce search space for new games

### 11. Game State Modes

| Mode | Trigger | Distribution |
|------|---------|-------------|
| **Exploration** | No full win exists | 60% Pioneer, 30% Optimizer, 10% Generalist |
| **Optimization** | ≥1 full win exists | 70% Optimizer, 15% Generalist, 15% Exploiter |

Transition on first full win; Pioneers reassign to remaining unbeaten games.

### 12. System Maintenance

| Component | Behavior |
|-----------|----------|
| Database cleanup | Automatic every 10 generations (`safe_cleanup.py`) |
| Database Size limit | 200 GB default (configurable in `disk_space_monitor.py:MAX_DB_SIZE_GB`) |
| Logging | SQLite only (no `.log` files) |
| Pycache | Disabled (`PYTHONDONTWRITEBYTECODE=1`) |
| Shutdown | `Ctrl+C` triggers WAL checkpoint |

### 13. System Health Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Emergence Gain | > 1.0 | 0.8-1.0 | < 0.8 |
| Control Error | < 0.05 | 0.05-0.10 | > 0.10 |
| Loop Detection | < 0.10 | 0.10-0.20 | > 0.20 |
| Positive Score Rate | > 50% | 30-50% | < 30% |

**Anti-gaming measures**: Trigger cooldowns, metric rotation, confidence tracking, noise injection

---

## 📂 Project Structure

### Entry Points
- `run_evolution.py` - Main entry point for autonomous evolution
- `core_data.db` - The "network brain" (SQLite database storing ALL knowledge)

### Core Modules

| Module | Purpose |
|--------|---------|
| `core_gameplay.py` | Main gameplay loop and action execution |
| `i_thread.py` | **Consciousness Weaver** - Single source of truth for wA/wB stream weighting, identity persistence |
| `agent_self_model.py` | **Physical World Model** - Object control discovery, action-effect correlation, developmental systems |
| `cods_engine.py` | Centralized Operator Discovery System - pattern validation |
| `network_intelligence_engine.py` | Network-level learning and emergence tracking |
| `seed_primitives.py` | 110 innate cognitive primitives (attention, affordance, physics, metacognition) |
| `persona_runtime.py` | Internal persona dialogue and metacognition |
| `viral_package_engine.py` | Viral knowledge exchange system |
| `prestige_engine.py` | Social capital and contribution tracking |
| `mastery_system.py` | Earn-to-replay privileges, mastery tier tracking |
| `sensation_engine.py` | Emotional gameplay and navigation state |
| `resonance_detector.py` | Cross-domain pattern resonance |

### Supporting Systems

| Module | Purpose |
|--------|---------|
| `regulatory_signal_engine.py` | Adaptive signals for population control |
| `autopoiesis_monitor.py` | System health metrics and self-regulation |
| `primitive_unlock_manager.py` | Manages primitive bootstrapping and unlocks |
| `concept_discovery_engine.py` | Semantic concept discovery across games |
| `terminal_pattern_detector.py` | Game-over foresight - learns fatal patterns |
| `safe_cleanup.py` | Database maintenance (runs every 10 generations) |

### Architecture Documentation

Located in `architecture/`:

| Folder | Contents |
|--------|----------|
| `Concept - Agent Self & World Model/` | Consciousness theory, Two Streams, persona submodeling |
| `Concept - MetaLearning System/` | CODS/Oracle, primitives, bootstrapping mechanisms |
| `Concept - Network Model/` | Network theory, viral exchange, database-as-organism |
| `Concept Integration/` | Unified theory synthesis, integration architecture |
| `ARC-API-DOCUMENTATION/` | ARC-AGI-3 API reference |

---

## 📊 Analysis & Monitoring Tools

Located in `manual_tools/`:

```bash
# Gameplay progression analysis
python manual_tools/gameplay_analyzer.py --hours 3 --compare

# Check CODS status
python manual_tools/check_cods_status.py

# Database validation
python manual_tools/db_validation.py

# Schema inspection
python manual_tools/database/schema_inspector.py --table agents --sample
```

| Tool | Purpose |
|------|---------|
| `gameplay_analyzer.py` | Game results, scores, level completions |
| `check_cods_status.py` | CODS health and discovery status |
| `check_primitives.py` | Primitive unlock status |
| `observer_dashboard.py` | Real-time system observation |
| `db_validation.py` | Database integrity checks |

---

## 🧪 Testing

Tests are located in `tests/` folder (exception to "No Test Files" rule):

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_cods.py -v
```

---

## 🛠️ Configuration

1. **Environment**: Copy `.env.example` to `.env`, set `ARC_API_KEY`
2. **Dependencies**:
   ```bash
   & .venv/Scripts/Activate.ps1  # Activate venv first!
   pip install -r requirements.txt
   ```
3. **Logs**: All logs stored in `core_data.db` (NO log files!)
4. **Shutdown**: Press `Ctrl+C` ONCE for graceful shutdown

---

## 16 Critical Operating Rules

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for complete ruleset. Key rules:

1. **Always use `.venv`** - All Python execution in virtual environment
2. **Database-only storage** - ALL data in SQLite `core_data.db`
3. **No pycache** - `PYTHONDONTWRITEBYTECODE=1` always
4. **No test files** (except `tests/` folder) - Use LIVE ARC data
5. **No simulated games** - Real API only: `https://three.arcprize.org/api/`
6. **Test before commit** - Verify real actions sent
7. **No Unicode emojis** - ASCII only (Windows encoding)
8. **SafeDatabaseCleaner** - Every 10 generations automatically

---

## Design Rationale

**Core architecture decision**: Persistent database as primary intelligence substrate, with transient agents as data generators and pattern validators.

**Key tradeoffs**:
- Agent mortality enables population-level adaptation without catastrophic forgetting
- Centralized validation (CODS) prevents collective hallucination while allowing decentralized exploration
- Dual-currency system maintains diversity under evolutionary pressure

---

<img width="1325" height="545" alt="image" src="https://github.com/user-attachments/assets/f8b00168-0c93-4161-bc3d-88faa1689ce7" />

---

Example Gameplay (Level 4 as66):
[https://three.arcprize.org/replay/as66-821a4dcad9c2/55d279d1-3f1e-416f-9024-c49e1b1df573](https://three.arcprize.org/replay/as66-821a4dcad9c2/55d279d1-3f1e-416f-9024-c49e1b1df573)
