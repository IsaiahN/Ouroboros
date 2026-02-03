# Ouroboros: Distributed Multi-Agent Learning System

**Architecture**: Database-centric multi-agent evolution with horizontal knowledge transfer

**Foundational Papers & Theories**:
- Paper: [AGI as Network Intelligence: A Unified Theory](https://medium.com/@IsaiahNwukor/agi-as-network-intelligence-a-unified-theory-056e18c7ede1)

---

## System Architecture

Three integrated subsystems:

| Subsystem | Function | Implementation |
|-----------|----------|----------------|
| **Storage Layer** | Persistent knowledge, game results | SQLite database |
| **Decision Layer** | Action selection via weighted rungs | 42-rung Decision System + Two Streams (wA/wB) |
| **Evolution Layer** | Population management, fitness selection | Evolutionary engine + Agents |

---

## Acknowledgments

- **ARC-AGI** - [Francois Chollet's ARC Prize](https://arcprize.org/) - The challenge driving this project
- **RLVR** - [Reinforcement Learning with Verifiable Rewards](https://arxiv.org/abs/2506.14245) - Core feedback mechanism
- **Johan Land** - [beetree/ARC-AGI](https://github.com/beetree/ARC-AGI) - Two-stage decomposition and sparse grid insights

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
- `arc-agi` - Official ARC-AGI-3 SDK
- `python-dotenv` - Environment configuration
- `numpy`, `pandas` - Data operations
- `torch` - Learned representations
- `aiohttp` - Async HTTP

## Quick Start

```bash
# Activate virtual environment
& .venv/Scripts/Activate.ps1  # PowerShell

# Quick test (1 agent, 1 game, 1 generation)
python evolution_runner.py --mode=offline --test --game=ls20

# Run with verbose output (see each action)
python evolution_runner.py --mode=offline --test --game=ls20 --verbose

# Full evolution run (offline mode)
python evolution_runner.py --mode=offline --population=10 --max-generations=50

# Online mode (submits to ARC scorecards)
python evolution_runner.py --mode=online
```

> **Important**: Always verify `(.venv)` prefix in terminal before running commands.

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--mode` | Operation mode: `offline` (local only), `online` (scorecards), `normal` (both) |
| `--test` | Minimal smoke test: 1 agent, 1 game, 1 generation |
| `--verbose`, `-v` | Show each action and score during gameplay |
| `--game GAME` | Target specific game (e.g., `--game=ls20`) |
| `--population N` | Number of agents (default: 10) |
| `--max-generations N` | Maximum generations (default: 100) |
| `--games-per-gen N` | Games per agent per generation (default: 3) |
| `--max-actions N` | Max actions per game (default: 500) |

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

### 3. Decision Rung System (Action Selection)

The core intelligence is a **42-rung modular decision ladder**. Each rung is a pluggable component that can propose actions with confidence scores.

**Strategies**:
- **LADDER**: First confident answer wins (fast, deterministic)
- **WEIGHTED**: All rungs vote, weighted sum decides (thorough)
- **PHASED**: Different orderings for orientation/hypothesis/exploitation phases

**Rung Categories**:

| Category | Purpose | Example Rungs |
|----------|---------|---------------|
| **Orientation** | Understand current state | Survey, Questioning, ExplorationPhase |
| **Filter** | Avoid bad actions | DeathAvoidance, PriorLessons, InfiniteLoopBreaker |
| **Hypothesis** | Test theories | ScientificMethod, TheoryGate, TwoStreams |
| **Exploitation** | Use known patterns | NetworkWisdom, FrontierTopology, AbstractionTemplates |
| **Emergency** | Break stuck states | InfiniteLoopBreaker, SmartActionSelection |
| **Fallback** | Default when nothing else works | RandomExploration |

**Key Rungs**:
- `DeathAvoidanceRung` - Learns fatal patterns, prevents game-over
- `PriorLessonsRung` - Applies lessons from previous games
- `NetworkWisdomRung` - Queries viral packages from successful agents
- `PrimitiveSuggesterRung` - Maps seed primitives to action suggestions
- `FrontierCheckpointRung` - Uses checkpoints for efficient exploration

### 4. Pattern Validation via RLVR

Patterns are validated through Reinforcement Learning with Verifiable Rewards:

| Function | Description |
|----------|-------------|
| Score feedback | Direct ARC API score validates action sequences |
| Cross-agent comparison | Successful patterns spread via viral packages |
| Fitness calculation | RLVR scores drive evolutionary selection |

**Architecture**: Decentralized exploration (agents), centralized fitness (RLVR), distributed storage (database).

### 5. Seed Primitives

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

## Project Structure

### Entry Points
- `evolution_runner.py` - Main entry point for autonomous evolution
- `core_data.db` - The "network brain" (SQLite database storing ALL knowledge)

### Core Modules

| Module | Purpose |
|--------|---------|
| `core_gameplay.py` | Main gameplay loop and action execution |
| `decision_rung_system.py` | 42-rung ladder for action selection |
| `seed_primitives.py` | Innate cognitive primitives (attention, affordance, physics) |
| `database_interface.py` | SQLite database operations |
| `evolutionary_engine.py` | Population evolution and breeding |
| `engines/consciousness/i_thread.py` | Stream A/B weighting, identity persistence |
| `engines/consciousness/sensation_engine.py` | Emotional gameplay and navigation state |
| `engines/social/viral_package_engine.py` | Viral knowledge exchange system |
| `engines/social/prestige_engine.py` | Social capital and contribution tracking |

### Supporting Systems

| Module | Purpose |
|--------|---------|
| `engines/regulation/regulatory_signal_engine.py` | Adaptive signals for population control |
| `engines/perception/terminal_pattern_detector.py` | Game-over foresight - learns fatal patterns |
| `engines/postgame/orchestrator.py` | RLVR fitness calculation |
| `safe_cleanup.py` | Database maintenance (runs every 10 generations) |

### Architecture & Theory Documentation

Theoretical concepts in `DOCS/`:

| Folder | Contents |
|--------|----------|
| `Concept - Agent Self & World Model/` | Consciousness theory, Two Streams, persona submodeling |
| `Concept - MetaLearning System/` | Primitives, bootstrapping mechanisms |
| `Concept - Network Model/` | Network theory, viral exchange, database-as-organism |
| `Concept Integration/` | Unified theory synthesis, integration architecture |

Architectural decisions in `architecture/`:

| File | Contents |
|------|----------|
| `decision_cognitive_architecture.md` | Decision rung system design |
| `frontier_checkpoint_system.md` | Checkpoint and progress tracking |

---

## Analysis & Monitoring Tools

Located in `manual_tools/`:

```bash
# Gameplay progression analysis
python manual_tools/analysis/gameplay_analyzer.py --hours 3

# Database validation
python manual_tools/db_validation.py

# Schema inspection
python manual_tools/database/schema_inspector.py --table agents --sample
```

| Tool | Purpose |
|------|---------|
| `analysis/gameplay_analyzer.py` | Game results, scores, level completions |
| `observer_dashboard.py` | Real-time system observation |
| `db_validation.py` | Database integrity checks |

---

## Testing

Tests are located in `tests/` folder (exception to "No Test Files" rule):

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_primitives.py -v
```

---

## Configuration

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
- RLVR feedback provides verifiable ground truth for pattern validation
- Dual-currency system maintains diversity under evolutionary pressure

---

<img width="1325" height="545" alt="image" src="https://github.com/user-attachments/assets/f8b00168-0c93-4161-bc3d-88faa1689ce7" />

---

Example Gameplay (Level 4 as66 - legacy version):
[https://three.arcprize.org/replay/as66-821a4dcad9c2/55d279d1-3f1e-416f-9024-c49e1b1df573](https://three.arcprize.org/replay/as66-821a4dcad9c2/55d279d1-3f1e-416f-9024-c49e1b1df573)
