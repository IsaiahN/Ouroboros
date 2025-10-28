# Adaptive Action Limits System

## ✅ Implemented: Self-Adjusting Generation Lifespan

### What It Does:
The system automatically adjusts `max_actions_per_level` and `max_total_actions` for each generation based on performance data.

### Key Features:

1. **Rewards Success with More Time**
   - High performing generations (≥10% success) get +15% more actions
   - Allows successful strategies more exploration time

2. **Punishes Failure with Less Time**
   - Low performing generations (<2% success) get -15% fewer actions
   - Speeds up evolution cycles when not making progress

3. **Detects Trends**
   - Improving trend (20%+ better) → modest increase (+7.5%)
   - Declining trend (20%+ worse) → modest decrease (-7.5%)

4. **Efficiency Monitoring**
   - If using <30% of available actions, caps increases
   - Prevents waste of computation time

5. **Hard Constraints**
   - **Floor**: 200 actions/level minimum (as requested)
   - **Ceiling**: 400 actions/level maximum
   - **Total range**: 600-3000 actions per game

### How It Works:

```python
# At start of each generation's evaluation:
actions_per_level, total_actions = adaptive_limits.adjust_limits(current_generation)

# Then configure all games with these limits:
engine.configure(
    max_actions_per_level=actions_per_level,  # Adaptive
    max_actions_per_game=total_actions        # Adaptive
)
```

### Example Behavior:

| Generation | Success Rate | Trend | Actions/Level | Total Actions | Reasoning |
|------------|-------------|-------|---------------|---------------|-----------|
| 0 | 0.5% | New | 200 | 1000 | Default start |
| 1 | 0.3% | Declining | 200 | 850 | Low success, reduce |
| 2 | 2.0% | Improving! | 200 | 918 | Improvement trend, increase |
| 3 | 12.0% | High success | 230 | 1055 | Doing well, more time |
| 4 | 15.0% | Still high | 265 | 1213 | Keep increasing |

### Benefits:

✅ **Faster Evolution** - Bad strategies get less time
✅ **Better Exploration** - Good strategies get more time  
✅ **Autonomous** - No manual tuning needed
✅ **Data-Driven** - Based on actual performance
✅ **Safe** - Hard floor prevents too-short games

### Integration:

Already integrated into `autonomous_evolution_runner.py`:
- Imports `AdaptiveActionLimits`
- Creates instance: `self.adaptive_limits = AdaptiveActionLimits(self.db)`
- Adjusts before each generation: `adaptive_limits.adjust_limits(current_generation)`
- Logs all adjustments to database for tracking

### Monitoring:

Check adjustments in system_logs:
```sql
SELECT message, extra_data 
FROM system_logs 
WHERE logger_name = 'AdaptiveActionLimits' 
ORDER BY timestamp DESC;
```

The system is now fully autonomous and self-optimizing! 🎯
