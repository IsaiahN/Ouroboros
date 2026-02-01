# Engines Refactoring TODO

**Created**: January 31, 2026  
**Updated**: January 31, 2026 (All phases complete!)  
**Goal**: Fix silent failures, add proper logging, split giant files, clean up registry

---

## Phase 1: Logging Infrastructure (P0) - COMPLETE

### 1.1 Create Unified Engine Logger - DONE
- [x] Created `engines/engine_logger.py`
  - Uses Python's `logging` module configured properly
  - Auto-tag with engine name via `get_engine_logger(name)`
  - Output to console AND database via `DatabaseLogHandler`
  - Structured context support via kwargs
  - Severity levels: DEBUG, INFO, WARNING, ERROR
  - Helper functions: `log_silent_failure()`, `log_import_error()`

```python
# Working API:
from engines.engine_logger import get_engine_logger, log_silent_failure
logger = get_engine_logger("viral_package")
logger.error("Failed to create package", exc=e, game_id=game_id)
log_silent_failure(logger, "operation_name", exception, {"context": "data"})
```

### 1.2 Configure Root Logger - DONE
- [x] engine_logger.py includes `DatabaseLogHandler` integration
- [x] Console handler with `[engine:LEVEL]` format
- [x] All engine logs route to `system_logs` table

---

## Phase 2: Fix Silent Failures (P0) - COMPLETE

### 2.1 `engines/registry.py` - DONE (refactored from 872 lines to ~560 lines)
- [x] Replaced 20+ `except ImportError: pass` blocks with data-driven loading
- [x] Created `ENGINE_CONFIGS` dict with 35 engine configurations
- [x] Single `_load_engine()` method handles all loading
- [x] Uses `log_import_error()` for all failures
- [x] Tracks `_load_errors` dict for diagnostics

### 2.2 `engines/social/viral_package_engine.py` - DONE
All silent failures fixed:
- [x] Line 76: Schema migration - now logs with `logger.debug()`
- [x] Line 139: Column addition - now logs
- [x] Line 377: JSON parsing - now catches `(json.JSONDecodeError, TypeError)`
- [x] Line 764-770: Loop bare excepts - now catch specific exceptions
- [x] Line 900, 911: Package tracking - now uses `log_silent_failure()`
- [x] Line 1138: Max beaten level - now uses `log_silent_failure()`
- [x] All `[VIRAL]`, `[PARIAH]` error prints - now use `logger.error()`

### 2.3 `engines/social/hypothesis_system.py` - DONE
- [x] Updated to use `get_engine_logger()` instead of `logging.getLogger()`
- [x] All `except: pass` blocks now catch `Exception`
- [x] Line 317, 905: Now use `log_silent_failure()`

### 2.4 `engines/social/cods_engine.py` - DONE
- [x] Updated to use `get_engine_logger()` 
- [x] All 6 silent failures fixed with specific exception types and logging

### 2.5 Other engines fixed:
- [x] `engines/self_model/symbolic_tracker.py` - Updated to engine_logger
- [x] `engines/planning/replay_learning_engine.py` - Added logger, fixed 4 bare excepts
- [x] `engines/planning/sequence_abstraction.py` - Updated to engine_logger, fixed 1 bare except

---

## Phase 3: Replace print() with Logger (P1) - COMPLETE for error/warning prints

### 3.1 Files with [WARN]/[ERROR] print() statements - DONE
- [x] `engines/postgame/fitness_calculator.py` - Now uses `logger.warning()`
- [x] `engines/postgame/lessons_extractor.py` - Now uses `logger.warning()`
- [x] `engines/postgame/orchestrator.py` - Now uses `logger.warning()`
- [x] `engines/social/viral_package_engine.py` - 25+ prints converted to logger calls

### 3.2 Files with debug print() statements - INTENTIONALLY KEPT
These are in docstrings, example blocks, or dashboard display functions:
- `engines/self_model/*.py` - Example usage in docstrings
- `engines/decision/__init__.py` - Example usage
- `engines/social/viral_package_engine.py` - Dashboard display function
- `engines/social/prestige_engine.py` - Leaderboard display function
- `engines/planning/sequence_abstraction.py` - Demo/test section

---

## Phase 4: Split Giant Files (P2) - COMPLETE

### 4.1 `engines/social/cods_engine.py` - DEPRECATED & REPLACED

**CODS System Deprecated (Jan 31 2026):**
The entire CODS (Cognitive Operator Discovery System) has been deprecated and replaced
with a simpler `PrimitiveSuggester` (~680 lines vs ~8,000 lines).

**Key insight**: All 315 seed primitives were always available via `seed_primitives.py`.
The elaborate "unlock ceremony" (Bayesian hypothesis testing, Oracle approval, cross-agent
replication) was solving a problem that didn't exist.

**New approach**:
- All primitives always available (no unlock gates)
- RLVR feedback tracks which primitive→action mappings work per game type
- Higher-performing primitives get suggested more often

**Files moved to `deprecated/cods_system/`:**
- cods_engine.py (4,925 lines)
- oracle_interface.py (936 lines)
- bayesian_hypothesis_engine.py (652 lines)
- operator_lifecycle_manager.py (497 lines)
- operator_composer.py
- primitive_unlock_manager.py (990 lines)
- remote_effect_learner.py (330 lines)
- execution_trace_miner.py (200 lines)
- test_cods*.py (test files)
- check_cods_status.py, check_primitives.py (manual tools)

**New file created:**
- [x] `engines/social/primitive_suggester.py` - PrimitiveSuggester class (680 lines)

**Result**: ~92% code reduction (8,000+ → 680 lines)

### 4.2 `engines/consciousness/i_thread.py` - DONE

**Extracted (Jan 2026):**
- [x] `engines/consciousness/i_thread_types.py` - All types, enums, dataclasses (996 lines):
  - DeathType, DeathPersona, DEATH_PERSONAS, DEATH_PHILOSOPHIES
  - ROLE_DEFAULT_WEIGHTS, ROLE_TENSION_PROFILES, THINKING_BUDGET_CONFIG
  - StreamProposal, ConflictResult, SynthesisResult, NoveltyConfig
  - EpisodicMemory, AgentNarrative, MortalityState (with 18 methods)
  - GutInstinctResult, DeliberationResult, ReasoningLog, IThreadState, MultiConflictResult

- [x] `engines/consciousness/deliberation_engine.py` - DeliberationEngine class (1,268 lines):
  - DELIBERATION_CONFIG constant
  - compute_deliberation_budget() method
  - capture_gut_instinct() method  
  - conduct_deliberation() method with full reasoning system
  - All phenomenological feeling tracking (resonance, deja_vu, insight, etc.)
  - RLVR data query and analysis integration

**Cleanup completed (Jan 31 2026):**
- [x] Removed ~2,700 lines of duplicate/orphaned code from i_thread.py
- [x] Added delegation methods to IThread class for backwards compatibility
- [x] Fixed missing `Any` import in i_thread_types.py

**Result**: Reduced from ~4,500 to 1,566 lines (~65% reduction)

### 4.3 `engines/perception/terminal_pattern_detector.py` - DONE

**Split completed (Jan 2026):**
- [x] `engines/perception/terminal/__init__.py` - Exports + TerminalPatternDetector facade
- [x] `engines/perception/terminal/death_zones.py` - DeathZoneTracker class (289 lines)
- [x] `engines/perception/terminal/dangerous_objects.py` - DangerousObjectTracker class (240 lines)
- [x] `engines/perception/terminal/game_over_theory.py` - GameOverTheorySystem class (372 lines)
- [x] Backwards-compatible import maintained

**Result**: Reduced from 2,282 to 1,397 lines (~39% reduction)

### 4.4 `engines/social/viral_package_engine.py` - DONE

**Split completed (Feb 2026):**
- [x] `engines/social/pariah_manager.py` - PariahManager class (827 lines):
  - Pariah creation, analysis, and spreading
  - Pariah action penalties (level-aware decay)
  - Role-adjusted penalties with network paralysis detection
  - Pariah lifecycle (decay, obsolescence, cleanup)
  - Dashboard methods (get_top_pariahs)

- [x] `engines/social/viral_package_engine.py` - Refactored to use composition:
  - Imports PariahManager and delegates all pariah methods
  - Backwards-compatible wrappers for all pariah methods
  - Clean separation of viral packages vs pariah management

**Result**: Reduced from 2,041 to 1,296 lines (~37% reduction)
**Total**: viral_package_engine.py (1,296) + pariah_manager.py (827) = 2,123 lines
(slight increase due to delegation wrappers and proper docstrings)

---

## Phase 5: Data-Driven Registry (P1) - COMPLETE

### 5.1 Refactor `engines/registry.py` - DONE
- [x] Created `ENGINE_CONFIGS` dict with `EngineConfig` dataclass (35 engine configurations)
- [x] Single `_load_engine(name)` method handles all loading via `importlib.import_module()`
- [x] Uses `log_import_error()` for all failures (no silent failures)
- [x] Tracks `_load_errors` dict for diagnostics
- [x] Property accessors maintained for IDE autocomplete
- [x] Updated to use `primitive_suggester` instead of deprecated `cods_engine`

**Result**: Reduced from 872 lines (20+ individual loaders) to ~560 lines (data-driven)

---

## Phase 6: Populate __init__.py Exports (P3) - COMPLETE

### 6.1 Update module __init__.py files - DONE
- [x] `engines/perception/__init__.py` - Exports VisualAnalyzer, TerminalPatternDetector, get_object_detector()
- [x] `engines/self_model/__init__.py` - Exports 18+ classes (comprehensive)
- [x] `engines/social/__init__.py` - Exports with lazy loading, includes PrimitiveSuggester, deprecated CODS stub
- [x] `engines/regulation/__init__.py` - Exports FrustrationDetector, ImaginationBudgetManager, lazy loaders
- [x] `engines/memory/__init__.py` - Exports EpisodicMemorySystem, get_near_miss_analyzer()
- [x] `engines/cognition/__init__.py` - Exports CognitiveStageSystem, MetacognitiveReasoningEngine
- [x] `engines/planning/__init__.py` - Exports SubgoalPlanner, SequenceAbstraction, get_replay_learning_engine()

---

## Execution Order

1. **Week 1: Logging** (Phase 1 + 2)
   - Create engine_logger.py
   - Fix silent failures in viral_package_engine.py (most critical)
   - Fix silent failures in registry.py
   
2. **Week 2: Registry + Prints** (Phase 3 + 5)
   - Implement data-driven registry
   - Replace print() statements with logger

3. **Week 3: Split Files** (Phase 4)
   - Split cods_engine.py (biggest)
   - Split i_thread.py
   - Split terminal_pattern_detector.py
   - Split viral_package_engine.py

4. **Week 4: Polish** (Phase 6)
   - Update __init__.py exports
   - Final testing
   - Remove any remaining dead code

---

## Success Criteria

- [x] Zero bare `except: pass` in engines/ (verified: 0 matches)
- [x] All errors logged to database AND console
- [x] No files over 2,000 lines in engines/ (verified: largest is i_thread.py at 1,566)
- [x] Registry uses data-driven loading (ENGINE_CONFIGS dict)
- [x] All __init__.py files have proper exports
- [x] `Select-String -Pattern "except.*pass"` returns 0 results (verified)
- [x] Print statements only in dashboards/examples (intentionally kept)

---

## Notes

- Keep backwards-compatible imports when splitting files
- Test each change against live evolution run
- Follow Rule 2: All logs go to database
- Follow Rule 11: No Unicode emojis in log messages
