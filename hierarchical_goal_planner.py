#!/usr/bin/env python3
"""
HIERARCHICAL GOAL PLANNING SYSTEM
==================================
Revolutionary multi-level strategic planning system for intelligent goal-setting and execution.

This system implements hierarchical planning with:
- Strategic, tactical, and operational goal levels
- Goal decomposition and dependency management
- Action sequence planning and execution
- Progress monitoring and adaptive replanning
- Resource allocation and constraint handling
"""

import os
import sys

# Disable Python bytecode generation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import json
import time
import logging
import sqlite3
import random
import math
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import uuid
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class GoalLevel(Enum):
    """Hierarchical levels of goals."""
    STRATEGIC = "strategic"      # High-level game objectives (win, maximize score)
    TACTICAL = "tactical"        # Medium-term objectives (explore area, find patterns)
    OPERATIONAL = "operational"  # Short-term objectives (execute specific action)

class GoalStatus(Enum):
    """Status of goal execution."""
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

class PlanningStrategy(Enum):
    """Planning algorithm strategies."""
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    BEST_FIRST = "best_first"
    A_STAR = "a_star"
    HIERARCHICAL = "hierarchical"

@dataclass
class GoalConstraint:
    """Constraint on goal execution."""
    constraint_type: str  # "time", "resource", "dependency", "condition"
    value: Any
    description: str

@dataclass
class ActionStep:
    """Single action step in a plan."""
    action: str
    coordinates: Optional[Tuple[int, int]]
    expected_outcome: str
    confidence: float
    estimated_time: float
    resources_required: Dict[str, float]

@dataclass
class Goal:
    """Hierarchical goal representation."""
    goal_id: str
    level: GoalLevel
    title: str
    description: str

    # Goal hierarchy
    parent_goal_id: Optional[str] = None
    sub_goal_ids: List[str] = field(default_factory=list)

    # Goal properties
    priority: float = 0.5  # 0.0 to 1.0
    urgency: float = 0.5   # 0.0 to 1.0
    complexity: float = 0.5  # 0.0 to 1.0

    # Execution state
    status: GoalStatus = GoalStatus.PLANNED
    progress: float = 0.0  # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Planning
    action_plan: List[ActionStep] = field(default_factory=list)
    constraints: List[GoalConstraint] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    # Metrics
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    success_probability: float = 0.5
    value_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary."""
        return asdict(self)

class PlanningContext:
    """Context information for planning."""

    def __init__(self):
        self.current_score: float = 0.0
        self.target_score: float = 8.0
        self.actions_taken: int = 0
        self.max_actions: int = 1500
        self.available_actions: List[int] = []
        self.game_state: str = "NOT_FINISHED"

        # Environmental context
        self.visual_features: List[Dict[str, Any]] = []
        self.coordinate_history: List[Tuple[int, int]] = []
        self.successful_patterns: List[Dict[str, Any]] = []

        # Resource constraints
        self.time_remaining: float = 1.0  # Normalized
        self.exploration_budget: float = 0.3
        self.exploitation_focus: float = 0.7

class GoalPlanner(ABC):
    """Abstract base class for goal planning algorithms."""

    @abstractmethod
    def create_plan(self, goal: Goal, context: PlanningContext) -> List[ActionStep]:
        """Create action plan for achieving the goal."""
        pass

    @abstractmethod
    def estimate_success_probability(self, goal: Goal, context: PlanningContext) -> float:
        """Estimate probability of goal success."""
        pass

class HierarchicalPlanner(GoalPlanner):
    """Hierarchical decomposition planner."""

    def create_plan(self, goal: Goal, context: PlanningContext) -> List[ActionStep]:
        """Create hierarchical action plan."""
        if goal.level == GoalLevel.STRATEGIC:
            return self._plan_strategic_goal(goal, context)
        elif goal.level == GoalLevel.TACTICAL:
            return self._plan_tactical_goal(goal, context)
        else:
            return self._plan_operational_goal(goal, context)

    def _plan_strategic_goal(self, goal: Goal, context: PlanningContext) -> List[ActionStep]:
        """Plan strategic-level goal (high-level game objectives)."""
        plan = []

        # Analyze current situation
        score_gap = context.target_score - context.current_score
        actions_remaining = context.max_actions - context.actions_taken

        if score_gap > 0 and actions_remaining > 0:
            # Plan exploration and exploitation phases
            exploration_actions = int(actions_remaining * context.exploration_budget)
            exploitation_actions = actions_remaining - exploration_actions

            # Exploration phase
            for i in range(exploration_actions):
                step = ActionStep(
                    action="ACTION6",  # Coordinate-based exploration
                    coordinates=self._suggest_exploration_coordinate(context),
                    expected_outcome="discover_patterns",
                    confidence=0.6,
                    estimated_time=1.0,
                    resources_required={"exploration_budget": 1.0 / exploration_actions}
                )
                plan.append(step)

            # Exploitation phase
            for i in range(exploitation_actions):
                step = ActionStep(
                    action="ACTION1",  # Conservative action
                    coordinates=None,
                    expected_outcome="incremental_progress",
                    confidence=0.8,
                    estimated_time=1.0,
                    resources_required={"exploitation_focus": 1.0 / exploitation_actions}
                )
                plan.append(step)

        return plan

    def _plan_tactical_goal(self, goal: Goal, context: PlanningContext) -> List[ActionStep]:
        """Plan tactical-level goal (medium-term objectives)."""
        plan = []

        # Pattern-based tactical planning
        if "explore_quadrant" in goal.description:
            # Systematic quadrant exploration
            quadrant_coords = self._get_quadrant_coordinates(goal.description)
            for coord in quadrant_coords[:5]:  # Limit to 5 actions
                step = ActionStep(
                    action="ACTION6",
                    coordinates=coord,
                    expected_outcome="quadrant_coverage",
                    confidence=0.7,
                    estimated_time=1.0,
                    resources_required={"exploration_budget": 0.2}
                )
                plan.append(step)

        elif "pattern_search" in goal.description:
            # Pattern discovery actions
            pattern_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
            for action in pattern_actions:
                step = ActionStep(
                    action=action,
                    coordinates=None,
                    expected_outcome="pattern_discovery",
                    confidence=0.6,
                    estimated_time=1.0,
                    resources_required={"pattern_analysis": 0.25}
                )
                plan.append(step)

        return plan

    def _plan_operational_goal(self, goal: Goal, context: PlanningContext) -> List[ActionStep]:
        """Plan operational-level goal (immediate actions)."""
        plan = []

        # Direct action execution
        if "execute_action" in goal.description:
            action_name = self._extract_action_from_description(goal.description)
            coordinates = self._extract_coordinates_from_description(goal.description)

            step = ActionStep(
                action=action_name,
                coordinates=coordinates,
                expected_outcome="direct_execution",
                confidence=0.9,
                estimated_time=1.0,
                resources_required={"action_budget": 1.0}
            )
            plan.append(step)

        return plan

    def _suggest_exploration_coordinate(self, context: PlanningContext) -> Tuple[int, int]:
        """Suggest coordinate for exploration."""
        # Avoid recently used coordinates
        used_coords = set(context.coordinate_history[-20:])

        # Generate diverse coordinates
        for _ in range(10):
            x = random.randint(0, 63)
            y = random.randint(0, 63)
            if (x, y) not in used_coords:
                return (x, y)

        # Fallback to random coordinate
        return (random.randint(0, 63), random.randint(0, 63))

    def _get_quadrant_coordinates(self, description: str) -> List[Tuple[int, int]]:
        """Get coordinates for quadrant exploration."""
        # Parse quadrant from description
        if "upper_left" in description:
            return [(16, 16), (8, 8), (24, 8), (8, 24), (24, 24)]
        elif "upper_right" in description:
            return [(48, 16), (40, 8), (56, 8), (40, 24), (56, 24)]
        elif "lower_left" in description:
            return [(16, 48), (8, 40), (24, 40), (8, 56), (24, 56)]
        elif "lower_right" in description:
            return [(48, 48), (40, 40), (56, 40), (40, 56), (56, 56)]
        else:
            return [(32, 32), (16, 16), (48, 16), (16, 48), (48, 48)]

    def _extract_action_from_description(self, description: str) -> str:
        """Extract action name from goal description."""
        for action in ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]:
            if action in description:
                return action
        return "ACTION1"  # Default

    def _extract_coordinates_from_description(self, description: str) -> Optional[Tuple[int, int]]:
        """Extract coordinates from goal description."""
        import re
        coord_match = re.search(r'\((\d+),\s*(\d+)\)', description)
        if coord_match:
            return (int(coord_match.group(1)), int(coord_match.group(2)))
        return None

    def estimate_success_probability(self, goal: Goal, context: PlanningContext) -> float:
        """Estimate probability of goal success."""
        base_probability = 0.5

        # Adjust based on goal level
        if goal.level == GoalLevel.STRATEGIC:
            base_probability = 0.3  # More ambitious
        elif goal.level == GoalLevel.TACTICAL:
            base_probability = 0.6  # Moderate difficulty
        else:
            base_probability = 0.8  # More achievable

        # Adjust based on context
        time_factor = context.time_remaining
        score_factor = min(context.current_score / context.target_score, 1.0)

        # Combine factors
        probability = base_probability * (0.4 + 0.3 * time_factor + 0.3 * score_factor)

        return min(max(probability, 0.0), 1.0)

class HierarchicalGoalPlanningSystem:
    """Revolutionary hierarchical goal planning and execution system."""

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize the hierarchical goal planning system."""
        self.db_path = db_path

        # Goal management
        self.goals: Dict[str, Goal] = {}
        self.active_goals: List[str] = []
        self.goal_hierarchy: Dict[str, List[str]] = {}  # parent_id -> [child_ids]

        # Planning components
        self.planners: Dict[PlanningStrategy, GoalPlanner] = {
            PlanningStrategy.HIERARCHICAL: HierarchicalPlanner()
        }
        self.current_strategy = PlanningStrategy.HIERARCHICAL

        # Execution state
        self.current_context = PlanningContext()
        self.execution_queue: deque = deque()
        self.completed_goals: List[str] = []

        # Performance tracking
        self.goal_success_rate = 0.0
        self.average_goal_duration = 0.0
        self.planning_efficiency = 0.0

        # Adaptive parameters
        self.exploration_factor = 0.3
        self.risk_tolerance = 0.5
        self.planning_horizon = 10  # Number of actions to plan ahead

        logger.info("HierarchicalGoalPlanningSystem initialized with intelligent planning capabilities")

    def create_strategic_goal(self, title: str, description: str, target_score: float,
                            max_actions: int, priority: float = 0.8) -> str:
        """Create a high-level strategic goal."""
        goal_id = str(uuid.uuid4())

        goal = Goal(
            goal_id=goal_id,
            level=GoalLevel.STRATEGIC,
            title=title,
            description=description,
            priority=priority,
            urgency=0.7,
            complexity=0.8,
            success_criteria=[
                f"achieve_score_{target_score}",
                f"within_actions_{max_actions}",
                "efficient_resource_usage"
            ],
            estimated_duration=max_actions * 0.8,
            value_estimate=target_score
        )

        self.goals[goal_id] = goal
        self.active_goals.append(goal_id)

        # Create initial sub-goals
        self._decompose_strategic_goal(goal)

        logger.info(f"Created strategic goal: {title} (ID: {goal_id})")
        return goal_id

    def create_tactical_goal(self, title: str, description: str, parent_goal_id: Optional[str] = None,
                           priority: float = 0.6) -> str:
        """Create a medium-term tactical goal."""
        goal_id = str(uuid.uuid4())

        goal = Goal(
            goal_id=goal_id,
            level=GoalLevel.TACTICAL,
            title=title,
            description=description,
            parent_goal_id=parent_goal_id,
            priority=priority,
            urgency=0.5,
            complexity=0.6,
            estimated_duration=5.0,
            value_estimate=priority * 2.0
        )

        self.goals[goal_id] = goal
        self.active_goals.append(goal_id)

        # Link to parent goal
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].sub_goal_ids.append(goal_id)
            if parent_goal_id not in self.goal_hierarchy:
                self.goal_hierarchy[parent_goal_id] = []
            self.goal_hierarchy[parent_goal_id].append(goal_id)

        logger.info(f"Created tactical goal: {title} (ID: {goal_id})")
        return goal_id

    def create_operational_goal(self, title: str, description: str, parent_goal_id: Optional[str] = None,
                              action: str = "ACTION1", coordinates: Optional[Tuple[int, int]] = None) -> str:
        """Create an immediate operational goal."""
        goal_id = str(uuid.uuid4())

        goal = Goal(
            goal_id=goal_id,
            level=GoalLevel.OPERATIONAL,
            title=title,
            description=description,
            parent_goal_id=parent_goal_id,
            priority=0.4,
            urgency=0.8,
            complexity=0.2,
            estimated_duration=1.0,
            value_estimate=0.5
        )

        # Create immediate action plan
        action_step = ActionStep(
            action=action,
            coordinates=coordinates,
            expected_outcome="immediate_execution",
            confidence=0.9,
            estimated_time=1.0,
            resources_required={"action_budget": 1.0}
        )
        goal.action_plan = [action_step]

        self.goals[goal_id] = goal
        self.active_goals.append(goal_id)

        # Link to parent goal
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].sub_goal_ids.append(goal_id)
            if parent_goal_id not in self.goal_hierarchy:
                self.goal_hierarchy[parent_goal_id] = []
            self.goal_hierarchy[parent_goal_id].append(goal_id)

        logger.info(f"Created operational goal: {title} (ID: {goal_id})")
        return goal_id

    def _decompose_strategic_goal(self, strategic_goal: Goal):
        """Decompose strategic goal into tactical sub-goals."""
        # Exploration phase tactical goals
        exploration_goal_id = self.create_tactical_goal(
            "Strategic Exploration",
            "explore_quadrant systematic pattern discovery",
            strategic_goal.goal_id,
            priority=0.7
        )

        # Pattern recognition tactical goals
        pattern_goal_id = self.create_tactical_goal(
            "Pattern Recognition",
            "pattern_search visual feature analysis",
            strategic_goal.goal_id,
            priority=0.8
        )

        # Exploitation tactical goals
        exploit_goal_id = self.create_tactical_goal(
            "Strategic Exploitation",
            "exploit_discovered_patterns maximize scoring",
            strategic_goal.goal_id,
            priority=0.9
        )

    def update_context(self, score: float, available_actions: List[int], actions_taken: int,
                      max_actions: int, visual_features: List[Dict[str, Any]] = None):
        """Update planning context with current game state."""
        self.current_context.current_score = score
        self.current_context.available_actions = available_actions
        self.current_context.actions_taken = actions_taken
        self.current_context.max_actions = max_actions
        self.current_context.time_remaining = max(0.0, (max_actions - actions_taken) / max_actions)

        if visual_features:
            self.current_context.visual_features = visual_features

        # Update adaptive parameters based on progress
        progress_ratio = actions_taken / max_actions
        if progress_ratio > 0.7:
            self.current_context.exploration_budget = 0.1  # Reduce exploration
            self.current_context.exploitation_focus = 0.9   # Increase exploitation
        elif progress_ratio > 0.4:
            self.current_context.exploration_budget = 0.2
            self.current_context.exploitation_focus = 0.8

    def get_next_action_recommendation(self) -> Dict[str, Any]:
        """Get next action recommendation based on current goal hierarchy."""
        # Select highest priority active goal
        if not self.active_goals:
            return self._create_default_recommendation()

        # Find the highest priority operational goal
        operational_goals = [
            goal_id for goal_id in self.active_goals
            if self.goals[goal_id].level == GoalLevel.OPERATIONAL and
               self.goals[goal_id].status == GoalStatus.PLANNED
        ]

        if operational_goals:
            # Execute planned operational goal
            goal_id = max(operational_goals, key=lambda g: self.goals[g].priority)
            return self._execute_operational_goal(goal_id)

        # Create new operational goal from tactical goals
        tactical_goals = [
            goal_id for goal_id in self.active_goals
            if self.goals[goal_id].level == GoalLevel.TACTICAL and
               self.goals[goal_id].status == GoalStatus.PLANNED
        ]

        if tactical_goals:
            # Plan and execute tactical goal
            goal_id = max(tactical_goals, key=lambda g: self.goals[g].priority)
            return self._plan_and_execute_tactical_goal(goal_id)

        # Fallback: create new tactical goals from strategic goals
        strategic_goals = [
            goal_id for goal_id in self.active_goals
            if self.goals[goal_id].level == GoalLevel.STRATEGIC
        ]

        if strategic_goals:
            goal_id = strategic_goals[0]
            return self._advance_strategic_goal(goal_id)

        return self._create_default_recommendation()

    def _execute_operational_goal(self, goal_id: str) -> Dict[str, Any]:
        """Execute an operational goal."""
        goal = self.goals[goal_id]

        if goal.action_plan:
            action_step = goal.action_plan[0]

            # Mark goal as active
            goal.status = GoalStatus.ACTIVE
            goal.started_at = time.time()

            recommendation = {
                "recommended_action": action_step.action,
                "coordinates": action_step.coordinates,
                "confidence": action_step.confidence,
                "goal_info": {
                    "goal_id": goal_id,
                    "goal_title": goal.title,
                    "goal_level": goal.level.value,
                    "expected_outcome": action_step.expected_outcome
                },
                "planning_source": "operational_goal_execution"
            }

            logger.info(f"Executing operational goal: {goal.title} -> {action_step.action}")
            return recommendation

        return self._create_default_recommendation()

    def _plan_and_execute_tactical_goal(self, goal_id: str) -> Dict[str, Any]:
        """Plan and execute a tactical goal."""
        goal = self.goals[goal_id]

        # Create action plan if not exists
        if not goal.action_plan:
            planner = self.planners[self.current_strategy]
            goal.action_plan = planner.create_plan(goal, self.current_context)
            goal.success_probability = planner.estimate_success_probability(goal, self.current_context)

        if goal.action_plan:
            # Create operational sub-goal for first action
            action_step = goal.action_plan[0]

            operational_id = self.create_operational_goal(
                f"Execute {action_step.action}",
                f"execute_action {action_step.action} coordinates {action_step.coordinates}",
                parent_goal_id=goal_id,
                action=action_step.action,
                coordinates=action_step.coordinates
            )

            # Execute the new operational goal
            return self._execute_operational_goal(operational_id)

        return self._create_default_recommendation()

    def _advance_strategic_goal(self, goal_id: str) -> Dict[str, Any]:
        """Advance strategic goal by creating new tactical sub-goals."""
        goal = self.goals[goal_id]

        # Create adaptive tactical goal based on current context
        if self.current_context.time_remaining > 0.5:
            # Still have time for exploration
            tactical_id = self.create_tactical_goal(
                "Adaptive Exploration",
                "explore_quadrant adaptive pattern discovery",
                parent_goal_id=goal_id,
                priority=0.7
            )
        else:
            # Focus on exploitation
            tactical_id = self.create_tactical_goal(
                "Final Exploitation",
                "exploit_patterns maximize final score",
                parent_goal_id=goal_id,
                priority=0.9
            )

        # Plan and execute the new tactical goal
        return self._plan_and_execute_tactical_goal(tactical_id)

    def _create_default_recommendation(self) -> Dict[str, Any]:
        """Create default recommendation when no goals are available."""
        # Create emergency strategic goal
        strategic_id = self.create_strategic_goal(
            "Emergency Strategy",
            "maximize score with remaining actions",
            target_score=self.current_context.target_score,
            max_actions=self.current_context.max_actions - self.current_context.actions_taken,
            priority=1.0
        )

        return {
            "recommended_action": "ACTION1",
            "coordinates": None,
            "confidence": 0.5,
            "goal_info": {
                "goal_id": strategic_id,
                "goal_title": "Emergency Strategy",
                "goal_level": "strategic",
                "expected_outcome": "emergency_action"
            },
            "planning_source": "emergency_fallback"
        }

    def record_action_outcome(self, goal_id: str, action: str, coordinates: Optional[Tuple[int, int]],
                            score_change: float, success: bool):
        """Record outcome of executed action for goal learning."""
        if goal_id not in self.goals:
            return

        goal = self.goals[goal_id]

        # Update goal progress
        if success:
            goal.progress += 1.0 / len(goal.action_plan) if goal.action_plan else 1.0
            goal.progress = min(goal.progress, 1.0)

        # Check if goal is completed
        if goal.progress >= 1.0 or (goal.level == GoalLevel.OPERATIONAL and success):
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = time.time()
            goal.actual_duration = goal.completed_at - (goal.started_at or goal.created_at)

            self._complete_goal(goal_id)
            logger.info(f"Goal completed: {goal.title}")

        elif not success and goal.level == GoalLevel.OPERATIONAL:
            goal.status = GoalStatus.FAILED
            self._handle_goal_failure(goal_id)
            logger.warning(f"Goal failed: {goal.title}")

        # Store outcome for learning
        self._store_goal_outcome(goal_id, action, coordinates, score_change, success)

    def _complete_goal(self, goal_id: str):
        """Handle goal completion and update parent goals."""
        goal = self.goals[goal_id]

        # Remove from active goals
        if goal_id in self.active_goals:
            self.active_goals.remove(goal_id)

        # Add to completed goals
        self.completed_goals.append(goal_id)

        # Update parent goal progress
        if goal.parent_goal_id and goal.parent_goal_id in self.goals:
            parent_goal = self.goals[goal.parent_goal_id]
            parent_progress = sum(
                self.goals[sub_id].progress
                for sub_id in parent_goal.sub_goal_ids
                if sub_id in self.goals
            ) / len(parent_goal.sub_goal_ids) if parent_goal.sub_goal_ids else 0.0

            parent_goal.progress = parent_progress

            # Check if parent goal is also completed
            if parent_goal.progress >= 1.0:
                self._complete_goal(goal.parent_goal_id)

    def _handle_goal_failure(self, goal_id: str):
        """Handle goal failure and create alternative plans."""
        goal = self.goals[goal_id]

        # Remove from active goals
        if goal_id in self.active_goals:
            self.active_goals.remove(goal_id)

        # Create alternative operational goal if parent exists
        if goal.parent_goal_id and goal.parent_goal_id in self.goals:
            parent_goal = self.goals[goal.parent_goal_id]

            # Create new operational goal with different approach
            alternative_id = self.create_operational_goal(
                f"Alternative to {goal.title}",
                f"execute_action ACTION{random.randint(1,4)} alternative approach",
                parent_goal_id=goal.parent_goal_id,
                action=f"ACTION{random.randint(1,4)}"
            )

            logger.info(f"Created alternative goal: {alternative_id}")

    def get_goal_hierarchy_status(self) -> Dict[str, Any]:
        """Get current status of goal hierarchy."""
        active_count = len(self.active_goals)
        completed_count = len(self.completed_goals)
        total_goals = len(self.goals)

        # Calculate success rate
        if completed_count > 0:
            successful_goals = sum(
                1 for goal_id in self.completed_goals
                if self.goals[goal_id].status == GoalStatus.COMPLETED
            )
            self.goal_success_rate = successful_goals / completed_count

        # Calculate average duration
        completed_goals_data = [
            self.goals[goal_id] for goal_id in self.completed_goals
            if self.goals[goal_id].actual_duration > 0
        ]

        if completed_goals_data:
            self.average_goal_duration = sum(g.actual_duration for g in completed_goals_data) / len(completed_goals_data)

        return {
            "goal_hierarchy_active": True,
            "total_goals": total_goals,
            "active_goals": active_count,
            "completed_goals": completed_count,
            "success_rate": self.goal_success_rate,
            "average_duration": self.average_goal_duration,
            "current_strategy": self.current_strategy.value,
            "goal_breakdown": {
                "strategic": sum(1 for g in self.goals.values() if g.level == GoalLevel.STRATEGIC),
                "tactical": sum(1 for g in self.goals.values() if g.level == GoalLevel.TACTICAL),
                "operational": sum(1 for g in self.goals.values() if g.level == GoalLevel.OPERATIONAL)
            },
            "context": {
                "time_remaining": self.current_context.time_remaining,
                "exploration_budget": self.current_context.exploration_budget,
                "exploitation_focus": self.current_context.exploitation_focus
            }
        }

    def _store_goal_outcome(self, goal_id: str, action: str, coordinates: Optional[Tuple[int, int]],
                          score_change: float, success: bool):
        """Store goal outcome to database for learning."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_outcomes (
                    goal_id TEXT,
                    timestamp REAL,
                    action TEXT,
                    coordinates TEXT,
                    score_change REAL,
                    success INTEGER,
                    goal_level TEXT,
                    goal_priority REAL
                )
            """)

            goal = self.goals[goal_id]

            # Insert outcome
            cursor.execute("""
                INSERT INTO goal_outcomes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal_id,
                time.time(),
                action,
                json.dumps(coordinates) if coordinates else None,
                score_change,
                1 if success else 0,
                goal.level.value,
                goal.priority
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing goal outcome: {e}")

# Global instance
goal_planner = HierarchicalGoalPlanningSystem()

def initialize_goal_planning_session(target_score: float, max_actions: int) -> str:
    """Initialize goal planning for a new game session."""
    strategic_goal_id = goal_planner.create_strategic_goal(
        "Game Victory Strategy",
        f"achieve target score {target_score} within {max_actions} actions using intelligent planning",
        target_score=target_score,
        max_actions=max_actions,
        priority=1.0
    )

    logger.info(f"Goal planning session initialized with strategic goal: {strategic_goal_id}")
    return strategic_goal_id

def get_hierarchical_action_recommendation(score: float, available_actions: List[int],
                                         actions_taken: int, max_actions: int,
                                         visual_features: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get action recommendation from hierarchical goal planning system."""
    # Update context
    goal_planner.update_context(score, available_actions, actions_taken, max_actions, visual_features)

    # Get recommendation
    recommendation = goal_planner.get_next_action_recommendation()

    # Add planning status
    recommendation["planning_status"] = goal_planner.get_goal_hierarchy_status()

    return recommendation

def record_hierarchical_outcome(goal_id: str, action: str, coordinates: Optional[Tuple[int, int]],
                               score_change: float, success: bool):
    """Record outcome of hierarchical planning action."""
    goal_planner.record_action_outcome(goal_id, action, coordinates, score_change, success)

if __name__ == "__main__":
    # Test the hierarchical goal planning system
    print("=== HIERARCHICAL GOAL PLANNING SYSTEM TEST ===")

    # Initialize planning session
    strategic_id = initialize_goal_planning_session(target_score=8.0, max_actions=50)

    # Simulate game progression
    score = 0.0
    actions_taken = 0
    available_actions = [1, 2, 3, 4, 6]

    for action_num in range(1, 11):
        # Get recommendation
        recommendation = get_hierarchical_action_recommendation(
            score, available_actions, actions_taken, 50
        )

        print(f"\nAction {action_num}:")
        print(f"  Recommended: {recommendation['recommended_action']}")
        print(f"  Confidence: {recommendation['confidence']:.3f}")
        print(f"  Goal: {recommendation['goal_info']['goal_title']}")
        print(f"  Level: {recommendation['goal_info']['goal_level']}")

        # Simulate action outcome
        score_change = random.uniform(-0.1, 0.5)
        success = score_change > 0
        score += score_change
        actions_taken += 1

        # Record outcome
        record_hierarchical_outcome(
            recommendation['goal_info']['goal_id'],
            recommendation['recommended_action'],
            recommendation.get('coordinates'),
            score_change,
            success
        )

        print(f"  Outcome: {score_change:+.2f} ({'success' if success else 'failure'})")

    # Print final status
    status = goal_planner.get_goal_hierarchy_status()
    print(f"\nFinal Planning Status:")
    print(f"Total Goals: {status['total_goals']}")
    print(f"Active Goals: {status['active_goals']}")
    print(f"Completed Goals: {status['completed_goals']}")
    print(f"Success Rate: {status['success_rate']:.2f}")
    print(f"Goal Breakdown: {status['goal_breakdown']}")