# Vulture Dead Code Analysis Checklist
**Generated**: January 29, 2026  
**Command**: `python -m vulture [core files] --min-confidence 80`

---

## UNREACHABLE CODE (Critical - Must Fix)

- [x] **agent_self_model.py:5141** - unreachable code after `if` (100%)
  - **Verdict**: KEEP - Comment says "fallback return", but `return None` at 5154 is after a try/except, not unreachable. False positive from complex control flow.
  
- [x] **agent_self_model.py:13809** - unreachable code after `return` (100%)
  - **Verdict**: FIX - **DUPLICATE RETURN STATEMENT** - Line 13808 returns, then 13810 also returns. Bug!

---

## UNUSED IMPORTS (90% confidence)

### agent_self_model.py
- [x] Line 25: `IThreadType` - **KEEP** - Used in TYPE_CHECKING block for type hints
- [x] Line 29: `IThreadState` - **REMOVE** - Imported but also assigned None in except block, redundant

### autonomous_evolution_runner.py
- [x] Line 77: `PariahValidator` - **KEEP** - Used in `run_pariah_validation` which IS used
- [x] Line 116: Multiple metrics imports - **KEEP** - These are conditionally imported and assigned None in except block. Used when available.

### cods_engine.py
- [x] Line 40: `OperatorStatus` - **REMOVE** - Imported but never used
- [x] Line 1242: `cast` - **REMOVE** - Imported inside function but never used (only `TList`, `TUnion` used)

### core_gameplay.py
- [x] Line 63: `IThreadState` - **REMOVE** - IThread used, but IThreadState not referenced
- [x] Line 63: `MultiConflictResult` - **REMOVE** - Not used in code
- [x] Line 63: `NoveltyConfig` - **REMOVE** - Not used in code
- [x] Line 63: `StreamProposal` - **REMOVE** - Not used in code
- [x] Line 101: `GoalEvaluator` - **KEEP** - Assigned None in except block, used conditionally
- [x] Line 101: `SymbolicWorldModel` - **KEEP** - Same pattern, conditionally used
- [x] Line 188: `ReplayLearningContext` - **KEEP** - Assigned None in except block
- [x] Line 198: `UIDetector` - **KEEP** - Assigned None in except block
- [x] Line 10457: `_time_mod` - **REMOVE** - Imported but standard `time` module works fine

### database_interface.py
- [x] Line 16: `timezone` - **REMOVE** - Imported but `datetime.now().isoformat()` used instead

---

## UNUSED VARIABLES (100% confidence)

### agent_self_model.py
- [x] Line 11006: `private_strength` - **FIX** - Parameter received but not used in `_build_narrative`

### arc_api_client.py (Context Manager - intentional)
- [x] Line 169: `exc_tb`, `exc_type`, `exc_val` - **WHITELIST** - Required by `__aexit__` signature

### cods_engine.py
- [x] Line 1328: `validation_games` - **FIX** - Parameter unused, should validate or remove

### core_gameplay.py
- [x] Line 2781: `target_position` - **WHITELIST** - Parameter for future use, documented
- [x] Line 15649: `exc_tb`, `exc_type`, `exc_val` - **WHITELIST** - Required by `__aexit__` signature
- [x] Line 15800: `duration_seconds` - **FIX** - Parameter received but not used in tracking

### database_interface.py
- [x] Line 1739: `since_date` - **WHITELIST** - Placeholder method, documented as "Placeholder"
- [x] Line 1744: `before_date` - **WHITELIST** - Placeholder method, documented as "Placeholder"

### seed_primitives.py (many - placeholders for future implementation)
- [x] All 22 variables - **WHITELIST** - These are all in partially-implemented primitives, intentional placeholders

---

## Summary of Actions

| Action | Count | Description |
|--------|-------|-------------|
| **FIX** | 4 | Duplicate return, unused params that should be used |
| **REMOVE** | 7 | Unused imports safe to delete |
| **WHITELIST** | 28 | Intentional: signatures, placeholders, conditionals |
| **KEEP** | 8 | Used but vulture can't detect (TYPE_CHECKING, conditionals) |

---

## Fix Plan

1. **agent_self_model.py:13809** - Remove duplicate `return new_wA, new_wB`
2. **cods_engine.py:40** - Remove `OperatorStatus` from import
3. **cods_engine.py:1242** - Remove `cast` from inline import
4. **core_gameplay.py:63** - Remove `IThreadState`, `MultiConflictResult`, `NoveltyConfig`, `StreamProposal`
5. **core_gameplay.py:10457** - Remove `import time as _time_mod`
6. **database_interface.py:16** - Remove `timezone` from import
7. Create `.vulture_whitelist.py` for intentional unused code

