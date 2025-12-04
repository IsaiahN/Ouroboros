"""
Core ARC-AGI-3 API Client

A clean, modular client for interacting with the ARC-AGI-3 API.
Contains only the essential functionality needed for gameplay.
No architect, governor, or director-specific code.
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, fall back to system environment variables
    pass

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
DEFAULT_BASE_URL = os.getenv('ARC_BASE_URL', "https://arc-agi3-production.up.railway.app")

# Check if we need /api/ prefix (for three.arcprize.org)
API_PREFIX = "/api" if "three.arcprize.org" in DEFAULT_BASE_URL else ""

GAMES_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/games"
SCORECARD_OPEN_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/scorecard/open"
SCORECARD_CLOSE_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/scorecard/close"
RESET_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/RESET"
ACTION1_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION1"
ACTION2_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION2"
ACTION3_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION3"
ACTION4_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION4"
ACTION5_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION5"
ACTION6_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION6"
ACTION7_ENDPOINT = f"{DEFAULT_BASE_URL}{API_PREFIX}/cmd/ACTION7"


@dataclass
class GameState:
    """Represents the current state of a game."""
    game_id: str
    guid: str
    state: str  # 'NOT_FINISHED', 'WIN', 'GAME_OVER'
    score: float
    win_score: float
    frame: List[List[int]]
    action_input: Optional[str]
    available_actions: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create GameState from API response."""
        # Unwrap frame if it's nested in extra arrays
        # API returns: [ [[64_rows_x_64_cols]] ] -> we want: [[64_rows_x_64_cols]]
        frame = data.get('frame', [])
        while frame and len(frame) == 1 and isinstance(frame[0], list) and len(frame[0]) > 1:
            frame = frame[0]
        
        return cls(
            game_id=data.get('game_id', ''),
            guid=data.get('guid', ''),
            state=data.get('state', 'UNKNOWN'),
            score=float(data.get('score', 0.0)),
            win_score=float(data.get('win_score', 0.0)),
            frame=frame,
            action_input=data.get('action_input'),
            available_actions=data.get('available_actions', [])
        )


@dataclass
class Scorecard:
    """Represents a scorecard for tracking performance."""
    card_id: str
    tags: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scorecard':
        """Create Scorecard from API response."""
        return cls(
            card_id=data.get('card_id', ''),
            tags=data.get('tags', [])
        )


class ARCError(Exception):
    """Base exception for ARC API errors."""
    pass


class ARCAuthenticationError(ARCError):
    """Raised when authentication fails."""
    pass


class ARCAPIError(ARCError):
    """Raised when the API returns an error."""
    pass


class ARCClient:
    """Core client for interacting with the ARC-AGI-3 API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the ARC-AGI-3 API client.

        Args:
            api_key: Your ARC API key. If not provided, will try to get from ARC_API_KEY env var.
            base_url: Base URL for the ARC API. Defaults to the production API.
        """
        self.api_key = api_key or os.getenv('ARC_API_KEY')
        if not self.api_key:
            raise ARCAuthenticationError(
                "ARC API key is required. Set ARC_API_KEY environment variable or pass api_key parameter."
            )

        self.base_url = base_url or DEFAULT_BASE_URL
        self.session = None
        self.current_game_id = None
        self.current_guid = None
        self.current_card_id = None
        self.current_scorecard_id = None

        # Headers for API requests
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        logger.info(f"Initialized ARC client with base URL: {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        # Create timeout with longer durations for long-running games
        timeout = aiohttp.ClientTimeout(
            total=None,  # No total timeout
            connect=30,  # 30 seconds to establish connection
            sock_read=600  # 10 minutes for reading response (very long games)
        )
        # Create connector with keep-alive enabled
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,  # Cache DNS for 5 minutes
            enable_cleanup_closed=True,
            force_close=False  # Keep connections alive
        )
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout,
            connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            # Give aiohttp time to close connections
            await asyncio.sleep(0.25)
            self.session = None
        self._reset_state()

    async def close(self):
        """Manually close the session and cleanup resources."""
        if self.session:
            await self.session.close()
            # Give aiohttp time to close connections
            await asyncio.sleep(0.25)
            self.session = None
        self._reset_state()

    def _reset_state(self):
        """Reset internal state variables."""
        self.current_game_id = None
        self.current_guid = None
        self.current_card_id = None
        self.current_scorecard_id = None

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the ARC API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments for the request

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            ARCError: If the request fails after all retries
            ARCAuthenticationError: If authentication fails
            ARCAPIError: If the API returns an error response
        """
        if not self.session:
            raise ARCError("Session not initialized. Use async with statement.")

        max_retries = 3
        retry_delay = 1

        logger.debug(f"Making {method} request to {url}")

        for attempt in range(max_retries):
            try:
                async with self.session.request(method=method, url=url, **kwargs) as response:
                    # Handle rate limiting with exponential backoff
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            logger.info(f"Rate limit hit, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Rate limit exceeded, max retries reached")
                            raise ARCAPIError("Rate limit exceeded, max retries reached")

                    # Parse JSON response
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        logger.error(f"Non-JSON response: {text}")
                        raise ARCAPIError(f"Non-JSON response: {text}")

                    # Handle authentication errors
                    if response.status == 401:
                        error_msg = data.get('error', 'Authentication failed - invalid API key')
                        logger.error(f"Authentication error: {error_msg}")
                        raise ARCAuthenticationError(error_msg)

                    # Handle game completion states
                    if response.status == 400 and data.get('error') == 'GAME_NOT_STARTED_ERROR':
                        logger.info("Game appears to be over (GAME_NOT_STARTED_ERROR)")
                        return {
                            'state': 'GAME_OVER',
                            'game_id': data.get('game_id', 'unknown'),
                            'score': data.get('score', 0),
                            'frame': [],
                            'available_actions': [],
                            'error': None
                        }
                    elif response.status == 404 and data.get('error') == 'VALIDATION_ERROR':
                        logger.info("Game validation error - likely game completed or expired")
                        return {
                            'state': 'GAME_OVER',
                            'game_id': data.get('game_id', 'unknown'),
                            'score': data.get('score', 0),
                            'frame': [],
                            'available_actions': [],
                            'error': None
                        }

                    # Handle other error status codes
                    if response.status >= 400:
                        error_msg = data.get('error', data.get('message', 'Unknown error'))
                        logger.error(f"API error {response.status}: {error_msg}")
                        raise ARCAPIError(f"API request failed with status {response.status}: {error_msg}")

                    return data

            except aiohttp.ClientError as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                continue

        error_msg = f"Failed to complete request after {max_retries} attempts"
        logger.error(error_msg)
        raise ARCError(error_msg)

    async def get_available_games(self) -> List[Dict[str, Any]]:
        """Get list of available games.

        Returns:
            List of available games with their metadata
        """
        response = await self._make_request("GET", GAMES_ENDPOINT)
        # Ensure we return a list
        if isinstance(response, dict):
            # If the API returns a dict with a games key, extract it
            if 'games' in response:
                return response['games']
            # Otherwise wrap the single game in a list
            return [response]
        return response

    def generate_tags(self, game_id: Optional[str] = None, session_id: Optional[str] = None, 
                     agent_id: Optional[str] = None, agent_mode: Optional[str] = None) -> List[str]:
        """Generate tags for scorecard identification.
        
        Args:
            game_id: Game identifier
            session_id: Session identifier
            agent_id: Agent identifier (optional)
            agent_mode: Agent operating mode - 'pioneer', 'optimizer', 'generalist' (optional)
        """
        import threading
        import platform
        import subprocess

        tags = ["BitterLesson"]

        # Add Git information
        git_available = False
        try:
            # Get current git branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            if branch_result.returncode == 0:
                branch_name = branch_result.stdout.strip()
                tags.append(f"branch_{branch_name}")
                git_available = True

            # Get last commit ID (short hash)
            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            if commit_result.returncode == 0:
                commit_id = commit_result.stdout.strip()
                tags.append(f"commit_{commit_id}")
                git_available = True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Git not available or not a git repository
            pass

        if not git_available:
            tags.append("git_unavailable")

        # Add Process ID
        pid = os.getpid()
        tags.append(f"pid_{pid}")

        # Add thread ID
        thread_id = threading.get_ident()
        tags.append(f"thread_{thread_id}")

        # Add session information
        if session_id:
            tags.append(f"session_{session_id[:8]}")

        # Add game information
        if game_id:
            tags.append(f"game_{game_id}")

        # Add timestamp
        timestamp = datetime.now().strftime("%H%M%S")
        tags.append(f"ts_{timestamp}")

        # Add system identifier
        tags.append(f"sys_{platform.system().lower()}")
        
        # Add agent information
        if agent_id:
            tags.append("agent")  # General tag indicating this is an agent run
            # Full agent ID for proper identification (was truncated causing "offsprin" bug)
            tags.append(f"agent_{agent_id}")
        
        # Add agent mode (CRITICAL: shows if optimizer/pioneer/generalist)
        if agent_mode:
            tags.append(f"mode_{agent_mode}")
            
            # If optimizer, add target level they're optimizing
            # This will be set by core_gameplay when optimizer starts
            optimizer_level = getattr(self, '_optimizer_target_level', None)
            if agent_mode == 'optimizer' and optimizer_level:
                tags.append(f"opt_level_{optimizer_level}")
        
        # Add parent agent tracking (for offspring lineage)
        parent_ids = getattr(self, '_parent_agent_ids', None)
        if parent_ids:
            if isinstance(parent_ids, (list, tuple)) and len(parent_ids) >= 2:
                tags.append(f"parent1_{parent_ids[0]}")
                tags.append(f"parent2_{parent_ids[1]}")
            elif isinstance(parent_ids, str):
                tags.append(f"parent_{parent_ids}")

        return tags

    async def open_scorecard(self, tags: Optional[List[str]] = None) -> Scorecard:
        """Open a new scorecard for tracking performance.

        Args:
            tags: Optional list of tags for the scorecard

        Returns:
            Scorecard: The opened scorecard
        """
        payload = {}
        if tags:
            payload["tags"] = tags

        response = await self._make_request("POST", SCORECARD_OPEN_ENDPOINT, json=payload)

        scorecard = Scorecard.from_dict(response)
        self.current_scorecard_id = scorecard.card_id

        logger.info(f"Opened scorecard: {scorecard.card_id}")
        return scorecard

    async def close_scorecard(self, card_id: Optional[str] = None) -> Dict[str, Any]:
        """Close a scorecard.

        Args:
            card_id: Scorecard ID to close. If not provided, uses current scorecard.

        Returns:
            Scorecard results
        """
        # Check if session is still active before attempting to close
        if not self.session:
            logger.warning(f"Session already closed, cannot close scorecard {card_id}")
            return {"status": "session_closed", "card_id": card_id}
        
        if not card_id:
            if not self.current_scorecard_id:
                raise ValueError("No scorecard ID provided and no current scorecard")
            card_id = self.current_scorecard_id

        payload = {"card_id": card_id}
        response = await self._make_request("POST", SCORECARD_CLOSE_ENDPOINT, json=payload)

        logger.info(f"Closed scorecard: {card_id}")
        return response

    async def reset_game(self, game_id: str, card_id: Optional[str] = None) -> GameState:
        """Reset the current game or start a new one.

        Args:
            game_id: Game ID to reset
            card_id: Scorecard ID. If not provided, uses current scorecard.

        Returns:
            GameState: The initial game state after reset.
        """
        # Check if session is still active
        if not self.session:
            raise ARCError("Session already closed, cannot reset game")
        
        if not card_id:
            if not self.current_scorecard_id:
                raise ValueError("No scorecard ID provided and no current scorecard")
            card_id = self.current_scorecard_id

        payload = {
            "game_id": game_id,
            "card_id": card_id
        }

        response = await self._make_request("POST", RESET_ENDPOINT, json=payload)

        # Update game state
        self.current_game_id = response.get("game_id")
        self.current_guid = response.get("guid")

        return GameState.from_dict(response)

    async def reset_level(self, game_id: Optional[str] = None, card_id: Optional[str] = None,
                         guid: Optional[str] = None) -> GameState:
        """Reset the CURRENT LEVEL (not the whole game) to initial frame state.
        
        Per ARC API documentation:
        - With guid provided: Resets current level if actions were taken
        - This allows retrying a level with a fresh initial frame
        
        Args:
            game_id: Game ID. If not provided, uses current game.
            card_id: Scorecard ID. If not provided, uses current scorecard.
            guid: Game GUID. REQUIRED for level reset (must be provided).
            
        Returns:
            GameState: The initial game state of the current level after reset.
        """
        if not self.session:
            raise ARCError("Session already closed, cannot reset level")
        
        # Use current values if not provided
        if not game_id:
            game_id = self.current_game_id
        if not card_id:
            card_id = self.current_scorecard_id
        if not guid:
            guid = self.current_guid
            
        if not all([game_id, card_id, guid]):
            raise ValueError("reset_level requires game_id, card_id, AND guid to reset current level")

        payload = {
            "game_id": game_id,
            "card_id": card_id,
            "guid": guid  # CRITICAL: With guid = level reset, without guid = new game
        }
        
        logger.info(f"[LEVEL RESET] Resetting level for game {game_id}, guid {guid[:8]}...")

        response = await self._make_request("POST", RESET_ENDPOINT, json=payload)

        # Update game state (guid should remain the same for level reset)
        self.current_game_id = response.get("game_id")
        self.current_guid = response.get("guid")
        
        logger.info(f"[LEVEL RESET] Level reset complete. Score: {response.get('score')}, State: {response.get('state')}")

        return GameState.from_dict(response)

    async def send_action(self, action: str, game_id: Optional[str] = None, card_id: Optional[str] = None,
                         guid: Optional[str] = None, x: Optional[int] = None, y: Optional[int] = None, **kwargs) -> GameState:
        """Send an action to the game.

        Args:
            action: The action to send (ACTION1, ACTION2, etc.)
            game_id: Game ID. If not provided, uses current game.
            card_id: Scorecard ID. If not provided, uses current scorecard.
            guid: Game GUID. If not provided, uses current GUID.
            x: X coordinate for ACTION6
            y: Y coordinate for ACTION6
            **kwargs: Additional parameters for the action

        Returns:
            GameState: The new game state after the action
        """
        # Use current values if not provided
        if not game_id:
            game_id = self.current_game_id
        if not card_id:
            card_id = self.current_scorecard_id
        if not guid:
            guid = self.current_guid

        if not all([game_id, card_id, guid]):
            raise ValueError("Missing required parameters: game_id, card_id, and guid must be provided")

        # Map action to endpoint
        action_endpoints = {
            "ACTION1": ACTION1_ENDPOINT,
            "ACTION2": ACTION2_ENDPOINT,
            "ACTION3": ACTION3_ENDPOINT,
            "ACTION4": ACTION4_ENDPOINT,
            "ACTION5": ACTION5_ENDPOINT,
            "ACTION6": ACTION6_ENDPOINT,
            "ACTION7": ACTION7_ENDPOINT
        }

        if action not in action_endpoints:
            raise ValueError(f"Invalid action: {action}. Must be one of {list(action_endpoints.keys())}")

        # Prepare request data
        payload: Dict[str, Any] = {
            "game_id": game_id,
            "card_id": card_id,
            "guid": guid
        }

        # Add action-specific parameters
        if action == "ACTION6":
            if x is None or y is None:
                raise ValueError("ACTION6 requires x and y coordinates")
            payload["x"] = x
            payload["y"] = y
            logger.info(f"Sending {action} to API with coordinates ({x}, {y})")
        else:
            logger.info(f"Sending {action} to API")
        
        # Add reasoning for ALL actions (optional JSON blob ≤16 KB)
        if "reasoning" in kwargs and kwargs["reasoning"]:
            payload["reasoning"] = kwargs["reasoning"]

        # Make the request
        response = await self._make_request("POST", action_endpoints[action], json=payload)
        
        logger.info(f"{action} API response - State: {response.get('state')}, Score: {response.get('score')}")

        # Update game state - preserve existing values if API doesn't return them
        # CRITICAL FIX: API sometimes doesn't include game_id/guid in response
        # Only update if present in response to prevent losing session state
        response_had_game_id = bool(response.get("game_id"))
        response_had_guid = bool(response.get("guid"))
        
        if response.get("game_id"):
            self.current_game_id = response.get("game_id")
        elif not self.current_game_id:
            logger.error(f"[WARN] CRITICAL: API response missing game_id AND current_game_id is None!")
            
        if response.get("guid"):
            self.current_guid = response.get("guid")
        elif not self.current_guid:
            logger.error(f"[WARN] CRITICAL: API response missing guid AND current_guid is None!")
            
        # Note: card_id is set via open_scorecard() and should persist through actions
        if not self.current_scorecard_id:
            logger.error(f"[WARN] CRITICAL: current_scorecard_id is None!")

        # Create GameState from response
        game_state = GameState.from_dict(response)
        
        # CRITICAL: Patch game_state if API didn't include game_id/guid
        # This ensures game_state object always has valid credentials
        patched = False
        if not game_state.game_id and self.current_game_id:
            game_state.game_id = self.current_game_id
            patched = True
        if not game_state.guid and self.current_guid:
            game_state.guid = self.current_guid
            patched = True
            
        if patched:
            logger.warning(f"[FIX] Patched GameState with preserved credentials (response had game_id={response_had_game_id}, guid={response_had_guid})")
        
        return game_state

    async def create_game(self, game_id: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new game by opening a scorecard and resetting the game.

        Args:
            game_id: Game ID to create/reset
            tags: Optional list of tags for the scorecard

        Returns:
            Dictionary containing the initial game state and scorecard info
        """
        try:
            # Open a new scorecard
            scorecard = await self.open_scorecard(tags or self.generate_tags(game_id=game_id))

            # Reset the game with the new scorecard
            game_state = await self.reset_game(game_id, scorecard.card_id)

            logger.info(f"Created game {game_id} with scorecard {scorecard.card_id}")

            return {
                'game_id': game_state.game_id,
                'guid': game_state.guid,
                'scorecard_id': scorecard.card_id,
                'frame': game_state.frame,
                'state': game_state.state,
                'score': game_state.score,
                'win_score': game_state.win_score,
                'action_input': game_state.action_input,
                'available_actions': game_state.available_actions
            }

        except Exception as e:
            logger.error(f"Error creating game {game_id}: {e}")
            raise