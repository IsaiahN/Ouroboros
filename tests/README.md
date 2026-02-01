# Tests

**Purpose**: Unit tests for core system components.
**Framework**: pytest

---

## Test Files

| File | Tests For | Priority |
|------|-----------|----------|
| `test_critical_systems.py` | Sequence system, pioneer assignment, budget preservation, validation rates | HIGH |
| `test_safe_cleanup.py` | SafeDatabaseCleaner functionality | HIGH |
| `test_new_modules.py` | New modules (hypothesis monitoring, emergency cleanup, etc.) | MEDIUM |
| `test_recent_changes.py` | Recent code changes (3-try fallback, social_rule_adherence, etc.) | MEDIUM |
| `test_sequence_system.py` | Sequence storage, retrieval, validation | HIGH |

---

## Running Tests

From the project root:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_critical_systems.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run tests matching a pattern
python -m pytest tests/ -k "sequence" -v
```

From the tests folder:

```bash
cd tests
$env:PYTHONPATH = ".."
python -m pytest . -v
```

---

## Test Categories (Per Master Ruleset)

The following systems should have test coverage:

1. **Sequence System** - Storage, retrieval, validation, matching
2. **Optimizer Checkpoints** - End subsequence append, replay completion
3. **Prestige Calculation** - Edge cases, dampening, caps
4. **Agent Role Assignment** - Correct game/level targeting
5. **Database Schema** - Consistency, integrity constraints

---

## Adding New Tests

1. Create test file: `test_<module_name>.py`
2. Import from parent directory: `from <module> import <Class>`
3. Use `unittest.TestCase` or pytest functions
4. Run tests before committing changes

---

**Note**: Tests reference the parent directory's modules. Ensure PYTHONPATH includes the project root.
