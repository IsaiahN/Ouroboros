# Frontier Checkpoint System
**Version**: 1.1  
**Date**: January 27, 2026  
**Status**: IMPLEMENTED  
**Purpose**: Constructive pathfinding for hard frontier levels through incremental progress tracking

---

## Problem Statement

**Current approach (elimination-based)**:
- Death avoidance system catalogs 100 ways to die
- Agent must randomly discover the 1 way to win
- No memory of GOOD moves, only BAD moves
- Each agent starts from scratch on frontier levels

**The waste**:
- Agent A survives 12 actions, dies on action 13
- Agent B starts from action 1 again, not action 12
- Progress is lost, exploration restarts

---

## Solution: Constructive Pathfinding

Build winning sequences incrementally by:
1. Tracking the BEST partial progress on each frontier level
2. Replaying known-good prefixes to skip explored territory
3. Exploring ONLY from the frontier of knowledge
4. Extending checkpoints when new progress is made

```
Agent A: Actions 1-8 (good), action 9 (death)
         → Checkpoint saved: [1,4,3,2,6,4,1,3] (8 actions)

Agent B: Replay checkpoint [1,4,3,2,6,4,1,3]
         → Now at known-good state in 8 actions (no decision cost)
         → Explore from here: actions 9-14 (good), action 15 (death)
         → Checkpoint EXTENDED: [1,4,3,2,6,4,1,3,2,1,4,6,3,1] (14 actions)

Agent C: Replay extended checkpoint...
         → Eventually: Full level completion
         → Save to winning_sequences
         → Checkpoint collection STOPS for this level
```

---

## Database Schema

```sql
CREATE TABLE frontier_checkpoints (
    -- Composite primary key for natural deduplication
    game_type TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    terminal_frame_hash TEXT NOT NULL,
    
    -- The action sequence that reaches this state
    action_sequence TEXT NOT NULL,      -- JSON array: [1,4,3,2,6,...]
    actions_count INTEGER NOT NULL,
    
    -- Progress metrics (game-agnostic)
    unique_frames_seen INTEGER DEFAULT 0,   -- Exploration diversity
    survival_score REAL DEFAULT 0,          -- Composite ranking metric
    
    -- Terminal state info
    terminal_reason TEXT,                   -- 'death' | 'stuck' | 'exploring' | 'timeout'
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,           -- How often replayed as base
    times_extended INTEGER DEFAULT 0,       -- How often someone built on this
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    
    -- Composite primary key: One row per unique terminal state per level
    PRIMARY KEY (game_type, level_number, terminal_frame_hash)
);

-- Index for fast "get best checkpoint" queries
CREATE INDEX idx_frontier_checkpoints_best 
ON frontier_checkpoints(game_type, level_number, survival_score DESC);

-- Index for cleanup queries
CREATE INDEX idx_frontier_checkpoints_usage
ON frontier_checkpoints(game_type, level_number, times_extended DESC, created_at);
```

---

## Key Design Decisions

### 1. Terminal Frame Hash as Deduplication Key

**Rationale**: Multiple action sequences can reach the SAME game state. We only need to keep the BEST path to each unique state.

**Example**:
- Path A: [1,4,3,2] → arrives at frame_hash "abc123"
- Path B: [4,1,2,3] → arrives at frame_hash "abc123" (same state!)
- Keep only the one with better survival_score

**UPSERT logic**:
```sql
INSERT INTO frontier_checkpoints (...) VALUES (...)
ON CONFLICT (game_type, level_number, terminal_frame_hash) DO UPDATE SET
    action_sequence = CASE 
        WHEN excluded.survival_score > frontier_checkpoints.survival_score 
        THEN excluded.action_sequence 
        ELSE frontier_checkpoints.action_sequence 
    END,
    actions_count = CASE 
        WHEN excluded.survival_score > frontier_checkpoints.survival_score 
        THEN excluded.actions_count 
        ELSE frontier_checkpoints.actions_count 
    END,
    survival_score = MAX(frontier_checkpoints.survival_score, excluded.survival_score),
    unique_frames_seen = MAX(frontier_checkpoints.unique_frames_seen, excluded.unique_frames_seen),
    times_extended = frontier_checkpoints.times_extended + 1,
    last_used_at = CURRENT_TIMESTAMP;
```

### 2. Survival Score (Composite Metric)

Game-agnostic progress signal combining:
- **unique_frames_seen**: Exploration diversity (not oscillating)
- **actions_count**: How long survived
- **oscillation_penalty**: Deduct for revisiting same frames

**Formula**:
```python
survival_score = (unique_frames_seen * 10) + actions_count - (oscillation_count * 5)
```

**Why this works without game knowledge**:
- More unique frames = exploring new territory (good)
- More actions = survived longer (good)
- Oscillation = stuck in loop (bad)

### 3. Lifecycle: Frontier → Beaten

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTIER LEVEL                           │
│                (no winning_sequence exists)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Checkpoint Collection ACTIVE                         │   │
│  │ - Save progress after each attempt                   │   │
│  │ - UPSERT: keep best path to each terminal state      │   │
│  │ - Agents replay best checkpoint, explore from there  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│               Level Completion Achieved                     │
│                           │                                 │
│                           ▼                                 │
│           Save to winning_sequences table                   │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     BEATEN LEVEL                            │
│                (winning_sequence exists)                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Checkpoint Collection STOPPED                        │   │
│  │ - Guard prevents new checkpoint saves                │   │
│  │ - Old checkpoints PRESERVED (historical data)        │   │
│  │ - Agents use winning_sequence for replay             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Don't Delete Old Checkpoints

**Rationale**: Historical data may be valuable for:
- Debugging why certain paths failed
- Alternative route discovery (if winning sequence invalidated)
- Analysis of exploration patterns

**Implementation**: Guard on INSERT, not DELETE
```python
def save_frontier_checkpoint(self, game_type, level, ...):
    # Guard: Only save if level is STILL frontier
    existing_win = self.db.execute_query("""
        SELECT 1 FROM winning_sequences 
        WHERE game_type = ? AND level = ? AND is_active = 1
        LIMIT 1
    """, (game_type, level))
    
    if existing_win:
        return None  # Level beaten, don't create new checkpoints
    
    # Proceed with UPSERT...
```

---

## Integration Points - Mapped to Existing Code

### Existing Infrastructure to REUSE

| Component | Location | Purpose | Reuse For |
|-----------|----------|---------|-----------|
| `_recent_action_traces` | `core_gameplay.py:1836, 9154` | Stores action history per game | Checkpoint action sequence source |
| `unique_frames_this_level` | `core_gameplay.py:27449` (`GameLoopState`) | Tracks unique frame hashes | `unique_frames_seen` metric |
| `compute_frame_hash()` | `terminal_pattern_detector.py:338` | Creates hash of game frame | `terminal_frame_hash` field |
| `_compute_frame_hash()` | `core_gameplay.py:6452, 27201` | Local frame hash (same algorithm) | Alternative if TPD unavailable |
| `_replay_sequence_inline()` | `core_gameplay.py:26816` | Replays action sequence in game | Checkpoint replay |
| `level_breakpoints` | `core_gameplay.py:25937-25944` | Tracks level boundaries in sequences | Useful for multi-level checkpoints |
| `_is_frontier_level()` | `core_gameplay.py` | Checks if level has winning_sequences | Guard for checkpoint saves |
| `CODSContext.is_frontier` | `cods_engine.py:92` | Frontier flag in reasoning context | Trigger for checkpoint mode |

### 1. Recording Checkpoints (after frontier level death)

**Insert at**: `core_gameplay.py` after death detection (~line 8155)

**Trigger conditions** (using existing data):
- `CODSContext.is_frontier == True` (from `cods_engine.py`)
- `loop_state.level_action_count >= 3` (from `core_gameplay.py:1510`)
- `len(loop_state.unique_frames_this_level) > level_action_count / 3` (oscillation filter)

**Data sources** (all existing):
```python
checkpoint_data = {
    'game_type': game_id[:4],                                    # Already parsed everywhere
    'level_number': loop_state.current_level,                    # GameLoopState field
    'terminal_frame_hash': self._compute_frame_hash(game_state.frame),  # core_gameplay.py:6452
    'action_sequence': json.dumps([t['action_type'] for t in self._recent_action_traces]),  # line 9154
    'actions_count': loop_state.level_action_count,              # core_gameplay.py:1510
    'unique_frames_seen': len(loop_state.unique_frames_this_level),  # core_gameplay.py:27449
    'survival_score': self._compute_survival_score(...)          # NEW: simple formula
}
```

### 2. Querying Best Checkpoint (at level start)

**Insert at**: `core_gameplay.py` when starting a new level (~line 4200)
- Existing code at `_handle_level_transition()` already handles level start logic
- After determining level is frontier, query for checkpoint

**Query** (new DB query):
```sql
SELECT action_sequence, actions_count, terminal_frame_hash
FROM frontier_checkpoints
WHERE game_type = ? AND level_number = ?
ORDER BY survival_score DESC, times_extended DESC
LIMIT 1;
```

**Integration with existing replay**:
- `_replay_sequence_inline()` at line 26816 already handles action replay
- It has level_breakpoints support for partial replay
- Checkpoint replay can use SAME mechanism with a "pseudo-sequence" dict:
```python
checkpoint_as_sequence = {
    'sequence_id': f'checkpoint_{game_type}_{level}',
    'action_sequence': checkpoint['action_sequence'],
    'level_number': level,
    'level_breakpoints': {'1': 0}  # Single level checkpoint
}
# Then call existing replay:
await self._replay_sequence_inline(game_state, checkpoint_as_sequence)
```

### 3. Replaying Checkpoint (reuse existing replay)

**Location**: Use existing `_replay_sequence_inline()` at `core_gameplay.py:26816`

**Existing capabilities** (already implemented):
- Handles action-by-action replay (line 26920+)
- Validates game state during replay
- Handles replay failures gracefully
- Supports partial replay via `level_breakpoints`
- Frame matching for recovery (line 26876)

**Adaptation needed**:
- Wrap checkpoint data to look like a sequence dict
- Call `_replay_sequence_inline()` with checkpoint data
- Mark as "checkpoint mode" to skip full sequence recording

### 4. Integration with Death Avoidance

**Death avoidance already queries**: `position_death_patterns` table (line 8191)
- After checkpoint replay, agent is at NEW position
- Existing `_load_death_patterns()` will query for current position
- No changes needed - systems work independently

**Sequence**:
```
1. Query best checkpoint for this (game_type, level)
2. Replay checkpoint actions via _replay_sequence_inline()
3. Agent now at checkpoint terminal state
4. Existing death avoidance queries position_death_patterns
5. Agent explores NEW territory, avoiding known deaths
6. If death: record_position_death() + save_frontier_checkpoint()
7. If progress: checkpoint extended
```

### 5. Guard: Stop Saves After Win

**Insert check in**: New `save_frontier_checkpoint()` method

**Reuse existing query** from `_is_frontier_level()`:
```python
# From core_gameplay.py - already checks winning_sequences
def _is_frontier_level(self, game_id, level):
    game_type = game_id[:4]
    result = self.db.execute_query("""
        SELECT 1 FROM winning_sequences
        WHERE game_type = ? AND level_number = ? AND is_active = 1
        LIMIT 1
    """, (game_type, level))
    return not result  # True if NO winning sequence exists
```

### 6. Survival Score Calculation (NEW)

**New helper method**:
```python
def _compute_survival_score(self, unique_frames: int, action_count: int, 
                            oscillation_count: int = 0) -> float:
    """Game-agnostic progress metric - higher = better"""
    return (unique_frames * 10) + action_count - (oscillation_count * 5)
```

**Oscillation detection** (reuse existing):
- `loop_state.unique_frames_this_level` is a SET - size shows diversity
- Compare: `action_count - len(unique_frames)` = oscillation approximation

---

## Maintenance

### Periodic Cleanup (keep top 20 per level)

Run every N generations or when table exceeds threshold:

```sql
-- Keep only top 20 checkpoints per (game_type, level_number)
-- Prioritize: high survival_score, frequently extended
WITH ranked AS (
    SELECT 
        game_type, level_number, terminal_frame_hash,
        ROW_NUMBER() OVER (
            PARTITION BY game_type, level_number 
            ORDER BY survival_score DESC, times_extended DESC
        ) as rn
    FROM frontier_checkpoints
)
DELETE FROM frontier_checkpoints
WHERE (game_type, level_number, terminal_frame_hash) IN (
    SELECT game_type, level_number, terminal_frame_hash
    FROM ranked WHERE rn > 20
);
```

**Estimated max rows**: 20 checkpoints × 9 levels × 100 games = 18,000 rows max

### Checkpoint Invalidation

A checkpoint may become invalid if:
- Replay fails (game over during replay)
- Game mechanics changed (API update)
- Sequence was recorded incorrectly

**Handle gracefully**:
```python
def invalidate_checkpoint(self, game_type, level, terminal_hash):
    self.db.execute_query("""
        UPDATE frontier_checkpoints 
        SET survival_score = survival_score * 0.5,
            terminal_reason = 'invalidated'
        WHERE game_type = ? AND level_number = ? AND terminal_frame_hash = ?
    """, (game_type, level, terminal_hash))
```

---

## Metrics to Track

| Metric | Query | Good Value |
|--------|-------|------------|
| Checkpoint extension rate | `AVG(times_extended)` | > 2 (checkpoints being built upon) |
| Unique terminal states | `COUNT(DISTINCT terminal_frame_hash)` per level | 5-20 (diverse exploration) |
| Best survival score trend | `MAX(survival_score)` over time | Increasing |
| Checkpoint → Win conversion | Levels that went from checkpoint to winning_sequence | Goal |

---

## Implementation Order (Detailed)

### Phase 1: Schema & Basic Recording

1. **Schema creation**
   - File: `complete_database_schema.sql`
   - Add `frontier_checkpoints` table (schema in this doc)
   - Run migration: `python -c "from database_interface import DatabaseInterface; db = DatabaseInterface('core_data.db'); db.execute_query('''CREATE TABLE IF NOT EXISTS...''')"

2. **Recording method** 
   - File: `core_gameplay.py`
   - Add method: `_save_frontier_checkpoint(game_type, level, frame_hash, actions, metrics)`
   - Uses existing: `_compute_frame_hash()` (line 6452), `_recent_action_traces` (line 9154)
   - Insert call after death detection (~line 8170), inside the `if is_frontier:` block

### Phase 2: Checkpoint Retrieval & Replay

3. **Query method**
   - File: `core_gameplay.py`
   - Add method: `_get_best_frontier_checkpoint(game_type, level) -> Optional[Dict]`
   - Simple SQL query, return action_sequence as list

4. **Replay integration**
   - File: `core_gameplay.py`
   - Modify level start logic (~line 4200 in `_handle_level_transition`)
   - If frontier level: query checkpoint, if exists: call `_replay_sequence_inline()` (line 26816)
   - Create wrapper to format checkpoint as pseudo-sequence dict

### Phase 3: Guards & Maintenance

5. **Guard on save**
   - In `_save_frontier_checkpoint()`: check `_is_frontier_level()` first
   - If winning_sequence exists, return early (no save)

6. **Cleanup integration**
   - File: `safe_cleanup.py`
   - Add cleanup function: keep top 20 checkpoints per (game_type, level)
   - Run every 10 generations with other cleanup tasks

### Phase 4: Metrics & Monitoring

7. **Metrics**
   - File: `manual_tools/gameplay_analyzer.py`
   - Add checkpoint stats: extension rate, conversion rate
   - Query: `SELECT game_type, level_number, COUNT(*), AVG(survival_score), MAX(survival_score) FROM frontier_checkpoints GROUP BY game_type, level_number`

---

## Open Questions - Resolved

1. **Minimum actions threshold**: **3 actions** before saving checkpoint
   - Fewer than 3 = instant death, no useful info
   - 3+ shows the agent survived initial state

2. **Oscillation detection**: Use existing `unique_frames_this_level` from `GameLoopState`
   - Formula: `oscillation_count ≈ action_count - len(unique_frames_this_level)`
   - If oscillation_count > action_count/2, reject checkpoint (pure loop)

3. **Checkpoint selection**: Always use best (highest `survival_score`)
   - Keep it simple initially
   - Future enhancement: 10% chance to try alternative checkpoint for diversity

4. **Cross-agent checkpoints**: YES - checkpoints are network knowledge
   - Any agent on frontier level should benefit from any checkpoint
   - This is consistent with "viral package" philosophy from Master Ruleset

---

**END OF ARCHITECTURE DOCUMENT**
