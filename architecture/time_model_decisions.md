# Time Models: Generation vs Wall-Clock

This document clarifies when to use generation-based time versus wall-clock time in the BitterTruth-AI system.

## Core Principle

> **Wall-clock time measures compute speed. Generation time measures learning opportunity.**

A fast machine running 100 generations/hour should treat 50-generation-old knowledge identically to a slow machine that took 5 hours to reach the same point. The fast machine accumulated more experience, but the knowledge isn't "older" in evolutionary terms.

---

## Generation Time (Preferred for Learning)

**Use generation-based time for anything related to knowledge, learning, or evolutionary metrics.**

| System | What Uses Generation Time | Why |
|--------|--------------------------|-----|
| **EmbeddingMatcher** | `created_generation`, `access_count` | Recent embeddings should rank higher |
| **Prestige Engine** | `generations_since_update` | Already correct - social capital decays in evolutionary time |
| **Pariah Manager** | `generations_since_trigger` | Already correct - danger signals fade as system learns |
| **Terminal Pattern Detector** | `generations_since_death` | Already correct - death patterns may become outdated |
| **Hypothesis System** | `last_tested` generation | Hypotheses should be re-tested periodically |
| **Temporal Integrator** | EWMA windows in generations | Experience integration is hardware-agnostic |
| **KnowledgeProvenance** | `temporal_spread_generations` | Knowledge validated across many generations is more reliable |
| **Checkpoint Decay** | Frontier checkpoint relevance | Old checkpoints may be superseded |
| **Lesson Decay** | Game-specific lessons | Tactical knowledge becomes stale |

### Generation Clock Usage

```python
from engines.memory import GenerationClock, compute_relevance_score

# Get current time
clock = GenerationClock.instance()
current_gen = clock.generation
ctx = clock.get_context()

# Compute decay
from engines.memory import compute_generation_decay, DECAY_CONFIG

weight = compute_generation_decay(
    generations_elapsed=current_gen - created_gen,
    half_life_generations=DECAY_CONFIG.EMBEDDING_HALF_LIFE  # 30 gens
)

# Or use the full relevance formula
score = compute_relevance_score(
    base_similarity=0.85,
    generations_elapsed=20,
    access_count=5,
    half_life_generations=30.0,
    recency_weight=0.3
)
```

### Half-Life Reference

| Knowledge Type | Half-Life (Generations) | Rationale |
|---------------|------------------------|-----------|
| Death Patterns | 10 | Fast-changing tactical info |
| Lessons Learned | 15 | Game-specific, becomes stale |
| Hypotheses | 20 | Need periodic re-validation |
| Frame Embeddings | 30 | Structural knowledge, moderately stable |
| Frontier Checkpoints | 50 | Proven progress points |
| Winning Sequences | ∞ (no decay) | Proven correct, never expires |

### Cross-Domain Penalty

When knowledge crosses game boundaries, apply 0.7x half-life multiplier:

```python
half_life = DECAY_CONFIG.get_half_life('embedding', cross_domain=True)
# Returns 30 * 0.7 = 21 generations
```

---

## Wall-Clock Time (Keep for Operations)

**Use wall-clock time for infrastructure, performance, and human-facing operations.**

| System | What Uses Wall-Clock | Why |
|--------|---------------------|-----|
| **API Timeouts** | HTTP request deadlines | Network latency is real-world |
| **Database Timestamps** | `created_at`, `updated_at` | Audit trails for debugging |
| **Performance Profiling** | Deliberation timing | Measuring actual compute cost |
| **User-Facing Logs** | Timestamp displays | Humans think in seconds |
| **Rate Limiting** | API call throttling | External service constraints |
| **Deliberation Budget** | `budget_seconds` | LLM API response times |

### Examples of Correct Wall-Clock Usage

```python
# API timeout - real network latency
response = requests.get(url, timeout=5.0)  # 5 seconds

# Performance measurement
start = time.time()
result = expensive_operation()
elapsed_ms = (time.time() - start) * 1000

# Database audit trail
cursor.execute("""
    INSERT INTO logs (message, created_at)
    VALUES (?, CURRENT_TIMESTAMP)
""", (msg,))

# Deliberation budget (LLM has real response times)
budget_seconds = 2.0  # Think for up to 2 seconds
```

---

## Migration Checklist

When adding new time-dependent features, ask:

1. **Is this about knowledge/learning?** → Use generation time
2. **Is this about operations/infrastructure?** → Use wall-clock
3. **Does hardware speed affect the meaning?** → Use generation time
4. **Is this user-facing or for debugging?** → Use wall-clock

### Systems Already Migrated to Generation Time

- [x] Prestige decay (`engines/social/prestige_engine.py`)
- [x] Pariah toxicity decay (`engines/social/pariah_manager.py`)
- [x] Terminal pattern decay (`engines/perception/terminal_pattern_detector.py`)
- [x] Agent social relevance (`engines/consciousness/i_thread_types.py`)
- [x] Rung temporal modulation (`decision_rung_system.py`)
- [x] Embedding recency (`engines/self_model/embedding_matcher.py`)

### Systems Using Wall-Clock (Correctly)

- [x] API timeouts (`arc_api_client.py`)
- [x] Database timestamps (all tables)
- [x] Deliberation budgets (`engines/consciousness/deliberation_engine.py`)
- [x] Performance logging (`database_logger.py`)

---

## Architecture Note

The `GenerationClock` is a singleton that should be advanced by the evolution runner:

```python
# In autonomous_evolution_runner.py
from engines.memory import GenerationClock

clock = GenerationClock.instance()

for generation in range(start_gen, max_gen):
    clock.set_generation(generation, action=0)

    # Run generation...
    for action_num in range(actions_per_gen):
        clock.advance_action()
        # Execute action...
```

This keeps all components synchronized without passing generation numbers everywhere.
