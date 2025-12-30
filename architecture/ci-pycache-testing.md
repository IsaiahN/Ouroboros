# CI and Runtime Pycache/Test Enforcement

Goal: enforce PYTHONDONTWRITEBYTECODE=1 (or python -B) everywhere; fail fast if __pycache__ appears; bake testing gates into CI/tasks.

## Runtime/Local Invocation
- Preferred: run all entry points with `python -B ...` to suppress pycache globally.
- Also set env: `PYTHONDONTWRITEBYTECODE=1` in task runners/launch configs as defense in depth.
- Add a startup guard that scans for __pycache__ after import; fail if found.

## sitecustomize.py (optional shared bootstrap)
- Place a sitecustomize.py at repo root or in PYTHONPATH that:
  - Sets `os.environ['PYTHONDONTWRITEBYTECODE'] = '1'` if not already set.
  - On import, scans for `__pycache__` directories under project root; if any exist, log and optionally raise in non-dev modes.
- Ensure PYTHONPATH includes repo root when running python so sitecustomize.py loads automatically.

## CI Strategy
- Use `python -B -m pytest` as the default test command.
- Pre-test step: `python -c "import sys; sys.exit(1 if '__pycache__' in '\n'.join([p for p in []]) else 0)"` is insufficient—use a real scan:
  - `python - <<'PY'
import os, sys
bad = []
for root, dirs, _ in os.walk('.'):
    for d in list(dirs):
        if d == '__pycache__':
            bad.append(os.path.join(root, d))
if bad:
    print('Found __pycache__:', bad)
    sys.exit(1)
PY`
- Post-test step: repeat the scan to ensure no pycache was created during tests.
- Optional: add a git clean check to ensure no pycache is introduced between steps.

## Task/launch.json Snippet (VS Code)
- Set env: `"PYTHONDONTWRITEBYTECODE": "1"` and args: `"-B"` for Python tasks.

## Make/Task Runner Example
- test: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest`
- lint: `PYTHONDONTWRITEBYTECODE=1 python -B -m ruff check .`
- pycache-check: run the os.walk script above.

## Enforcement Policy
- Any CI job fails if __pycache__ exists pre/post run.
- Any learning run must set python -B or PYTHONDONTWRITEBYTECODE=1; orchestrator should warn/abort if env not set.
- sitecustomize.py is allowed but must remain small, ASCII-only, and not introduce side-effects beyond pycache guard.
