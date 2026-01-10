## Ouroboros: Generalized learning via distributed networks

**Paradigm Shift - The Network is the Organism.**

- Thesis: [AGI as Network Intelligence: A Unified Theory](https://medium.com/@IsaiahNwukor/agi-as-network-intelligence-a-unified-theory-056e18c7ede1)

### The Process of Discovery
**The Nature of the Problem**

Taming Alignment is a matter of understanding the **<ins>Nested [Observer Paradox](https://en.wikipedia.org/wiki/Observer%27s_paradox).</ins>**
This system explains some of the underlying mechanisms behind the butterfly effect.

Here are some of the bigger collaborators/influences for the project:

- **Patrick Cox - Tetrahedral Object architecture (Math based Storytelling for characters)**

- **RLVR - Reinforcement Learning with Verifiable Rewards Implicitly Incentivizes Correct Reasoning in Base LLMs](https://arxiv.org/abs/2506.14245)**
   - Xumeng Wen, Zihan Liu, Shun Zheng, Shengyu Ye, Zhirong Wu, Yang Wang, Zhijian Xu, Xiao Liang, Junjie Li, Ziming Miao, Jiang Bian, Mao Yang


- We are grateful to our collaborators, acquaintences, friends, family and all connections (past/present/future) who contribute.

## Project that encapsulated the work to get the theory
Ouroboros is an evolutionary system designed to solve the [ARC-AGI-3 challenge](https://arcprize.org/arc-agi/3/), an open source.
Unlike traditional agents, it treats the entire population as a single learning network, preserving knowledge across generations through a centralized database.

## Quick Start

```bash
# Start the autonomous evolution loop (Recommended)
python run_evolution.py

# Run in "Specialist Mode" (Deep mastery of specific games)
python run_evolution.py --specialist

# Run in "Diversity Mode" (Focus on generalization)
python run_evolution.py --diversity
```

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

### 1. Evolutionary Biome Architecture
The system mimics biological evolution with three distinct layers of information:
-   **Layer 1: Static Genome (Nature)**. Hard-coded traits (e.g., neural architecture type). Low mutation, high stability.
-   **Layer 2: Epigenetic (Nurture)**. Learning rates and biases. Inherited but decays over generations of agents. Allows temporary adaptation to environmental stress.
-   **Layer 3: Somatic (Culture)**. Real-time knowledge (e.g., "Red pixels are dangerous"). High plasticity. **Not inherited** biologically but stored in the Community Database for all agents to access.

Features derived from these layers:

- Horizontal Gene Transfer: Agents swapping strategies regardless of lineage.
- Viral Packages: Successful strategies spreading rapidly through a network.
- Pariahs: Failure patterns marked for avoidance.

### 2. Sensation Engine of the Network
Agents possess "Semantic Sensation" that biases their navigation (Actions 1-7):
-   **Perception**: Agents recognize objects (e.g., "Blue Square").
-   **Sensation**: Objects trigger emotional states (Frustrated, Cautious, Curious, Confident) based on history.
-   **Action Bias**: Emotions influence movement. "Fear" causes retreat; "Curiosity" drives exploration.
-   **Navigation State**: A floating-point value (-1.0 to +1.0) representing the agent's current mood.

### 3. Agent Roles
The workforce is divided into specialized roles:
-   **Pioneers**: Frontier explorers that seek novel solutions on unbeaten levels.
-   **Optimizers**: Efficiency experts that refine existing solutions on beaten games.
-   **Generalists**: Balanced validators that ensure solution robustness.
-   **Exploiters**: Post-optimization refiners

### 4. Agent Self-Model & Perception
Agents develop a concept of "Self" using Stream-aware perception (aligned with Two Streams Theory):
-   **Self-Recognition**: Tracks which pixels/objects move in response to agent actions.
-   **Confidence Maps**: Builds a probability map of controlled elements.
-   **Agency**: Distinguishes between agent actions and environmental physics.
-   **Self-Direction**: Agents balance private reasoning vs network wisdom based on w_A/w_B weighting.
-   **Stream-Aware Perception**: Each object perceived through 4 knowledge sources:
    - **Stream A** (Private): What I personally observe (color, position, shape)
    - **Stream B** (Collective): What the network knows about this object type
    - **Hypothesis** (Theory): Current working theory from CODS about control
    - **Synthesis** (Persona): Weighted integration (w_A * Stream A + w_B * Stream B)
-   **Cognitive State**: Calculated from stream conflict (automatic/deliberative/vivid/paralyzed) to modulate decisions.    

### 5. Cross-Role Resonance Detection
The system identifies objective truths through cross-role pattern agreement:
-   **Resonance Principle**: When Pioneers (blind), Generalists (network-guided), and Exploiters (micro-optimizers) independently discover the same abstract pattern, that's **resonance** - evidence of objective truth.
-   **Pattern Hashing**: Sequences are fingerprinted by cognitive structure (theory type, complexity, strategy) not raw actions.
-   **Role Diversity Scoring**: Higher resonance when more different roles independently converge.
-   **Amplification Signals**: High-resonance patterns trigger network-wide exploration boosts.

### 6. Abstraction & Symbolic Reasoning
To solve complex tasks, the system moves beyond pixel manipulation:
-   **Symbolic Reasoning**: Converts grid states into logical symbols (e.g., `Shape(Color.RED, Pos(0,0))`). Agents reason about relationships between these symbols rather than raw pixels.
-   **Rule Induction**: Derives abstract rules (e.g., "Fill all enclosed areas with blue") from symbolic relationships.
-   **Counterfactual Analysis**: "What if?" reasoning to test hypotheses before acting.

### 7. Sequence Abstraction
The system learns and generalizes action sequences:
-   **Winning Sequences**: Complete solutions stored in the database.
-   **Sequence Abstraction**: Identifies reusable *patterns* within sequences (e.g., "Move to corner" is a reusable sub-sequence).
-   **Replay & Refinement**: Agents replay abstract sequences to reach the "frontier" (unsolved levels), allowing them to focus compute on the unknown levels.

### 8. Prestige vs. Action Allowances (The "Sacred Separation")
The system strictly separates Social Capital from Economic Capital, unlike human societies where they often mix:

| Feature | Prestige (Social Capital) | Action Allowance (Economic Capital) |
| :--- | :--- | :--- |
| **Definition** | Respect earned by contributing to the network (teaching, validating). | The computational budget (actions/currency) an agent can spend. |
| **Source** | Earned by **helping others** (e.g., uploading useful sequences). | Earned by **personal performance** (high scores, efficiency). |
| **Function** | Determines **influence** (breeding rights, sequence priority). | Determines **lifespan** (how long they can play/explore). |
| **Philosophy** | "What value do you contribute to the collective?" | "What value do you earn for yourself?" |
| **Separation** | **Prestige cannot buy Actions.** A great agent who plays poorly will still run out of energy. | **Actions cannot buy Prestige.** An agent with a large action allowance but is selfish, will have no influence/prestige. |

**Adaptive Action Allowances**:
Action allowances are not static, but adaptively meritocratic. The system dynamically adjusts allowances based performance. High-performing agents receive larger allowances, allowing them to tackle deeper, more complex problems.

### 9. Game State Modes
The system dynamically shifts its strategy based on the state of each game:
-   **Exploration Mode** (Unbeaten Games):
    -   **60% Pioneers**: Aggressively search for *any* solution.
    -   **Target**: Frontier levels (unsolved).
-   **Optimization Mode** (Beaten Games):
    -   **70% Optimizers**: Refine existing solutions to reduce action counts.
    -   **Target**: Efficiency and robustness.
    -   **Transition**: Happens  when the first full game win is achieved for that game type.


### 10. System Maintenance & Safety
The system includes autonomous maintenance to ensure long-term stability:
-   **Database Vacuuming**: Automatically optimizes the SQLite database to prevent bloat.
-   **Sequence Pruning**: Aggressively removes "dead" sequences (low success rate, excessive actions) to keep the knowledge base clean.
-   **Agent Sunsetting**: Agents are automatically retired after a set number of generations or if performance stagnates, ensuring the population remains fresh and competitive.
-   **Semantic Forgetting**: Unused knowledge and weak object-sensation mappings decay over time (Generational Forgetting), preventing the accumulation of obsolete data.
-   **Disk Monitoring**: Enforces a 10GB hard limit on database size.
-   **Pycache Prevention**: Strictly enforces `PYTHONDONTWRITEBYTECODE=1` to keep the file system clean.
-   **Graceful Shutdown**: Handles `Ctrl+C` signals to ensure WAL (Write-Ahead Log) checkpoints are written before exiting, preventing data corruption.

### 11. Societal Metrics & Autopoiesis
The system implements self-regulating metrics inspired by autopoiesis (self-maintaining systems) with anti-Goodhart safeguards:

-   **Emergence Gain**: Measures whether network intelligence grows faster than individual learning. Target: > 1.0 (network outpaces individuals).
-   **Control Error**: Deviation between intended vs actual system behavior. Target: < 0.30 (system responds predictably).
-   **Identity Drift**: Tracks system coherence over time. Target: < 0.25 (maintains core identity while adapting).
-   **Loop Detection**: Identifies stuck agents repeating futile action patterns. Triggers intervention when detected.
-   **Role Saturation**: Monitors agent role distribution health. Alerts when roles become imbalanced.

**Anti-Goodhart Protections**:
-   **Trigger Controller**: Prevents feedback resonance with cooldowns, damping, and corroboration requirements.
-   **Metric Rotation**: Periodically rotates which metrics are "active" to prevent gaming.
-   **Metric Confidence**: Meta-metric tracking contradiction rates and predictive power.
-   **Noise Injection**: Random perturbations prevent overfitting to exact thresholds.

## 📂 Key Files
-   `run_evolution.py`: Main entry point.
-   `core_data.db`: The "network" (SQLite database storing ALL knowledge).

**Core Modules**:
-   `core_gameplay.py`: Main gameplay loop and action execution.
-   `network_intelligence_engine.py`: Network-level learning and emergence tracking.
-   `cods_engine.py`: Composed Operator Discovery System - failure-driven primitive learning.
-   `concept_discovery_engine.py`: Semantic concept discovery across games.
-   `terminal_pattern_detector.py`: Game-over foresight - learns fatal action patterns.
-   `seed_primitives.py`: derived cognitive primitives (attention, affordance, physics priors, metacognition).
-   `regulatory_signal_engine.py`: Adaptive signals for population control.
-   `autopoiesis_monitor.py`: System health metrics and self-regulation.

## 📊 Analysis Tools

Reusable tools for monitoring and debugging the system:

```bash
# Gameplay progression analysis
python manual_tools/gameplay_analyzer.py --hours 3 --compare

# Network health diagnostics
python network_health_report.py

# Automated reasoning bug detection
python investigate_bugs.py

# Database schema inspection  
python manual_tools/schema_inspector.py --table agents --sample
python manual_tools/schema_inspector.py --counts
```

| Tool | Purpose |
|------|--------|
| `gameplay_analyzer.py` | Analyze game results, scores, level completions, baseline comparison |
| `network_health_report.py` | Population stats, emergence gain, cognitive stages, sequence health |
| `investigate_bugs.py` | Detect and investigate reasoning disconnects automatically |
| `schema_inspector.py` | Inspect database tables, columns, row counts, sample data |

## 🛠️ Configuration
-   **Environment**: Copy `.env.example` to `.env`, set `ARC_API_KEY`, then `pip install -r requirements.txt` (includes `python-dotenv` for automatic loading).
-   **Logs**: All logs are stored in `core_data.db` (No log files!).
-   **Shutdown**: Press `Ctrl+C` ONCE for graceful shutdown (saves state & closes scorecard(s)).

---
<img width="1325" height="545" alt="image" src="https://github.com/user-attachments/assets/f8b00168-0c93-4161-bc3d-88faa1689ce7" />
