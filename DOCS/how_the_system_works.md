# How the Ouroboros System Works
**Master Reference Guide**
**Date**: December 3, 2025

## 1. Core Philosophy: The Network is the Organism
The Ouroboros system is designed as a **network-centric evolutionary AI**. Unlike traditional reinforcement learning where individual agents are the focus, here:
-   The **Network (Database)** is the immortal organism.
-   **Agents** are temporary vessels (like cells) that gather experiences.
-   **Knowledge** (sequences, patterns, rules) is horizontally transferred and persists beyond agent lifespan.
-   **Success** is defined by the growth of network intelligence, not individual agent high scores.

## 2. System Architecture
The system operates on a **Three-Layer Architecture**:

### Layer 1: Static Genome (Nature)
-   **What**: Fundamental agent traits (Species type, base architecture).
-   **Plasticity**: Low.
-   **Inheritance**: 100% genetic.
-   **Mutation**: 1-2% per generation.

### Layer 2: Epigenetic (Nurture)
-   **What**: Learning parameters (Attention weights, exploration rates, social rule adherence).
-   **Plasticity**: Medium.
-   **Inheritance**: Fitness-weighted with 0.95 decay (prevents overfitting to past environments).
-   **Mutation**: 10-20% per generation.

### Layer 3: Somatic (Experience)
-   **What**: Learned knowledge (Winning sequences, patterns, "muscle memory").
-   **Plasticity**: High.
-   **Inheritance**: **NOT INHERITED**. Stored in the Community Database.
-   **Access**: Agents query the database for sequences based on Bayesian reputation.
-   **Agent Self-Model**: Tracks "self" vs "environment" (e.g., "I control the red pixel").

## 3. The Autonomous Loop (Ouroboros)
The system runs in a continuous autonomous loop managed by the **Claude Code Coordinator**:

1.  **Analyze**: The `PerformanceAnalyzer` reviews game results, network health, and prestige distribution.
2.  **Hypothesize**: The coordinator determines the next evolutionary strategy (e.g., "Increase exploration", "Focus on optimization").
3.  **Evolve**: The `EvolutionaryEngine` breeds new agents, applies mutations, and handles horizontal gene transfer.
4.  **Deploy**: Agents are assigned to games based on their role (Pioneer, Optimizer, etc.).
5.  **Execute**: Agents play ARC games using the `ARCRLVRFramework` (Reasoning, Learning, Validation, Revision).
6.  **Store**: All actions, results, and discoveries are logged to the SQLite `core_data.db`.
7.  **Repeat**: The cycle continues 24/7.

## 4. Agent Roles
Agents are specialized to ensure efficient coverage of the problem space:

-   **PIONEERS (60%)**: Explore unbeaten "frontier" levels. Use best known sequences to reach the edge, then explore.
-   **OPTIMIZERS (30%)**: Refine solutions for beaten games. Focus on reducing action counts and finding more efficient paths.
-   **GENERALISTS (10%)**: Balanced players with **Emotional Intelligence** (Sensation Engine). Validate others' work.
-   **EXPLOITERS (5-15%)**: Micro-optimize fully solved games. **REQUIRE** proven sequences; do not explore. Split 50/50 between "Social" and "Sociopath".

**Dynamic Role Distribution**:
The mix of agents changes based on the game state:
-   **Exploration Mode** (Unsolved): Heavy on Pioneers to find first wins.
-   **Optimization Mode** (Solved): Switches to Optimizers and Exploiters to refine solutions.

## 5. Key Subsystems

### Sensation Engine (Phase 4.5)
-   Gives agents "feelings" about game objects and states.
-   Maps objects to sensations (e.g., "Red pixels feel dangerous").
-   Biases navigation actions based on emotional state (-1.0 Fear to +1.0 Excitement).

### Viral Packages & Horizontal Transfer
-   Successful strategies are packaged as "viruses".
-   These packages infect other agents, spreading useful behaviors rapidly across the population.
-   "Pariah" patterns (failures) are also spread to warn agents what *not* to do.

### Regulatory Signal Engine
-   Maintains homeostasis (balance) in the network.
-   Signals like "Population Stress" or "Diversity Crisis" trigger automatic parameter adjustments (e.g., increasing mutation rates).

### Breakthrough Systems (Tier 1-3)
-   **Subgoal Planner**: Decomposes problems into hierarchical plans (Objective -> Subgoals -> Actions).
-   **Frustration Detector**: Uses quorum sensing to detect collective failure and trigger "Desperation Mode".
-   **Near-Miss Analyzer**: Learns from "almost winning" runs (15-18/20 scores).
-   **Collective Reasoning**: Enables multi-agent collaboration on hard problems.
-   **Counterfactual Analyzer**: Performs "What if?" analysis to find alternative paths.

### Meta-Learning (AGI Mode)
-   **Meta-Learning Curriculum**: 4-stage progression (Specialization -> Generalization).
-   **Rule Induction**: Learns abstract IF-THEN rules from successful runs.
-   **Visual Reasoning**: Analyzes grids for symmetry, patterns, and shapes.

### Agent Self-Model
-   Tracks which objects/pixels agents control ("I am this object").
-   Builds confidence maps based on action-response correlations.

### Sequence System
-   **Full Game Sequences**: The "Holy Grail" - completing an entire game in one run.
-   **Partial Sequences**: Level-by-level solutions.
-   **Validation**: Sequences are constantly re-validated by agents. Low-reliability sequences are pruned.

## 6. Testing Protocol
-   **Unit Testing**: Encouraged for all new code changes.
-   **Live Data Only**: **NO dummy data** allowed in the database. All database records must originate from live ARC 3 API gameplay.
-   **No Simulations**: Always use the real ARC 3 API.

## 7. Data Flow
`Agent Action` -> `ARC API` -> `Result` -> `Database` -> `Performance Analyzer` -> `Evolution Strategy` -> `New Agents`

## 8. Where to Find Things
-   **Master Ruleset**: `.github/copilot-instructions.md`
-   **Implementation Details**: `DOCS/ouroboros_final_implementation.md`
-   **Progress & Status**: `progress.md`
-   **Database Schema**: `complete_database_schema.sql`
-   **Core Logic**: `core_gameplay.py`, `autonomous_evolution_runner.py`
