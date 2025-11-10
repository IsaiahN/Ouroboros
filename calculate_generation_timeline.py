#!/usr/bin/env python3
"""Calculate optimal configuration for 8-hour evolution run"""

print("=" * 70)
print("8-HOUR EVOLUTION RUN CALCULATION")
print("=" * 70)
print()

total_minutes = 8 * 60
print(f"Total Time: {total_minutes} minutes (8 hours)")
print()

# Different mode options
modes = [
    ("Standard (60 min)", 60, 10),
    ("Fast (30 min)", 30, 5),
    ("Moderate (45 min)", 45, 10),
    ("Custom (40 min)", 40, 8)
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
print("RECOMMENDATION: Moderate 45-minute mode (10 generations)")
print("=" * 70)
print()
print("Why 45 minutes?")
print("  • 10 generations in 8 hours (solid sample size)")
print("  • 10 games per generation = 100 total games")
print("  • ~4.5 minutes per game (sufficient for level 3+ with 5000 action budget)")
print("  • Best balance of evaluation depth vs iteration speed")
print("  • Enough time for breakthrough systems to activate")
print()
print("With the new architecture:")
print("  ✓ No specialist protection blocking selection")
print("  ✓ Prestige provides earned protection (0-80%)")
print("  ✓ Operating modes guide mutation (pioneer/optimizer/generalist)")
print("  ✓ 5000 action budget allows level 3+ attempts")
print("  ✓ Anti-oscillation prevents wasted loops")
print()
print("Command:")
print("  python autonomous_evolution_runner.py --max-generations 10 --evolution-interval 45 --games-per-gen 10")
print()
print("OR use the wrapper:")
print("  python run_evolution.py --max-generations 10")
print()
print("=" * 70)