#!/usr/bin/env python3
"""Calculate optimal configuration for 15-hour evolution run"""

print("=" * 70)
print("15-HOUR EVOLUTION RUN CALCULATION")
print("=" * 70)
print()

total_minutes = 15 * 60
print(f"Total Time: {total_minutes} minutes (15 hours)")
print()

# Historical data from Generation 156: 1 gen = ~4.5 hours with 10 games
# But this seems unusually slow - likely had API issues or delays
# Normal expected: 10 games with 3828 agents should be faster

# Different mode options with realistic estimates
modes = [
    ("Standard (60 min)", 60, 10),
    ("Moderate (45 min)", 45, 10),
    ("Fast (30 min)", 30, 8),
    ("Quick (20 min)", 20, 5)
]

print("MODE OPTIONS:")
print()

for name, interval, games in modes:
    gens = total_minutes // interval
    total_games = gens * games
    time_per_game = (interval * 60) // games
    
    print(f"{name}")
    print(f"  Evolution Interval: {interval} min")
    print(f"  Games per Generation: {games}")
    print(f"  Generations: {gens}")
    print(f"  Total Games: {total_games:,}")
    print(f"  Avg time per game: ~{time_per_game:.0f} seconds")
    print()

print("=" * 70)
print("RECOMMENDATION: Moderate 45-minute mode (20 generations)")
print("=" * 70)
print()
print("Why 45 minutes?")
print("  • 20 generations in 15 hours (excellent sample size)")
print("  • 10 games per generation = 200 total games")
print("  • ~4.5 minutes per game (sufficient for level 3+ with 6000 action budget)")
print("  • Best balance of evaluation depth vs iteration speed")
print("  • Enough time for breakthrough systems to activate")
print("  • Smart agent-to-task assignment maximizes efficiency")
print()
print("With the new enhancements:")
print("  ✓ Win-state driven agent assignment (pioneers/optimizers/generalists)")
print("  ✓ Pioneers → unbeaten games (frontier discovery)")
print("  ✓ Optimizers → games with beaten levels (reduce action counts)")
print("  ✓ Automatic sequence selection per level")
print("  ✓ 2000 actions/level, 6000 total (adaptive)")
print("  ✓ Anti-oscillation + API RESET escape mechanisms")
print("  ✓ Prestige-based survival (0-80% earned protection)")
print()
print("Command:")
print("  python run_evolution.py --max-generations 20")
print()
print("Alternative (if you want faster iterations):")
print("  python run_evolution.py --max-generations 30 --evolution-interval 30 --games-per-gen 8")
print()
print("Alternative (if you want deeper evaluation):")
print("  python run_evolution.py --max-generations 15 --evolution-interval 60 --games-per-gen 15")
print()
print("=" * 70)