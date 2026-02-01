"""
Network Exploration Tracker: Collective spatial knowledge across all agents.

This module enables agents to:
1. Query what the NETWORK has explored on a level (not just themselves)
2. Save their exploration discoveries for future agents
3. Identify unexplored regions to prioritize
4. Build a "world map" from collective history

Key Insight: Instead of each agent starting blind, they inherit the network's
spatial knowledge and can focus on filling gaps rather than re-exploring.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class NetworkExplorationTracker:
    """
    Tracks and queries collective exploration data across all agents.

    The network builds a shared "world map" for each level:
    - Where have agents been?
    - What did they find there?
    - What actions were tried?
    - Where is dangerous vs productive?

    New agents query this map to explore UNEXPLORED areas efficiently.
    """

    # Grid quantization: divide frame into NxN regions
    GRID_SIZE = 8  # 8x8 = 64 regions per level

    def __init__(self, db):
        """
        Initialize tracker with database connection.

        Args:
            db: Database interface with execute_query method
        """
        self.db = db
        self._ensure_tables()

        # Local cache for current game session
        self._current_game_type: Optional[str] = None
        self._current_level: Optional[int] = None
        self._session_visited: Set[Tuple[int, int]] = set()
        self._session_actions: Dict[int, int] = {}  # action -> count

    def _ensure_tables(self):
        """Ensure exploration tables exist."""
        try:
            # Check if table exists
            result = self.db.execute_query("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='network_exploration_map'
            """)

            if not result:
                # Create tables
                self.db.execute_query("""
                    CREATE TABLE IF NOT EXISTS network_exploration_map (
                        exploration_id TEXT PRIMARY KEY,
                        game_type TEXT NOT NULL,
                        level_number INTEGER NOT NULL,
                        region_x INTEGER NOT NULL,
                        region_y INTEGER NOT NULL,
                        times_visited INTEGER DEFAULT 1,
                        unique_agents INTEGER DEFAULT 1,
                        last_visitor_id TEXT,
                        objects_found TEXT,
                        interactions_tried TEXT,
                        score_changes_here INTEGER DEFAULT 0,
                        deaths_here INTEGER DEFAULT 0,
                        novelty_score REAL DEFAULT 1.0,
                        productivity_score REAL DEFAULT 0.0,
                        danger_score REAL DEFAULT 0.0,
                        first_explored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_explored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(game_type, level_number, region_x, region_y)
                    )
                """)

                self.db.execute_query("""
                    CREATE TABLE IF NOT EXISTS network_action_coverage (
                        coverage_id TEXT PRIMARY KEY,
                        game_type TEXT NOT NULL,
                        level_number INTEGER NOT NULL,
                        action_number INTEGER NOT NULL,
                        times_used INTEGER DEFAULT 1,
                        unique_agents INTEGER DEFAULT 1,
                        score_increases INTEGER DEFAULT 0,
                        score_decreases INTEGER DEFAULT 0,
                        no_change INTEGER DEFAULT 0,
                        caused_death INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        avg_score_change REAL DEFAULT 0.0,
                        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(game_type, level_number, action_number)
                    )
                """)

                # Create indexes
                self.db.execute_query("""
                    CREATE INDEX IF NOT EXISTS idx_exploration_map_game_level
                    ON network_exploration_map(game_type, level_number)
                """)
                self.db.execute_query("""
                    CREATE INDEX IF NOT EXISTS idx_action_coverage_game_level
                    ON network_action_coverage(game_type, level_number)
                """)

                logger.info("[EXPLORATION] Created network_exploration_map tables")
        except Exception as e:
            logger.debug(f"[EXPLORATION] Table check/create failed: {e}")

    def _position_to_region(
        self,
        x: int,
        y: int,
        frame_width: int,
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Convert pixel position to grid region.

        Args:
            x, y: Pixel coordinates
            frame_width, frame_height: Frame dimensions

        Returns:
            (region_x, region_y) tuple
        """
        region_x = min(self.GRID_SIZE - 1, max(0, int(x * self.GRID_SIZE / max(1, frame_width))))
        region_y = min(self.GRID_SIZE - 1, max(0, int(y * self.GRID_SIZE / max(1, frame_height))))
        return (region_x, region_y)

    # =========================================================================
    # QUERY METHODS: Get network's collective exploration knowledge
    # =========================================================================

    def get_network_exploration_map(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Get the network's collective exploration map for a level.

        This is the key method - returns what the NETWORK knows about this level
        from all previous agents' explorations.

        Args:
            game_type: Game type (e.g., 'ls20')
            level: Level number

        Returns:
            Dict with:
            - explored_regions: List of {x, y, visits, productivity, danger}
            - unexplored_regions: List of {x, y} regions never visited
            - coverage_percent: How much of map has been explored
            - hotspots: High-productivity regions
            - danger_zones: High-danger regions
            - recommended_exploration: Best unexplored regions to try
        """
        result = {
            'explored_regions': [],
            'unexplored_regions': [],
            'coverage_percent': 0.0,
            'hotspots': [],
            'danger_zones': [],
            'recommended_exploration': [],
            'total_network_visits': 0,
            'unique_agents_explored': 0
        }

        try:
            # Get all explored regions
            rows = self.db.execute_query("""
                SELECT region_x, region_y, times_visited, unique_agents,
                       novelty_score, productivity_score, danger_score,
                       objects_found, score_changes_here, deaths_here
                FROM network_exploration_map
                WHERE game_type = ? AND level_number = ?
                ORDER BY novelty_score DESC
            """, (game_type, level))

            explored_set = set()
            total_visits = 0
            max_agents = 0

            for row in (rows or []):
                rx, ry = row['region_x'], row['region_y']
                explored_set.add((rx, ry))
                total_visits += row['times_visited']
                max_agents = max(max_agents, row['unique_agents'])

                region_info = {
                    'x': rx,
                    'y': ry,
                    'visits': row['times_visited'],
                    'agents': row['unique_agents'],
                    'novelty': round(row['novelty_score'], 2),
                    'productivity': round(row['productivity_score'], 2),
                    'danger': round(row['danger_score'], 2),
                    'score_changes': row['score_changes_here'],
                    'deaths': row['deaths_here']
                }

                result['explored_regions'].append(region_info)

                # Categorize
                if row['productivity_score'] > 0.5:
                    result['hotspots'].append(region_info)
                if row['danger_score'] > 0.5:
                    result['danger_zones'].append(region_info)

            result['total_network_visits'] = total_visits
            result['unique_agents_explored'] = max_agents

            # Find unexplored regions
            all_regions = {(x, y) for x in range(self.GRID_SIZE) for y in range(self.GRID_SIZE)}
            unexplored = all_regions - explored_set

            result['unexplored_regions'] = [{'x': x, 'y': y} for x, y in unexplored]
            result['coverage_percent'] = round(len(explored_set) / len(all_regions) * 100, 1)

            # Recommend exploration targets (unexplored + adjacent to productive)
            recommended = []
            for ux, uy in unexplored:
                # Check if adjacent to any productive region
                adjacent_productive = False
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = ux + dx, uy + dy
                    if (nx, ny) in explored_set:
                        # Check if adjacent region was productive
                        for region in result['explored_regions']:
                            if region['x'] == nx and region['y'] == ny:
                                if region['productivity'] > 0.3:
                                    adjacent_productive = True
                                    break

                priority = 2 if adjacent_productive else 1
                recommended.append({'x': ux, 'y': uy, 'priority': priority})

            # Sort by priority (higher first)
            recommended.sort(key=lambda r: r['priority'], reverse=True)
            result['recommended_exploration'] = recommended[:10]  # Top 10

        except Exception as e:
            logger.debug(f"[EXPLORATION] Query failed: {e}")

        return result

    def get_network_action_coverage(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Get the network's action usage statistics for a level.

        Returns what actions have been tried, how often, and their outcomes.

        Args:
            game_type: Game type
            level: Level number

        Returns:
            Dict with:
            - action_stats: {action: {uses, success_rate, avg_score_change}}
            - untried_actions: Actions with <3 uses
            - best_actions: Actions with highest success rate
            - dangerous_actions: Actions that caused deaths
        """
        result = {
            'action_stats': {},
            'untried_actions': [],
            'underexplored_actions': [],
            'best_actions': [],
            'dangerous_actions': [],
            'total_action_attempts': 0
        }

        try:
            rows = self.db.execute_query("""
                SELECT action_number, times_used, unique_agents,
                       score_increases, score_decreases, no_change,
                       caused_death, success_rate, avg_score_change
                FROM network_action_coverage
                WHERE game_type = ? AND level_number = ?
            """, (game_type, level))

            tried_actions = set()

            for row in (rows or []):
                action = row['action_number']
                tried_actions.add(action)
                result['total_action_attempts'] += row['times_used']

                stats = {
                    'uses': row['times_used'],
                    'agents': row['unique_agents'],
                    'success_rate': round(row['success_rate'], 2),
                    'avg_score_change': round(row['avg_score_change'], 2),
                    'score_increases': row['score_increases'],
                    'score_decreases': row['score_decreases'],
                    'deaths': row['caused_death']
                }
                result['action_stats'][action] = stats

                # Categorize
                if row['times_used'] < 3:
                    result['underexplored_actions'].append(action)
                if row['success_rate'] > 0.3 and row['times_used'] >= 3:
                    result['best_actions'].append((action, row['success_rate']))
                if row['caused_death'] > 0:
                    result['dangerous_actions'].append((action, row['caused_death']))

            # Find completely untried actions (1-7)
            all_actions = set(range(1, 8))
            result['untried_actions'] = list(all_actions - tried_actions)

            # Sort best actions by success rate
            result['best_actions'].sort(key=lambda x: x[1], reverse=True)
            result['best_actions'] = [a[0] for a in result['best_actions'][:3]]

        except Exception as e:
            logger.debug(f"[EXPLORATION] Action coverage query failed: {e}")

        return result

    def get_exploration_context_for_reasoning(
        self,
        game_type: str,
        level: int,
        current_position: Optional[Tuple[int, int]] = None,
        frame_width: int = 64,
        frame_height: int = 64
    ) -> Dict[str, Any]:
        """
        Get complete exploration context for the reasoning payload.

        This is the main integration point - returns everything an agent needs
        to make exploration-aware decisions.

        Args:
            game_type: Current game type
            level: Current level
            current_position: Agent's current (x, y) position
            frame_width, frame_height: Frame dimensions

        Returns:
            Dict suitable for inclusion in reasoning payload
        """
        # Get network maps
        exploration_map = self.get_network_exploration_map(game_type, level)
        action_coverage = self.get_network_action_coverage(game_type, level)

        context = {
            'network_exploration': {
                'coverage_percent': exploration_map['coverage_percent'],
                'total_visits': exploration_map['total_network_visits'],
                'unique_explorers': exploration_map['unique_agents_explored'],
                'unexplored_count': len(exploration_map['unexplored_regions']),
                'hotspot_count': len(exploration_map['hotspots']),
                'danger_zone_count': len(exploration_map['danger_zones']),
            },
            'exploration_recommendations': {
                'unexplored_regions': exploration_map['recommended_exploration'][:5],
                'untried_actions': action_coverage['untried_actions'],
                'underexplored_actions': action_coverage['underexplored_actions'],
                'best_actions': action_coverage['best_actions'],
            },
            'current_region': None,
            'current_region_known': False,
            'suggested_direction': None
        }

        # If we have current position, determine which region we're in
        if current_position:
            cx, cy = current_position
            region = self._position_to_region(cx, cy, frame_width, frame_height)
            context['current_region'] = {'x': region[0], 'y': region[1]}

            # Check if current region is known
            for explored in exploration_map['explored_regions']:
                if explored['x'] == region[0] and explored['y'] == region[1]:
                    context['current_region_known'] = True
                    context['current_region_info'] = {
                        'visits': explored['visits'],
                        'productivity': explored['productivity'],
                        'danger': explored['danger']
                    }
                    break

            # Suggest direction toward nearest unexplored region
            if exploration_map['recommended_exploration']:
                best_target = exploration_map['recommended_exploration'][0]
                tx, ty = best_target['x'], best_target['y']
                rx, ry = region

                # Determine direction
                if abs(tx - rx) >= abs(ty - ry):
                    context['suggested_direction'] = 'right' if tx > rx else 'left'
                else:
                    context['suggested_direction'] = 'down' if ty > ry else 'up'

        return context

    # =========================================================================
    # SAVE METHODS: Record agent's exploration for future agents
    # =========================================================================

    def record_position_visit(
        self,
        game_type: str,
        level: int,
        agent_id: str,
        x: int,
        y: int,
        frame_width: int,
        frame_height: int,
        score_changed: bool = False,
        objects_at_position: Optional[List[Dict]] = None,
        caused_death: bool = False
    ):
        """
        Record that an agent visited a position.

        Updates the network's collective exploration map.

        Args:
            game_type: Game type
            level: Level number
            agent_id: Agent that visited
            x, y: Position coordinates
            frame_width, frame_height: Frame dimensions
            score_changed: Whether score changed at this position
            objects_at_position: Objects found here
            caused_death: Whether visiting here caused death
        """
        region = self._position_to_region(x, y, frame_width, frame_height)
        rx, ry = region

        # Track in session cache to count unique visits
        session_key = (game_type, level)
        if session_key != (self._current_game_type, self._current_level):
            self._current_game_type = game_type
            self._current_level = level
            self._session_visited = set()
            self._session_actions = {}

        is_new_region_this_session = region not in self._session_visited
        self._session_visited.add(region)

        try:
            # Check if region exists
            existing = self.db.execute_query("""
                SELECT exploration_id, times_visited, unique_agents,
                       score_changes_here, deaths_here, novelty_score,
                       productivity_score, danger_score, objects_found
                FROM network_exploration_map
                WHERE game_type = ? AND level_number = ?
                  AND region_x = ? AND region_y = ?
            """, (game_type, level, rx, ry))

            if existing:
                row = existing[0]
                new_visits = row['times_visited'] + 1
                new_agents = row['unique_agents'] + (1 if is_new_region_this_session else 0)
                new_score_changes = row['score_changes_here'] + (1 if score_changed else 0)
                new_deaths = row['deaths_here'] + (1 if caused_death else 0)

                # Update novelty (decays with visits)
                new_novelty = max(0.0, 1.0 - (new_visits / 20.0))

                # Update productivity (based on score changes)
                new_productivity = new_score_changes / max(1, new_visits)

                # Update danger (based on deaths)
                new_danger = new_deaths / max(1, new_visits)

                # Merge objects found
                old_objects = json.loads(row['objects_found'] or '[]')
                if objects_at_position:
                    for obj in objects_at_position:
                        if obj not in old_objects:
                            old_objects.append(obj)

                self.db.execute_query("""
                    UPDATE network_exploration_map
                    SET times_visited = ?,
                        unique_agents = ?,
                        last_visitor_id = ?,
                        score_changes_here = ?,
                        deaths_here = ?,
                        novelty_score = ?,
                        productivity_score = ?,
                        danger_score = ?,
                        objects_found = ?,
                        last_explored_at = CURRENT_TIMESTAMP
                    WHERE exploration_id = ?
                """, (
                    new_visits, new_agents, agent_id,
                    new_score_changes, new_deaths,
                    new_novelty, new_productivity, new_danger,
                    json.dumps(old_objects[:20]),  # Limit size
                    row['exploration_id']
                ))
            else:
                # Insert new region
                self.db.execute_query("""
                    INSERT INTO network_exploration_map
                    (exploration_id, game_type, level_number, region_x, region_y,
                     times_visited, unique_agents, last_visitor_id,
                     objects_found, score_changes_here, deaths_here,
                     novelty_score, productivity_score, danger_score)
                    VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?, 0.95, ?, ?)
                """, (
                    str(uuid.uuid4()), game_type, level, rx, ry, agent_id,
                    json.dumps(objects_at_position or []),
                    1 if score_changed else 0,
                    1 if caused_death else 0,
                    1.0 if score_changed else 0.0,
                    1.0 if caused_death else 0.0
                ))

        except Exception as e:
            logger.debug(f"[EXPLORATION] Record visit failed: {e}")

    def record_action_use(
        self,
        game_type: str,
        level: int,
        agent_id: str,
        action: int,
        score_before: int,
        score_after: int,
        caused_death: bool = False
    ):
        """
        Record that an agent used an action.

        Updates the network's action coverage statistics.

        Args:
            game_type: Game type
            level: Level number
            agent_id: Agent that used action
            action: Action number (1-7)
            score_before, score_after: Scores before/after action
            caused_death: Whether action caused death
        """
        if action < 1 or action > 7:
            return

        score_change = score_after - score_before

        try:
            existing = self.db.execute_query("""
                SELECT coverage_id, times_used, unique_agents,
                       score_increases, score_decreases, no_change,
                       caused_death, success_rate, avg_score_change
                FROM network_action_coverage
                WHERE game_type = ? AND level_number = ? AND action_number = ?
            """, (game_type, level, action))

            if existing:
                row = existing[0]
                new_uses = row['times_used'] + 1
                new_increases = row['score_increases'] + (1 if score_change > 0 else 0)
                new_decreases = row['score_decreases'] + (1 if score_change < 0 else 0)
                new_no_change = row['no_change'] + (1 if score_change == 0 else 0)
                new_deaths = row['caused_death'] + (1 if caused_death else 0)

                # Calculate new success rate (positive score changes)
                new_success_rate = new_increases / max(1, new_uses)

                # Calculate running average score change
                old_avg = row['avg_score_change']
                new_avg = (old_avg * row['times_used'] + score_change) / new_uses

                self.db.execute_query("""
                    UPDATE network_action_coverage
                    SET times_used = ?,
                        score_increases = ?,
                        score_decreases = ?,
                        no_change = ?,
                        caused_death = ?,
                        success_rate = ?,
                        avg_score_change = ?,
                        last_used_at = CURRENT_TIMESTAMP
                    WHERE coverage_id = ?
                """, (
                    new_uses, new_increases, new_decreases, new_no_change,
                    new_deaths, new_success_rate, new_avg, row['coverage_id']
                ))
            else:
                # Insert new action record
                success_rate = 1.0 if score_change > 0 else 0.0
                self.db.execute_query("""
                    INSERT INTO network_action_coverage
                    (coverage_id, game_type, level_number, action_number,
                     times_used, unique_agents, score_increases, score_decreases,
                     no_change, caused_death, success_rate, avg_score_change)
                    VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), game_type, level, action,
                    1 if score_change > 0 else 0,
                    1 if score_change < 0 else 0,
                    1 if score_change == 0 else 0,
                    1 if caused_death else 0,
                    success_rate, float(score_change)
                ))

        except Exception as e:
            logger.debug(f"[EXPLORATION] Record action failed: {e}")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_exploration_priority_action(
        self,
        game_type: str,
        level: int,
        current_position: Optional[Tuple[int, int]],
        frame_width: int,
        frame_height: int
    ) -> Optional[int]:
        """
        Get the best action to take for exploration purposes.

        Prioritizes:
        1. Untried actions
        2. Actions that move toward unexplored regions
        3. Underexplored actions

        Args:
            game_type: Current game
            level: Current level
            current_position: Agent position
            frame_width, frame_height: Frame dimensions

        Returns:
            Recommended action number, or None
        """
        context = self.get_exploration_context_for_reasoning(
            game_type, level, current_position, frame_width, frame_height
        )

        # Priority 1: Completely untried actions
        if context['exploration_recommendations']['untried_actions']:
            return context['exploration_recommendations']['untried_actions'][0]

        # Priority 2: Action toward unexplored region
        direction = context.get('suggested_direction')
        if direction:
            direction_to_action = {
                'up': 1,
                'down': 2,
                'left': 3,
                'right': 4
            }
            if direction in direction_to_action:
                return direction_to_action[direction]

        # Priority 3: Underexplored actions
        if context['exploration_recommendations']['underexplored_actions']:
            return context['exploration_recommendations']['underexplored_actions'][0]

        return None

    def clear_level_exploration(self, game_type: str, level: int):
        """Clear exploration data for a specific level (use sparingly)."""
        try:
            self.db.execute_query("""
                DELETE FROM network_exploration_map
                WHERE game_type = ? AND level_number = ?
            """, (game_type, level))
            self.db.execute_query("""
                DELETE FROM network_action_coverage
                WHERE game_type = ? AND level_number = ?
            """, (game_type, level))
            logger.info(f"[EXPLORATION] Cleared exploration data for {game_type} L{level}")
        except Exception as e:
            logger.debug(f"[EXPLORATION] Clear failed: {e}")

    def save_session_exploration(
        self,
        game_type: str,
        level: int,
        agent_id: Optional[str] = None
    ) -> int:
        """
        Flush current session's exploration to the network database.

        Called before proactive reset to ensure all learned exploration
        data is persisted before the reset occurs.

        Args:
            game_type: Game type
            level: Level number
            agent_id: Agent saving the exploration

        Returns:
            Number of regions saved/updated
        """
        if not self._session_visited:
            return 0

        saved = 0
        try:
            for region in self._session_visited:
                rx, ry = region

                # Update or insert the region (simplified - just mark as visited)
                existing = self.db.execute_query("""
                    SELECT exploration_id, times_visited
                    FROM network_exploration_map
                    WHERE game_type = ? AND level_number = ?
                      AND region_x = ? AND region_y = ?
                """, (game_type, level, rx, ry))

                if existing:
                    # Already exists - increment visit count
                    self.db.execute_query("""
                        UPDATE network_exploration_map
                        SET times_visited = times_visited + 1,
                            last_visitor_id = ?,
                            last_explored_at = CURRENT_TIMESTAMP
                        WHERE exploration_id = ?
                    """, (agent_id, existing[0]['exploration_id']))
                else:
                    # New region - insert
                    self.db.execute_query("""
                        INSERT INTO network_exploration_map
                        (exploration_id, game_type, level_number, region_x, region_y,
                         times_visited, unique_agents, last_visitor_id,
                         novelty_score, productivity_score, danger_score)
                        VALUES (?, ?, ?, ?, ?, 1, 1, ?, 0.95, 0.0, 0.0)
                    """, (str(uuid.uuid4()), game_type, level, rx, ry, agent_id))

                saved += 1

            logger.info(f"[EXPLORATION] Saved {saved} explored regions for {game_type} L{level}")

        except Exception as e:
            logger.debug(f"[EXPLORATION] Session save failed: {e}")

        return saved
