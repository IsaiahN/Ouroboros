#!/usr/bin/env python3
"""
Evolution Runner - Clean SDK-based implementation
=================================================

Simple, direct implementation using the arc_agi SDK.
Replaces the bloated autonomous_evolution_runner.py.

Usage:
    python evolution_runner.py --mode=offline --test --game=ls20
    python evolution_runner.py --mode=online --max-generations=10
"""

import os
import sys

# Rule 1: No pycache
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import argparse
import asyncio
import random
import signal
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# SDK imports
from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState

# Local imports
from database_interface import DatabaseInterface
from decision_rung_system import DecisionRungSystem


@dataclass
class AgentState:
    """Minimal agent state for evolution."""
    agent_id: str
    generation: int = 0
    total_score: float = 0.0
    games_played: int = 0
    wins: int = 0

    @property
    def avg_score(self) -> float:
        return self.total_score / max(1, self.games_played)

    @property
    def win_rate(self) -> float:
        return self.wins / max(1, self.games_played)


@dataclass
class GameResult:
    """Result of a single game."""
    game_id: str
    agent_id: str
    score: float
    levels_completed: int
    total_levels: int
    is_win: bool
    actions_taken: int
    action_sequence: List[str] = field(default_factory=list)


class EvolutionRunner:
    """
    Clean evolution runner using arc_agi SDK directly.

    Core loop:
    1. Create agents
    2. Each agent plays games
    3. Record results
    4. Evolve (select best, mutate, create offspring)
    5. Repeat
    """

    def __init__(
        self,
        mode: str = "normal",
        db_path: str = "core_data.db",
        population_size: int = 10,
        games_per_generation: int = 5,
        max_generations: int = 10,
        max_actions_per_game: int = 500,
        target_game: Optional[str] = None,
        verbose: bool = False,
    ):
        self.mode = mode
        self.verbose = verbose
        self.db = DatabaseInterface(db_path)
        self.population_size = population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.max_actions = max_actions_per_game
        self.target_game = target_game

        # SDK setup
        op_mode = {
            'offline': OperationMode.OFFLINE,
            'online': OperationMode.ONLINE,
            'normal': OperationMode.NORMAL,
        }.get(mode.lower(), OperationMode.NORMAL)

        self.arcade = Arcade(operation_mode=op_mode)

        # Decision system
        self.decision_system = DecisionRungSystem(strategy='ladder')

        # State
        self.agents: List[AgentState] = []
        self.current_generation = 0
        self.running = True

        # Signal handling
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        print("\n[STOP] Shutdown requested...")
        self.running = False

    def _create_agent_id(self) -> str:
        """Generate unique agent ID."""
        import uuid
        return f"agent_{uuid.uuid4().hex[:12]}"

    def initialize_population(self) -> List[AgentState]:
        """Create initial agent population."""
        print(f"\n[INIT] Creating {self.population_size} agents...")

        agents = []
        for i in range(self.population_size):
            agent = AgentState(
                agent_id=self._create_agent_id(),
                generation=0,
            )
            agents.append(agent)

            # Default genome
            genome = '{"exploration_rate": 0.3, "learning_rate": 0.1}'

            # Store in database
            self.db.execute_query("""
                INSERT OR REPLACE INTO agents (
                    agent_id, generation, agent_type, genome, specialization,
                    created_at, is_active
                ) VALUES (?, ?, 'evolved', ?, 'generalist', datetime('now'), TRUE)
            """, (agent.agent_id, 0, genome))

        print(f"[OK] Created {len(agents)} agents")
        return agents

    def get_available_games(self) -> List[str]:
        """Get list of available game IDs."""
        try:
            envs = self.arcade.get_environments()
            game_ids = [e.game_id for e in envs]

            # Filter to target game if specified
            if self.target_game:
                game_ids = [g for g in game_ids if g.startswith(self.target_game)]

            return game_ids
        except Exception as e:
            print(f"[ERROR] Failed to get games: {e}")
            return []

    def play_game(self, agent: AgentState, game_id: str) -> GameResult:
        """
        Play a single game with an agent.

        Uses the decision system to select actions.
        """
        env = None
        try:
            env = self.arcade.make(game_id)
        except Exception as e:
            print(f"  [ERROR] Failed to create env for {game_id}: {e}")
            return GameResult(
                game_id=game_id,
                agent_id=agent.agent_id,
                score=0.0,
                levels_completed=0,
                total_levels=1,
                is_win=False,
                actions_taken=0,
            )

        if env is None:
            print(f"  [ERROR] env is None for {game_id}")
            return GameResult(
                game_id=game_id,
                agent_id=agent.agent_id,
                score=0.0,
                levels_completed=0,
                total_levels=1,
                is_win=False,
                actions_taken=0,
            )

        actions_taken = 0
        action_sequence = []
        last_obs = None
        prev_levels = 0

        # Get initial observation and available actions
        initial_obs = env.observation_space
        available_actions = getattr(initial_obs, 'available_actions', [1, 2, 3, 4])
        win_levels = getattr(initial_obs, 'win_levels', 7)

        if self.verbose:
            print(f"    Game: {game_id} | Available actions: {available_actions} | Win at: {win_levels} levels")

        # Game loop
        while actions_taken < self.max_actions:
            if not self.running:
                break

            # Get current observation from last step (or initial)
            obs = last_obs if last_obs else initial_obs

            # Build context for decision system with available_actions
            context = {
                'game_id': game_id,
                'agent_id': agent.agent_id,
                'actions_taken': actions_taken,
                'state': str(obs.state) if obs else 'UNKNOWN',
                'frame_data': obs,
                'available_actions': available_actions,
                'levels_completed': getattr(obs, 'levels_completed', 0),
                'win_levels': win_levels,
            }

            # Get action from decision system
            try:
                result = self.decision_system.decide(context, {})
                action_num = result.action if result else random.choice(available_actions)
                # Validate action is in available set
                if action_num not in available_actions:
                    action_num = random.choice(available_actions)
                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)
            except Exception:
                # Fallback to random from available actions only
                action_num = random.choice(available_actions)
                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)

            # Take action
            try:
                obs = env.step(action)
                actions_taken += 1
                action_sequence.append(action.name)
                last_obs = obs

                # Track level progress
                current_levels = getattr(obs, 'levels_completed', 0) or 0
                level_up = current_levels > prev_levels
                prev_levels = current_levels

                # Verbose output
                if self.verbose:
                    levels = current_levels
                    state_str = str(obs.state).replace('GameState.', '') if obs else '?'
                    level_indicator = ' [LEVEL UP!]' if level_up else ''
                    print(f"    [{actions_taken:3d}] {action.name:8s} -> levels={levels}/{win_levels} state={state_str}{level_indicator}")

                # Check for game end
                if obs and obs.state == GameState.WIN:
                    if self.verbose:
                        print(f"    [WIN!] Game won after {actions_taken} actions!")
                    break
                if obs and obs.state == GameState.GAME_OVER:
                    if self.verbose:
                        print(f"    [GAME OVER] after {actions_taken} actions")
                    break

            except Exception as e:
                print(f"  [ERROR] Step failed: {e}")
                break

        # Extract results - use levels_completed as the score metric
        levels_completed = 0
        total_levels = win_levels
        is_win = False

        if last_obs:
            levels_completed = getattr(last_obs, 'levels_completed', 0) or 0
            is_win = last_obs.state == GameState.WIN

        # Score is based on level progress (0.0 to 1.0)
        score = levels_completed / total_levels if total_levels > 0 else 0.0

        return GameResult(
            game_id=game_id,
            agent_id=agent.agent_id,
            score=score,
            levels_completed=levels_completed,
            total_levels=total_levels,
            is_win=is_win,
            actions_taken=actions_taken,
            action_sequence=action_sequence,
        )

    def run_generation(self) -> Dict[str, Any]:
        """Run one generation of evolution."""
        print(f"\n{'='*60}")
        print(f"GENERATION {self.current_generation}")
        print(f"{'='*60}")

        games = self.get_available_games()
        if not games:
            print("[ERROR] No games available!")
            return {'games_played': 0, 'wins': 0}

        print(f"[GAMES] {len(games)} available: {games}")

        results = []
        total_wins = 0
        total_score = 0.0

        # Each agent plays games
        for agent in self.agents:
            if not self.running:
                break

            # Select games for this agent
            agent_games = random.sample(games, min(self.games_per_generation, len(games)))

            print(f"\n[AGENT] {agent.agent_id[:12]}... playing {len(agent_games)} games")

            for game_id in agent_games:
                if not self.running:
                    break

                result = self.play_game(agent, game_id)
                results.append(result)

                # Update agent state
                agent.games_played += 1
                agent.total_score += result.score
                if result.is_win:
                    agent.wins += 1
                    total_wins += 1

                total_score += result.score

                # Log result
                status = "[WIN]" if result.is_win else f"[{result.levels_completed}/{result.total_levels}]"
                print(f"  {game_id}: {status} score={result.score:.1f} actions={result.actions_taken}")

                # Store in database
                self._store_game_result(result)

        games_played = len(results)
        avg_score = total_score / max(1, games_played)
        win_rate = total_wins / max(1, games_played)

        print(f"\n[SUMMARY] Gen {self.current_generation}: {games_played} games, {total_wins} wins ({win_rate*100:.1f}%), avg score: {avg_score:.2f}")

        return {
            'games_played': games_played,
            'wins': total_wins,
            'win_rate': win_rate,
            'avg_score': avg_score,
        }

    def _store_game_result(self, result: GameResult):
        """Store game result in database."""
        import uuid
        session_id = str(uuid.uuid4())

        try:
            # Create training session first (FK requirement)
            self.db.execute_query("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status, total_actions
                ) VALUES (?, ?, datetime('now'), 'evolution', 'completed', ?)
            """, (session_id, result.game_id, result.actions_taken))

            # Now store game result
            self.db.execute_query("""
                INSERT INTO game_results (
                    game_id, session_id, start_time, end_time, status,
                    final_score, total_actions, win_detected,
                    level_completions, generation
                ) VALUES (?, ?, datetime('now'), datetime('now'), 'completed',
                          ?, ?, ?, ?, ?)
            """, (
                result.game_id,
                session_id,
                result.score,
                result.actions_taken,
                result.is_win,
                result.levels_completed,
                self.current_generation,
            ))

            # Store winning sequence if won
            if result.is_win and result.action_sequence:
                self.db.execute_query("""
                    INSERT INTO winning_sequences (
                        game_id, sequence_data, score, generation, agent_id,
                        is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, TRUE, datetime('now'))
                """, (
                    result.game_id,
                    ','.join(result.action_sequence),
                    result.score,
                    self.current_generation,
                    result.agent_id,
                ))
                print(f"    [SAVED] Winning sequence for {result.game_id}")

        except Exception as e:
            print(f"  [WARN] Failed to store result: {e}")

    def evolve(self):
        """
        Evolve population: select best agents, create offspring.

        Simple tournament selection + mutation.
        """
        print(f"\n[EVOLVE] Evolving population...")

        # Sort by fitness (avg score * win_rate bonus)
        def fitness(a: AgentState) -> float:
            return a.avg_score * (1 + a.win_rate)

        self.agents.sort(key=fitness, reverse=True)

        # Keep top 50% (minimum 1)
        keep_count = max(1, len(self.agents) // 2)
        survivors = self.agents[:keep_count]
        print(f"  Top performers: {[f'{a.agent_id[:8]}(s={a.avg_score:.1f})' for a in survivors[:3]]}")

        # Create offspring from survivors
        offspring = []
        while len(survivors) + len(offspring) < self.population_size:
            parent = random.choice(survivors)
            child = AgentState(
                agent_id=self._create_agent_id(),
                generation=self.current_generation + 1,
            )
            offspring.append(child)

            # Default genome (could inherit/mutate from parent)
            genome = '{"exploration_rate": 0.3, "learning_rate": 0.1}'

            # Store in database
            self.db.execute_query("""
                INSERT INTO agents (
                    agent_id, generation, agent_type, genome, specialization,
                    parent_ids, created_at, is_active
                ) VALUES (?, ?, 'evolved', ?, 'generalist', ?, datetime('now'), TRUE)
            """, (child.agent_id, child.generation, genome, f'["{parent.agent_id}"]'))

        self.agents = survivors + offspring
        print(f"  New population: {len(survivors)} survivors + {len(offspring)} offspring = {len(self.agents)}")

    def run(self):
        """Main evolution loop."""
        print("\n" + "="*60)
        print("EVOLUTION RUNNER")
        print("="*60)
        print(f"Mode: {self.mode.upper()}")
        print(f"Population: {self.population_size}")
        print(f"Games/Gen: {self.games_per_generation}")
        print(f"Max Generations: {self.max_generations}")
        if self.target_game:
            print(f"Target Game: {self.target_game}")
        print("="*60)

        # Initialize
        self.agents = self.initialize_population()

        # Main loop
        while self.running and self.current_generation < self.max_generations:
            # Run generation
            stats = self.run_generation()

            if not self.running:
                break

            # Evolve
            self.evolve()

            self.current_generation += 1

        # Final summary
        print("\n" + "="*60)
        print("EVOLUTION COMPLETE")
        print("="*60)
        print(f"Generations: {self.current_generation}")
        print(f"Final population: {len(self.agents)}")

        if self.agents:
            best = max(self.agents, key=lambda a: a.avg_score)
            print(f"Best agent: {best.agent_id} (avg score: {best.avg_score:.2f}, wins: {best.wins})")


def main():
    parser = argparse.ArgumentParser(description='Evolution Runner')
    parser.add_argument('--mode', choices=['online', 'offline', 'normal'], default='normal',
                       help='Operation mode')
    parser.add_argument('--population', type=int, default=10,
                       help='Population size')
    parser.add_argument('--games-per-gen', type=int, default=5,
                       help='Games per generation per agent')
    parser.add_argument('--max-generations', type=int, default=10,
                       help='Maximum generations')
    parser.add_argument('--max-actions', type=int, default=500,
                       help='Max actions per game')
    parser.add_argument('--game', type=str, default=None,
                       help='Target specific game (e.g., ls20)')
    parser.add_argument('--test', action='store_true',
                       help='Quick test mode (1 agent, 1 game, 1 gen)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show each action and score during gameplay')

    args = parser.parse_args()

    # Test mode overrides
    if args.test:
        args.population = 1
        args.games_per_gen = 1
        args.max_generations = 1
        args.max_actions = 100

    runner = EvolutionRunner(
        mode=args.mode,
        population_size=args.population,
        games_per_generation=args.games_per_gen,
        max_generations=args.max_generations,
        max_actions_per_game=args.max_actions,
        target_game=args.game,
        verbose=args.verbose,
    )

    runner.run()


if __name__ == "__main__":
    main()
