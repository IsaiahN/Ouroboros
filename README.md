# Core Game Mechanics

A clean, modular implementation of essential ARC-AGI-3 game functionality. This module contains only the core mechanics needed to play games without the complexity of architect, governor, or director systems.

## Features

- **Clean ARC API Client**: Simple interface for interacting with ARC-AGI-3 API
- **Session Management**: Handle game sessions with graceful startup and shutdown
- **Action Handling**: Send and validate game actions with automatic tracing
- **Database Persistence**: Store game data, action traces, and performance metrics
- **Gameplay Engine**: Complete game playing logic with multiple strategies
- **Performance Tracking**: Built-in statistics and effectiveness analysis

## Core Components

### ARCClient
- Connect to ARC-AGI-3 API
- Manage scorecards and game state
- Send actions with retry logic and error handling
- Handle authentication and rate limiting

### GameSessionManager
- Manage session lifecycle (start/shutdown)
- Track session statistics
- Handle graceful interruption
- Coordinate between API and database

### ActionHandler
- Send different types of actions (ACTION1-ACTION7)
- Validate coordinates for ACTION6
- Detect frame changes
- Track action effectiveness

### DatabaseInterface
- Store game results and action traces
- Manage session data
- Query performance statistics
- Handle database schema initialization

### GameplayEngine
- Complete game playing logic
- Multiple built-in strategies
- Support for custom action callbacks
- Session and multi-game management

## Quick Start

### Basic Usage

```python
import asyncio
from CORE_GAME_MECHANICS import GameplayEngine

async def play_game():
    # Initialize with your API key
    async with GameplayEngine(api_key="your_arc_api_key") as engine:
        # Play a single game
        result = await engine.play_single_game("game_123")
        print(f"Final score: {result['final_score']}")
        print(f"Won: {result['win']}")

asyncio.run(play_game())
```

### Command Line Usage

```bash
# Play a single game
python -m CORE_GAME_MECHANICS.main_runner play game_123 --api-key YOUR_KEY

# Run a gaming session
python -m CORE_GAME_MECHANICS.main_runner session --max-games 5 --strategy balanced

# Show statistics
python -m CORE_GAME_MECHANICS.main_runner stats

# List available games
python -m CORE_GAME_MECHANICS.main_runner list --api-key YOUR_KEY
```

### Environment Setup

```bash
export ARC_API_KEY="your_arc_api_key_here"
```

## Advanced Usage

### Custom Strategy

```python
async def my_strategy(game_state, action_handler):
    """Custom action selection strategy."""
    if game_state.score < 50:
        # Conservative approach at low scores
        return "ACTION1"
    else:
        # More aggressive when score is higher
        return action_handler.get_random_action(game_state.available_actions)

async with GameplayEngine() as engine:
    result = await engine.play_single_game("game_123", my_strategy)
```

### Manual Session Management

```python
from CORE_GAME_MECHANICS import GameSessionManager, ActionHandler

session_manager = GameSessionManager()
action_handler = ActionHandler(session_manager)

try:
    # Start session
    session_id = await session_manager.start_session()

    # Create game
    game_data = await session_manager.create_game("game_123")

    # Send actions
    game_state = await action_handler.send_action_1()
    game_state = await action_handler.send_action_6(x=5, y=3, frame=game_state.frame)

    # Finish game
    await session_manager.finish_game(game_state.state, game_state.score)

finally:
    await session_manager.shutdown()
```

### Database Operations

```python
from CORE_GAME_MECHANICS import DatabaseInterface

db = DatabaseInterface("my_games.db")

# Get performance statistics
stats = db.get_database_stats()
print(f"Total games played: {stats['game_results_count']}")

# Get recent game results
recent_games = db.get_game_results(limit=10)
for game in recent_games:
    print(f"Game {game['game_id']}: {game['final_score']} points")

# Analyze action effectiveness
effectiveness = db.get_action_effectiveness("game_123")
for action in effectiveness:
    print(f"ACTION{action['action_number']}: {action['success_rate']:.2f} success rate")
```

## Database Schema

The module creates the following core tables:

- **training_sessions**: Session metadata and statistics
- **game_results**: Individual game outcomes
- **action_traces**: Detailed action logging
- **action_effectiveness**: Action performance tracking
- **score_history**: Score progression over time
- **global_counters**: System state counters

## Configuration

The `GameplayEngine` can be configured with various parameters:

```python
engine.configure(
    max_actions_per_game=100,      # Maximum actions per game
    action_timeout=30.0,           # Timeout for actions
    strategy='balanced',           # Default strategy
    enable_random_exploration=True, # Allow random exploration
    coordinate_retry_limit=3       # Retries for ACTION6
)
```

## Built-in Strategies

- **balanced**: Uses action effectiveness data when available, falls back to random
- **random**: Random action selection
- **conservative**: Avoids ACTION6, prefers "safe" actions
- **exploration**: Prefers ACTION6 for exploration

## Error Handling

The module includes comprehensive error handling:

- API authentication errors
- Rate limiting with exponential backoff
- Game completion detection
- Database transaction safety
- Graceful shutdown on interruption

## Logging

Comprehensive logging is built-in:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs are written to both console and 'core_game_mechanics.log'
```

## File Structure

```
CORE_GAME_MECHANICS/
├── __init__.py                 # Module initialization and exports
├── arc_api_client.py          # ARC-AGI-3 API client
├── database_interface.py      # Database operations
├── game_session_manager.py    # Session lifecycle management
├── action_handler.py          # Action sending and validation
├── core_gameplay.py           # Main gameplay engine
├── main_runner.py             # Command-line interface
├── example_usage.py           # Usage examples
├── core_database_schema.sql   # Database schema
└── README.md                  # This file
```

## Requirements

- Python 3.7+
- aiohttp
- sqlite3 (built-in)
- ARC-AGI-3 API key

## Installation

1. Copy the `CORE_GAME_MECHANICS` folder to your project
2. Install dependencies: `pip install aiohttp`
3. Set your API key: `export ARC_API_KEY="your_key"`
4. Run examples: `python -m CORE_GAME_MECHANICS.example_usage`

## Examples

See `example_usage.py` for comprehensive examples of all functionality.

## License

This module is part of the Tabula Rasa project.