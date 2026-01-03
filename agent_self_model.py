#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: MUST be before other imports

"""
Agent Self-Model System
=======================

Implements "I am this object" tracking for agents.
Identifies which objects/pixels agents control in each game/level.

This addresses the agent self-model requirement from operational philosophy.
"""

import json
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class AgentSelfModel:
    """
    Tracks which objects agents control in games.
    
    Builds a "self-model" for each agent by analyzing:
    - Which pixels/objects respond to agent actions
    - Correlation between actions and frame changes
    - Controlled vs environmental objects
    
    Network Knowledge Sharing:
    - Agents share "I am this object" discoveries to network_object_control_hypotheses
    - Other agents validate/refute these hypotheses during gameplay
    - Bayesian reputation scoring determines reliability
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize self-model system."""
        self.db = DatabaseInterface(db_path)
        self.db_path = db_path
        self._abstraction_engine = None
        self._abstraction_unavailable = False
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create agent_object_control and network hypothesis tables if needed."""
        # Individual agent control maps
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_object_control (
                agent_id TEXT,
                game_id TEXT,
                level_number INTEGER,
                controlled_objects TEXT,
                confidence REAL,
                learned_at TEXT,
                PRIMARY KEY (agent_id, game_id, level_number)
            )
        """)
        
        # Network-level "I am this object" hypotheses - shared across agents
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS network_object_control_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The hypothesis: "I control object at these coordinates"
                control_pattern TEXT NOT NULL,
                action_response_map TEXT NOT NULL,
                
                -- Discovery context
                discovered_by_agent TEXT NOT NULL,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                discovery_generation INTEGER DEFAULT 0,
                
                -- Validation tracking (Bayesian reputation)
                validation_attempts INTEGER DEFAULT 0,
                validation_successes INTEGER DEFAULT 0,
                validation_failures INTEGER DEFAULT 0,
                reliability_score REAL DEFAULT 0.5,
                
                -- Status
                is_active BOOLEAN DEFAULT TRUE,
                last_validated DATETIME,
                validated_by_win BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Index for fast lookup by game type
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_hypotheses_game 
            ON network_object_control_hypotheses(game_type, level_number, is_active)
        """)
        
        # ACTION5 behavior mapping - what does ACTION5 do in each game type?
        # This is crucial because ACTION5 is context-dependent (rotate, toggle, interact, etc.)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS action5_behavior_map (
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                behavior_type TEXT NOT NULL,
                affected_objects TEXT,
                effect_description TEXT,
                confidence REAL DEFAULT 0.5,
                discovery_count INTEGER DEFAULT 1,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (game_type, level_number)
            )
        """)
        
        # ACTION6 pseudo button behavior - what do clicks at specific regions do?
        # ACTION6 uses x,y coordinates (0-63 range) like a touchscreen
        # Clicking pseudo buttons often produces movement similar to ACTION1-4
        # We divide screen into regions and track what clicking each region does
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS pseudo_button_behavior (
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                region_x INTEGER NOT NULL,
                region_y INTEGER NOT NULL,
                
                -- What does clicking this region do?
                produces_action TEXT,
                movement_direction TEXT,
                affected_objects TEXT,
                effect_description TEXT,
                
                -- Confidence tracking
                confidence REAL DEFAULT 0.5,
                discovery_count INTEGER DEFAULT 1,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (game_type, level_number, region_x, region_y)
            )
        """)
        
        # Index for fast pseudo button lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_pseudo_button_game 
            ON pseudo_button_behavior(game_type, level_number)
        """)

        # =====================================================================
        # OBJECT SELECTION STATE (Added 2025-12-08)
        # =====================================================================
        # ACTION6 can do TWO things:
        # 1. Click on "buttons" -> triggers events (existing pseudo_button_behavior)
        # 2. Click on "objects" -> SELECTS that object for control by ACTION1-4
        #
        # This table tracks which objects are SELECTABLE (can become controlled)
        # vs which are just buttons. The currently selected object determines
        # what ACTION1-4 will move.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS object_selection_state (
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                object_color INTEGER NOT NULL,
                
                -- Object identification
                object_coordinates TEXT,           -- Last known "(x,y)" of selectable object
                object_signature TEXT,             -- Stable identifier for the object
                
                -- What kind of object is this?
                is_selectable BOOLEAN DEFAULT FALSE,    -- Can it be selected via ACTION6?
                is_moveable BOOLEAN DEFAULT FALSE,      -- Does it respond to ACTION1-4 when selected?
                is_button BOOLEAN DEFAULT FALSE,        -- Does clicking trigger an event instead?
                
                -- Selection mechanics
                selection_method TEXT DEFAULT 'action6_click',  -- How is it selected?
                control_actions TEXT,                   -- Which actions control it when selected (JSON list)
                
                -- Network learning
                confidence REAL DEFAULT 0.5,
                discovery_count INTEGER DEFAULT 1,
                discovered_by_agent TEXT,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (game_type, level_number, object_color)
            )
        """)
        
        # Add click behavior classification columns (migration for existing tables)
        click_behavior_columns = [
            ('click_behavior_type', 'TEXT DEFAULT "unknown"'),
            ('is_self_toggle', 'INTEGER DEFAULT 0'),
            ('is_trigger', 'INTEGER DEFAULT 0'),
            ('is_reference', 'INTEGER DEFAULT 0'),  # NEW: FT09-style reference objects
            ('movement_verified', 'INTEGER DEFAULT 0'),
            ('affects_objects', 'TEXT'),
            ('state_changes_observed', 'INTEGER DEFAULT 0'),
            ('movement_test_count', 'INTEGER DEFAULT 0'),
            # Shape-based generalization columns (2025-12-27)
            # Allows agents to learn "all horizontal bars are clickable" not just "color 9 is clickable"
            ('shape_signature', 'TEXT'),  # e.g., "horizontal_bar", "vertical_bar", "square", "blob"
            ('shape_width', 'INTEGER'),   # Bounding box width
            ('shape_height', 'INTEGER'),  # Bounding box height
            ('shape_density', 'REAL'),    # Fill density (cells / bbox_area)
        ]
        for col_name, col_type in click_behavior_columns:
            try:
                self.db.execute_query(f"ALTER TABLE object_selection_state ADD COLUMN {col_name} {col_type}")
            except:
                pass  # Column already exists
        
        # Index for fast selectable object lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_selection_game 
            ON object_selection_state(game_type, level_number, is_selectable)
        """)
        
        # Index for shape-based generalization (find all games where shape X is selectable)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_selection_shape 
            ON object_selection_state(game_type, shape_signature, is_selectable)
        """)
        
        # =====================================================================
        # CURRENT SELECTION TRACKING (per-session, not persisted long-term)
        # =====================================================================
        # Tracks what object is CURRENTLY selected during gameplay.
        # This is ephemeral - cleared each game session.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS current_selection_tracking (
                session_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Currently selected object
                selected_object_color INTEGER,
                selected_object_coords TEXT,        -- "(x,y)" when selected
                selection_action_index INTEGER,     -- Which action selected it
                
                -- Tracking
                selection_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (session_id, game_id, level_number)
            )
        """)
        
        # =====================================================================
        # ACTION6 AVAILABILITY TRACKING (Added 2025-12-08)
        # =====================================================================
        # ACTION6 availability is a SIGNAL:
        # - ACTION6 present = something is selectable on the grid
        # - ACTION6 absent = nothing is currently selectable
        # This helps agents discover CONDITIONS that enable selectability
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS action6_availability_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER,
                
                -- Availability state
                action6_available INTEGER NOT NULL,  -- 1 = available, 0 = not available
                previous_action TEXT,                -- What action preceded this state
                previous_action_coords TEXT,         -- Coordinates if applicable
                
                -- Context for pattern detection
                grid_hash TEXT,                      -- Hash of grid state when availability changed
                available_actions_list TEXT,         -- Full list of available actions (JSON)
                
                -- Tracking
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_action6_availability_game 
            ON action6_availability_events(game_id, level_number, action6_available)
        """)
        
        # =====================================================================
        # SELECTABILITY CONDITIONS (Network Knowledge)
        # =====================================================================
        # Learned patterns for what makes ACTION6 become available/unavailable
        # Example: "Move blue object to (3,4)" -> ACTION6 becomes available
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS selectability_conditions (
                condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- What triggers selectability change
                trigger_action TEXT,                 -- e.g., "ACTION1", "ACTION6"
                trigger_coords TEXT,                 -- Coordinates if relevant
                trigger_object_color INTEGER,        -- Object involved in trigger
                trigger_description TEXT,            -- Human-readable description
                
                -- Result of trigger
                action6_became_available INTEGER,    -- 1 = appeared, 0 = disappeared
                
                -- Validation
                occurrence_count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, trigger_action, trigger_coords, action6_became_available)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_selectability_conditions_game 
            ON selectability_conditions(game_type, level_number, action6_became_available)
        """)
        
        # =====================================================================
        # COLLISION/INTERACTION DETECTION (Added 2025-12-08)
        # =====================================================================
        # When controlled objects move through the grid, they can collide with
        # or interact with other objects. These collisions can trigger:
        # - Object disappearance (collected)
        # - Object transformation (color change)
        # - New object appearance
        # - Level progress (score increase)
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS collision_events (
                collision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER,
                
                -- Controlled object that moved
                controlled_object_color INTEGER NOT NULL,
                controlled_from_x INTEGER,
                controlled_from_y INTEGER,
                controlled_to_x INTEGER,
                controlled_to_y INTEGER,
                
                -- Object that was collided with
                target_object_color INTEGER,
                target_object_x INTEGER,
                target_object_y INTEGER,
                
                -- Collision type
                collision_type TEXT,  -- 'overlap', 'adjacent', 'push', 'same_cell'
                
                -- What happened after collision
                effect_observed TEXT,  -- 'target_disappeared', 'target_moved', 'nothing', etc.
                grid_changes_json TEXT,  -- Detailed changes
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_collision_events_game 
            ON collision_events(game_id, level_number, controlled_object_color)
        """)
        
        # =====================================================================
        # COLLISION EFFECTS (Network Knowledge)
        # =====================================================================
        # Learned patterns: "When color X collides with color Y, effect Z happens"
        # These are verified through multiple observations
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS collision_effects (
                effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Interaction pattern
                controlled_object_color INTEGER NOT NULL,
                target_object_color INTEGER NOT NULL,
                collision_type TEXT,  -- 'overlap', 'push', 'adjacent'
                
                -- Observed effect
                effect_type TEXT NOT NULL,  -- 'target_disappears', 'target_moves', 'color_change', 'spawn_object', 'score_increase'
                effect_details TEXT,        -- JSON with additional info
                
                -- Validation tracking
                occurrence_count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, controlled_object_color, target_object_color, effect_type)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_collision_effects_game 
            ON collision_effects(game_type, level_number)
        """)
        
        # =====================================================================
        # AUTONOMOUS OBJECTS (Objects that move without player input)
        # =====================================================================
        # Some objects in games move on their own (NPCs, enemies, etc.)
        # The agent needs to distinguish:
        # - Objects I control
        # - Objects that react to my actions
        # - Objects that move independently (autonomous)
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS autonomous_objects (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Object identification
                object_color INTEGER NOT NULL,
                
                -- Movement characteristics
                movement_pattern TEXT,           -- 'random', 'chasing', 'fleeing', 'patrol', 'unknown'
                moves_per_turn REAL DEFAULT 0,   -- Average moves per player action
                moves_without_input INTEGER DEFAULT 0,  -- How often it moves when we don't act
                
                -- Controllability
                is_ever_controllable INTEGER DEFAULT 0,  -- Can it be controlled sometimes?
                controllable_conditions TEXT,            -- What makes it controllable (JSON)
                
                -- Validation
                observation_count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, object_color)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_objects_game 
            ON autonomous_objects(game_type, level_number)
        """)
        
        # =====================================================================
        # INTERACTION TRIGGERS (Grid-Wide Effects from Any Action)
        # =====================================================================
        # KEY INSIGHT: When you interact with object A at position (5,5),
        # it might cause a change to object B at position (20,20).
        # This is a TRIGGER - a causal relationship the agent must learn.
        #
        # Examples:
        # - Clicking a button (ACTION6) makes a wall disappear elsewhere
        # - Moving into an object causes another object to change color
        # - Selecting an object unlocks a previously non-selectable object
        #
        # CONSISTENCY = CAUSALITY: If the same trigger produces the same
        # effect 3+ times, it's likely causal, not coincidental.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS interaction_triggers (
                trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The triggering action
                trigger_action TEXT NOT NULL,         -- ACTION1-7
                trigger_position_x INTEGER,           -- Where action was taken (for ACTION6)
                trigger_position_y INTEGER,
                trigger_object_color INTEGER,         -- Object that was interacted with
                trigger_interaction_type TEXT,        -- 'collision', 'selection', 'click', 'adjacent'
                
                -- The observed effect (can be anywhere on the grid)
                effect_position_x INTEGER,            -- Where effect happened
                effect_position_y INTEGER,
                effect_object_color INTEGER,          -- Object that was affected
                effect_type TEXT NOT NULL,            -- 'color_change', 'disappear', 'appear', 'move', 
                                                      -- 'size_change', 'shape_change', 'become_controllable',
                                                      -- 'become_selectable', 'score_increase'
                effect_details TEXT,                  -- JSON with before/after values
                
                -- Distance between trigger and effect (remote effects are interesting)
                effect_distance REAL,                 -- Manhattan distance from trigger to effect
                
                -- Consistency tracking (key to distinguishing causal from coincidental)
                occurrence_count INTEGER DEFAULT 1,
                consistent_count INTEGER DEFAULT 1,   -- Times effect matched exactly
                inconsistent_count INTEGER DEFAULT 0, -- Times expected effect didn't happen
                confidence REAL DEFAULT 0.5,
                
                -- Timestamps
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Deprecation tracking (for safe_cleanup.py)
                is_active INTEGER DEFAULT 1,              -- 0 = deprecated (stale or low confidence)
                last_observed_generation INTEGER DEFAULT 0, -- For staleness detection
                
                UNIQUE(game_type, level_number, trigger_action, trigger_object_color, 
                       effect_object_color, effect_type)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_interaction_triggers_game 
            ON interaction_triggers(game_type, level_number)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_interaction_triggers_confidence 
            ON interaction_triggers(confidence DESC)
        """)
        
        # =====================================================================
        # TRIGGER SEQUENCES (Order of Triggers Matters!)
        # =====================================================================
        # KEY INSIGHT: The ORDER in which you activate triggers can be the key
        # to winning. Example: "First rotate A, THEN click B, THEN move C"
        #
        # This table tracks successful trigger sequences that led to:
        # - Level wins
        # - Score increases
        # - Unlocking new areas
        #
        # SEQUENCE MATCHING: When replaying, agents can follow proven sequences.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS trigger_sequences (
                sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The sequence itself (JSON array of trigger steps)
                -- Each step: {action, object_color, effect_type, step_number}
                sequence_json TEXT NOT NULL,
                sequence_length INTEGER NOT NULL,
                sequence_hash TEXT,               -- Hash for quick comparison
                
                -- What did this sequence achieve?
                outcome_type TEXT NOT NULL,       -- 'level_win', 'score_increase', 'unlock', 'progress'
                outcome_details TEXT,             -- JSON with specifics
                
                -- Validation tracking
                times_succeeded INTEGER DEFAULT 1,
                times_attempted INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 1.0,
                
                -- Discovery context
                discovered_by_agent TEXT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_validated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Is this a complete solution or partial?
                is_complete_solution INTEGER DEFAULT 0,  -- Did it win the level?
                
                -- Deprecation tracking (for safe_cleanup.py)
                is_active INTEGER DEFAULT 1,              -- 0 = deprecated
                last_observed_generation INTEGER DEFAULT 0, -- For staleness detection
                
                UNIQUE(game_type, level_number, sequence_hash)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_trigger_sequences_game 
            ON trigger_sequences(game_type, level_number, outcome_type)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_trigger_sequences_success 
            ON trigger_sequences(success_rate DESC)
        """)
        
        # =====================================================================
        # TRIGGER SEQUENCE EVENTS (Individual steps in a sequence attempt)
        # =====================================================================
        # Track each trigger activation during gameplay.
        # At level end, successful sequences are promoted to trigger_sequences.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS trigger_sequence_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                
                -- What trigger was activated
                trigger_action TEXT NOT NULL,
                trigger_object_color INTEGER,
                trigger_interaction_type TEXT,
                
                -- What effect occurred
                effect_object_color INTEGER,
                effect_type TEXT,
                
                -- Position in the sequence (1-indexed)
                step_number INTEGER NOT NULL,
                
                -- Context
                score_before REAL,
                score_after REAL,
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_trigger_events_game 
            ON trigger_sequence_events(game_id, level_number)
        """)
        
        # =====================================================================
        # OBJECT PROPERTIES (Track size, shape, position, controllability)
        # =====================================================================
        # Beyond just color, objects have:
        # - Size (number of cells)
        # - Shape (contiguous pattern)
        # - Position (center of mass)
        # - Controllability (can it be selected/controlled?)
        # Changes to ANY of these properties are potential triggers.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS object_property_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                
                -- Object identification
                object_color INTEGER NOT NULL,
                
                -- Object properties at this moment
                cell_count INTEGER,               -- Size = number of cells
                bounding_box_width INTEGER,       -- Shape approximation
                bounding_box_height INTEGER,
                center_x REAL,                    -- Center of mass
                center_y REAL,
                shape_hash TEXT,                  -- Hash of relative positions (for shape comparison)
                is_contiguous INTEGER DEFAULT 1,  -- Is object one connected piece?
                
                -- Orientation/rotation tracking
                orientation TEXT,                 -- 'original', 'rot90', 'rot180', 'rot270', 'flip_h', 'flip_v', etc.
                orientation_hash TEXT,            -- Canonical shape hash (same for all rotations of same shape)
                
                -- Controllability state
                is_controlled INTEGER DEFAULT 0,     -- Currently controlled by player?
                is_selectable INTEGER DEFAULT 0,     -- Can be selected (ACTION6 would select it)?
                
                -- Context
                frame_hash TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_snapshots_game 
            ON object_property_snapshots(game_id, level_number, action_number)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_snapshots_color 
            ON object_property_snapshots(game_id, object_color)
        """)
        
        # =====================================================================
        # OBJECT PROPERTY CHANGES (What property changed and when)
        # =====================================================================
        # Track changes to object properties over time.
        # This helps learn what interactions cause what property changes.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS object_property_changes (
                change_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                
                -- Object identification
                object_color INTEGER NOT NULL,
                
                -- What changed
                property_name TEXT NOT NULL,      -- 'size', 'shape', 'position', 'controllable', 'selectable', 'color'
                value_before TEXT,                -- String representation of before value
                value_after TEXT,                 -- String representation of after value
                
                -- Context: what action triggered this change?
                triggering_action TEXT,           -- ACTION1-7
                triggering_object_color INTEGER,  -- If collision, what color did we interact with?
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_property_changes_game 
            ON object_property_changes(game_id, level_number)
        """)
        
        # =====================================================================
        # PERCEPTUAL PRIMITIVE 1: SELF-OBJECT IDENTITY
        # =====================================================================
        # Tracks "I am THIS object" with confidence scoring.
        # Critical distinction:
        # - self_object_identity: Who am I RIGHT NOW in this level?
        # - control_transfer_events: I WAS object X, now I AM object Y
        # - indirect_causation: I control X, which AFFECTS Y (but I don't control Y)
        #
        # The difference between control transfer and indirect causation:
        # - Control Transfer: ACTION1-4 now move a DIFFERENT object
        # - Indirect Causation: ACTION1-4 still move the same object, but
        #   that object's movement CAUSED a change in another object
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS self_object_identity (
                identity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Current controlled object
                self_object_color INTEGER NOT NULL,       -- Color ID of controlled object
                self_object_signature TEXT,               -- Shape hash for stable identification
                self_object_center_x REAL,                -- Center of mass at identification
                self_object_center_y REAL,
                
                -- Confidence and evidence
                confidence REAL DEFAULT 0.5,              -- 0.0 to 1.0
                correlation_score REAL DEFAULT 0.0,       -- Action-direction correlation
                sample_count INTEGER DEFAULT 0,           -- Number of action samples
                
                -- Singularity check (should be exactly 1 controlled object)
                total_candidate_objects INTEGER DEFAULT 1,  -- How many objects responded?
                is_ambiguous INTEGER DEFAULT 0,             -- 1 = multiple objects respond equally
                
                -- When was this identity established?
                established_at_action INTEGER DEFAULT 0,    -- Action number when identified
                still_valid INTEGER DEFAULT 1,              -- 0 = object lost/changed
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_validated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_id, level_number, established_at_action)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_self_object_identity_game 
            ON self_object_identity(game_id, level_number, still_valid)
        """)
        
        # =====================================================================
        # CONTROL TRANSFER EVENTS
        # =====================================================================
        # "I WAS controlling object X, now I AM controlling object Y"
        #
        # This happens when:
        # - Clicking (ACTION6) on a different object to select it
        # - Some trigger causes control to switch automatically
        # - Reaching a checkpoint that gives control of a new character
        #
        # NOT the same as indirect causation - here, ACTION1-4 now move Y, not X.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS control_transfer_events (
                transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                
                -- What was controlled before
                previous_object_color INTEGER,
                previous_object_signature TEXT,
                previous_object_center_x REAL,
                previous_object_center_y REAL,
                
                -- What is controlled now
                new_object_color INTEGER NOT NULL,
                new_object_signature TEXT,
                new_object_center_x REAL,
                new_object_center_y REAL,
                
                -- What caused the transfer?
                transfer_trigger_action TEXT,             -- ACTION6 click, automatic, etc.
                transfer_trigger_coords TEXT,             -- Click coords if ACTION6
                transfer_trigger_reason TEXT,             -- 'selection', 'automatic', 'collision', 'unknown'
                
                -- Confidence that this is a real control transfer (not just indirect causation)
                transfer_confidence REAL DEFAULT 0.5,
                verified_by_movement INTEGER DEFAULT 0,   -- 1 = confirmed new object responds to ACTION1-4
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_control_transfer_game 
            ON control_transfer_events(game_id, level_number)
        """)
        
        # =====================================================================
        # CONTROL TRANSFER PATTERNS (Network Knowledge)
        # =====================================================================
        # Learned patterns: "In game X level Y, clicking color 5 transfers control to it"
        # Shared across agents for faster learning.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS control_transfer_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Transfer pattern
                transfer_trigger_action TEXT NOT NULL,    -- Usually ACTION6
                target_object_color INTEGER,              -- Color of object that becomes controlled
                target_object_signature TEXT,             -- Shape of object (for non-color identification)
                transfer_conditions TEXT,                 -- JSON: what conditions enable this transfer
                
                -- Validation
                occurrence_count INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 1,          -- Times transfer was verified
                confidence REAL DEFAULT 0.5,
                
                -- Timestamps
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, transfer_trigger_action, target_object_color)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_control_transfer_patterns_game 
            ON control_transfer_patterns(game_type, level_number)
        """)
        
        # =====================================================================
        # INDIRECT CAUSATION EFFECTS
        # =====================================================================
        # "I control object X. When X does something, it CAUSES object Y to change.
        #  But I still control X, not Y."
        #
        # Examples:
        # - I push X into Y -> Y moves (but I still control X)
        # - I move X over a trigger -> a wall Y disappears (but I still control X)
        # - X collides with Y -> Y changes color (but I still control X)
        #
        # The key difference from control_transfer:
        # - Control Transfer: ACTION1-4 now move Y instead of X
        # - Indirect Causation: ACTION1-4 still move X, X's actions affect Y
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS indirect_causation_events (
                causation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                
                -- The controlled object (I still control this)
                controlled_object_color INTEGER NOT NULL,
                controlled_action TEXT NOT NULL,          -- What action I took (ACTION1-4)
                controlled_movement_x REAL,               -- How controlled object moved
                controlled_movement_y REAL,
                
                -- The affected object (I DON'T control this, but my action affected it)
                affected_object_color INTEGER NOT NULL,
                affected_effect_type TEXT,                -- 'moved', 'disappeared', 'appeared', 'color_changed', 'transformed'
                affected_movement_x REAL,                 -- If moved, how much?
                affected_movement_y REAL,
                affected_details TEXT,                    -- JSON with before/after details
                
                -- Causation type
                causation_type TEXT,                      -- 'collision', 'trigger', 'push', 'remote'
                causation_distance REAL,                  -- Distance between controlled and affected
                
                -- Confidence this is indirect causation (not control transfer)
                -- High if controlled object still responds to subsequent actions
                confidence REAL DEFAULT 0.5,
                verified_still_controlled INTEGER DEFAULT 0,  -- 1 = confirmed I still control original
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_indirect_causation_game 
            ON indirect_causation_events(game_id, level_number)
        """)
        
        # =====================================================================
        # PERCEPTUAL PRIMITIVE 2: GRID REGION CLASSIFICATION
        # =====================================================================
        # Not all pixels are gameplay. Some are UI (lives, score, move counter).
        # Classification:
        # - 'playfield': Interactive area where gameplay happens
        # - 'ui': Information display (counters, status)
        # - 'decoration': Static elements that never change
        # - 'unknown': Not yet classified
        #
        # Heuristics:
        # - Never changes across actions -> decoration or ui
        # - Changes only symbolically (numbers) -> ui
        # - Responds to actions -> playfield
        # - Contains self-object -> definitely playfield
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS grid_region_classification (
                classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Region bounds (divide grid into macro-regions)
                region_x INTEGER NOT NULL,                -- 0-7 (divides into 8x8 regions)
                region_y INTEGER NOT NULL,                -- 0-7
                region_min_pixel_x INTEGER,               -- Actual pixel bounds
                region_max_pixel_x INTEGER,
                region_min_pixel_y INTEGER,
                region_max_pixel_y INTEGER,
                
                -- Classification
                classification TEXT DEFAULT 'unknown',    -- 'playfield', 'ui', 'decoration', 'unknown'
                classification_reason TEXT,               -- Why this classification
                
                -- Evidence tracking
                total_observations INTEGER DEFAULT 0,     -- How many times observed
                times_changed INTEGER DEFAULT 0,          -- How many times content changed
                times_responded_to_action INTEGER DEFAULT 0,  -- Changes correlated with actions
                times_symbolic_change INTEGER DEFAULT 0,  -- Small isolated changes (counters)
                contains_self_object INTEGER DEFAULT 0,   -- Ever contained the controlled object
                
                -- Confidence
                confidence REAL DEFAULT 0.5,
                
                -- Timestamps
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, region_x, region_y)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_grid_region_classification_game 
            ON grid_region_classification(game_type, level_number, classification)
        """)
        
        # =====================================================================
        # PERCEPTUAL PRIMITIVE 3: RESOURCE COUNTER DETECTION
        # =====================================================================
        # Small isolated objects with changing numbers = finite resources
        # Examples: Lives (hearts), moves remaining, energy, ammo
        #
        # Detection:
        # - Small object (1-5 cells) in UI region
        # - Changes value after actions
        # - Depletion correlates with game over or level fail
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS detected_resource_counters (
                counter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Location (should be in UI region)
                region_x INTEGER NOT NULL,
                region_y INTEGER NOT NULL,
                pixel_x INTEGER,                          -- Exact location
                pixel_y INTEGER,
                
                -- Counter characteristics
                counter_type TEXT DEFAULT 'unknown',      -- 'lives', 'moves', 'score', 'energy', 'unknown'
                initial_value INTEGER,                    -- Value at level start
                current_value INTEGER,                    -- Last observed value
                min_observed INTEGER,                     -- Lowest value seen
                max_observed INTEGER,                     -- Highest value seen
                
                -- Change behavior
                change_direction TEXT,                    -- 'decreasing', 'increasing', 'both'
                change_trigger TEXT,                      -- 'per_action', 'per_collision', 'per_time', 'unknown'
                change_amount INTEGER DEFAULT 1,          -- Typical change per event
                
                -- Depletion consequence
                depletion_consequence TEXT,               -- 'game_over', 'level_fail', 'lose_ability', 'unknown'
                depletion_observed INTEGER DEFAULT 0,     -- Have we seen it hit 0?
                
                -- Validation
                observation_count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                
                -- Timestamps
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, region_x, region_y)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_resource_counters_game 
            ON detected_resource_counters(game_type, level_number)
        """)
        
        # =====================================================================
        # PERCEPTUAL PRIMITIVE 4: VALENCE ASSOCIATIONS
        # =====================================================================
        # Every change gets tagged with positive/negative valence:
        # - Score increase -> positive
        # - Score decrease -> negative
        # - Level completion -> strong positive
        # - Game over -> strong negative
        # - Counter decrease -> context-dependent
        #
        # This grounds the sensation engine with OUTCOME-based feelings.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS valence_associations (
                association_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- What triggered this valence?
                trigger_type TEXT NOT NULL,               -- 'collision', 'action', 'proximity', 'selection'
                trigger_action TEXT,                      -- ACTION1-7 if applicable
                trigger_object_color INTEGER,             -- Object color if applicable
                trigger_target_color INTEGER,             -- Target of interaction if applicable
                
                -- What was the consequence?
                consequence_type TEXT NOT NULL,           -- 'score_change', 'counter_change', 'game_end', 'level_end'
                consequence_details TEXT,                 -- JSON with specifics
                
                -- Valence: -1.0 (very bad) to +1.0 (very good)
                valence REAL NOT NULL,
                valence_magnitude REAL DEFAULT 0.5,       -- How strong is this association?
                
                -- Validation
                observation_count INTEGER DEFAULT 1,
                consistent_count INTEGER DEFAULT 1,       -- Times this valence was confirmed
                confidence REAL DEFAULT 0.5,
                
                -- Timestamps
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, trigger_type, trigger_object_color, 
                       trigger_target_color, consequence_type)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_valence_associations_game 
            ON valence_associations(game_type, level_number)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_valence_associations_valence 
            ON valence_associations(valence)
        """)
        
        # =====================================================================
        # PERCEPTUAL PRIMITIVE 5: INFERRED GOAL STATES
        # =====================================================================
        # Goals aren't always visible objects. They can be abstract states:
        # - "Clear all objects of color X"
        # - "Reach position (X, Y)"
        # - "Match a specific pattern"
        # - "Survive N actions"
        #
        # Inference: Analyze what grid state existed when level ended successfully.
        # =====================================================================
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS inferred_goal_states (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Goal type
                goal_type TEXT NOT NULL,                  -- 'clear_color', 'reach_position', 'match_pattern', 
                                                          -- 'survive', 'collect_all', 'transform', 'unknown'
                
                -- Goal parameters (depends on goal_type)
                goal_params TEXT,                         -- JSON: {color_to_clear, position_to_reach, pattern_hash, etc.}
                
                -- How was this goal inferred?
                inference_method TEXT,                    -- 'level_end_analysis', 'score_correlation', 'network_wisdom'
                inference_evidence TEXT,                  -- JSON: evidence supporting this inference
                
                -- Goal progress tracking (for agents to use)
                progress_metric TEXT,                     -- How to measure progress toward this goal
                                                          -- e.g., "count of color X remaining" or "distance to position"
                
                -- Validation
                times_validated INTEGER DEFAULT 1,        -- Times this goal was confirmed by level wins
                confidence REAL DEFAULT 0.5,
                
                -- Is the goal visible or abstract?
                is_visible INTEGER DEFAULT 0,             -- 1 = goal object exists on grid
                goal_object_color INTEGER,                -- If visible, what color is the goal?
                
                -- Timestamps
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_validated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(game_type, level_number, goal_type, goal_params)
            )
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_inferred_goals_game 
            ON inferred_goal_states(game_type, level_number)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_inferred_goals_confidence 
            ON inferred_goal_states(confidence DESC)
        """)
    
    def _get_current_generation(self) -> int:
        """Get current generation from evolutionary_state for deprecation tracking."""
        try:
            result = self.db.execute_query(
                'SELECT value FROM evolutionary_state WHERE key = "current_generation"'
            )
            return int(result[0]['value']) if result else 0
        except:
            return 0
    
    def identify_controlled_objects(
        self, 
        game_id: str, 
        level: int, 
        action_sequence: List[Dict],
        frame_sequence: List[Dict]
    ) -> Tuple[List[str], float]:
        """
        Identify which objects respond to actions using action-movement correlation.
        
        FIXED (2025-12-06): Previous implementation tracked ALL changed coordinates,
        resulting in 600+ "controlled" objects (the entire screen). 
        
        New approach: Correlate action DIRECTION with object MOVEMENT direction.
        - ACTION1 (up) -> object moves up (y decreases)
        - ACTION2 (down) -> object moves down (y increases)
        - ACTION3 (left) -> object moves left (x decreases)
        - ACTION4 (right) -> object moves right (x increases)
        
        Only objects that consistently move in the action's direction are "controlled".
        
        Args:
            game_id: Game identifier
            level: Level number
            action_sequence: List of actions taken (with 'action_type' field)
            frame_sequence: List of frames (before/after each action, with 'grid' field)
        
        Returns:
            (controlled_objects, confidence) - controlled objects as list of "x:N,y:M" strings
        """
        if not action_sequence or not frame_sequence:
            return ([], 0.0)
        
        # Map action types to expected movement directions
        # ARC games: ACTION1=up, ACTION2=down, ACTION3=left, ACTION4=right
        # ACTION5 is CONTEXT-DEPENDENT (rotate, toggle, interact, etc.) - we learn what it does
        # ACTION6=click, ACTION7=submit are coordinate-based, handled separately
        ACTION_DIRECTION = {
            'ACTION1': (0, -1),  # up: y decreases
            'ACTION2': (0, 1),   # down: y increases  
            'ACTION3': (-1, 0),  # left: x decreases
            'ACTION4': (1, 0),   # right: x increases
            'action_1': (0, -1),
            'action_2': (0, 1),
            'action_3': (-1, 0),
            'action_4': (1, 0),
        }
        
        # ACTION5 variants - we don't know direction, but we track if it causes changes
        ACTION5_VARIANTS = {'ACTION5', 'action_5', 'ACTION 5'}
        
        # ACTION6 is coordinate-based clicking (0-63 range) - pseudo buttons
        ACTION6_VARIANTS = {'ACTION6', 'action_6', 'ACTION 6'}
        
        # Track object movement correlation: object_signature -> {correct_moves, total_moves}
        object_control_score = {}  # {object_id: {'correct': int, 'total': int, 'positions': [(x,y)]}}
        
        # Track ACTION5 effects separately (non-directional but may indicate control)
        action5_effects = {}  # {object_id: {'changes': int, 'total': int}}
        
        # Track ACTION6 (pseudo button) effects by screen region
        # Divides 64x64 screen into 8x8 regions (8 pixels each)
        action6_region_effects = {}  # {(region_x, region_y): {'direction': counts, 'objects': set}}
        
        for i, action in enumerate(action_sequence):
            if i >= len(frame_sequence) - 1:
                break
            
            frame_before = frame_sequence[i]
            frame_after = frame_sequence[i + 1]
            
            action_type = action.get('action_type', '')
            
            # Handle ACTION5 specially - it's context-dependent per game type
            if action_type in ACTION5_VARIANTS:
                self._track_action5_effects(
                    frame_before, frame_after, action5_effects, game_id, level
                )
                continue
            
            # Handle ACTION6 (pseudo button clicks) - coordinate-based
            if action_type in ACTION6_VARIANTS:
                click_x = action.get('x', action.get('click_x', 0))
                click_y = action.get('y', action.get('click_y', 0))
                self._track_action6_effects(
                    frame_before, frame_after, action6_region_effects,
                    click_x, click_y, game_id, level
                )
                continue
            
            # Get action direction (skip click/submit which are coordinate-based)
            expected_direction = ACTION_DIRECTION.get(action_type)
            if not expected_direction:
                continue  # Skip ACTION6=click, ACTION7=submit (coordinate-based)
            
            dx_expected, dy_expected = expected_direction
            
            # Find objects that MOVED in the expected direction
            grid_before = frame_before.get('grid', [])
            grid_after = frame_after.get('grid', [])
            
            if not grid_before or not grid_after:
                continue
            
            # Find objects in before and after frames (non-zero, non-background cells)
            objects_before = self._find_objects_in_grid(grid_before)
            objects_after = self._find_objects_in_grid(grid_after)
            
            # Match objects and check movement direction
            for obj_id, positions_before in objects_before.items():
                if obj_id not in objects_after:
                    continue  # Object disappeared
                
                positions_after = objects_after[obj_id]
                
                # Calculate centroid movement
                cx_before = sum(p[0] for p in positions_before) / len(positions_before)
                cy_before = sum(p[1] for p in positions_before) / len(positions_before)
                cx_after = sum(p[0] for p in positions_after) / len(positions_after)
                cy_after = sum(p[1] for p in positions_after) / len(positions_after)
                
                dx_actual = cx_after - cx_before
                dy_actual = cy_after - cy_before
                
                # Did object move at all?
                if abs(dx_actual) < 0.5 and abs(dy_actual) < 0.5:
                    continue  # Object didn't move
                
                # Initialize tracking for this object
                if obj_id not in object_control_score:
                    object_control_score[obj_id] = {'correct': 0, 'total': 0, 'positions': []}
                
                object_control_score[obj_id]['total'] += 1
                object_control_score[obj_id]['positions'] = list(positions_after)[:5]  # Store sample positions
                
                # Check if movement matches expected direction
                movement_matches = False
                if dx_expected != 0:  # Horizontal action
                    movement_matches = (dx_expected > 0 and dx_actual > 0.5) or (dx_expected < 0 and dx_actual < -0.5)
                if dy_expected != 0:  # Vertical action
                    movement_matches = (dy_expected > 0 and dy_actual > 0.5) or (dy_expected < 0 and dy_actual < -0.5)
                
                if movement_matches:
                    object_control_score[obj_id]['correct'] += 1
        
        # Identify controlled objects: >60% correct movement correlation with at least 2 samples
        controlled = []
        best_score = 0.0
        
        for obj_id, scores in object_control_score.items():
            if scores['total'] < 2:
                continue  # Not enough samples
            
            correlation = scores['correct'] / scores['total']
            if correlation >= 0.6:  # 60% threshold for "controlled"
                # Store representative position(s) of this object
                for pos in scores['positions'][:3]:  # Max 3 positions per controlled object
                    controlled.append(f"x:{pos[0]},y:{pos[1]}")
                best_score = max(best_score, correlation)
        
        # Also check ACTION5 effects - objects that consistently change on ACTION5
        # may be "controlled" even if not directionally
        for obj_id, effects in action5_effects.items():
            if effects['total'] < 2:
                continue
            
            change_rate = effects['changes'] / effects['total']
            if change_rate >= 0.7:  # 70% threshold for ACTION5 control (higher since non-directional)
                # This object responds to ACTION5 - mark as controlled
                if obj_id not in object_control_score:
                    # Get positions from the effects tracking
                    for pos in effects.get('positions', [])[:3]:
                        controlled.append(f"x:{pos[0]},y:{pos[1]}")
                    best_score = max(best_score, change_rate)
                    logger.debug(f"[SELF-MODEL] ACTION5 controls object {obj_id} (change rate: {change_rate:.2f})")
        
        # Confidence is the best correlation score, or 0 if nothing found
        confidence = best_score if controlled else 0.0
        
        # Limit to max 50 controlled coordinates (prevent bloat)
        controlled = controlled[:50]
        
        return (controlled, confidence)
    
    def _track_action5_effects(
        self,
        frame_before: Dict,
        frame_after: Dict,
        action5_effects: Dict,
        game_id: str,
        level: int
    ) -> None:
        """
        Track what ACTION5 does in this game/level.
        
        ACTION5 is context-dependent: rotate, toggle, interact, select, etc.
        We learn empirically by tracking which objects change when ACTION5 is used.
        
        Args:
            frame_before: Frame before ACTION5
            frame_after: Frame after ACTION5
            action5_effects: Dict tracking {object_id: {changes, total, positions}}
            game_id: Current game (for logging)
            level: Current level
        """
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return
        
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        # Check each object for ANY change (position, size, color transformation)
        for obj_id, positions_before in objects_before.items():
            if obj_id not in action5_effects:
                action5_effects[obj_id] = {'changes': 0, 'total': 0, 'positions': []}
            
            action5_effects[obj_id]['total'] += 1
            
            if obj_id not in objects_after:
                # Object disappeared - that's a change!
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['positions'] = list(positions_before)[:5]
                continue
            
            positions_after = objects_after[obj_id]
            
            # Check for position change
            cx_before = sum(p[0] for p in positions_before) / len(positions_before)
            cy_before = sum(p[1] for p in positions_before) / len(positions_before)
            cx_after = sum(p[0] for p in positions_after) / len(positions_after)
            cy_after = sum(p[1] for p in positions_after) / len(positions_after)
            
            position_changed = abs(cx_after - cx_before) > 0.3 or abs(cy_after - cy_before) > 0.3
            
            # Check for size/shape change
            size_changed = abs(len(positions_after) - len(positions_before)) > 0
            
            # Check for rotation/transformation (positions differ but centroid same)
            positions_set_before = set(positions_before)
            positions_set_after = set(positions_after)
            shape_changed = positions_set_before != positions_set_after
            
            if position_changed or size_changed or shape_changed:
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['positions'] = list(positions_after)[:5]
        
        # Also check for NEW objects that appeared (ACTION5 might create things)
        for obj_id, positions_after in objects_after.items():
            if obj_id not in objects_before:
                if obj_id not in action5_effects:
                    action5_effects[obj_id] = {'changes': 0, 'total': 0, 'positions': []}
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['total'] += 1
                action5_effects[obj_id]['positions'] = list(positions_after)[:5]
    
    def _track_action6_effects(
        self,
        frame_before: Dict,
        frame_after: Dict,
        action6_region_effects: Dict,
        click_x: int,
        click_y: int,
        game_id: str,
        level: int
    ) -> None:
        """
        Track what ACTION6 (pseudo button clicks) do at specific screen regions.
        
        ACTION6 uses x,y coordinates (0-63 range) like a touchscreen.
        Clicking on pseudo buttons often produces movement effects similar to ACTION1-4.
        We divide the screen into 8x8 regions and track what clicking each region does.
        
        Args:
            frame_before: Frame before click
            frame_after: Frame after click
            action6_region_effects: Dict tracking effects by region
            click_x, click_y: Click coordinates (0-63)
            game_id: Current game
            level: Current level
        """
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return
        
        # Convert click coords to region (divide into 8x8 grid of regions)
        # Each region is 8 pixels (64 / 8 = 8)
        region_x = min(click_x // 8, 7)  # 0-7
        region_y = min(click_y // 8, 7)  # 0-7
        region_key = (region_x, region_y)
        
        if region_key not in action6_region_effects:
            action6_region_effects[region_key] = {
                'up': 0, 'down': 0, 'left': 0, 'right': 0,
                'toggle': 0, 'no_effect': 0,
                'affected_objects': set(),
                'total': 0
            }
        
        action6_region_effects[region_key]['total'] += 1
        
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        # Track what direction objects moved (if any)
        movement_detected = False
        for obj_id, positions_before in objects_before.items():
            if obj_id not in objects_after:
                # Object disappeared - that's a toggle/change
                action6_region_effects[region_key]['toggle'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
                continue
            
            positions_after = objects_after[obj_id]
            
            # Calculate movement
            cx_before = sum(p[0] for p in positions_before) / len(positions_before)
            cy_before = sum(p[1] for p in positions_before) / len(positions_before)
            cx_after = sum(p[0] for p in positions_after) / len(positions_after)
            cy_after = sum(p[1] for p in positions_after) / len(positions_after)
            
            dx = cx_after - cx_before
            dy = cy_after - cy_before
            
            # Determine movement direction
            if abs(dy) > 0.5 and dy < 0:
                action6_region_effects[region_key]['up'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dy) > 0.5 and dy > 0:
                action6_region_effects[region_key]['down'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dx) > 0.5 and dx < 0:
                action6_region_effects[region_key]['left'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dx) > 0.5 and dx > 0:
                action6_region_effects[region_key]['right'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
        
        # Check for new objects (button might spawn things)
        for obj_id in objects_after:
            if obj_id not in objects_before:
                action6_region_effects[region_key]['toggle'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
        
        if not movement_detected:
            action6_region_effects[region_key]['no_effect'] += 1
    
    def _find_objects_in_grid(self, grid: List) -> Dict[int, List[Tuple[int, int]]]:
        """
        Find all distinct objects in a grid by color/value.
        
        Returns dict mapping object_id (color value) -> list of (x, y) positions.
        Ignores background (value 0) and very common values (>50% of grid = background).
        """
        objects = {}  # color -> [(x, y), ...]
        
        if not grid:
            return objects
        
        height = len(grid)
        width = len(grid[0]) if grid else 0
        total_cells = height * width
        
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == 0:  # Skip background
                    continue
                if cell not in objects:
                    objects[cell] = []
                objects[cell].append((x, y))
        
        # Filter out "background" colors that cover >50% of non-zero cells
        filtered = {}
        for color, positions in objects.items():
            if len(positions) < total_cells * 0.5:  # Not background
                filtered[color] = positions
        
        return filtered
    
    def _find_changed_coordinates(
        self, 
        frame_before: Dict, 
        frame_after: Dict
    ) -> List[str]:
        """
        Find coordinates that changed between frames.
        
        Args:
            frame_before: Frame state before action
            frame_after: Frame state after action
        
        Returns:
            List of changed coordinate strings (e.g., "x:5,y:10")
        """
        changed = []
        
        # Simple pixel-level comparison
        # In real implementation, would compare grid states
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return changed
        
        for y in range(min(len(grid_before), len(grid_after))):
            for x in range(min(len(grid_before[y]), len(grid_after[y]))):
                if grid_before[y][x] != grid_after[y][x]:
                    changed.append(f"x:{x},y:{y}")
        
        return changed
    
    def store_control_map(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        confidence: float
    ):
        """
        Store agent's control map in database.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
            controlled_objects: List of controlled object coordinates
            confidence: Confidence score (0.0-1.0)
        """
        from datetime import datetime
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_object_control
            (agent_id, game_id, level_number, controlled_objects, confidence, learned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            game_id,
            level,
            json.dumps(controlled_objects),
            confidence,
            datetime.now().isoformat()
        ))
        
        logger.info(
            f"Stored control map for {agent_id} on {game_id} L{level}: "
            f"{len(controlled_objects)} objects (confidence: {confidence:.2f})"
        )
    
    def get_controlled_objects(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> Optional[List[str]]:
        """
        Retrieve agent's known controlled objects.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
        
        Returns:
            List of controlled object coordinates, or None if not learned
        """
        result = self.db.execute_query("""
            SELECT controlled_objects, confidence
            FROM agent_object_control
            WHERE agent_id = ? AND game_id = ? AND level_number = ?
        """, (agent_id, game_id, level))
        
        if result and result[0]['controlled_objects']:
            return json.loads(result[0]['controlled_objects'])
        
        return None

    def get_self_identity_snapshot(
        self,
        agent_id: Optional[str],
        game_id: Optional[str],
        level: Optional[int],
        frame: Optional[List[List[int]]] = None
    ) -> Dict[str, Any]:
        """Lightweight self-identity snapshot for persona reasoning."""
        controlled: List[str] = []
        try:
            if agent_id and game_id and level is not None:
                controlled = self.get_controlled_objects(agent_id, game_id, level) or []
        except Exception:
            controlled = []

        shape: Optional[str] = None
        try:
            if frame and isinstance(frame, list) and frame and isinstance(frame[0], list):
                shape = f"{len(frame)}x{len(frame[0])}"
        except Exception:
            shape = None

        return {
            'controlled_objects': controlled,
            'frame_shape': shape,
            'level': level,
            'game_id': game_id,
        }
    
    # ========================================================================
    # SYSTEMATIC OBJECT CONTROL DISCOVERY
    # ========================================================================
    # This is a SEED capability - even babies do this!
    # Pick up objects, test if you can control them, learn what you control.
    # ========================================================================
    
    def generate_object_discovery_plan(
        self,
        frame: List[List[int]],
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a systematic plan to discover which objects are controllable.
        
        This is what babies do:
        1. See distinct objects
        2. Try to interact with each
        3. See if it responds to control
        4. Remember which ones respond
        
        Args:
            frame: Current game frame
            game_type: Game type
            level: Current level
            
        Returns:
            List of discovery actions to take:
            [
                {'phase': 'click', 'target': obj_id, 'coords': (x, y)},
                {'phase': 'test', 'actions': [1, 2, 3, 4]},
                ...
            ]
        """
        # Use seed primitive to find distinct objects
        from seed_primitives import get_seed_primitives
        primitives = get_seed_primitives()
        
        objects = primitives.call('find_distinct_objects', frame)
        
        if not objects:
            return []
        
        # Check what we already know about this game/level
        known_controllable = self._get_known_controllable_objects(game_type, level)
        known_buttons = self._get_known_buttons(game_type, level)
        
        # Generate discovery plan
        plan = []
        
        for obj in objects:
            obj_id = obj['object_id']
            color = obj['color']
            cx, cy = obj['centroid']
            
            # Skip if we already know about this object
            if obj_id in known_controllable or obj_id in known_buttons:
                continue
            
            # Plan 1: Click on the object (try to select it)
            plan.append({
                'phase': 'select',
                'action': 'ACTION6',
                'target': obj_id,
                'coords': (int(cx), int(cy)),
                'purpose': f'Click on {obj_id} to see if selectable'
            })
            
            # Plan 2: Test movement actions (see if object responds)
            plan.append({
                'phase': 'test_control',
                'actions': ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'],
                'target': obj_id,
                'purpose': f'Test if {obj_id} responds to movement'
            })
        
        logger.info(f"[DISCOVERY] Generated {len(plan)} discovery actions for {len(objects)} objects")
        return plan
    
    def execute_object_discovery(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        action_taken: str,
        click_coords: Tuple[int, int] = None,
        game_type: str = None,
        level: int = None,
        agent_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze a single action to discover object control relationships.
        
        Call this after EVERY action during the discovery phase.
        
        Args:
            frame_before: Frame before action
            frame_after: Frame after action
            action_taken: The action (ACTION1-ACTION7)
            click_coords: For ACTION6, the click coordinates
            game_type: Game type for storing results
            level: Level number
            agent_id: Agent doing the discovery
            
        Returns:
            Discovery result:
            {
                'discovered_control': bool,
                'object_id': str or None,
                'control_type': 'direct'|'after_select'|'button'|None,
                'movement_matches_action': bool,
                'confidence': float
            }
        """
        from seed_primitives import get_seed_primitives
        primitives = get_seed_primitives()
        
        result = {
            'discovered_control': False,
            'object_id': None,
            'control_type': None,
            'movement_matches_action': False,
            'confidence': 0.0
        }
        
        # Get objects in both frames
        objects_before = primitives.call('find_distinct_objects', frame_before)
        objects_after = primitives.call('find_distinct_objects', frame_after)
        
        if not objects_before:
            return result
        
        # Map action to expected direction
        action_num = int(action_taken.replace('ACTION', '')) if action_taken.startswith('ACTION') else 0
        
        # Track spurious/environmental movement (objects that move but not matching our action)
        spurious_movers = []
        
        # For movement actions (1-4), check if any object moved in the expected direction
        if action_num in [1, 2, 3, 4]:
            for obj in objects_before:
                obj_id = obj['object_id']
                
                # Use seed primitive to check movement
                movement = primitives.call('get_object_movement', obj_id, frame_before, frame_after)
                matches = primitives.call('action_matches_movement', action_num, movement)
                
                # SPURIOUS MOVEMENT DETECTION
                # Object moved but in WRONG direction = environmental/NPC, not controlled
                if movement and movement != 'none' and not matches:
                    spurious_movers.append({
                        'object_id': obj_id,
                        'movement': movement,
                        'expected': {1: 'up', 2: 'down', 3: 'left', 4: 'right'}.get(action_num)
                    })
                    # Record as likely environmental object
                    if game_type and level:
                        try:
                            controlled_color = int(obj_id.replace('obj_', ''))
                            self._record_spurious_movement(
                                game_type, level, controlled_color, 
                                action_taken, movement, agent_id
                            )
                        except Exception as e:
                            logger.debug(f"Spurious movement recording failed: {e}")
                
                if matches:
                    result['discovered_control'] = True
                    result['object_id'] = obj_id
                    result['control_type'] = 'direct'
                    result['movement_matches_action'] = True
                    result['confidence'] = 0.7
                    
                    # Store discovery locally
                    if game_type and level:
                        self._record_control_discovery(
                            game_type, level, obj_id,
                            control_type='direct',
                            confidence=0.7,
                            agent_id=agent_id
                        )
                        
                        # SHARE TO NETWORK: Observation-based validation (not waiting for win!)
                        # learn_from_movement_correlation tracks observation count
                        # and only validates after 3+ consistent observations
                        try:
                            # Extract color from obj_id (e.g., "obj_10" -> 10)
                            controlled_color = int(obj_id.replace('obj_', ''))
                            # Map action to direction for network hypothesis
                            action_to_direction = {1: 'up', 2: 'down', 3: 'left', 4: 'right'}
                            direction = action_to_direction.get(action_num, movement)
                            
                            self.learn_from_movement_correlation(
                                agent_id=agent_id or 'discovery',
                                game_id=f"{game_type}-discovery",
                                level=level,
                                action=action_taken,
                                direction=direction,
                                controlled_color=controlled_color,
                                generation=0
                            )
                            # Log message now in learn_from_movement_correlation based on observation count
                        except Exception as e:
                            logger.debug(f"Network sharing failed (non-critical): {e}")
                    
                    logger.info(f"[DISCOVERY] Found control: {obj_id} responds to {action_taken}")
                    break
        
        # For ACTION6 (click), check if we selected something
        elif action_num == 6 and click_coords:
            clicked_obj = primitives.call('get_click_target', frame_before, click_coords[0], click_coords[1])
            
            if clicked_obj:
                result['object_id'] = clicked_obj
                
                # Did anything change after clicking?
                for obj in objects_before:
                    if obj['object_id'] == clicked_obj:
                        # Check if object properties changed
                        movement = primitives.call('get_object_movement', clicked_obj, frame_before, frame_after)
                        
                        if movement != 'none':
                            # Object moved when clicked - might be a button or direct control
                            result['discovered_control'] = True
                            result['control_type'] = 'button'
                            result['confidence'] = 0.6
                            
                            if game_type and level:
                                self._record_button_discovery(
                                    game_type, level, click_coords[0], click_coords[1],
                                    movement, clicked_obj, agent_id
                                )
                                
                                # SHARE TO NETWORK: Button discovery based on observation
                                # Uses same repeated testing logic as movement
                                try:
                                    controlled_color = int(clicked_obj.replace('obj_', ''))
                                    self.learn_from_movement_correlation(
                                        agent_id=agent_id or 'discovery',
                                        game_id=f"{game_type}-discovery",
                                        level=level,
                                        action='ACTION6',
                                        direction=movement,
                                        controlled_color=controlled_color,
                                        generation=0
                                    )
                                    # Log message handled by learn_from_movement_correlation
                                except Exception as e:
                                    logger.debug(f"Network button sharing failed: {e}")
                        else:
                            # Object didn't move - might be a selection (test with next movement)
                            result['control_type'] = 'maybe_selectable'
                            result['confidence'] = 0.3
        
        # Add spurious movers info to result (for debugging/analysis)
        if spurious_movers:
            result['spurious_movers'] = spurious_movers
            result['spurious_count'] = len(spurious_movers)
        
        return result
    
    def get_discovery_phase_actions(
        self,
        frame: List[List[int]],
        game_type: str,
        level: int,
        actions_taken: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next action for the discovery phase.
        
        First 20 actions should systematically test objects.
        Discovery phase length evolves naturally through selection pressure -
        agents with optimal discovery time succeed more and reproduce.
        
        Args:
            frame: Current frame
            game_type: Game type
            level: Level number
            actions_taken: How many actions taken so far
            
        Returns:
            Action recommendation or None if discovery complete:
            {'action': 'ACTION6', 'x': 10, 'y': 15, 'reason': 'Testing object obj_3'}
        """
        # Only do discovery phase in first 20 actions
        # NOTE: Discovery length evolves naturally - agents with optimal discovery
        # time succeed more and reproduce. No central coordinator intervention.
        if actions_taken > 20:
            return None
        
        # Generate plan if we don't have one
        if not hasattr(self, '_current_discovery_plan') or not self._current_discovery_plan:
            self._current_discovery_plan = self.generate_object_discovery_plan(frame, game_type, level)
            self._discovery_plan_index = 0
        
        # Get next action from plan
        if self._discovery_plan_index >= len(self._current_discovery_plan):
            # Discovery complete
            return None
        
        step = self._current_discovery_plan[self._discovery_plan_index]
        
        if step['phase'] == 'select':
            self._discovery_plan_index += 1
            return {
                'action': step['action'],
                'x': step['coords'][0],
                'y': step['coords'][1],
                'reason': step['purpose']
            }
        elif step['phase'] == 'test_control':
            # Test one movement action at a time
            if not hasattr(self, '_test_action_index'):
                self._test_action_index = 0
            
            actions = step['actions']
            if self._test_action_index >= len(actions):
                self._test_action_index = 0
                self._discovery_plan_index += 1
                return self.get_discovery_phase_actions(frame, game_type, level, actions_taken)
            
            action = actions[self._test_action_index]
            self._test_action_index += 1
            
            return {
                'action': action,
                'reason': f"Testing {step['target']} control with {action}"
            }
        
        return None
    
    def _get_known_controllable_objects(self, game_type: str, level: int) -> List[str]:
        """Get objects already known to be controllable for this game/level."""
        result = self.db.execute_query("""
            SELECT object_color FROM object_selection_state
            WHERE game_type = ? AND level_number = ? AND is_moveable = 1
        """, (game_type, level))
        
        return [f"obj_{r['object_color']}" for r in result] if result else []
    
    def _get_known_buttons(self, game_type: str, level: int) -> List[str]:
        """Get objects already known to be buttons for this game/level."""
        result = self.db.execute_query("""
            SELECT object_color FROM object_selection_state
            WHERE game_type = ? AND level_number = ? AND is_button = 1
        """, (game_type, level))
        
        return [f"obj_{r['object_color']}" for r in result] if result else []
    
    def _record_control_discovery(
        self,
        game_type: str,
        level: int,
        object_id: str,
        control_type: str,
        confidence: float,
        agent_id: str = None
    ):
        """Record a control discovery to the database."""
        # Extract color from object_id
        try:
            color = int(object_id.replace('obj_', ''))
        except:
            return
        
        self.db.execute_query("""
            INSERT INTO object_selection_state 
            (game_type, level_number, object_color, is_selectable, is_moveable, 
             control_actions, confidence, discovered_by_agent)
            VALUES (?, ?, ?, 1, 1, ?, ?, ?)
            ON CONFLICT(game_type, level_number, object_color) DO UPDATE SET
                is_moveable = 1,
                confidence = MAX(confidence, excluded.confidence),
                discovery_count = discovery_count + 1,
                last_observed = CURRENT_TIMESTAMP
        """, (game_type, level, color, 
              json.dumps(['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']),
              confidence, agent_id))
    
    def _record_spurious_movement(
        self,
        game_type: str,
        level: int,
        object_color: int,
        action_taken: str,
        actual_movement: str,
        agent_id: str = None
    ):
        """
        Record when an object moves in a direction that doesn't match our action.
        
        This indicates the object is likely environmental/NPC movement, not player-controlled.
        Used to filter out false positives in control detection.
        
        Example: We pressed ACTION1 (up) but obj_5 moved left = obj_5 is environmental
        """
        # Use object_selection_state to mark as environmental (lower confidence)
        self.db.execute_query("""
            INSERT INTO object_selection_state 
            (game_type, level_number, object_color, is_selectable, is_moveable, 
             control_actions, confidence, discovered_by_agent)
            VALUES (?, ?, ?, 0, 0, ?, ?, ?)
            ON CONFLICT(game_type, level_number, object_color) DO UPDATE SET
                confidence = MAX(0.1, confidence - 0.1),
                movement_test_count = COALESCE(movement_test_count, 0) + 1,
                last_observed = CURRENT_TIMESTAMP
        """, (game_type, level, object_color, 
              json.dumps([]),  # No control actions
              0.1,  # Low confidence = likely environmental
              agent_id))
        
        logger.debug(
            f"[SPURIOUS] color_{object_color} moved {actual_movement} on {action_taken} "
            f"(expected opposite) - likely environmental"
        )
    
    def _record_button_discovery(
        self,
        game_type: str,
        level: int,
        x: int,
        y: int,
        movement_direction: str,
        affected_object: str,
        agent_id: str = None
    ):
        """Record a button discovery to the database."""
        region_x = min(x // 8, 7)
        region_y = min(y // 8, 7)
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO pseudo_button_behavior
            (game_type, level_number, region_x, region_y, 
             produces_action, movement_direction, affected_objects, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (game_type, level, region_x, region_y,
              f'ACTION6@{x},{y}', movement_direction, 
              json.dumps([affected_object]), 0.6))
    
    def reset_discovery_state(self):
        """Reset discovery state for a new game/level."""
        self._current_discovery_plan = []
        self._discovery_plan_index = 0
        self._test_action_index = 0

    # ========================================================================
    # TETRAHEDRAL GRAMMAR: INTERPRETATION (VOID) AXIS
    # ========================================================================
    # From McGuffin Tensor Framework: Every object needs four axes:
    #   Structure (A) - What it IS (position, color, form)
    #   Function (B)  - What it DOES (responds to actions, effects)
    #   Method (C)    - HOW it operates (control correlation, action map)
    #   Interpretation (D) - WHAT IT MEANS (semantic role, goal relevance)
    # 
    # This is the VOID axis - the meaning anchor that makes all other axes coherent.
    # ========================================================================
    
    # Relational tensors from McGuffin: Each pair of axes creates a relationship
    OBJECT_RELATIONSHIP_TENSORS = {
        ('structure', 'function'): 'enables',      # Structure enables Function
        ('structure', 'method'): 'constrains',     # Structure constrains Method
        ('structure', 'interpretation'): 'defines', # Structure defines Meaning
        ('function', 'method'): 'triggers',        # Function triggers Method
        ('function', 'interpretation'): 'reveals', # Function reveals Meaning
        ('method', 'interpretation'): 'anchors',   # Method anchors Meaning
    }
    
    def calculate_interpretation_axis(
        self,
        agent_id: str,
        obj_data: Dict[str, Any],
        goal_context: Dict[str, Any],
        sensation_engine: Any = None
    ) -> Dict[str, Any]:
        """
        Calculate the Interpretation (Void) axis for an object.
        
        This is the MEANING layer that integrates:
        - Is this ME or something else?
        - Is this relevant to my goal?
        - Is this dangerous or helpful?
        
        From McGuffin: Void = Context = Meaning. Without this axis,
        agents see facts but don't understand them.
        
        Args:
            agent_id: Agent identifier
            obj_data: Object data with structure/function/method info
            goal_context: Goal information (positions, types)
            sensation_engine: Optional SensationEngine for emotional data
            
        Returns:
            Interpretation axis dictionary with semantic role, relevance, threat, attraction
        """
        interpretation = {
            'semantic_role': 'unknown',    # 'self', 'tool', 'obstacle', 'goal', 'environmental'
            'goal_relevance': 0.0,         # 0-1: How relevant to winning?
            'threat_level': 0.0,           # 0-1: How dangerous?
            'attraction': 0.0,             # -1 to 1: Avoid (-) or approach (+)?
            'meaning_confidence': 0.0,     # 0-1: How confident in this interpretation?
            'is_self': False,              # Boolean: Is this the agent?
            'is_tool': False,              # Boolean: Is this a controllable tool?
            'is_goal': False,              # Boolean: Is this a goal/target?
            'is_obstacle': False           # Boolean: Is this blocking progress?
        }
        
        # Get sensation data if available (emotional context)
        sensation_score = 0.0
        impression_data = None
        if sensation_engine:
            try:
                obj_type = f"color_{obj_data.get('color', 0)}"
                sensation_score = sensation_engine.perceive_object(agent_id, obj_type, obj_data)
                impression_data = sensation_engine.query_personal_impression(agent_id, obj_type)
                
                if impression_data:
                    # Apply learned associations from sensation engine
                    association = impression_data.get('association', 'neutral')
                    strength = impression_data.get('impression_strength', 0.5)
                    
                    if association == 'danger':
                        interpretation['threat_level'] = strength
                        interpretation['is_obstacle'] = strength > 0.5
                    elif association == 'goal':
                        interpretation['goal_relevance'] = strength
                        interpretation['is_goal'] = strength > 0.5
                    elif association == 'obstacle':
                        interpretation['threat_level'] = strength * 0.5
                        interpretation['is_obstacle'] = strength > 0.5
            except Exception as e:
                logger.debug(f"Sensation integration failed: {e}")
        
        # Determine semantic role based on control quality (Method axis)
        control_quality = obj_data.get('control_correlation', 0.0)
        
        if control_quality > 0.8:
            # High control = likely self
            interpretation['semantic_role'] = 'self'
            interpretation['is_self'] = True
            interpretation['meaning_confidence'] = control_quality
            interpretation['attraction'] = 0.0  # Neutral - we ARE this
        elif control_quality > 0.5:
            # Medium control = tool we can use
            interpretation['semantic_role'] = 'tool'
            interpretation['is_tool'] = True
            interpretation['meaning_confidence'] = control_quality * 0.8
            interpretation['attraction'] = 0.3  # Mild approach
        elif interpretation['threat_level'] > 0.5:
            # High threat = obstacle
            interpretation['semantic_role'] = 'obstacle'
            interpretation['meaning_confidence'] = interpretation['threat_level']
            interpretation['attraction'] = -0.8  # Strong avoid
        elif interpretation['goal_relevance'] > 0.5:
            # High goal relevance = target
            interpretation['semantic_role'] = 'goal'
            interpretation['meaning_confidence'] = interpretation['goal_relevance']
            interpretation['attraction'] = 0.9  # Strong approach
        else:
            # Default: environmental object
            interpretation['semantic_role'] = 'environmental'
            interpretation['meaning_confidence'] = 0.3
            interpretation['attraction'] = sensation_score * 0.3  # Mild bias from sensation
        
        # Check against goal context for goal relevance
        goal_positions = goal_context.get('goal_positions', [])
        obj_position = obj_data.get('position')
        
        if obj_position and goal_positions:
            # Check if this object is at or near a goal position
            for goal_pos in goal_positions:
                if obj_position == goal_pos:
                    interpretation['goal_relevance'] = 1.0
                    interpretation['is_goal'] = True
                    interpretation['semantic_role'] = 'goal'
                    interpretation['attraction'] = 1.0
                    interpretation['meaning_confidence'] = 0.9
                    break
        
        # Final attraction calculation: combine all signals
        interpretation['attraction'] = max(-1.0, min(1.0, (
            interpretation['goal_relevance'] * 0.5 +
            sensation_score * 0.2 -
            interpretation['threat_level'] * 0.5 +
            (0.2 if interpretation['is_tool'] else 0.0)
        )))
        
        return interpretation
    
    def build_tetrahedral_object(
        self,
        agent_id: str,
        obj_color: int,
        positions: List[Tuple[int, int]],
        game_id: str,
        level: int,
        frame: Optional[List] = None,
        sensation_engine: Any = None
    ) -> Dict[str, Any]:
        """
        Build a complete tetrahedral perception for an object.
        
        Integrates all four axes:
        - Structure (A): What it IS
        - Function (B): What it DOES
        - Method (C): HOW it operates
        - Interpretation (D): WHAT IT MEANS
        
        Args:
            agent_id: Agent identifier
            obj_color: Object color value
            positions: List of (row, col) positions for this object
            game_id: Game identifier
            level: Level number
            frame: Current game frame
            sensation_engine: Optional SensationEngine
            
        Returns:
            Complete tetrahedral object perception
        """
        # STRUCTURE AXIS (A) - What it IS
        structure = {
            'color': obj_color,
            'positions': positions[:10],  # Limit for size
            'cell_count': len(positions),
            'stability': 1.0,  # Assume stable unless tracked otherwise
            'centroid': (
                sum(p[0] for p in positions) / len(positions) if positions else 0,
                sum(p[1] for p in positions) / len(positions) if positions else 0
            )
        }
        
        # FUNCTION AXIS (B) - What it DOES
        function = {
            'responds_to_actions': [],
            'effect': 'unknown',
            'reactivity': 0.0,
            'known_effects': []
        }
        
        try:
            # Query collision effects for this color
            effects = self.db.execute_query("""
                SELECT effect_type, confidence, occurrence_count
                FROM collision_effects
                WHERE game_type = ? AND level_number = ? 
                  AND (controlled_object_color = ? OR target_object_color = ?)
                ORDER BY confidence DESC LIMIT 5
            """, (game_id, level, obj_color, obj_color))
            
            if effects:
                function['known_effects'] = [
                    {'type': e['effect_type'], 'confidence': e['confidence']}
                    for e in effects
                ]
                function['reactivity'] = len(effects) / 5.0  # Normalize
        except Exception:
            pass
        
        # METHOD AXIS (C) - HOW it operates
        method = {
            'is_controlled': False,
            'control_correlation': 0.0,
            'action_response_map': {},
            'intentionality': 0.0  # 0 = passive, 1 = autonomous
        }
        
        try:
            # Check if this color is in controlled objects
            controlled = self.get_controlled_objects(agent_id, game_id, level)
            if controlled:
                for coord in controlled:
                    # Parse coordinate and check if it matches this object's positions
                    try:
                        parts = coord.split(',')
                        x = int(parts[0].replace('x:', ''))
                        y = int(parts[1].replace('y:', ''))
                        if (y, x) in positions:
                            method['is_controlled'] = True
                            method['control_correlation'] = 0.8
                            break
                    except Exception:
                        pass
            
            # Check for autonomous movement patterns
            autonomous = self.db.execute_query("""
                SELECT movement_pattern, moves_per_turn, is_ever_controllable
                FROM autonomous_objects
                WHERE game_type = ? AND level_number = ? AND object_color = ?
            """, (game_id, level, obj_color))
            
            if autonomous:
                a = autonomous[0]
                method['intentionality'] = a['moves_per_turn'] if a['moves_per_turn'] else 0.0
                if a['is_ever_controllable']:
                    method['is_controlled'] = True
        except Exception:
            pass
        
        # INTERPRETATION AXIS (D) - WHAT IT MEANS (The Void)
        interpretation = self.calculate_interpretation_axis(
            agent_id,
            {
                'color': obj_color,
                'position': structure['centroid'],
                'control_correlation': method['control_correlation']
            },
            {'goal_positions': []},  # Will be populated by caller if available
            sensation_engine
        )
        
        return {
            'structure': structure,
            'function': function,
            'method': method,
            'interpretation': interpretation
        }
    
    def calculate_mood_vector(self, tetrahedral_perception: Dict[str, Dict]) -> str:
        """
        Calculate agent's decision mood from tetrahedral perception balance.
        
        From McGuffin's decision framework:
        - Driven: One axis dominant - focused action
        - Balanced: Two axes compete - careful action
        - Diffuse: Three axes equal - exploratory
        - Conflict: Void axis outlying - hesitate
        
        Args:
            tetrahedral_perception: Dict of object_key -> tetrahedral object
            
        Returns:
            Mood state: 'driven', 'balanced', 'diffuse', or 'conflict'
        """
        if not tetrahedral_perception:
            return 'diffuse'
        
        # Aggregate weights across all perceived objects
        structure_weight = 0.0
        function_weight = 0.0
        method_weight = 0.0
        interpretation_weight = 0.0
        obj_count = 0
        
        for obj_key, obj_data in tetrahedral_perception.items():
            structure = obj_data.get('structure', {})
            function = obj_data.get('function', {})
            method = obj_data.get('method', {})
            interpretation = obj_data.get('interpretation', {})
            
            structure_weight += structure.get('stability', 0.5)
            function_weight += function.get('reactivity', 0.5)
            method_weight += method.get('control_correlation', 0.5)
            interpretation_weight += interpretation.get('goal_relevance', 0.5)
            obj_count += 1
        
        if obj_count == 0:
            return 'diffuse'
        
        # Normalize
        weights = [
            structure_weight / obj_count,
            function_weight / obj_count,
            method_weight / obj_count,
            interpretation_weight / obj_count
        ]
        
        max_w, min_w = max(weights), min(weights)
        spread = max_w - min_w
        
        # Check if void (interpretation) is outlying
        void_weight = interpretation_weight / obj_count
        other_avg = (structure_weight + function_weight + method_weight) / (obj_count * 3)
        void_deviation = abs(void_weight - other_avg)
        
        if void_deviation > 0.4:
            return 'conflict'  # Void axis misaligned - internal struggle
        elif spread > 0.5:
            return 'driven'    # One axis dominates - focused action
        elif spread > 0.3:
            return 'balanced'  # Two axes compete - careful action
        else:
            return 'diffuse'   # All axes similar - exploratory
    
    def build_control_map(
        self,
        agent_id: str,
        game_id: str,
        gameplay_data: Dict
    ) -> Dict[int, List[str]]:
        """
        Build complete control map for all levels in a game.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            gameplay_data: Complete gameplay data with actions and frames
        
        Returns:
            Dictionary mapping level -> controlled objects
        """
        control_map = {}
        
        for level_data in gameplay_data.get('levels', []):
            level = level_data.get('level_number')
            actions = level_data.get('actions', [])
            frames = level_data.get('frames', [])
            
            if level is None or not actions or not frames:
                continue
            
            controlled, confidence = self.identify_controlled_objects(
                game_id, level, actions, frames
            )
            
            if controlled and confidence > 0.5:
                control_map[level] = controlled
                self.store_control_map(agent_id, game_id, level, controlled, confidence)
        
        return control_map
    
    # ========================================================================
    # NETWORK KNOWLEDGE SHARING: "I AM THIS OBJECT" HYPOTHESES
    # ========================================================================
    
    # ------------------------------------------------------------------
    # Few-shot relational patterns (SequenceAbstraction bridge)
    # ------------------------------------------------------------------
    def _get_abstraction_engine(self):
        """Lazy init abstraction engine; returns None if unavailable."""
        if self._abstraction_engine or self._abstraction_unavailable:
            return self._abstraction_engine
        try:
            from sequence_abstraction import SequenceAbstraction
            self._abstraction_engine = SequenceAbstraction(self.db_path)
            return self._abstraction_engine
        except Exception as exc:
            logger.debug(f"Abstraction engine unavailable for self-model: {exc}")
            self._abstraction_unavailable = True
            return None

    def get_few_shot_control_relations(
        self,
        game_id: str,
        level: int,
        min_confidence: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Expose few-shot invariants/variants from sequence abstraction for control bootstrapping.
        Returns None if insufficient data or low confidence.
        """
        engine = self._get_abstraction_engine()
        if not engine:
            return None

        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        relations = engine.get_few_shot_relations(game_type, level)

        if not relations or relations.get("confidence", 0.0) < min_confidence:
            return None
        return relations

    def share_control_discovery_to_network(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, List[str]],
        confidence: float,
        generation: int = 0
    ) -> Optional[str]:
        """
        Share "I am this object" discovery to network for other agents to validate.
        
        This is the core of network-level self-model learning:
        - Agent discovers which objects it controls
        - Shares hypothesis to network
        - Other agents validate during their gameplay
        - High-reliability patterns become network knowledge
        
        Args:
            agent_id: Discovering agent
            game_id: Game where discovery was made
            level: Level number
            controlled_objects: Coordinates of controlled objects
            action_response_map: Maps action types to responding coordinates
            confidence: Discovery confidence
            generation: Current evolution generation
        
        Returns:
            hypothesis_id if shared, None if already exists or low confidence
        """
        if confidence < 0.6 or not controlled_objects:
            return None
        
        # Extract game type (e.g., 'ft09' from 'ft09-abc123')
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Create control pattern signature for deduplication
        pattern_signature = self._create_pattern_signature(controlled_objects, action_response_map)
        
        # Check if similar hypothesis already exists
        existing = self.db.execute_query("""
            SELECT hypothesis_id, validation_attempts, reliability_score
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? AND control_pattern = ? AND is_active = TRUE
        """, (game_type, level, pattern_signature))
        
        if existing:
            # Update existing with validation attempt
            return existing[0]['hypothesis_id']
        
        # Create new hypothesis
        hypothesis_id = f"oc_{game_type}_L{level}_{uuid.uuid4().hex[:8]}"
        
        self.db.execute_query("""
            INSERT INTO network_object_control_hypotheses
            (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
             discovered_by_agent, discovery_generation, reliability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hypothesis_id,
            game_type,
            level,
            pattern_signature,
            json.dumps(action_response_map),
            agent_id,
            generation,
            confidence  # Initial reliability = discovery confidence
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} shared 'I am object' hypothesis: "
            f"{hypothesis_id} for {game_type} L{level} ({len(controlled_objects)} objects)"
        )
        
        return hypothesis_id
    
    def learn_from_movement_correlation(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        action: str,
        direction: str,
        controlled_color: int,
        generation: int = 0
    ) -> None:
        """
        Learn object control from action-movement correlation.
        
        When frame_changes show "color_X moved [direction]" after an action
        that corresponds to that direction, we learn that we control color_X.
        
        This is the core "I am this object" learning mechanism.
        
        Args:
            agent_id: Agent making the discovery
            game_id: Game identifier
            level: Level number
            action: Action taken (e.g., ACTION3)
            direction: Direction object moved (e.g., "left")
            controlled_color: Color number that moved
            generation: Current evolution generation
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Create control pattern
        control_pattern = {
            'discovery_type': 'movement_correlation',
            'controlled_color': controlled_color,
            'action': action,
            'direction': direction
        }
        
        # Build action-response map
        action_response = {action: direction}
        
        # Check if we already have this knowledge
        existing = self.db.execute_query("""
            SELECT hypothesis_id, reliability_score, validation_attempts
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND control_pattern LIKE ? AND is_active = TRUE
        """, (game_type, level, f'%"controlled_color": {controlled_color}%'))
        
        if existing:
            # Update existing - increase reliability only if direction matches
            row = existing[0]
            current_attempts = row['validation_attempts'] or 0
            
            # Check if this observation matches existing pattern
            # (same action should produce same direction)
            try:
                existing_pattern = self.db.execute_query("""
                    SELECT action_response_map FROM network_object_control_hypotheses
                    WHERE hypothesis_id = ?
                """, (row['hypothesis_id'],))
                if existing_pattern:
                    existing_responses = json.loads(existing_pattern[0]['action_response_map'])
                    expected_direction = existing_responses.get(action)
                    
                    if expected_direction and expected_direction != direction:
                        # CONTRADICTION: Same action, different direction = spurious correlation
                        # This might be an NPC or environmental animation
                        self.db.execute_query("""
                            UPDATE network_object_control_hypotheses
                            SET validation_attempts = validation_attempts + 1,
                                reliability_score = MAX(0.1, reliability_score - 0.15),
                                last_validated = CURRENT_TIMESTAMP
                            WHERE hypothesis_id = ?
                        """, (row['hypothesis_id'],))
                        logger.warning(
                            f"[MOVEMENT] CONTRADICTION: {action} moved color_{controlled_color} {direction} "
                            f"but expected {expected_direction} - lowering reliability"
                        )
                        return  # Don't update with contradictory data
            except Exception as e:
                logger.debug(f"Pattern comparison failed: {e}")
            
            # Consistent observation - increase reliability
            new_reliability = min(0.95, row['reliability_score'] + 0.1)
            self.db.execute_query("""
                UPDATE network_object_control_hypotheses
                SET reliability_score = ?,
                    validation_attempts = validation_attempts + 1,
                    validation_successes = validation_successes + 1,
                    last_validated = CURRENT_TIMESTAMP
                WHERE hypothesis_id = ?
            """, (new_reliability, row['hypothesis_id']))
            
            # Only log as validated after 3+ consistent observations
            if current_attempts + 1 >= 3:
                logger.info(
                    f"[MOVEMENT] VALIDATED (x{current_attempts + 1}): color_{controlled_color} "
                    f"responds to {action} with {direction} (reliability {new_reliability:.2f})"
                )
            else:
                logger.debug(f"[MOVEMENT] Observation {current_attempts + 1}/3 for color_{controlled_color}")
        else:
            # Create new hypothesis with LOW initial confidence
            # Correlation != Causation - need multiple observations to validate
            hypothesis_id = self._generate_hypothesis_id()
            self.db.execute_query("""
                INSERT INTO network_object_control_hypotheses
                (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
                 discovered_by_agent, discovery_generation, reliability_score, discovery_method,
                 validation_attempts, validation_successes)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.3, 'movement_correlation', 1, 1)
            """, (
                hypothesis_id, game_type, level, json.dumps(control_pattern),
                json.dumps(action_response), agent_id, generation
            ))
            logger.debug(
                f"[MOVEMENT] Observation 1/3: {action} may control color_{controlled_color} "
                f"(needs {2} more consistent observations)"
            )
        
        # Also store in agent's personal control map
        try:
            self.store_control_map(
                agent_id=agent_id,
                game_id=game_id,
                level=level,
                controlled=[(controlled_color, action, direction)],
                confidence=0.75
            )
        except Exception as e:
            logger.debug(f"Personal control map update failed: {e}")

    def get_network_control_hypotheses(
        self,
        game_id: str,
        level: int,
        min_reliability: float = 0.3
    ) -> List[Dict]:
        """
        Get network-validated "I am this object" hypotheses for a game/level.
        
        Use this to bootstrap agent self-model with network knowledge.
        
        Args:
            game_id: Game identifier
            level: Level number
            min_reliability: Minimum reliability score to return
        
        Returns:
            List of hypothesis dictionaries with control patterns and reliability
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # CORRELATION != CAUSATION FILTER
        # Only return hypotheses that have been validated at least 3 times
        # with consistent results. Single observations could be spurious.
        # TIER 5 - SELECTION: Order by outcome (best_score_achieved) not just validation
        results = self.db.execute_query("""
            SELECT 
                hypothesis_id,
                control_pattern,
                action_response_map,
                reliability_score,
                validation_attempts,
                validation_successes,
                validated_by_win,
                COALESCE(best_score_achieved, 0) as best_score_achieved
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND is_active = TRUE 
                  AND reliability_score >= ?
                  AND (validation_attempts >= 3 OR validated_by_win = TRUE)
            ORDER BY validated_by_win DESC, 
                     best_score_achieved DESC, 
                     reliability_score DESC
            LIMIT 5
        """, (game_type, level, min_reliability))
        
        hypotheses = []
        for row in results or []:
            hypotheses.append({
                'hypothesis_id': row['hypothesis_id'],
                'controlled_objects': json.loads(row['control_pattern']) if row['control_pattern'].startswith('[') else row['control_pattern'].split(','),
                'action_response_map': json.loads(row['action_response_map']) if row['action_response_map'] else {},
                'reliability': row['reliability_score'],
                'validation_count': row['validation_attempts'],
                'success_rate': row['validation_successes'] / max(1, row['validation_attempts']),
                'validated_by_win': row['validated_by_win'],
                'best_score_achieved': row['best_score_achieved']  # TIER 5 - competition by outcome
            })
        
        # TIER 6 - SYNTHESIS: If we have multiple moderate-reliability hypotheses
        # but none with high confidence, try to synthesize a composite
        if len(hypotheses) >= 2 and all(h['reliability'] < 0.8 for h in hypotheses):
            composite = self.synthesize_composite_hypothesis(game_id, level)
            if composite and composite.get('hypothesis_id') not in [h['hypothesis_id'] for h in hypotheses]:
                # Insert composite at the front (highest priority)
                hypotheses.insert(0, {
                    'hypothesis_id': composite['hypothesis_id'],
                    'controlled_objects': composite.get('control_pattern', '').split(',') if isinstance(composite.get('control_pattern'), str) else [],
                    'action_response_map': composite.get('action_map', {}),
                    'reliability': composite.get('reliability', 0.5),
                    'validation_count': 0,
                    'success_rate': 0.0,
                    'validated_by_win': False,
                    'best_score_achieved': 0,
                    'is_composite': True
                })
        
        return hypotheses
    
    def validate_control_hypothesis(
        self,
        hypothesis_id: str,
        success: bool,
        validated_by_win: bool = False
    ):
        """
        Record validation result for a network control hypothesis.
        
        Called when an agent uses a network hypothesis and succeeds/fails.
        Updates Bayesian reliability score.
        
        Args:
            hypothesis_id: Hypothesis being validated
            success: Whether the hypothesis helped (True) or failed (False)
            validated_by_win: Whether validation came from level/game win
        """
        # Get current stats
        current = self.db.execute_query("""
            SELECT validation_attempts, validation_successes, validation_failures, reliability_score
            FROM network_object_control_hypotheses
            WHERE hypothesis_id = ?
        """, (hypothesis_id,))
        
        if not current:
            return
        
        row = current[0]
        attempts = row['validation_attempts'] + 1
        successes = row['validation_successes'] + (1 if success else 0)
        failures = row['validation_failures'] + (0 if success else 1)
        
        # Bayesian reliability update with prior
        prior_successes = 1  # Weak prior
        prior_total = 2
        reliability = (successes + prior_successes) / (attempts + prior_total)
        
        # Mark validated_by_win if this validation was from a win
        win_flag = validated_by_win or row.get('validated_by_win', False)
        
        # Deactivate if reliability drops too low
        is_active = reliability >= 0.2
        
        self.db.execute_query("""
            UPDATE network_object_control_hypotheses
            SET validation_attempts = ?,
                validation_successes = ?,
                validation_failures = ?,
                reliability_score = ?,
                validated_by_win = ?,
                is_active = ?,
                last_validated = CURRENT_TIMESTAMP
            WHERE hypothesis_id = ?
        """, (attempts, successes, failures, reliability, win_flag, is_active, hypothesis_id))
        
        if not is_active:
            logger.info(f"[NETWORK] Control hypothesis {hypothesis_id} deactivated (reliability: {reliability:.2f})")
    
    def synthesize_composite_hypothesis(
        self,
        game_id: str,
        level: int
    ) -> Optional[Dict]:
        """
        TIER 6 - SYNTHESIS: Combine validated hypotheses into composite strategies.
        
        This is the highest tier of the thought process colony. When multiple
        validated hypotheses exist for a game/level, this method:
        1. Queries all validated hypotheses
        2. Identifies complementary patterns (e.g., control + goal)
        3. Creates a composite hypothesis combining them
        4. Stores composite with references to source hypotheses
        
        A composite hypothesis answers: "I control X, and my goal is Y"
        rather than just "I control X" or "Y is the goal".
        
        Args:
            game_id: Game identifier
            level: Level number
            
        Returns:
            Composite hypothesis dict if synthesis successful, None otherwise
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Get all validated hypotheses for this game/level
        validated = self.db.execute_query("""
            SELECT 
                hypothesis_id,
                control_pattern,
                action_response_map,
                reliability_score,
                validation_attempts,
                best_score_achieved
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ?
                  AND is_active = TRUE
                  AND reliability_score >= 0.5
                  AND (validation_attempts >= 3 OR validated_by_win = TRUE)
            ORDER BY best_score_achieved DESC, reliability_score DESC
            LIMIT 10
        """, (game_type, level))
        
        if not validated or len(validated) < 2:
            # Need at least 2 hypotheses to synthesize
            return None
        
        # Group hypotheses by pattern type
        control_hypotheses = []
        goal_hypotheses = []
        
        for row in validated:
            try:
                action_map = json.loads(row['action_response_map']) if row['action_response_map'] else {}
                hypothesis = {
                    'id': row['hypothesis_id'],
                    'control_pattern': row['control_pattern'],
                    'action_map': action_map,
                    'reliability': row['reliability_score'],
                    'best_score': row.get('best_score_achieved', 0)
                }
                
                # Classify: control hypotheses have directional mappings
                if any(k in str(action_map) for k in ['up', 'down', 'left', 'right', 'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']):
                    control_hypotheses.append(hypothesis)
                else:
                    goal_hypotheses.append(hypothesis)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if not control_hypotheses:
            return None
        
        # Create composite: best control + any complementary patterns
        best_control = control_hypotheses[0]
        
        # Check if composite already exists
        composite_id = f"composite_{game_type}_{level}_{best_control['id'][:8]}"
        existing = self.db.execute_query("""
            SELECT hypothesis_id FROM network_object_control_hypotheses
            WHERE hypothesis_id = ?
        """, (composite_id,))
        
        if existing:
            # Composite already exists, return it
            return {
                'hypothesis_id': composite_id,
                'is_composite': True,
                'source_hypotheses': [best_control['id']],
                'reliability': best_control['reliability']
            }
        
        # Build composite action map
        composite_action_map = dict(best_control['action_map'])
        source_ids = [best_control['id']]
        
        # Add complementary patterns from other hypotheses
        for h in control_hypotheses[1:3]:  # Limit to top 3
            for key, value in h['action_map'].items():
                if key not in composite_action_map:
                    composite_action_map[key] = value
                    source_ids.append(h['id'])
        
        # Calculate composite reliability (weighted average)
        total_weight = sum(h['reliability'] for h in control_hypotheses[:3])
        composite_reliability = total_weight / min(3, len(control_hypotheses))
        
        # Store composite hypothesis
        try:
            self.db.execute_query("""
                INSERT INTO network_object_control_hypotheses
                (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
                 discovered_by_agent, discovery_generation, validation_attempts, 
                 validation_successes, reliability_score, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, TRUE)
            """, (
                composite_id,
                game_type,
                level,
                best_control['control_pattern'],
                json.dumps(composite_action_map),
                f"synthesis_from_{len(source_ids)}_sources",
                self.db.get_generation() if hasattr(self.db, 'get_generation') else 0,
                composite_reliability
            ))
            
            logger.info(f"[TIER-6] Synthesized composite hypothesis {composite_id} from {len(source_ids)} sources")
            
            return {
                'hypothesis_id': composite_id,
                'is_composite': True,
                'source_hypotheses': source_ids,
                'control_pattern': best_control['control_pattern'],
                'action_map': composite_action_map,
                'reliability': composite_reliability
            }
        except Exception as e:
            logger.debug(f"Failed to store composite hypothesis: {e}")
            return None
    
    def _create_pattern_signature(self, controlled_objects: List[str], action_map: Dict) -> str:
        """
        Create a signature for deduplication of similar patterns.
        
        Uses sorted coordinates to ensure consistent comparison.
        """
        sorted_objects = sorted(controlled_objects)
        return json.dumps(sorted_objects)
    
    # =========================================================================
    # ACTION5 BEHAVIOR MAPPING (Network-Level Knowledge)
    # =========================================================================
    
    def save_action5_behavior(
        self,
        game_type: str,
        level: int,
        behavior_type: str,
        affected_objects: List[str],
        effect_description: str,
        confidence: float
    ) -> None:
        """
        Save discovered ACTION5 behavior to network-level knowledge.
        
        This allows all agents to benefit from one agent's discovery
        of what ACTION5 does in a particular game type.
        
        Args:
            game_type: The game type (e.g., "tetris_variant")
            level: Level number where behavior was observed
            behavior_type: Type of behavior (rotation, toggle, interact, select, etc.)
            affected_objects: List of object color IDs affected
            effect_description: Human-readable description of the effect
            confidence: Confidence level (0.0 to 1.0)
        """
        existing = self.db.execute_query("""
            SELECT confidence, discovery_count FROM action5_behavior_map
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level))
        
        affected_str = ",".join(str(o) for o in affected_objects) if affected_objects else ""
        
        if existing:
            # Update with weighted average confidence
            row = existing[0]
            old_conf = row['confidence']
            count = row['discovery_count']
            new_count = count + 1
            new_conf = (old_conf * count + confidence) / new_count
            
            self.db.execute_query("""
                UPDATE action5_behavior_map
                SET behavior_type = ?,
                    affected_objects = ?,
                    effect_description = ?,
                    confidence = ?,
                    discovery_count = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ?
            """, (behavior_type, affected_str, effect_description, new_conf, new_count, game_type, level))
            
            logger.debug(f"[ACTION5] Updated behavior for {game_type} L{level}: {behavior_type} (conf: {new_conf:.2f}, count: {new_count})")
        else:
            # Insert new discovery
            self.db.execute_query("""
                INSERT INTO action5_behavior_map
                (game_type, level_number, behavior_type, affected_objects, effect_description, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_type, level, behavior_type, affected_str, effect_description, confidence))
            
            logger.info(f"[ACTION5] New behavior discovered for {game_type} L{level}: {behavior_type}")
    
    def get_action5_behavior(self, game_type: str, level: int) -> Optional[Dict]:
        """
        Retrieve known ACTION5 behavior for a game type and level.
        
        Returns:
            Dict with behavior_type, affected_objects, effect_description, confidence
            or None if no behavior known
        """
        result = self.db.execute_query("""
            SELECT behavior_type, affected_objects, effect_description, confidence
            FROM action5_behavior_map
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level))
        
        if result:
            row = result[0]
            return {
                'behavior_type': row['behavior_type'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            }
        return None
    
    def classify_action5_effect(self, action5_effects: Dict, game_type: str, level: int) -> str:
        """
        Classify what ACTION5 does based on observed effects.
        
        Analyzes the tracked effects and determines the behavior type.
        Also saves the discovery to network knowledge.
        
        Args:
            action5_effects: Dict from identify_controlled_objects tracking
            game_type: Game type for storing
            level: Level number
        
        Returns:
            Behavior type string (rotation, toggle, interact, select, unknown)
        """
        if not action5_effects:
            return "unknown"
        
        # Analyze the effects
        total_observations = 0
        position_changes = 0
        affected_ids = []
        
        for obj_id, effects in action5_effects.items():
            if effects['total'] < 1:
                continue
            
            total_observations += effects['total']
            
            if effects['changes'] > 0:
                affected_ids.append(str(obj_id))
                
                # Analyze what kind of changes occurred
                if effects.get('positions'):
                    # If object moved significantly, it's position change
                    position_changes += 1
                
        if total_observations < 2:
            return "unknown"
        
        # Determine behavior type based on patterns
        behavior_type = "interact"  # Default
        effect_description = "ACTION5 affects objects in this level"
        
        change_rate = len(affected_ids) / len(action5_effects) if action5_effects else 0
        
        if change_rate > 0.5:
            # Most objects change - likely global effect
            behavior_type = "toggle"
            effect_description = f"ACTION5 toggles/transforms multiple objects (affects {len(affected_ids)} objects)"
        elif change_rate > 0.0 and len(affected_ids) <= 2:
            # One or two objects change - likely rotation or select
            if position_changes > 0:
                behavior_type = "rotation"
                effect_description = f"ACTION5 rotates object {affected_ids[0] if affected_ids else 'unknown'}"
            else:
                behavior_type = "select"
                effect_description = f"ACTION5 selects or activates object {affected_ids[0] if affected_ids else 'unknown'}"
        
        # Save to network knowledge
        confidence = min(0.9, total_observations / 10)  # More observations = higher confidence
        self.save_action5_behavior(
            game_type=game_type,
            level=level,
            behavior_type=behavior_type,
            affected_objects=affected_ids,
            effect_description=effect_description,
            confidence=confidence
        )
        
        return behavior_type
    
    # =========================================================================
    # ACTION6 PSEUDO BUTTON BEHAVIOR (Network-Level Knowledge)
    # =========================================================================
    
    def save_pseudo_button_behavior(
        self,
        game_type: str,
        level: int,
        region_x: int,
        region_y: int,
        produces_action: str,
        movement_direction: str,
        affected_objects: List[str],
        effect_description: str,
        confidence: float
    ) -> None:
        """
        Save discovered pseudo button behavior to network-level knowledge.
        
        When agents discover what clicking a screen region does,
        share it so other agents can use the pseudo buttons effectively.
        
        Args:
            game_type: The game type
            level: Level number
            region_x, region_y: Screen region (0-7 each, dividing 64x64 into 8x8)
            produces_action: Equivalent action (e.g., 'up', 'down', 'toggle')
            movement_direction: Direction of movement if any
            affected_objects: Object IDs affected by this button
            effect_description: Human-readable description
            confidence: Confidence level (0.0 to 1.0)
        """
        existing = self.db.execute_query("""
            SELECT confidence, discovery_count FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))
        
        affected_str = ",".join(str(o) for o in affected_objects) if affected_objects else ""
        
        if existing:
            row = existing[0]
            old_conf = row['confidence']
            count = row['discovery_count']
            new_count = count + 1
            new_conf = (old_conf * count + confidence) / new_count
            
            self.db.execute_query("""
                UPDATE pseudo_button_behavior
                SET produces_action = ?,
                    movement_direction = ?,
                    affected_objects = ?,
                    effect_description = ?,
                    confidence = ?,
                    discovery_count = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
            """, (produces_action, movement_direction, affected_str, effect_description,
                  new_conf, new_count, game_type, level, region_x, region_y))
            
            logger.debug(f"[BUTTON] Updated region ({region_x},{region_y}) for {game_type} L{level}: {produces_action}")
        else:
            self.db.execute_query("""
                INSERT INTO pseudo_button_behavior
                (game_type, level_number, region_x, region_y, produces_action,
                 movement_direction, affected_objects, effect_description, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_type, level, region_x, region_y, produces_action,
                  movement_direction, affected_str, effect_description, confidence))
            
            logger.info(f"[BUTTON] New pseudo button at ({region_x},{region_y}) for {game_type} L{level}: {produces_action}")
    
    def get_pseudo_button_behavior(self, game_type: str, level: int, region_x: int, region_y: int) -> Optional[Dict]:
        """
        Retrieve known pseudo button behavior for a specific screen region.
        
        Returns:
            Dict with produces_action, movement_direction, affected_objects, confidence
            or None if no behavior known
        """
        result = self.db.execute_query("""
            SELECT produces_action, movement_direction, affected_objects, effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))
        
        if result:
            row = result[0]
            return {
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            }
        return None
    
    def get_all_pseudo_buttons(self, game_type: str, level: int, min_confidence: float = 0.5) -> List[Dict]:
        """
        Get all known pseudo buttons for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of pseudo button dicts with region coords and behavior
        """
        results = self.db.execute_query("""
            SELECT region_x, region_y, produces_action, movement_direction, 
                   affected_objects, effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))
        
        buttons = []
        for row in results or []:
            buttons.append({
                'region_x': row['region_x'],
                'region_y': row['region_y'],
                'screen_x_range': (row['region_x'] * 8, row['region_x'] * 8 + 7),
                'screen_y_range': (row['region_y'] * 8, row['region_y'] * 8 + 7),
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            })
        return buttons
    
    def classify_pseudo_button_effects(
        self,
        action6_region_effects: Dict,
        game_type: str,
        level: int
    ) -> Dict[Tuple[int, int], str]:
        """
        Classify and save pseudo button behaviors based on tracked effects.
        
        Analyzes what each screen region does when clicked and saves
        the discoveries to network knowledge.
        
        Args:
            action6_region_effects: Dict from identify_controlled_objects tracking
            game_type: Game type for storing
            level: Level number
        
        Returns:
            Dict mapping (region_x, region_y) -> behavior description
        """
        classified = {}
        
        for region_key, effects in action6_region_effects.items():
            region_x, region_y = region_key
            
            if effects['total'] < 2:
                continue  # Not enough samples
            
            # Determine dominant effect
            directions = {
                'up': effects['up'],
                'down': effects['down'],
                'left': effects['left'],
                'right': effects['right']
            }
            
            max_direction = max(directions.items(), key=lambda x: x[1])
            toggle_count = effects['toggle']
            no_effect_count = effects['no_effect']
            total = effects['total']
            
            # Determine what this button does
            if no_effect_count > total * 0.7:
                # Mostly no effect - not a useful button
                continue
            
            affected_list = list(effects['affected_objects'])
            
            if toggle_count > max_direction[1] and toggle_count > total * 0.3:
                # Toggle behavior dominates
                produces_action = 'toggle'
                movement_direction = 'none'
                effect_desc = f"Clicking region ({region_x},{region_y}) toggles/spawns objects"
            elif max_direction[1] > total * 0.4:
                # Directional movement dominates
                produces_action = f'move_{max_direction[0]}'
                movement_direction = max_direction[0]
                effect_desc = f"Clicking region ({region_x},{region_y}) moves objects {max_direction[0]}"
            else:
                # Mixed or unclear effect
                produces_action = 'interact'
                movement_direction = 'mixed'
                effect_desc = f"Clicking region ({region_x},{region_y}) has mixed effects"
            
            confidence = min(0.9, effects['total'] / 10)
            
            # Save to network
            self.save_pseudo_button_behavior(
                game_type=game_type,
                level=level,
                region_x=region_x,
                region_y=region_y,
                produces_action=produces_action,
                movement_direction=movement_direction,
                affected_objects=affected_list,
                effect_description=effect_desc,
                confidence=confidence
            )
            
            classified[region_key] = produces_action
        
        return classified

    # ========================================================================
    # OBJECT SELECTION TRACKING (Added 2025-12-08)
    # ========================================================================
    # ACTION6 has two modes:
    # 1. Click "buttons" -> triggers events (handled by pseudo_button_behavior)
    # 2. Click "objects" -> SELECTS that object for control by ACTION1-4
    #
    # This section implements dynamic selection tracking:
    # - What object is currently selected?
    # - Which objects are selectable (can become controlled)?
    # - How does selection change what ACTION1-4 do?
    # ========================================================================
    
    def track_selection_change(
        self,
        session_id: str,
        game_id: str,
        level: int,
        action_index: int,
        action_type: str,
        click_x: Optional[int],
        click_y: Optional[int],
        frame_before: Dict,
        frame_after: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        Track if an ACTION6 click selected a new object for control.
        
        This is called after every ACTION6 to detect if clicking on an object
        caused it to become the "selected" object that ACTION1-4 will now move.
        
        Pattern detection:
        1. ACTION6 clicks at (x, y)
        2. Subsequent ACTION1-4 moves object at/near (x, y)
        3. Conclusion: ACTION6 selected that object
        
        Args:
            session_id: Current game session
            game_id: Game identifier
            level: Level number
            action_index: Which action in sequence
            action_type: Should be ACTION6 or similar
            click_x, click_y: Where was clicked (0-63 range)
            frame_before, frame_after: Frame data
        
        Returns:
            Selection info dict if selection detected, None otherwise
        """
        if click_x is None or click_y is None:
            return None
        
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return None
        
        # Find what object was clicked on
        clicked_object = self._get_object_at_coords(grid_before, click_x, click_y)
        
        if clicked_object is None or clicked_object == 0:
            # Clicked on background - might be a button area instead
            return None
        
        # Store the current selection
        self._update_current_selection(
            session_id=session_id,
            game_id=game_id,
            level=level,
            object_color=clicked_object,
            object_coords=f"({click_x},{click_y})",
            action_index=action_index
        )
        
        logger.debug(
            f"[SELECTION] Clicked on object color {clicked_object} at ({click_x},{click_y}) "
            f"- may now be selected for control"
        )
        
        return {
            'selected_object_color': clicked_object,
            'selected_coords': (click_x, click_y),
            'action_index': action_index,
            'game_type': game_type,
            'level': level
        }
    
    def verify_selection_controls_movement(
        self,
        session_id: str,
        game_id: str,
        level: int,
        movement_action: str,  # ACTION1-4
        frame_before: Dict,
        frame_after: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        Verify if the currently selected object moved in response to ACTION1-4.
        
        If the previously selected object (via ACTION6) moved when we used
        ACTION1-4, then we've confirmed the selection mechanism.
        
        Args:
            session_id: Current game session
            game_id: Game identifier  
            level: Level number
            movement_action: The action used (ACTION1, ACTION2, etc.)
            frame_before, frame_after: Frame data
        
        Returns:
            Verification result dict if selection was confirmed, None otherwise
        """
        # Get current selection
        current_selection = self.get_current_selection(session_id, game_id, level)
        
        if not current_selection:
            return None  # No object was selected
        
        selected_color = current_selection.get('selected_object_color')
        if selected_color is None:
            return None
        
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return None
        
        # Find positions of selected object before and after
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        if selected_color not in objects_before or selected_color not in objects_after:
            return None  # Object not found or disappeared
        
        positions_before = objects_before[selected_color]
        positions_after = objects_after[selected_color]
        
        # Calculate movement
        cx_before = sum(p[0] for p in positions_before) / len(positions_before)
        cy_before = sum(p[1] for p in positions_before) / len(positions_before)
        cx_after = sum(p[0] for p in positions_after) / len(positions_after)
        cy_after = sum(p[1] for p in positions_after) / len(positions_after)
        
        dx = cx_after - cx_before
        dy = cy_after - cy_before
        
        # Did it move?
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            return None  # Object didn't move
        
        # Determine movement direction
        movement_direction = None
        if abs(dy) > abs(dx):
            movement_direction = 'up' if dy < 0 else 'down'
        else:
            movement_direction = 'left' if dx < 0 else 'right'
        
        # Check if movement matches action
        action_to_expected_direction = {
            'ACTION1': 'up', 'action_1': 'up',
            'ACTION2': 'down', 'action_2': 'down',
            'ACTION3': 'left', 'action_3': 'left',
            'ACTION4': 'right', 'action_4': 'right',
        }
        
        expected = action_to_expected_direction.get(movement_action)
        movement_matches = (expected == movement_direction)
        
        if movement_matches:
            # Extract shape info from positions_before
            shape_info = None
            if positions_before:
                xs = [p[0] for p in positions_before]
                ys = [p[1] for p in positions_before]
                bbox_width = max(xs) - min(xs) + 1
                bbox_height = max(ys) - min(ys) + 1
                bbox_area = bbox_width * bbox_height
                density = len(positions_before) / bbox_area if bbox_area > 0 else 1.0
                shape_info = {
                    'width': bbox_width,
                    'height': bbox_height,
                    'density': density
                }
            
            # Confirmed: This object is selectable and moveable
            self._save_selectable_object(
                game_type=game_type,
                level=level,
                object_color=selected_color,
                object_coords=current_selection.get('selected_object_coords'),
                is_moveable=True,
                control_actions=[movement_action],
                confidence=0.8,
                shape_info=shape_info
            )
            
            logger.info(
                f"[SELECTION CONFIRMED] Object color {selected_color} "
                f"moved {movement_direction} on {movement_action} after selection"
            )
            
            return {
                'confirmed': True,
                'object_color': selected_color,
                'movement_direction': movement_direction,
                'action_used': movement_action,
                'game_type': game_type,
                'level': level
            }
        
        return None
    
    def get_current_selection(
        self,
        session_id: str,
        game_id: str,
        level: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected object for this session/game/level.
        
        Returns:
            Dict with selection info, or None if nothing selected
        """
        result = self.db.execute_query("""
            SELECT selected_object_color, selected_object_coords, selection_action_index
            FROM current_selection_tracking
            WHERE session_id = ? AND game_id = ? AND level_number = ?
        """, (session_id, game_id, level))
        
        if result and result[0]['selected_object_color'] is not None:
            return {
                'selected_object_color': result[0]['selected_object_color'],
                'selected_object_coords': result[0]['selected_object_coords'],
                'selection_action_index': result[0]['selection_action_index']
            }
        return None
    
    def _update_current_selection(
        self,
        session_id: str,
        game_id: str,
        level: int,
        object_color: int,
        object_coords: str,
        action_index: int
    ) -> None:
        """Update the currently selected object."""
        self.db.execute_query("""
            INSERT OR REPLACE INTO current_selection_tracking
            (session_id, game_id, level_number, selected_object_color, 
             selected_object_coords, selection_action_index, selection_time)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, game_id, level, object_color, object_coords, action_index))
    
    def clear_selection(self, session_id: str, game_id: str, level: int) -> None:
        """Clear the current selection (e.g., when level ends)."""
        self.db.execute_query("""
            DELETE FROM current_selection_tracking
            WHERE session_id = ? AND game_id = ? AND level_number = ?
        """, (session_id, game_id, level))
    
    def _get_object_at_coords(self, grid: List, x: int, y: int) -> Optional[int]:
        """Get the object color at specific coordinates."""
        if not grid:
            return None
        
        if 0 <= y < len(grid) and 0 <= x < len(grid[0] if grid else []):
            return grid[y][x]
        return None
    
    def _save_selectable_object(
        self,
        game_type: str,
        level: int,
        object_color: int,
        object_coords: Optional[str],
        is_moveable: bool,
        control_actions: List[str],
        confidence: float,
        shape_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a discovered selectable object to network knowledge.
        
        Args:
            game_type: Game type (e.g., 'sp80')
            level: Level number
            object_color: Color of the selectable object
            object_coords: "(x,y)" coordinates string
            is_moveable: Whether object responds to ACTION1-4
            control_actions: List of actions that control this object
            confidence: Discovery confidence
            shape_info: Optional dict with shape properties:
                - width: Bounding box width
                - height: Bounding box height
                - density: Fill density
                (Shape signature will be computed from these)
        """
        import json
        
        # Compute shape signature if shape_info provided
        shape_signature = None
        shape_width = None
        shape_height = None
        shape_density = None
        
        if shape_info:
            shape_width = shape_info.get('width')
            shape_height = shape_info.get('height')
            shape_density = shape_info.get('density', 1.0)
            
            if shape_width and shape_height:
                shape_signature = self.compute_shape_signature(
                    shape_width, shape_height, shape_density
                )
        
        # Check if entry exists
        existing = self.db.execute_query("""
            SELECT discovery_count, confidence, control_actions
            FROM object_selection_state
            WHERE game_type = ? AND level_number = ? AND object_color = ?
        """, (game_type, level, object_color))
        
        if existing:
            # Update existing entry
            old_count = existing[0]['discovery_count']
            old_confidence = existing[0]['confidence']
            old_actions = json.loads(existing[0]['control_actions'] or '[]')
            
            # Merge control actions
            merged_actions = list(set(old_actions + control_actions))
            
            # Bayesian confidence update
            new_confidence = (old_confidence * old_count + confidence) / (old_count + 1)
            
            # Build update query - include shape fields if we have them
            if shape_signature:
                self.db.execute_query("""
                    UPDATE object_selection_state
                    SET is_selectable = TRUE,
                        is_moveable = ?,
                        object_coordinates = COALESCE(?, object_coordinates),
                        control_actions = ?,
                        confidence = ?,
                        discovery_count = discovery_count + 1,
                        last_observed = CURRENT_TIMESTAMP,
                        shape_signature = COALESCE(?, shape_signature),
                        shape_width = COALESCE(?, shape_width),
                        shape_height = COALESCE(?, shape_height),
                        shape_density = COALESCE(?, shape_density)
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (is_moveable, object_coords, json.dumps(merged_actions), 
                      new_confidence, shape_signature, shape_width, shape_height,
                      shape_density, game_type, level, object_color))
            else:
                self.db.execute_query("""
                    UPDATE object_selection_state
                    SET is_selectable = TRUE,
                        is_moveable = ?,
                        object_coordinates = COALESCE(?, object_coordinates),
                        control_actions = ?,
                        confidence = ?,
                        discovery_count = discovery_count + 1,
                        last_observed = CURRENT_TIMESTAMP
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (is_moveable, object_coords, json.dumps(merged_actions), 
                      new_confidence, game_type, level, object_color))
        else:
            # Insert new entry with shape info
            self.db.execute_query("""
                INSERT INTO object_selection_state
                (game_type, level_number, object_color, object_coordinates,
                 is_selectable, is_moveable, is_button, control_actions, confidence,
                 shape_signature, shape_width, shape_height, shape_density)
                VALUES (?, ?, ?, ?, TRUE, ?, FALSE, ?, ?, ?, ?, ?, ?)
            """, (game_type, level, object_color, object_coords, 
                  is_moveable, json.dumps(control_actions), confidence,
                  shape_signature, shape_width, shape_height, shape_density))
        
        shape_msg = f" shape={shape_signature}" if shape_signature else ""
        logger.info(
            f"[NETWORK] Saved selectable object: {game_type} L{level} "
            f"color={object_color} moveable={is_moveable}{shape_msg}"
        )
    
    def get_selectable_objects(
        self,
        game_type: str,
        level: int,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get all known selectable objects for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of selectable object dicts
        """
        results = self.db.execute_query("""
            SELECT object_color, object_coordinates, is_moveable, 
                   control_actions, confidence
            FROM object_selection_state
            WHERE game_type = ? AND level_number = ? 
                  AND is_selectable = TRUE AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))
        
        objects = []
        for row in results or []:
            objects.append({
                'object_color': row['object_color'],
                'coordinates': row['object_coordinates'],
                'is_moveable': bool(row['is_moveable']),
                'control_actions': json.loads(row['control_actions'] or '[]'),
                'confidence': row['confidence']
            })
        return objects
    
    # =========================================================================
    # SHAPE-BASED GENERALIZATION (2025-12-27)
    # =========================================================================
    # Instead of just learning "color 9 is selectable", learn "horizontal bars
    # are selectable". This allows agents to enumerate ALL matching objects
    # on frontier levels, not just the specific color they saw before.
    # =========================================================================
    
    def compute_shape_signature(
        self,
        width: int,
        height: int,
        density: float = 1.0
    ) -> str:
        """
        Compute a shape signature from bounding box dimensions.
        
        Shape signatures allow generalization across colors:
        - "horizontal_bar": width >= 3 * height (wide and thin)
        - "vertical_bar": height >= 3 * width (tall and thin)
        - "square": 0.7 <= aspect <= 1.4 (roughly square)
        - "wide_rect": 1.4 < aspect < 3.0 (moderately wide)
        - "tall_rect": 0.33 < aspect < 0.7 (moderately tall)
        - "blob": density < 0.5 (sparse, non-rectangular)
        - "small": size < 4 pixels (too small to classify)
        
        Args:
            width: Bounding box width
            height: Bounding box height
            density: Fill density (cells / bbox_area), default 1.0
            
        Returns:
            Shape signature string
        """
        if width <= 0 or height <= 0:
            return "unknown"
        
        # Small objects are hard to classify
        if width * height < 4:
            return "small"
        
        # Sparse objects are "blobs"
        if density < 0.5:
            return "blob"
        
        aspect = width / height
        
        if aspect >= 3.0:
            return "horizontal_bar"
        elif aspect <= 0.33:
            return "vertical_bar"
        elif 0.7 <= aspect <= 1.4:
            return "square"
        elif aspect > 1.4:
            return "wide_rect"
        else:  # 0.33 < aspect < 0.7
            return "tall_rect"
    
    def get_selectable_shapes_for_game(
        self,
        game_type: str,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Get all shape signatures that are known to be selectable for a game type.
        
        This is the KEY method for generalization:
        - Query across ALL levels to find what shapes work
        - Returns shape signatures, not specific colors
        - Agents use this to enumerate objects on frontier levels
        
        Args:
            game_type: Game type to query (e.g., 'sp80')
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of dicts with shape_signature and aggregate stats
        """
        results = self.db.execute_query("""
            SELECT 
                shape_signature,
                COUNT(*) as occurrence_count,
                AVG(confidence) as avg_confidence,
                MAX(confidence) as max_confidence,
                GROUP_CONCAT(DISTINCT object_color) as colors_seen
            FROM object_selection_state
            WHERE game_type = ? 
                  AND is_selectable = TRUE 
                  AND shape_signature IS NOT NULL
                  AND confidence >= ?
            GROUP BY shape_signature
            ORDER BY avg_confidence DESC, occurrence_count DESC
        """, (game_type, min_confidence))
        
        shapes = []
        for row in results or []:
            if row['shape_signature']:  # Skip NULL
                shapes.append({
                    'shape_signature': row['shape_signature'],
                    'occurrence_count': row['occurrence_count'],
                    'avg_confidence': row['avg_confidence'],
                    'max_confidence': row['max_confidence'],
                    'colors_seen': row['colors_seen'].split(',') if row['colors_seen'] else []
                })
        return shapes
    
    def find_objects_matching_shape(
        self,
        frame: List[List[int]],
        target_shapes: List[str],
        exclude_colors: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all objects in the current frame that match target shape signatures.
        
        This is used on FRONTIER levels to enumerate all objects the agent
        should TRY clicking, based on shape generalization from previous levels.
        
        Args:
            frame: Current game frame (2D grid of colors)
            target_shapes: List of shape signatures to match (e.g., ["horizontal_bar"])
            exclude_colors: Colors to skip (e.g., background, already tried)
            
        Returns:
            List of matching objects with position, color, and shape info
        """
        if not frame or not target_shapes:
            return []
        
        exclude_colors = exclude_colors or [0]  # Default: exclude background
        
        import numpy as np
        grid = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        height, width = grid.shape
        
        # Find connected components (shapes)
        visited = np.zeros_like(grid, dtype=bool)
        matching_objects = []
        
        def flood_fill(start_y, start_x, color):
            """Find connected component of same color."""
            stack = [(start_y, start_x)]
            cells = []
            
            while stack:
                y, x = stack.pop()
                if y < 0 or y >= height or x < 0 or x >= width:
                    continue
                if visited[y, x] or grid[y, x] != color:
                    continue
                
                visited[y, x] = True
                cells.append((y, x))
                
                # 4-connected neighbors
                stack.extend([(y+1, x), (y-1, x), (y, x+1), (y, x-1)])
            
            return cells
        
        # Scan grid for objects
        for y in range(height):
            for x in range(width):
                if visited[y, x]:
                    continue
                    
                color = int(grid[y, x])
                if color in exclude_colors:
                    visited[y, x] = True
                    continue
                
                cells = flood_fill(y, x, color)
                
                if len(cells) < 2:  # Skip single-pixel objects
                    continue
                
                # Compute bounding box
                rows = [c[0] for c in cells]
                cols = [c[1] for c in cells]
                min_row, max_row = min(rows), max(rows)
                min_col, max_col = min(cols), max(cols)
                
                bbox_width = max_col - min_col + 1
                bbox_height = max_row - min_row + 1
                bbox_area = bbox_width * bbox_height
                density = len(cells) / bbox_area if bbox_area > 0 else 0
                
                # Compute shape signature
                shape_sig = self.compute_shape_signature(bbox_width, bbox_height, density)
                
                # Check if this shape matches any target
                if shape_sig in target_shapes:
                    center_y = sum(rows) // len(rows)
                    center_x = sum(cols) // len(cols)
                    
                    matching_objects.append({
                        'color': color,
                        'shape_signature': shape_sig,
                        'center': (center_x, center_y),  # (x, y) for click coords
                        'bounding_box': {
                            'left': min_col,
                            'top': min_row,
                            'width': bbox_width,
                            'height': bbox_height
                        },
                        'size': len(cells),
                        'density': density
                    })
        
        return matching_objects
    
    def get_untried_objects_for_frontier(
        self,
        game_type: str,
        level: int,
        frame: List[List[int]],
        tried_colors: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get objects the agent should try clicking on a frontier level.
        
        This is the main entry point for frontier exploration with shape generalization:
        1. Query what shapes are selectable in this game (from previous levels)
        2. Find all objects in current frame matching those shapes
        3. Filter out objects already tried
        4. Return prioritized list of objects to try
        
        Args:
            game_type: Game type (e.g., 'sp80')
            level: Current level number
            frame: Current game frame
            tried_colors: Colors already tried this session
            
        Returns:
            List of objects to try, prioritized by confidence
        """
        tried_colors = tried_colors or []
        
        # Step 1: Get selectable shapes for this game
        selectable_shapes = self.get_selectable_shapes_for_game(game_type, min_confidence=0.5)
        
        if not selectable_shapes:
            # No shape data yet - fall back to trying any non-background object
            logger.debug(f"[SHAPE] No selectable shapes known for {game_type} - exploring blindly")
            return []
        
        # Step 2: Extract shape signatures
        target_shapes = [s['shape_signature'] for s in selectable_shapes]
        logger.info(f"[SHAPE] {game_type} known selectable shapes: {target_shapes}")
        
        # Step 3: Find matching objects in current frame
        exclude = [0] + tried_colors  # Background + already tried
        matching = self.find_objects_matching_shape(frame, target_shapes, exclude)
        
        if not matching:
            logger.debug(f"[SHAPE] No matching objects found in frame for shapes {target_shapes}")
            return []
        
        # Step 4: Prioritize by shape confidence
        shape_confidence = {s['shape_signature']: s['avg_confidence'] for s in selectable_shapes}
        
        for obj in matching:
            obj['shape_confidence'] = shape_confidence.get(obj['shape_signature'], 0.5)
        
        # Sort by confidence (highest first)
        matching.sort(key=lambda x: x['shape_confidence'], reverse=True)
        
        logger.info(
            f"[SHAPE] Found {len(matching)} objects to try on {game_type} L{level}: "
            f"{[(o['color'], o['shape_signature']) for o in matching[:5]]}"
        )
        
        return matching

    def discover_selectable_objects(
        self,
        game_id: str,
        level: int,
        action_sequence: List[Dict],
        frame_sequence: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Analyze an action sequence to discover selectable objects.
        
        Pattern: ACTION6(x,y) -> ACTION1-4 -> object at (x,y) moved
        
        This is the main entry point for discovering the selection mechanism
        by analyzing complete gameplay sequences.
        
        Args:
            game_id: Game identifier
            level: Level number
            action_sequence: List of actions with action_type, x, y
            frame_sequence: List of frames with grid data
        
        Returns:
            List of discovered selectable objects
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        discovered = []
        
        # Look for pattern: ACTION6 followed by ACTION1-4
        ACTION6_VARIANTS = {'ACTION6', 'action_6', 'ACTION 6'}
        MOVEMENT_ACTIONS = {'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4',
                          'action_1', 'action_2', 'action_3', 'action_4'}
        
        pending_click = None  # Store last ACTION6 click info
        
        for i, action in enumerate(action_sequence):
            if i >= len(frame_sequence) - 1:
                break
            
            action_type = action.get('action_type', '')
            frame_before = frame_sequence[i]
            frame_after = frame_sequence[i + 1]
            
            if action_type in ACTION6_VARIANTS:
                # Record this click as potential selection
                click_x = action.get('x', action.get('click_x'))
                click_y = action.get('y', action.get('click_y'))
                
                if click_x is not None and click_y is not None:
                    grid = frame_before.get('grid', [])
                    clicked_color = self._get_object_at_coords(grid, click_x, click_y)
                    
                    if clicked_color and clicked_color != 0:
                        pending_click = {
                            'click_x': click_x,
                            'click_y': click_y,
                            'object_color': clicked_color,
                            'action_index': i,
                            'frame': frame_before
                        }
            
            elif action_type in MOVEMENT_ACTIONS and pending_click:
                # Check if the clicked object moved
                grid_before = frame_before.get('grid', [])
                grid_after = frame_after.get('grid', [])
                
                clicked_color = pending_click['object_color']
                
                objects_before = self._find_objects_in_grid(grid_before)
                objects_after = self._find_objects_in_grid(grid_after)
                
                if clicked_color in objects_before and clicked_color in objects_after:
                    pos_before = objects_before[clicked_color]
                    pos_after = objects_after[clicked_color]
                    
                    # Calculate movement
                    cx_before = sum(p[0] for p in pos_before) / len(pos_before)
                    cy_before = sum(p[1] for p in pos_before) / len(pos_before)
                    cx_after = sum(p[0] for p in pos_after) / len(pos_after)
                    cy_after = sum(p[1] for p in pos_after) / len(pos_after)
                    
                    dx = cx_after - cx_before
                    dy = cy_after - cy_before
                    
                    # Did it move?
                    if abs(dx) >= 0.5 or abs(dy) >= 0.5:
                        # Extract shape info from positions before movement
                        shape_info = None
                        if pos_before:
                            xs = [p[0] for p in pos_before]
                            ys = [p[1] for p in pos_before]
                            bbox_width = max(xs) - min(xs) + 1
                            bbox_height = max(ys) - min(ys) + 1
                            bbox_area = bbox_width * bbox_height
                            density = len(pos_before) / bbox_area if bbox_area > 0 else 1.0
                            shape_info = {
                                'width': bbox_width,
                                'height': bbox_height,
                                'density': density
                            }
                        
                        # Object moved after being clicked - it's selectable!
                        self._save_selectable_object(
                            game_type=game_type,
                            level=level,
                            object_color=clicked_color,
                            object_coords=f"({pending_click['click_x']},{pending_click['click_y']})",
                            is_moveable=True,
                            control_actions=[action_type],
                            confidence=0.85,
                            shape_info=shape_info
                        )
                        
                        discovered.append({
                            'object_color': clicked_color,
                            'click_coords': (pending_click['click_x'], pending_click['click_y']),
                            'movement_action': action_type,
                            'confirmed': True,
                            'shape_signature': self.compute_shape_signature(
                                shape_info['width'], shape_info['height'], shape_info['density']
                            ) if shape_info else None
                        })
                        
                        shape_msg = f" shape={discovered[-1].get('shape_signature')}" if shape_info else ""
                        logger.info(
                            f"[DISCOVERY] Selectable object found: color {clicked_color} "
                            f"at ({pending_click['click_x']},{pending_click['click_y']}) "
                            f"responds to {action_type} after ACTION6 selection{shape_msg}"
                        )
                
                # Clear pending click after movement action (successful or not)
                pending_click = None
        
        return discovered

    # ========================================================================
    # ACTION6 AVAILABILITY TRACKING (Added 2025-12-08)
    # ========================================================================
    # ACTION6 availability is a SIGNAL about game state:
    # - Present = something is selectable
    # - Absent = nothing currently selectable (conditions not met)
    # Learning these conditions is key to solving selection-based puzzles
    # ========================================================================
    
    def track_action6_availability(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        action_number: int,
        available_actions: List[str],
        previous_action: Optional[str] = None,
        previous_action_coords: Optional[str] = None,
        grid: Optional[List] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Track when ACTION6 becomes available or unavailable.
        
        This is called after every action to detect availability changes.
        When ACTION6 appears/disappears, it signals a change in selectability state.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
            action_number: Which action in sequence
            available_actions: Current list of available actions
            previous_action: What action was just taken
            previous_action_coords: Coordinates if applicable
            grid: Current grid state for hashing
        
        Returns:
            Dict with availability info if state changed, None otherwise
        """
        action6_available = 1 if 'ACTION6' in available_actions or 'action_6' in available_actions else 0
        
        # Calculate grid hash for pattern matching
        grid_hash = None
        if grid:
            import hashlib
            grid_str = str(grid)
            grid_hash = hashlib.md5(grid_str.encode()).hexdigest()[:16]
        
        # Store the event
        self.db.execute_query("""
            INSERT INTO action6_availability_events
            (agent_id, game_id, level_number, action_number, action6_available,
             previous_action, previous_action_coords, grid_hash, available_actions_list)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, game_id, level, action_number, action6_available,
              previous_action, previous_action_coords, grid_hash,
              json.dumps(available_actions)))
        
        return {
            'action6_available': bool(action6_available),
            'action_number': action_number,
            'previous_action': previous_action,
            'grid_hash': grid_hash
        }
    
    def detect_action6_state_change(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze action history to detect when ACTION6 availability changed.
        
        Returns list of state change events with context about what triggered them.
        """
        results = self.db.execute_query("""
            SELECT action_number, action6_available, previous_action, 
                   previous_action_coords, grid_hash
            FROM action6_availability_events
            WHERE agent_id = ? AND game_id = ? AND level_number = ?
            ORDER BY action_number ASC
        """, (agent_id, game_id, level))
        
        if not results or len(results) < 2:
            return []
        
        state_changes = []
        prev_available = results[0]['action6_available']
        
        for row in results[1:]:
            current_available = row['action6_available']
            
            if current_available != prev_available:
                # State changed!
                state_changes.append({
                    'action_number': row['action_number'],
                    'became_available': current_available == 1,
                    'trigger_action': row['previous_action'],
                    'trigger_coords': row['previous_action_coords'],
                    'grid_hash': row['grid_hash']
                })
                
                # Learn this as a selectability condition
                game_type = game_id.split('-')[0] if '-' in game_id else game_id
                self._save_selectability_condition(
                    game_type=game_type,
                    level=level,
                    trigger_action=row['previous_action'],
                    trigger_coords=row['previous_action_coords'],
                    action6_became_available=current_available
                )
            
            prev_available = current_available
        
        return state_changes
    
    def _save_selectability_condition(
        self,
        game_type: str,
        level: int,
        trigger_action: Optional[str],
        trigger_coords: Optional[str],
        action6_became_available: int
    ) -> None:
        """Save a discovered selectability condition to network knowledge."""
        if not trigger_action:
            return
        
        # Try to update existing or insert new
        existing = self.db.execute_query("""
            SELECT condition_id, occurrence_count, confidence
            FROM selectability_conditions
            WHERE game_type = ? AND level_number = ? 
                  AND trigger_action = ? AND COALESCE(trigger_coords, '') = COALESCE(?, '')
                  AND action6_became_available = ?
        """, (game_type, level, trigger_action, trigger_coords or '', action6_became_available))
        
        if existing:
            # Update count and confidence
            old_count = existing[0]['occurrence_count']
            new_confidence = min(0.95, 0.5 + (old_count * 0.1))  # Cap at 0.95
            
            self.db.execute_query("""
                UPDATE selectability_conditions
                SET occurrence_count = occurrence_count + 1,
                    confidence = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE condition_id = ?
            """, (new_confidence, existing[0]['condition_id']))
        else:
            # Insert new condition
            desc = f"{trigger_action}"
            if trigger_coords:
                desc += f" at {trigger_coords}"
            desc += f" -> ACTION6 {'appears' if action6_became_available else 'disappears'}"
            
            self.db.execute_query("""
                INSERT OR IGNORE INTO selectability_conditions
                (game_type, level_number, trigger_action, trigger_coords,
                 trigger_description, action6_became_available, confidence)
                VALUES (?, ?, ?, ?, ?, ?, 0.5)
            """, (game_type, level, trigger_action, trigger_coords, desc, action6_became_available))
        
        logger.debug(
            f"[SELECTABILITY] Learned: {trigger_action} "
            f"{'enables' if action6_became_available else 'disables'} ACTION6 in {game_type} L{level}"
        )
    
    def get_selectability_triggers(
        self,
        game_type: str,
        level: int,
        want_available: bool = True,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get known conditions that make ACTION6 available/unavailable.
        
        Args:
            game_type: Game type to query
            level: Level number
            want_available: If True, get conditions that ENABLE ACTION6
                           If False, get conditions that DISABLE ACTION6
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of trigger conditions
        """
        target = 1 if want_available else 0
        
        results = self.db.execute_query("""
            SELECT trigger_action, trigger_coords, trigger_description,
                   occurrence_count, confidence
            FROM selectability_conditions
            WHERE game_type = ? AND level_number = ? 
                  AND action6_became_available = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, target, min_confidence))
        
        return [
            {
                'trigger_action': row['trigger_action'],
                'trigger_coords': row['trigger_coords'],
                'description': row['trigger_description'],
                'occurrence_count': row['occurrence_count'],
                'confidence': row['confidence']
            }
            for row in (results or [])
        ]

    def record_availability_control_proof(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        trigger_action: str,
        new_actions: List[int],
        frame_state: Optional[List] = None
    ) -> None:
        """
        Record proof of object control based on available_actions change.
        
        When clicking an object unlocks movement actions (1-4), this is strong
        evidence that we selected something controllable. This updates the
        network control hypotheses with high confidence.
        
        Args:
            agent_id: Agent that discovered this
            game_id: Game identifier
            level: Level number
            trigger_action: Action that caused the change (usually ACTION6)
            new_actions: List of new actions that became available
            frame_state: Current frame for object identification
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # This is strong control evidence - movement was unlocked
        has_movement = any(a in [1, 2, 3, 4] for a in new_actions)
        
        if has_movement and trigger_action:
            # Try to identify what was clicked by examining frame state
            clicked_color = None
            if frame_state:
                # Look for recently selected object (usually has visual indicator)
                # For now, log the event with frame hash
                import hashlib
                frame_hash = hashlib.md5(str(frame_state).encode()).hexdigest()[:16]
            else:
                frame_hash = None
            
            # Store as strong control discovery
            # This gets shared to network_object_control_hypotheses
            control_pattern = {
                'discovery_type': 'availability_change',
                'trigger_action': trigger_action,
                'unlocked_actions': new_actions,
                'confidence_source': 'movement_unlocked'
            }
            
            action_response = {}
            for action_num in new_actions:
                if action_num == 1:
                    action_response['ACTION1'] = 'up'
                elif action_num == 2:
                    action_response['ACTION2'] = 'down'
                elif action_num == 3:
                    action_response['ACTION3'] = 'left'
                elif action_num == 4:
                    action_response['ACTION4'] = 'right'
            
            # Share to network with high confidence (this is strong evidence)
            try:
                hypothesis_id = self._generate_hypothesis_id()
                self.db.execute_query("""
                    INSERT OR IGNORE INTO network_object_control_hypotheses
                    (hypothesis_id, game_type, level_number, control_pattern, 
                     action_response_map, reliability_score, discovery_method,
                     validation_attempts, validation_successes, validated_by_win)
                    VALUES (?, ?, ?, ?, ?, 0.85, 'availability_change', 1, 1, FALSE)
                """, (hypothesis_id, game_type, level, 
                      json.dumps(control_pattern), json.dumps(action_response)))
                
                logger.info(
                    f"[CONTROL PROOF] Recorded availability change: {trigger_action} "
                    f"unlocked {new_actions} in {game_type} L{level}"
                )
            except Exception as e:
                logger.debug(f"Failed to record availability control proof: {e}")
    
    def _generate_hypothesis_id(self) -> str:
        """Generate a unique hypothesis ID."""
        import uuid
        return str(uuid.uuid4())[:12]

    # ========================================================================
    # COLLISION/INTERACTION DETECTION (Added 2025-12-08)
    # ========================================================================
    # When controlled objects move through the grid, they can interact with
    # other objects. Detecting these interactions is key to understanding
    # game mechanics and discovering winning strategies.
    # ========================================================================
    
    def get_grid_diff(
        self,
        grid_before: List,
        grid_after: List
    ) -> Dict[str, Any]:
        """
        Calculate differences between two grid states.
        
        Returns detailed information about what changed:
        - Objects that appeared
        - Objects that disappeared
        - Objects that moved
        - Objects that changed color
        
        Args:
            grid_before: Grid state before action
            grid_after: Grid state after action
        
        Returns:
            Dict with change information
        """
        if not grid_before or not grid_after:
            return {'changed': False, 'changes': []}
        
        # Find all object positions in both grids
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        changes = []
        
        # Check each cell for changes
        for y in range(min(len(grid_before), len(grid_after))):
            row_before = grid_before[y] if y < len(grid_before) else []
            row_after = grid_after[y] if y < len(grid_after) else []
            
            for x in range(max(len(row_before), len(row_after))):
                cell_before = row_before[x] if x < len(row_before) else 0
                cell_after = row_after[x] if x < len(row_after) else 0
                
                if cell_before != cell_after:
                    changes.append({
                        'x': x,
                        'y': y,
                        'color_before': cell_before,
                        'color_after': cell_after,
                        'type': self._classify_change(cell_before, cell_after)
                    })
        
        # Calculate object-level changes
        appeared = {}
        disappeared = {}
        moved = {}
        
        all_colors = set(objects_before.keys()) | set(objects_after.keys())
        
        for color in all_colors:
            if color == 0:  # Skip background
                continue
            
            before_positions = set(objects_before.get(color, []))
            after_positions = set(objects_after.get(color, []))
            
            if before_positions and not after_positions:
                disappeared[color] = list(before_positions)
            elif after_positions and not before_positions:
                appeared[color] = list(after_positions)
            elif before_positions != after_positions:
                moved[color] = {
                    'from': list(before_positions),
                    'to': list(after_positions)
                }
        
        return {
            'changed': len(changes) > 0,
            'cell_changes': changes,
            'objects_appeared': appeared,
            'objects_disappeared': disappeared,
            'objects_moved': moved
        }
    
    def _classify_change(self, before: int, after: int) -> str:
        """Classify the type of cell change."""
        if before == 0 and after != 0:
            return 'appeared'
        elif before != 0 and after == 0:
            return 'disappeared'
        elif before != 0 and after != 0:
            return 'color_changed'
        else:
            return 'unknown'
    
    def detect_collision(
        self,
        controlled_color: int,
        grid_before: List,
        grid_after: List,
        movement_direction: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if a controlled object collided with another object.
        
        Args:
            controlled_color: Color of the controlled object
            grid_before: Grid state before movement
            grid_after: Grid state after movement
            movement_direction: 'up', 'down', 'left', 'right'
        
        Returns:
            Collision info dict if collision detected, None otherwise
        """
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        if controlled_color not in objects_before:
            return None
        
        # Get controlled object positions
        controlled_before = objects_before[controlled_color]
        controlled_after = objects_after.get(controlled_color, [])
        
        if not controlled_after:
            return None  # Controlled object disappeared (might be game over)
        
        # Calculate movement vector
        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        
        dx, dy = direction_map.get(movement_direction, (0, 0))
        
        # Find cells the controlled object moved into
        controlled_before_set = set(tuple(p) for p in controlled_before)
        new_positions = []
        
        for pos in controlled_before:
            new_pos = (pos[0] + dx, pos[1] + dy)
            if new_pos not in controlled_before_set:
                new_positions.append(new_pos)
        
        # Check if any new position was occupied by another object
        collisions = []
        
        for new_pos in new_positions:
            x, y = new_pos
            if 0 <= y < len(grid_before) and 0 <= x < len(grid_before[0] if grid_before else []):
                cell_before = grid_before[y][x]
                
                if cell_before != 0 and cell_before != controlled_color:
                    # Collision detected!
                    cell_after = grid_after[y][x] if (0 <= y < len(grid_after) and 0 <= x < len(grid_after[0] if grid_after else [])) else 0
                    
                    collisions.append({
                        'target_color': cell_before,
                        'target_position': (x, y),
                        'collision_type': 'same_cell',
                        'target_disappeared': cell_before not in objects_after,
                        'target_still_there': cell_after == cell_before
                    })
        
        if collisions:
            return {
                'controlled_color': controlled_color,
                'movement_direction': movement_direction,
                'collisions': collisions
            }
        
        return None
    
    def record_collision_event(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        action_number: int,
        controlled_color: int,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        target_color: int,
        target_pos: Tuple[int, int],
        collision_type: str,
        effect_observed: str,
        grid_changes: Optional[Dict] = None
    ) -> None:
        """Record a collision event to the database."""
        self.db.execute_query("""
            INSERT INTO collision_events
            (agent_id, game_id, level_number, action_number,
             controlled_object_color, controlled_from_x, controlled_from_y,
             controlled_to_x, controlled_to_y,
             target_object_color, target_object_x, target_object_y,
             collision_type, effect_observed, grid_changes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, game_id, level, action_number,
              controlled_color, from_pos[0], from_pos[1],
              to_pos[0], to_pos[1],
              target_color, target_pos[0], target_pos[1],
              collision_type, effect_observed,
              json.dumps(grid_changes) if grid_changes else None))
        
        # Learn this as a collision effect
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        self._save_collision_effect(
            game_type=game_type,
            level=level,
            controlled_color=controlled_color,
            target_color=target_color,
            collision_type=collision_type,
            effect_type=effect_observed
        )
    
    def _save_collision_effect(
        self,
        game_type: str,
        level: int,
        controlled_color: int,
        target_color: int,
        collision_type: str,
        effect_type: str
    ) -> None:
        """Save a discovered collision effect to network knowledge."""
        existing = self.db.execute_query("""
            SELECT effect_id, occurrence_count, confidence
            FROM collision_effects
            WHERE game_type = ? AND level_number = ?
                  AND controlled_object_color = ? AND target_object_color = ?
                  AND effect_type = ?
        """, (game_type, level, controlled_color, target_color, effect_type))
        
        if existing:
            old_count = existing[0]['occurrence_count']
            new_confidence = min(0.95, 0.5 + (old_count * 0.1))
            
            self.db.execute_query("""
                UPDATE collision_effects
                SET occurrence_count = occurrence_count + 1,
                    confidence = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE effect_id = ?
            """, (new_confidence, existing[0]['effect_id']))
        else:
            self.db.execute_query("""
                INSERT OR IGNORE INTO collision_effects
                (game_type, level_number, controlled_object_color, target_object_color,
                 collision_type, effect_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, 0.5)
            """, (game_type, level, controlled_color, target_color, collision_type, effect_type))
        
        logger.debug(
            f"[COLLISION] Learned: color {controlled_color} + color {target_color} "
            f"-> {effect_type} in {game_type} L{level}"
        )
    
    def get_collision_effects(
        self,
        game_type: str,
        level: int,
        controlled_color: Optional[int] = None,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get known collision effects for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            controlled_color: Optional filter by controlled object color
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of collision effect patterns
        """
        if controlled_color is not None:
            results = self.db.execute_query("""
                SELECT controlled_object_color, target_object_color, collision_type,
                       effect_type, occurrence_count, confidence
                FROM collision_effects
                WHERE game_type = ? AND level_number = ?
                      AND controlled_object_color = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (game_type, level, controlled_color, min_confidence))
        else:
            results = self.db.execute_query("""
                SELECT controlled_object_color, target_object_color, collision_type,
                       effect_type, occurrence_count, confidence
                FROM collision_effects
                WHERE game_type = ? AND level_number = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (game_type, level, min_confidence))
        
        return [
            {
                'controlled_color': row['controlled_object_color'],
                'target_color': row['target_object_color'],
                'collision_type': row['collision_type'],
                'effect_type': row['effect_type'],
                'occurrence_count': row['occurrence_count'],
                'confidence': row['confidence']
            }
            for row in (results or [])
        ]

    # ========================================================================
    # AUTONOMOUS OBJECT DETECTION (Added 2025-12-08)
    # ========================================================================
    # Some objects move independently of player input (NPCs, enemies, etc.)
    # The agent needs to distinguish between objects it controls, objects
    # that react to its actions, and objects that move on their own.
    # ========================================================================
    
    def detect_autonomous_movement(
        self,
        grid_before: List,
        grid_after: List,
        controlled_colors: List[int],
        action_taken: str
    ) -> List[Dict[str, Any]]:
        """
        Detect objects that moved without being controlled.
        
        Args:
            grid_before: Grid state before action
            grid_after: Grid state after action
            controlled_colors: Colors of objects the agent controls
            action_taken: What action was taken
        
        Returns:
            List of autonomously moving objects
        """
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        autonomous_movements = []
        
        for color in objects_before:
            if color == 0:  # Skip background
                continue
            if color in controlled_colors:  # Skip controlled objects
                continue
            
            if color in objects_after:
                before_positions = set(tuple(p) for p in objects_before[color])
                after_positions = set(tuple(p) for p in objects_after[color])
                
                if before_positions != after_positions:
                    # This object moved but we didn't control it!
                    autonomous_movements.append({
                        'object_color': color,
                        'from_positions': list(before_positions),
                        'to_positions': list(after_positions),
                        'action_when_moved': action_taken
                    })
        
        return autonomous_movements
    
    def record_autonomous_object(
        self,
        game_type: str,
        level: int,
        object_color: int,
        movement_pattern: str = 'unknown',
        moves_without_input: bool = False
    ) -> None:
        """Record discovery of an autonomous object."""
        existing = self.db.execute_query("""
            SELECT record_id, observation_count, moves_per_turn
            FROM autonomous_objects
            WHERE game_type = ? AND level_number = ? AND object_color = ?
        """, (game_type, level, object_color))
        
        if existing:
            self.db.execute_query("""
                UPDATE autonomous_objects
                SET observation_count = observation_count + 1,
                    moves_per_turn = moves_per_turn + 1,
                    moves_without_input = CASE WHEN ? THEN 1 ELSE moves_without_input END,
                    movement_pattern = COALESCE(NULLIF(?, 'unknown'), movement_pattern),
                    confidence = LEAST(0.95, confidence + 0.05),
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ? AND object_color = ?
            """, (moves_without_input, movement_pattern, game_type, level, object_color))
        else:
            self.db.execute_query("""
                INSERT INTO autonomous_objects
                (game_type, level_number, object_color, movement_pattern,
                 moves_without_input, confidence)
                VALUES (?, ?, ?, ?, ?, 0.5)
            """, (game_type, level, object_color, movement_pattern, 1 if moves_without_input else 0))
        
        logger.debug(
            f"[AUTONOMOUS] Object color {object_color} moves independently "
            f"in {game_type} L{level}, pattern: {movement_pattern}"
        )
    
    def get_autonomous_objects(
        self,
        game_type: str,
        level: int,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get known autonomous objects for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of autonomous object info
        """
        results = self.db.execute_query("""
            SELECT object_color, movement_pattern, moves_per_turn,
                   moves_without_input, is_ever_controllable, 
                   controllable_conditions, confidence
            FROM autonomous_objects
            WHERE game_type = ? AND level_number = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))
        
        return [
            {
                'object_color': row['object_color'],
                'movement_pattern': row['movement_pattern'],
                'moves_per_turn': row['moves_per_turn'],
                'moves_without_input': bool(row['moves_without_input']),
                'is_controllable': bool(row['is_ever_controllable']),
                'controllable_conditions': row['controllable_conditions'],
                'confidence': row['confidence']
            }
            for row in (results or [])
        ]

    # ========================================================================
    # COMPREHENSIVE OBJECT PROPERTY ANALYSIS (Added 2025-12-08)
    # ========================================================================
    # Track all object properties: size, shape, position, controllability.
    # Changes to ANY property can be triggers for game mechanics.
    # ========================================================================
    
    def analyze_object_properties(
        self,
        grid: List,
        controlled_colors: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze all objects in a grid and compute their properties.
        
        Properties tracked:
        - cell_count: Number of cells (size)
        - bounding_box: (width, height)
        - center: (x, y) center of mass
        - shape_hash: Hash of relative positions (for shape comparison)
        - is_contiguous: Whether object is one connected piece
        - is_controlled: Whether currently under player control
        - orientation: Normalized shape signature for rotation/flip detection
        - canonical_shape: Positions normalized to detect rotations
        
        Args:
            grid: Grid state to analyze
            controlled_colors: List of colors currently controlled by player
        
        Returns:
            Dict mapping color -> property dict
        """
        if not grid:
            return {}
        
        objects = self._find_objects_in_grid(grid)
        properties = {}
        
        controlled_set = set(controlled_colors or [])
        
        for color, positions in objects.items():
            if color == 0:
                continue
            
            # Size
            cell_count = len(positions)
            
            # Bounding box
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            bb_width = max_x - min_x + 1
            bb_height = max_y - min_y + 1
            
            # Center of mass
            center_x = sum(xs) / cell_count
            center_y = sum(ys) / cell_count
            
            # Shape hash: relative positions from top-left corner (orientation-dependent)
            relative_positions = sorted([(x - min_x, y - min_y) for x, y in positions])
            shape_hash = hash(tuple(relative_positions))
            
            # Contiguity check (BFS from first cell)
            is_contiguous = self._check_contiguity(positions)
            
            # ================================================================
            # ORIENTATION DETECTION (Added 2025-12-08)
            # ================================================================
            # Compute all 8 transformations (4 rotations x 2 flips) and use
            # the lexicographically smallest as the "canonical" form.
            # If two objects have the same canonical form but different
            # relative_positions, one is a rotation/flip of the other.
            # ================================================================
            orientation_data = self._compute_orientation(relative_positions, bb_width, bb_height)
            
            properties[color] = {
                'cell_count': cell_count,
                'bounding_box': (bb_width, bb_height),
                'center': (center_x, center_y),
                'shape_hash': str(shape_hash),
                'is_contiguous': is_contiguous,
                'is_controlled': color in controlled_set,
                'positions': positions,
                'relative_positions': relative_positions,
                'canonical_shape': orientation_data['canonical'],
                'orientation': orientation_data['orientation'],
                'orientation_hash': orientation_data['canonical_hash']
            }
        
        return properties
    
    def _compute_orientation(
        self, 
        relative_positions: List[Tuple[int, int]], 
        width: int, 
        height: int
    ) -> Dict[str, Any]:
        """
        Compute orientation and canonical form of a shape.
        
        Generates all 8 transformations (4 rotations x 2 flips) and returns:
        - canonical: The lexicographically smallest transformation
        - orientation: Which transformation the original shape is
        - canonical_hash: Hash of the canonical form (same for all rotations/flips)
        
        Orientations:
        - 'original': No transformation
        - 'rot90': Rotated 90 degrees clockwise
        - 'rot180': Rotated 180 degrees
        - 'rot270': Rotated 270 degrees clockwise
        - 'flip_h': Flipped horizontally
        - 'flip_v': Flipped vertically
        - 'flip_h_rot90': Flipped horizontally then rotated 90
        - 'flip_v_rot90': Flipped vertically then rotated 90
        """
        if not relative_positions:
            return {'canonical': [], 'orientation': 'original', 'canonical_hash': '0'}
        
        # Generate all 8 transformations
        transformations = {}
        
        # Original
        transformations['original'] = tuple(sorted(relative_positions))
        
        # Rotate 90 clockwise: (x, y) -> (y, width-1-x) but we normalize to (0,0) origin
        def rotate_90(positions, w, h):
            rotated = [(y, w - 1 - x) for x, y in positions]
            min_x = min(p[0] for p in rotated)
            min_y = min(p[1] for p in rotated)
            return sorted([(x - min_x, y - min_y) for x, y in rotated])
        
        # Rotate 180: (x, y) -> (width-1-x, height-1-y)
        def rotate_180(positions, w, h):
            rotated = [(w - 1 - x, h - 1 - y) for x, y in positions]
            min_x = min(p[0] for p in rotated)
            min_y = min(p[1] for p in rotated)
            return sorted([(x - min_x, y - min_y) for x, y in rotated])
        
        # Rotate 270 clockwise: (x, y) -> (height-1-y, x)
        def rotate_270(positions, w, h):
            rotated = [(h - 1 - y, x) for x, y in positions]
            min_x = min(p[0] for p in rotated)
            min_y = min(p[1] for p in rotated)
            return sorted([(x - min_x, y - min_y) for x, y in rotated])
        
        # Flip horizontal: (x, y) -> (width-1-x, y)
        def flip_h(positions, w, h):
            flipped = [(w - 1 - x, y) for x, y in positions]
            min_x = min(p[0] for p in flipped)
            return sorted([(x - min_x, y) for x, y in flipped])
        
        # Flip vertical: (x, y) -> (x, height-1-y)
        def flip_v(positions, w, h):
            flipped = [(x, h - 1 - y) for x, y in positions]
            min_y = min(p[1] for p in flipped)
            return sorted([(x, y - min_y) for x, y in flipped])
        
        # Apply transformations
        transformations['rot90'] = tuple(rotate_90(relative_positions, width, height))
        transformations['rot180'] = tuple(rotate_180(relative_positions, width, height))
        transformations['rot270'] = tuple(rotate_270(relative_positions, width, height))
        transformations['flip_h'] = tuple(flip_h(relative_positions, width, height))
        transformations['flip_v'] = tuple(flip_v(relative_positions, width, height))
        
        # Combined: flip then rotate
        flipped_h = flip_h(relative_positions, width, height)
        flipped_v = flip_v(relative_positions, width, height)
        h_bb = (max(p[0] for p in flipped_h) + 1, max(p[1] for p in flipped_h) + 1)
        v_bb = (max(p[0] for p in flipped_v) + 1, max(p[1] for p in flipped_v) + 1)
        transformations['flip_h_rot90'] = tuple(rotate_90(flipped_h, h_bb[0], h_bb[1]))
        transformations['flip_v_rot90'] = tuple(rotate_90(flipped_v, v_bb[0], v_bb[1]))
        
        # Find canonical form (lexicographically smallest)
        canonical_orientation = min(transformations.keys(), key=lambda k: transformations[k])
        canonical = transformations[canonical_orientation]
        
        # Determine what orientation the ORIGINAL shape is relative to canonical
        # The original shape's orientation is how you'd need to transform canonical to get original
        original = transformations['original']
        
        # Find which transformation the original matches
        for orient, transformed in transformations.items():
            if transformed == original:
                current_orientation = orient
                break
        else:
            current_orientation = 'original'
        
        return {
            'canonical': list(canonical),
            'orientation': current_orientation,
            'canonical_hash': str(hash(canonical))
        }
    
    def detect_rotation(
        self,
        props_before: Dict[str, Any],
        props_after: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if an object rotated or flipped between two states.
        
        Args:
            props_before: Object properties before action
            props_after: Object properties after action
        
        Returns:
            Rotation info dict if rotation detected, None otherwise
        """
        if not props_before or not props_after:
            return None
        
        # Same canonical shape = same object, possibly rotated
        if props_before.get('orientation_hash') != props_after.get('orientation_hash'):
            return None  # Different shape entirely, not a rotation
        
        orient_before = props_before.get('orientation', 'original')
        orient_after = props_after.get('orientation', 'original')
        
        if orient_before == orient_after:
            return None  # No rotation
        
        # Determine the type of rotation/flip
        rotation_type = self._classify_rotation(orient_before, orient_after)
        
        return {
            'rotated': True,
            'from_orientation': orient_before,
            'to_orientation': orient_after,
            'rotation_type': rotation_type
        }
    
    def _classify_rotation(self, orient_before: str, orient_after: str) -> str:
        """Classify the type of rotation/flip between two orientations."""
        # Map orientation transitions to human-readable rotation types
        rotation_map = {
            ('original', 'rot90'): 'rotate_90_cw',
            ('original', 'rot180'): 'rotate_180',
            ('original', 'rot270'): 'rotate_90_ccw',
            ('original', 'flip_h'): 'flip_horizontal',
            ('original', 'flip_v'): 'flip_vertical',
            ('rot90', 'original'): 'rotate_90_ccw',
            ('rot90', 'rot180'): 'rotate_90_cw',
            ('rot90', 'rot270'): 'rotate_180',
            ('rot180', 'original'): 'rotate_180',
            ('rot180', 'rot90'): 'rotate_90_ccw',
            ('rot180', 'rot270'): 'rotate_90_cw',
            ('rot270', 'original'): 'rotate_90_cw',
            ('rot270', 'rot90'): 'rotate_180',
            ('rot270', 'rot180'): 'rotate_90_ccw',
            ('flip_h', 'original'): 'flip_horizontal',
            ('flip_v', 'original'): 'flip_vertical',
        }
        
        return rotation_map.get((orient_before, orient_after), f'{orient_before}_to_{orient_after}')
    
    def _check_contiguity(self, positions: List[Tuple[int, int]]) -> bool:
        """Check if a set of positions forms a contiguous object."""
        if len(positions) <= 1:
            return True
        
        pos_set = set(positions)
        visited = set()
        stack = [positions[0]]
        
        while stack:
            curr = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            
            # Check 4-connected neighbors
            x, y = curr
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                if neighbor in pos_set and neighbor not in visited:
                    stack.append(neighbor)
        
        return len(visited) == len(positions)
    
    def detect_property_changes(
        self,
        grid_before: List,
        grid_after: List,
        controlled_colors: Optional[List[int]] = None,
        action_taken: Optional[str] = None,
        triggering_color: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect all property changes for all objects between two grid states.
        
        This is the COMPREHENSIVE change detection that catches:
        - Color changes (object changes color)
        - Size changes (object grows or shrinks)
        - Shape changes (object changes form)
        - Position changes (object moves)
        - Controllability changes (object becomes/stops being controllable)
        - Appearance/disappearance
        
        Args:
            grid_before: Grid state before action
            grid_after: Grid state after action
            controlled_colors: Colors currently under control
            action_taken: What action triggered this
            triggering_color: What object was interacted with
        
        Returns:
            List of property change dicts
        """
        props_before = self.analyze_object_properties(grid_before, controlled_colors)
        props_after = self.analyze_object_properties(grid_after, controlled_colors)
        
        changes = []
        all_colors = set(props_before.keys()) | set(props_after.keys())
        
        for color in all_colors:
            if color == 0:
                continue
            
            before = props_before.get(color)
            after = props_after.get(color)
            
            # Object appeared
            if before is None and after is not None:
                changes.append({
                    'object_color': color,
                    'property_name': 'existence',
                    'value_before': 'absent',
                    'value_after': 'present',
                    'change_type': 'appeared',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
                continue
            
            # Object disappeared
            if before is not None and after is None:
                changes.append({
                    'object_color': color,
                    'property_name': 'existence',
                    'value_before': 'present',
                    'value_after': 'absent',
                    'change_type': 'disappeared',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
                continue
            
            # At this point, both before and after MUST exist (not None)
            # The above continue statements handle the None cases
            if before is None or after is None:
                continue  # Safety guard for type checker
            
            # Check each property for changes
            if before['cell_count'] != after['cell_count']:
                changes.append({
                    'object_color': color,
                    'property_name': 'size',
                    'value_before': str(before['cell_count']),
                    'value_after': str(after['cell_count']),
                    'change_type': 'grew' if after['cell_count'] > before['cell_count'] else 'shrank',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
            
            if before['shape_hash'] != after['shape_hash']:
                changes.append({
                    'object_color': color,
                    'property_name': 'shape',
                    'value_before': before['shape_hash'],
                    'value_after': after['shape_hash'],
                    'change_type': 'shape_changed',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
            
            # Position change (center moved more than 0.5 cells)
            dist = ((before['center'][0] - after['center'][0])**2 + 
                    (before['center'][1] - after['center'][1])**2) ** 0.5
            if dist > 0.5:
                changes.append({
                    'object_color': color,
                    'property_name': 'position',
                    'value_before': f"{before['center'][0]:.1f},{before['center'][1]:.1f}",
                    'value_after': f"{after['center'][0]:.1f},{after['center'][1]:.1f}",
                    'change_type': 'moved',
                    'distance_moved': dist,
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
            
            if before['is_controlled'] != after['is_controlled']:
                changes.append({
                    'object_color': color,
                    'property_name': 'controllable',
                    'value_before': str(before['is_controlled']),
                    'value_after': str(after['is_controlled']),
                    'change_type': 'became_controllable' if after['is_controlled'] else 'lost_control',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
            
            if before['is_contiguous'] != after['is_contiguous']:
                changes.append({
                    'object_color': color,
                    'property_name': 'contiguity',
                    'value_before': 'contiguous' if before['is_contiguous'] else 'fragmented',
                    'value_after': 'contiguous' if after['is_contiguous'] else 'fragmented',
                    'change_type': 'merged' if after['is_contiguous'] else 'split',
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
            
            # ================================================================
            # ORIENTATION/ROTATION DETECTION (Added 2025-12-08)
            # ================================================================
            # Check if the object rotated or flipped.
            # Same canonical shape but different orientation = rotation/flip.
            # This is a key trigger type for puzzle mechanics.
            # ================================================================
            rotation_info = self.detect_rotation(before, after)
            if rotation_info and rotation_info.get('rotated'):
                changes.append({
                    'object_color': color,
                    'property_name': 'orientation',
                    'value_before': rotation_info['from_orientation'],
                    'value_after': rotation_info['to_orientation'],
                    'change_type': rotation_info['rotation_type'],
                    'triggering_action': action_taken,
                    'triggering_color': triggering_color
                })
        
        return changes
    
    def record_interaction_trigger(
        self,
        game_type: str,
        level_number: int,
        trigger_action: str,
        trigger_position: Optional[Tuple[int, int]],
        trigger_object_color: Optional[int],
        trigger_interaction_type: str,
        effect_position: Optional[Tuple[int, int]],
        effect_object_color: int,
        effect_type: str,
        effect_details: Optional[Dict] = None
    ) -> None:
        """
        Record a discovered interaction trigger to network knowledge.
        
        This learns causal relationships:
        "When I do X at position A, effect Y happens at position B"
        
        Consistency tracking: If this exact trigger+effect pair is seen again,
        confidence increases. If trigger happens but effect doesn't, confidence decreases.
        
        Args:
            game_type: Game type
            level_number: Level number
            trigger_action: What action triggered this (ACTION1-7)
            trigger_position: Where action was taken (for ACTION6)
            trigger_object_color: Object that was interacted with
            trigger_interaction_type: 'collision', 'selection', 'click', 'adjacent'
            effect_position: Where effect happened
            effect_object_color: Object that was affected
            effect_type: What happened
            effect_details: Additional info as dict
        """
        # Calculate distance between trigger and effect
        effect_distance = None
        if trigger_position and effect_position:
            effect_distance = abs(trigger_position[0] - effect_position[0]) + \
                            abs(trigger_position[1] - effect_position[1])
        
        existing = self.db.execute_query("""
            SELECT trigger_id, occurrence_count, consistent_count, confidence
            FROM interaction_triggers
            WHERE game_type = ? AND level_number = ?
                  AND trigger_action = ? AND trigger_object_color = ?
                  AND effect_object_color = ? AND effect_type = ?
        """, (game_type, level_number, trigger_action, trigger_object_color,
              effect_object_color, effect_type))
        
        if existing:
            # Seen this before - increase confidence
            old_count = existing[0]['occurrence_count']
            old_consistent = existing[0]['consistent_count']
            new_confidence = min(0.99, (old_consistent + 1) / (old_count + 1 + 2))  # Laplace smoothing
            current_gen = self._get_current_generation()
            
            self.db.execute_query("""
                UPDATE interaction_triggers
                SET occurrence_count = occurrence_count + 1,
                    consistent_count = consistent_count + 1,
                    confidence = ?,
                    last_observed = CURRENT_TIMESTAMP,
                    last_observed_generation = ?,
                    is_active = 1
                WHERE trigger_id = ?
            """, (new_confidence, current_gen, existing[0]['trigger_id']))
            
            logger.debug(
                f"[TRIGGER] Confirmed: {trigger_action}+{trigger_object_color} -> "
                f"{effect_type} on {effect_object_color} (count={old_count+1}, conf={new_confidence:.2f})"
            )
        else:
            # First time seeing this trigger
            current_gen = self._get_current_generation()
            self.db.execute_query("""
                INSERT OR IGNORE INTO interaction_triggers
                (game_type, level_number, trigger_action, trigger_position_x, trigger_position_y,
                 trigger_object_color, trigger_interaction_type,
                 effect_position_x, effect_position_y, effect_object_color,
                 effect_type, effect_details, effect_distance, confidence,
                 is_active, last_observed_generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.5, 1, ?)
            """, (game_type, level_number, trigger_action,
                  trigger_position[0] if trigger_position else None,
                  trigger_position[1] if trigger_position else None,
                  trigger_object_color, trigger_interaction_type,
                  effect_position[0] if effect_position else None,
                  effect_position[1] if effect_position else None,
                  effect_object_color, effect_type,
                  json.dumps(effect_details) if effect_details else None,
                  effect_distance, current_gen))
            
            logger.info(
                f"[TRIGGER] New: {trigger_action}+{trigger_object_color} -> "
                f"{effect_type} on {effect_object_color} (distance={effect_distance})"
            )
    
    def record_trigger_inconsistency(
        self,
        game_type: str,
        level_number: int,
        trigger_action: str,
        trigger_object_color: int
    ) -> None:
        """
        Record when an expected trigger didn't produce the expected effect.
        
        This decreases confidence - if a trigger is inconsistent, it might be
        coincidental rather than causal.
        
        Args:
            game_type: Game type
            level_number: Level number
            trigger_action: What action was taken
            trigger_object_color: Object that was interacted with
        """
        # Find all triggers matching this action+object
        self.db.execute_query("""
            UPDATE interaction_triggers
            SET inconsistent_count = inconsistent_count + 1,
                confidence = MAX(0.1, 
                    CAST(consistent_count AS REAL) / 
                    (occurrence_count + inconsistent_count + 2)
                )
            WHERE game_type = ? AND level_number = ?
                  AND trigger_action = ? AND trigger_object_color = ?
        """, (game_type, level_number, trigger_action, trigger_object_color))
    
    def get_known_triggers(
        self,
        game_type: str,
        level_number: int,
        min_confidence: float = 0.6,
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get known interaction triggers for a game/level.
        
        Only returns triggers that have been observed multiple times
        with high consistency (likely causal, not coincidental).
        
        Args:
            game_type: Game type to query
            level_number: Level number
            min_confidence: Minimum confidence threshold
            min_occurrences: Minimum times trigger was observed
        
        Returns:
            List of trigger patterns with confidence scores
        """
        results = self.db.execute_query("""
            SELECT trigger_action, trigger_position_x, trigger_position_y,
                   trigger_object_color, trigger_interaction_type,
                   effect_position_x, effect_position_y, effect_object_color,
                   effect_type, effect_details, effect_distance,
                   occurrence_count, consistent_count, inconsistent_count, confidence
            FROM interaction_triggers
            WHERE game_type = ? AND level_number = ?
                  AND confidence >= ? AND occurrence_count >= ?
            ORDER BY confidence DESC, occurrence_count DESC
        """, (game_type, level_number, min_confidence, min_occurrences))
        
        return [
            {
                'trigger_action': row['trigger_action'],
                'trigger_position': (row['trigger_position_x'], row['trigger_position_y']) 
                                    if row['trigger_position_x'] is not None else None,
                'trigger_object_color': row['trigger_object_color'],
                'trigger_type': row['trigger_interaction_type'],
                'effect_position': (row['effect_position_x'], row['effect_position_y'])
                                   if row['effect_position_x'] is not None else None,
                'effect_object_color': row['effect_object_color'],
                'effect_type': row['effect_type'],
                'effect_distance': row['effect_distance'],
                'occurrences': row['occurrence_count'],
                'consistent': row['consistent_count'],
                'inconsistent': row['inconsistent_count'],
                'confidence': row['confidence']
            }
            for row in (results or [])
        ]
    
    def record_all_grid_effects(
        self,
        game_type: str,
        level_number: int,
        action_taken: str,
        trigger_position: Optional[Tuple[int, int]],
        trigger_object_color: Optional[int],
        trigger_type: str,
        grid_before: List,
        grid_after: List,
        controlled_colors: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect and record ALL effects on the grid from a single action.
        
        This is the main entry point for comprehensive effect detection.
        It finds all property changes and records them as potential triggers.
        
        Args:
            game_type: Game type
            level_number: Level number
            action_taken: What action was taken
            trigger_position: Where action was taken (for ACTION6)
            trigger_object_color: What object was directly interacted with
            trigger_type: 'collision', 'selection', 'click', 'movement'
            grid_before: Grid state before action
            grid_after: Grid state after action
            controlled_colors: Colors currently under control
        
        Returns:
            List of all detected effects
        """
        # Get all property changes
        changes = self.detect_property_changes(
            grid_before=grid_before,
            grid_after=grid_after,
            controlled_colors=controlled_colors,
            action_taken=action_taken,
            triggering_color=trigger_object_color
        )
        
        # Record each change as a potential trigger
        for change in changes:
            # Skip recording the movement of the controlled object itself
            # (that's expected, not a trigger)
            if (change['object_color'] == trigger_object_color and 
                change['property_name'] == 'position' and
                trigger_type == 'movement'):
                continue
            
            # Get position of affected object if available
            props_after = self.analyze_object_properties(grid_after)
            effect_position = None
            if change['object_color'] in props_after:
                center = props_after[change['object_color']]['center']
                effect_position = (int(center[0]), int(center[1]))
            
            self.record_interaction_trigger(
                game_type=game_type,
                level_number=level_number,
                trigger_action=action_taken,
                trigger_position=trigger_position,
                trigger_object_color=trigger_object_color,
                trigger_interaction_type=trigger_type,
                effect_position=effect_position,
                effect_object_color=change['object_color'],
                effect_type=change['change_type'],
                effect_details={
                    'property': change['property_name'],
                    'before': change['value_before'],
                    'after': change['value_after']
                }
            )
        
        return changes

    # ========================================================================
    # TRIGGER SEQUENCE TRACKING (Order of Triggers Matters!)
    # ========================================================================
    # Track the order in which triggers are activated during gameplay.
    # Successful sequences are stored for replay by other agents.
    # ========================================================================
    
    def __init_sequence_tracker(self, game_id: str, level_number: int) -> None:
        """Initialize a new sequence tracking session for a level."""
        if not hasattr(self, '_active_sequences'):
            self._active_sequences = {}
        
        key = f"{game_id}:{level_number}"
        self._active_sequences[key] = {
            'game_id': game_id,
            'level_number': level_number,
            'steps': [],
            'step_count': 0,
            'start_score': None
        }
    
    def record_trigger_step(
        self,
        game_id: str,
        level_number: int,
        action_number: int,
        trigger_action: str,
        trigger_object_color: Optional[int],
        trigger_interaction_type: str,
        effect_object_color: Optional[int],
        effect_type: str,
        score_before: Optional[float] = None,
        score_after: Optional[float] = None
    ) -> None:
        """
        Record a single trigger activation as part of the current sequence.
        
        This builds up the sequence step-by-step during gameplay.
        At level end, finalize_sequence() is called to save if successful.
        
        Args:
            game_id: Current game ID
            level_number: Current level
            action_number: Action index
            trigger_action: What action was taken
            trigger_object_color: Object that was interacted with
            trigger_interaction_type: Type of interaction
            effect_object_color: Object that was affected
            effect_type: What effect occurred
            score_before: Score before this action
            score_after: Score after this action
        """
        key = f"{game_id}:{level_number}"
        
        # Initialize if needed
        if not hasattr(self, '_active_sequences'):
            self._active_sequences = {}
        if key not in self._active_sequences:
            self.__init_sequence_tracker(game_id, level_number)
        
        seq = self._active_sequences[key]
        seq['step_count'] += 1
        
        step = {
            'step_number': seq['step_count'],
            'action_number': action_number,
            'trigger_action': trigger_action,
            'trigger_object_color': trigger_object_color,
            'trigger_interaction_type': trigger_interaction_type,
            'effect_object_color': effect_object_color,
            'effect_type': effect_type
        }
        
        seq['steps'].append(step)
        
        # Track score changes
        if seq['start_score'] is None and score_before is not None:
            seq['start_score'] = score_before
        
        # Also log to database for later analysis
        self.db.execute_query("""
            INSERT INTO trigger_sequence_events
            (game_id, level_number, action_number, trigger_action,
             trigger_object_color, trigger_interaction_type,
             effect_object_color, effect_type, step_number,
             score_before, score_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (game_id, level_number, action_number, trigger_action,
              trigger_object_color, trigger_interaction_type,
              effect_object_color, effect_type, seq['step_count'],
              score_before, score_after))
    
    def finalize_sequence(
        self,
        game_id: str,
        level_number: int,
        outcome_type: str,
        outcome_details: Optional[Dict] = None,
        agent_id: Optional[str] = None,
        level_won: bool = False
    ) -> Optional[str]:
        """
        Finalize and save a trigger sequence at level end.
        
        Only saves sequences that achieved something meaningful
        (level win, score increase, etc.)
        
        Args:
            game_id: Game ID
            level_number: Level number
            outcome_type: 'level_win', 'score_increase', 'progress', etc.
            outcome_details: Additional outcome information
            agent_id: Agent that discovered this sequence
            level_won: Whether the level was completed
        
        Returns:
            Sequence ID if saved, None if not worth saving
        """
        key = f"{game_id}:{level_number}"
        
        if not hasattr(self, '_active_sequences') or key not in self._active_sequences:
            return None
        
        seq = self._active_sequences[key]
        
        # Don't save empty sequences
        if not seq['steps']:
            del self._active_sequences[key]
            return None
        
        # Create sequence hash for deduplication
        sequence_json = json.dumps(seq['steps'], sort_keys=True)
        sequence_hash = str(hash(sequence_json))
        
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Check if we've seen this sequence before
        existing = self.db.execute_query("""
            SELECT sequence_id, times_succeeded, times_attempted
            FROM trigger_sequences
            WHERE game_type = ? AND level_number = ? AND sequence_hash = ?
        """, (game_type, level_number, sequence_hash))
        
        if existing:
            # Update existing sequence
            new_attempts = existing[0]['times_attempted'] + 1
            new_successes = existing[0]['times_succeeded'] + (1 if level_won else 0)
            new_rate = new_successes / new_attempts if new_attempts > 0 else 0
            current_gen = self._get_current_generation()
            
            self.db.execute_query("""
                UPDATE trigger_sequences
                SET times_attempted = ?,
                    times_succeeded = ?,
                    success_rate = ?,
                    last_validated = CURRENT_TIMESTAMP,
                    is_complete_solution = MAX(is_complete_solution, ?),
                    last_observed_generation = ?,
                    is_active = 1
                WHERE sequence_id = ?
            """, (new_attempts, new_successes, new_rate, 
                  1 if level_won else 0, current_gen, existing[0]['sequence_id']))
            
            del self._active_sequences[key]
            return str(existing[0]['sequence_id'])
        else:
            # Save new sequence
            current_gen = self._get_current_generation()
            self.db.execute_query("""
                INSERT INTO trigger_sequences
                (game_type, level_number, sequence_json, sequence_length,
                 sequence_hash, outcome_type, outcome_details,
                 discovered_by_agent, is_complete_solution,
                 is_active, last_observed_generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (game_type, level_number, sequence_json, len(seq['steps']),
                  sequence_hash, outcome_type,
                  json.dumps(outcome_details) if outcome_details else None,
                  agent_id, 1 if level_won else 0, current_gen))
            
            logger.info(
                f"[SEQUENCE] Saved new trigger sequence for {game_type} L{level_number}: "
                f"{len(seq['steps'])} steps, outcome={outcome_type}"
            )
            
            del self._active_sequences[key]
            return sequence_hash
    
    def get_proven_sequences(
        self,
        game_type: str,
        level_number: int,
        min_success_rate: float = 0.5,
        complete_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get proven trigger sequences for a game/level.
        
        Returns sequences that have been successfully used before,
        ordered by success rate.
        
        Args:
            game_type: Game type to query
            level_number: Level number
            min_success_rate: Minimum success rate threshold
            complete_only: Only return complete solutions (level wins)
        
        Returns:
            List of sequence dicts with steps and success info
        """
        query = """
            SELECT sequence_id, sequence_json, sequence_length,
                   outcome_type, times_succeeded, times_attempted,
                   success_rate, is_complete_solution
            FROM trigger_sequences
            WHERE game_type = ? AND level_number = ?
                  AND success_rate >= ?
        """
        params = [game_type, level_number, min_success_rate]
        
        if complete_only:
            query += " AND is_complete_solution = 1"
        
        query += " ORDER BY success_rate DESC, times_succeeded DESC"
        
        results = self.db.execute_query(query, tuple(params))
        
        sequences = []
        for row in (results or []):
            try:
                steps = json.loads(row['sequence_json'])
            except:
                steps = []
            
            sequences.append({
                'sequence_id': row['sequence_id'],
                'steps': steps,
                'length': row['sequence_length'],
                'outcome_type': row['outcome_type'],
                'times_succeeded': row['times_succeeded'],
                'times_attempted': row['times_attempted'],
                'success_rate': row['success_rate'],
                'is_complete': bool(row['is_complete_solution'])
            })
        
        return sequences
    
    def get_next_expected_trigger(
        self,
        game_type: str,
        level_number: int,
        completed_steps: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        Given completed trigger steps, predict the next trigger to activate.
        
        Matches current progress against proven sequences to suggest
        the next step.
        
        Args:
            game_type: Game type
            level_number: Level number
            completed_steps: Steps already completed this attempt
        
        Returns:
            Suggested next trigger step, or None if no match found
        """
        sequences = self.get_proven_sequences(game_type, level_number, min_success_rate=0.5)
        
        if not sequences:
            return None
        
        completed_len = len(completed_steps)
        
        # Find sequences that match our progress so far
        for seq in sequences:
            if len(seq['steps']) <= completed_len:
                continue  # This sequence is shorter than our progress
            
            # Check if our steps match the beginning of this sequence
            match = True
            for i, step in enumerate(completed_steps):
                if i >= len(seq['steps']):
                    match = False
                    break
                
                seq_step = seq['steps'][i]
                # Compare key fields
                if (step.get('trigger_action') != seq_step.get('trigger_action') or
                    step.get('effect_type') != seq_step.get('effect_type')):
                    match = False
                    break
            
            if match and completed_len < len(seq['steps']):
                # Found a matching sequence - return the next step
                next_step = seq['steps'][completed_len]
                next_step['from_sequence_id'] = seq['sequence_id']
                next_step['sequence_success_rate'] = seq['success_rate']
                return next_step
        
        return None
    
    def clear_sequence_tracker(self, game_id: str, level_number: int) -> None:
        """Clear the sequence tracker for a game/level without saving."""
        key = f"{game_id}:{level_number}"
        if hasattr(self, '_active_sequences') and key in self._active_sequences:
            del self._active_sequences[key]
    
    # =========================================================================
    # PERCEPTUAL PRIMITIVE 1: SELF-OBJECT IDENTITY METHODS
    # =========================================================================
    
    def update_self_object_identity(
        self,
        game_id: str,
        level_number: int,
        action_number: int,
        self_object_color: int,
        self_object_signature: Optional[str],
        center_x: float,
        center_y: float,
        confidence: float,
        correlation_score: float,
        sample_count: int,
        total_candidates: int = 1
    ) -> None:
        """
        Update or create self-object identity for this game/level.
        
        This is "I am THIS object" - the core self-model.
        Should be called when we've identified what object responds to our actions.
        
        Args:
            game_id: Current game
            level_number: Current level
            action_number: When this identity was established
            self_object_color: Color ID of the controlled object
            self_object_signature: Shape hash for stable identification
            center_x, center_y: Center of mass of the object
            confidence: 0.0 to 1.0 confidence in this identification
            correlation_score: Action-direction correlation score
            sample_count: Number of action samples used
            total_candidates: How many objects responded (should be 1)
        """
        is_ambiguous = 1 if total_candidates > 1 else 0
        
        # First, mark any previous identity as no longer valid
        self.db.execute_query("""
            UPDATE self_object_identity
            SET still_valid = 0
            WHERE game_id = ? AND level_number = ? AND still_valid = 1
        """, (game_id, level_number))
        
        # Insert new identity
        self.db.execute_query("""
            INSERT INTO self_object_identity
            (game_id, level_number, self_object_color, self_object_signature,
             self_object_center_x, self_object_center_y, confidence,
             correlation_score, sample_count, total_candidate_objects,
             is_ambiguous, established_at_action, still_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (game_id, level_number, self_object_color, self_object_signature,
              center_x, center_y, confidence, correlation_score, sample_count,
              total_candidates, is_ambiguous, action_number))
        
        logger.debug(
            f"[SELF-MODEL] Identity established: game={game_id} L{level_number} "
            f"color={self_object_color} confidence={confidence:.2f} "
            f"{'(AMBIGUOUS)' if is_ambiguous else ''}"
        )
    
    def get_current_self_object(
        self,
        game_id: str,
        level_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current self-object identity for this game/level.
        
        Returns:
            Dict with self_object_color, confidence, center_x/y, etc.
            or None if no identity established yet.
        """
        result = self.db.execute_query("""
            SELECT self_object_color, self_object_signature,
                   self_object_center_x, self_object_center_y,
                   confidence, correlation_score, sample_count,
                   total_candidate_objects, is_ambiguous,
                   established_at_action
            FROM self_object_identity
            WHERE game_id = ? AND level_number = ? AND still_valid = 1
            ORDER BY established_at_action DESC
            LIMIT 1
        """, (game_id, level_number))
        
        if result:
            row = result[0]
            return {
                'self_object_color': row['self_object_color'],
                'self_object_signature': row['self_object_signature'],
                'center_x': row['self_object_center_x'],
                'center_y': row['self_object_center_y'],
                'confidence': row['confidence'],
                'correlation_score': row['correlation_score'],
                'sample_count': row['sample_count'],
                'is_ambiguous': bool(row['is_ambiguous']),
                'total_candidates': row['total_candidate_objects']
            }
        return None
    
    def detect_control_transfer(
        self,
        game_id: str,
        level_number: int,
        action_number: int,
        previous_color: Optional[int],
        previous_signature: Optional[str],
        previous_center: Optional[Tuple[float, float]],
        new_color: int,
        new_signature: Optional[str],
        new_center: Tuple[float, float],
        trigger_action: str,
        trigger_coords: Optional[str] = None,
        trigger_reason: str = 'unknown'
    ) -> str:
        """
        Record a control transfer event: "I WAS object X, now I AM object Y"
        
        This is different from indirect causation - here, ACTION1-4 now move
        a DIFFERENT object than before.
        
        Args:
            game_id: Current game
            level_number: Current level
            action_number: When transfer occurred
            previous_color/signature/center: Old controlled object (if known)
            new_color/signature/center: New controlled object
            trigger_action: What caused the transfer (usually ACTION6)
            trigger_coords: Click coordinates if ACTION6
            trigger_reason: 'selection', 'automatic', 'collision', 'unknown'
        
        Returns:
            transfer_id as string
        """
        prev_cx, prev_cy = previous_center if previous_center else (None, None)
        new_cx, new_cy = new_center
        
        self.db.execute_query("""
            INSERT INTO control_transfer_events
            (game_id, level_number, action_number,
             previous_object_color, previous_object_signature,
             previous_object_center_x, previous_object_center_y,
             new_object_color, new_object_signature,
             new_object_center_x, new_object_center_y,
             transfer_trigger_action, transfer_trigger_coords,
             transfer_trigger_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (game_id, level_number, action_number,
              previous_color, previous_signature, prev_cx, prev_cy,
              new_color, new_signature, new_cx, new_cy,
              trigger_action, trigger_coords, trigger_reason))
        
        # Also update self_object_identity
        self.update_self_object_identity(
            game_id, level_number, action_number,
            new_color, new_signature, new_cx, new_cy,
            confidence=0.7,  # Medium confidence until verified
            correlation_score=0.0,  # Not yet measured
            sample_count=0,
            total_candidates=1
        )
        
        # Learn this transfer pattern for the network
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        self._learn_control_transfer_pattern(
            game_type, level_number, trigger_action, new_color, new_signature
        )
        
        logger.info(
            f"[CONTROL-TRANSFER] {game_id} L{level_number}: "
            f"color {previous_color} -> color {new_color} "
            f"via {trigger_action} ({trigger_reason})"
        )
        
        return f"{game_id}:{level_number}:{action_number}"
    
    def _learn_control_transfer_pattern(
        self,
        game_type: str,
        level_number: int,
        trigger_action: str,
        target_color: int,
        target_signature: Optional[str]
    ) -> None:
        """Learn and share a control transfer pattern with the network."""
        # Check if pattern exists
        existing = self.db.execute_query("""
            SELECT pattern_id, occurrence_count
            FROM control_transfer_patterns
            WHERE game_type = ? AND level_number = ?
                  AND transfer_trigger_action = ? AND target_object_color = ?
        """, (game_type, level_number, trigger_action, target_color))
        
        if existing:
            # Update existing pattern
            self.db.execute_query("""
                UPDATE control_transfer_patterns
                SET occurrence_count = occurrence_count + 1,
                    confidence = MIN(0.95, confidence + 0.05),
                    last_observed = CURRENT_TIMESTAMP
                WHERE pattern_id = ?
            """, (existing[0]['pattern_id'],))
        else:
            # Create new pattern
            self.db.execute_query("""
                INSERT INTO control_transfer_patterns
                (game_type, level_number, transfer_trigger_action,
                 target_object_color, target_object_signature)
                VALUES (?, ?, ?, ?, ?)
            """, (game_type, level_number, trigger_action, target_color, target_signature))
    
    def get_known_control_transfers(
        self,
        game_type: str,
        level_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get known control transfer patterns for a game/level.
        
        Returns list of patterns with target colors and trigger actions.
        """
        results = self.db.execute_query("""
            SELECT transfer_trigger_action, target_object_color,
                   target_object_signature, confidence, occurrence_count
            FROM control_transfer_patterns
            WHERE game_type = ? AND level_number = ? AND confidence >= 0.5
            ORDER BY confidence DESC
        """, (game_type, level_number))
        
        return [
            {
                'trigger_action': r['transfer_trigger_action'],
                'target_color': r['target_object_color'],
                'target_signature': r['target_object_signature'],
                'confidence': r['confidence'],
                'occurrences': r['occurrence_count']
            }
            for r in (results or [])
        ]
    
    def record_indirect_causation(
        self,
        game_id: str,
        level_number: int,
        action_number: int,
        controlled_color: int,
        controlled_action: str,
        controlled_movement: Tuple[float, float],
        affected_color: int,
        affected_effect: str,
        affected_movement: Optional[Tuple[float, float]] = None,
        affected_details: Optional[Dict] = None,
        causation_type: str = 'unknown',
        causation_distance: float = 0.0
    ) -> None:
        """
        Record an indirect causation event: "I control X, X affected Y"
        
        This is when my controlled object causes a change in another object,
        but I still control the original object (not a transfer).
        
        Args:
            game_id: Current game
            level_number: Current level
            action_number: When this happened
            controlled_color: Color of object I control
            controlled_action: What action I took (ACTION1-4)
            controlled_movement: How my object moved (dx, dy)
            affected_color: Color of affected object
            affected_effect: 'moved', 'disappeared', 'appeared', 'color_changed', 'transformed'
            affected_movement: If moved, (dx, dy) of affected object
            affected_details: Additional details as dict
            causation_type: 'collision', 'trigger', 'push', 'remote'
            causation_distance: Distance between controlled and affected objects
        """
        ctrl_dx, ctrl_dy = controlled_movement
        aff_dx, aff_dy = affected_movement if affected_movement else (None, None)
        
        self.db.execute_query("""
            INSERT INTO indirect_causation_events
            (game_id, level_number, action_number,
             controlled_object_color, controlled_action,
             controlled_movement_x, controlled_movement_y,
             affected_object_color, affected_effect_type,
             affected_movement_x, affected_movement_y,
             affected_details, causation_type, causation_distance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (game_id, level_number, action_number,
              controlled_color, controlled_action, ctrl_dx, ctrl_dy,
              affected_color, affected_effect, aff_dx, aff_dy,
              json.dumps(affected_details) if affected_details else None,
              causation_type, causation_distance))
        
        logger.debug(
            f"[INDIRECT-CAUSE] {game_id} L{level_number}: "
            f"color {controlled_color} {controlled_action} -> "
            f"color {affected_color} {affected_effect} ({causation_type})"
        )
    
    def verify_still_controlled(
        self,
        game_id: str,
        level_number: int,
        expected_color: int,
        frame_before: Dict,
        frame_after: Dict,
        action_taken: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Verify that we still control the expected object after an action.
        
        This distinguishes control transfer from indirect causation:
        - If expected_color moved in action direction: still controlled
        - If expected_color didn't move but another did: control transferred
        - If nothing moved: ambiguous
        
        Args:
            game_id: Current game
            level_number: Current level
            expected_color: The color we think we control
            frame_before: Grid state before action
            frame_after: Grid state after action
            action_taken: ACTION1-4 that was taken
        
        Returns:
            (still_controlled: bool, new_controlled_color: Optional[int])
        """
        ACTION_DIRECTION = {
            'ACTION1': (0, -1), 'action_1': (0, -1),
            'ACTION2': (0, 1), 'action_2': (0, 1),
            'ACTION3': (-1, 0), 'action_3': (-1, 0),
            'ACTION4': (1, 0), 'action_4': (1, 0),
        }
        
        expected_dir = ACTION_DIRECTION.get(action_taken)
        if not expected_dir:
            return (True, None)  # Non-directional action, assume still controlled
        
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return (True, None)
        
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        dx_expected, dy_expected = expected_dir
        
        # Check if expected_color moved in the right direction
        expected_key = f"color_{expected_color}"
        if expected_key in objects_before and expected_key in objects_after:
            pos_before = objects_before[expected_key]
            pos_after = objects_after[expected_key]
            
            cx_before = sum(p[0] for p in pos_before) / len(pos_before)
            cy_before = sum(p[1] for p in pos_before) / len(pos_before)
            cx_after = sum(p[0] for p in pos_after) / len(pos_after)
            cy_after = sum(p[1] for p in pos_after) / len(pos_after)
            
            dx_actual = cx_after - cx_before
            dy_actual = cy_after - cy_before
            
            # Check if movement matches expected direction
            moved_correctly = False
            if dx_expected != 0:
                moved_correctly = (dx_expected > 0 and dx_actual > 0.3) or (dx_expected < 0 and dx_actual < -0.3)
            if dy_expected != 0:
                moved_correctly = (dy_expected > 0 and dy_actual > 0.3) or (dy_expected < 0 and dy_actual < -0.3)
            
            if moved_correctly:
                return (True, None)  # Still control expected object
        
        # Expected object didn't move correctly - check if something else did
        for obj_id, pos_before in objects_before.items():
            if obj_id == expected_key:
                continue
            if obj_id not in objects_after:
                continue
            
            pos_after = objects_after[obj_id]
            
            cx_before = sum(p[0] for p in pos_before) / len(pos_before)
            cy_before = sum(p[1] for p in pos_before) / len(pos_before)
            cx_after = sum(p[0] for p in pos_after) / len(pos_after)
            cy_after = sum(p[1] for p in pos_after) / len(pos_after)
            
            dx_actual = cx_after - cx_before
            dy_actual = cy_after - cy_before
            
            moved_correctly = False
            if dx_expected != 0:
                moved_correctly = (dx_expected > 0 and dx_actual > 0.3) or (dx_expected < 0 and dx_actual < -0.3)
            if dy_expected != 0:
                moved_correctly = (dy_expected > 0 and dy_actual > 0.3) or (dy_expected < 0 and dy_actual < -0.3)
            
            if moved_correctly:
                # Found a different object that moved - control transferred!
                # obj_id can be 'color_N' string or just N as int
                if isinstance(obj_id, str) and obj_id.startswith('color_'):
                    new_color = int(obj_id.replace('color_', ''))
                else:
                    new_color = int(obj_id)
                return (False, new_color)
        
        # Nothing moved in expected direction - ambiguous
        return (True, None)
    
    # =========================================================================
    # PERCEPTUAL PRIMITIVE 2: GRID REGION CLASSIFICATION METHODS
    # =========================================================================
    
    def classify_grid_regions(
        self,
        game_id: str,
        level_number: int,
        frame: Dict,
        action_history: Optional[List[Dict]] = None,
        frame_history: Optional[List[Dict]] = None
    ) -> Dict[Tuple[int, int], str]:
        """
        Classify grid regions as 'playfield', 'ui', 'decoration', or 'unknown'.
        
        Divides the 64x64 grid into 8x8 macro-regions and classifies each.
        
        Args:
            game_id: Current game
            level_number: Current level
            frame: Current frame with 'grid' field
            action_history: Optional list of actions taken
            frame_history: Optional list of frame snapshots
        
        Returns:
            Dict mapping (region_x, region_y) to classification
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        grid = frame.get('grid', [])
        
        if not grid:
            return {}
        
        # First, check if we have existing classifications
        existing = self.db.execute_query("""
            SELECT region_x, region_y, classification, confidence
            FROM grid_region_classification
            WHERE game_type = ? AND level_number = ? AND confidence >= 0.6
        """, (game_type, level_number))
        
        if existing and len(existing) >= 32:  # At least half the regions classified
            return {
                (r['region_x'], r['region_y']): r['classification']
                for r in existing
            }
        
        # Otherwise, analyze current frame
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        
        region_size_y = max(1, height // 8)
        region_size_x = max(1, width // 8)
        
        classifications = {}
        
        for ry in range(8):
            for rx in range(8):
                min_y = ry * region_size_y
                max_y = min((ry + 1) * region_size_y, height)
                min_x = rx * region_size_x
                max_x = min((rx + 1) * region_size_x, width)
                
                # Analyze region content
                region_pixels = []
                for y in range(min_y, max_y):
                    for x in range(min_x, max_x):
                        if y < len(grid) and x < len(grid[y]):
                            region_pixels.append(grid[y][x])
                
                if not region_pixels:
                    classifications[(rx, ry)] = 'unknown'
                    continue
                
                # Heuristics for classification
                unique_colors = len(set(region_pixels))
                non_zero = sum(1 for p in region_pixels if p != 0)
                total_pixels = len(region_pixels)
                
                # Mostly empty -> likely decoration or playfield
                if non_zero < total_pixels * 0.1:
                    classification = 'playfield'  # Empty playfield area
                # Very few unique colors, small area with content -> likely UI
                elif unique_colors <= 2 and non_zero < total_pixels * 0.3:
                    classification = 'ui'
                # Edge regions with little activity -> likely decoration
                elif (rx in [0, 7] or ry in [0, 7]) and unique_colors <= 2:
                    classification = 'decoration'
                else:
                    classification = 'playfield'
                
                classifications[(rx, ry)] = classification
                
                # Store/update in database
                self._update_region_classification(
                    game_type, level_number, rx, ry,
                    min_x, max_x, min_y, max_y,
                    classification, 'initial_heuristic',
                    confidence=0.5
                )
        
        return classifications
    
    def _update_region_classification(
        self,
        game_type: str,
        level_number: int,
        region_x: int,
        region_y: int,
        min_px: int,
        max_px: int,
        min_py: int,
        max_py: int,
        classification: str,
        reason: str,
        confidence: float
    ) -> None:
        """Update or insert a region classification."""
        existing = self.db.execute_query("""
            SELECT classification_id, total_observations, classification
            FROM grid_region_classification
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level_number, region_x, region_y))
        
        if existing:
            # Update - increase confidence if same classification, decrease if different
            old_class = existing[0]['classification']
            observations = existing[0]['total_observations'] + 1
            
            if old_class == classification:
                new_confidence = min(0.95, confidence + 0.05)
            else:
                new_confidence = max(0.1, confidence - 0.1)
            
            self.db.execute_query("""
                UPDATE grid_region_classification
                SET classification = ?, classification_reason = ?,
                    total_observations = ?, confidence = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE classification_id = ?
            """, (classification, reason, observations, new_confidence,
                  existing[0]['classification_id']))
        else:
            self.db.execute_query("""
                INSERT INTO grid_region_classification
                (game_type, level_number, region_x, region_y,
                 region_min_pixel_x, region_max_pixel_x,
                 region_min_pixel_y, region_max_pixel_y,
                 classification, classification_reason, confidence,
                 total_observations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (game_type, level_number, region_x, region_y,
                  min_px, max_px, min_py, max_py,
                  classification, reason, confidence))
    
    def get_playfield_bounds(
        self,
        game_type: str,
        level_number: int
    ) -> Tuple[int, int, int, int]:
        """
        Get the bounding box of the playfield (non-UI/decoration regions).
        
        Returns:
            (min_x, min_y, max_x, max_y) in pixel coordinates
        """
        playfield_regions = self.db.execute_query("""
            SELECT region_min_pixel_x, region_max_pixel_x,
                   region_min_pixel_y, region_max_pixel_y
            FROM grid_region_classification
            WHERE game_type = ? AND level_number = ? AND classification = 'playfield'
        """, (game_type, level_number))
        
        if not playfield_regions:
            return (0, 0, 63, 63)  # Default to full grid
        
        min_x = min(r['region_min_pixel_x'] for r in playfield_regions)
        min_y = min(r['region_min_pixel_y'] for r in playfield_regions)
        max_x = max(r['region_max_pixel_x'] for r in playfield_regions)
        max_y = max(r['region_max_pixel_y'] for r in playfield_regions)
        
        return (min_x, min_y, max_x, max_y)
    
    def is_ui_region(self, game_type: str, level_number: int, x: int, y: int) -> bool:
        """
        Check if a pixel coordinate is in a UI region.
        
        Args:
            game_type: Game type
            level_number: Level number
            x, y: Pixel coordinates
        
        Returns:
            True if in UI region, False otherwise
        """
        # Convert pixel to region
        region_x = min(x // 8, 7)
        region_y = min(y // 8, 7)
        
        result = self.db.execute_query("""
            SELECT classification
            FROM grid_region_classification
            WHERE game_type = ? AND level_number = ? 
                  AND region_x = ? AND region_y = ?
        """, (game_type, level_number, region_x, region_y))
        
        if result:
            return result[0]['classification'] == 'ui'
        return False
    
    # =========================================================================
    # PERCEPTUAL PRIMITIVE 3: RESOURCE COUNTER DETECTION METHODS
    # =========================================================================
    
    def detect_resource_counters(
        self,
        game_id: str,
        level_number: int,
        frame: Dict,
        previous_frame: Optional[Dict] = None,
        score_change: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect potential resource counters in the frame.
        
        Looks for small isolated objects in UI regions that might be counters.
        
        Args:
            game_id: Current game
            level_number: Current level
            frame: Current frame
            previous_frame: Previous frame for change detection
            score_change: If score changed, helps validate counters
        
        Returns:
            List of detected counters with type and value estimates
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        grid = frame.get('grid', [])
        
        if not grid:
            return []
        
        # First check for known counters
        known = self.db.execute_query("""
            SELECT region_x, region_y, counter_type, current_value, confidence
            FROM detected_resource_counters
            WHERE game_type = ? AND level_number = ? AND confidence >= 0.5
        """, (game_type, level_number))
        
        if known:
            # Update known counters with current values
            counters = []
            for k in known:
                counters.append({
                    'region': (k['region_x'], k['region_y']),
                    'type': k['counter_type'],
                    'value': k['current_value'],
                    'confidence': k['confidence']
                })
            return counters
        
        # Scan for new counters in UI regions
        detected = []
        
        for ry in range(8):
            for rx in range(8):
                if not self.is_ui_region(game_type, level_number, rx * 8, ry * 8):
                    continue
                
                # Analyze this UI region for counter-like objects
                region_pixels = self._extract_region_pixels(grid, rx, ry)
                
                if not region_pixels:
                    continue
                
                # Count non-zero pixels (potential counter indicator)
                non_zero = [p for p in region_pixels if p != 0]
                
                # Counters are typically small (1-5 cells) with distinctive colors
                if 1 <= len(non_zero) <= 10:
                    detected.append({
                        'region': (rx, ry),
                        'type': 'unknown',
                        'value': len(non_zero),  # Rough estimate
                        'confidence': 0.3
                    })
        
        return detected
    
    def _extract_region_pixels(
        self,
        grid: List[List[int]],
        region_x: int,
        region_y: int
    ) -> List[int]:
        """Extract all pixels from a region."""
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        
        region_size_y = max(1, height // 8)
        region_size_x = max(1, width // 8)
        
        min_y = region_y * region_size_y
        max_y = min((region_y + 1) * region_size_y, height)
        min_x = region_x * region_size_x
        max_x = min((region_x + 1) * region_size_x, width)
        
        pixels = []
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if y < len(grid) and x < len(grid[y]):
                    pixels.append(grid[y][x])
        
        return pixels
    
    # =========================================================================
    # PERCEPTUAL PRIMITIVE 4: VALENCE ASSOCIATION METHODS
    # =========================================================================
    
    def record_valence_association(
        self,
        game_id: str,
        level_number: int,
        trigger_type: str,
        trigger_action: Optional[str],
        trigger_object_color: Optional[int],
        trigger_target_color: Optional[int],
        consequence_type: str,
        consequence_details: Optional[Dict],
        valence: float
    ) -> None:
        """
        Record a valence association: "This interaction = good/bad"
        
        Args:
            game_id: Current game
            level_number: Current level
            trigger_type: 'collision', 'action', 'proximity', 'selection'
            trigger_action: ACTION1-7 if applicable
            trigger_object_color: Object color involved
            trigger_target_color: Target of interaction
            consequence_type: 'score_change', 'counter_change', 'game_end', 'level_end'
            consequence_details: Additional info
            valence: -1.0 (very bad) to +1.0 (very good)
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Check for existing association
        existing = self.db.execute_query("""
            SELECT association_id, valence, observation_count, consistent_count
            FROM valence_associations
            WHERE game_type = ? AND level_number = ?
                  AND trigger_type = ? AND consequence_type = ?
                  AND (trigger_object_color = ? OR (trigger_object_color IS NULL AND ? IS NULL))
                  AND (trigger_target_color = ? OR (trigger_target_color IS NULL AND ? IS NULL))
        """, (game_type, level_number, trigger_type, consequence_type,
              trigger_object_color, trigger_object_color,
              trigger_target_color, trigger_target_color))
        
        if existing:
            row = existing[0]
            new_obs = row['observation_count'] + 1
            
            # Check if this observation is consistent with previous
            valence_matches = (row['valence'] > 0 and valence > 0) or (row['valence'] < 0 and valence < 0)
            new_consistent = row['consistent_count'] + (1 if valence_matches else 0)
            
            # Average valence with exponential moving average
            new_valence = row['valence'] * 0.8 + valence * 0.2
            new_confidence = new_consistent / new_obs
            
            self.db.execute_query("""
                UPDATE valence_associations
                SET valence = ?, observation_count = ?, consistent_count = ?,
                    confidence = ?, last_observed = CURRENT_TIMESTAMP
                WHERE association_id = ?
            """, (new_valence, new_obs, new_consistent, new_confidence,
                  row['association_id']))
        else:
            self.db.execute_query("""
                INSERT INTO valence_associations
                (game_type, level_number, trigger_type, trigger_action,
                 trigger_object_color, trigger_target_color,
                 consequence_type, consequence_details, valence, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.5)
            """, (game_type, level_number, trigger_type, trigger_action,
                  trigger_object_color, trigger_target_color,
                  consequence_type, json.dumps(consequence_details) if consequence_details else None,
                  valence))
    
    def get_object_valence(
        self,
        game_type: str,
        level_number: int,
        object_color: int
    ) -> float:
        """
        Get the overall valence associated with an object color.
        
        Returns average valence across all interactions involving this object.
        """
        results = self.db.execute_query("""
            SELECT valence, confidence
            FROM valence_associations
            WHERE game_type = ? AND level_number = ?
                  AND (trigger_object_color = ? OR trigger_target_color = ?)
                  AND confidence >= 0.4
        """, (game_type, level_number, object_color, object_color))
        
        if not results:
            return 0.0  # Neutral if unknown
        
        # Weighted average by confidence
        total_weight = sum(r['confidence'] for r in results)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(r['valence'] * r['confidence'] for r in results)
        return weighted_sum / total_weight
    
    def get_all_object_valences(
        self,
        game_type: str,
        level_number: int
    ) -> Dict[int, float]:
        """
        Get valence for all known objects in a level.
        
        Returns dict mapping object_color to valence.
        """
        results = self.db.execute_query("""
            SELECT trigger_object_color, trigger_target_color, valence, confidence
            FROM valence_associations
            WHERE game_type = ? AND level_number = ? AND confidence >= 0.4
        """, (game_type, level_number))
        
        valences: Dict[int, List[Tuple[float, float]]] = {}  # color -> [(valence, confidence)]
        
        for r in (results or []):
            for color in [r['trigger_object_color'], r['trigger_target_color']]:
                if color is not None:
                    if color not in valences:
                        valences[color] = []
                    valences[color].append((r['valence'], r['confidence']))
        
        # Compute weighted averages
        result = {}
        for color, vals in valences.items():
            total_weight = sum(v[1] for v in vals)
            if total_weight > 0:
                result[color] = sum(v[0] * v[1] for v in vals) / total_weight
        
        return result
    
    # =========================================================================
    # PERCEPTUAL PRIMITIVE 5: GOAL STATE INFERENCE METHODS
    # =========================================================================
    
    def infer_goal_from_level_end(
        self,
        game_id: str,
        level_number: int,
        final_frame: Dict,
        initial_frame: Optional[Dict],
        action_history: List[Dict],
        final_score: float,
        level_won: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Infer the goal state from analyzing a level completion.
        
        Compares initial and final states to determine what changed
        that caused the level to end.
        
        Args:
            game_id: Game that was played
            level_number: Level that was completed
            final_frame: Frame at level end
            initial_frame: Frame at level start
            action_history: Actions taken during level
            final_score: Score at level end
            level_won: Whether the level was won
        
        Returns:
            Goal hypothesis dict, or None if couldn't infer
        """
        if not level_won:
            return None  # Only infer from wins
        
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        final_grid = final_frame.get('grid', [])
        initial_grid = initial_frame.get('grid', []) if initial_frame else []
        
        if not final_grid:
            return None
        
        # Analyze what's different between initial and final
        final_objects = self._find_objects_in_grid(final_grid)
        initial_objects = self._find_objects_in_grid(initial_grid) if initial_grid else {}
        
        # Check for "clear all of color X" pattern
        cleared_colors = []
        for obj_id, positions in initial_objects.items():
            if obj_id not in final_objects:
                # obj_id can be 'color_N' string or just N as int
                if isinstance(obj_id, str) and obj_id.startswith('color_'):
                    color = int(obj_id.replace('color_', ''))
                else:
                    color = int(obj_id)
                cleared_colors.append(color)
        
        if cleared_colors:
            # Goal might be "clear all of these colors"
            goal = {
                'goal_type': 'clear_color',
                'goal_params': json.dumps({'colors_to_clear': cleared_colors}),
                'inference_method': 'level_end_analysis',
                'confidence': 0.6
            }
            self._save_goal_inference(game_type, level_number, goal)
            return goal
        
        # Check for "reach position" pattern - where did self-object end up?
        self_obj = self.get_current_self_object(game_id, level_number)
        if self_obj:
            self_color = self_obj['self_object_color']
            self_key = f"color_{self_color}"
            
            if self_key in final_objects:
                final_positions = final_objects[self_key]
                cx = sum(p[0] for p in final_positions) / len(final_positions)
                cy = sum(p[1] for p in final_positions) / len(final_positions)
                
                goal = {
                    'goal_type': 'reach_position',
                    'goal_params': json.dumps({
                        'target_x': round(cx),
                        'target_y': round(cy)
                    }),
                    'inference_method': 'level_end_analysis',
                    'confidence': 0.5
                }
                self._save_goal_inference(game_type, level_number, goal)
                return goal
        
        # Default: unknown goal type
        goal = {
            'goal_type': 'unknown',
            'goal_params': json.dumps({'frame_hash': hash(str(final_grid))}),
            'inference_method': 'level_end_analysis',
            'confidence': 0.3
        }
        self._save_goal_inference(game_type, level_number, goal)
        return goal
    
    def _save_goal_inference(
        self,
        game_type: str,
        level_number: int,
        goal: Dict[str, Any]
    ) -> None:
        """Save a goal inference to the database."""
        # Check for existing
        existing = self.db.execute_query("""
            SELECT goal_id, times_validated
            FROM inferred_goal_states
            WHERE game_type = ? AND level_number = ? AND goal_type = ?
        """, (game_type, level_number, goal['goal_type']))
        
        if existing:
            self.db.execute_query("""
                UPDATE inferred_goal_states
                SET times_validated = times_validated + 1,
                    confidence = MIN(0.95, confidence + 0.1),
                    last_validated = CURRENT_TIMESTAMP
                WHERE goal_id = ?
            """, (existing[0]['goal_id'],))
        else:
            self.db.execute_query("""
                INSERT INTO inferred_goal_states
                (game_type, level_number, goal_type, goal_params,
                 inference_method, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_type, level_number, goal['goal_type'],
                  goal['goal_params'], goal['inference_method'],
                  goal['confidence']))
    
    def get_goal_hypothesis(
        self,
        game_type: str,
        level_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best goal hypothesis for a game/level.
        
        Returns the highest confidence goal inference, or None.
        """
        result = self.db.execute_query("""
            SELECT goal_type, goal_params, confidence, times_validated,
                   inference_method, progress_metric
            FROM inferred_goal_states
            WHERE game_type = ? AND level_number = ?
            ORDER BY confidence DESC, times_validated DESC
            LIMIT 1
        """, (game_type, level_number))
        
        if result:
            row = result[0]
            return {
                'goal_type': row['goal_type'],
                'goal_params': json.loads(row['goal_params']) if row['goal_params'] else {},
                'confidence': row['confidence'],
                'times_validated': row['times_validated'],
                'inference_method': row['inference_method'],
                'progress_metric': row['progress_metric']
            }
        return None
    
    def get_goal_progress(
        self,
        game_type: str,
        level_number: int,
        current_frame: Dict
    ) -> float:
        """
        Estimate progress toward the inferred goal (0.0 to 1.0).
        
        Based on the goal type and current frame state.
        """
        goal = self.get_goal_hypothesis(game_type, level_number)
        
        if not goal:
            return 0.0
        
        grid = current_frame.get('grid', [])
        if not grid:
            return 0.0
        
        current_objects = self._find_objects_in_grid(grid)
        
        if goal['goal_type'] == 'clear_color':
            colors_to_clear = goal['goal_params'].get('colors_to_clear', [])
            if not colors_to_clear:
                return 0.0
            
            # Count how many are still present
            remaining = 0
            for color in colors_to_clear:
                if f"color_{color}" in current_objects:
                    remaining += 1
            
            progress = 1.0 - (remaining / len(colors_to_clear))
            return progress
        
        elif goal['goal_type'] == 'reach_position':
            target_x = goal['goal_params'].get('target_x', 0)
            target_y = goal['goal_params'].get('target_y', 0)
            
            # Find self-object position
            for obj_id, positions in current_objects.items():
                cx = sum(p[0] for p in positions) / len(positions)
                cy = sum(p[1] for p in positions) / len(positions)
                
                # Assuming grid is 64x64, max distance is ~90
                distance = ((cx - target_x) ** 2 + (cy - target_y) ** 2) ** 0.5
                max_distance = 90.0
                progress = 1.0 - min(1.0, distance / max_distance)
                
                return progress
        
        return 0.0  # Unknown goal type

    # ========================================================================
    # CLICK BEHAVIOR CLASSIFICATION SYSTEM (Added 2025-12-25)
    # ========================================================================
    # Three distinct click behaviors for clickable objects:
    # 1. SELF_TOGGLE: Clicking changes THIS object's state (button on/off)
    # 2. TRIGGER: Clicking changes OTHER objects' states (switch opens door)
    # 3. SELECTABLE: Clicking gives movement control ("I became this object")
    #
    # Detection requires testing:
    # - Click object -> observe frame changes
    # - If object itself changed: SELF_TOGGLE
    # - If OTHER objects changed: TRIGGER
    # - Then try ACTION1-4:
    #   - If clicked object moves: SELECTABLE
    #   - If still doesn't move: confirm TOGGLE or TRIGGER only
    # ========================================================================
    
    def classify_click_behavior(
        self,
        game_id: str,
        level: int,
        click_x: int,
        click_y: int,
        object_color: int,
        frame_before_click: List,
        frame_after_click: List,
        frames_after_movement_tests: Optional[Dict[str, List]] = None
    ) -> Dict[str, Any]:
        """
        Classify the behavior type of a clicked object.
        
        Args:
            game_id: Game identifier
            level: Level number
            click_x, click_y: Click coordinates
            object_color: Color of clicked object
            frame_before_click: Grid state before ACTION6 click
            frame_after_click: Grid state after ACTION6 click
            frames_after_movement_tests: Dict mapping ACTION1-4 -> frame after
                                         (for movement verification)
        
        Returns:
            Classification dict with behavior type and evidence
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Analyze what changed from the click itself
        diff = self.get_grid_diff(frame_before_click, frame_after_click)
        
        classification = {
            'object_color': object_color,
            'click_coords': (click_x, click_y),
            'behavior_type': 'unknown',
            'is_self_toggle': False,
            'is_trigger': False,
            'is_selectable': False,
            'movement_verified': False,
            'self_changes': [],
            'other_changes': [],
            'movement_responses': {}
        }
        
        if not diff['changed']:
            # Click had no immediate effect - might still be selectable
            # Need to test movement
            classification['behavior_type'] = 'no_immediate_effect'
        else:
            # Analyze what changed
            self_changed = False
            others_changed = False
            
            # Check if the clicked object itself changed
            if object_color in diff.get('objects_disappeared', {}):
                self_changed = True
                classification['self_changes'].append('disappeared')
            
            if object_color in diff.get('objects_moved', {}):
                self_changed = True
                classification['self_changes'].append('moved')
            
            # Check cell changes at click location
            for change in diff.get('cell_changes', []):
                if change['x'] == click_x and change['y'] == click_y:
                    if change['color_before'] == object_color:
                        self_changed = True
                        classification['self_changes'].append(
                            f"state_change:{change['color_before']}->{change['color_after']}"
                        )
            
            # Check for changes to OTHER objects
            for color in diff.get('objects_disappeared', {}):
                if color != object_color and color != 0:
                    others_changed = True
                    classification['other_changes'].append({
                        'color': color,
                        'change': 'disappeared',
                        'positions': diff['objects_disappeared'][color]
                    })
            
            for color in diff.get('objects_moved', {}):
                if color != object_color and color != 0:
                    others_changed = True
                    classification['other_changes'].append({
                        'color': color,
                        'change': 'moved',
                        'details': diff['objects_moved'][color]
                    })
            
            for color in diff.get('objects_appeared', {}):
                if color != object_color and color != 0:
                    others_changed = True
                    classification['other_changes'].append({
                        'color': color,
                        'change': 'appeared',
                        'positions': diff['objects_appeared'][color]
                    })
            
            # Initial classification from click effect
            classification['is_self_toggle'] = self_changed
            classification['is_trigger'] = others_changed
        
        # Now check movement responses if provided
        if frames_after_movement_tests:
            reference_frame = frame_after_click
            movement_responses = {}
            
            for action, frame_after in frames_after_movement_tests.items():
                action_diff = self.get_grid_diff(reference_frame, frame_after)
                
                # Did the clicked object move in response to this action?
                if object_color in action_diff.get('objects_moved', {}):
                    movement_responses[action] = {
                        'moved': True,
                        'details': action_diff['objects_moved'][object_color]
                    }
                    classification['is_selectable'] = True
                    classification['movement_verified'] = True
                else:
                    movement_responses[action] = {'moved': False}
            
            classification['movement_responses'] = movement_responses
        
        # Determine final behavior type
        # ================================================================
        # BEHAVIOR TYPES:
        # - selectable: Can be selected and then moved with ACTION1-4
        # - trigger_only: Clicking causes changes to OTHER objects
        # - self_toggle_only: Clicking changes only THIS object
        # - toggle_and_trigger: Clicking changes both self and others
        # - reference: Object that defines a pattern for others to match
        #              (doesn't change, doesn't trigger, but has visual info)
        # - unknown: Insufficient data to classify
        # ================================================================
        if classification['is_selectable'] and classification['movement_verified']:
            classification['behavior_type'] = 'selectable'
        elif classification['is_trigger'] and not classification['is_self_toggle']:
            classification['behavior_type'] = 'trigger_only'
        elif classification['is_self_toggle'] and not classification['is_trigger']:
            classification['behavior_type'] = 'self_toggle_only'
        elif classification['is_self_toggle'] and classification['is_trigger']:
            classification['behavior_type'] = 'toggle_and_trigger'
        elif not diff['changed'] and classification.get('movement_verified'):
            classification['behavior_type'] = 'selectable'
        elif not diff['changed'] and not classification.get('movement_verified'):
            # ================================================================
            # REFERENCE DETECTION (FT09-style objects)
            # ================================================================
            # Object that:
            # 1. Does NOT change when clicked (no toggle)
            # 2. Does NOT trigger changes to other objects
            # 3. Does NOT move when ACTION1-4 are applied
            # These are "template" objects that define patterns for goals.
            # Example: FT09's center grid shows the target pattern.
            # ================================================================
            classification['behavior_type'] = 'reference'
            classification['is_reference'] = True
        else:
            classification['behavior_type'] = 'unknown'
        
        # Save to database
        self._save_click_behavior_classification(
            game_type=game_type,
            level=level,
            object_color=object_color,
            classification=classification
        )
        
        logger.info(
            f"[CLICK CLASSIFY] {game_type} L{level} color={object_color}: "
            f"{classification['behavior_type']} "
            f"(toggle={classification['is_self_toggle']}, "
            f"trigger={classification['is_trigger']}, "
            f"select={classification['is_selectable']}, "
            f"ref={classification.get('is_reference', False)})"
        )
        
        return classification
    
    def _save_click_behavior_classification(
        self,
        game_type: str,
        level: int,
        object_color: int,
        classification: Dict[str, Any]
    ) -> None:
        """Save click behavior classification to database."""
        import json
        
        behavior_type = classification.get('behavior_type', 'unknown')
        is_self_toggle = classification.get('is_self_toggle', False)
        is_trigger = classification.get('is_trigger', False)
        is_selectable = classification.get('is_selectable', False)
        movement_verified = classification.get('movement_verified', False)
        other_changes = classification.get('other_changes', [])
        
        # Get affected object colors from other_changes
        affects_colors = [c['color'] for c in other_changes if 'color' in c]
        
        # REFERENCE flag (for FT09-style pattern template objects)
        is_reference = classification.get('is_reference', False)
        
        # Check if entry exists
        existing = self.db.execute_query("""
            SELECT discovery_count, state_changes_observed, movement_test_count
            FROM object_selection_state
            WHERE game_type = ? AND level_number = ? AND object_color = ?
        """, (game_type, level, object_color))
        
        if existing:
            old_count = existing[0]['discovery_count'] or 1
            old_state_changes = existing[0]['state_changes_observed'] or 0
            old_movement_tests = existing[0]['movement_test_count'] or 0
            
            # Calculate new confidence based on observations
            new_confidence = min(0.95, 0.5 + (old_count * 0.05))
            
            self.db.execute_query("""
                UPDATE object_selection_state
                SET click_behavior_type = ?,
                    is_self_toggle = ?,
                    is_trigger = ?,
                    is_selectable = ?,
                    is_moveable = ?,
                    is_reference = ?,
                    movement_verified = ?,
                    affects_objects = ?,
                    state_changes_observed = ?,
                    movement_test_count = ?,
                    confidence = ?,
                    discovery_count = discovery_count + 1,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ? AND object_color = ?
            """, (
                behavior_type,
                1 if is_self_toggle else 0,
                1 if is_trigger else 0,
                1 if is_selectable else 0,
                1 if (is_selectable and movement_verified) else 0,
                1 if is_reference else 0,
                1 if movement_verified else 0,
                json.dumps(affects_colors) if affects_colors else None,
                old_state_changes + (1 if is_self_toggle or is_trigger else 0),
                old_movement_tests + (1 if movement_verified else 0),
                new_confidence,
                game_type, level, object_color
            ))
        else:
            # Insert new entry
            self.db.execute_query("""
                INSERT INTO object_selection_state
                (game_type, level_number, object_color, 
                 click_behavior_type, is_self_toggle, is_trigger, is_selectable,
                 is_moveable, is_button, is_reference, movement_verified, affects_objects,
                 state_changes_observed, movement_test_count, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.5)
            """, (
                game_type, level, object_color,
                behavior_type,
                1 if is_self_toggle else 0,
                1 if is_trigger else 0,
                1 if is_selectable else 0,
                1 if (is_selectable and movement_verified) else 0,
                1 if (is_self_toggle and not is_selectable) else 0,  # is_button
                1 if is_reference else 0,  # is_reference (FT09-style pattern template)
                1 if movement_verified else 0,
                json.dumps(affects_colors) if affects_colors else None,
                1 if is_self_toggle or is_trigger else 0,
                1 if movement_verified else 0
            ))
    
    def get_click_behavior(
        self,
        game_type: str,
        level: int,
        object_color: Optional[int] = None,
        min_confidence: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Get known click behaviors for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            object_color: Specific color to query (or None for all)
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of click behavior dicts
        """
        if object_color is not None:
            results = self.db.execute_query("""
                SELECT object_color, click_behavior_type, is_self_toggle,
                       is_trigger, is_selectable, is_moveable, is_reference, movement_verified,
                       affects_objects, state_changes_observed, movement_test_count,
                       confidence
                FROM object_selection_state
                WHERE game_type = ? AND level_number = ? AND object_color = ?
                      AND confidence >= ?
            """, (game_type, level, object_color, min_confidence))
        else:
            results = self.db.execute_query("""
                SELECT object_color, click_behavior_type, is_self_toggle,
                       is_trigger, is_selectable, is_moveable, is_reference, movement_verified,
                       affects_objects, state_changes_observed, movement_test_count,
                       confidence
                FROM object_selection_state
                WHERE game_type = ? AND level_number = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (game_type, level, min_confidence))
        
        behaviors = []
        for row in results or []:
            behaviors.append({
                'object_color': row['object_color'],
                'behavior_type': row['click_behavior_type'] or 'unknown',
                'is_self_toggle': bool(row['is_self_toggle']),
                'is_trigger': bool(row['is_trigger']),
                'is_selectable': bool(row['is_selectable']),
                'is_moveable': bool(row['is_moveable']),
                'is_reference': bool(row.get('is_reference', False)),  # FT09-style pattern template
                'movement_verified': bool(row['movement_verified']),
                'affects_objects': json.loads(row['affects_objects'] or '[]'),
                'state_changes_observed': row['state_changes_observed'] or 0,
                'movement_test_count': row['movement_test_count'] or 0,
                'confidence': row['confidence']
            })
        return behaviors
    
    def systematic_click_discovery(
        self,
        game_id: str,
        level: int,
        current_frame: List,
        available_colors: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest next click action for systematic object discovery.
        
        Prioritizes testing objects that haven't been tested yet,
        or have low confidence classifications.
        
        Args:
            game_id: Game identifier
            level: Level number
            current_frame: Current grid state
            available_colors: Colors of objects visible in frame
        
        Returns:
            Suggested click action or None if all objects tested
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Get existing knowledge
        known_behaviors = self.get_click_behavior(game_type, level, min_confidence=0.0)
        known_colors = {b['object_color'] for b in known_behaviors}
        
        # Find untested colors
        untested = [c for c in available_colors if c not in known_colors and c != 0]
        
        if untested:
            # Test an untested object
            target_color = untested[0]
            objects = self._find_objects_in_grid(current_frame)
            
            if target_color in objects:
                positions = objects[target_color]
                # Get center of object
                cx = sum(p[0] for p in positions) // len(positions)
                cy = sum(p[1] for p in positions) // len(positions)
                
                return {
                    'action': 'ACTION6',
                    'x': cx,
                    'y': cy,
                    'reason': f'Testing untested object color {target_color}',
                    'target_color': target_color,
                    'phase': 'initial_click'
                }
        
        # Check for objects needing movement verification
        for behavior in known_behaviors:
            if behavior['behavior_type'] == 'no_immediate_effect' and not behavior['movement_verified']:
                target_color = behavior['object_color']
                objects = self._find_objects_in_grid(current_frame)
                
                if target_color in objects:
                    positions = objects[target_color]
                    cx = sum(p[0] for p in positions) // len(positions)
                    cy = sum(p[1] for p in positions) // len(positions)
                    
                    return {
                        'action': 'ACTION6',
                        'x': cx,
                        'y': cy,
                        'reason': f'Re-testing color {target_color} for movement verification',
                        'target_color': target_color,
                        'phase': 'retest_for_movement'
                    }
        
        # All objects tested
        return None


# ============================================================================
# TWO-STREAMS CONSCIOUSNESS: WEAVING REPORTER
# ============================================================================

class WeavingReporter:
    """
    Generates self-reflection "weaving reports" for every action.
    
    Philosophy: Every action sent to ARC API includes full self_reflection weaving data.
    This is the agent's introspection visible in every API call.
    
    Local Database Storage: Uses sampling to prevent bloat:
    - Sampling Rate: Store 1 in 10 decisions locally (10%)
    - Exception: Always store if conflict_detected = True
    - Exception: Always store level completion / game end decisions
    """
    
    # Sampling rate for local storage (10% of non-exceptional decisions)
    SAMPLING_RATE = 0.1
    
    def __init__(self, db: DatabaseInterface):
        """Initialize weaving reporter."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure decision_weaving_reports table exists."""
        # Table should be created in Phase 1, but ensure it exists
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS decision_weaving_reports (
                report_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER,
                action_number INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                emotional_input REAL,
                semantic_input REAL,
                identity_input REAL,
                private_memory_strength REAL,
                network_recommendation_strength REAL,
                self_network_bias REAL,
                final_decision_weight REAL,
                chosen_action TEXT,
                alternative_action TEXT,
                conflict_detected BOOLEAN DEFAULT FALSE,
                outcome_correct BOOLEAN,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_weaving_agent_game 
            ON decision_weaving_reports(agent_id, game_id)
        """)
    
    def generate_report(
        self,
        agent_id: str,
        game_id: str,
        level_number: int,
        action_number: int,
        chosen_action: str,
        private_memory_strength: float,
        network_recommendation_strength: float,
        self_network_bias: float,
        navigation_state: float,
        role_confidence: float,
        role_fit_score: float,
        sensation_profile: Dict,
        alternative_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weaving report for an action decision.
        
        This is called for EVERY action to produce API-ready self-reflection.
        
        Args:
            agent_id: Agent making the decision
            game_id: Current game
            level_number: Current level
            action_number: Action counter in this game
            chosen_action: The action being taken
            private_memory_strength: How strong agent's own memory signal is (0-1)
            network_recommendation_strength: How strong network's recommendation is (0-1)
            self_network_bias: Agent's bias toward self (0=network, 1=self)
            navigation_state: Agent's emotional state (-1 to 1)
            role_confidence: Agent's confidence in their role (0-1)
            role_fit_score: How well agent fits their role (0-1)
            sensation_profile: Agent's sensation mappings
            alternative_action: What network recommended (if different)
            
        Returns:
            Complete weaving report dictionary for API
        """
        import uuid
        from datetime import datetime
        
        # Calculate internal network inputs
        # Emotional: Map navigation_state from [-1,1] to [0,1]
        emotional_input = (navigation_state + 1.0) / 2.0
        
        # Semantic: Average of top sensation scores (if any)
        object_sensations = sensation_profile.get('object_sensations', {})
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = sum(top_sensations) / len(top_sensations) if top_sensations else 0.5
            # Normalize to 0-1 range (sensations are -1 to 1)
            semantic_input = (semantic_input + 1.0) / 2.0
        else:
            semantic_input = 0.5  # Neutral if no sensations
        
        # Identity: Average of role_confidence and role_fit_score
        identity_input = (role_confidence + role_fit_score) / 2.0
        
        # Calculate final decision weight using Two-Streams formula
        # final_weight = private * bias + network * (1 - bias)
        alpha = self_network_bias
        final_decision_weight = (
            private_memory_strength * alpha + 
            network_recommendation_strength * (1.0 - alpha)
        )
        
        # Detect conflict (significant difference between private and network)
        conflict_detected = abs(private_memory_strength - network_recommendation_strength) > 0.3
        
        # Build human-readable summary
        emotion_label = self._get_emotion_label(navigation_state)
        
        report = {
            'report_id': f"weave_{uuid.uuid4().hex[:12]}",
            'agent_id': agent_id,
            'game_id': game_id,
            'level_number': level_number,
            'action_number': action_number,
            'timestamp': datetime.now().isoformat(),
            
            # Internal networks (Three Streams)
            'emotional_input': round(emotional_input, 3),
            'semantic_input': round(semantic_input, 3),
            'identity_input': round(identity_input, 3),
            
            # Two-Streams weighting
            'private_memory_strength': round(private_memory_strength, 3),
            'network_recommendation_strength': round(network_recommendation_strength, 3),
            'self_network_bias': round(self_network_bias, 3),
            'final_decision_weight': round(final_decision_weight, 3),
            
            # Decision
            'chosen_action': chosen_action,
            'alternative_action': alternative_action,
            'conflict_detected': conflict_detected,
            
            # Narrative summary
            'narrative': self._build_narrative(
                emotion_label, private_memory_strength, network_recommendation_strength,
                alpha, chosen_action, alternative_action, conflict_detected
            ),
            
            # Outcome (to be filled in later)
            'outcome_correct': None
        }
        
        return report
    
    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get human-readable emotion label from navigation state."""
        if navigation_state < -0.5:
            return 'frustrated'
        elif navigation_state < -0.1:
            return 'cautious'
        elif navigation_state < 0.1:
            return 'neutral'
        elif navigation_state < 0.5:
            return 'curious'
        else:
            return 'confident'
    
    def _build_narrative(
        self,
        emotion: str,
        private_strength: float,
        network_strength: float,
        alpha: float,
        chosen_action: str,
        alternative: Optional[str],
        conflict: bool
    ) -> str:
        """Build human-readable narrative of decision."""
        parts = []
        
        # Emotional state
        parts.append(f"Feeling {emotion}")
        
        # Stream preference
        if alpha > 0.6:
            parts.append("trusting own experience")
        elif alpha < 0.4:
            parts.append("following network wisdom")
        else:
            parts.append("balancing self and network")
        
        # Conflict
        if conflict:
            if alternative:
                parts.append(f"(conflicted: network suggested {alternative})")
            else:
                parts.append("(internal conflict detected)")
        
        # Decision
        parts.append(f"-> {chosen_action}")
        
        return " | ".join(parts)
    
    def format_for_api(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format weaving report for inclusion in API reasoning payload.
        
        Returns a compact version suitable for the 16KB limit.
        """
        return {
            'emotional_network': report['emotional_input'],
            'semantic_network': report['semantic_input'],
            'identity_network': report['identity_input'],
            'private_memory': report['private_memory_strength'],
            'network_wisdom': report['network_recommendation_strength'],
            'self_trust_bias': report['self_network_bias'],
            'decision_weight': report['final_decision_weight'],
            'conflict': report['conflict_detected'],
            'narrative': report['narrative']
        }
    
    def should_store_locally(self, report: Dict[str, Any], is_terminal: bool = False) -> bool:
        """
        Determine if this report should be stored in local database.
        
        Storage criteria (to prevent bloat):
        - Always store if conflict_detected = True
        - Always store if is_terminal (level/game end)
        - Otherwise, sample at 10% rate
        """
        import random
        
        # Always store conflicts
        if report.get('conflict_detected'):
            return True
        
        # Always store terminal decisions
        if is_terminal:
            return True
        
        # Otherwise, sample
        return random.random() < self.SAMPLING_RATE
    
    def store_report(self, report: Dict[str, Any]) -> None:
        """Store a weaving report in the database."""
        self.db.execute_query("""
            INSERT INTO decision_weaving_reports
            (report_id, agent_id, game_id, level_number, action_number, timestamp,
             emotional_input, semantic_input, identity_input,
             private_memory_strength, network_recommendation_strength,
             self_network_bias, final_decision_weight,
             chosen_action, alternative_action, conflict_detected, outcome_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report['report_id'], report['agent_id'], report['game_id'],
            report['level_number'], report['action_number'], report['timestamp'],
            report['emotional_input'], report['semantic_input'], report['identity_input'],
            report['private_memory_strength'], report['network_recommendation_strength'],
            report['self_network_bias'], report['final_decision_weight'],
            report['chosen_action'], report['alternative_action'],
            report['conflict_detected'], report.get('outcome_correct')
        ))
    
    def update_outcome(self, report_id: str, outcome_correct: bool) -> None:
        """Update the outcome for a stored report (for meta-learning)."""
        self.db.execute_query("""
            UPDATE decision_weaving_reports
            SET outcome_correct = ?
            WHERE report_id = ?
        """, (outcome_correct, report_id))


# ============================================================================
# COGNITIVE STAGE SYSTEM (Developmental Progression)
# ============================================================================

class CognitiveStageSystem:
    """
    Tracks and evolves agent cognitive development through three stages:
    
    1. PREOPERATIONAL (Early Development)
       - Explores through action-effect observation
       - No planning, reactive behavior
       - Learning object permanence and causation
       
    2. CONCRETE_OPERATIONAL (Learned Patterns)
       - Can apply learned sequences
       - Understands conservation and reversibility
       - Logical thinking about concrete objects
       
    3. FORMAL_OPERATIONAL (Abstract Reasoning)
       - Hypothetical-deductive reasoning
       - Can create and test hypotheses
       - Abstract pattern generalization
    
    Stage transitions based on demonstrated competencies, not age/time.
    """
    
    # Stage names (Piaget-based, adapted for AI agents)
    PREOPERATIONAL = 'preoperational'
    CONCRETE_OPERATIONAL = 'concrete_operational'
    FORMAL_OPERATIONAL = 'formal_operational'
    
    # Competency thresholds for stage transitions
    COMPETENCIES = {
        'preoperational_to_concrete': {
            'games_played': 5,          # Minimum experience
            'sequences_discovered': 1,   # Can find a winning pattern
            'object_control_learned': True,  # Knows "I am this object"
            'action_effect_pairs': 3     # Understands cause-effect
        },
        'concrete_to_formal': {
            'games_played': 20,
            'sequences_discovered': 5,
            'hypotheses_created': 2,     # Has generated own hypotheses
            'cross_game_transfer': True, # Applied learning across game types
            'validation_success_rate': 0.6  # Sequences work for others too
        }
    }
    
    def __init__(self, db: DatabaseInterface):
        """Initialize cognitive stage system."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure cognitive stage tracking table exists."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_cognitive_stages (
                agent_id TEXT PRIMARY KEY,
                current_stage TEXT NOT NULL DEFAULT 'preoperational',
                stage_entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Competency tracking
                games_played INTEGER DEFAULT 0,
                sequences_discovered INTEGER DEFAULT 0,
                hypotheses_created INTEGER DEFAULT 0,
                object_control_learned BOOLEAN DEFAULT FALSE,
                action_effect_pairs INTEGER DEFAULT 0,
                cross_game_transfer BOOLEAN DEFAULT FALSE,
                validation_success_rate REAL DEFAULT 0.0,
                
                -- Stage history
                preoperational_exit DATETIME,
                concrete_exit DATETIME,
                
                last_evaluated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cognitive_stage 
            ON agent_cognitive_stages(current_stage)
        """)
    
    def get_stage(self, agent_id: str) -> str:
        """Get agent's current cognitive stage."""
        result = self.db.execute_query("""
            SELECT current_stage FROM agent_cognitive_stages WHERE agent_id = ?
        """, (agent_id,))
        
        if result:
            return result[0]['current_stage']
        
        # Initialize new agent at preoperational stage
        self._initialize_agent(agent_id)
        return self.PREOPERATIONAL
    
    def _initialize_agent(self, agent_id: str) -> None:
        """Initialize cognitive stage tracking for new agent."""
        self.db.execute_query("""
            INSERT OR IGNORE INTO agent_cognitive_stages (agent_id, current_stage)
            VALUES (?, ?)
        """, (agent_id, self.PREOPERATIONAL))
    
    def update_competencies(
        self,
        agent_id: str,
        games_played_delta: int = 0,
        sequences_discovered_delta: int = 0,
        hypotheses_created_delta: int = 0,
        object_control_learned: bool = None,
        action_effect_pairs_delta: int = 0,
        cross_game_transfer: bool = None,
        validation_success_rate: float = None
    ) -> Dict[str, Any]:
        """
        Update agent's cognitive competencies and check for stage transition.
        
        Returns:
            Dict with current_stage, transitioned (bool), and competencies
        """
        # Ensure agent exists
        self._initialize_agent(agent_id)
        
        # Build update query dynamically
        updates = []
        params = []
        
        if games_played_delta:
            updates.append("games_played = games_played + ?")
            params.append(games_played_delta)
        if sequences_discovered_delta:
            updates.append("sequences_discovered = sequences_discovered + ?")
            params.append(sequences_discovered_delta)
        if hypotheses_created_delta:
            updates.append("hypotheses_created = hypotheses_created + ?")
            params.append(hypotheses_created_delta)
        if object_control_learned is not None:
            updates.append("object_control_learned = ?")
            params.append(object_control_learned)
        if action_effect_pairs_delta:
            updates.append("action_effect_pairs = action_effect_pairs + ?")
            params.append(action_effect_pairs_delta)
        if cross_game_transfer is not None:
            updates.append("cross_game_transfer = ?")
            params.append(cross_game_transfer)
        if validation_success_rate is not None:
            updates.append("validation_success_rate = ?")
            params.append(validation_success_rate)
        
        updates.append("last_evaluated = CURRENT_TIMESTAMP")
        
        if updates:
            query = f"UPDATE agent_cognitive_stages SET {', '.join(updates)} WHERE agent_id = ?"
            params.append(agent_id)
            self.db.execute_query(query, tuple(params))
        
        # Check for stage transition
        return self._evaluate_stage_transition(agent_id)
    
    def _evaluate_stage_transition(self, agent_id: str) -> Dict[str, Any]:
        """Evaluate if agent should transition to next cognitive stage."""
        result = self.db.execute_query("""
            SELECT * FROM agent_cognitive_stages WHERE agent_id = ?
        """, (agent_id,))
        
        if not result:
            return {'current_stage': self.PREOPERATIONAL, 'transitioned': False}
        
        r = result[0]
        current_stage = r['current_stage']
        transitioned = False
        new_stage = current_stage
        
        if current_stage == self.PREOPERATIONAL:
            # Check for transition to concrete operational
            reqs = self.COMPETENCIES['preoperational_to_concrete']
            if (r['games_played'] >= reqs['games_played'] and
                r['sequences_discovered'] >= reqs['sequences_discovered'] and
                r['object_control_learned'] and
                r['action_effect_pairs'] >= reqs['action_effect_pairs']):
                
                new_stage = self.CONCRETE_OPERATIONAL
                transitioned = True
                self.db.execute_query("""
                    UPDATE agent_cognitive_stages 
                    SET current_stage = ?, 
                        preoperational_exit = CURRENT_TIMESTAMP,
                        stage_entered_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (new_stage, agent_id))
                logger.info(f"[COGNITIVE] Agent {agent_id[:8]} -> CONCRETE_OPERATIONAL stage")
        
        elif current_stage == self.CONCRETE_OPERATIONAL:
            # Check for transition to formal operational
            reqs = self.COMPETENCIES['concrete_to_formal']
            if (r['games_played'] >= reqs['games_played'] and
                r['sequences_discovered'] >= reqs['sequences_discovered'] and
                r['hypotheses_created'] >= reqs['hypotheses_created'] and
                r['cross_game_transfer'] and
                r['validation_success_rate'] >= reqs['validation_success_rate']):
                
                new_stage = self.FORMAL_OPERATIONAL
                transitioned = True
                self.db.execute_query("""
                    UPDATE agent_cognitive_stages 
                    SET current_stage = ?, 
                        concrete_exit = CURRENT_TIMESTAMP,
                        stage_entered_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (new_stage, agent_id))
                logger.info(f"[COGNITIVE] Agent {agent_id[:8]} -> FORMAL_OPERATIONAL stage")
        
        return {
            'current_stage': new_stage,
            'transitioned': transitioned,
            'competencies': dict(r)
        }
    
    def get_stage_capabilities(self, agent_id: str) -> Dict[str, bool]:
        """Get what cognitive capabilities an agent has based on their stage."""
        stage = self.get_stage(agent_id)
        
        capabilities = {
            # Preoperational capabilities (all agents have these)
            'action_exploration': True,
            'object_observation': True,
            'pattern_recognition': True,
            
            # Concrete operational capabilities
            'sequence_following': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],
            'reversibility_understanding': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],
            'conservation_of_state': stage in [self.CONCRETE_OPERATIONAL, self.FORMAL_OPERATIONAL],
            
            # Formal operational capabilities
            'hypothesis_generation': stage == self.FORMAL_OPERATIONAL,
            'abstract_generalization': stage == self.FORMAL_OPERATIONAL,
            'hypothetical_reasoning': stage == self.FORMAL_OPERATIONAL,
            'cross_domain_transfer': stage == self.FORMAL_OPERATIONAL
        }
        
        return capabilities
    
    def get_population_distribution(self) -> Dict[str, int]:
        """Get distribution of agents across cognitive stages."""
        result = self.db.execute_query("""
            SELECT current_stage, COUNT(*) as count
            FROM agent_cognitive_stages
            GROUP BY current_stage
        """)
        
        distribution = {
            self.PREOPERATIONAL: 0,
            self.CONCRETE_OPERATIONAL: 0,
            self.FORMAL_OPERATIONAL: 0
        }
        
        for r in result or []:
            stage = r['current_stage']
            if stage in distribution:
                distribution[stage] = r['count']
        
        return distribution


# ============================================================================
# METACOGNITIVE REASONING ENGINE
# ============================================================================
# Implements the missing metacognitive capabilities from "how to reason.md":
# - Assumption Tracker: "What am I assuming that might not be true?"
# - Prediction Before Action: "If my theory is right, this should cause X"
# - Theory Revision: "My theory was wrong because..."
# - Failure Commonality: "These N attempts all failed the same way"
# - Elimination Tracker: "I've proven these approaches won't work"
# - Post-Win Reflection: "The key insight that unlocked this was..."
# ============================================================================

class MetacognitiveReasoningEngine:
    """
    Provides metacognitive reasoning capabilities for agents.
    
    Philosophy: Strong problem-solvers don't just try things - they:
    1. Make PREDICTIONS before acting ("if theory is right, X should happen")
    2. Track ASSUMPTIONS that might be wrong
    3. Analyze FAILURE PATTERNS (what do failed attempts have in common?)
    4. ELIMINATE possibilities systematically
    5. REFLECT after success to extract transferable insights
    
    This shifts agents from "random exploration" to "scientific hypothesis testing".
    """
    
    def __init__(self, db: DatabaseInterface):
        """Initialize metacognitive engine."""
        self.db = db
        self._ensure_tables()

        # Provenance for the current session (attempt/mode/generation/role)
        self._session_provenance: Dict[str, Any] = {}
        
        # Session state (cleared per game)
        self._current_assumptions = []
        self._pending_prediction = None
        self._failed_attempts = []
        self._eliminated_actions = set()
        self._theory_revisions = []
        self._current_theory = None

    def set_session_provenance(
        self,
        attempt_id: Optional[str],
        mode: Optional[str],
        generation: Optional[int],
        role: Optional[str],
    ) -> None:
        """Record provenance for metacog inserts (DB-only, no side effects)."""
        self._session_provenance = {
            'attempt_id': attempt_id,
            'mode': mode,
            'generation': generation,
            'role': role,
        }
    
    def _ensure_tables(self):
        """Create metacognitive tracking tables."""
        # Track assumptions and their validity
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_assumptions (
                assumption_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The assumption
                assumption_text TEXT NOT NULL,
                assumption_type TEXT NOT NULL,  -- 'control', 'goal', 'obstacle', 'rule'
                
                -- Status
                is_valid BOOLEAN DEFAULT NULL,  -- NULL = untested, TRUE/FALSE = tested
                tested_at DATETIME,
                test_result TEXT,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Track predictions and outcomes
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_predictions (
                prediction_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The prediction
                theory_text TEXT NOT NULL,
                predicted_outcome TEXT NOT NULL,  -- "score will increase", "object will move right"
                action_taken TEXT NOT NULL,
                
                -- Outcome
                actual_outcome TEXT,
                prediction_correct BOOLEAN,
                theory_revised BOOLEAN DEFAULT FALSE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Track failure commonalities
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_failure_patterns (
                pattern_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The pattern
                common_factor TEXT NOT NULL,  -- "all failures involved color_3"
                failure_count INTEGER NOT NULL,
                example_actions TEXT,  -- JSON list of actions that failed
                
                -- Insight derived
                insight TEXT,
                insight_applied BOOLEAN DEFAULT FALSE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Track eliminated possibilities
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_eliminations (
                elimination_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- What was eliminated
                eliminated_action TEXT NOT NULL,  -- "ACTION1", "ACTION2", etc.
                reason TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                
                -- Evidence
                test_count INTEGER DEFAULT 1,
                consistent_failure BOOLEAN DEFAULT TRUE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Track post-win reflections (the key insight)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_insights (
                insight_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The insight
                key_insight TEXT NOT NULL,
                winning_strategy TEXT NOT NULL,
                
                -- What led to the breakthrough
                breakthrough_action TEXT,
                theory_at_breakthrough TEXT,
                actions_before_breakthrough INTEGER,
                
                -- Transferability
                is_transferable BOOLEAN DEFAULT FALSE,
                applicable_to TEXT,  -- JSON list of similar game types

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for fast lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_metacog_assumptions_game 
            ON metacognitive_assumptions(game_type, level_number, is_valid)
        """)
    
    # ========================================================================
    # 1. ASSUMPTION TRACKER
    # ========================================================================
    # "What am I assuming that might not be true?"
    # ========================================================================
    
    def register_assumption(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        assumption: str,
        assumption_type: str = 'rule'
    ) -> str:
        """
        Register an assumption the agent is making.
        
        Examples:
        - "I control the blue object"
        - "Rare colors are goals"
        - "ACTION1 moves me up"
        - "Walls cannot be passed"
        
        Args:
            agent_id: Agent making assumption
            game_type: Current game type
            level_number: Current level
            assumption: The assumption text
            assumption_type: 'control', 'goal', 'obstacle', 'rule'
            
        Returns:
            assumption_id
        """
        assumption_id = f"assume_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO metacognitive_assumptions 
            (assumption_id, agent_id, game_type, level_number, assumption_text, assumption_type,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assumption_id,
            agent_id,
            game_type,
            level_number,
            assumption,
            assumption_type,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))
        
        # Track in session
        self._current_assumptions.append({
            'id': assumption_id,
            'text': assumption,
            'type': assumption_type,
            'tested': False
        })
        
        logger.debug(f"[METACOG] Registered assumption: {assumption}")
        return assumption_id
    
    def challenge_assumption(
        self,
        assumption_id: str,
        is_valid: bool,
        test_result: str
    ) -> None:
        """
        Record the result of testing an assumption.
        
        Args:
            assumption_id: ID of assumption being tested
            is_valid: Whether assumption proved true
            test_result: Description of what happened
        """
        self.db.execute_query("""
            UPDATE metacognitive_assumptions 
            SET is_valid = ?, tested_at = datetime('now'), test_result = ?
            WHERE assumption_id = ?
        """, (is_valid, test_result, assumption_id))
        
        # Update session state
        for a in self._current_assumptions:
            if a['id'] == assumption_id:
                a['tested'] = True
                a['valid'] = is_valid
        
        status = "CONFIRMED" if is_valid else "DISPROVEN"
        logger.info(f"[METACOG] Assumption {status}: {test_result}")
    
    def get_untested_assumptions(
        self,
        game_type: str,
        level_number: int
    ) -> List[Dict[str, Any]]:
        """Get assumptions that haven't been tested yet."""
        result = self.db.execute_query("""
            SELECT assumption_id, assumption_text, assumption_type
            FROM metacognitive_assumptions
            WHERE game_type = ? AND level_number = ? AND is_valid IS NULL
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number))
        
        return result or []
    
    def get_disproven_assumptions(
        self,
        game_type: str,
        level_number: int
    ) -> List[Dict[str, Any]]:
        """Get assumptions that were proven false - avoid repeating these errors."""
        result = self.db.execute_query("""
            SELECT assumption_text, test_result
            FROM metacognitive_assumptions
            WHERE game_type = ? AND level_number = ? AND is_valid = FALSE
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number))
        
        return result or []
    
    # ========================================================================
    # 2. PREDICTION BEFORE ACTION
    # ========================================================================
    # "If my theory is right, then THIS should happen"
    # ========================================================================
    
    def make_prediction(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        theory: str,
        predicted_outcome: str,
        action: str
    ) -> str:
        """
        Make a prediction before taking an action.
        
        This is the key shift from random exploration to hypothesis testing.
        
        Examples:
        - Theory: "I control the blue object"
          Prediction: "ACTION1 will move it up"
          Action: "ACTION1"
          
        - Theory: "Rare colors are goals"
          Prediction: "Touching color_7 will increase score"
          Action: "ACTION4" (move toward color_7)
        
        Args:
            agent_id: Agent making prediction
            game_type: Current game type
            level_number: Current level
            theory: The underlying theory being tested
            predicted_outcome: What should happen if theory is correct
            action: The action being taken to test
            
        Returns:
            prediction_id
        """
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO metacognitive_predictions 
            (prediction_id, agent_id, game_type, level_number, theory_text, predicted_outcome, action_taken,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id,
            agent_id,
            game_type,
            level_number,
            theory,
            predicted_outcome,
            action,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))
        
        # Store pending prediction for outcome evaluation
        self._pending_prediction = {
            'id': prediction_id,
            'theory': theory,
            'predicted': predicted_outcome,
            'action': action,
            'game_type': game_type,
            'level_number': level_number,
        }
        
        self._current_theory = theory
        
        logger.info(f"[METACOG] PREDICTION: If '{theory}' then {action} should cause '{predicted_outcome}'")
        return prediction_id

    def peek_prediction(self) -> Optional[str]:
        """Lightweight peek at the pending prediction outcome, if any."""
        if not self._pending_prediction:
            return None
        return self._pending_prediction.get('predicted')

    def _record_significance_observation(
        self,
        prediction_id: str,
        theory: str,
        game_type: str,
        level_number: int,
        prediction_correct: bool,
        generation: Optional[int],
    ) -> None:
        """Update reliability/consensus and promote strong hypotheses to beliefs."""
        try:
            total_rows = self.db.execute_query(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) AS successes
                FROM metacognitive_predictions
                WHERE theory_text = ?
            """,
                (theory,),
            ) or []

            total = total_rows[0]['total'] if total_rows and 'total' in total_rows[0] else 0
            successes = total_rows[0]['successes'] if total_rows and 'successes' in total_rows[0] else 0
            reliability = round(successes / total, 3) if total else 0.5
            consensus = reliability  # proxy until cross-agent consensus is recorded
            decay_score = max(0.0, 1.0 - reliability)
            last_gen = generation or self._session_provenance.get('generation') or 0

            self.db.execute_query(
                """
                UPDATE metacognitive_predictions
                SET reliability = ?,
                    consensus = ?,
                    last_observed_generation = ?,
                    decay_score = ?
                WHERE prediction_id = ?
                """,
                (reliability, consensus, last_gen, decay_score, prediction_id),
            )

            # Keep assumptions in sync with observed reliability
            self.db.execute_query(
                """
                UPDATE metacognitive_assumptions
                SET reliability = COALESCE(?, reliability),
                    consensus = COALESCE(?, consensus),
                    last_observed_generation = COALESCE(?, last_observed_generation),
                    decay_score = COALESCE(?, decay_score)
                WHERE game_type = ? AND level_number = ?
                """,
                (reliability, consensus, last_gen, decay_score, game_type, level_number),
            )

            # Promotion: after ≥3 observations and reliability >= 0.7, persist as belief/insight
            if total >= 3 and reliability >= 0.7:
                existing = self.db.execute_query(
                    """SELECT insight_id FROM metacognitive_insights
                        WHERE key_insight = ? LIMIT 1""",
                    (theory,),
                )
                if not existing:
                    insight_id = f"insight_{uuid.uuid4().hex[:12]}"
                    self.db.execute_query(
                        """
                        INSERT INTO metacognitive_insights(
                            insight_id, agent_id, game_type, level_number, key_insight, winning_strategy,
                            breakthrough_action, theory_at_breakthrough, actions_before_breakthrough,
                            is_transferable, source_attempt_id, source_mode, last_observed_generation,
                            decay_score, reliability, consensus
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            insight_id,
                            'metacog_auto',
                            game_type,
                            level_number,
                            theory,
                            f"Significance loop confirmed ({successes}/{total})",
                            None,
                            theory,
                            total,
                            True,
                            self._session_provenance.get('attempt_id'),
                            self._session_provenance.get('mode'),
                            last_gen,
                            decay_score,
                            reliability,
                            consensus,
                        ),
                    )
        except Exception:
            logger.debug("Significance observation recording failed (non-critical)")
    
    def evaluate_prediction(
        self,
        actual_outcome: str,
        score_before: float,
        score_after: float,
        frame_changed: bool,
        generation: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate the pending prediction against actual outcome.
        
        Returns evaluation with recommendation for theory revision.
        """
        if not self._pending_prediction:
            return {'status': 'no_pending_prediction'}
        
        pred = self._pending_prediction
        prediction_id = pred['id']
        
        # Determine if prediction was correct
        predicted = pred['predicted'].lower()
        prediction_correct = False
        
        if 'score' in predicted and 'increase' in predicted:
            prediction_correct = score_after > score_before
        elif 'move' in predicted:
            prediction_correct = frame_changed
        elif 'no change' in predicted:
            prediction_correct = not frame_changed
        else:
            # Generic check - frame change or score change counts as something happened
            prediction_correct = frame_changed or score_after > score_before
        
        # Record outcome
        self.db.execute_query("""
            UPDATE metacognitive_predictions 
            SET actual_outcome = ?, prediction_correct = ?,
                last_observed_generation = COALESCE(?, last_observed_generation, 0),
                decay_score = COALESCE(decay_score, 0.0)
            WHERE prediction_id = ?
        """, (actual_outcome, prediction_correct, generation, prediction_id))
        
        result = {
            'prediction_id': prediction_id,
            'theory': pred['theory'],
            'predicted': pred['predicted'],
            'actual': actual_outcome,
            'correct': prediction_correct
        }
        
        if prediction_correct:
            logger.info(f"[METACOG] PREDICTION CORRECT: Theory '{pred['theory']}' confirmed!")
            result['recommendation'] = 'strengthen_theory'
        else:
            logger.info(f"[METACOG] PREDICTION WRONG: Expected '{pred['predicted']}', got '{actual_outcome}'")
            result['recommendation'] = 'revise_theory'
            
            # Queue theory revision
            self._theory_revisions.append({
                'old_theory': pred['theory'],
                'failed_prediction': pred['predicted'],
                'actual': actual_outcome
            })
        
        # Clear pending prediction
        self._pending_prediction = None

        # Update reliability/consensus and promotion ladder
        self._record_significance_observation(
            prediction_id=prediction_id,
            theory=pred['theory'],
            game_type=pred.get('game_type', 'unknown'),
            level_number=pred.get('level_number', 1),
            prediction_correct=prediction_correct,
            generation=generation,
        )
        
        return result
    
    # ========================================================================
    # 3. THEORY REVISION
    # ========================================================================
    # "My theory was wrong because..."
    # ========================================================================
    
    def revise_theory(
        self,
        old_theory: str,
        failed_prediction: str,
        actual_outcome: str
    ) -> str:
        """
        Generate a revised theory based on failed prediction.
        
        Returns:
            New theory text
        """
        # Simple heuristic revision rules
        new_theory = old_theory
        
        if 'control' in old_theory.lower() and 'no change' in actual_outcome.lower():
            # "I control X" but nothing moved -> probably don't control X
            new_theory = old_theory.replace('I control', 'I might NOT control')
            
        elif 'goal' in old_theory.lower() and 'no score' in actual_outcome.lower():
            # "X is goal" but score didn't increase -> probably not the goal
            new_theory = old_theory.replace('is a goal', 'is NOT a goal')
            
        elif 'move' in failed_prediction.lower() and 'blocked' in actual_outcome.lower():
            # Predicted movement but was blocked -> add obstacle awareness
            new_theory = f"{old_theory} (but obstacles block movement)"
        
        else:
            # Generic revision
            new_theory = f"REVISED: {old_theory} [failed: {failed_prediction}]"
        
        logger.info(f"[METACOG] THEORY REVISED: '{old_theory}' -> '{new_theory}'")
        
        self._current_theory = new_theory
        return new_theory
    
    def get_current_theory(self) -> Optional[str]:
        """Get the current working theory."""
        return self._current_theory
    
    def get_theory_revision_history(self) -> List[Dict[str, Any]]:
        """Get history of theory revisions this session."""
        return self._theory_revisions.copy()
    
    # ========================================================================
    # 4. FAILURE COMMONALITY ANALYSIS
    # ========================================================================
    # "These N attempts all failed the same way - what do they have in common?"
    # ========================================================================
    
    def record_failure(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Record a failed attempt for commonality analysis.
        
        Args:
            action: The action that failed
            context: Context of failure (colors nearby, position, etc.)
        """
        self._failed_attempts.append({
            'action': action,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 20 failures
        if len(self._failed_attempts) > 20:
            self._failed_attempts = self._failed_attempts[-20:]
    
    def analyze_failure_commonality(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        min_failures: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze recent failures to find common factors.
        
        Returns:
            Common factor analysis if pattern found, None otherwise
        """
        if len(self._failed_attempts) < min_failures:
            return None
        
        # Analyze last N failures
        recent_failures = self._failed_attempts[-min_failures:]
        
        # Check for common actions
        action_counts = {}
        for f in recent_failures:
            action = f.get('action', '')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Check for common context elements
        context_elements = {}
        for f in recent_failures:
            context = f.get('context', {})
            for key, value in context.items():
                element = f"{key}:{value}"
                context_elements[element] = context_elements.get(element, 0) + 1
        
        # Find most common factor
        common_factor = None
        max_count = 0
        
        for action, count in action_counts.items():
            if count >= min_failures * 0.8 and count > max_count:
                common_factor = f"ACTION: {action}"
                max_count = count
        
        for element, count in context_elements.items():
            if count >= min_failures * 0.8 and count > max_count:
                common_factor = f"CONTEXT: {element}"
                max_count = count
        
        if not common_factor:
            return None
        
        # Generate insight
        insight = self._generate_failure_insight(common_factor, recent_failures)
        
        # Store pattern
        pattern_id = f"fail_{uuid.uuid4().hex[:12]}"
        self.db.execute_query("""
            INSERT INTO metacognitive_failure_patterns
            (pattern_id, agent_id, game_type, level_number, common_factor, failure_count, example_actions, insight,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_id, agent_id, game_type, level_number,
            common_factor, len(recent_failures),
            json.dumps([f['action'] for f in recent_failures]),
            insight,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))
        
        logger.info(f"[METACOG] FAILURE PATTERN: {common_factor} - {insight}")
        
        return {
            'pattern_id': pattern_id,
            'common_factor': common_factor,
            'failure_count': len(recent_failures),
            'insight': insight
        }
    
    def _generate_failure_insight(
        self,
        common_factor: str,
        failures: List[Dict[str, Any]]
    ) -> str:
        """Generate an insight from failure pattern."""
        if 'ACTION:' in common_factor:
            action = common_factor.replace('ACTION: ', '')
            return f"Stop using {action} - it consistently fails in this context"
        elif 'color' in common_factor.lower():
            return f"Avoid interaction with {common_factor.split(':')[1]} - it leads to failure"
        elif 'position' in common_factor.lower():
            return f"This position/area seems dangerous - avoid or find another route"
        else:
            return f"Pattern detected: {common_factor} correlates with failure"
    
    # ========================================================================
    # 5. ELIMINATION TRACKER
    # ========================================================================
    # "I've proven these 8 approaches won't work, so it must be one of these 3"
    # ========================================================================
    
    def eliminate_action(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action: str,
        reason: str
    ) -> None:
        """
        Mark an action as eliminated (proven not to work).
        
        Args:
            agent_id: Agent eliminating action
            game_type: Current game type
            level_number: Current level
            action: The action to eliminate (e.g., "ACTION1")
            reason: Why it's being eliminated
        """
        # Add to session set
        self._eliminated_actions.add(action)
        
        # Check if already eliminated in DB
        existing = self.db.execute_query("""
            SELECT elimination_id, test_count FROM metacognitive_eliminations
            WHERE agent_id = ? AND game_type = ? AND level_number = ? AND eliminated_action = ?
        """, (agent_id, game_type, level_number, action))
        
        if existing:
            # Increment test count
            self.db.execute_query("""
                UPDATE metacognitive_eliminations 
                SET test_count = test_count + 1,
                    last_observed_generation = COALESCE(?, last_observed_generation, 0),
                    decay_score = COALESCE(decay_score, 0.0)
                WHERE elimination_id = ?
            """, (
                self._session_provenance.get('generation'),
                existing[0]['elimination_id'],
            ))
        else:
            # Insert new elimination
            elimination_id = f"elim_{uuid.uuid4().hex[:12]}"
            self.db.execute_query("""
                INSERT INTO metacognitive_eliminations
                (elimination_id, agent_id, game_type, level_number, eliminated_action, reason,
                 source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elimination_id,
                agent_id,
                game_type,
                level_number,
                action,
                reason,
                self._session_provenance.get('attempt_id'),
                self._session_provenance.get('mode'),
                self._session_provenance.get('generation') or 0,
                0.0,
                0.5,
                0.0,
            ))
        
        logger.debug(f"[METACOG] ELIMINATED: {action} - {reason}")
    
    def get_eliminated_actions(
        self,
        game_type: str,
        level_number: int,
        min_confidence: float = 0.6
    ) -> List[str]:
        """Get list of actions that have been eliminated for this level."""
        result = self.db.execute_query("""
            SELECT eliminated_action FROM metacognitive_eliminations
            WHERE game_type = ? AND level_number = ? 
              AND confidence >= ? AND consistent_failure = TRUE
            ORDER BY test_count DESC
        """, (game_type, level_number, min_confidence))
        
        db_eliminated = [r['eliminated_action'] for r in (result or [])]
        
        # Combine with session eliminations
        all_eliminated = set(db_eliminated) | self._eliminated_actions
        return list(all_eliminated)
    
    def get_remaining_actions(
        self,
        game_type: str,
        level_number: int,
        all_actions: List[str] = None
    ) -> List[str]:
        """Get actions that haven't been eliminated yet."""
        if all_actions is None:
            all_actions = [f"ACTION{i}" for i in range(1, 8)]
        
        eliminated = set(self.get_eliminated_actions(game_type, level_number))
        return [a for a in all_actions if a not in eliminated]
    
    def get_elimination_summary(
        self,
        game_type: str,
        level_number: int
    ) -> str:
        """Get human-readable elimination summary."""
        eliminated = self.get_eliminated_actions(game_type, level_number)
        remaining = self.get_remaining_actions(game_type, level_number)
        
        if not eliminated:
            return "No actions eliminated yet - all options open"
        
        return (
            f"Eliminated {len(eliminated)} actions ({', '.join(eliminated)}). "
            f"Remaining options: {', '.join(remaining)}"
        )
    
    # ========================================================================
    # 6. POST-WIN REFLECTION
    # ========================================================================
    # "What was the key insight that unlocked this?"
    # ========================================================================
    
    def record_win_reflection(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        key_insight: str,
        winning_strategy: str,
        breakthrough_action: Optional[str] = None,
        theory_at_breakthrough: Optional[str] = None,
        actions_before_breakthrough: int = 0
    ) -> str:
        """
        Record reflection after winning - what was the key insight?
        
        This is critical for extracting transferable knowledge.
        
        Examples:
        - "The key insight was that color_3 objects can be pushed"
        - "The winning strategy was to clear obstacles before moving to goal"
        - "The breakthrough was realizing ACTION5 toggles switches"
        
        Returns:
            insight_id
        """
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"
        
        # Determine if insight is transferable
        is_transferable = any([
            'all games' in key_insight.lower(),
            'always' in key_insight.lower(),
            'general rule' in key_insight.lower(),
            'pattern' in key_insight.lower()
        ])
        
        self.db.execute_query("""
            INSERT INTO metacognitive_insights
            (insight_id, agent_id, game_type, level_number, key_insight, winning_strategy,
             breakthrough_action, theory_at_breakthrough, actions_before_breakthrough, is_transferable,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id, agent_id, game_type, level_number,
            key_insight, winning_strategy, breakthrough_action,
            theory_at_breakthrough, actions_before_breakthrough, is_transferable,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))
        
        logger.info(f"[METACOG] WIN REFLECTION: '{key_insight}' (strategy: {winning_strategy})")
        
        return insight_id
    
    def generate_win_reflection(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action_history: List[str],
        score_history: List[float]
    ) -> Dict[str, Any]:
        """
        Automatically generate win reflection from action history.
        
        Analyzes the sequence of actions to identify:
        - When the breakthrough happened (first score increase)
        - What theory was active at that point
        - What strategy worked
        
        Returns:
            Generated reflection
        """
        if not action_history or not score_history:
            return {'status': 'no_history'}
        
        # Find breakthrough moment (first significant score increase)
        breakthrough_idx = None
        for i in range(1, len(score_history)):
            if score_history[i] > score_history[i-1]:
                breakthrough_idx = i
                break
        
        if breakthrough_idx is None:
            # No clear breakthrough - use last action before win
            breakthrough_idx = len(action_history) - 1
        
        breakthrough_action = action_history[breakthrough_idx] if breakthrough_idx < len(action_history) else None
        
        # Analyze winning pattern
        action_counts = {}
        for a in action_history:
            action_counts[a] = action_counts.get(a, 0) + 1
        
        most_used = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
        
        # Generate key insight
        if breakthrough_action:
            key_insight = f"Breakthrough came from {breakthrough_action} at action {breakthrough_idx}"
        else:
            key_insight = f"Gradual progress using primarily {most_used}"
        
        # Generate winning strategy
        unique_actions = len(set(action_history))
        if unique_actions <= 2:
            winning_strategy = f"Focused approach using {unique_actions} action types"
        else:
            winning_strategy = f"Mixed approach with {unique_actions} different actions"
        
        # Record reflection
        insight_id = self.record_win_reflection(
            agent_id=agent_id,
            game_type=game_type,
            level_number=level_number,
            key_insight=key_insight,
            winning_strategy=winning_strategy,
            breakthrough_action=breakthrough_action,
            theory_at_breakthrough=self._current_theory,
            actions_before_breakthrough=breakthrough_idx or 0
        )
        
        return {
            'insight_id': insight_id,
            'key_insight': key_insight,
            'winning_strategy': winning_strategy,
            'breakthrough_action': breakthrough_action,
            'actions_before_breakthrough': breakthrough_idx
        }
    
    def get_relevant_insights(
        self,
        game_type: str,
        level_number: int,
        include_transferable: bool = True
    ) -> List[Dict[str, Any]]:
        """Get insights relevant to current game/level."""
        result = self.db.execute_query("""
            SELECT key_insight, winning_strategy, breakthrough_action, is_transferable
            FROM metacognitive_insights
            WHERE (game_type = ? AND level_number = ?)
               OR (is_transferable = TRUE AND ? = TRUE)
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number, include_transferable))
        
        return result or []
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def reset_session(self) -> None:
        """Reset session state for new game."""
        self._current_assumptions = []
        self._pending_prediction = None
        self._failed_attempts = []
        self._eliminated_actions = set()
        self._theory_revisions = []
        self._current_theory = None
        
        logger.debug("[METACOG] Session reset for new game")
    
    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get summary of current metacognitive state."""
        untested = [a for a in self._current_assumptions if not a.get('tested')]
        disproven = [a for a in self._current_assumptions if a.get('tested') and not a.get('valid')]
        
        return {
            'current_theory': self._current_theory,
            'assumptions_count': len(self._current_assumptions),
            'untested_assumptions': len(untested),
            'disproven_assumptions': len(disproven),
            'pending_prediction': self._pending_prediction is not None,
            'failures_recorded': len(self._failed_attempts),
            'actions_eliminated': len(self._eliminated_actions),
            'theory_revisions': len(self._theory_revisions)
        }
    
    def get_q8_metacognitive_context(
        self,
        agent_id: str,
        game_type: str,
        level_number: int
    ) -> Dict[str, Any]:
        """
        Build Q8 context for reasoning logs.
        
        Q8: What am I assuming? What have I proven/disproven? What's eliminated?
        
        Returns:
            Q8 context dictionary
        """
        summary = self.get_metacognitive_summary()
        eliminated = self.get_eliminated_actions(game_type, level_number)
        remaining = self.get_remaining_actions(game_type, level_number)
        disproven = self.get_disproven_assumptions(game_type, level_number)
        insights = self.get_relevant_insights(game_type, level_number)
        
        # Build insight text
        if self._current_theory:
            theory_insight = f"Working theory: {self._current_theory}"
        else:
            theory_insight = "No working theory yet - exploring"
        
        if eliminated:
            elimination_insight = f"Eliminated {len(eliminated)} actions, {len(remaining)} remain"
        else:
            elimination_insight = "All actions still viable"
        
        if disproven:
            assumption_insight = f"Disproven {len(disproven)} assumptions"
        else:
            assumption_insight = "No assumptions disproven yet"
        
        return {
            'Q8': f"{theory_insight}. {elimination_insight}. {assumption_insight}.",
            'current_theory': self._current_theory,
            'theory_revisions': len(self._theory_revisions),
            'eliminated_actions': eliminated,
            'remaining_actions': remaining,
            'disproven_assumptions': [d['assumption_text'] for d in disproven],
            'relevant_insights': [i['key_insight'] for i in insights[:3]],
            'pending_prediction': self._pending_prediction is not None,
            'confidence': min(0.9, 0.3 + len(self._theory_revisions) * 0.1 + len(eliminated) * 0.05)
        }


# ============================================================================
# EPISODIC MEMORY SYSTEM (Agent History Query + Intuition)
# ============================================================================

class EpisodicMemorySystem:
    """
    Enables agents to query their own experience history (wA) vs network wisdom (wB).
    
    Philosophy: "Episodic memory" is not a separate storage - it's the ability
    to query one's own action history and form intuitions from personal experience.
    
    This implements the Two-Streams insight that private memory (wA) should be
    queryable and comparable against network recommendations (wB).
    
    Key Queries:
    - "What did I do last time in this situation?"
    - "Did my approach work better than network's?"
    - "What's my personal success pattern?"
    """
    
    def __init__(self, db: DatabaseInterface):
        """Initialize episodic memory system."""
        self.db = db
    
    def query_personal_history(
        self,
        agent_id: str,
        game_type: str,
        level: int,
        context: str = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query agent's personal history for this game/level combination.
        
        This is the "what did I do last time?" query.
        
        Args:
            agent_id: Agent querying their history
            game_type: Game type prefix (e.g., "SP80")
            level: Level number
            context: Optional context string (e.g., "stuck_state")
            limit: Max records to return
            
        Returns:
            Dict with episodes, patterns, and intuition strength
        """
        # Get agent's historical game results for this game type/level
        episodes = self.db.execute_query("""
            SELECT 
                gr.game_id, gr.final_score, gr.levels_completed,
                gr.actions_used, gr.timestamp,
                CASE WHEN gr.final_score > 0 THEN 1 ELSE 0 END as success
            FROM game_results gr
            WHERE gr.agent_id = ? 
              AND gr.game_id LIKE ?
            ORDER BY gr.timestamp DESC
            LIMIT ?
        """, (agent_id, f"{game_type}%", limit))
        
        if not episodes:
            return {
                'has_history': False,
                'episodes': [],
                'intuition_strength': 0.0,
                'personal_pattern': None,
                'recommendation': 'explore_new'
            }
        
        # Calculate success rate (personal intuition strength)
        successes = sum(1 for e in episodes if e['success'])
        total = len(episodes)
        success_rate = successes / total if total > 0 else 0.0
        
        # Find common patterns in successful episodes
        successful_episodes = [e for e in episodes if e['success']]
        personal_pattern = None
        
        if successful_episodes:
            # Calculate average actions for success
            avg_actions = sum(e['actions_used'] for e in successful_episodes) / len(successful_episodes)
            avg_score = sum(e['final_score'] for e in successful_episodes) / len(successful_episodes)
            
            personal_pattern = {
                'avg_actions_to_win': avg_actions,
                'avg_score': avg_score,
                'consistent_success': len(successful_episodes) >= 2
            }
        
        # Determine recommendation based on history
        if success_rate >= 0.7:
            recommendation = 'trust_self'  # Strong personal track record
        elif success_rate >= 0.3:
            recommendation = 'blend_sources'  # Mixed results
        else:
            recommendation = 'try_network'  # Personal approach not working
        
        return {
            'has_history': True,
            'episodes': [dict(e) for e in episodes],
            'intuition_strength': success_rate,
            'personal_pattern': personal_pattern,
            'recommendation': recommendation,
            'total_attempts': total,
            'successes': successes
        }
    
    def compare_streams(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Compare agent's private experience (wA) vs network wisdom (wB).
        
        This is the core Two-Streams comparison that enables agents to
        make informed decisions about which source to trust.
        
        Returns:
            Dict with wA_strength, wB_strength, recommended_bias, and reasoning
        """
        game_type = game_id[:4] if game_id else ''
        
        # Stream A: Personal experience (wA)
        personal = self.query_personal_history(agent_id, game_type, level)
        wA_strength = personal['intuition_strength']
        wA_episodes = personal['total_attempts'] if personal['has_history'] else 0
        
        # Stream B: Network wisdom (wB)
        network = self.db.execute_query("""
            SELECT 
                COUNT(*) as sequence_count,
                AVG(ws.efficiency_score) as avg_efficiency,
                MAX(ws.times_referenced) as max_references,
                AVG(COALESCE(sr.success_rate, 0.5)) as avg_success_rate
            FROM winning_sequences ws
            LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
            WHERE ws.game_id LIKE ? 
              AND ws.level_number = ?
              AND ws.is_active = 1
        """, (f"{game_type}%", level))
        
        wB_strength = 0.0
        wB_sequences = 0
        
        if network and network[0]['sequence_count'] > 0:
            n = network[0]
            wB_sequences = n['sequence_count']
            # Network strength based on availability and reputation
            availability_score = min(1.0, wB_sequences / 5.0)  # Cap at 5 sequences
            reputation_score = n['avg_success_rate'] or 0.5
            wB_strength = (availability_score * 0.4) + (reputation_score * 0.6)
        
        # Compare streams
        stream_difference = wA_strength - wB_strength
        
        if stream_difference > 0.2:
            recommended_bias = 0.7  # Trust self more
            reasoning = f"Personal success ({wA_strength:.0%}) exceeds network ({wB_strength:.0%})"
        elif stream_difference < -0.2:
            recommended_bias = 0.3  # Trust network more
            reasoning = f"Network ({wB_strength:.0%}) outperforms personal ({wA_strength:.0%})"
        else:
            recommended_bias = 0.5  # Balanced
            reasoning = f"Streams comparable: personal {wA_strength:.0%}, network {wB_strength:.0%}"
        
        # Check for conflict (significant disagreement)
        conflict_detected = abs(stream_difference) > 0.3
        
        return {
            'wA_strength': wA_strength,
            'wA_episodes': wA_episodes,
            'wB_strength': wB_strength,
            'wB_sequences': wB_sequences,
            'recommended_bias': recommended_bias,
            'reasoning': reasoning,
            'conflict_detected': conflict_detected,
            'stream_difference': stream_difference
        }
    
    def get_narrative_summary(
        self,
        agent_id: str,
        game_type: str,
        level: int
    ) -> str:
        """
        Generate a natural language summary of agent's experience.
        
        This creates the "last time I..." narrative for agent reasoning.
        """
        history = self.query_personal_history(agent_id, game_type, level, limit=3)
        
        if not history['has_history']:
            return "First time encountering this game type - exploring with fresh perspective."
        
        episodes = history['episodes']
        recent = episodes[0] if episodes else None
        
        if not recent:
            return "No detailed episode memory available."
        
        # Build narrative
        parts = []
        
        # Most recent outcome
        if recent['success']:
            parts.append(f"Last attempt succeeded with score {recent['final_score']:.0f} in {recent['actions_used']} actions.")
        else:
            parts.append(f"Last attempt ended at level {recent.get('levels_completed', 0)} after {recent['actions_used']} actions.")
        
        # Pattern summary
        if history['personal_pattern']:
            pattern = history['personal_pattern']
            if pattern['consistent_success']:
                parts.append(f"Consistently winning with ~{pattern['avg_actions_to_win']:.0f} actions.")
            else:
                parts.append("Success pattern still emerging.")
        
        # Recommendation
        rec = history['recommendation']
        if rec == 'trust_self':
            parts.append("My approach works well - trusting personal experience.")
        elif rec == 'try_network':
            parts.append("Personal approach struggling - considering network alternatives.")
        else:
            parts.append("Balancing personal intuition with network guidance.")
        
        return " ".join(parts)

    # ========================================================================
    # PRE-GAME AUTOBIOGRAPHICAL SYNTHESIS
    # ========================================================================
    # 
    # Philosophy: Before taking their first action, agents synthesize their
    # complete understanding of a game from all available data sources.
    # This gives agents true Stream A (private memory) that accumulates
    # meaning across sessions - not just aggregate statistics.
    #
    # Key insight: Agents should start each game INFORMED by their history,
    # not "dumb" with NULL values everywhere.
    # ========================================================================

    def synthesize_pregame_autobiography(
        self,
        agent_id: str,
        game_type: str,
        target_level: int,
        current_generation: int = 0,
        is_frontier: bool = False
    ) -> Dict[str, Any]:
        """
        Synthesize agent's complete autobiographical understanding before gameplay.
        
        This is the "What do I know about this game?" query that gives agents
        true private memory (wA) informed by all their past experiences.
        
        Args:
            agent_id: Agent synthesizing their autobiography
            game_type: Game type prefix (e.g., "SP80")
            target_level: Target level to play
            current_generation: Current generation for temporal weighting
            is_frontier: Whether this is an unbeaten game/level
            
        Returns:
            Comprehensive autobiography with strategies, pariahs, theories,
            uncertainties, and metacognitive recommendations
        """
        autobiography = {
            # Identity
            'agent_id': agent_id,
            'game_type': game_type,
            'target_level': target_level,
            'is_frontier': is_frontier,
            'synthesis_timestamp': datetime.now().isoformat(),
            
            # Experience Summary (populated below)
            'total_games_played': 0,
            'total_wins': 0,
            'win_rate': 0.0,
            'weighted_win_rate': 0.0,  # Temporal-weighted
            'max_level_reached': 0,
            'avg_actions_per_game': 0.0,
            
            # What Worked (wA positive)
            'successful_strategies': [],
            'personal_winning_sequences': [],
            'effective_actions': {},
            
            # What To Avoid (wA negative)
            'personal_pariahs': [],
            'dangerous_objects': [],
            'failed_theories': [],
            
            # My Theories (wA hypothetical)
            'active_theories': [],
            'control_hypotheses': [],
            'goal_hypothesis': None,
            
            # Network Influence (wB summary)
            'network_sequences_available': 0,
            'network_best_efficiency': 0.0,
            'viral_packages_received': 0,
            'network_pariahs_for_level': 0,
            
            # Metacognitive Assessment
            'recommended_strategy': None,
            'confidence_level': 0.0,
            'key_uncertainty': None,
            
            # Narrative Summary
            'autobiography_narrative': ''
        }
        
        try:
            # Query 1: Personal game history (aggregated)
            self._populate_game_history(autobiography, agent_id, game_type, current_generation)
            
            # Query 2: Personal action patterns
            self._populate_action_patterns(autobiography, agent_id, game_type)
            
            # Query 3: Personal theories, controls, and pariahs
            self._populate_knowledge_base(autobiography, agent_id, game_type, target_level)
            
            # Query 4: Network influence
            self._populate_network_context(autobiography, game_type, target_level)
            
            # Metacognitive synthesis
            autobiography['recommended_strategy'] = self._compute_recommended_strategy(autobiography)
            autobiography['key_uncertainty'] = self._identify_key_uncertainties(autobiography)
            autobiography['confidence_level'] = autobiography['recommended_strategy'].get('confidence', 0.3)
            
            # Generate human-readable narrative
            autobiography['autobiography_narrative'] = self._generate_autobiography_narrative(autobiography)
            
        except Exception as e:
            logger.error(f"Autobiography synthesis error for {agent_id}: {e}")
            autobiography['autobiography_narrative'] = f"Synthesis failed: {e}. Defaulting to exploration."
            autobiography['recommended_strategy'] = {
                'strategy': 'explore',
                'rationale': 'Synthesis failed',
                'confidence': 0.2
            }
        
        return autobiography

    def _temporal_weight(
        self,
        generation_created: int,
        current_generation: int,
        half_life: int = 20
    ) -> float:
        """
        Weight experiences by recency using exponential decay.
        
        Experience from `half_life` generations ago has 50% weight.
        
        Args:
            generation_created: When the experience occurred
            current_generation: Current generation
            half_life: Generations until 50% decay (default 20)
            
        Returns:
            Weight between 0.0 and 1.0
        """
        # Only skip if current_generation is unknown/invalid
        if current_generation < 0:
            return 1.0  # No temporal data, full weight
        
        # generation_created = 0 is valid (experience from generation 0)
        age = max(0, current_generation - generation_created)
        weight = 0.5 ** (age / half_life) if half_life > 0 else 1.0
        return max(0.01, weight)  # Minimum 1% weight

    def _populate_game_history(
        self,
        autobiography: Dict[str, Any],
        agent_id: str,
        game_type: str,
        current_generation: int
    ) -> None:
        """Populate experience summary from game_results."""
        try:
            # Get aggregate stats
            history = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_games,
                    SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as wins,
                    MAX(levels_completed) as max_level,
                    AVG(actions_used) as avg_actions,
                    AVG(final_score) as avg_score
                FROM game_results
                WHERE agent_id = ? AND game_id LIKE ?
            """, (agent_id, f"{game_type}%"))
            
            if history and history[0]['total_games']:
                h = history[0]
                autobiography['total_games_played'] = h['total_games'] or 0
                autobiography['total_wins'] = h['wins'] or 0
                autobiography['max_level_reached'] = h['max_level'] or 0
                autobiography['avg_actions_per_game'] = h['avg_actions'] or 0.0
                
                if autobiography['total_games_played'] > 0:
                    autobiography['win_rate'] = autobiography['total_wins'] / autobiography['total_games_played']
            
            # Calculate temporal-weighted win rate (recent games matter more)
            if current_generation > 0:
                recent_games = self.db.execute_query("""
                    SELECT final_score, generation
                    FROM game_results
                    WHERE agent_id = ? AND game_id LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (agent_id, f"{game_type}%"))
                
                if recent_games:
                    weighted_wins = 0.0
                    total_weight = 0.0
                    
                    for game in recent_games:
                        gen = game.get('generation', current_generation)
                        weight = self._temporal_weight(gen, current_generation)
                        total_weight += weight
                        if game['final_score'] and game['final_score'] > 0:
                            weighted_wins += weight
                    
                    if total_weight > 0:
                        autobiography['weighted_win_rate'] = weighted_wins / total_weight
                    else:
                        autobiography['weighted_win_rate'] = autobiography['win_rate']
                else:
                    autobiography['weighted_win_rate'] = autobiography['win_rate']
            else:
                autobiography['weighted_win_rate'] = autobiography['win_rate']
                
        except Exception as e:
            logger.debug(f"Game history population failed: {e}")

    def _populate_action_patterns(
        self,
        autobiography: Dict[str, Any],
        agent_id: str,
        game_type: str
    ) -> None:
        """Populate what actions worked/failed from action_traces."""
        try:
            # Get action effectiveness patterns
            actions = self.db.execute_query("""
                SELECT 
                    action_name,
                    COUNT(*) as uses,
                    AVG(score_after - score_before) as avg_delta,
                    SUM(CASE WHEN score_after > score_before THEN 1 ELSE 0 END) as positive_outcomes
                FROM action_traces
                WHERE agent_id = ? AND game_id LIKE ?
                GROUP BY action_name
                ORDER BY avg_delta DESC
            """, (agent_id, f"{game_type}%"))
            
            if actions:
                effective_actions = {}
                for action in actions:
                    action_name = action['action_name']
                    uses = action['uses'] or 0
                    avg_delta = action['avg_delta'] or 0.0
                    positive = action['positive_outcomes'] or 0
                    
                    if uses > 0:
                        effective_actions[action_name] = {
                            'uses': uses,
                            'avg_score_delta': round(avg_delta, 3),
                            'positive_rate': round(positive / uses, 2) if uses > 0 else 0.0
                        }
                
                autobiography['effective_actions'] = effective_actions
                
                # Identify successful strategies (actions with positive avg delta)
                for action_name, data in effective_actions.items():
                    if data['avg_score_delta'] > 0 and data['uses'] >= 5:
                        autobiography['successful_strategies'].append({
                            'description': f"Using {action_name} tends to improve score",
                            'action': action_name,
                            'times_used': data['uses'],
                            'success_rate': data['positive_rate']
                        })
                
        except Exception as e:
            logger.debug(f"Action pattern population failed: {e}")

    def _populate_knowledge_base(
        self,
        autobiography: Dict[str, Any],
        agent_id: str,
        game_type: str,
        target_level: int
    ) -> None:
        """Populate theories, controls, pariahs from knowledge tables."""
        try:
            # Get active theories
            theories = self.db.execute_query("""
                SELECT theory_type, description, confidence, tests_conducted, status
                FROM agent_theories 
                WHERE agent_id = ? AND game_type = ? AND status IN ('testing', 'validated')
                ORDER BY confidence DESC
                LIMIT 10
            """, (agent_id, game_type))
            
            if theories:
                for t in theories:
                    autobiography['active_theories'].append({
                        'type': t['theory_type'],
                        'description': t['description'],
                        'confidence': t['confidence'] or 0.5,
                        'tests': t['tests_conducted'] or 0,
                        'status': t['status']
                    })
            
            # Get control hypotheses (agent discovered)
            controls = self.db.execute_query("""
                SELECT controlled_pattern, action_response, reliability_score, validation_attempts
                FROM network_object_control_hypotheses 
                WHERE discovered_by = ? AND game_type = ? AND is_active = 1
                ORDER BY reliability_score DESC
                LIMIT 10
            """, (agent_id, game_type))
            
            if controls:
                for c in controls:
                    try:
                        pattern = json.loads(c['controlled_pattern']) if c['controlled_pattern'] else {}
                        response = json.loads(c['action_response']) if c['action_response'] else {}
                        autobiography['control_hypotheses'].append({
                            'controlled_color': pattern.get('color', 'unknown'),
                            'action': response.get('action', 'unknown'),
                            'direction': response.get('direction', 'unknown'),
                            'reliability': c['reliability_score'] or 0.5
                        })
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Get goal hypothesis
            goals = self.db.execute_query("""
                SELECT goal_type, goal_params, confidence
                FROM inferred_goal_states
                WHERE game_type = ? AND level_number = ?
                ORDER BY confidence DESC
                LIMIT 1
            """, (game_type, target_level))
            
            if goals and goals[0]:
                autobiography['goal_hypothesis'] = {
                    'goal_type': goals[0]['goal_type'],
                    'confidence': goals[0]['confidence'] or 0.5
                }
            
            # Get pariahs agent has encountered
            pariahs = self.db.execute_query("""
                SELECT p.failure_pattern, p.death_count, p.created_at
                FROM pariahs p
                JOIN agent_pariah_awareness apa ON p.pariah_id = apa.pariah_id
                WHERE apa.agent_id = ? AND p.game_id LIKE ?
                ORDER BY p.death_count DESC
                LIMIT 5
            """, (agent_id, f"{game_type}%"))
            
            if pariahs:
                for p in pariahs:
                    autobiography['personal_pariahs'].append({
                        'pattern': p['failure_pattern'] or 'unknown pattern',
                        'times_died': p['death_count'] or 1,
                        'last_death': p['created_at'] or 'unknown'
                    })
            
            # Get dangerous objects from sensation mappings
            dangers = self.db.execute_query("""
                SELECT object_type, failure_count, sensation_score
                FROM object_sensation_mappings
                WHERE agent_id = ? AND game_type = ? AND failure_count > success_count
                ORDER BY failure_count DESC
                LIMIT 5
            """, (agent_id, game_type))
            
            if dangers:
                for d in dangers:
                    try:
                        # Extract color from object_type like "color_5"
                        color = int(d['object_type'].replace('color_', '')) if d['object_type'] else -1
                        autobiography['dangerous_objects'].append({
                            'color': color,
                            'death_count': d['failure_count'] or 0,
                            'sensation_score': d['sensation_score'] or 0.0
                        })
                    except (ValueError, AttributeError):
                        pass
                        
        except Exception as e:
            logger.debug(f"Knowledge base population failed: {e}")

    def _populate_network_context(
        self,
        autobiography: Dict[str, Any],
        game_type: str,
        target_level: int
    ) -> None:
        """Populate network influence (wB) context."""
        try:
            # Get network sequences available
            sequences = self.db.execute_query("""
                SELECT COUNT(*) as seq_count, MAX(efficiency_score) as best_efficiency
                FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
            """, (f"{game_type}%", target_level))
            
            if sequences and sequences[0]:
                autobiography['network_sequences_available'] = sequences[0]['seq_count'] or 0
                autobiography['network_best_efficiency'] = sequences[0]['best_efficiency'] or 0.0
            
            # Get network pariahs for this level
            pariah_count = self.db.execute_query("""
                SELECT COUNT(*) as pariah_count
                FROM pariahs
                WHERE game_id LIKE ? AND level_number = ?
            """, (f"{game_type}%", target_level))
            
            if pariah_count and pariah_count[0]:
                autobiography['network_pariahs_for_level'] = pariah_count[0]['pariah_count'] or 0
                
        except Exception as e:
            logger.debug(f"Network context population failed: {e}")

    def _compute_recommended_strategy(
        self,
        autobiography: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent metacognition: "What strategy should I use on this game?"
        
        This is the agent's self-awareness - deciding when to trust
        themselves vs trust the network vs explore.
        """
        games_played = autobiography['total_games_played']
        win_rate = autobiography['weighted_win_rate']  # Use temporal-weighted
        network_available = autobiography['network_sequences_available']
        network_efficiency = autobiography['network_best_efficiency']
        is_frontier = autobiography['is_frontier']
        
        # Strategy 1: Explore (frontier games or no data)
        if is_frontier:
            return {
                'strategy': 'explore',
                'rationale': 'Frontier game - no network knowledge exists, must explore',
                'confidence': 0.3
            }
        
        # Strategy 2: Trust Self (experienced + successful)
        if games_played >= 20 and win_rate >= 0.6:
            return {
                'strategy': 'trust_self',
                'rationale': f"Strong personal track record ({win_rate:.0%} win rate from {games_played} games)",
                'confidence': min(0.9, win_rate)
            }
        
        # Strategy 3: Trust Network (novice but network has good solutions)
        if games_played < 5 and network_available >= 5 and network_efficiency > 0.6:
            return {
                'strategy': 'trust_network',
                'rationale': f"Limited personal experience ({games_played} games) but strong network knowledge available ({network_available} sequences)",
                'confidence': network_efficiency
            }
        
        # Strategy 4: Blend (moderate experience, mixed results)
        if games_played >= 5 and network_available > 0:
            # Calculate blend confidence
            personal_factor = min(1.0, win_rate)
            network_factor = min(1.0, network_efficiency)
            blend_confidence = (personal_factor + network_factor) / 2
            
            if win_rate > 0.3:
                return {
                    'strategy': 'blend',
                    'rationale': f"Moderate experience ({win_rate:.0%} win rate) + network knowledge ({network_available} sequences)",
                    'confidence': blend_confidence
                }
        
        # Strategy 5: Explore (insufficient data for other strategies)
        return {
            'strategy': 'explore',
            'rationale': f"Insufficient data (played {games_played} games, {win_rate:.0%} win rate)",
            'confidence': max(0.2, win_rate * 0.5)
        }

    def _identify_key_uncertainties(
        self,
        autobiography: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Agent identifies: "What am I still confused about?"
        
        This is metacognitive awareness of knowledge gaps - agents
        know what they don't know.
        """
        uncertainties = []
        
        # Uncertainty 1: No control hypotheses
        if len(autobiography['control_hypotheses']) == 0:
            uncertainties.append({
                'type': 'control',
                'description': "I don't know how to control any objects",
                'priority': 'high',
                'recommended_action': 'systematic_discovery'
            })
        
        # Uncertainty 2: No goal hypothesis
        if not autobiography['goal_hypothesis'] or autobiography['goal_hypothesis'].get('confidence', 0) < 0.5:
            uncertainties.append({
                'type': 'goal',
                'description': "I'm unclear about the goal of this game",
                'priority': 'high',
                'recommended_action': 'observe_winning_patterns'
            })
        
        # Uncertainty 3: Low win rate despite experience
        if autobiography['total_games_played'] >= 20 and autobiography['win_rate'] < 0.3:
            uncertainties.append({
                'type': 'strategy',
                'description': "My strategies aren't working despite practice",
                'priority': 'medium',
                'recommended_action': 'query_network_for_better_strategies'
            })
        
        # Uncertainty 4: Unstable theories (tested but inconclusive)
        unstable_theories = [
            t for t in autobiography['active_theories']
            if t['tests'] >= 5 and 0.3 < t['confidence'] < 0.7
        ]
        
        if unstable_theories:
            uncertainties.append({
                'type': 'theory_instability',
                'description': f"I have {len(unstable_theories)} theories with unclear validity",
                'priority': 'low',
                'recommended_action': 'focused_testing'
            })
        
        # Uncertainty 5: Many pariahs (danger-prone)
        if len(autobiography['personal_pariahs']) >= 3:
            uncertainties.append({
                'type': 'danger_avoidance',
                'description': f"I've died to {len(autobiography['personal_pariahs'])} different patterns",
                'priority': 'medium',
                'recommended_action': 'cautious_exploration'
            })
        
        # Return highest priority uncertainty (or None)
        if uncertainties:
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            return max(uncertainties, key=lambda u: priority_order.get(u['priority'], 0))
        
        return None

    def _generate_autobiography_narrative(
        self,
        autobiography: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable autobiography summary.
        
        This is for Oracle/human observation and for populating
        the agent's Q3 ("what worked before") reasoning field.
        """
        parts = []
        
        # Opening: Experience summary
        games = autobiography['total_games_played']
        if games == 0:
            parts.append("This is my first time playing this game.")
        elif games < 5:
            parts.append(f"I've only played this game {games} time{'s' if games != 1 else ''}.")
        else:
            parts.append(
                f"I've played this game {games} times, "
                f"winning {autobiography['win_rate']:.0%} of the time."
            )
        
        # What I know works
        if autobiography['successful_strategies']:
            top = autobiography['successful_strategies'][0]
            parts.append(
                f"I've found that {top['description'].lower()} "
                f"(used {top['times_used']} times, {top['success_rate']:.0%} success)."
            )
        
        # What I know to avoid
        if autobiography['personal_pariahs']:
            top_danger = autobiography['personal_pariahs'][0]
            parts.append(
                f"I've learned to avoid {top_danger['pattern']} "
                f"(killed me {top_danger['times_died']} time{'s' if top_danger['times_died'] != 1 else ''})."
            )
        
        # My control knowledge
        controls = autobiography['control_hypotheses']
        if controls:
            parts.append(f"I know how to control {len(controls)} object{'s' if len(controls) != 1 else ''}.")
        else:
            parts.append("I haven't discovered any object controls yet.")
        
        # Active theories
        theories = autobiography['active_theories']
        if theories:
            validated = [t for t in theories if t['status'] == 'validated']
            testing = [t for t in theories if t['status'] == 'testing']
            if validated:
                parts.append(f"I have {len(validated)} validated theor{'ies' if len(validated) != 1 else 'y'}.")
            if testing:
                parts.append(f"I'm testing {len(testing)} theor{'ies' if len(testing) != 1 else 'y'}.")
        
        # Network influence
        network = autobiography['network_sequences_available']
        if network > 0:
            parts.append(f"The network has {network} sequence{'s' if network != 1 else ''} for this level.")
        
        # Current uncertainty
        uncertainty = autobiography['key_uncertainty']
        if uncertainty:
            parts.append(f"My main uncertainty: {uncertainty['description']}")
        
        # Strategy decision
        strategy = autobiography['recommended_strategy']
        if strategy:
            strat = strategy['strategy']
            if strat == 'trust_self':
                parts.append("I'm confident in my own approach.")
            elif strat == 'trust_network':
                parts.append("I'll rely on what others have learned.")
            elif strat == 'blend':
                parts.append("I'll blend my experience with network knowledge.")
            elif strat == 'explore':
                parts.append("I need to explore and experiment.")
        
        return " ".join(parts)

    # ========================================================================
    # RUNTIME AUTOBIOGRAPHY UPDATES (wA/wB Dynamic Weighting)
    # ========================================================================
    # These methods update the autobiography DURING gameplay, allowing
    # the agent's self-model to evolve as they play. The wA/wB weighting
    # adapts based on which stream (personal vs network) is proving reliable.
    # ========================================================================

    def initialize_session_state(
        self,
        autobiography: Dict[str, Any],
        agent_id: Optional[str] = None,
        agent_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize runtime session state within autobiography.
        
        Called at game start to set up tracking for this session.
        This creates the dynamic portion of the autobiography that
        updates as the agent plays.
        
        wA/wB Initialization Priority:
        1. Persisted self_network_bias from DB (if agent has learned bias)
        2. Role-based defaults (if agent has assigned role)
        3. Strategy-based defaults (from autobiography synthesis)
        4. Fallback: 0.5/0.5 balanced
        
        Role-based wA/wB defaults (from AGI theory):
        - PIONEER: wA=0.7, wB=0.3 (favor personal exploration, cautious of network)
        - OPTIMIZER: wA=0.3, wB=0.7 (rely on network sequences, refine)
        - GENERALIST: wA=0.5, wB=0.5 (balanced - sensation-enabled)
        - EXPLOITER: wA=0.4, wB=0.6 (follow network but can break rules)
        
        Args:
            autobiography: Pre-game synthesized autobiography
            agent_id: Agent ID (for DB lookup of persisted bias)
            agent_role: Agent's current role (pioneer/optimizer/generalist/exploiter)
            
        Returns:
            Updated autobiography with session_state initialized
        """
        strategy = autobiography.get('recommended_strategy', {}).get('strategy', 'explore')
        
        # ================================================================
        # PRIORITY 1: Persisted self_network_bias from database
        # ================================================================
        # Agent's learned wA/wB across games - this persists and evolves
        persisted_bias = None
        if agent_id and self.db:
            try:
                result = self.db.execute_query(
                    "SELECT self_network_bias FROM agents WHERE agent_id = ?",
                    (agent_id,)
                )
                if result and result[0].get('self_network_bias') is not None:
                    persisted_bias = result[0]['self_network_bias']
            except Exception as e:
                logger.debug(f"Could not retrieve persisted bias: {e}")
        
        # ================================================================
        # PRIORITY 2: Role-based defaults
        # ================================================================
        # Agent roles have inherent wA/wB tendencies from AGI theory
        role_defaults = {
            'pioneer': (0.7, 0.3),     # Self-reliant explorers
            'optimizer': (0.3, 0.7),    # Network-dependent refiners
            'generalist': (0.5, 0.5),   # Balanced
            'exploiter': (0.4, 0.6),    # Slightly network-favoring
        }
        
        # ================================================================
        # PRIORITY 3: Strategy-based defaults (from autobiography)
        # ================================================================
        strategy_defaults = {
            'trust_self': (0.7, 0.3),
            'trust_network': (0.3, 0.7),
            'blend': (0.5, 0.5),
            'explore': (0.5, 0.5),
        }
        
        # ================================================================
        # RESOLVE INITIAL wA/wB
        # ================================================================
        if persisted_bias is not None:
            # Priority 1: Use persisted bias (self_network_bias is wB)
            initial_wB = persisted_bias
            initial_wA = 1.0 - initial_wB
            bias_source = 'persisted'
        elif agent_role and agent_role.lower() in role_defaults:
            # Priority 2: Use role-based default
            initial_wA, initial_wB = role_defaults[agent_role.lower()]
            bias_source = f'role:{agent_role}'
        else:
            # Priority 3: Use strategy-based default
            initial_wA, initial_wB = strategy_defaults.get(strategy, (0.5, 0.5))
            bias_source = f'strategy:{strategy}'
        
        autobiography['session_state'] = {
            'actions_taken_this_game': 0,
            'actions_taken_this_level': 0,
            'current_level': 1,
            'discoveries_this_game': [],
            'confirmations_this_game': [],
            'contradictions_this_game': [],
            'wA': initial_wA,
            'wB': initial_wB,
            'initial_wA': initial_wA,  # Track starting point for role evaluation
            'initial_wB': initial_wB,
            'bias_source': bias_source,
            'agent_role': agent_role,
            'stream_trust_history': [],
            'level_transitions': [],
            'last_action_source': None,  # 'wA', 'wB', or 'explore'
            'last_action_outcome': None,  # 'positive', 'negative', 'neutral'
        }
        
        autobiography['session_narrative'] = (
            f"Starting game as {agent_role or 'unknown'} with strategy '{strategy}' "
            f"(wA={initial_wA:.2f}, wB={initial_wB:.2f}, source={bias_source})."
        )
        
        return autobiography

    def reset_wA_wB_for_role_change(
        self,
        agent_id: str,
        new_role: str
    ) -> Tuple[float, float]:
        """
        Reset agent's wA/wB bias when they change roles.
        
        Per AGI theory: When agents switch roles, their stream weighting
        should reset to the new role's default, not carry over old habits.
        
        This updates BOTH the database (self_network_bias) and returns
        the new values for session initialization.
        
        Args:
            agent_id: Agent ID
            new_role: New role being assigned
            
        Returns:
            Tuple of (new_wA, new_wB)
        """
        role_defaults = {
            'pioneer': (0.7, 0.3),
            'optimizer': (0.3, 0.7),
            'generalist': (0.5, 0.5),
            'exploiter': (0.4, 0.6),
        }
        
        new_wA, new_wB = role_defaults.get(new_role.lower(), (0.5, 0.5))
        
        # Update database with new bias
        try:
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (new_wB, agent_id)  # self_network_bias is wB
            )
            logger.info(
                f"[ROLE CHANGE] Reset wA/wB for {agent_id[:8]} -> {new_role}: "
                f"wA={new_wA:.2f}, wB={new_wB:.2f}"
            )
        except Exception as e:
            logger.warning(f"Failed to reset wA/wB in DB: {e}")
        
        return new_wA, new_wB

    def update_autobiography_after_action(
        self,
        autobiography: Dict[str, Any],
        action: str,
        action_source: str,  # 'wA' (personal), 'wB' (network), 'explore'
        outcome: str,  # 'positive' (score up), 'negative' (stuck/died), 'neutral'
        discovery: Optional[Dict[str, Any]] = None,
        confirmation: Optional[Dict[str, Any]] = None,
        contradiction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update autobiography based on action outcome.
        
        This is the core runtime learning - adjusting wA/wB weights
        based on which stream is providing better guidance.
        
        Args:
            autobiography: Current autobiography with session_state
            action: Action taken (e.g., 'ACTION1')
            action_source: Which stream influenced this action
            outcome: Result of the action
            discovery: New control/pattern discovered (optional)
            confirmation: Network hypothesis confirmed (optional)
            contradiction: Personal vs network disagreement (optional)
            
        Returns:
            Updated autobiography
        """
        if 'session_state' not in autobiography:
            autobiography = self.initialize_session_state(autobiography)
        
        session = autobiography['session_state']
        session['actions_taken_this_game'] += 1
        session['actions_taken_this_level'] += 1
        
        # Record what happened
        session['last_action_source'] = action_source
        session['last_action_outcome'] = outcome
        
        # Track stream trust history
        session['stream_trust_history'].append({
            'action_num': session['actions_taken_this_game'],
            'source': action_source,
            'outcome': outcome,
            'action': action
        })
        # Keep last 50 entries
        if len(session['stream_trust_history']) > 50:
            session['stream_trust_history'] = session['stream_trust_history'][-50:]
        
        # ================================================================
        # DYNAMIC wA/wB ADJUSTMENT
        # ================================================================
        # Shift trust toward whichever stream is providing better outcomes.
        # Small increments to avoid oscillation.
        # ================================================================
        wA, wB = session['wA'], session['wB']
        
        if action_source == 'wA':  # Personal strategy
            if outcome == 'positive':
                wA = min(0.9, wA + 0.03)  # Reinforce personal trust
                wB = max(0.1, wB - 0.02)
            elif outcome == 'negative':
                wA = max(0.1, wA - 0.02)  # Reduce personal trust
                wB = min(0.9, wB + 0.02)
        elif action_source == 'wB':  # Network strategy
            if outcome == 'positive':
                wB = min(0.9, wB + 0.03)  # Reinforce network trust
                wA = max(0.1, wA - 0.02)
            elif outcome == 'negative':
                wB = max(0.1, wB - 0.02)  # Reduce network trust
                wA = min(0.9, wA + 0.02)
        # Exploration doesn't shift weights
        
        # Normalize to sum = 1.0
        total = wA + wB
        session['wA'] = wA / total
        session['wB'] = wB / total
        
        # ================================================================
        # TRACK DISCOVERIES
        # ================================================================
        if discovery:
            discovery['when'] = f"action {session['actions_taken_this_game']}"
            discovery['level'] = session['current_level']
            session['discoveries_this_game'].append(discovery)
        
        if confirmation:
            confirmation['when'] = f"action {session['actions_taken_this_game']}"
            session['confirmations_this_game'].append(confirmation)
        
        if contradiction:
            contradiction['when'] = f"action {session['actions_taken_this_game']}"
            session['contradictions_this_game'].append(contradiction)
        
        return autobiography

    def update_autobiography_on_level_change(
        self,
        autobiography: Dict[str, Any],
        old_level: int,
        new_level: int,
        actions_to_complete: int
    ) -> Dict[str, Any]:
        """
        Update autobiography when level changes.
        
        This records level completion and resets per-level counters.
        Also updates the narrative with level transition.
        """
        if 'session_state' not in autobiography:
            autobiography = self.initialize_session_state(autobiography)
        
        session = autobiography['session_state']
        
        # Record transition
        session['level_transitions'].append({
            'from_level': old_level,
            'to_level': new_level,
            'actions_taken': actions_to_complete,
            'wA_at_transition': session['wA'],
            'wB_at_transition': session['wB']
        })
        
        session['current_level'] = new_level
        session['actions_taken_this_level'] = 0
        
        # Update narrative
        autobiography['session_narrative'] += (
            f" Completed level {old_level} in {actions_to_complete} actions."
            f" Now on level {new_level} (wA={session['wA']:.2f}, wB={session['wB']:.2f})."
        )
        
        return autobiography

    def get_current_wA_wB(
        self,
        autobiography: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Get current wA/wB weighting for action selection.
        
        Returns:
            Tuple of (wA, wB) where wA + wB = 1.0
        """
        if 'session_state' not in autobiography:
            return (0.5, 0.5)
        return (
            autobiography['session_state']['wA'],
            autobiography['session_state']['wB']
        )

    def get_action_source_recommendation(
        self,
        autobiography: Dict[str, Any],
        personal_action: Optional[str] = None,
        network_action: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Decide which action source to use based on current wA/wB.
        
        This is the core decision function - should the agent follow
        their personal experience (wA) or network wisdom (wB)?
        
        Args:
            autobiography: Current autobiography with session_state
            personal_action: Action suggested by personal experience
            network_action: Action suggested by network knowledge
            
        Returns:
            Tuple of (action, source, reasoning) where:
            - action: The recommended action string
            - source: 'wA', 'wB', or 'explore'
            - reasoning: Human-readable explanation
        """
        if 'session_state' not in autobiography:
            return ('explore', 'explore', 'No session state - exploring')
        
        session = autobiography['session_state']
        wA, wB = session['wA'], session['wB']
        
        # If only one option available
        if personal_action and not network_action:
            return (personal_action, 'wA', f"Using personal strategy (wA={wA:.2f}, no network option)")
        if network_action and not personal_action:
            return (network_action, 'wB', f"Following network (wB={wB:.2f}, no personal option)")
        if not personal_action and not network_action:
            return ('explore', 'explore', "No suggestions from either stream - exploring")
        
        # Both options available - use weighted probabilistic selection
        import random
        
        if personal_action == network_action:
            # Both agree - use either
            return (personal_action, 'blend', f"Both streams agree (wA={wA:.2f}, wB={wB:.2f})")
        
        # Probabilistic selection based on weights
        if random.random() < wA:
            reasoning = (
                f"Choosing personal strategy (wA={wA:.2f} > random). "
                f"Recent outcomes: {self._summarize_recent_outcomes(session, 'wA')}"
            )
            return (personal_action, 'wA', reasoning)
        else:
            reasoning = (
                f"Following network (wB={wB:.2f} > random). "
                f"Recent outcomes: {self._summarize_recent_outcomes(session, 'wB')}"
            )
            return (network_action, 'wB', reasoning)

    def _summarize_recent_outcomes(
        self,
        session: Dict[str, Any],
        source: str
    ) -> str:
        """Summarize recent outcomes for a given source."""
        history = session.get('stream_trust_history', [])
        recent = [h for h in history[-20:] if h['source'] == source]
        if not recent:
            return "no recent data"
        
        positive = sum(1 for h in recent if h['outcome'] == 'positive')
        negative = sum(1 for h in recent if h['outcome'] == 'negative')
        total = len(recent)
        
        return f"{positive}/{total} positive, {negative}/{total} negative"

    def generate_runtime_narrative(
        self,
        autobiography: Dict[str, Any]
    ) -> str:
        """
        Generate current narrative reflecting runtime state.
        
        This combines the static autobiography with dynamic session state
        to create a live self-description.
        """
        base = autobiography.get('autobiography_narrative', '')
        session = autobiography.get('session_state', {})
        
        if not session:
            return base
        
        parts = [base]
        
        # Current session status
        actions = session.get('actions_taken_this_game', 0)
        level = session.get('current_level', 1)
        wA, wB = session.get('wA', 0.5), session.get('wB', 0.5)
        
        parts.append(
            f"Currently on level {level} after {actions} actions "
            f"(wA={wA:.2f}, wB={wB:.2f})."
        )
        
        # Discoveries this session
        discoveries = session.get('discoveries_this_game', [])
        if discoveries:
            parts.append(f"This session I discovered: {len(discoveries)} new control(s).")
        
        # Confirmations/contradictions
        confirmations = session.get('confirmations_this_game', [])
        contradictions = session.get('contradictions_this_game', [])
        
        if confirmations:
            parts.append(f"Network wisdom confirmed {len(confirmations)} time(s).")
        if contradictions:
            parts.append(f"My experience contradicted network {len(contradictions)} time(s).")
        
        # Trust trend
        history = session.get('stream_trust_history', [])
        if len(history) >= 10:
            recent_wA = sum(1 for h in history[-10:] if h['source'] == 'wA' and h['outcome'] == 'positive')
            recent_wB = sum(1 for h in history[-10:] if h['source'] == 'wB' and h['outcome'] == 'positive')
            if recent_wA > recent_wB:
                parts.append("Personal strategies are working better recently.")
            elif recent_wB > recent_wA:
                parts.append("Network wisdom is proving more reliable recently.")
        
        return " ".join(parts)

    def persist_wA_wB_at_game_end(
        self,
        agent_id: str,
        autobiography: Dict[str, Any],
        game_outcome: str  # 'win', 'loss', 'timeout'
    ) -> bool:
        """
        Persist learned wA/wB bias to database at game end.
        
        The agent's wA/wB shifts during gameplay based on outcomes.
        At game end, we blend this session's learned bias with their
        historical bias, weighted by outcome quality.
        
        Philosophy: Wins teach more than losses. Agents that win
        should have their learned biases weighted more heavily.
        
        Args:
            agent_id: Agent ID
            autobiography: Current autobiography with session_state
            game_outcome: 'win', 'loss', or 'timeout'
            
        Returns:
            True if persisted successfully
        """
        if not agent_id or 'session_state' not in autobiography:
            return False
        
        session = autobiography['session_state']
        session_wB = session.get('wB', 0.5)
        initial_wB = session.get('initial_wB', 0.5)
        
        # How much did wB shift this game?
        shift = session_wB - initial_wB
        
        # Only persist if there was meaningful shift (> 0.05)
        if abs(shift) < 0.05:
            logger.debug(
                f"[wA/wB] Agent {agent_id[:8]} wB shift too small ({shift:.3f}), not persisting"
            )
            return False
        
        # Outcome-weighted learning rate
        # Wins: Learn more from this session (blend 40% session, 60% historical)
        # Losses: Learn less (blend 20% session, 80% historical)
        # Timeout: Learn moderately (blend 30% session, 70% historical)
        if game_outcome == 'win':
            session_weight = 0.4
        elif game_outcome == 'timeout':
            session_weight = 0.3
        else:  # loss
            session_weight = 0.2
        
        try:
            # Get current persisted bias
            result = self.db.execute_query(
                "SELECT self_network_bias FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            
            if result and result[0].get('self_network_bias') is not None:
                historical_wB = result[0]['self_network_bias']
            else:
                # No historical - use role default (session has it from initialization)
                historical_wB = initial_wB
            
            # Blend session learning with historical
            new_wB = (session_weight * session_wB) + ((1 - session_weight) * historical_wB)
            
            # Clamp to valid range
            new_wB = max(0.1, min(0.9, new_wB))
            
            # Update database
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (new_wB, agent_id)
            )
            
            logger.info(
                f"[wA/wB] Agent {agent_id[:8]} persisted bias: "
                f"{historical_wB:.2f} -> {new_wB:.2f} "
                f"(session learned {session_wB:.2f}, outcome={game_outcome})"
            )
            return True
            
        except Exception as e:
            logger.warning(f"Failed to persist wA/wB for {agent_id[:8]}: {e}")
            return False


# ============================================================================
# AGENT NETWORK CONTRIBUTOR (Decentralized Knowledge Sharing)
# ============================================================================

class AgentNetworkContributor:
    """
    Enables agents to CONTRIBUTE to and QUERY from the network autonomously.
    
    Philosophy: Intelligence spreads through viral information transfer,
    not hierarchical command. Agents share what they learned (both successes
    and failures) and query peer discoveries - no central coordinator.
    
    Key Mechanisms:
    1. broadcast_failed_attempt() - Share what DIDN'T work
    2. share_success_insight() - Share abstract patterns that worked
    3. query_peer_insights() - Ask what others discovered
    4. check_my_progress() - Self-assess against network baseline
    
    This implements the AGI theory's "viral exchange principle":
    "The infection mechanism IS the coordination mechanism."
    """
    
    def __init__(self, db: DatabaseInterface):
        """Initialize agent network contributor."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure network contribution tables exist."""
        # Failed attempts - what agents tried that didn't work
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_failed_attempts (
                attempt_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- What was tried
                action_sequence TEXT,       -- JSON: list of actions attempted
                attempt_description TEXT,   -- Natural language: "tried going left around obstacle"
                frames_survived INTEGER,    -- How long it lasted
                death_cause TEXT,           -- What killed the attempt (if known)
                
                -- Network learning value
                confirmed_by_others INTEGER DEFAULT 0,  -- How many others hit same wall
                helpful_count INTEGER DEFAULT 0,        -- How many queried this
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_confirmed DATETIME
            )
        """)
        
        # Success insights - abstract patterns that worked
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_success_insights (
                insight_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER,
                
                -- The insight
                insight_type TEXT NOT NULL,     -- 'avoid_pattern', 'approach_pattern', 'timing', 'sequence'
                insight_text TEXT NOT NULL,     -- Natural language: "go around obstacles on the right"
                confidence REAL DEFAULT 0.5,
                
                -- Supporting evidence
                times_worked INTEGER DEFAULT 1,
                times_failed INTEGER DEFAULT 0,
                
                -- Network validation
                peer_confirmations INTEGER DEFAULT 0,
                peer_rejections INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_validated DATETIME
            )
        """)
        
        # Indexes for efficient querying
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_failed_attempts_game 
            ON agent_failed_attempts(game_type, level_number)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_success_insights_game 
            ON agent_success_insights(game_type, level_number, confidence DESC)
        """)
    
    def broadcast_failed_attempt(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action_sequence: List[str] = None,
        attempt_description: str = None,
        frames_survived: int = 0,
        death_cause: str = None
    ) -> Optional[str]:
        """
        Agent broadcasts what they tried that DIDN'T work.
        
        This is viral information transfer - sharing failure patterns helps
        others avoid the same mistakes without central coordination.
        
        Args:
            agent_id: Agent sharing the failure
            game_type: Game type (e.g., "SP80")
            level_number: Level where failure occurred
            action_sequence: List of actions tried
            attempt_description: Natural language description
            frames_survived: How long the attempt lasted
            death_cause: What ended the attempt
            
        Returns:
            attempt_id if broadcasted, None if duplicate/ignored
        """
        import uuid
        import json
        
        # Check if similar failure already exists
        existing = self.db.execute_query("""
            SELECT attempt_id, confirmed_by_others 
            FROM agent_failed_attempts
            WHERE game_type = ? AND level_number = ?
              AND (attempt_description = ? OR action_sequence = ?)
            LIMIT 1
        """, (
            game_type, level_number, 
            attempt_description,
            json.dumps(action_sequence) if action_sequence else None
        ))
        
        if existing:
            # Confirm existing failure - others hit same wall
            self.db.execute_query("""
                UPDATE agent_failed_attempts
                SET confirmed_by_others = confirmed_by_others + 1,
                    last_confirmed = CURRENT_TIMESTAMP
                WHERE attempt_id = ?
            """, (existing[0]['attempt_id'],))
            logger.debug(
                f"[NETWORK] Agent {agent_id[:8]} confirmed failure pattern on {game_type} L{level_number}"
            )
            return existing[0]['attempt_id']
        
        # New failure pattern - broadcast to network
        attempt_id = f"fail_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO agent_failed_attempts (
                attempt_id, agent_id, game_type, level_number,
                action_sequence, attempt_description, frames_survived, death_cause
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt_id, agent_id, game_type, level_number,
            json.dumps(action_sequence) if action_sequence else None,
            attempt_description, frames_survived, death_cause
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} broadcast failure: {game_type} L{level_number} - "
            f"{attempt_description or 'action sequence'}"
        )
        return attempt_id
    
    def share_success_insight(
        self,
        agent_id: str,
        game_type: str,
        insight_text: str,
        insight_type: str = 'approach_pattern',
        level_number: int = None,
        confidence: float = 0.6
    ) -> Optional[str]:
        """
        Agent shares an abstract insight about what WORKED.
        
        Unlike exact sequences, insights are patterns that can transfer:
        - "Go around obstacles on the right side"
        - "Wait for the moving object to pass"
        - "The red objects are dangerous"
        
        Args:
            agent_id: Agent sharing the insight
            game_type: Game type this applies to
            insight_text: Natural language insight
            insight_type: Category ('avoid_pattern', 'approach_pattern', 'timing', 'sequence')
            level_number: Specific level or None for game-wide
            confidence: How confident the agent is (0.0-1.0)
            
        Returns:
            insight_id if shared, None if duplicate
        """
        import uuid
        
        # Check for similar existing insight
        existing = self.db.execute_query("""
            SELECT insight_id, times_worked, peer_confirmations
            FROM agent_success_insights
            WHERE game_type = ? AND insight_text = ?
              AND (level_number = ? OR level_number IS NULL OR ? IS NULL)
            LIMIT 1
        """, (game_type, insight_text, level_number, level_number))
        
        if existing:
            # Peer confirmation - same insight discovered independently
            self.db.execute_query("""
                UPDATE agent_success_insights
                SET times_worked = times_worked + 1,
                    peer_confirmations = peer_confirmations + 1,
                    confidence = MIN(0.95, confidence + 0.05),
                    last_validated = CURRENT_TIMESTAMP
                WHERE insight_id = ?
            """, (existing[0]['insight_id'],))
            logger.debug(
                f"[NETWORK] Agent {agent_id[:8]} confirmed insight on {game_type}: {insight_text[:40]}"
            )
            return existing[0]['insight_id']
        
        # New insight - share with network
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO agent_success_insights (
                insight_id, agent_id, game_type, level_number,
                insight_type, insight_text, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id, agent_id, game_type, level_number,
            insight_type, insight_text, confidence
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} shared insight: {game_type} - {insight_text[:50]}"
        )
        return insight_id
    
    def query_peer_insights(
        self,
        game_type: str,
        level_number: int = None,
        limit: int = 5,
        min_confidence: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Agent queries what other agents discovered.
        
        This is the "ask the network" mechanism - agents pull wisdom
        from peers rather than having it pushed by a coordinator.
        
        Args:
            game_type: Game type to query
            level_number: Specific level or None for game-wide
            limit: Max insights to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of insights ranked by confidence and peer validation
        """
        # Query success insights
        if level_number is not None:
            insights = self.db.execute_query("""
                SELECT 
                    insight_id, insight_type, insight_text, confidence,
                    times_worked, peer_confirmations, peer_rejections,
                    (times_worked + peer_confirmations) as validation_score
                FROM agent_success_insights
                WHERE game_type = ? 
                  AND (level_number = ? OR level_number IS NULL)
                  AND confidence >= ?
                ORDER BY validation_score DESC, confidence DESC
                LIMIT ?
            """, (game_type, level_number, min_confidence, limit))
        else:
            insights = self.db.execute_query("""
                SELECT 
                    insight_id, insight_type, insight_text, confidence,
                    times_worked, peer_confirmations, peer_rejections,
                    (times_worked + peer_confirmations) as validation_score
                FROM agent_success_insights
                WHERE game_type = ? AND confidence >= ?
                ORDER BY validation_score DESC, confidence DESC
                LIMIT ?
            """, (game_type, min_confidence, limit))
        
        # Mark as helpful (for future relevance scoring)
        for insight in insights or []:
            self.db.execute_query("""
                UPDATE agent_success_insights
                SET last_validated = CURRENT_TIMESTAMP
                WHERE insight_id = ?
            """, (insight['insight_id'],))
        
        return [dict(i) for i in insights] if insights else []
    
    def query_peer_failures(
        self,
        game_type: str,
        level_number: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Agent queries what other agents tried that DIDN'T work.
        
        This helps agents avoid repeating known failures.
        
        Args:
            game_type: Game type to query
            level_number: Specific level
            limit: Max failures to return
            
        Returns:
            List of failed attempts to avoid
        """
        failures = self.db.execute_query("""
            SELECT 
                attempt_id, attempt_description, death_cause,
                frames_survived, confirmed_by_others,
                (confirmed_by_others + 1) as certainty_score
            FROM agent_failed_attempts
            WHERE game_type = ? AND level_number = ?
            ORDER BY certainty_score DESC, frames_survived ASC
            LIMIT ?
        """, (game_type, level_number, limit))
        
        # Mark as helpful
        for failure in failures or []:
            self.db.execute_query("""
                UPDATE agent_failed_attempts
                SET helpful_count = helpful_count + 1
                WHERE attempt_id = ?
            """, (failure['attempt_id'],))
        
        return [dict(f) for f in failures] if failures else []
    
    def check_my_progress(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        my_best_score: float = 0,
        my_attempts: int = 1
    ) -> Dict[str, Any]:
        """
        Agent self-assesses their progress against network baseline.
        
        This replaces external "stuck detection" with agent self-awareness.
        Agent asks: "Am I making progress compared to peers?"
        
        Args:
            agent_id: Agent checking progress
            game_type: Game type
            level_number: Level to check
            my_best_score: Agent's best score on this level
            my_attempts: How many attempts agent has made
            
        Returns:
            Dict with progress assessment and recommendations
        """
        # Get network baseline for this level
        network = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT gr.agent_id) as agents_attempted,
                AVG(gr.final_score) as avg_score,
                MAX(gr.final_score) as best_score,
                AVG(gr.actions_used) as avg_actions,
                SUM(CASE WHEN gr.final_score > 0 THEN 1 ELSE 0 END) as successes,
                COUNT(*) as total_attempts
            FROM game_results gr
            WHERE gr.game_id LIKE ?
              AND gr.timestamp > datetime('now', '-24 hours')
        """, (f"{game_type}%",))
        
        if not network or not network[0]['agents_attempted']:
            return {
                'has_network_data': False,
                'assessment': 'exploring_unknown',
                'recommendation': 'continue_exploring',
                'reasoning': 'No network data - pioneering this game'
            }
        
        n = network[0]
        network_success_rate = n['successes'] / n['total_attempts'] if n['total_attempts'] > 0 else 0
        
        # Compare to network
        am_above_average = my_best_score > (n['avg_score'] or 0)
        am_struggling = my_attempts > 5 and my_best_score < (n['avg_score'] or 0) * 0.5
        network_also_struggling = network_success_rate < 0.2
        
        if am_above_average:
            assessment = 'above_network'
            recommendation = 'share_insight'  # I'm doing well, share what works
            reasoning = f"My score {my_best_score:.0f} exceeds network avg {n['avg_score']:.0f}"
        elif am_struggling and not network_also_struggling:
            assessment = 'below_network'
            recommendation = 'query_peers'  # Others succeed, I should ask them
            reasoning = f"I'm struggling ({my_attempts} attempts) but network has {network_success_rate:.0%} success"
        elif am_struggling and network_also_struggling:
            assessment = 'frontier_problem'
            recommendation = 'try_novel'  # Everyone struggles, try something new
            reasoning = f"Network also struggling ({network_success_rate:.0%}) - pioneer new approaches"
        else:
            assessment = 'normal_progress'
            recommendation = 'continue'
            reasoning = f"Making normal progress (score {my_best_score:.0f} vs avg {n['avg_score']:.0f})"
        
        return {
            'has_network_data': True,
            'assessment': assessment,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'network_stats': {
                'agents_attempted': n['agents_attempted'],
                'avg_score': n['avg_score'],
                'best_score': n['best_score'],
                'success_rate': network_success_rate
            },
            'my_stats': {
                'best_score': my_best_score,
                'attempts': my_attempts
            }
        }
    
    def reject_insight(
        self,
        insight_id: str,
        agent_id: str = None
    ) -> None:
        """
        Agent rejects an insight that didn't work for them.
        
        This is the negative feedback that keeps insights honest.
        
        Args:
            insight_id: Insight to reject
            agent_id: Agent rejecting (for logging)
        """
        self.db.execute_query("""
            UPDATE agent_success_insights
            SET times_failed = times_failed + 1,
                peer_rejections = peer_rejections + 1,
                confidence = MAX(0.1, confidence - 0.1)
            WHERE insight_id = ?
        """, (insight_id,))
        
        logger.debug(f"[NETWORK] Insight {insight_id[:12]} rejected - confidence reduced")


# ============================================================================
# AGENT-INITIATED HYPOTHESIS SYSTEM
# ============================================================================

class AgentHypothesisSystem:
    """
    Enables agents to CREATE hypotheses, not just follow them.
    
    Key insight: Formal operational agents should be able to:
    1. Notice patterns in their experience
    2. Formulate testable hypotheses
    3. Design experiments to test them
    4. Update beliefs based on results
    
    This requires FORMAL_OPERATIONAL cognitive stage.
    """
    
    def __init__(self, db: DatabaseInterface, cognitive_system: CognitiveStageSystem):
        """Initialize agent hypothesis system."""
        self.db = db
        self.cognitive_system = cognitive_system
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure agent hypothesis tables exist."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                
                -- Hypothesis content
                game_type TEXT NOT NULL,
                level_number INTEGER,
                hypothesis_text TEXT NOT NULL,
                hypothesis_type TEXT NOT NULL,  -- 'object_behavior', 'action_effect', 'sequence_pattern', 'game_rule'
                
                -- PRIMITIVE-AWARE HYPOTHESIS STRUCTURE
                -- Hypotheses are now expressed in terms of primitives + actions
                primitives_used TEXT,            -- JSON: list of primitives referenced in this hypothesis
                trigger_condition TEXT,          -- JSON: {primitive: name, params: {...}} - what triggers the action
                predicted_action TEXT,           -- ACTION1-ACTION7 that the hypothesis suggests
                action_sequence TEXT,            -- JSON: sequence of actions if multi-step
                
                -- Evidence and confidence
                supporting_evidence TEXT,        -- JSON: list of observations supporting this
                contradicting_evidence TEXT,     -- JSON: list of observations against this
                confidence REAL DEFAULT 0.5,
                
                -- Testing
                tests_conducted INTEGER DEFAULT 0,
                tests_successful INTEGER DEFAULT 0,
                last_tested DATETIME,
                
                -- Status
                status TEXT DEFAULT 'proposed',  -- 'proposed', 'testing', 'confirmed', 'refuted', 'abandoned'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        # Add new columns if table already exists (migration)
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN primitives_used TEXT")
        except:
            pass  # Column already exists
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN trigger_condition TEXT")
        except:
            pass
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN predicted_action TEXT")
        except:
            pass
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN action_sequence TEXT")
        except:
            pass
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_agent_hypotheses_game 
            ON agent_hypotheses(game_type, level_number, status)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_agent_hypotheses_agent 
            ON agent_hypotheses(agent_id, status)
        """)

        # Telemetry for hypothesis promotion/decay events (DB-only)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacog_hypothesis_events (
                event_id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,         -- 'promotion', 'decay'
                from_status TEXT,
                to_status TEXT,
                confidence_before REAL,
                confidence_after REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def can_create_hypothesis(self, agent_id: str) -> bool:
        """Check if agent has the cognitive capability to create hypotheses."""
        capabilities = self.cognitive_system.get_stage_capabilities(agent_id)
        return capabilities.get('hypothesis_generation', False)
    
    def create_hypothesis(
        self,
        agent_id: str,
        game_type: str,
        hypothesis_text: str,
        hypothesis_type: str,
        level_number: int = None,
        initial_evidence: List[str] = None,
        primitives_used: List[str] = None,
        trigger_condition: Dict[str, Any] = None,
        predicted_action: str = None,
        action_sequence: List[str] = None
    ) -> Optional[str]:
        """
        Agent creates a new hypothesis based on observations.
        
        Only agents in FORMAL_OPERATIONAL stage can create hypotheses.
        
        PRIMITIVE-AWARE HYPOTHESES:
        Hypotheses can now be expressed in terms of:
        - primitives_used: Which primitives inform this hypothesis
        - trigger_condition: {primitive: 'detect_color_change', params: {color: 'red'}}
        - predicted_action: 'ACTION2' - what to do when trigger fires
        - action_sequence: ['ACTION2', 'ACTION4'] - multi-step response
        
        Args:
            agent_id: Agent creating hypothesis
            game_type: Game type this applies to
            hypothesis_text: Natural language hypothesis
            hypothesis_type: Category ('object_behavior', 'action_effect', 'sequence_pattern', 'game_rule')
            level_number: Optional specific level
            initial_evidence: List of observations supporting this hypothesis
            primitives_used: List of primitive names used in this hypothesis
            trigger_condition: Dict with primitive and params that trigger the action
            predicted_action: Single action prediction (ACTION1-ACTION7)
            action_sequence: Sequence of actions if multi-step
            
        Returns:
            hypothesis_id if created, None if agent lacks capability
        """
        if not self.can_create_hypothesis(agent_id):
            logger.debug(f"[HYPOTHESIS] Agent {agent_id[:8]} lacks cognitive stage for hypothesis creation")
            return None
        
        import uuid
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:12]}"
        
        evidence_json = json.dumps(initial_evidence or [])
        primitives_json = json.dumps(primitives_used or [])
        trigger_json = json.dumps(trigger_condition) if trigger_condition else None
        sequence_json = json.dumps(action_sequence) if action_sequence else None
        
        self.db.execute_query("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, level_number, hypothesis_text, 
             hypothesis_type, supporting_evidence, confidence, status,
             primitives_used, trigger_condition, predicted_action, action_sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?)
        """, (hypothesis_id, agent_id, game_type, level_number, hypothesis_text,
              hypothesis_type, evidence_json, 0.5,
              primitives_json, trigger_json, predicted_action, sequence_json))
        
        # Update agent's competency
        self.cognitive_system.update_competencies(agent_id, hypotheses_created_delta=1)
        
        # Log with primitive info if available
        if primitives_used:
            logger.info(f"[HYPOTHESIS] Agent {agent_id[:8]} created primitive-aware: {hypothesis_text[:40]}... using {primitives_used}")
        else:
            logger.info(f"[HYPOTHESIS] Agent {agent_id[:8]} created: {hypothesis_text[:50]}...")
        
        return hypothesis_id

    def _log_hypothesis_event(
        self,
        *,
        hypothesis_id: str,
        agent_id: str,
        event_type: str,
        from_status: Optional[str],
        to_status: Optional[str],
        confidence_before: Optional[float],
        confidence_after: Optional[float]
    ) -> None:
        """Record promotion/decay telemetry (DB-only)."""
        try:
            event_id = f"h_evt_{uuid.uuid4().hex[:12]}"
            self.db.execute_query(
                """
                INSERT INTO metacog_hypothesis_events (
                    event_id, hypothesis_id, agent_id, event_type,
                    from_status, to_status, confidence_before, confidence_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    hypothesis_id,
                    agent_id,
                    event_type,
                    from_status,
                    to_status,
                    confidence_before,
                    confidence_after,
                ),
            )
        except Exception as e:
            logger.debug(f"[HYPOTHESIS] Event log failed: {e}")
    
    def record_test_result(
        self,
        hypothesis_id: str,
        success: bool,
        observation: str = None
    ) -> Dict[str, Any]:
        """
        Record the result of testing a hypothesis.
        
        Returns updated hypothesis status and confidence.
        """
        # Get current hypothesis
        result = self.db.execute_query("""
            SELECT * FROM agent_hypotheses WHERE hypothesis_id = ?
        """, (hypothesis_id,))
        
        if not result:
            return {'error': 'hypothesis_not_found'}
        
        h = result[0]
        
        # Update test counts
        tests = h['tests_conducted'] + 1
        successes = h['tests_successful'] + (1 if success else 0)
        
        # Calculate new confidence using Bayesian-ish update
        prior = h['confidence']
        if success:
            new_confidence = prior + (1.0 - prior) * 0.2  # Move toward 1.0
        else:
            new_confidence = prior * 0.8  # Decay toward 0
        
        new_confidence = max(0.05, min(0.95, new_confidence))
        
        # Update evidence
        evidence_key = 'supporting_evidence' if success else 'contradicting_evidence'
        existing_evidence = json.loads(h[evidence_key] or '[]')
        if observation:
            existing_evidence.append(observation)
        evidence_json = json.dumps(existing_evidence[-10:])  # Keep last 10
        
        # Determine status
        status = h['status']
        if new_confidence > 0.85 and tests >= 3:
            status = 'confirmed'
        elif new_confidence < 0.15 and tests >= 3:
            status = 'refuted'
        elif status == 'proposed':
            status = 'testing'

        # Telemetry: log promotion/decay when status changes or confidence drops
        try:
            event_type = None
            from_status = h['status']
            to_status = status

            if to_status != from_status:
                event_type = 'promotion' if to_status in {'testing', 'confirmed'} else 'decay'
            elif new_confidence < prior:
                event_type = 'decay'

            if event_type:
                self._log_hypothesis_event(
                    hypothesis_id=hypothesis_id,
                    agent_id=h['agent_id'],
                    event_type=event_type,
                    from_status=from_status,
                    to_status=to_status,
                    confidence_before=prior,
                    confidence_after=new_confidence,
                )
        except Exception:
            pass
        
        self.db.execute_query(f"""
            UPDATE agent_hypotheses
            SET tests_conducted = ?,
                tests_successful = ?,
                confidence = ?,
                {evidence_key} = ?,
                status = ?,
                last_tested = CURRENT_TIMESTAMP
            WHERE hypothesis_id = ?
        """, (tests, successes, new_confidence, evidence_json, status, hypothesis_id))
        
        return {
            'hypothesis_id': hypothesis_id,
            'new_confidence': new_confidence,
            'status': status,
            'tests_conducted': tests,
            'tests_successful': successes
        }
    
    def get_agent_hypotheses(
        self,
        agent_id: str,
        game_type: str = None,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """Get hypotheses created by an agent."""
        query = "SELECT * FROM agent_hypotheses WHERE agent_id = ?"
        params = [agent_id]
        
        if game_type:
            query += " AND game_type = ?"
            params.append(game_type)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT 20"
        
        result = self.db.execute_query(query, tuple(params))
        return [dict(r) for r in result] if result else []
    
    def suggest_hypothesis_from_pattern(
        self,
        agent_id: str,
        game_type: str,
        observations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze observations and suggest a hypothesis the agent could create.
        
        This helps agents generate hypotheses by finding patterns in their experience.
        """
        if not self.can_create_hypothesis(agent_id):
            return None
        
        if len(observations) < 3:
            return None  # Need minimum observations
        
        # Look for action-effect patterns
        action_effects = {}
        for obs in observations:
            action = obs.get('action')
            effect = obs.get('effect')
            if action and effect:
                if action not in action_effects:
                    action_effects[action] = []
                action_effects[action].append(effect)
        
        # Find consistent patterns
        for action, effects in action_effects.items():
            if len(effects) >= 2:
                # Check if same effect occurs consistently
                effect_counts = {}
                for e in effects:
                    effect_counts[e] = effect_counts.get(e, 0) + 1
                
                for effect, count in effect_counts.items():
                    if count >= 2:
                        return {
                            'suggested_hypothesis': f"ACTION{action} consistently causes {effect}",
                            'hypothesis_type': 'action_effect',
                            'evidence_count': count,
                            'confidence': count / len(effects)
                        }
        
        return None

    def generate_primitive_aware_hypothesis(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        available_primitives: List[str],
        game_observations: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a hypothesis that explicitly references available primitives.
        
        This is the key method that connects primitives to hypothesis formation.
        The agent thinks: "Given I have [primitives], what combination + actions
        might help me progress?"
        
        Args:
            agent_id: Agent creating hypothesis
            game_type: Current game type
            level_number: Current level
            available_primitives: List of primitive names agent can use
            game_observations: Dict with observed patterns:
                - frame_changes: What changed between frames
                - controlled_objects: What agent controls
                - stuck_pattern: How agent is stuck (if any)
                - action_effects: Observed action->effect mappings
                - goal_indicators: Detected goal patterns
                
        Returns:
            hypothesis_id if created, None otherwise
        """
        if not self.can_create_hypothesis(agent_id):
            return None
        
        # ===================================================================
        # PRIMITIVE-BASED REASONING
        # Map observations to primitives that could detect/exploit them
        # ===================================================================
        
        primitives_to_use = []
        trigger_condition = None
        predicted_action = None
        action_sequence = None
        
        # 1. OBJECT DETECTION -> Movement primitives
        controlled = game_observations.get('controlled_objects', [])
        if controlled:
            # Agent knows what it controls - can use movement detection
            if 'detect_movement' in available_primitives:
                primitives_to_use.append('detect_movement')
            if 'track_object' in available_primitives:
                primitives_to_use.append('track_object')
        
        # 2. FRAME CHANGES -> Pattern detection primitives
        frame_changes = game_observations.get('frame_changes', {})
        if frame_changes:
            change_type = frame_changes.get('type', 'unknown')
            
            if change_type == 'color_change' and 'detect_color_change' in available_primitives:
                primitives_to_use.append('detect_color_change')
                trigger_condition = {
                    'primitive': 'detect_color_change',
                    'params': {'watch_for': frame_changes.get('colors', [])}
                }
            
            if change_type == 'boundary_hit' and 'detect_boundary' in available_primitives:
                primitives_to_use.append('detect_boundary')
                trigger_condition = {
                    'primitive': 'detect_boundary',
                    'params': {'direction': frame_changes.get('direction')}
                }
            
            if change_type == 'object_appeared' and 'detect_new_object' in available_primitives:
                primitives_to_use.append('detect_new_object')
        
        # 3. STUCK PATTERNS -> Escape strategy primitives
        stuck_pattern = game_observations.get('stuck_pattern')
        if stuck_pattern:
            if 'oscillation' in stuck_pattern.lower():
                # Oscillating = need to break pattern
                if 'detect_oscillation' in available_primitives:
                    primitives_to_use.append('detect_oscillation')
                # Suggest a different action
                last_actions = game_observations.get('last_actions', [])
                if last_actions:
                    # Avoid the oscillating actions
                    used_actions = set(last_actions[-4:])
                    for a in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6']:
                        if a not in used_actions:
                            predicted_action = a
                            break
        
        # 4. GOAL INDICATORS -> Goal-seeking primitives  
        goal_indicators = game_observations.get('goal_indicators', {})
        if goal_indicators:
            goal_direction = goal_indicators.get('direction')
            if goal_direction and 'identify_goal' in available_primitives:
                primitives_to_use.append('identify_goal')
                # Map direction to action
                direction_to_action = {
                    'up': 'ACTION1', 'right': 'ACTION2',
                    'down': 'ACTION4', 'left': 'ACTION3'
                }
                predicted_action = direction_to_action.get(goal_direction, 'ACTION6')
        
        # 5. ACTION EFFECTS -> Use proven patterns
        action_effects = game_observations.get('action_effects', {})
        if action_effects:
            # Find actions that had positive effects
            for action, effect in action_effects.items():
                if effect.get('positive'):
                    # This action worked before
                    if 'get_last_action' in available_primitives:
                        primitives_to_use.append('get_last_action')
                    if not predicted_action:
                        predicted_action = action
        
        # ===================================================================
        # GENERATE HYPOTHESIS
        # ===================================================================
        
        if not primitives_to_use:
            # No specific primitives matched - use basic reasoning
            primitives_to_use = [p for p in available_primitives 
                                if p in ['get_frame', 'get_action_history', 'frame_diff']][:3]
        
        # Build hypothesis text
        if trigger_condition and predicted_action:
            hypothesis_text = (
                f"When {trigger_condition['primitive']} detects change, "
                f"execute {predicted_action} to progress"
            )
        elif predicted_action:
            hypothesis_text = f"Execute {predicted_action} based on observed patterns"
        elif stuck_pattern:
            hypothesis_text = f"Escape {stuck_pattern} by trying alternative actions"
        else:
            hypothesis_text = f"Explore using {primitives_to_use[:2]} to find path forward"
        
        # Create the hypothesis
        return self.create_hypothesis(
            agent_id=agent_id,
            game_type=game_type,
            hypothesis_text=hypothesis_text,
            hypothesis_type='action_effect' if predicted_action else 'sequence_pattern',
            level_number=level_number,
            initial_evidence=[json.dumps(game_observations)],
            primitives_used=primitives_to_use,
            trigger_condition=trigger_condition,
            predicted_action=predicted_action,
            action_sequence=action_sequence
        )

    def get_primitive_based_action(
        self,
        agent_id: str,
        game_type: str,
        level_number: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an action recommendation based on agent's primitive-aware hypotheses.
        
        This queries the agent's confirmed/testing hypotheses and returns
        an actionable recommendation if a trigger condition is met.
        
        Returns:
            Dict with 'action', 'hypothesis_id', 'confidence', 'primitives' or None
        """
        # Get agent's active primitive-aware hypotheses
        hypotheses = self.db.execute_query("""
            SELECT hypothesis_id, predicted_action, trigger_condition,
                   action_sequence, primitives_used, confidence, hypothesis_text
            FROM agent_hypotheses
            WHERE agent_id = ?
              AND game_type = ?
              AND (level_number = ? OR level_number IS NULL)
              AND status IN ('proposed', 'testing', 'confirmed')
              AND predicted_action IS NOT NULL
            ORDER BY 
                CASE status 
                    WHEN 'confirmed' THEN 1 
                    WHEN 'testing' THEN 2 
                    ELSE 3 
                END,
                confidence DESC
            LIMIT 5
        """, (agent_id, game_type, level_number))
        
        if not hypotheses:
            return None
        
        # Return the highest confidence hypothesis with an action
        for h in hypotheses:
            if h['predicted_action']:
                return {
                    'action': h['predicted_action'],
                    'hypothesis_id': h['hypothesis_id'],
                    'confidence': h['confidence'],
                    'primitives': json.loads(h['primitives_used'] or '[]'),
                    'reasoning': h['hypothesis_text']
                }
        
        return None

    def get_hypotheses_by_primitives(
        self,
        primitives: List[str],
        game_type: str = None,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find hypotheses that use specific primitives.
        
        Useful for:
        - Finding how other agents used a primitive
        - Learning from network's primitive combinations
        - Identifying which primitives lead to success
        
        Args:
            primitives: List of primitive names to search for
            game_type: Optional game type filter
            min_confidence: Minimum hypothesis confidence
            
        Returns:
            List of matching hypotheses with usage context
        """
        # Build query to search JSON primitives_used field
        matches = []
        
        for primitive in primitives:
            query = """
                SELECT h.*, a.fitness
                FROM agent_hypotheses h
                LEFT JOIN agents a ON h.agent_id = a.agent_id
                WHERE h.primitives_used LIKE ?
                  AND h.confidence >= ?
                  AND h.status IN ('testing', 'confirmed')
            """
            params = [f'%"{primitive}"%', min_confidence]
            
            if game_type:
                query += " AND h.game_type = ?"
                params.append(game_type)
            
            query += " ORDER BY h.confidence DESC LIMIT 10"
            
            results = self.db.execute_query(query, tuple(params))
            if results:
                for r in results:
                    matches.append({
                        'hypothesis_id': r['hypothesis_id'],
                        'agent_id': r['agent_id'],
                        'hypothesis_text': r['hypothesis_text'],
                        'primitives': json.loads(r['primitives_used'] or '[]'),
                        'predicted_action': r['predicted_action'],
                        'confidence': r['confidence'],
                        'agent_fitness': r.get('fitness', 0),
                        'status': r['status']
                    })
        
        # Deduplicate and sort by confidence
        seen = set()
        unique = []
        for m in matches:
            if m['hypothesis_id'] not in seen:
                seen.add(m['hypothesis_id'])
                unique.append(m)
        
        return sorted(unique, key=lambda x: x['confidence'], reverse=True)


if __name__ == "__main__":
    # Test self-model system
    print("=" * 70)
    print("AGENT SELF-MODEL SYSTEM TEST")
    print("=" * 70)
    
    asm = AgentSelfModel()
    
    # Test table creation
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='agent_object_control'
    """)
    
    if result:
        print("[OK] agent_object_control table exists")
    else:
        print("[FAIL] Table creation failed")
    
    # Test ACTION5 behavior table
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='action5_behavior_map'
    """)
    
    if result:
        print("[OK] action5_behavior_map table exists")
    else:
        print("[FAIL] ACTION5 behavior table creation failed")
    
    # Test basic functionality
    test_controlled = ["x:5,y:10", "x:6,y:10"]
    asm.store_control_map("test_agent", "test_game", 1, test_controlled, 0.85)
    
    retrieved = asm.get_controlled_objects("test_agent", "test_game", 1)
    if retrieved == test_controlled:
        print("[OK] Store and retrieve working")
    else:
        print(f"[FAIL] Mismatch: {retrieved} != {test_controlled}")
    
    # Test ACTION5 behavior storage
    asm.save_action5_behavior(
        game_type="test_game_type",
        level=1,
        behavior_type="rotation",
        affected_objects=["3", "5"],
        effect_description="ACTION5 rotates object 3",
        confidence=0.75
    )
    
    behavior = asm.get_action5_behavior("test_game_type", 1)
    if behavior and behavior['behavior_type'] == "rotation":
        print("[OK] ACTION5 behavior storage working")
    else:
        print(f"[FAIL] ACTION5 behavior mismatch: {behavior}")
    
    # Test pseudo button behavior storage
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pseudo_button_behavior'
    """)
    
    if result:
        print("[OK] pseudo_button_behavior table exists")
    else:
        print("[FAIL] Pseudo button table creation failed")
    
    # Test pseudo button storage
    asm.save_pseudo_button_behavior(
        game_type="test_game_type",
        level=1,
        region_x=7,
        region_y=0,
        produces_action="move_up",
        movement_direction="up",
        affected_objects=["3"],
        effect_description="Clicking top-right moves object up",
        confidence=0.8
    )
    
    button = asm.get_pseudo_button_behavior("test_game_type", 1, 7, 0)
    if button and button['produces_action'] == "move_up":
        print("[OK] Pseudo button behavior storage working")
    else:
        print(f"[FAIL] Pseudo button behavior mismatch: {button}")
    
    # Test get all buttons
    all_buttons = asm.get_all_pseudo_buttons("test_game_type", 1)
    if len(all_buttons) >= 1:
        print(f"[OK] Get all pseudo buttons working ({len(all_buttons)} buttons)")
    else:
        print("[FAIL] Get all pseudo buttons failed")
    
    print("\n[OK] Agent Self-Model system operational")
