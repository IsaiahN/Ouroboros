# Master Guide: Using PyDeps for AGI System Debugging
**System**: Unified AGI Architecture (Network + Metalearning + Consciousness Theories)  
**Version**: 1.1  
**Date**: January 12, 2026  
**Purpose**: Fix circular dependencies, silent failures, and logic flow breaks in 100+ file Python codebase
**Environment**: Windows + VS Code + Copilot

---

## CRITICAL OPERATING RULES FOR THIS GUIDE

### Rule 1: No Unicode Emojis
- Use ASCII alternatives: `[OK]`, `[FAIL]`, `[WARN]`, `->`, `<->`
- **Why**: Windows cp1252 encoding errors prevent scripts from running
- **Applies to**: All commands, output examples, and documentation

### Rule 2: Test Before Commit
- Test all fixes on the actual codebase
- Verify with pydeps after each fix
- Run integration tests to confirm data flows
- **Only commit to git when confirmed working**

### Rule 3: No Orphaned Code
- Every fix must integrate cleanly with existing architecture
- Account for all imports and references
- Delete old unused code when refactoring
- Update all dependent files

### Rule 4: Database-Only Storage
- All analysis results go in database, not log files
- Use `database_logger.py` for logging
- Store pydeps reports in `architecture/analysis/` directory only for review
- Store pydeps diagrams (svgs) in `diagrams/` directory only for review

### Rule 5: Real Testing Only
- Never use mock/simulated data
- Test fixes against actual ARC AGI 3 games
- Verify data flows with live database queries

### Rule 6: Diagrams Folder Convention
- ALL generated SVG diagrams MUST be saved to `diagrams/` folder
- NEVER save SVGs to `analysis/` or project root
- Standard diagram names:
  - `deps_core_gameplay.svg` - Core gameplay dependencies
  - `deps_cods_engine.svg` - CODS engine dependencies
  - `deps_seed_primitives.svg` - Primitives dependencies
  - `full_dependencies.svg` - Complete system graph
- **Why**: Centralized location for all architecture visualizations

---

## Executive Summary

Your AGI system is already implemented but has three critical issues:
1. **Circular dependencies** - Modules import each other creating cycles
2. **Silent failures** - Logic breaks without error messages
3. **Flow leaks** - Data not propagating through the architecture correctly

This guide provides a systematic approach using **pydeps** (dependency analysis) and **VS Code with Copilot** (automated fixing) based on your unified theoretical architecture.

> **NOTE**: This guide contains both **actual tools** (that exist in the codebase) and **template scripts** (example code you can implement). Actual tools are marked with `[EXISTS]`. Template scripts are provided as reference implementations.
>
> **Actual Tools Available**:
> - `analyze_dependencies.py` - PyDeps wrapper with stats, orphan detection, cycle checking
> - `theory_alignment_checker.py` - Theory alignment verification
> - `safe_cleanup.py` - Database cleanup utility
> - `tests/` folder - Existing test suite

---

## Part I: Understanding Your System Architecture

### The Three-Layer Architecture

Based on the master ruleset, your system follows a three-layer agent architecture:

**Layer 1: Static Genome (Nature - "Hardware")**
- Agent type, base architecture, core capabilities
- Mutation Rate: 1-2% per generation
- Inheritance: Full genetic (100%)
- Lifespan: Entire agent life

**Layer 2: Epigenetic (Nurture - "Learning Capacity")**
- Feature attention weights, learning rate modifiers
- Sensation profile, social rule adherence
- Stream weighting (w_A/w_B balance)
- Mutation Rate: 10-20% per generation
- Inheritance: Fitness-weighted with 0.95 decay

**Layer 3: Somatic (Experience - "Learned Knowledge")**
- Winning sequences, discovered patterns, action memories
- NOT INHERITED - stored in community database
- Lifespan: Outlives agent (network memory)

**At the code architecture level**, this translates to:

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: CENTRAL INFRASTRUCTURE (Persistent)                   │
│  - Database (core_data.db) - The immortal organism              │
│  - CODS/Oracle - Centralized validator                          │
│  - Regulatory Engine - Population management                    │
└─────────────────────────────────────────────────────────────────┘
                              <->
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: KNOWLEDGE LAYER (Distributed)                         │
│  - Viral Information Packages - Spreadable knowledge units      │
│  - Resonance Patterns - Cross-domain validations               │
│  - Composed Operators - Discovered primitives                   │
└─────────────────────────────────────────────────────────────────┘
                              <->
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: AGENT LAYER (Temporary)                              │
│  - Two-Stream Consciousness (Stream A/B)                        │
│  - Persona Ensemble (Proposers/Observers/Evaluators)           │
│  - Cognitive Roles (Pioneer/Optimizer/Generalist/Exploiter)    │
└─────────────────────────────────────────────────────────────────┘
```

### Critical Data Flows (Where Leaks Likely Occur)

**Flow 1: Gameplay -> CODS -> Validation -> Unlocking**
```
agent plays game -> generates RLVR data -> 
CODS analyzes -> validates patterns -> 
unlocks primitives -> creates viral packages
```

**Flow 2: Stream B Knowledge Retrieval**
```
agent queries Stream B -> 
retrieves viral packages from database -> 
integrates with Stream A -> 
action selected
```

**Flow 3: Persona Synthesis**
```
streams conflict detected -> 
personas generate proposals -> 
synthesis proposal created -> 
surprise measured -> 
action executed
```

**Flow 4: Prestige -> Viral Spread**
```
agent discovers pattern -> 
RLVR validates -> 
prestige awarded -> 
viral package created -> 
spreads to all agents
```

---

## Part II: Setup Phase

### Step 0: Activate Virtual Environment

**CRITICAL**: ALL commands must run in the `.venv` virtual environment.

**Windows (PowerShell)**:
```powershell
# Navigate to project root
cd C:\Users\Admin\Documents\GitHub\BitterTruth-AI

# Activate virtual environment
& .venv/Scripts/Activate.ps1

# Verify activation - should see (.venv) prefix in prompt
# (.venv) PS C:\Users\Admin\Documents\GitHub\BitterTruth-AI>

# Programmatic verification (recommended)
python -c "import sys; print(sys.prefix)"
# Should output: C:\Users\Admin\Documents\GitHub\BitterTruth-AI\.venv
```

**Linux/macOS**:
```bash
cd /path/to/BitterTruth-AI
source .venv/bin/activate
# Verify: should see (.venv) prefix
python -c "import sys; print(sys.prefix)"
# Should show .venv path, NOT system Python
```

> **WARNING**: If you see "No module named pydeps" or similar errors, you likely forgot to activate the venv!
> 
> **DIAGNOSTIC**: Run `python -c "import sys; print(sys.prefix)"` - if it shows system Python (e.g., `C:\Python313`), activate venv first!

### Step 1: Install Dependencies

**CRITICAL**: Always disable pycache (Rule 1)

**Windows (PowerShell)** (with venv activated):
```powershell
# Set environment variable for current session
$env:PYTHONDONTWRITEBYTECODE = "1"

# Set permanently (user level)
[Environment]::SetEnvironmentVariable("PYTHONDONTWRITEBYTECODE", "1", "User")

# Install pydeps (into .venv)
pip install pydeps

# Install Graphviz (required for visualization) - system-wide
# Option 1: Download from https://graphviz.org/download/
# Option 2: Use chocolatey: choco install graphviz
# Option 3: Use winget: winget install graphviz

# Verify installation
pydeps --version
```

**Linux/macOS** (with venv activated):
```bash
# Set environment variable
export PYTHONDONTWRITEBYTECODE=1
echo "export PYTHONDONTWRITEBYTECODE=1" >> ~/.bashrc

# Install pydeps (into venv) and graphviz (system)
pip install pydeps
sudo apt-get install graphviz -y  # Debian/Ubuntu
# brew install graphviz           # macOS
```

### Step 2: Create Project Structure Map

**Windows (PowerShell)**:
```powershell
# Navigate to project root
cd C:\Users\Admin\Documents\GitHub\BitterTruth-AI

# Create required directories (diagrams/ already exists)
New-Item -ItemType Directory -Path "diagrams" -Force

# List all Python files
Get-ChildItem -Recurse -Filter "*.py" | Select-Object FullName

# Count files
(Get-ChildItem -Recurse -Filter "*.py").Count
```

**Linux/macOS**:
```bash
cd /path/to/BitterTruth-AI
mkdir -p diagrams
find . -name "*.py" -type f | wc -l
```

### Step 3: Initial Dependency Scan

**IMPORTANT**: All SVG diagrams MUST be saved to the `diagrams/` folder.

Use the wrapper script `analyze_dependencies.py` which handles all pydeps configuration:

```powershell
# Generate dependency diagrams for key modules (saves to diagrams/ folder)
python analyze_dependencies.py --full --core --reasoning

# Check for circular dependencies
python analyze_dependencies.py --cycles

# Get stats and check for orphaned modules
python analyze_dependencies.py --stats --orphans

# Generate specific module diagrams
python analyze_dependencies.py --module core_gameplay
python analyze_dependencies.py --module cods_engine
```

**Direct pydeps usage** (if needed):
```powershell
# Generate diagram for specific module
pydeps core_gameplay --max-bacon=3 -o diagrams/deps_core_gameplay.svg

# Show cycles for a module
pydeps cods_engine --show-cycles
```

---

## Part III: Theoretical Architecture Mapping

### Critical Files by Theory (Expected Structure)

Based on your three theories, your codebase likely has:

#### **Network Theory Files** (Layer 1)
> **Note**: This project uses a FLAT structure (no subdirectories). Files are in project root.

```
# Database Layer
core_data.db                    # SQLite database (the immortal organism)
complete_database_schema.sql    # Table definitions
database_interface.py           # Database access layer
enhanced_database_interface.py  # Extended database operations
database_logger.py              # Database-backed logging

# Network/Viral System
viral_package_engine.py         # Viral package management
prestige_engine.py              # Social capital system
prestige_vampire_detector.py    # Prestige abuse detection
regulatory_signal_engine.py     # Population control signals
resonance_detector.py           # Cross-domain pattern detection
horizontal_transfer_engine.py   # Knowledge transfer between agents
network_intelligence_engine.py  # Network-level learning
network_knowledge_synthesis.py  # Knowledge aggregation
```

#### **Metalearning Theory Files** (Layer 2)
```
# CODS/Oracle System
cods_engine.py                  # Centralized Oracle/Discovery System
oracle_interface.py             # Oracle access interface
oracle_health_monitor.py        # Oracle system health
oracle_stuck_game_diagnostics.py # Stuck game analysis

# Primitives & Operators  
seed_primitives.py              # 110 innate primitive operations
primitive_unlock_manager.py     # Granting discovered primitives
operator_composer.py            # Operator combination/composition

# Scientific Method
scientific_method_engine.py     # Hypothesis formation
rule_induction_engine.py        # Pattern -> rule extraction
concept_discovery_engine.py     # New concept identification
```

#### **Consciousness Theory Files** (Layer 3)
```
# Two-Stream Architecture (integrated into core modules)
# Stream A (private experience): Tracked in agent_operating_mode_system.py
# Stream B (network wisdom): Queries viral_package_engine.py via database

# Persona System
persona_runtime.py              # Persona ensemble management
                                # - Action proposers
                                # - Observer personas  
                                # - Strategy evaluators

# Agent Identity & Self-Model
agent_self_model.py             # "I am this object" comprehension
agent_factory.py                # Agent creation
agent_lifecycle_manager.py      # Agent birth/death/evolution
agent_operating_mode_system.py  # Role emergence, stream weighting (w_A/w_B)

# Gameplay (Main Loop)
core_gameplay.py                # Main game loop, consciousness step
                                # - _consciousness_step() method
                                # - Two-stream integration
                                # - Persona invocation
action_handler.py               # Action execution
arc_api_client.py               # ARC-AGI API interaction
game_session_manager.py         # Game state management
```

### Expected Import Patterns (Clean Architecture)

**CRITICAL**: The dual-economy principle (SACRED) must be maintained:
- **Prestige** (social capital) = Trust weighting, credibility
- **Action Budgets** (economic capital) = Ability to play games
- **NEVER MIX THESE TWO CURRENCIES**

**Correct Flow** (No cycles):
```
Layer 3 (Agents) -> imports -> Layer 2 (CODS/Operators)
Layer 2 (CODS)   -> imports -> Layer 1 (Database)
Layer 1 (Database) -> imports -> Nothing (base layer)
```

**Problematic Patterns** (Causes cycles):
```
[FAIL] Layer 1 -> Layer 2 -> Layer 1 (cycle)
[FAIL] Layer 2 -> Layer 3 -> Layer 2 (cycle)
[FAIL] core_gameplay.py <-> cods_engine.py (bidirectional)
[FAIL] agent_operating_mode_system.py <-> viral_package_engine.py (circular)
```

---

## Part IV: Dependency Analysis Protocol

### Phase 1: Identify All Cycles

Use VS Code with Copilot to analyze dependencies. First run the actual analysis tools:

```powershell
# Run cycle detection
python analyze_dependencies.py --cycles

# Get full stats
python analyze_dependencies.py --stats --orphans
```

Then ask Copilot to analyze the results. Example prompt:

> "Analyze the circular dependencies found by analyze_dependencies.py and categorize them by architectural layer (Database/Network, CODS/Operators, Agents/Consciousness). Identify cross-layer cycles which are most dangerous."

**Analysis Template** (for reference):
```markdown
# Task: Identify and Categorize Circular Dependencies

## Context
AGI system with 100+ files implementing:
- Network Theory (viral packages, database)
- Metalearning Theory (CODS/Oracle, primitives)
- Consciousness Theory (streams, personas)

## Input Files
- analysis/cycles_report.txt
- diagrams/full_dependencies.svg

## Steps
1. Read the pydeps cycle report
2. Parse all circular dependency chains
3. Categorize by layer:
   - Layer 1 cycles (Database/Network)
   - Layer 2 cycles (CODS/Operators)
   - Layer 3 cycles (Agents/Consciousness)
   - Cross-layer cycles (most dangerous)
4. For each cycle, identify:
   - Files involved
   - Specific imports causing cycle
   - Theoretical architectural violation
   - Severity (1-5, based on data flow impact)
5. Create priority-sorted list

## Output
File: analysis/cycles_analysis.json
Format:
{
  "cycles": [
    {
      "id": 1,
      "severity": 5,
      "type": "cross_layer",
      "files": ["stream_b.py", "viral_packages.py", "agent.py"],
      "chain": "stream_b -> viral_packages -> agent -> stream_b",
      "theoretical_issue": "Stream B should only READ from database, not trigger agent updates",
      "suggested_fix": "Extract database query to separate module"
    },
    ...
  ],
  "summary": {
    "total_cycles": 15,
    "layer_1_cycles": 2,
    "layer_2_cycles": 5,
    "layer_3_cycles": 4,
    "cross_layer_cycles": 4
  }
}
```

Use VS Code Copilot Chat to help analyze and fix identified cycles.

### Phase 2: Map Silent Failures

**Reference Prompt Template** (use with VS Code Copilot):
```markdown
# Task: Find Silent Failure Points

## Context
System has logic breaks without error messages. Data isn't propagating correctly.

## Critical Data Flows to Trace
Based on unified architecture:

### Flow 1: RLVR Validation -> Primitive Unlocking
**Expected**: Agent performance -> CODS analyzes -> primitive unlocked
**Files to check**:
- gameplay files (generates RLVR data)
- cods/pattern_validator.py (analyzes data)
- primitives/primitive_unlocker.py (grants primitive)
- database updates (logs unlock)

**Check for**:
- Is RLVR data being written to database?
- Is CODS querying this data?
- Are unlock conditions being checked?
- Are primitives actually being added to agent's toolkit?

### Flow 2: Stream B -> Viral Package Retrieval
**Expected**: Agent queries Stream B -> retrieves packages -> integrates
**Files to check**:
- consciousness/stream_b.py (query logic)
- database_managers/viral_package_manager.py (retrieval)
- agents/agent.py (integration)

**Check for**:
- Is Stream B actually calling database?
- Are viral packages being returned?
- Is empty result handled (returns None vs [])?
- Are packages filtered correctly by game_type?

### Flow 3: Persona Synthesis -> Action Execution
**Expected**: Conflict detected -> personas propose -> synthesis -> action
**Files to check**:
- consciousness/persona_ensemble.py (proposals)
- agents/action_executor.py (execution)
- gameplay/core_gameplay.py (main loop)

**Check for**:
- Are personas being invoked when streams conflict?
- Are proposals being scored?
- Is synthesis happening or defaulting to first option?
- Are actions actually sent to ARC API?

## Steps
1. For each flow, add debug logging at every step
2. Run a test game with logging enabled
3. Identify where data stops propagating
4. Create failure_points.json with:
   - Flow name
   - Last successful step
   - First failing step
   - Missing logic/function call
   - Suggested fix

## Output
File: manual_tools/analysis/failure_points.json [TEMPLATE]
```

Use VS Code Copilot to help trace data flows and identify failure points.

### Phase 3: Logic Flow Verification

**Reference Prompt Template** (use with VS Code Copilot):
```markdown
# Task: Verify Critical Logic Flows

## Context
Verify that the theoretical architecture is actually implemented in code.

## Theoretical Requirements to Verify

### Requirement 1: CODS is Centralized (Not Per-Agent)
**Theory states**: CODS watches ALL agent gameplay, is external validator
**Code should show**: 
- Single CODS instance
- CODS receives data from all agents
- Agents don't instantiate their own CODS
**Check files**:
- cods/oracle.py (should be singleton or global)
- agents/agent.py (should NOT create CODS)

### Requirement 2: Roles Are Emergent (Not Assigned)
**Theory states**: Roles emerge from w_A/w_B weights + context
**Code should show**:
- agents.self_network_bias determines role
- Role can change mid-game based on updates
- No "role assignment" in agent creation
**Check files**:
- agents/agent.py (initialization)
- network/regulatory_engine.py (population management)

### Requirement 3: Stream B Queries Viral Packages
**Theory states**: Stream B gets collective wisdom from database
**Code should show**:
- stream_b.py queries viral_information_packages table
- Results filtered by relevance/credibility
- Agent doesn't need to "know" other agents directly
**Check files**:
- consciousness/stream_b.py
- database_managers/viral_package_manager.py

### Requirement 4: Personas Create Internal Dialogue
**Theory states**: Multiple personas argue, synthesize, surprise agent
**Code should show**:
- Multiple persona instances per agent
- Personas generate competing proposals
- Synthesis proposal when conflict high
- Surprise measured (chosen action vs habit)
**Check files**:
- consciousness/persona_ensemble.py
- agents/agent.py (persona invocation)

## Steps
1. For each requirement, trace through code
2. Verify implementation matches theory
3. Identify missing components
4. Create verification_report.json

## Output
File: manual_tools/analysis/verification_report.json [TEMPLATE]
Format:
{
  "requirements": [
    {
      "name": "CODS is centralized",
      "status": "IMPLEMENTED" | "PARTIAL" | "MISSING",
      "issues": ["agents/agent.py creates local CODS instance"],
      "suggested_fix": "Move CODS to global singleton pattern"
    },
    ...
  ]
}
```

Use the existing theory alignment checker:
```powershell
python theory_alignment_checker.py --grade
python theory_alignment_checker.py --fix-plan
```

---

## Part V: Fixing Strategy

### Fix Priority Matrix

Based on severity and theoretical alignment:

**Priority 1** (Fix immediately - system broken):
- Cross-layer circular dependencies
- CODS not centralized (if true)
- Stream B not querying database
- Silent failures in RLVR validation flow

**Priority 2** (Fix soon - features incomplete):
- Layer 2/3 circular dependencies
- Persona synthesis not happening
- Resonance detection not active
- Prestige not awarding correctly

**Priority 3** (Fix eventually - optimization):
- Layer 1 internal cycles
- Redundant imports
- Missing type hints
- Performance bottlenecks

### Systematic Fix Approach

#### Fix Template for Circular Dependencies

For each cycle identified in Phase 1:

**File**: `fixes/fix_cycle_[ID].md`
```markdown
# Fix Circular Dependency: [Cycle ID]

## Cycle Description
Files: [A.py, B.py, C.py]
Chain: A -> B -> C -> A

## Theoretical Issue
[Why this violates architecture, e.g., "Stream B should not import Agent"]

## Fix Strategy
Choose one:
1. **Dependency Injection**: Pass dependency as parameter
2. **Extract Interface**: Create abstract base class
3. **Late Import**: Import inside function (temporary fix)
4. **Extract Module**: Move shared code to new module
5. **Inversion**: Reverse dependency direction

## Chosen Strategy
[Strategy number and justification]

## Implementation Steps
1. [Specific code change 1]
2. [Specific code change 2]
3. [Run tests]
4. [Verify cycle broken with pydeps]

## Validation
```powershell
# After fix, verify cycle is gone
python analyze_dependencies.py --cycles
# Or direct pydeps:
pydeps module_name --show-cycles
```

## Tests
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] pydeps confirms cycle broken
- [ ] Theoretical architecture maintained
```

#### Example: Fixing Stream B <- -> Viral Packages Cycle

**Problem**: `stream_b.py` imports `viral_packages.py`, which imports `agent.py`, which imports `stream_b.py`

**Solution**: Extract database queries to separate module

```python
# OLD (circular):
# stream_b.py
from viral_packages import ViralPackageManager

class StreamB:
    def query_knowledge(self):
        manager = ViralPackageManager()
        return manager.get_packages()

# viral_packages.py
from agent import Agent

class ViralPackageManager:
    def spread_to_agents(self):
        agents = Agent.get_all()  # This creates cycle!

# NEW (no cycle):
# database/queries.py (NEW FILE)
def get_viral_packages(filters):
    """Pure database query, no agent logic"""
    conn = get_db_connection()
    return conn.execute("SELECT * FROM viral_information_packages WHERE ...").fetchall()

# stream_b.py
from database.queries import get_viral_packages

class StreamB:
    def query_knowledge(self):
        return get_viral_packages(self.filters)

# viral_packages.py
from database.queries import get_viral_packages

class ViralPackageManager:
    def spread_packages(self, agent_ids):
        # Receives agent IDs as parameter, doesn't import Agent
        packages = get_viral_packages()
        # ... spread logic
```

---

## Part VI: VS Code Copilot Workflow

### Master Fix Strategy

Use VS Code with Copilot for automated fixes. For large refactoring tasks, break them into focused prompts.

**Fix Plan Template** (for reference):
```markdown
# Master Fix Plan: AGI System Dependency Cleanup

## Phase 1: Critical Fixes (Do First)

### Fix 1: Centralize CODS
**Issue**: If agents create their own CODS instances
**Fix**: 
1. Create `cods/cods_singleton.py`
2. Implement singleton pattern
3. Update all agent files to use singleton
4. Test with 3 agents playing simultaneously

### Fix 2: Extract Database Queries
**Issue**: Circular imports through database access
**Fix**:
1. Create `database/queries.py`
2. Move all SQL queries here
3. Remove database imports from consciousness/ and agents/
4. Update imports everywhere

### Fix 3: Implement Late Imports (Temporary)
**Issue**: Circular imports we can't fix immediately
**Fix**:
1. Identify unavoidable cycles
2. Move imports inside functions
3. Add TODO comments for proper fix
4. Document in architecture_debt.md

## Phase 2: Data Flow Verification

### Verify 1: RLVR -> Primitive Unlocking
**Test**: Create test agent, achieve 20% improvement, verify primitive unlocked
**Files**: gameplay/*, cods/*, primitives/*
**Success**: Primitive appears in agent's toolkit

### Verify 2: Stream B Retrieval
**Test**: Create agent, query Stream B, verify packages returned
**Files**: consciousness/stream_b.py, database/*
**Success**: Agent receives non-empty list of packages

### Verify 3: Persona Synthesis
**Test**: Create high-conflict scenario, verify synthesis proposal generated
**Files**: consciousness/persona_ensemble.py, agents/*
**Success**: Synthesis proposal has surprise_score > 0

## Phase 3: Re-Architecture (If Needed)

### If Major Issues Found
Consider creating:
- `core/` - Pure business logic (no imports from layers above)
- `interfaces/` - Abstract base classes to break cycles
- `utils/` - Shared utilities (no domain logic)

## Validation After Each Fix
```bash
# 1. Check cycles removed [EXISTS]
python analyze_dependencies.py --cycles

# 2. Run tests [EXISTS]
pytest tests/ -v

# 3. Verify theory alignment [EXISTS]
python theory_alignment_checker.py --grade

# 4. Check for orphaned modules [EXISTS]
python analyze_dependencies.py --orphans
```

## Success Criteria
- [ ] Zero circular dependencies (pydeps clean)
- [ ] All 4 critical data flows working (tests pass)
- [ ] 100+ file tests complete successfully
- [ ] No silent failures in logs
- [ ] Architecture matches theoretical design
```

### Using VS Code Copilot for Fixes

Instead of running a CLI tool, use VS Code Copilot Chat:

1. **Open the file** with the circular dependency issue
2. **Ask Copilot** to fix it with context, e.g.:
   > "This file has a circular import with X. Extract the shared functionality to break the cycle."
3. **Verify the fix**:
   ```powershell
   python analyze_dependencies.py --cycles
   pytest tests/ -v
   ```
4. **Commit only when verified working**

---

## Part VII: Continuous Monitoring

### Daily Dependency Check

**IMPORTANT**: Use `safe_cleanup.py` for all database cleanup operations
- **Automatic**: Runs every 10 generations in `autonomous_evolution_runner.py`
- **Manual**: `python safe_cleanup.py` (dry run) or `python safe_cleanup.py --execute`
- **Preserves**: Winning sequences, active agents, positive scores, learned knowledge
- **Cleans**: Zero-score results, old logs, excess navigation history

**Script**: `scripts/check_dependencies.ps1` [TEMPLATE - Create if needed]
```powershell
# PowerShell script to check for circular dependencies

# Use the wrapper script
$result = python analyze_dependencies.py --cycles --quiet 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] CYCLES DETECTED!"
    Write-Host $result
    exit 1
} else {
    Write-Host "[OK] No cycles detected"
    exit 0
}
```

**Linux/macOS Alternative** (`scripts/check_dependencies.sh`):
```bash
#!/bin/bash
# Use the wrapper script
if ! python analyze_dependencies.py --cycles --quiet; then
    echo "[FAIL] CYCLES DETECTED!"
    exit 1
fi
echo "[OK] No cycles detected"
```

### Integration Tests

**File**: `tests/test_critical_flows.py` [TEMPLATE - Create if needed]
```python
"""Test critical data flows match theoretical architecture"""

import pytest
from agents.agent import Agent
from cods.oracle import get_cods_instance
from consciousness.stream_b import StreamB
from database.queries import get_viral_packages

def test_cods_is_centralized():
    """Verify CODS is singleton, not per-agent"""
    agent1 = Agent(agent_id=1)
    agent2 = Agent(agent_id=2)
    
    cods1 = get_cods_instance()
    cods2 = get_cods_instance()
    
    assert cods1 is cods2, "CODS should be singleton"
    assert not hasattr(agent1, 'cods'), "Agent should not own CODS"

def test_stream_b_queries_database():
    """Verify Stream B gets data from database, not other agents"""
    agent = Agent(agent_id=1)
    stream_b = StreamB(agent_id=1)
    
    packages = stream_b.query_knowledge(game_type='symmetry')
    
    assert isinstance(packages, list), "Should return list of packages"
    assert len(packages) >= 0, "Should handle empty results"
    # Verify it came from database
    db_packages = get_viral_packages({'game_type': 'symmetry'})
    assert packages == db_packages, "Stream B should match direct DB query"

def test_rlvr_to_unlock_flow():
    """Verify RLVR validation unlocks primitives"""
    agent = Agent(agent_id=1)
    initial_primitives = len(agent.get_primitives())
    
    # Simulate high-performance gameplay
    agent.play_game(game_id='test_001')
    agent.record_performance(improvement=0.25)  # 25% improvement
    
    # CODS should analyze and unlock
    cods = get_cods_instance()
    cods.analyze_agent_performance(agent.agent_id)
    
    # Verify primitive unlocked
    final_primitives = len(agent.get_primitives())
    assert final_primitives > initial_primitives, "Should unlock primitive"

def test_persona_synthesis_on_conflict():
    """Verify personas synthesize when streams conflict"""
    agent = Agent(agent_id=1)
    agent.streams.A.prediction = "move_left"
    agent.streams.B.prediction = "move_right"  # Conflict!
    
    proposals = agent.persona_ensemble.generate_proposals()
    
    # Should have synthesis proposal
    synthesis_proposals = [p for p in proposals if p.is_synthesis]
    assert len(synthesis_proposals) > 0, "Should generate synthesis on conflict"
    
    # Synthesis should have higher surprise potential
    synthesis = synthesis_proposals[0]
    assert synthesis.surprise_score > 0.3, "Synthesis should be surprising"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
# Run existing tests [EXISTS]
pytest tests/ -v

# Or run specific test file if created
# pytest tests/test_critical_flows.py -v
```

---

## Part VIII: Emergency Procedures

### If System Completely Broken

**Emergency Fix Script**: `scripts/emergency_reset.sh` [TEMPLATE - Create if needed]
```bash
#!/bin/bash

echo "🚨 EMERGENCY SYSTEM RESET"

# 1. Backup current state
timestamp=$(date +%Y%m%d_%H%M%S)
cp -r . "../backup_$timestamp"
echo "[OK] Backup created: ../backup_$timestamp"

# 2. Reset database
sqlite3 database/core_data.db < database/schema.sql
echo "[OK] Database reset"

# 3. Clear compiled Python
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete
echo "[OK] Cleared Python cache"

# 4. Verify imports work
python -c "
import sys
sys.path.insert(0, '.')
try:
    from agents.agent import Agent
    from cods.oracle import get_cods_instance
    from consciousness.stream_b import StreamB
    print('[OK] Core imports working')
except ImportError as e:
    print(f'[FAIL] Import error: {e}')
    sys.exit(1)
"

# 5. Run a quick syntax check
python -m py_compile core_gameplay.py

echo "[OK] Emergency reset complete"
```

### Rollback to Working State

```bash
# If fix broke something, rollback
git checkout HEAD~1  # Go back one commit
git checkout -b emergency-rollback

# Or restore from backup
cp -r ../backup_TIMESTAMP/* .
```

---

## Part IX: Success Metrics

### How to Know It's Working

**Metric 1: Zero Cycles**
```powershell
# Use the wrapper script
python analyze_dependencies.py --cycles
# Should output: "No circular dependencies found"
```

**Metric 2: Data Flows Work**
```bash
# Run existing tests [EXISTS]
pytest tests/ -v
# All tests should pass
```

**Metric 3: Agents Actually Learn**
```sql
-- Run in: sqlite3 core_data.db
-- Check if primitives are being unlocked
SELECT COUNT(*) FROM primitive_unlock_attempts WHERE status = 'SUCCESS';
-- Should increase over time

-- Check if viral packages are spreading
SELECT COUNT(*) FROM agent_viral_infections WHERE infection_date > datetime('now', '-1 hour');
-- Should be non-zero during gameplay
```

**Metric 4: Theoretical Alignment**
```bash
# Verify architecture matches theory [EXISTS]
python theory_alignment_checker.py --grade
# Should output score and any issues found
```

---

## Part X: Advanced Techniques

### Using PyDeps for Architecture Enforcement

**Script**: `scripts/enforce_architecture.py` [TEMPLATE - Create if needed]
```python
"""Enforce architectural rules using pydeps output"""

import subprocess
import json
import sys

# Architectural rules
RULES = {
    "layer_1_files": ["database/", "network/"],
    "layer_2_files": ["cods/", "primitives/", "operators/"],
    "layer_3_files": ["agents/", "consciousness/", "gameplay/"],
    "forbidden_imports": [
        ("layer_1", "layer_2"),  # Layer 1 cannot import Layer 2
        ("layer_1", "layer_3"),  # Layer 1 cannot import Layer 3
        ("layer_2", "layer_3"),  # Layer 2 cannot import Layer 3
    ]
}

def get_layer(filepath):
    """Determine which layer a file belongs to"""
    for layer_name, prefixes in [("layer_1", RULES["layer_1_files"]),
                                   ("layer_2", RULES["layer_2_files"]),
                                   ("layer_3", RULES["layer_3_files"])]:
        for prefix in prefixes:
            if filepath.startswith(prefix):
                return layer_name
    return "unknown"

def check_architectural_violations():
    """Check if any imports violate architectural layers"""
    # Use analyze_dependencies.py which wraps pydeps
    result = subprocess.run(
        ["python", "analyze_dependencies.py", "--cycles", "--quiet"],
        capture_output=True,
        text=True
    )
    
    violations = []
    # Parse output and check for violations
    # (Implementation details depend on pydeps output format)
    
    return violations

if __name__ == "__main__":
    violations = check_architectural_violations()
    if violations:
        print("[FAIL] ARCHITECTURAL VIOLATIONS DETECTED:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("[OK] Architecture is clean")
        sys.exit(0)
```

### Pre-Commit Hook

**Option 1: PowerShell** (`.git/hooks/pre-commit.ps1`):
```powershell
Write-Host "Checking for circular dependencies..."

# Run cycle check using wrapper
$result = python analyze_dependencies.py --cycles --quiet 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] COMMIT BLOCKED: Circular dependencies detected"
    Write-Host $result
    exit 1
}

Write-Host "[OK] Dependency checks passed"
exit 0
```

**Option 2: Bash** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash

echo "Checking for circular dependencies..."

# Run architecture enforcement using wrapper script
if ! python analyze_dependencies.py --cycles --quiet; then
    echo "[FAIL] COMMIT BLOCKED: Circular dependencies detected"
    echo "Fix cycles before committing. See architecture/Pydeps_Usage_Guide.md"
    exit 1
fi

echo "[OK] Dependency checks passed"
exit 0
```

Make executable (Linux/macOS only):
```bash
chmod +x .git/hooks/pre-commit
```

> **Windows Note**: Git hooks work on Windows without chmod. Just save the file with no extension for bash, or use `.ps1` extension for PowerShell hooks.

---

## Part XI: Common Issues and Solutions

### Issue 1: "Module not found" in pydeps

**Symptom**: `pydeps` reports module not found errors

**Solution**:
```powershell
# Windows: Ensure PYTHONPATH includes project root
$env:PYTHONPATH = "$(Get-Location);$env:PYTHONPATH"

# Or run with python -m
python -m pydeps core_gameplay --show-cycles

# Best: Use the wrapper script which handles paths
python analyze_dependencies.py --module core_gameplay
```

```bash
# Linux/macOS
export PYTHONPATH=$(pwd):$PYTHONPATH
python -m pydeps core_gameplay --show-cycles
```

### Issue 2: Too many cycles to visualize

**Symptom**: SVG file is unreadable due to complexity

**Solution**:
```powershell
# Focus on specific module
python analyze_dependencies.py --module cods_engine

# Or limit depth with direct pydeps
pydeps core_gameplay --max-bacon=2 -o diagrams/core_limited.svg

# Generate focused diagrams for key subsystems
python analyze_dependencies.py --core      # Core gameplay only
python analyze_dependencies.py --reasoning # Reasoning engines only
```

### Issue 3: Large refactoring overwhelms context

**Symptom**: Copilot loses track during complex multi-file refactoring

**Solution**:
Break into smaller, focused tasks:
```powershell
# Instead of one big refactor, do incremental fixes:

# Step 1: Fix one cycle
# Ask Copilot: "Fix the circular import between stream_b.py and viral_packages.py"

# Step 2: Verify
python analyze_dependencies.py --cycles

# Step 3: Fix next cycle
# Repeat until all cycles resolved
```

### Issue 4: Fixes break tests

**Symptom**: After fixing cycle, tests fail

**Solution**:
```powershell
# Revert and analyze
git checkout HEAD~1

# Check what tests expect
pytest tests/ -v --tb=long

# Ask Copilot to update tests:
# "Update tests in tests/ to work with new import structure where database queries are now centralized"
```

---

## Part XII: Documentation Maintenance

### Update After Each Major Fix

**File**: `docs/ARCHITECTURE_CHANGELOG.md`
```markdown
# Architecture Changelog

## 2026-01-12: Dependency Cleanup
- **Fixed**: Circular dependency between stream_b.py and viral_packages.py
- **Method**: Extracted database queries to database/queries.py
- **Impact**: Stream B now cleanly queries database without agent imports
- **Tests**: test_stream_b_queries_database() passes

## 2026-01-12: CODS Centralization
- **Fixed**: Agents were creating individual CODS instances
- **Method**: Implemented singleton pattern in cods/cods_singleton.py
- **Impact**: All agents now share single CODS validator
- **Tests**: test_cods_is_centralized() passes
```

### Architecture Diagram

Update as system evolves:

**File**: `docs/CURRENT_ARCHITECTURE.md`
```markdown
# Current System Architecture (As-Implemented)

## Layer 1: Database (No imports from above)
- database/core_data.db
- database/schema.sql
- database/queries.py (NEW: Central query module)

## Layer 2: Knowledge Management (Imports Layer 1 only)
- cods/cods_singleton.py (NEW: Centralized validator)
- cods/pattern_validator.py
- cods/primitive_unlocker.py
- network/viral_package_manager.py
- primitives/primitive_registry.py

## Layer 3: Agent Cognition (Imports Layers 1-2)
- agents/agent.py
- consciousness/stream_a.py
- consciousness/stream_b.py (NOW USES: database/queries.py)
- consciousness/persona_ensemble.py
- gameplay/core_gameplay.py

## Key Design Decisions
1. **Database queries centralized**: All SQL in database/queries.py
2. **CODS is singleton**: Single instance for entire population
3. **Roles are emergent**: Based on agents.self_network_bias
4. **Personas create synthesis**: Implements internal dialogue
```

---

## Part XIII: Final Checklist

### Forbidden Actions During Fixes

**DO NOT**:
- Mix prestige and action budgets in any fix
- Create test/mock games or simulated data
- Use file-based logging (use database_logger.py)
- Allow .pyc files to persist
- Commit to git before real evolution testing
- Create orphaned/duplicate code
- Hard-code game solutions
- Tell agents HOW to play games (defeats generalization)

**ALWAYS**:
- Use real ARC AGI 3 API
- Store everything in database
- Test with live data
- Update documentation on changes
- Think network-centrically
- Maintain three-layer separation (Genome/Epigenetic/Somatic)
- Respect agent role permissions

### Before Declaring Victory

- [ ] **Zero cycles confirmed**: `python analyze_dependencies.py --cycles` returns clean
- [ ] **All critical flows working**: Tests in `tests/` folder pass
- [ ] **CODS is centralized**: Only one instance exists
- [ ] **Stream B queries database**: No agent-to-agent imports
- [ ] **Personas synthesize**: Conflict detection -> synthesis generation
- [ ] **RLVR flow complete**: Performance -> CODS -> unlocking -> database
- [ ] **Prestige awarded**: Discoveries tracked in `agents.discovery_prestige`
- [ ] **Viral packages spread**: `agent_viral_infections` table populates
- [ ] **Resonance detection**: Cross-domain patterns logged
- [ ] **Architecture documented**: `progress.md` updated with changes
- [ ] **Tests passing**: `pytest tests/ -v` shows pass rate
- [ ] **Performance acceptable**: Evolution runs complete without errors
- [ ] **No orphaned modules**: `python analyze_dependencies.py --orphans` returns clean

### Success Signature

You'll know the system is working when:
1. **Agents play games** -> You see RLVR data in database
2. **CODS validates** -> Primitive unlock attempts logged
3. **Knowledge spreads** -> Viral packages appear in other agents
4. **Streams integrate** -> Conflict logs show A/B weighting
5. **Personas argue** -> Synthesis proposals generated
6. **System learns** -> Performance improves over generations

---

## Appendix A: Quick Reference Commands

### Actual Tools [EXISTS]
```bash
# Dependency analysis with stats
python analyze_dependencies.py --stats

# Check for orphaned modules
python analyze_dependencies.py --orphans

# Check for circular imports
python analyze_dependencies.py --cycles

# Generate dependency diagrams (saves to diagrams/ folder)
python analyze_dependencies.py --full --core --reasoning

# Theory alignment verification
python theory_alignment_checker.py --grade      # Self-grade (quick score)
python theory_alignment_checker.py              # Full report
python theory_alignment_checker.py --fix-plan   # Prioritized fixes

# Database cleanup
python safe_cleanup.py                          # Dry run
python safe_cleanup.py --execute                # Execute cleanup

# Run existing tests
pytest tests/ -v

# Check database state
sqlite3 core_data.db "SELECT COUNT(*) FROM viral_information_packages;"
```

### Template Commands (implement if needed)
```bash
# Direct pydeps usage (output to diagrams/ folder)
pydeps module_name --show-cycles -o diagrams/report.svg

# Check specific cycle
pydeps module_name --show-cycles | grep "cycle_file.py"
```

---

## Appendix B: Contact and Support

If you encounter issues not covered here:

1. **Check database logs**: Query `system_logs` table in `core_data.db`
2. **Review theory**: Re-read integration points in theoretical docs
3. **Test in isolation**: Create minimal reproduction script
4. **Document issue**: Add to `progress.md`
5. **Use analysis tools**: Run `python analyze_dependencies.py --stats --orphans`

---

**END OF MASTER GUIDE**

*This guide is living documentation. Update it as you fix issues and learn more about your system's behavior.*
