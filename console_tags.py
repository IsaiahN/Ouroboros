import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Console Tags - Unified logging tag system for Ouroboros.

Provides consistent console output formatting across all modules.
Per SYSTEM_COHERENCE_REPORT.md recommendations.

Usage:
    from console_tags import TAGS, log
    
    print(f"{TAGS['generation']} Gen 45 starting with 60 agents")
    # or
    log('generation', "Gen 45 starting with 60 agents")
"""

# ============================================================================
# STANDARDIZED CONSOLE TAGS
# Use these instead of ad-hoc prefixes for consistent output
# ============================================================================

TAGS = {
    # Lifecycle events
    'generation': '[GENERATION]',
    'evolution': '[EVOLUTION]',
    'agent': '[AGENT]',
    'budget': '[BUDGET]',
    'result': '[RESULT]',
    'scheduled': '[SCHEDULED]',
    
    # Sequence system
    '3_try': '[3-TRY]',
    'multi_stage': '[MULTI-STAGE]',
    'template': '[TEMPLATE]',
    'sequence': '[SEQUENCE]',
    
    # Cognitive systems
    'cods': '[CODS]',
    'rule': '[RULE]',
    'selection': '[SELECTION]',
    'goal_inferred': '[GOAL INFERRED]',
    'hypothesis': '[HYPOTHESIS]',
    'world_model': '[WORLD-MODEL]',
    
    # Navigation and control
    'escape': '[ESCAPE]',
    'sync': '[SYNC]',
    'self_directed': '[SELF-DIRECTED]',
    'stop': '[STOP]',
    'pause': '[PAUSE]',
    
    # Analysis systems
    'frustration': '[FRUSTRATION]',
    'near_miss': '[NEAR-MISS]',
    'counterfactual': '[COUNTERFACTUAL]',
    'ensemble': '[ENSEMBLE]',
    
    # Network systems
    'viral': '[VIRAL]',
    'prestige': '[PRESTIGE]',
    'network': '[NETWORK]',
    'homeostasis': '[HOMEOSTASIS]',
    'signals': '[SIGNALS]',
    
    # Planning
    'subgoal': '[SUBGOAL]',
    'meta': '[META]',
    
    # Decision memory and sensation
    'dm': '[DM]',
    'sensation': '[SENSATION]',
    
    # Autopoiesis and metrics
    'autopoiesis': '[AUTOPOIESIS]',
    'emergence': '[EMERGENCE]',
    'identity': '[IDENTITY]',
    
    # Disk and cleanup
    'disk_space': '[DISK SPACE]',
    'cleanup': '[CLEANUP]',
    'prune': '[PRUNE]',
    
    # DNA and evolution
    'dna': '[DNA]',
    'mutation': '[MUTATION]',
    'crossover': '[CROSSOVER]',
    
    # Optimization
    'optimization': '[OPTIMIZATION]',
    'optimizer': '[OPTIMIZER]',
    'pioneer': '[PIONEER]',
    'generalist': '[GENERALIST]',
    'exploiter': '[EXPLOITER]',
    
    # Status messages
    'ok': '[OK]',
    'warn': '[WARN]',
    'error': '[ERROR]',
    'critical': '[CRITICAL]',
    'info': '[INFO]',
    'debug': '[DEBUG]',
    
    # Regulation and history
    'regulation': '[REGULATION]',
    'history': '[HISTORY]',
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(tag_name: str, message: str, end: str = '\n') -> None:
    """
    Print a tagged message to console.
    
    Args:
        tag_name: Key from TAGS dict (e.g., 'generation', 'warn')
        message: The message to print
        end: Line ending (default newline)
    
    Example:
        log('generation', "Gen 45 starting")
        # Prints: [GENERATION] Gen 45 starting
    """
    tag = TAGS.get(tag_name, f'[{tag_name.upper()}]')
    print(f"{tag} {message}", end=end)


def log_ok(message: str) -> None:
    """Shortcut for success messages."""
    log('ok', message)


def log_warn(message: str) -> None:
    """Shortcut for warning messages."""
    log('warn', message)


def log_error(message: str) -> None:
    """Shortcut for error messages."""
    log('error', message)


def log_info(message: str) -> None:
    """Shortcut for info messages."""
    log('info', message)


def format_agent_line(
    role: str,
    agent_id: str,
    games: list,
    game_count: int
) -> str:
    """
    Format an agent assignment line.
    
    Args:
        role: Agent role (pioneer/optimizer/generalist/exploiter)
        agent_id: Full agent ID (will be truncated to 8 chars)
        games: List of game IDs assigned
        game_count: Number of games
    
    Returns:
        Formatted string like "[SCHEDULED] PIONEER abc12345 -> sp80, ls20 (3 games)"
    """
    game_types = list(set(g[:4] for g in games))
    return f"{TAGS['scheduled']} {role.upper()} {agent_id[:8]} -> {', '.join(game_types)} ({game_count} games)"


def format_result_line(
    score: int,
    actions: int,
    win: bool,
    level: int = -1
) -> str:
    """
    Format a game result line.
    
    Args:
        score: Final score
        actions: Total actions taken
        win: Whether game was won
        level: Optional level number reached (-1 if not specified)
    
    Returns:
        Formatted result string
    """
    win_str = "Win!" if win else "No Win"
    level_str = f", Level: {level}" if level >= 0 else ""
    return f"{TAGS['result']} Score: {score}, Actions: {actions}, {win_str}{level_str}"


# ============================================================================
# HIERARCHY TEMPLATE (for reference in documentation)
# ============================================================================

CONSOLE_HIERARCHY_TEMPLATE = """
[GENERATION] Gen 45 starting with 60 agents
  [AGENT] pioneer_abc12345 -> sp80, ls20 (3 games)
    [BUDGET] Game sp80-xxx: 800 total actions allocated
    [3-TRY] Attempt 1/3: sequence_id
    [CODS] Using operator: pixel_compare
    [RULE] Following rule abc123 (confidence: 0.85)
    [SELECTION] Clicking selectable object at (15, 20)
    [ESCAPE] ACTION3 to break frozen state
    [HYPOTHESIS] Generated failure hypothesis for level 2
    [FRUSTRATION] Agent frustration level: 0.7
  [RESULT] Score: 3, Actions: 245, Win: False
  [NEAR-MISS] Score 18/20 - analyzing failure point
[EVOLUTION] Gen 45 complete: 60% avg score, 2 wins
"""
