# BugFix #8: Pattern Storage NOT NULL Constraint

## Issue
**Error**: `NOT NULL constraint failed: discovered_patterns.concrete_examples`

**Symptoms**:
- Evolution running but pattern learning failing
- Error log: "Error storing discovered pattern: NOT NULL constraint failed"
- Occurred during active evolution at 15:33:55 - 15:35:08 (5+ errors)
- Meta-learning system blocked from storing discovered patterns

## Root Cause
The `_store_discovered_pattern()` method at line 2227 was attempting to INSERT into `discovered_patterns` table but was **missing** the required `concrete_examples` column.

**Database Schema** (`ouroboros_database_extension.sql` line 334):
```sql
concrete_examples TEXT NOT NULL,  -- JSON: array of sequence_ids that match
```

**Broken INSERT** (line 2227-2236):
```python
INSERT INTO discovered_patterns (
    pattern_id, pattern_name, pattern_type, pattern_signature,
    occurrence_count, success_count, success_rate,
    confidence_score, discovered_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```

Missing columns:
- `concrete_examples` (NOT NULL)
- `avg_score_achieved` (NOT NULL)
- `avg_efficiency` (NOT NULL)

## Why It Happened
Two different code paths insert into `discovered_patterns`:

1. **Line 1599** (`_detect_and_store_abstract_pattern`): Stores patterns from winning sequences
   - ✅ Has `concrete_examples` with `json.dumps([sequence_id])`
   - ✅ Working correctly

2. **Line 2227** (`_store_discovered_pattern`): Stores meta-learned patterns from rule induction
   - ❌ Missing `concrete_examples` column
   - ❌ Missing `avg_score_achieved` and `avg_efficiency`
   - This is what caused the NULL constraint errors

Meta-patterns don't have concrete sequence examples (they're abstract rules), but the database schema requires the column to be NOT NULL.

## Solution
Added the missing columns to the INSERT statement with appropriate default values:

```python
INSERT INTO discovered_patterns (
    pattern_id, pattern_name, pattern_type, pattern_signature,
    concrete_examples, occurrence_count, success_count, success_rate,
    avg_score_achieved, avg_efficiency, confidence_score, discovered_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

# With values:
json.dumps([]),  # Empty examples for meta-patterns
0.0,             # avg_score_achieved (no concrete games yet)
0.0,             # avg_efficiency (no concrete games yet)
```

## Files Changed
- `core_gameplay.py` line 2227-2236: Added missing columns to INSERT

## Verification
Created `verify_pattern_fix.py` to test the fix:
- ✅ Pattern INSERT succeeds without NULL constraint error
- ✅ Empty JSON array `[]` stored correctly for meta-patterns
- ✅ Can be parsed as valid JSON
- ✅ No database errors

## Impact
**Before Fix**:
- Meta-learning system completely blocked
- Pattern induction rules couldn't be stored
- Evolution continued but pattern learning failed silently
- System could discover patterns but not persist them

**After Fix**:
- Meta-patterns stored successfully
- Pattern induction rules persisted to database
- Full pattern learning system operational
- Both sequence-based patterns (line 1599) and meta-learned patterns (line 2227) working

## Timeline
- **Error occurred**: 2025-10-31 15:33:55 - 15:35:08 (during active evolution)
- **Root cause identified**: Line 2227 missing columns
- **Fix applied**: Added concrete_examples, avg_score_achieved, avg_efficiency
- **Verified**: Test passed, no NULL constraint errors

## Related Systems
- **Sequence Learning** (line 1599): ✅ Still working (has concrete_examples)
- **Meta-Learning** (line 2227): ✅ NOW FIXED (has concrete_examples)
- **Pattern Application** (line 1619): ✅ Unaffected
- **Community Memory**: ✅ Unaffected (separate winning_sequences table)

## Testing Notes
The existing pattern (pat_0eaad2390d65140c) has 66 concrete sequence examples, proving the first code path works. The second code path for meta-learned patterns is now also working after this fix.

Evolution can now continue with full pattern learning capabilities!
