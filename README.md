# BitterTruth-AI

A sophisticated ARC-AGI-3 game player with **evolved algorithmic intelligence**. Features a comprehensive evolution system that learns and adapts strategies using real-world algorithms, genetic programming, and multi-armed bandits.

## Features

- **🧬 Evolved Algorithm System**: 25+ real-world algorithms adapted for gameplay
- **🎯 Intelligent Action Selection**: Algorithms learn and improve over time
- **📊 Performance Analytics**: Comprehensive tracking and evolution metrics
- **🔄 Algorithm Inheritance**: Multi-parent evolution with proper lineage tracking
- **🎮 Multiple Strategies**: From simple random to sophisticated evolved intelligence
- **💾 Database Persistence**: Complete game history and algorithm performance data
- **🏷️ Smart Tagging**: Automatic BitterLesson tagging with git integration

## Core Components

### ARCClient
- Connect to ARC-AGI-3 API
- Manage scorecards and game state with automatic tagging
- Send actions with retry logic and error handling
- Handle authentication and rate limiting
- Generate automatic tags including "BitterLesson", git branch, and commit ID

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
python main_runner.py play game_123 --api-key YOUR_KEY

# Run a gaming session with evolved strategy
python main_runner.py session --max-games 5 --strategy evolved

# Run with traditional strategies
python main_runner.py session --max-games 5 --strategy balanced

# Show statistics
python main_runner.py stats

# List available games
python main_runner.py list --api-key YOUR_KEY

# Evolution system management
python main_runner.py evolution manage init     # Initialize evolution system
python main_runner.py evolution stats           # Show evolution statistics
python main_runner.py evolution status          # Show system status
```

### Environment Setup

#### Option 1: Using .env file (Recommended)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your ARC-AGI-3 API key:
```bash
# ARC-AGI-3 API Configuration (REQUIRED)
ARC_API_KEY=your_actual_api_key_here

# Optional: Database Configuration
DATABASE_PATH=core_data.db

# Optional: Logging Configuration
LOG_LEVEL=INFO

# Optional: API Configuration
ARC_BASE_URL=https://arc-agi3-production.up.railway.app

# Python Configuration
# Disable Python bytecode (.pyc) file generation
PYTHONDONTWRITEBYTECODE=1
```

#### Option 2: Using environment variables

```bash
export ARC_API_KEY="your_arc_api_key_here"
```

## Advanced Usage

### Evolution System

```bash
# Initialize the evolution system with seeded algorithms
python main_runner.py evolution manage init

# Run games with evolved strategy (uses best performing algorithms)
python main_runner.py session --strategy evolved --max-games 10

# View evolution statistics
python main_runner.py evolution stats

# Check system status
python main_runner.py evolution status
```

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
import game_session_manager
import action_handler

session_manager = game_session_manager.GameSessionManager()
action_handler_instance = action_handler.ActionHandler(session_manager)

try:
    # Start session
    session_id = await session_manager.start_session()

    # Create game
    game_data = await session_manager.create_game("game_123")

    # Send actions
    game_state = await action_handler_instance.send_action_1()
    game_state = await action_handler_instance.send_action_6(x=5, y=3, frame=game_state.frame)

    # Finish game
    await session_manager.finish_game(game_state.state, game_state.score)

finally:
    await session_manager.shutdown()
```

### Database Operations

```python
import database_interface

db = database_interface.DatabaseInterface("my_games.db")

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

**Core Game Tables:**
- **training_sessions**: Session metadata and statistics
- **game_results**: Individual game outcomes
- **action_traces**: Detailed action logging
- **action_effectiveness**: Action performance tracking
- **score_history**: Score progression over time
- **global_counters**: System state counters

**Evolution System Tables:**
- **algorithms**: Algorithm definitions and AST representations
- **algorithm_performance**: Performance tracking and fitness scores
- **evolution_generations**: Generation-by-generation evolution tracking
- **algorithm_routines**: Game-type specific algorithm sequences
- **seeded_algorithms_meta**: Metadata for real-world algorithm adaptations
- **game_type_performance**: Performance metrics by game type prefix

## Configuration

The `GameplayEngine` can be configured with various parameters:

```python
engine.configure(
    max_actions_per_game=100,      # Maximum actions per game
    action_timeout=30.0,           # Timeout for actions
    strategy='evolved',            # Default strategy (evolved recommended)
    enable_random_exploration=True, # Allow random exploration
    coordinate_retry_limit=3       # Retries for ACTION6
)
```

## Scorecard Tagging

### Automatic Tag Generation

The ARCClient automatically generates identifying tags for each scorecard created with the ARC-AGI-3 API:

**Core Tags:**
- `core_game_mechanics` - Identifies this module
- `BitterLesson` - Project identifier

**Git Information** (when available):
- `branch_{branch_name}` - Current git branch (e.g., `branch_v1.0.1`)
- `commit_{short_hash}` - Short commit hash (e.g., `commit_2506d85`)
- `git_unavailable` - Fallback when git is not available

**Runtime Information:**
- `pid_{process_id}` - Process identifier
- `thread_{thread_id}` - Thread identifier
- `session_{session_id}` - Session identifier (first 8 characters)
- `game_{game_id}` - Game identifier
- `ts_{timestamp}` - Timestamp (HHMMSS format)
- `sys_{system}` - Operating system (windows, linux, darwin)

**Example Tags:**
```
["core_game_mechanics", "BitterLesson", "branch_v1.0.1", "commit_2506d85",
 "pid_12345", "thread_67890", "session_abc12345", "game_test_001",
 "ts_143022", "sys_windows"]
```

This tagging system helps track and identify game sessions across different environments and git states.

## Python Configuration

### Disabling Python Bytecode Files

The project is configured to disable Python bytecode (`.pyc`) file generation to keep the workspace clean:

- **Environment Variable**: `PYTHONDONTWRITEBYTECODE=1` (set in `.env` file)
- **Command Line**: Use `python -B` to run scripts with bytecode generation disabled
- **Git**: `__pycache__/` directories are automatically ignored via `.gitignore`

**Benefits:**
- Cleaner project directory without `__pycache__` folders
- Reduced file system clutter during development
- Simplified version control (no bytecode files to track)

**Alternative Methods:**
```bash
# Run with bytecode disabled
python -B main_runner.py

# Or set environment variable manually
export PYTHONDONTWRITEBYTECODE=1
python main_runner.py
```

## Built-in Strategies

- **evolved**: Uses the algorithmic evolution system with 25+ real-world algorithms (recommended)
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

## Recent Improvements (v1.0.1)

### Critical Bug Fixes

**List Subtraction Error Resolution**
- Fixed "unsupported operand type(s) for -: 'list' and 'list'" error that was causing evolution system failures
- Added comprehensive type checking for all score operations in:
  - `main_runner.py`: Score handling in evolved_strategy function
  - `algorithm_evaluator.py`: Score validation in _evaluate_action_node method
  - `coordinate_strategies.py`: Score type safety in generate_action6_coordinates
  - `start_game.py`: Score normalization during game context updates
  - `evolution_manager.py`: Score validation in routine context updates

**Enhanced Error Logging**
- Added detailed warning messages when list scores are detected and converted
- Implemented defensive programming with try-catch blocks around all score arithmetic
- Added comprehensive logging with type information for debugging

### Algorithm System Enhancements

**Coordinate Generation Improvements**
- Fixed coordinate bounds to properly use 0-63 range for ACTION6
- Enhanced 8-strategy coordinate generation system:
  - Random uniform distribution across full coordinate space
  - Systematic grid exploration (8x8 grid)
  - Spiral outward pattern from center
  - Corner-focused exploration with center variance
  - Edge-focused coordinate selection
  - Gradient-following based on successful coordinates
  - Clustered exploration around success zones
  - Frame analysis for activity-based coordinate selection

**Meta Strategy System**
- Implemented 4 comprehensive meta strategies:
  - `FRAME_AVOID`: Avoid coordinates where frame changes occurred
  - `FRAME_TARGET`: Target coordinates near recent frame changes
  - `ACTION_REPEAT`: Repeat coordinates from recent successful actions
  - `ACTION_NEARBY`: Explore coordinates near recent successes
- Algorithm-specific meta strategy pairing for optimal performance
- Frame change detection and analysis for intelligent coordinate enhancement

**Evolution System Stability**
- Fixed algorithm switching logic to trigger based on performance conditions
- Enhanced Multi-Armed Bandit (MAB) algorithm selection
- Improved evolution triggering based on:
  - Frequency-based evolution (every N games)
  - Performance stagnation detection
  - Population depletion protection
- Added comprehensive algorithm performance tracking and fitness calculation

### Performance & Reliability

**API Rate Limiting**
- Added 1-2 second delays between API actions to prevent overwhelming the server
- Implemented exponential backoff for failed requests
- Enhanced retry logic with proper error handling

**Python Environment Optimization**
- Disabled Python bytecode (.pyc) file generation globally with multiple methods:
  - Environment variable `PYTHONDONTWRITEBYTECODE=1`
  - Programmatic `sys.dont_write_bytecode = True`
  - Command-line flag `-B` in execution scripts
- Automatic __pycache__ directory cleanup

**Console Output Enhancements**
- Added algorithm visibility showing which algorithm makes each decision
- Enhanced coordinate information display for ACTION6
- Improved error messages with detailed type information
- Real-time algorithm switching notifications

### Development Improvements

**Database Integration**
- Enhanced algorithm performance persistence
- Improved evolution history tracking
- Better session and game result management
- Comprehensive seeded algorithm metadata storage

**Code Quality**
- Added comprehensive type checking throughout the codebase
- Improved error handling with graceful fallbacks
- Enhanced logging with detailed debugging information
- Better separation of concerns in algorithm evaluation

### Known Issues Resolved

- ✅ **Fixed**: List subtraction errors in evolution system
- ✅ **Fixed**: Algorithm switching not occurring during gameplay
- ✅ **Fixed**: Hardcoded coordinates in ACTION6 instead of dynamic generation
- ✅ **Fixed**: Evolution system not triggering at game completion
- ✅ **Fixed**: Coordinate bounds validation errors
- ✅ **Fixed**: Python bytecode file generation issues
- ✅ **Fixed**: Action selection logic choosing unavailable actions

### Migration Notes

No breaking changes - existing databases and configurations remain compatible. The system will automatically apply the new type checking and error handling improvements.

## Database Logging

All application logs are stored in the database instead of files for better organization and queryability:

```python
from database_logger import setup_database_logging

# Set up database logging (automatic in all modules)
db_handler = setup_database_logging()

# Logs are written to both console and database 'system_logs' table
# Log level controlled by LOG_LEVEL environment variable
```

### Viewing Logs

```python
from database_logger import get_recent_logs

# Get recent logs from database
logs = get_recent_logs(limit=50, level='INFO')

# Filter by session or game
session_logs = get_recent_logs(session_id='session_123')
game_logs = get_recent_logs(game_id='game_456')
```

**Benefits of Database Logging:**
- No log files cluttering the filesystem
- Structured, queryable log data
- Session and game context tracking
- Automatic cleanup and organization
- Enhanced searching and filtering

## File Structure

```
BitterTruth-AI/
├── main_runner.py                    # Primary entry point and CLI
├── start_game.py                     # Alternative simple game starter
├── core_gameplay.py                  # Main gameplay engine
├── game_session_manager.py           # Session lifecycle management
├── action_handler.py                 # Action sending and validation
├── arc_api_client.py                 # ARC-AGI-3 API client
├── database_interface.py             # Database operations
├── evolution_manager.py              # Evolution system orchestrator
├── routine_manager.py                # Game-type specific algorithm routines
├── seeded_algorithm_builders.py      # Real-world algorithm adaptations
├── algorithm_representations.py      # AST and algorithm structures
├── core_database_schema.sql          # Database schema with evolution tables
├── algorithms-list.md                # List of implemented algorithms
├── .env.example                      # Environment configuration template
└── README.md                         # This file
```

## Requirements

- Python 3.7+
- aiohttp
- sqlite3 (built-in)
- python-dotenv (optional, for .env file support)
- ARC-AGI-3 API key

## Installation

1. Clone the repository: `git clone <repository_url>`
2. Install dependencies: `pip install aiohttp python-dotenv`
3. Set up environment variables (see Environment Setup section above)
4. Initialize evolution system: `python main_runner.py evolution manage init`
5. Run your first game: `python main_runner.py session --strategy evolved --max-games 1`

## Examples

See `start_game.py` for a simple standalone game example, or use `main_runner.py` for full functionality including the evolution system.

## License

This module is part of the Tabula Rasa project.