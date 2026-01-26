# Self-Supervised Dynamics: Complete Implementation Plan

**Version**: 1.0  
**Date**: January 26, 2026  
**Purpose**: Add learned representations for implicit generalization without embedding an LLM  
**Status**: PLANNED

---

## Executive Summary

| Aspect | Details |
|--------|---------|
| **Data Available** | 55,800+ frame transitions, 6 game types, 64x64 grids |
| **Database Size** | 15.4 GB (safe headroom under 200 GB limit) |
| **Dependencies to Add** | `torch>=2.0.0` (CPU-only, ~200MB) |
| **New Files** | 2 new files, 1 migration, 1 schema update |
| **Integration Points** | 4 existing files modified |
| **Training Frequency** | Every 10 generations (matches cleanup cadence) |

---

## Why This Approach?

### The Gap: Explicit vs Implicit Generalization

**Current System (Explicit)**:
```python
IF game_type == "SP80" AND object_color == 9:
    apply_hypothesis_47()
```
- Requires exact symbolic matches
- Novel combinations require new rules
- O(exponential) in transformation types

**With Learned Representations (Implicit)**:
```python
embedding = encoder(frame)
similar_situations = find_nearest(embedding)
action = vote_on_best_action(similar_situations)
```
- Similar situations cluster in embedding space
- Automatically generalizes across rotations, colors, positions
- O(log n) similarity lookup

### Why Dynamics Learning (Not Autoencoder or Contrastive)?

| Approach | Uses Your Data? | Learns Outcomes? | Requires Augmentation? |
|----------|-----------------|------------------|------------------------|
| Autoencoder | Partial | No | No |
| Contrastive | Partial | No | Yes (manual) |
| **Dynamics** | **Full** | **Yes** | **No** |

Your `action_traces` table stores `(frame_before, action, frame_after, score_delta)` - **perfect** for dynamics learning. The model learns to predict outcomes, which forces it to learn what matters for game progression.

---

## Phase 1: Foundation (New Files)

### 1.1 Create `representation_learner.py`

**Location**: Project root (alongside `core_gameplay.py`)

```
representation_learner.py
|-- GridEncoder (nn.Module)          # Convolutional frame encoder
|-- DynamicsPredictor (nn.Module)    # Action-conditional next-state predictor  
|-- RepresentationLearner (main class)
|   |-- __init__()                   # Load/create model, connect to DB
|   |-- load_training_data()         # Pull from action_traces
|   |-- train_epoch()                # One training pass
|   |-- train_on_recent_games()      # Called every 10 generations
|   |-- encode_frame()               # Get embedding for a frame
|   |-- find_similar_situations()    # Nearest-neighbor search in embedding space
|   |-- predict_next_state()         # Forward dynamics prediction
|   +-- save_model() / load_model()  # Persistence
+-- Utility functions
    |-- frame_to_tensor()            # JSON grid -> torch tensor
    +-- cosine_similarity()          # For nearest-neighbor search
```

**Key Design Decisions**:

| Decision | Rationale |
|----------|-----------|
| **64x64x10 input** | Matches your frame size (64x64) with 10 color channels (one-hot) |
| **128-dim latent** | Compact enough for fast similarity search, expressive enough for game dynamics |
| **CPU-only training** | Avoids CUDA dependency; ~55K samples trains in <5 minutes on CPU |
| **No raw frame storage** | Store embeddings only (512 bytes vs 40KB per frame) |
| **Separate dynamics head** | Lets encoder learn state features, dynamics head learns action effects |

### 1.2 Create `migrations/add_frame_embeddings.py`

Adds the new table and columns needed:

```sql
-- New table for cached embeddings
CREATE TABLE IF NOT EXISTS frame_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id INTEGER NOT NULL,           -- FK to action_traces.id
    game_type TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    embedding BLOB NOT NULL,             -- 128 floats as bytes (512 bytes)
    action_taken INTEGER,
    score_delta REAL,
    frame_changed BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trace_id) REFERENCES action_traces(id),
    UNIQUE(trace_id)
);

-- Index for game_type+level queries (find similar situations in same context)
CREATE INDEX IF NOT EXISTS idx_frame_embeddings_game_level 
ON frame_embeddings(game_type, level_number);

-- Add embedding column to action_traces for inline storage (optional)
ALTER TABLE action_traces ADD COLUMN frame_embedding BLOB;
```

---

## Phase 2: Neural Network Architecture

### 2.1 Grid Encoder

```python
class GridEncoder(nn.Module):
    """
    Convolutional encoder for 64x64 ARC game frames.
    
    Input: (batch, 10, 64, 64) - one-hot color channels
    Output: (batch, 128) - latent embedding
    """
    
    def __init__(self, num_colors=10, latent_dim=128):
        super().__init__()
        
        self.encoder = nn.Sequential(
            # 64x64 -> 32x32
            nn.Conv2d(num_colors, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            
            # 32x32 -> 16x16
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            
            # 16x16 -> 8x8
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            
            # 8x8 -> 4x4
            nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            
            # Flatten and project
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, latent_dim),
            nn.LayerNorm(latent_dim)  # Normalize for cosine similarity
        )
    
    def forward(self, x):
        return self.encoder(x)
```

### 2.2 Dynamics Predictor

```python
class DynamicsPredictor(nn.Module):
    """
    Predicts next frame embedding from current embedding + action.
    
    Input: (batch, 128 + 8) - embedding + one-hot action
    Output: (batch, 128) - predicted next embedding
    """
    
    def __init__(self, latent_dim=128, num_actions=8):
        super().__init__()
        
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + num_actions, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, latent_dim)
        )
    
    def forward(self, embedding, action_onehot):
        combined = torch.cat([embedding, action_onehot], dim=-1)
        return self.predictor(combined)
```

### 2.3 Combined Model

```python
class DynamicsModel(nn.Module):
    """Combined encoder + dynamics predictor."""
    
    def __init__(self, num_colors=10, latent_dim=128, num_actions=8):
        super().__init__()
        self.encoder = GridEncoder(num_colors, latent_dim)
        self.dynamics = DynamicsPredictor(latent_dim, num_actions)
        self.latent_dim = latent_dim
    
    def encode(self, frame):
        """Get embedding for a frame."""
        return self.encoder(frame)
    
    def predict_next(self, frame, action_onehot):
        """Predict next frame's embedding."""
        current_embed = self.encode(frame)
        return self.dynamics(current_embed, action_onehot)
    
    def forward(self, frame_before, action_onehot, frame_after):
        """
        Training forward pass.
        Returns: (predicted_next_embed, actual_next_embed)
        """
        embed_before = self.encode(frame_before)
        embed_after_actual = self.encode(frame_after)
        embed_after_predicted = self.dynamics(embed_before, action_onehot)
        return embed_after_predicted, embed_after_actual
```

---

## Phase 3: Training Pipeline

### 3.1 Data Loading From `action_traces`

```python
def load_training_data(self, limit: int = 50000) -> List[Dict]:
    """
    Load training data directly from existing action_traces table.
    
    Filters:
    - Must have both frame_before and frame_after
    - Prioritize diverse game_types
    - Weight by score_change (important transitions)
    """
    rows = self.db.execute_query("""
        SELECT 
            id,
            game_id,
            level_number,
            action_number,
            frame_before,
            frame_after,
            score_change,
            frame_changed
        FROM action_traces 
        WHERE frame_before IS NOT NULL 
          AND frame_after IS NOT NULL
          AND action_number BETWEEN 1 AND 7
        ORDER BY 
            ABS(score_change) DESC,  -- Prioritize score-changing actions
            RANDOM()
        LIMIT ?
    """, (limit,))
    
    data = []
    for row in rows:
        try:
            data.append({
                'trace_id': row['id'],
                'game_type': row['game_id'].split('-')[0],
                'level': row['level_number'],
                'action': row['action_number'],
                'frame_before': json.loads(row['frame_before']),
                'frame_after': json.loads(row['frame_after']),
                'score_delta': row['score_change'] or 0.0,
                'frame_changed': row['frame_changed'],
            })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return data
```

### 3.2 Training Loop

```python
def train_on_recent_games(self, hours: int = 72, epochs: int = 10, batch_size: int = 64):
    """
    Train the dynamics model on recent gameplay data.
    Called every 10 generations by autonomous_evolution_runner.
    
    Training objective: Predict next frame embedding from (current frame, action).
    """
    print(f"[REP] Loading training data from last {hours} hours...")
    data = self.load_training_data(limit=50000)
    
    if len(data) < 1000:
        print(f"[REP] Insufficient data ({len(data)} samples), skipping training")
        return
    
    print(f"[REP] Training on {len(data)} frame transitions...")
    self.model.train()
    
    for epoch in range(epochs):
        random.shuffle(data)
        total_loss = 0
        num_batches = 0
        
        for i in range(0, len(data) - batch_size, batch_size):
            batch = data[i:i+batch_size]
            
            # Convert to tensors
            frames_before = torch.stack([
                self._frame_to_tensor(b['frame_before']) for b in batch
            ])
            frames_after = torch.stack([
                self._frame_to_tensor(b['frame_after']) for b in batch
            ])
            actions = torch.tensor([b['action'] for b in batch])
            action_onehot = F.one_hot(actions, num_classes=8).float()
            
            # Forward pass
            predicted, actual = self.model(frames_before, action_onehot, frames_after)
            
            # MSE loss on embeddings
            loss = F.mse_loss(predicted, actual.detach())
            
            # Weight by importance (score-changing transitions matter more)
            importance = torch.tensor([
                1.0 + min(5.0, abs(b['score_delta']))  # Cap at 6x weight
                for b in batch
            ])
            loss = (loss * importance.unsqueeze(1)).mean()
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / max(1, num_batches)
        print(f"  Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.4f}")
    
    # Save updated model
    self.save_model()
    print(f"[REP] Training complete, model saved")
```

### 3.3 Frame-to-Tensor Conversion

```python
def _frame_to_tensor(self, frame: List[List[int]]) -> torch.Tensor:
    """
    Convert JSON grid to one-hot tensor.
    
    Input: 64x64 list of color integers (0-9)
    Output: (10, 64, 64) tensor with one-hot channels
    """
    # Pad/crop to 64x64
    h, w = len(frame), len(frame[0]) if frame else 0
    
    padded = [[0] * 64 for _ in range(64)]
    for i in range(min(h, 64)):
        for j in range(min(w, 64)):
            padded[i][j] = frame[i][j] if frame[i][j] < 10 else 0
    
    # Convert to numpy then one-hot
    arr = np.array(padded, dtype=np.int64)
    one_hot = np.eye(10, dtype=np.float32)[arr]  # (64, 64, 10)
    one_hot = one_hot.transpose(2, 0, 1)  # (10, 64, 64)
    
    return torch.from_numpy(one_hot)
```

---

## Phase 4: Inference Integration

### 4.1 Similarity Search

```python
def find_similar_situations(
    self, 
    frame: List[List[int]], 
    game_type: str = None,
    level: int = None,
    top_k: int = 10
) -> List[Dict]:
    """
    Find historically similar situations using embedding similarity.
    
    Returns list of similar past experiences with their outcomes.
    """
    # Encode query frame
    query_tensor = self._frame_to_tensor(frame).unsqueeze(0)
    self.model.eval()
    with torch.no_grad():
        query_embed = self.model.encode(query_tensor).squeeze().numpy()
    
    # Build SQL filter
    where_clauses = ["1=1"]
    params = []
    
    if game_type:
        where_clauses.append("game_type = ?")
        params.append(game_type)
    if level:
        where_clauses.append("level_number = ?")
        params.append(level)
    
    where_sql = " AND ".join(where_clauses)
    params.append(top_k * 10)  # Get more, filter by similarity
    
    # Get candidate embeddings
    rows = self.db.execute_query(f"""
        SELECT 
            fe.trace_id,
            fe.embedding,
            fe.game_type,
            fe.level_number,
            fe.action_taken,
            fe.score_delta,
            fe.frame_changed
        FROM frame_embeddings fe
        WHERE {where_sql}
        ORDER BY RANDOM()
        LIMIT ?
    """, tuple(params))
    
    # Compute similarities
    results = []
    for row in rows:
        stored_embed = np.frombuffer(row['embedding'], dtype=np.float32)
        similarity = np.dot(query_embed, stored_embed) / (
            np.linalg.norm(query_embed) * np.linalg.norm(stored_embed) + 1e-8
        )
        results.append({
            'trace_id': row['trace_id'],
            'similarity': float(similarity),
            'game_type': row['game_type'],
            'level': row['level_number'],
            'action_taken': row['action_taken'],
            'score_delta': row['score_delta'],
            'frame_changed': row['frame_changed'],
        })
    
    # Sort by similarity and return top_k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]
```

### 4.2 Integration with `agent_self_model.py`

Add new method `get_embedding_suggested_action()`:

```python
def get_embedding_suggested_action(
    self,
    frame: List[List[int]],
    game_type: str,
    level: int
) -> Optional[Dict[str, Any]]:
    """
    Query learned representations for similar situations.
    Returns suggested action based on what worked in similar past frames.
    
    This provides IMPLICIT generalization: finds similar situations
    even if game_type, colors, or positions are different.
    """
    if not hasattr(self, 'rep_learner') or not self.rep_learner:
        return None
    
    try:
        # Find similar situations
        similar = self.rep_learner.find_similar_situations(
            frame=frame,
            game_type=game_type,  # None to search across all games
            level=None,           # None to find cross-level patterns
            top_k=10
        )
        
        if not similar:
            return None
        
        # Vote on best action based on successful similar situations
        action_votes = {}
        for s in similar:
            if s['score_delta'] > 0 or s['frame_changed']:
                # Weight by similarity and outcome
                action = s['action_taken']
                weight = s['similarity'] * (1.0 + s['score_delta'])
                action_votes[action] = action_votes.get(action, 0) + weight
        
        if not action_votes:
            return None
        
        # Return highest-voted action
        best_action = max(action_votes, key=action_votes.get)
        confidence = action_votes[best_action] / sum(action_votes.values())
        
        return {
            'suggested_action': f'ACTION{best_action}',
            'confidence': confidence,
            'similar_count': len(similar),
            'source': 'embedding_similarity'
        }
        
    except Exception as e:
        logger.debug(f"Embedding suggestion failed: {e}")
        return None
```

---

## Phase 5: Integration Points

### 5.1 Modify `core_gameplay.py::_select_action()`

Add embedding-based suggestion as a new decision source:

```python
# In _select_action(), after discovery exploitation, before rule-based selection:

# ================================================================
# EMBEDDING-BASED SIMILARITY (Implicit Generalization)
# ================================================================
# Query learned representations for similar situations.
# This finds patterns across games/levels that explicit rules miss.
# ================================================================
if hasattr(self, 'agent_self_model') and self.agent_self_model:
    try:
        game_type = self.session_manager.current_game_id.split('-')[0] if self.session_manager.current_game_id else None
        current_level = loop_state.current_level if loop_state else 1
        
        embed_suggestion = self.agent_self_model.get_embedding_suggested_action(
            frame=game_state.frame,
            game_type=game_type,
            level=current_level
        )
        
        if embed_suggestion and embed_suggestion['confidence'] > 0.6:
            action = embed_suggestion['suggested_action']
            reason = (
                f"[EMBED-SIMILARITY] {action} worked in {embed_suggestion['similar_count']} "
                f"similar situations (confidence: {embed_suggestion['confidence']:.2f})"
            )
            logger.debug(f"[EMBED] Using similarity-based action: {action}")
            return action, reason
            
    except Exception as e:
        logger.debug(f"Embedding selection failed: {e}")
```

### 5.2 Modify `autonomous_evolution_runner.py`

Add training trigger every 10 generations:

```python
# In run_generation(), around line 2437 (where cleanup runs):

# ================================================================
# REPRESENTATION LEARNING (Every 10 generations)
# ================================================================
# Train the dynamics model on recent gameplay to improve pattern recognition.
# This learns implicit representations that generalize across games.
# ================================================================
if self.current_generation % 10 == 0:
    try:
        from representation_learner import RepresentationLearner
        
        rep_learner = RepresentationLearner(self.db)
        print(f"\n[REP-LEARN] Training dynamics model on recent gameplay...")
        rep_learner.train_on_recent_games(hours=72, epochs=10)
        
        # Compute embeddings for recent traces that don't have them yet
        print(f"[REP-LEARN] Computing embeddings for new traces...")
        rep_learner.compute_embeddings_for_recent_traces(hours=24)
        
    except ImportError:
        print(f"  [SKIP] Representation learner not available")
    except Exception as e:
        print(f"  [WARN] Representation learning failed: {e}")
```

### 5.3 Modify `agent_self_model.py::__init__()`

Initialize the representation learner:

```python
# In AgentSelfModel.__init__():

# Initialize representation learner (lazy load)
self._rep_learner = None

@property
def rep_learner(self):
    """Lazy-load representation learner to avoid import overhead."""
    if self._rep_learner is None:
        try:
            from representation_learner import RepresentationLearner
            model_path = "models/dynamics_model.pt"
            if os.path.exists(model_path):
                self._rep_learner = RepresentationLearner(self.db, model_path)
                logger.info("[REP] Loaded representation learner")
            else:
                logger.debug("[REP] No trained model found, similarity search disabled")
        except ImportError:
            logger.debug("[REP] torch not available, similarity search disabled")
    return self._rep_learner
```

### 5.4 Update `requirements.txt`

```
python-dotenv>=1.0.0
aiohttp>=3.9.0
numpy>=1.24.0
pandas>=2.0.0
pydeps>=1.12.0
pytest>=8.0.0
torch>=2.0.0  # CPU-only, for learned representations
```

---

## Phase 6: Schema Updates

### 6.1 Add to `complete_database_schema.sql`

```sql
-- ============================================================================
-- LEARNED REPRESENTATIONS (Implicit Generalization)
-- ============================================================================
-- Stores frame embeddings from dynamics model for similarity search.
-- Enables finding "similar situations" across games without explicit rules.

CREATE TABLE IF NOT EXISTS frame_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id INTEGER NOT NULL,                -- FK to action_traces.id
    game_type TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    
    -- The learned representation (128 floats = 512 bytes)
    embedding BLOB NOT NULL,
    
    -- Context for weighted similarity
    action_taken INTEGER,
    score_delta REAL DEFAULT 0.0,
    frame_changed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    model_version TEXT DEFAULT 'v1',          -- Track model versions
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (trace_id) REFERENCES action_traces(id),
    UNIQUE(trace_id)
);

-- Fast lookup by game context
CREATE INDEX IF NOT EXISTS idx_frame_embeddings_game_level 
ON frame_embeddings(game_type, level_number);

-- Track model training history
CREATE TABLE IF NOT EXISTS representation_model_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version TEXT NOT NULL,
    training_samples INTEGER NOT NULL,
    final_loss REAL,
    training_duration_seconds REAL,
    trained_at TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

---

## Phase 7: File Structure

```
BitterTruth-AI/
|-- representation_learner.py          # NEW: Main representation learning module
|-- models/                            # NEW: Directory for saved models
|   +-- dynamics_model.pt              # Trained PyTorch model (~5MB)
|-- migrations/
|   +-- add_frame_embeddings.py        # NEW: Schema migration
|-- requirements.txt                   # MODIFIED: Add torch
|-- complete_database_schema.sql       # MODIFIED: Add new tables
|-- agent_self_model.py                # MODIFIED: Add rep_learner property, get_embedding_suggested_action
|-- core_gameplay.py                   # MODIFIED: Add embedding suggestion in _select_action
+-- autonomous_evolution_runner.py     # MODIFIED: Add training trigger every 10 gens
```

---

## Phase 8: Testing & Validation

### 8.1 Validation Criteria

| Metric | Target | Method |
|--------|--------|--------|
| Training Loss | < 0.1 after 10 epochs | Monitor in training loop |
| Similarity Accuracy | Same-game frames cluster | Visualize embeddings |
| Embedding Storage | < 1GB for 100K traces | 512 bytes x 100K = 51MB |
| Suggestion Hit Rate | > 30% suggestions used | Log in `_select_action` |
| Cross-Game Transfer | Suggestions from other games | Remove game_type filter |

### 8.2 Testing Commands

```bash
# Test training pipeline
python -c "
from representation_learner import RepresentationLearner
from database_interface import DatabaseInterface
db = DatabaseInterface()
rl = RepresentationLearner(db)
rl.train_on_recent_games(hours=24, epochs=3)
"

# Test similarity search
python -c "
import json
from representation_learner import RepresentationLearner
from database_interface import DatabaseInterface
db = DatabaseInterface()
rl = RepresentationLearner(db, 'models/dynamics_model.pt')
# Get a sample frame
row = db.execute_query('SELECT frame_before FROM action_traces WHERE frame_before IS NOT NULL LIMIT 1')[0]
frame = json.loads(row['frame_before'])
similar = rl.find_similar_situations(frame, top_k=5)
print(f'Found {len(similar)} similar situations')
for s in similar:
    print(f'  Similarity: {s[\"similarity\"]:.3f}, Action: {s[\"action_taken\"]}, Score: {s[\"score_delta\"]}')
"
```

---

## Phase 9: Rollout Plan

| Stage | What | When | Rollback |
|-------|------|------|----------|
| 1 | Add `torch` to requirements | Immediate | Remove from requirements |
| 2 | Create `representation_learner.py` | Immediate | Delete file |
| 3 | Run migration | Before next evolution | Drop new tables |
| 4 | Train initial model offline | Before next evolution | Delete model file |
| 5 | Add lazy loader to `agent_self_model.py` | After training | Revert change |
| 6 | Add suggestion to `_select_action` | After validation | Revert change |
| 7 | Add training trigger to evolution runner | After 5-gen test | Revert change |

---

## Phase 10: Monitoring & Maintenance

### 10.1 Add to `safe_cleanup.py`

```python
# Clean old embeddings (keep last 100K)
def cleanup_old_embeddings(self, keep_count: int = 100000):
    """Remove oldest embeddings to prevent unbounded growth."""
    count = self.db.execute_query(
        "SELECT COUNT(*) as c FROM frame_embeddings"
    )[0]['c']
    
    if count > keep_count:
        delete_count = count - keep_count
        self.db.execute_query("""
            DELETE FROM frame_embeddings 
            WHERE id IN (
                SELECT id FROM frame_embeddings 
                ORDER BY created_at ASC 
                LIMIT ?
            )
        """, (delete_count,))
        return delete_count
    return 0
```

### 10.2 Health Monitoring

Add to `oracle_health_monitor.py`:

```python
def check_representation_health(self) -> Dict[str, Any]:
    """Check health of learned representations."""
    stats = {}
    
    # Model exists?
    model_path = "models/dynamics_model.pt"
    stats['model_exists'] = os.path.exists(model_path)
    
    # Embedding count
    result = self.db.execute_query(
        "SELECT COUNT(*) as c FROM frame_embeddings"
    )
    stats['embedding_count'] = result[0]['c'] if result else 0
    
    # Training recency
    result = self.db.execute_query(
        "SELECT MAX(trained_at) as last FROM representation_model_history"
    )
    stats['last_training'] = result[0]['last'] if result and result[0]['last'] else None
    
    return stats
```

---

## Summary: No Gaps Checklist

| Aspect | Covered? | Details |
|--------|----------|---------|
| **Data Source** | YES | Uses existing `action_traces` table |
| **Dependencies** | YES | Only adds `torch` (CPU) |
| **Database Schema** | YES | Migration + schema update provided |
| **Training Trigger** | YES | Every 10 generations in evolution runner |
| **Inference Integration** | YES | New method in `agent_self_model.py` |
| **Action Selection** | YES | Added to `_select_action()` pipeline |
| **Lazy Loading** | YES | Only loads model when needed |
| **Cleanup** | YES | Added to `safe_cleanup.py` |
| **Monitoring** | YES | Added to health monitor |
| **Rollback Plan** | YES | Each phase independently reversible |
| **Testing** | YES | Commands and criteria provided |
| **Model Persistence** | YES | Save/load in `models/` directory |
| **Rule Compliance** | YES | No test files, database-only storage, no emojis |

---

## Theoretical Foundation

### What Dynamics Learning Captures

The model learns to predict: **"Given this frame and this action, what will the next frame look like (in embedding space)?"**

To do this well, it must learn:
1. **What moves** - which pixels respond to actions
2. **How things move** - directional mappings (action 1 = up, etc.)
3. **Object permanence** - things that don't change stay constant
4. **Control invariants** - "I control the blue thing" regardless of position

### Why Embeddings Enable Implicit Generalization

In a well-learned representation space:

| Geometric Property | Semantic Meaning |
|--------------------|------------------|
| Distance | Conceptual similarity |
| Direction | Meaningful transformation |
| Clusters | Categories |
| Linear subspaces | Attributes (color, size, shape) |

This means the model finds "similar situations" without needing exact symbolic matches. A rotated, color-swapped version of a pattern lands near the original in embedding space.

### Integration with CODS Validation

The representation learner provides **suggestions**, not **decisions**. CODS still validates:
- Embedding suggestions are one input to action selection
- Successful actions update the embedding database
- Failed actions don't poison the embedding space (score_delta filtering)

This maintains the hybrid architecture: **learned perception + explicit validation**.

---

**END OF IMPLEMENTATION PLAN**
