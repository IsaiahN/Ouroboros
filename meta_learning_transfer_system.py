#!/usr/bin/env python3
"""
META-LEARNING TRANSFER SYSTEM
==============================
Revolutionary system for learning transferable knowledge across different games and contexts.

This system enables cross-game knowledge transfer through:
- Meta-learning algorithms for rapid adaptation
- Transferable strategy patterns and concepts
- Few-shot learning for new game scenarios
- Knowledge base of reusable game principles
- Context-aware strategy adaptation
- Performance transfer optimization
"""

import os
import sys

# Disable Python bytecode generation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import numpy as np
import json
import time
import logging
import sqlite3
import random
import math
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque, Counter
from enum import Enum
import threading
import pickle
import hashlib

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Types of transferable knowledge."""
    STRATEGY_PATTERN = "strategy_pattern"
    ACTION_SEQUENCE = "action_sequence"
    COORDINATE_PATTERN = "coordinate_pattern"
    SUCCESS_CONDITION = "success_condition"
    FAILURE_PATTERN = "failure_pattern"
    META_STRATEGY = "meta_strategy"

class TransferScope(Enum):
    """Scope of knowledge transfer."""
    WITHIN_GAME = "within_game"      # Transfer within same game type
    CROSS_GAME = "cross_game"        # Transfer across different games
    CROSS_DOMAIN = "cross_domain"    # Transfer across different domains

class AdaptationMethod(Enum):
    """Methods for adapting knowledge to new contexts."""
    DIRECT_TRANSFER = "direct_transfer"
    ANALOGICAL_MAPPING = "analogical_mapping"
    PARAMETER_TUNING = "parameter_tuning"
    STRATEGY_SYNTHESIS = "strategy_synthesis"

@dataclass
class GameContext:
    """Context information for a game."""
    game_id: str
    game_type: str  # e.g., "LP85", "FT09", etc.
    target_score: float
    max_actions: int
    action_space: List[int]
    initial_state: Dict[str, Any]
    final_state: Dict[str, Any]
    total_actions: int
    final_score: float
    success: bool

@dataclass
class TransferableKnowledge:
    """Encapsulation of transferable knowledge."""
    knowledge_id: str
    knowledge_type: KnowledgeType
    content: Dict[str, Any]

    # Context information
    source_games: List[str]
    applicable_contexts: List[str]
    success_rate: float
    usage_count: int

    # Transfer metrics
    transfer_success_rate: float
    adaptation_difficulty: float
    generalization_score: float

    # Metadata
    created_at: float
    last_used: float
    confidence: float

@dataclass
class StrategyPattern:
    """Represents a reusable strategy pattern."""
    pattern_id: str
    name: str
    description: str

    # Pattern definition
    action_sequence: List[str]
    condition_requirements: List[str]
    expected_outcomes: List[str]

    # Context adaptation
    adaptable_parameters: Dict[str, Any]
    context_mapping: Dict[str, str]

    # Performance data
    success_contexts: List[str]
    failure_contexts: List[str]
    average_effectiveness: float

class MetaLearner:
    """Meta-learning algorithm for extracting transferable patterns."""

    def __init__(self):
        """Initialize meta-learner."""
        self.pattern_extractor = PatternExtractor()
        self.similarity_calculator = ContextSimilarityCalculator()
        self.adaptation_engine = KnowledgeAdaptationEngine()

    def extract_knowledge_from_games(self, game_sessions: List[Dict[str, Any]]) -> List[TransferableKnowledge]:
        """Extract transferable knowledge from multiple game sessions."""
        knowledge_items = []

        # Group games by type and performance
        game_groups = self._group_games_by_characteristics(game_sessions)

        for group_name, games in game_groups.items():
            # Extract patterns from each group
            patterns = self.pattern_extractor.extract_patterns(games)

            for pattern in patterns:
                knowledge = self._convert_pattern_to_knowledge(pattern, games, group_name)
                knowledge_items.append(knowledge)

        return knowledge_items

    def _group_games_by_characteristics(self, game_sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group games by similar characteristics."""
        groups = defaultdict(list)

        for game in game_sessions:
            # Group by game type and performance level
            game_type = game.get('game_id', 'unknown')[:4]  # e.g., 'LP85'
            success = game.get('success', False)
            score_ratio = game.get('final_score', 0) / game.get('target_score', 1)

            if success:
                group_key = f"{game_type}_successful"
            elif score_ratio > 0.5:
                group_key = f"{game_type}_moderate"
            else:
                group_key = f"{game_type}_struggling"

            groups[group_key].append(game)

        return groups

    def _convert_pattern_to_knowledge(self, pattern: Dict[str, Any],
                                    source_games: List[Dict[str, Any]],
                                    group_name: str) -> TransferableKnowledge:
        """Convert extracted pattern to transferable knowledge."""
        knowledge_id = hashlib.md5(str(pattern).encode()).hexdigest()[:8]

        # Determine knowledge type
        if 'action_sequence' in pattern:
            knowledge_type = KnowledgeType.ACTION_SEQUENCE
        elif 'coordinate_pattern' in pattern:
            knowledge_type = KnowledgeType.COORDINATE_PATTERN
        elif 'success_condition' in pattern:
            knowledge_type = KnowledgeType.SUCCESS_CONDITION
        else:
            knowledge_type = KnowledgeType.STRATEGY_PATTERN

        # Calculate success rate
        successful_games = [g for g in source_games if g.get('success', False)]
        success_rate = len(successful_games) / len(source_games) if source_games else 0.0

        # Create knowledge item
        knowledge = TransferableKnowledge(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            content=pattern,
            source_games=[g.get('game_id', '') for g in source_games],
            applicable_contexts=[group_name],
            success_rate=success_rate,
            usage_count=0,
            transfer_success_rate=0.0,
            adaptation_difficulty=0.5,
            generalization_score=self._calculate_generalization_score(pattern, source_games),
            created_at=time.time(),
            last_used=0.0,
            confidence=success_rate
        )

        return knowledge

    def _calculate_generalization_score(self, pattern: Dict[str, Any],
                                      source_games: List[Dict[str, Any]]) -> float:
        """Calculate how well a pattern generalizes across different contexts."""
        if len(source_games) < 2:
            return 0.0

        # Calculate diversity of source games
        game_types = set(g.get('game_id', '')[:4] for g in source_games)
        score_ranges = [g.get('final_score', 0) for g in source_games]

        # Diversity measures
        type_diversity = len(game_types) / max(len(source_games), 1)
        score_diversity = np.std(score_ranges) / (np.mean(score_ranges) + 1e-6) if score_ranges else 0.0

        # Pattern complexity (simpler patterns generalize better)
        pattern_complexity = len(str(pattern)) / 1000.0  # Normalize by string length
        complexity_factor = 1.0 / (1.0 + pattern_complexity)

        generalization_score = (type_diversity + min(score_diversity, 1.0)) * complexity_factor / 2.0
        return min(generalization_score, 1.0)

class PatternExtractor:
    """Extracts reusable patterns from game data."""

    def extract_patterns(self, game_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns from game sessions."""
        patterns = []

        # Extract action sequence patterns
        patterns.extend(self._extract_action_sequences(game_sessions))

        # Extract coordinate patterns
        patterns.extend(self._extract_coordinate_patterns(game_sessions))

        # Extract success condition patterns
        patterns.extend(self._extract_success_conditions(game_sessions))

        # Extract failure patterns
        patterns.extend(self._extract_failure_patterns(game_sessions))

        return patterns

    def _extract_action_sequences(self, game_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common action sequences."""
        patterns = []

        # Collect all action sequences
        all_sequences = []
        for game in game_sessions:
            actions = game.get('action_history', [])
            if len(actions) >= 3:
                # Extract subsequences of length 3-5
                for length in range(3, min(6, len(actions) + 1)):
                    for i in range(len(actions) - length + 1):
                        sequence = tuple(actions[i:i+length])
                        all_sequences.append(sequence)

        # Find frequent sequences
        sequence_counts = Counter(all_sequences)
        frequent_sequences = [seq for seq, count in sequence_counts.items()
                            if count >= max(2, len(game_sessions) * 0.3)]

        for sequence in frequent_sequences:
            pattern = {
                'type': 'action_sequence',
                'action_sequence': list(sequence),
                'frequency': sequence_counts[sequence],
                'context_requirements': self._infer_sequence_context(sequence, game_sessions)
            }
            patterns.append(pattern)

        return patterns

    def _extract_coordinate_patterns(self, game_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract coordinate usage patterns."""
        patterns = []

        # Collect coordinate data
        coordinate_data = []
        for game in game_sessions:
            coords = game.get('coordinate_history', [])
            if coords:
                coordinate_data.extend(coords)

        if not coordinate_data:
            return patterns

        # Analyze coordinate clusters
        clusters = self._find_coordinate_clusters(coordinate_data)

        for i, cluster in enumerate(clusters):
            if len(cluster) >= 3:  # Significant cluster
                center = self._calculate_cluster_center(cluster)
                radius = self._calculate_cluster_radius(cluster, center)

                pattern = {
                    'type': 'coordinate_pattern',
                    'coordinate_pattern': {
                        'center': center,
                        'radius': radius,
                        'coordinates': cluster,
                        'usage_frequency': len(cluster)
                    }
                }
                patterns.append(pattern)

        return patterns

    def _extract_success_conditions(self, game_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns that lead to success."""
        patterns = []

        successful_games = [g for g in game_sessions if g.get('success', False)]
        if len(successful_games) < 2:
            return patterns

        # Analyze common characteristics of successful games
        common_features = self._find_common_features(successful_games)

        if common_features:
            pattern = {
                'type': 'success_condition',
                'success_condition': common_features,
                'success_rate': len(successful_games) / len(game_sessions),
                'sample_size': len(successful_games)
            }
            patterns.append(pattern)

        return patterns

    def _extract_failure_patterns(self, game_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns that lead to failure."""
        patterns = []

        failed_games = [g for g in game_sessions if not g.get('success', False)]
        if len(failed_games) < 2:
            return patterns

        # Analyze common characteristics of failed games
        common_features = self._find_common_features(failed_games)

        if common_features:
            pattern = {
                'type': 'failure_pattern',
                'failure_pattern': common_features,
                'failure_rate': len(failed_games) / len(game_sessions),
                'sample_size': len(failed_games)
            }
            patterns.append(pattern)

        return patterns

    def _infer_sequence_context(self, sequence: Tuple[str, ...],
                              game_sessions: List[Dict[str, Any]]) -> List[str]:
        """Infer context requirements for an action sequence."""
        contexts = []

        # Find games where this sequence appeared
        relevant_games = []
        for game in game_sessions:
            actions = game.get('action_history', [])
            if self._sequence_appears_in_actions(sequence, actions):
                relevant_games.append(game)

        if relevant_games:
            # Analyze common context features
            score_ranges = [g.get('final_score', 0) for g in relevant_games]
            action_counts = [g.get('total_actions', 0) for g in relevant_games]

            if score_ranges:
                avg_score = np.mean(score_ranges)
                if avg_score > 3.0:
                    contexts.append('high_score_context')
                elif avg_score > 1.0:
                    contexts.append('moderate_score_context')
                else:
                    contexts.append('low_score_context')

            if action_counts:
                avg_actions = np.mean(action_counts)
                if avg_actions < 50:
                    contexts.append('early_game')
                elif avg_actions < 200:
                    contexts.append('mid_game')
                else:
                    contexts.append('late_game')

        return contexts

    def _sequence_appears_in_actions(self, sequence: Tuple[str, ...], actions: List[str]) -> bool:
        """Check if sequence appears in action list."""
        seq_len = len(sequence)
        for i in range(len(actions) - seq_len + 1):
            if tuple(actions[i:i+seq_len]) == sequence:
                return True
        return False

    def _find_coordinate_clusters(self, coordinates: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        """Find clusters of coordinates using simple distance-based clustering."""
        if not coordinates:
            return []

        clusters = []
        used = set()

        for coord in coordinates:
            if coord in used:
                continue

            # Start new cluster
            cluster = [coord]
            used.add(coord)

            # Find nearby coordinates
            for other_coord in coordinates:
                if other_coord in used:
                    continue

                distance = np.sqrt((coord[0] - other_coord[0])**2 + (coord[1] - other_coord[1])**2)
                if distance <= 10.0:  # Threshold for clustering
                    cluster.append(other_coord)
                    used.add(other_coord)

            if len(cluster) >= 2:  # Minimum cluster size
                clusters.append(cluster)

        return clusters

    def _calculate_cluster_center(self, cluster: List[Tuple[int, int]]) -> Tuple[float, float]:
        """Calculate center of coordinate cluster."""
        x_coords = [coord[0] for coord in cluster]
        y_coords = [coord[1] for coord in cluster]
        return (np.mean(x_coords), np.mean(y_coords))

    def _calculate_cluster_radius(self, cluster: List[Tuple[int, int]],
                                center: Tuple[float, float]) -> float:
        """Calculate radius of coordinate cluster."""
        distances = []
        for coord in cluster:
            distance = np.sqrt((coord[0] - center[0])**2 + (coord[1] - center[1])**2)
            distances.append(distance)
        return np.mean(distances)

    def _find_common_features(self, game_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common features across game sessions."""
        if not game_sessions:
            return {}

        features = {}

        # Score characteristics
        scores = [g.get('final_score', 0) for g in game_sessions]
        if scores:
            features['score_range'] = (min(scores), max(scores))
            features['average_score'] = np.mean(scores)

        # Action characteristics
        action_counts = [g.get('total_actions', 0) for g in game_sessions]
        if action_counts:
            features['action_range'] = (min(action_counts), max(action_counts))
            features['average_actions'] = np.mean(action_counts)

        # Game type characteristics
        game_types = [g.get('game_id', '')[:4] for g in game_sessions if g.get('game_id')]
        if game_types:
            type_counts = Counter(game_types)
            features['dominant_game_types'] = [t for t, c in type_counts.most_common(3)]

        return features

class ContextSimilarityCalculator:
    """Calculates similarity between different game contexts."""

    def calculate_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity score between two contexts."""
        similarities = []

        # Game type similarity
        type1 = context1.get('game_type', '')
        type2 = context2.get('game_type', '')
        type_similarity = 1.0 if type1 == type2 else 0.3 if type1[:2] == type2[:2] else 0.0
        similarities.append(type_similarity)

        # Score target similarity
        target1 = context1.get('target_score', 0)
        target2 = context2.get('target_score', 0)
        if target1 > 0 and target2 > 0:
            score_similarity = 1.0 - abs(target1 - target2) / max(target1, target2)
            similarities.append(score_similarity)

        # Action space similarity
        actions1 = set(context1.get('action_space', []))
        actions2 = set(context2.get('action_space', []))
        if actions1 and actions2:
            action_similarity = len(actions1 & actions2) / len(actions1 | actions2)
            similarities.append(action_similarity)

        # Time constraint similarity
        max_actions1 = context1.get('max_actions', 0)
        max_actions2 = context2.get('max_actions', 0)
        if max_actions1 > 0 and max_actions2 > 0:
            time_similarity = 1.0 - abs(max_actions1 - max_actions2) / max(max_actions1, max_actions2)
            similarities.append(time_similarity)

        return np.mean(similarities) if similarities else 0.0

class KnowledgeAdaptationEngine:
    """Adapts transferable knowledge to new contexts."""

    def adapt_knowledge(self, knowledge: TransferableKnowledge,
                       target_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt knowledge to a new context."""
        adapted_content = knowledge.content.copy()

        if knowledge.knowledge_type == KnowledgeType.ACTION_SEQUENCE:
            adapted_content = self._adapt_action_sequence(knowledge.content, target_context)
        elif knowledge.knowledge_type == KnowledgeType.COORDINATE_PATTERN:
            adapted_content = self._adapt_coordinate_pattern(knowledge.content, target_context)
        elif knowledge.knowledge_type == KnowledgeType.SUCCESS_CONDITION:
            adapted_content = self._adapt_success_condition(knowledge.content, target_context)

        return adapted_content

    def _adapt_action_sequence(self, content: Dict[str, Any],
                             target_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt action sequence to target context."""
        adapted = content.copy()

        # Filter actions by available actions in target context
        available_actions = target_context.get('action_space', [])
        original_sequence = content.get('action_sequence', [])

        adapted_sequence = []
        for action in original_sequence:
            if action in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION5', 'ACTION6', 'ACTION7']:
                action_num = int(action.replace('ACTION', ''))
                if action_num in available_actions:
                    adapted_sequence.append(action)
                else:
                    # Find closest available action
                    closest_action = min(available_actions, key=lambda x: abs(x - action_num))
                    adapted_sequence.append(f'ACTION{closest_action}')
            else:
                adapted_sequence.append(action)

        adapted['action_sequence'] = adapted_sequence
        adapted['adaptation_applied'] = True

        return adapted

    def _adapt_coordinate_pattern(self, content: Dict[str, Any],
                                target_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt coordinate pattern to target context."""
        adapted = content.copy()

        coord_pattern = content.get('coordinate_pattern', {})
        if coord_pattern:
            center = coord_pattern.get('center', (32, 32))
            radius = coord_pattern.get('radius', 10)

            # Ensure coordinates are within valid range (0-63)
            adapted_center = (
                max(0, min(63, center[0])),
                max(0, min(63, center[1]))
            )

            adapted['coordinate_pattern'] = {
                'center': adapted_center,
                'radius': radius,
                'adaptation_applied': True
            }

        return adapted

    def _adapt_success_condition(self, content: Dict[str, Any],
                               target_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt success condition to target context."""
        adapted = content.copy()

        success_condition = content.get('success_condition', {})
        if success_condition:
            # Scale score targets to match new context
            target_score = target_context.get('target_score', 8.0)

            if 'average_score' in success_condition:
                original_avg = success_condition['average_score']
                scaling_factor = target_score / max(original_avg, 1.0)

                adapted['success_condition'] = success_condition.copy()
                adapted['success_condition']['average_score'] = original_avg * scaling_factor
                adapted['success_condition']['adaptation_applied'] = True

        return adapted

class MetaLearningTransferSystem:
    """Revolutionary meta-learning system for transferable knowledge."""

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize the meta-learning transfer system."""
        self.db_path = db_path

        # Core components
        self.meta_learner = MetaLearner()
        self.knowledge_base: Dict[str, TransferableKnowledge] = {}
        self.context_similarity = ContextSimilarityCalculator()
        self.adaptation_engine = KnowledgeAdaptationEngine()

        # Learning state
        self.game_sessions: List[Dict[str, Any]] = []
        self.transfer_history: List[Dict[str, Any]] = []

        # Performance tracking
        self.transfer_success_rate = 0.0
        self.knowledge_utilization = defaultdict(int)
        self.adaptation_success = defaultdict(list)

        logger.info("MetaLearningTransferSystem initialized with cross-game knowledge transfer")

    def record_game_session(self, game_id: str, game_type: str, target_score: float,
                          max_actions: int, action_space: List[int],
                          action_history: List[str], coordinate_history: List[Tuple[int, int]],
                          final_score: float, total_actions: int, success: bool):
        """Record a completed game session for learning."""
        session = {
            'game_id': game_id,
            'game_type': game_type,
            'target_score': target_score,
            'max_actions': max_actions,
            'action_space': action_space,
            'action_history': action_history,
            'coordinate_history': coordinate_history,
            'final_score': final_score,
            'total_actions': total_actions,
            'success': success,
            'timestamp': time.time()
        }

        self.game_sessions.append(session)

        # Limit session history
        if len(self.game_sessions) > 500:
            self.game_sessions = self.game_sessions[-500:]

        logger.info(f"Recorded game session: {game_id} (success: {success}, score: {final_score})")

        # Trigger learning if we have enough data
        if len(self.game_sessions) >= 5 and len(self.game_sessions) % 10 == 0:
            self._update_knowledge_base()

    def _update_knowledge_base(self):
        """Update knowledge base with new transferable patterns."""
        # Extract new knowledge from recent sessions
        recent_sessions = self.game_sessions[-20:]  # Last 20 sessions
        new_knowledge = self.meta_learner.extract_knowledge_from_games(recent_sessions)

        for knowledge in new_knowledge:
            # Check if similar knowledge already exists
            existing_id = self._find_similar_knowledge(knowledge)

            if existing_id:
                # Merge with existing knowledge
                self._merge_knowledge(existing_id, knowledge)
            else:
                # Add as new knowledge
                self.knowledge_base[knowledge.knowledge_id] = knowledge

        logger.info(f"Knowledge base updated: {len(self.knowledge_base)} total items")

    def _find_similar_knowledge(self, new_knowledge: TransferableKnowledge) -> Optional[str]:
        """Find similar existing knowledge in the knowledge base."""
        for existing_id, existing_knowledge in self.knowledge_base.items():
            if (existing_knowledge.knowledge_type == new_knowledge.knowledge_type and
                self._calculate_knowledge_similarity(existing_knowledge, new_knowledge) > 0.8):
                return existing_id
        return None

    def _calculate_knowledge_similarity(self, k1: TransferableKnowledge,
                                      k2: TransferableKnowledge) -> float:
        """Calculate similarity between two knowledge items."""
        if k1.knowledge_type != k2.knowledge_type:
            return 0.0

        # Compare content similarity (simplified)
        content1_str = json.dumps(k1.content, sort_keys=True)
        content2_str = json.dumps(k2.content, sort_keys=True)

        # Simple string similarity
        common_chars = len(set(content1_str) & set(content2_str))
        total_chars = len(set(content1_str) | set(content2_str))

        return common_chars / total_chars if total_chars > 0 else 0.0

    def _merge_knowledge(self, existing_id: str, new_knowledge: TransferableKnowledge):
        """Merge new knowledge with existing knowledge."""
        existing = self.knowledge_base[existing_id]

        # Update source games
        existing.source_games.extend(new_knowledge.source_games)
        existing.source_games = list(set(existing.source_games))  # Remove duplicates

        # Update applicable contexts
        existing.applicable_contexts.extend(new_knowledge.applicable_contexts)
        existing.applicable_contexts = list(set(existing.applicable_contexts))

        # Update success rate (weighted average)
        total_usage = existing.usage_count + new_knowledge.usage_count + 1
        existing.success_rate = (
            existing.success_rate * existing.usage_count +
            new_knowledge.success_rate * new_knowledge.usage_count +
            new_knowledge.success_rate
        ) / total_usage

        # Update confidence
        existing.confidence = max(existing.confidence, new_knowledge.confidence)

        logger.info(f"Merged knowledge: {existing_id}")

    def get_applicable_knowledge(self, current_context: Dict[str, Any]) -> List[Tuple[TransferableKnowledge, float]]:
        """Get knowledge applicable to current context with adaptation scores."""
        applicable = []

        for knowledge in self.knowledge_base.values():
            # Calculate applicability score
            applicability = self._calculate_applicability(knowledge, current_context)

            if applicability > 0.3:  # Threshold for consideration
                applicable.append((knowledge, applicability))

        # Sort by applicability score
        applicable.sort(key=lambda x: x[1], reverse=True)

        return applicable[:5]  # Top 5 most applicable

    def _calculate_applicability(self, knowledge: TransferableKnowledge,
                               context: Dict[str, Any]) -> float:
        """Calculate how applicable knowledge is to current context."""
        scores = []

        # Base success rate
        scores.append(knowledge.success_rate)

        # Confidence in knowledge
        scores.append(knowledge.confidence)

        # Generalization score
        scores.append(knowledge.generalization_score)

        # Context similarity (if we have source context info)
        if knowledge.applicable_contexts:
            context_match = any(
                ctx in context.get('game_type', '') for ctx in knowledge.applicable_contexts
            )
            scores.append(1.0 if context_match else 0.3)

        # Recency factor (prefer recently validated knowledge)
        time_since_used = time.time() - knowledge.last_used
        recency_score = 1.0 / (1.0 + time_since_used / (24 * 3600))  # Decay over days
        scores.append(recency_score)

        return np.mean(scores)

    def apply_knowledge(self, knowledge: TransferableKnowledge,
                       current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply knowledge to current context with adaptation."""
        # Adapt knowledge to current context
        adapted_content = self.adaptation_engine.adapt_knowledge(knowledge, current_context)

        # Update usage statistics
        knowledge.usage_count += 1
        knowledge.last_used = time.time()
        self.knowledge_utilization[knowledge.knowledge_id] += 1

        # Return application recommendations
        application = {
            'knowledge_id': knowledge.knowledge_id,
            'knowledge_type': knowledge.knowledge_type.value,
            'adapted_content': adapted_content,
            'confidence': knowledge.confidence,
            'expected_effectiveness': knowledge.success_rate,
            'source_games': knowledge.source_games[:3],  # Show top 3 source games
            'application_method': self._determine_application_method(knowledge, current_context)
        }

        logger.info(f"Applied knowledge: {knowledge.knowledge_id} "
                   f"(type: {knowledge.knowledge_type.value}, confidence: {knowledge.confidence:.3f})")

        return application

    def _determine_application_method(self, knowledge: TransferableKnowledge,
                                    context: Dict[str, Any]) -> str:
        """Determine how to apply the knowledge."""
        if knowledge.knowledge_type == KnowledgeType.ACTION_SEQUENCE:
            return "execute_action_sequence"
        elif knowledge.knowledge_type == KnowledgeType.COORDINATE_PATTERN:
            return "focus_coordinate_region"
        elif knowledge.knowledge_type == KnowledgeType.SUCCESS_CONDITION:
            return "optimize_for_conditions"
        elif knowledge.knowledge_type == KnowledgeType.FAILURE_PATTERN:
            return "avoid_failure_patterns"
        else:
            return "strategic_guidance"

    def record_transfer_outcome(self, knowledge_id: str, context: Dict[str, Any],
                              outcome_success: bool, performance_improvement: float):
        """Record outcome of knowledge transfer for learning."""
        if knowledge_id in self.knowledge_base:
            knowledge = self.knowledge_base[knowledge_id]

            # Update transfer success rate
            self.adaptation_success[knowledge_id].append(outcome_success)
            if len(self.adaptation_success[knowledge_id]) > 50:
                self.adaptation_success[knowledge_id] = self.adaptation_success[knowledge_id][-50:]

            knowledge.transfer_success_rate = np.mean(self.adaptation_success[knowledge_id])

            # Update confidence based on transfer results
            if outcome_success:
                knowledge.confidence = min(1.0, knowledge.confidence * 1.1)
            else:
                knowledge.confidence = max(0.1, knowledge.confidence * 0.9)

        # Record transfer history
        transfer_record = {
            'knowledge_id': knowledge_id,
            'context': context,
            'success': outcome_success,
            'improvement': performance_improvement,
            'timestamp': time.time()
        }
        self.transfer_history.append(transfer_record)

        # Limit transfer history
        if len(self.transfer_history) > 1000:
            self.transfer_history = self.transfer_history[-1000:]

    def get_transfer_recommendations(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations for knowledge transfer to current context."""
        applicable_knowledge = self.get_applicable_knowledge(current_context)

        recommendations = []
        for knowledge, applicability in applicable_knowledge:
            application = self.apply_knowledge(knowledge, current_context)
            application['applicability_score'] = applicability
            recommendations.append(application)

        return recommendations

    def get_transfer_system_status(self) -> Dict[str, Any]:
        """Get current status of the transfer system."""
        # Calculate overall transfer success rate
        all_successes = []
        for successes in self.adaptation_success.values():
            all_successes.extend(successes)

        overall_success_rate = np.mean(all_successes) if all_successes else 0.0

        return {
            "meta_learning_active": True,
            "knowledge_base_size": len(self.knowledge_base),
            "game_sessions_learned": len(self.game_sessions),
            "transfer_success_rate": overall_success_rate,
            "total_transfers": len(self.transfer_history),
            "knowledge_breakdown": {
                kt.value: sum(1 for k in self.knowledge_base.values() if k.knowledge_type == kt)
                for kt in KnowledgeType
            },
            "most_used_knowledge": [
                {"id": kid, "usage": count}
                for kid, count in sorted(self.knowledge_utilization.items(),
                                       key=lambda x: x[1], reverse=True)[:5]
            ],
            "recent_session_success_rate": np.mean([
                s['success'] for s in self.game_sessions[-20:]
            ]) if len(self.game_sessions) >= 20 else 0.0
        }

# Global instance
meta_transfer_system = MetaLearningTransferSystem()

def record_game_for_meta_learning(game_id: str, game_type: str, target_score: float,
                                 max_actions: int, action_space: List[int],
                                 action_history: List[str], coordinate_history: List[Tuple[int, int]],
                                 final_score: float, total_actions: int, success: bool):
    """Record game session for meta-learning."""
    meta_transfer_system.record_game_session(
        game_id, game_type, target_score, max_actions, action_space,
        action_history, coordinate_history, final_score, total_actions, success
    )

def get_meta_learning_recommendations(current_game_type: str, target_score: float,
                                    max_actions: int, action_space: List[int],
                                    current_score: float, actions_taken: int) -> List[Dict[str, Any]]:
    """Get meta-learning recommendations for current game context."""
    context = {
        'game_type': current_game_type,
        'target_score': target_score,
        'max_actions': max_actions,
        'action_space': action_space,
        'current_score': current_score,
        'actions_taken': actions_taken,
        'game_progress': actions_taken / max_actions
    }

    return meta_transfer_system.get_transfer_recommendations(context)

def record_meta_learning_outcome(knowledge_id: str, context: Dict[str, Any],
                                outcome_success: bool, performance_improvement: float):
    """Record outcome of applying meta-learned knowledge."""
    meta_transfer_system.record_transfer_outcome(
        knowledge_id, context, outcome_success, performance_improvement
    )

def get_meta_learning_status() -> Dict[str, Any]:
    """Get current meta-learning system status."""
    return meta_transfer_system.get_transfer_system_status()

if __name__ == "__main__":
    # Test the meta-learning transfer system
    print("=== META-LEARNING TRANSFER SYSTEM TEST ===")

    # Simulate recording several game sessions
    for i in range(15):
        game_type = random.choice(['LP85', 'FT09', 'VC33', 'AS66'])
        target_score = random.uniform(5.0, 10.0)
        final_score = random.uniform(0.0, target_score)
        success = final_score >= target_score * 0.8

        actions = [f"ACTION{random.randint(1,6)}" for _ in range(random.randint(10, 50))]
        coordinates = [(random.randint(0, 63), random.randint(0, 63)) for _ in range(len(actions)//3)]

        record_game_for_meta_learning(
            game_id=f"{game_type.lower()}-{i:04d}",
            game_type=game_type,
            target_score=target_score,
            max_actions=100,
            action_space=[1, 2, 3, 4, 6],
            action_history=actions,
            coordinate_history=coordinates,
            final_score=final_score,
            total_actions=len(actions),
            success=success
        )

    # Get recommendations for a new game
    recommendations = get_meta_learning_recommendations(
        current_game_type='LP85',
        target_score=8.0,
        max_actions=100,
        action_space=[1, 2, 3, 4, 6],
        current_score=2.0,
        actions_taken=25
    )

    print(f"Meta-Learning Recommendations:")
    for i, rec in enumerate(recommendations):
        print(f"  {i+1}. Knowledge ID: {rec['knowledge_id']}")
        print(f"     Type: {rec['knowledge_type']}")
        print(f"     Confidence: {rec['confidence']:.3f}")
        print(f"     Method: {rec['application_method']}")

    # Get system status
    status = get_meta_learning_status()
    print(f"\nMeta-Learning System Status:")
    print(f"  Knowledge Base: {status['knowledge_base_size']} items")
    print(f"  Sessions Learned: {status['game_sessions_learned']}")
    print(f"  Transfer Success Rate: {status['transfer_success_rate']:.3f}")
    print(f"  Total Transfers: {status['total_transfers']}")
    print(f"  Knowledge Breakdown: {status['knowledge_breakdown']}")