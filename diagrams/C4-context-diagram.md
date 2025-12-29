# C4 Context Diagram - Ouroboros System

## System Context Level

This diagram shows the Ouroboros autonomous evolution system and its external interactions.

```mermaid
C4Context
    title System Context Diagram - Ouroboros Autonomous Evolution

    Person(operator, "Operator/Oracle", "Human overseeing system evolution. Starts/stops runs, reviews progress")
    
    System(ouroboros, "Ouroboros Evolution System", "Autonomous multi-agent system that evolves to solve ARC-AGI-3 puzzles through network-level intelligence")
    
    System_Ext(arc_api, "ARC-AGI-3 API", "External game API providing puzzle games and scoring")
    
    System_Ext(sqlite, "SQLite Database", "Persistent storage for all agent data, sequences, knowledge")

    Rel(operator, ouroboros, "Starts evolution, reviews progress, fixes bugs")
    Rel(ouroboros, arc_api, "Plays games via REST API", "HTTPS")
    Rel(ouroboros, sqlite, "Stores all data", "SQLite/WAL mode")
    Rel(arc_api, ouroboros, "Returns game state, scores")
```

## Context Description

### The Ouroboros System
- **Purpose**: Achieve 100% win rate on all ARC-AGI-3 puzzle games through autonomous network-level evolution
- **Philosophy**: "The database is the organism" - agents are temporary vessels, knowledge persists
- **Mode**: Fully autonomous with optional operator oversight

### External Systems

| System | Purpose | Interaction |
|--------|---------|-------------|
| **ARC-AGI-3 API** | Provides puzzle games with levels, frames, actions 1-7 | Agents play real games, never simulated |
| **SQLite Database** | Persistent storage (~10 GB limit) | 73+ tables storing everything |

### Key Actors

| Actor | Role | Interactions |
|-------|------|--------------|
| **Operator/Oracle** | Autonomous oversight (Claude/Copilot) | Monitors health, fixes bugs, commits changes |

## Architecture Principles

1. **Database-Only Storage**: All data in SQLite, never log files
2. **Real Games Only**: Never mock/simulate - always use ARC API
3. **Network-Centric**: Knowledge belongs to network, not individual agents
4. **Prestige/Budget Separation**: Social capital (prestige) separate from economic capital (action budgets)
5. **No Unicode Emojis**: ASCII only for Windows compatibility
