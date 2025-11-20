# Root Cause Investigation: Invalid Sequences with Score 0

## Problem
6 sequences were stored as "winning" sequences but score 0.0 when replayed.

## Investigation Query
```sql
SELECT 
    ws.sequence_id,
    ws.game_id,
    ws.total_score,
    ws.total_actions,
    ws.generation_discovered,
    ws.agent_id,
    ws.discovered_at
FROM winning_sequences ws
WHERE ws.sequence_id IN (
    'seq_f343df4343194b76',
    'seq_d18872e172724367',
    'seq_c0913da344d2458e',
    'seq_086ff9c55b164e8d',
    'seq_445b3c2ca1d54ba2',
    'seq_a0c92394bc7244ef'
)
```

## Findings
- All 6 sequences have `total_score = 1.0` in database
- All 6 sequences have very few actions (1-3 actions)
- When replayed, they score 0.0 (not 1.0)

## Hypothesis
These sequences were likely captured from **incomplete level completions** or **false positives** where:
1. The game state showed `score = 1.0` temporarily
2. The sequence was saved before the level was actually validated
3. OR: The game API changed and these sequences are now invalid

## Root Cause
**Likely**: Sequence capture logic doesn't validate that the sequence actually completes the level before saving.

## Recommendation
Add validation step in sequence capture:
1. Capture sequence
2. **Immediately replay it** to verify it works
3. Only save if replay succeeds
4. This prevents storing invalid sequences

## Status
- ✅ 3 sequences pruned (had >=3 validation attempts)
- ⏳ 3 sequences remain (need more validation attempts before pruning)
- 📝 Recommendation documented for future implementation
