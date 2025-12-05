# Ouroboros: Autonomous ARC AGI Evolution

**The Network is the Organism.**

Ouroboros is an evolutionary system designed to solve the ARC-AGI-3 challenge. Unlike traditional agents, it treats the entire population as a single learning network, preserving knowledge across generations through a centralized database.

Thesis: [AGI is not a brain - It's a Network](https://adventuresinml.substack.com/p/agi-is-not-a-brain-its-a-society)

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

### 4. Agent Self-Model
Agents develop a concept of "Self-Direction" vs "Collective Intelligence" vs "Environment":
-   **Self-Recognition**: Tracks which pixels/objects move in response to agent actions.
-   **Confidence Maps**: Builds a probability map of controlled elements.
-   **Agency**: Allows agents to distinguish between their actions and environmental physics.
-   **Self-Direction**: Agents can choose to act on their own or follow the collective intelligience (The Network) based on their assigned role.    

### 5. Abstraction & Symbolic Reasoning
To solve complex tasks, the system moves beyond pixel manipulation:
-   **Symbolic Reasoning**: Converts grid states into logical symbols (e.g., `Shape(Color.RED, Pos(0,0))`). Agents reason about relationships between these symbols rather than raw pixels.
-   **Rule Induction**: Derives abstract rules (e.g., "Fill all enclosed areas with blue") from symbolic relationships.
-   **Counterfactual Analysis**: "What if?" reasoning to test hypotheses before acting.

### 6. Sequence Abstraction
The system learns and generalizes action sequences:
-   **Winning Sequences**: Complete solutions stored in the database.
-   **Sequence Abstraction**: Identifies reusable *patterns* within sequences (e.g., "Move to corner" is a reusable sub-sequence).
-   **Replay & Refinement**: Agents replay abstract sequences to reach the "frontier" (unsolved levels), allowing them to focus compute on the unknown levels.

### 7. Prestige vs. Action Allowances (The "Sacred Separation")
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

### 8. Game State Modes
The system dynamically shifts its strategy based on the state of each game:
-   **Exploration Mode** (Unbeaten Games):
    -   **60% Pioneers**: Aggressively search for *any* solution.
    -   **Target**: Frontier levels (unsolved).
-   **Optimization Mode** (Beaten Games):
    -   **70% Optimizers**: Refine existing solutions to reduce action counts.
    -   **Target**: Efficiency and robustness.
    -   **Transition**: Happens  when the first full game win is achieved for that game type.


### 9. System Maintenance & Safety
The system includes autonomous maintenance to ensure long-term stability:
-   **Database Vacuuming**: Automatically optimizes the SQLite database to prevent bloat.
-   **Sequence Pruning**: Aggressively removes "dead" sequences (low success rate, excessive actions) to keep the knowledge base clean.
-   **Agent Sunsetting**: Agents are automatically retired after a set number of generations or if performance stagnates, ensuring the population remains fresh and competitive.
-   **Semantic Forgetting**: Unused knowledge and weak object-sensation mappings decay over time (Generational Forgetting), preventing the accumulation of obsolete data.
-   **Disk Monitoring**: Enforces a 10GB hard limit on database size.
-   **Pycache Prevention**: Strictly enforces `PYTHONDONTWRITEBYTECODE=1` to keep the file system clean.
-   **Graceful Shutdown**: Handles `Ctrl+C` signals to ensure WAL (Write-Ahead Log) checkpoints are written before exiting, preventing data corruption.

## 📂 Key Files
-   `run_evolution.py`: Main entry point.
-   `core_data.db`: The "network" (SQLite database storing ALL knowledge).
-   `DOCS/how_the_system_works.md`: Detailed system architecture.

## 🛠️ Configuration
-   **Environment**: Copy `.env.example` to `.env` and set `ARC_API_KEY`.
-   **Logs**: All logs are stored in `core_data.db` (No log files!).
-   **Shutdown**: Press `Ctrl+C` ONCE for graceful shutdown (saves state & closes scorecard(s)).

---
<img width="1325" height="545" alt="image" src="https://github.com/user-attachments/assets/f8b00168-0c93-4161-bc3d-88faa1689ce7" />
