#!/usr/bin/env python3
"""
VISUAL INTELLIGENCE REVOLUTION SYSTEM
=====================================
Revolutionary computer vision engine for game frame analysis and pattern recognition.

This system analyzes game frames using advanced computer vision techniques to:
- Detect patterns, objects, and strategic opportunities
- Identify optimal action coordinates through visual analysis
- Track visual changes and evolution over time
- Provide intelligent visual-based recommendations
"""

import os
import sys

# Disable Python bytecode generation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import numpy as np
import cv2
import json
import time
import logging
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
import hashlib

logger = logging.getLogger(__name__)

class VisualPattern(Enum):
    """Types of visual patterns detected in game frames."""
    CLUSTER = "cluster"
    LINE = "line"
    CORNER = "corner"
    BOUNDARY = "boundary"
    SYMMETRY = "symmetry"
    GRADIENT = "gradient"
    ANOMALY = "anomaly"
    TARGET = "target"

@dataclass
class VisualFeature:
    """Detected visual feature in game frame."""
    pattern_type: VisualPattern
    confidence: float
    coordinates: Tuple[int, int]
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    properties: Dict[str, Any]
    strategic_value: float  # 0.0 to 1.0
    timestamp: float

@dataclass
class FrameAnalysis:
    """Complete analysis of a game frame."""
    frame_hash: str
    timestamp: float
    game_id: str
    action_number: int

    # Visual features
    detected_features: List[VisualFeature]
    dominant_colors: List[Tuple[int, int, int]]
    edge_density: float
    symmetry_score: float
    complexity_score: float

    # Strategic analysis
    recommended_coordinates: List[Tuple[Tuple[int, int], float]]  # (x,y), confidence
    action_recommendations: List[Tuple[str, float]]  # action, confidence
    visual_change_score: float  # compared to previous frame

class VisualIntelligenceEngine:
    """Revolutionary visual intelligence system for game analysis."""

    def __init__(self, db_path: str = "core_data.db", frame_history_size: int = 50):
        """Initialize the visual intelligence engine.

        Args:
            db_path: Database path for persistence
            frame_history_size: Number of frames to keep in history
        """
        self.db_path = db_path
        self.frame_history_size = frame_history_size

        # Frame analysis history
        self.frame_history: deque = deque(maxlen=frame_history_size)
        self.pattern_library: Dict[str, List[VisualFeature]] = defaultdict(list)

        # Computer vision components
        self.edge_detector = cv2.Canny
        self.contour_detector = cv2.findContours
        self.template_matchers = {}

        # Strategic analysis parameters
        self.strategic_weights = {
            "edge_proximity": 0.2,
            "cluster_density": 0.25,
            "symmetry_break": 0.15,
            "color_contrast": 0.1,
            "pattern_novelty": 0.3
        }

        # Performance tracking
        self.analysis_times = deque(maxlen=100)
        self.detection_accuracy = defaultdict(list)

        logger.info("VisualIntelligenceEngine initialized with computer vision capabilities")

    def analyze_frame(self, frame: np.ndarray, game_id: str, action_number: int) -> FrameAnalysis:
        """Perform comprehensive visual analysis of a game frame.

        Args:
            frame: Game frame as numpy array (height, width, channels)
            game_id: Current game identifier
            action_number: Current action number

        Returns:
            Complete frame analysis with detected features and recommendations
        """
        start_time = time.time()

        # Convert frame to different color spaces for analysis
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        elif len(frame.shape) == 2:
            gray = frame
            hsv = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB), cv2.COLOR_RGB2HSV)
        else:
            # Handle unexpected frame formats
            gray = np.mean(frame, axis=-1) if len(frame.shape) == 3 else frame
            hsv = np.zeros((*gray.shape, 3), dtype=np.uint8)

        # Generate frame hash for tracking
        frame_hash = hashlib.md5(frame.tobytes()).hexdigest()

        # Detect visual features
        detected_features = self._detect_visual_features(frame, gray, hsv)

        # Analyze frame properties
        dominant_colors = self._extract_dominant_colors(frame)
        edge_density = self._calculate_edge_density(gray)
        symmetry_score = self._calculate_symmetry_score(gray)
        complexity_score = self._calculate_complexity_score(gray)

        # Generate strategic recommendations
        recommended_coordinates = self._generate_coordinate_recommendations(detected_features, frame.shape)
        action_recommendations = self._generate_action_recommendations(detected_features, frame.shape)

        # Calculate visual change from previous frame
        visual_change_score = self._calculate_visual_change(frame_hash, detected_features)

        # Create frame analysis
        analysis = FrameAnalysis(
            frame_hash=frame_hash,
            timestamp=time.time(),
            game_id=game_id,
            action_number=action_number,
            detected_features=detected_features,
            dominant_colors=dominant_colors,
            edge_density=edge_density,
            symmetry_score=symmetry_score,
            complexity_score=complexity_score,
            recommended_coordinates=recommended_coordinates,
            action_recommendations=action_recommendations,
            visual_change_score=visual_change_score
        )

        # Store in history and database
        self.frame_history.append(analysis)
        self._store_analysis_to_db(analysis)

        # Update pattern library
        self._update_pattern_library(detected_features)

        # Track performance
        analysis_time = time.time() - start_time
        self.analysis_times.append(analysis_time)

        logger.info(f"Visual analysis complete: {len(detected_features)} features detected, "
                   f"{len(recommended_coordinates)} coordinates recommended, "
                   f"analysis time: {analysis_time:.3f}s")

        return analysis

    def _detect_visual_features(self, frame: np.ndarray, gray: np.ndarray, hsv: np.ndarray) -> List[VisualFeature]:
        """Detect various visual features in the frame."""
        features = []

        # Edge detection for boundaries and lines
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 10:  # Filter small noise
                # Analyze contour properties
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w // 2, y + h // 2

                # Determine pattern type based on shape
                pattern_type = self._classify_contour_pattern(contour)
                confidence = min(cv2.contourArea(contour) / 100.0, 1.0)
                strategic_value = self._calculate_strategic_value(contour, frame.shape)

                feature = VisualFeature(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    coordinates=(center_x, center_y),
                    bounding_box=(x, y, w, h),
                    properties={
                        "area": cv2.contourArea(contour),
                        "perimeter": cv2.arcLength(contour, True),
                        "aspect_ratio": w / h if h > 0 else 0
                    },
                    strategic_value=strategic_value,
                    timestamp=time.time()
                )
                features.append(feature)

        # Detect color clusters
        features.extend(self._detect_color_clusters(frame, hsv))

        # Detect symmetry patterns
        features.extend(self._detect_symmetry_patterns(gray))

        # Detect anomalies (unusual patterns)
        features.extend(self._detect_anomalies(gray, hsv))

        return features

    def _classify_contour_pattern(self, contour) -> VisualPattern:
        """Classify a contour into a visual pattern type."""
        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Classify based on number of vertices and shape properties
        vertices = len(approx)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if vertices <= 4 and area > 50:
            return VisualPattern.CORNER
        elif vertices > 8 or (perimeter > 0 and area / (perimeter ** 2) > 0.05):
            return VisualPattern.CLUSTER
        elif vertices <= 6:
            return VisualPattern.LINE
        else:
            return VisualPattern.BOUNDARY

    def _detect_color_clusters(self, frame: np.ndarray, hsv: np.ndarray) -> List[VisualFeature]:
        """Detect regions with similar colors that form clusters."""
        features = []

        # Define color ranges for cluster detection
        color_ranges = [
            ((0, 50, 50), (10, 255, 255)),    # Red
            ((25, 50, 50), (35, 255, 255)),   # Yellow
            ((45, 50, 50), (75, 255, 255)),   # Green
            ((100, 50, 50), (130, 255, 255)), # Blue
        ]

        for i, (lower, upper) in enumerate(color_ranges):
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 20:  # Significant cluster
                    x, y, w, h = cv2.boundingRect(contour)
                    center_x, center_y = x + w // 2, y + h // 2

                    feature = VisualFeature(
                        pattern_type=VisualPattern.CLUSTER,
                        confidence=min(area / 200.0, 1.0),
                        coordinates=(center_x, center_y),
                        bounding_box=(x, y, w, h),
                        properties={
                            "area": area,
                            "color_range_index": i,
                            "density": area / (w * h) if w * h > 0 else 0
                        },
                        strategic_value=self._calculate_cluster_strategic_value(area, center_x, center_y, frame.shape),
                        timestamp=time.time()
                    )
                    features.append(feature)

        return features

    def _detect_symmetry_patterns(self, gray: np.ndarray) -> List[VisualFeature]:
        """Detect symmetrical patterns in the frame."""
        features = []
        h, w = gray.shape

        # Check horizontal symmetry
        left_half = gray[:, :w//2]
        right_half = cv2.flip(gray[:, w//2:], 1)

        if left_half.shape == right_half.shape:
            symmetry_diff = np.mean(np.abs(left_half.astype(float) - right_half.astype(float)))
            symmetry_score = max(0, 1.0 - symmetry_diff / 255.0)

            if symmetry_score > 0.7:  # High symmetry
                feature = VisualFeature(
                    pattern_type=VisualPattern.SYMMETRY,
                    confidence=symmetry_score,
                    coordinates=(w // 2, h // 2),
                    bounding_box=(0, 0, w, h),
                    properties={
                        "symmetry_type": "horizontal",
                        "symmetry_score": symmetry_score
                    },
                    strategic_value=symmetry_score * 0.8,
                    timestamp=time.time()
                )
                features.append(feature)

        # Check vertical symmetry
        top_half = gray[:h//2, :]
        bottom_half = cv2.flip(gray[h//2:, :], 0)

        if top_half.shape == bottom_half.shape:
            symmetry_diff = np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float)))
            symmetry_score = max(0, 1.0 - symmetry_diff / 255.0)

            if symmetry_score > 0.7:  # High symmetry
                feature = VisualFeature(
                    pattern_type=VisualPattern.SYMMETRY,
                    confidence=symmetry_score,
                    coordinates=(w // 2, h // 2),
                    bounding_box=(0, 0, w, h),
                    properties={
                        "symmetry_type": "vertical",
                        "symmetry_score": symmetry_score
                    },
                    strategic_value=symmetry_score * 0.8,
                    timestamp=time.time()
                )
                features.append(feature)

        return features

    def _detect_anomalies(self, gray: np.ndarray, hsv: np.ndarray) -> List[VisualFeature]:
        """Detect unusual patterns or anomalies that might be strategic."""
        features = []

        # Use statistical analysis to find unusual regions
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)

        # Find regions significantly different from the mean
        anomaly_threshold = mean_intensity + 2 * std_intensity
        anomaly_mask = (gray > anomaly_threshold) | (gray < mean_intensity - 2 * std_intensity)

        # Find connected components of anomalies
        contours, _ = cv2.findContours(anomaly_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 15:  # Significant anomaly
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w // 2, y + h // 2

                # Calculate anomaly strength
                roi = gray[y:y+h, x:x+w]
                anomaly_strength = np.abs(np.mean(roi) - mean_intensity) / (std_intensity + 1e-6)

                feature = VisualFeature(
                    pattern_type=VisualPattern.ANOMALY,
                    confidence=min(anomaly_strength / 3.0, 1.0),
                    coordinates=(center_x, center_y),
                    bounding_box=(x, y, w, h),
                    properties={
                        "area": area,
                        "anomaly_strength": anomaly_strength,
                        "mean_intensity": np.mean(roi)
                    },
                    strategic_value=min(anomaly_strength / 2.0, 1.0),
                    timestamp=time.time()
                )
                features.append(feature)

        return features

    def _calculate_strategic_value(self, contour, frame_shape: Tuple[int, int]) -> float:
        """Calculate strategic value of a contour based on position and properties."""
        # Get contour properties
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        center_x, center_y = x + w // 2, y + h // 2

        # Factors affecting strategic value
        h_frame, w_frame = frame_shape[:2]

        # Distance from center (center might be more strategic)
        center_distance = np.sqrt((center_x - w_frame/2)**2 + (center_y - h_frame/2)**2)
        center_factor = 1.0 - min(center_distance / (w_frame/2), 1.0)

        # Size factor (larger features might be more important)
        size_factor = min(area / (w_frame * h_frame * 0.1), 1.0)

        # Edge proximity (features near edges might be strategic)
        edge_distance = min(center_x, center_y, w_frame - center_x, h_frame - center_y)
        edge_factor = 1.0 - min(edge_distance / (min(w_frame, h_frame) * 0.1), 1.0)

        # Combine factors
        strategic_value = (
            center_factor * self.strategic_weights["edge_proximity"] +
            size_factor * self.strategic_weights["cluster_density"] +
            edge_factor * self.strategic_weights["symmetry_break"]
        )

        return min(strategic_value, 1.0)

    def _calculate_cluster_strategic_value(self, area: float, x: int, y: int, frame_shape: Tuple[int, int]) -> float:
        """Calculate strategic value specifically for color clusters."""
        h_frame, w_frame = frame_shape[:2]

        # Position-based value
        center_x, center_y = w_frame // 2, h_frame // 2
        distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        position_value = 1.0 - min(distance_from_center / (min(w_frame, h_frame) / 2), 1.0)

        # Size-based value
        size_value = min(area / (w_frame * h_frame * 0.05), 1.0)

        return (position_value + size_value) / 2.0

    def _extract_dominant_colors(self, frame: np.ndarray) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from the frame using K-means clustering."""
        if len(frame.shape) == 2:
            # Grayscale - return intensity levels
            hist = cv2.calcHist([frame], [0], None, [8], [0, 256])
            dominant_intensities = np.argsort(hist.flatten())[-3:]
            return [(int(i * 32), int(i * 32), int(i * 32)) for i in dominant_intensities]

        # Reshape frame for K-means
        pixels = frame.reshape(-1, 3)
        pixels = pixels.astype(np.float32)

        # Apply K-means clustering
        k = 5
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Get the most frequent colors
        centers = centers.astype(np.uint8)
        label_counts = np.bincount(labels.flatten())
        dominant_indices = np.argsort(label_counts)[-3:]  # Top 3

        return [tuple(centers[i]) for i in dominant_indices]

    def _calculate_edge_density(self, gray: np.ndarray) -> float:
        """Calculate the density of edges in the frame."""
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = gray.shape[0] * gray.shape[1]
        return edge_pixels / total_pixels

    def _calculate_symmetry_score(self, gray: np.ndarray) -> float:
        """Calculate overall symmetry score of the frame."""
        h, w = gray.shape

        # Horizontal symmetry
        left = gray[:, :w//2]
        right = cv2.flip(gray[:, w//2:], 1)
        if left.shape == right.shape:
            h_symmetry = 1.0 - np.mean(np.abs(left.astype(float) - right.astype(float))) / 255.0
        else:
            h_symmetry = 0.0

        # Vertical symmetry
        top = gray[:h//2, :]
        bottom = cv2.flip(gray[h//2:, :], 0)
        if top.shape == bottom.shape:
            v_symmetry = 1.0 - np.mean(np.abs(top.astype(float) - bottom.astype(float))) / 255.0
        else:
            v_symmetry = 0.0

        return max(h_symmetry, v_symmetry)

    def _calculate_complexity_score(self, gray: np.ndarray) -> float:
        """Calculate visual complexity score based on edge density and variance."""
        # Ensure gray image is uint8 for OpenCV
        if gray.dtype != np.uint8:
            gray = np.uint8(np.clip(gray * 255 if gray.max() <= 1.0 else gray, 0, 255))

        # Edge complexity
        edges = cv2.Canny(gray, 50, 150)
        edge_complexity = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])

        # Intensity variance
        variance_complexity = np.var(gray) / (255 ** 2)

        # Combine measures
        return min((edge_complexity + variance_complexity) / 2.0, 1.0)

    def _generate_coordinate_recommendations(self, features: List[VisualFeature], frame_shape: Tuple[int, int]) -> List[Tuple[Tuple[int, int], float]]:
        """Generate coordinate recommendations based on detected visual features."""
        recommendations = []

        # Sort features by strategic value
        strategic_features = sorted(features, key=lambda f: f.strategic_value, reverse=True)

        # Generate recommendations from top strategic features
        for feature in strategic_features[:10]:  # Top 10 features
            x, y = feature.coordinates
            confidence = feature.strategic_value * feature.confidence

            # Adjust coordinates to valid game range (assuming 64x64 game grid)
            game_x = int((x / frame_shape[1]) * 64)
            game_y = int((y / frame_shape[0]) * 64)

            # Clamp to valid range
            game_x = max(0, min(63, game_x))
            game_y = max(0, min(63, game_y))

            recommendations.append(((game_x, game_y), confidence))

        # Add some exploration points based on visual analysis
        h, w = frame_shape[:2]
        exploration_points = [
            ((16, 16), 0.3),  # Upper left quadrant
            ((48, 16), 0.3),  # Upper right quadrant
            ((16, 48), 0.3),  # Lower left quadrant
            ((48, 48), 0.3),  # Lower right quadrant
        ]

        recommendations.extend(exploration_points)

        # Sort by confidence and remove duplicates
        unique_recommendations = []
        seen_coords = set()

        for coord, conf in sorted(recommendations, key=lambda x: x[1], reverse=True):
            if coord not in seen_coords:
                unique_recommendations.append((coord, conf))
                seen_coords.add(coord)

        return unique_recommendations[:8]  # Top 8 recommendations

    def _generate_action_recommendations(self, features: List[VisualFeature], frame_shape: Tuple[int, int]) -> List[Tuple[str, float]]:
        """Generate action recommendations based on visual analysis."""
        recommendations = []

        # Analyze feature distribution
        cluster_count = sum(1 for f in features if f.pattern_type == VisualPattern.CLUSTER)
        line_count = sum(1 for f in features if f.pattern_type == VisualPattern.LINE)
        corner_count = sum(1 for f in features if f.pattern_type == VisualPattern.CORNER)
        anomaly_count = sum(1 for f in features if f.pattern_type == VisualPattern.ANOMALY)

        total_features = len(features)

        if total_features == 0:
            return [("ACTION1", 0.5), ("ACTION6", 0.4)]

        # ACTION6 (coordinate-based) is good for clusters and anomalies
        action6_confidence = min((cluster_count + anomaly_count) / total_features * 1.5, 1.0)
        if action6_confidence > 0.3:
            recommendations.append(("ACTION6", action6_confidence))

        # ACTION1 is good for exploration when visual complexity is low
        complexity = self._calculate_complexity_score(np.zeros(frame_shape[:2]))  # Placeholder
        action1_confidence = max(0.3, 1.0 - complexity)
        recommendations.append(("ACTION1", action1_confidence))

        # ACTION4 is good when there are many line patterns
        if line_count > 0:
            action4_confidence = min(line_count / total_features * 2.0, 0.8)
            recommendations.append(("ACTION4", action4_confidence))

        # ACTION2 and ACTION3 for corner patterns
        if corner_count > 0:
            corner_confidence = min(corner_count / total_features * 1.5, 0.7)
            recommendations.append(("ACTION2", corner_confidence))
            recommendations.append(("ACTION3", corner_confidence))

        # Sort by confidence
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return recommendations[:5]  # Top 5 action recommendations

    def _calculate_visual_change(self, frame_hash: str, features: List[VisualFeature]) -> float:
        """Calculate visual change score compared to previous frame."""
        if len(self.frame_history) == 0:
            return 0.0

        previous_analysis = self.frame_history[-1]

        # Hash-based change detection
        hash_change = 1.0 if frame_hash != previous_analysis.frame_hash else 0.0

        # Feature-based change detection
        prev_features = previous_analysis.detected_features
        current_feature_count = len(features)
        prev_feature_count = len(prev_features)

        feature_count_change = abs(current_feature_count - prev_feature_count) / max(prev_feature_count, 1)

        # Strategic value change
        current_strategic_total = sum(f.strategic_value for f in features)
        prev_strategic_total = sum(f.strategic_value for f in prev_features)
        strategic_change = abs(current_strategic_total - prev_strategic_total) / max(prev_strategic_total, 1)

        # Combine change measures
        total_change = (hash_change * 0.3 + feature_count_change * 0.4 + strategic_change * 0.3)

        return min(total_change, 1.0)

    def _update_pattern_library(self, features: List[VisualFeature]):
        """Update pattern library with new detected features."""
        for feature in features:
            pattern_key = f"{feature.pattern_type.value}_{int(feature.strategic_value * 10)}"
            self.pattern_library[pattern_key].append(feature)

            # Limit library size
            if len(self.pattern_library[pattern_key]) > 100:
                self.pattern_library[pattern_key] = self.pattern_library[pattern_key][-100:]

    def _store_analysis_to_db(self, analysis: FrameAnalysis):
        """Store frame analysis to database for historical tracking."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_analysis (
                    frame_hash TEXT,
                    timestamp REAL,
                    game_id TEXT,
                    action_number INTEGER,
                    feature_count INTEGER,
                    edge_density REAL,
                    symmetry_score REAL,
                    complexity_score REAL,
                    visual_change_score REAL,
                    recommended_coordinates TEXT,
                    action_recommendations TEXT
                )
            """)

            # Insert analysis
            cursor.execute("""
                INSERT INTO visual_analysis VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.frame_hash,
                analysis.timestamp,
                analysis.game_id,
                analysis.action_number,
                len(analysis.detected_features),
                analysis.edge_density,
                analysis.symmetry_score,
                analysis.complexity_score,
                analysis.visual_change_score,
                json.dumps(analysis.recommended_coordinates),
                json.dumps(analysis.action_recommendations)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing visual analysis: {e}")

    def get_visual_recommendations(self, frame: np.ndarray, game_id: str, action_number: int) -> Dict[str, Any]:
        """Get visual intelligence recommendations for current frame.

        Args:
            frame: Current game frame
            game_id: Game identifier
            action_number: Current action number

        Returns:
            Dictionary with visual recommendations and analysis
        """
        # Perform frame analysis
        analysis = self.analyze_frame(frame, game_id, action_number)

        # Generate summary recommendations
        top_coordinates = analysis.recommended_coordinates[:3]  # Top 3
        top_actions = analysis.action_recommendations[:2]  # Top 2

        return {
            "visual_intelligence_active": True,
            "frame_analysis": {
                "features_detected": len(analysis.detected_features),
                "edge_density": analysis.edge_density,
                "symmetry_score": analysis.symmetry_score,
                "complexity_score": analysis.complexity_score,
                "visual_change": analysis.visual_change_score
            },
            "coordinate_recommendations": top_coordinates,
            "action_recommendations": top_actions,
            "strategic_features": [
                {
                    "type": f.pattern_type.value,
                    "confidence": f.confidence,
                    "coordinates": f.coordinates,
                    "strategic_value": f.strategic_value
                }
                for f in sorted(analysis.detected_features, key=lambda x: x.strategic_value, reverse=True)[:5]
            ],
            "performance_metrics": {
                "avg_analysis_time": np.mean(self.analysis_times) if self.analysis_times else 0.0,
                "frames_analyzed": len(self.frame_history)
            }
        }

# Global instance
visual_intelligence = VisualIntelligenceEngine()

def analyze_game_frame(frame: np.ndarray, game_id: str, action_number: int) -> Dict[str, Any]:
    """Analyze game frame and get visual intelligence recommendations."""
    return visual_intelligence.get_visual_recommendations(frame, game_id, action_number)

def get_visual_coordinate_recommendations(frame: np.ndarray) -> List[Tuple[Tuple[int, int], float]]:
    """Get coordinate recommendations based on visual analysis."""
    analysis = visual_intelligence.analyze_frame(frame, "visual_query", 0)
    return analysis.recommended_coordinates

if __name__ == "__main__":
    # Test the visual intelligence engine
    print("=== VISUAL INTELLIGENCE ENGINE TEST ===")

    # Create a test frame (64x64 RGB)
    test_frame = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)

    # Add some patterns for testing
    test_frame[10:20, 10:20] = [255, 0, 0]  # Red square
    test_frame[40:50, 40:50] = [0, 255, 0]  # Green square
    cv2.line(test_frame, (0, 30), (63, 30), (0, 0, 255), 2)  # Blue line

    # Analyze the frame
    recommendations = analyze_game_frame(test_frame, "test_game", 1)

    print(f"Visual Intelligence Results:")
    print(f"Features detected: {recommendations['frame_analysis']['features_detected']}")
    print(f"Edge density: {recommendations['frame_analysis']['edge_density']:.3f}")
    print(f"Symmetry score: {recommendations['frame_analysis']['symmetry_score']:.3f}")
    print(f"Complexity score: {recommendations['frame_analysis']['complexity_score']:.3f}")

    print(f"\nTop coordinate recommendations:")
    for i, (coord, conf) in enumerate(recommendations['coordinate_recommendations']):
        print(f"  {i+1}. {coord} (confidence: {conf:.3f})")

    print(f"\nTop action recommendations:")
    for action, conf in recommendations['action_recommendations']:
        print(f"  {action}: {conf:.3f}")