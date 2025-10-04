#!/usr/bin/env python3
"""
PREDICTIVE ACTION OUTCOME MODELING SYSTEM
==========================================
Revolutionary probabilistic system for predicting action outcomes with uncertainty estimation.

This system predicts action results before execution using:
- Bayesian uncertainty quantification
- Monte Carlo simulation for probability distributions
- Confidence intervals and risk assessment
- Multi-modal outcome prediction (score, state, side effects)
- Adaptive learning from prediction errors
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
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import threading
import statistics

logger = logging.getLogger(__name__)

class OutcomeType(Enum):
    """Types of outcomes to predict."""
    SCORE_CHANGE = "score_change"
    STATE_TRANSITION = "state_transition"
    COORDINATE_EFFECT = "coordinate_effect"
    SIDE_EFFECTS = "side_effects"
    SUCCESS_PROBABILITY = "success_probability"

class UncertaintyMethod(Enum):
    """Methods for uncertainty estimation."""
    BAYESIAN = "bayesian"
    MONTE_CARLO = "monte_carlo"
    ENSEMBLE = "ensemble"
    BOOTSTRAP = "bootstrap"

@dataclass
class PredictionContext:
    """Context information for making predictions."""
    current_score: float
    action_number: int
    available_actions: List[int]
    recent_actions: List[str]
    coordinate_history: List[Tuple[int, int]]
    visual_features: List[float]
    game_progress: float  # 0.0 to 1.0

    def to_feature_vector(self) -> np.ndarray:
        """Convert context to feature vector for modeling."""
        features = [
            self.current_score,
            self.action_number,
            len(self.available_actions),
            self.game_progress
        ]

        # Action availability encoding
        action_encoding = [0.0] * 7
        for action in self.available_actions:
            if 1 <= action <= 7:
                action_encoding[action - 1] = 1.0
        features.extend(action_encoding)

        # Recent action pattern (last 5 actions)
        action_pattern = [0.0] * 35  # 7 actions * 5 positions
        for i, action in enumerate(self.recent_actions[-5:]):
            if action.startswith('ACTION'):
                action_idx = int(action.replace('ACTION', '')) - 1
                if 0 <= action_idx < 7:
                    action_pattern[i * 7 + action_idx] = 1.0
        features.extend(action_pattern)

        # Coordinate features (normalized)
        if self.coordinate_history:
            recent_coords = self.coordinate_history[-3:]  # Last 3 coordinates
            coord_features = []
            for coord in recent_coords:
                coord_features.extend([coord[0] / 64.0, coord[1] / 64.0])
            # Pad to fixed size (3 coordinates = 6 features)
            while len(coord_features) < 6:
                coord_features.append(0.0)
            features.extend(coord_features[:6])
        else:
            features.extend([0.0] * 6)

        # Visual features (top 10, normalized)
        visual_subset = self.visual_features[:10] if self.visual_features else []
        while len(visual_subset) < 10:
            visual_subset.append(0.0)
        features.extend(visual_subset)

        return np.array(features, dtype=np.float32)

@dataclass
class OutcomePrediction:
    """Prediction for a specific outcome type."""
    outcome_type: OutcomeType
    predicted_value: float
    confidence_interval: Tuple[float, float]  # (lower, upper)
    uncertainty: float  # Standard deviation
    probability_mass: Dict[str, float]  # For discrete outcomes
    confidence: float  # Overall confidence in prediction
    method_used: UncertaintyMethod

@dataclass
class ActionPrediction:
    """Complete prediction for an action."""
    action: str
    coordinates: Optional[Tuple[int, int]]
    context: PredictionContext
    predictions: Dict[OutcomeType, OutcomePrediction]
    overall_expected_value: float
    risk_assessment: Dict[str, float]
    timestamp: float

class BayesianPredictor:
    """Bayesian predictor with uncertainty quantification."""

    def __init__(self, feature_size: int):
        """Initialize Bayesian predictor."""
        self.feature_size = feature_size
        self.prior_mean = 0.0
        self.prior_variance = 1.0

        # Model parameters (Bayesian linear regression)
        self.weights_mean = np.zeros(feature_size)
        self.weights_covariance = np.eye(feature_size) * self.prior_variance
        self.noise_precision = 1.0

        # Training data
        self.observations = []
        self.targets = []

    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Make prediction with uncertainty.

        Returns:
            Tuple of (mean_prediction, uncertainty)
        """
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        # Predictive mean
        mean = np.dot(features, self.weights_mean)

        # Predictive variance (including model uncertainty)
        model_variance = np.dot(features, np.dot(self.weights_covariance, features.T))
        noise_variance = 1.0 / self.noise_precision
        total_variance = model_variance + noise_variance

        return float(mean[0]), float(np.sqrt(total_variance))

    def update(self, features: np.ndarray, target: float):
        """Update model with new observation (Bayesian update)."""
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        # Store observation
        self.observations.append(features.flatten())
        self.targets.append(target)

        # Bayesian linear regression update
        precision_matrix = np.linalg.inv(self.weights_covariance)
        precision_matrix += self.noise_precision * np.dot(features.T, features)

        self.weights_covariance = np.linalg.inv(precision_matrix)

        weighted_target = self.noise_precision * target * features.flatten()
        weighted_prior = np.dot(np.linalg.inv(np.eye(self.feature_size) * self.prior_variance),
                               self.weights_mean)

        self.weights_mean = np.dot(self.weights_covariance, weighted_target + weighted_prior)

class MonteCarloPredictor:
    """Monte Carlo simulation for outcome prediction."""

    def __init__(self, num_simulations: int = 1000):
        """Initialize Monte Carlo predictor."""
        self.num_simulations = num_simulations
        self.historical_outcomes = defaultdict(list)

    def predict(self, action: str, context: PredictionContext) -> Dict[str, Tuple[float, float, List[float]]]:
        """Predict outcomes using Monte Carlo simulation.

        Returns:
            Dict mapping outcome types to (mean, std, samples)
        """
        predictions = {}

        # Get relevant historical data
        context_key = self._get_context_key(action, context)
        historical_data = self.historical_outcomes.get(context_key, [])

        if len(historical_data) < 5:
            # Use generic historical data if specific context lacks data
            all_data = []
            for key, data in self.historical_outcomes.items():
                if action in key:
                    all_data.extend(data)
            historical_data = all_data if all_data else [0.0]

        # Monte Carlo simulation
        samples = []
        for _ in range(self.num_simulations):
            # Sample from historical distribution with noise
            if historical_data:
                base_outcome = random.choice(historical_data)
                noise = random.gauss(0, 0.1)  # Add uncertainty
                sample = base_outcome + noise
            else:
                # Prior distribution when no data
                sample = random.gauss(0.0, 0.2)

            samples.append(sample)

        # Calculate statistics
        mean_outcome = np.mean(samples)
        std_outcome = np.std(samples)

        predictions['score_change'] = (mean_outcome, std_outcome, samples)

        return predictions

    def update(self, action: str, context: PredictionContext, outcome: float):
        """Update model with observed outcome."""
        context_key = self._get_context_key(action, context)
        self.historical_outcomes[context_key].append(outcome)

        # Limit history size
        if len(self.historical_outcomes[context_key]) > 100:
            self.historical_outcomes[context_key] = self.historical_outcomes[context_key][-100:]

    def _get_context_key(self, action: str, context: PredictionContext) -> str:
        """Generate context key for grouping similar situations."""
        score_bucket = int(context.current_score * 4)  # 0.25 buckets
        progress_bucket = int(context.game_progress * 4)
        action_count_bucket = int(context.action_number / 10)

        return f"{action}_{score_bucket}_{progress_bucket}_{action_count_bucket}"

class EnsemblePredictor:
    """Ensemble of predictors for robust predictions."""

    def __init__(self, feature_size: int):
        """Initialize ensemble predictor."""
        self.predictors = [
            BayesianPredictor(feature_size),
            BayesianPredictor(feature_size),
            BayesianPredictor(feature_size)
        ]
        self.predictor_weights = [1.0] * len(self.predictors)

    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Make ensemble prediction."""
        predictions = []
        uncertainties = []

        for predictor in self.predictors:
            pred, unc = predictor.predict(features)
            predictions.append(pred)
            uncertainties.append(unc)

        # Weighted average
        total_weight = sum(self.predictor_weights)
        weighted_pred = sum(p * w for p, w in zip(predictions, self.predictor_weights)) / total_weight

        # Ensemble uncertainty (includes disagreement)
        prediction_variance = np.var(predictions)
        average_uncertainty = np.mean(uncertainties)
        total_uncertainty = np.sqrt(prediction_variance + average_uncertainty ** 2)

        return weighted_pred, total_uncertainty

    def update(self, features: np.ndarray, target: float):
        """Update all predictors in ensemble."""
        # Calculate individual errors for weight adjustment
        predictions = []
        for i, predictor in enumerate(self.predictors):
            pred, _ = predictor.predict(features)
            predictions.append(pred)
            predictor.update(features, target)

        # Update predictor weights based on performance
        errors = [abs(pred - target) for pred in predictions]
        if max(errors) > 0:
            # Inverse error weighting
            self.predictor_weights = [1.0 / (error + 1e-6) for error in errors]

class PredictiveOutcomeModeler:
    """Revolutionary predictive action outcome modeling system."""

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize the predictive outcome modeling system."""
        self.db_path = db_path

        # Feature configuration
        self.feature_size = 62  # Based on PredictionContext.to_feature_vector() (4+7+35+6+10=62)

        # Prediction models
        self.bayesian_predictors = {
            OutcomeType.SCORE_CHANGE: BayesianPredictor(self.feature_size),
            OutcomeType.SUCCESS_PROBABILITY: BayesianPredictor(self.feature_size)
        }

        self.monte_carlo_predictor = MonteCarloPredictor(num_simulations=1000)
        self.ensemble_predictor = EnsemblePredictor(self.feature_size)

        # Prediction history
        self.prediction_history: List[ActionPrediction] = []
        self.prediction_errors = defaultdict(deque)

        # Model performance tracking
        self.accuracy_metrics = defaultdict(deque)
        self.calibration_data = defaultdict(list)

        # Configuration
        self.uncertainty_threshold = 0.5
        self.confidence_threshold = 0.7
        self.prediction_horizon = 5  # Actions to look ahead

        logger.info("PredictiveOutcomeModeler initialized with Bayesian uncertainty quantification")

    def predict_action_outcomes(self, action: str, coordinates: Optional[Tuple[int, int]],
                                context: PredictionContext) -> ActionPrediction:
        """Predict comprehensive outcomes for a proposed action."""
        start_time = time.time()

        # Convert context to features
        features = context.to_feature_vector()

        # Generate predictions for different outcome types
        predictions = {}

        # Score change prediction (Bayesian)
        score_pred, score_unc = self.bayesian_predictors[OutcomeType.SCORE_CHANGE].predict(features)
        score_ci = (score_pred - 1.96 * score_unc, score_pred + 1.96 * score_unc)  # 95% CI

        predictions[OutcomeType.SCORE_CHANGE] = OutcomePrediction(
            outcome_type=OutcomeType.SCORE_CHANGE,
            predicted_value=score_pred,
            confidence_interval=score_ci,
            uncertainty=score_unc,
            probability_mass={},
            confidence=self._calculate_confidence(score_unc),
            method_used=UncertaintyMethod.BAYESIAN
        )

        # Success probability prediction
        success_pred, success_unc = self.bayesian_predictors[OutcomeType.SUCCESS_PROBABILITY].predict(features)
        success_pred = max(0.0, min(1.0, success_pred))  # Clamp to [0,1]
        success_ci = (max(0.0, success_pred - 1.96 * success_unc),
                     min(1.0, success_pred + 1.96 * success_unc))

        predictions[OutcomeType.SUCCESS_PROBABILITY] = OutcomePrediction(
            outcome_type=OutcomeType.SUCCESS_PROBABILITY,
            predicted_value=success_pred,
            confidence_interval=success_ci,
            uncertainty=success_unc,
            probability_mass={
                "success": success_pred,
                "failure": 1.0 - success_pred
            },
            confidence=self._calculate_confidence(success_unc),
            method_used=UncertaintyMethod.BAYESIAN
        )

        # Monte Carlo predictions for additional outcomes
        mc_predictions = self.monte_carlo_predictor.predict(action, context)
        if 'score_change' in mc_predictions:
            mc_mean, mc_std, mc_samples = mc_predictions['score_change']

            # Create distribution-based prediction
            predictions[OutcomeType.STATE_TRANSITION] = OutcomePrediction(
                outcome_type=OutcomeType.STATE_TRANSITION,
                predicted_value=mc_mean,
                confidence_interval=(np.percentile(mc_samples, 2.5), np.percentile(mc_samples, 97.5)),
                uncertainty=mc_std,
                probability_mass=self._calculate_outcome_probabilities(mc_samples),
                confidence=self._calculate_confidence(mc_std),
                method_used=UncertaintyMethod.MONTE_CARLO
            )

        # Ensemble prediction for robustness
        ensemble_pred, ensemble_unc = self.ensemble_predictor.predict(features)
        predictions[OutcomeType.COORDINATE_EFFECT] = OutcomePrediction(
            outcome_type=OutcomeType.COORDINATE_EFFECT,
            predicted_value=ensemble_pred,
            confidence_interval=(ensemble_pred - 1.96 * ensemble_unc, ensemble_pred + 1.96 * ensemble_unc),
            uncertainty=ensemble_unc,
            probability_mass={},
            confidence=self._calculate_confidence(ensemble_unc),
            method_used=UncertaintyMethod.ENSEMBLE
        )

        # Calculate overall expected value
        overall_ev = self._calculate_expected_value(predictions, context)

        # Risk assessment
        risk_assessment = self._assess_risk(predictions, context)

        # Create action prediction
        action_prediction = ActionPrediction(
            action=action,
            coordinates=coordinates,
            context=context,
            predictions=predictions,
            overall_expected_value=overall_ev,
            risk_assessment=risk_assessment,
            timestamp=time.time()
        )

        # Store prediction for later evaluation
        self.prediction_history.append(action_prediction)

        # Limit history size
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]

        logger.info(f"Predicted outcomes for {action}: EV={overall_ev:.3f}, "
                   f"Score Δ={score_pred:.3f}±{score_unc:.3f}, "
                   f"Success P={success_pred:.3f}")

        return action_prediction

    def _calculate_confidence(self, uncertainty: float) -> float:
        """Calculate confidence score from uncertainty."""
        # Higher uncertainty -> lower confidence
        confidence = 1.0 / (1.0 + uncertainty)
        return min(max(confidence, 0.0), 1.0)

    def _calculate_outcome_probabilities(self, samples: List[float]) -> Dict[str, float]:
        """Calculate probability mass for discrete outcomes."""
        total_samples = len(samples)
        if total_samples == 0:
            return {}

        positive_samples = sum(1 for s in samples if s > 0)
        negative_samples = sum(1 for s in samples if s < 0)
        neutral_samples = total_samples - positive_samples - negative_samples

        return {
            "positive": positive_samples / total_samples,
            "negative": negative_samples / total_samples,
            "neutral": neutral_samples / total_samples
        }

    def _calculate_expected_value(self, predictions: Dict[OutcomeType, OutcomePrediction],
                                context: PredictionContext) -> float:
        """Calculate overall expected value of the action."""
        score_change = predictions.get(OutcomeType.SCORE_CHANGE)
        success_prob = predictions.get(OutcomeType.SUCCESS_PROBABILITY)

        if not score_change or not success_prob:
            return 0.0

        # Expected value considering success probability
        ev = score_change.predicted_value * success_prob.predicted_value

        # Adjust for uncertainty (prefer more certain predictions)
        uncertainty_penalty = (score_change.uncertainty + success_prob.uncertainty) / 2
        ev *= (1.0 - min(uncertainty_penalty, 0.5))

        # Time factor (earlier actions have more potential)
        time_factor = (1.0 - context.game_progress) * 0.1 + 0.9
        ev *= time_factor

        return ev

    def _assess_risk(self, predictions: Dict[OutcomeType, OutcomePrediction],
                    context: PredictionContext) -> Dict[str, float]:
        """Assess risk factors for the predicted action."""
        risk_factors = {}

        # Uncertainty risk
        total_uncertainty = sum(pred.uncertainty for pred in predictions.values()) / len(predictions)
        risk_factors["uncertainty_risk"] = min(total_uncertainty, 1.0)

        # Downside risk (probability of negative outcomes)
        score_pred = predictions.get(OutcomeType.SCORE_CHANGE)
        if score_pred:
            lower_ci = score_pred.confidence_interval[0]
            risk_factors["downside_risk"] = max(0.0, -lower_ci) if lower_ci < 0 else 0.0

        # Opportunity cost (missing better alternatives)
        current_ev = self._calculate_expected_value(predictions, context)
        baseline_ev = 0.1  # Expected value of conservative action
        risk_factors["opportunity_cost"] = max(0.0, baseline_ev - current_ev)

        # Time pressure risk
        risk_factors["time_pressure"] = context.game_progress

        # Overall risk score
        risk_factors["overall_risk"] = np.mean(list(risk_factors.values()))

        return risk_factors

    def update_predictions_with_outcome(self, action: str, coordinates: Optional[Tuple[int, int]],
                                       context: PredictionContext, actual_score_change: float,
                                       actual_success: bool):
        """Update predictive models with observed outcomes."""
        features = context.to_feature_vector()

        # Update Bayesian predictors
        self.bayesian_predictors[OutcomeType.SCORE_CHANGE].update(features, actual_score_change)
        self.bayesian_predictors[OutcomeType.SUCCESS_PROBABILITY].update(features, 1.0 if actual_success else 0.0)

        # Update Monte Carlo predictor
        self.monte_carlo_predictor.update(action, context, actual_score_change)

        # Update ensemble predictor
        self.ensemble_predictor.update(features, actual_score_change)

        # Track prediction accuracy
        self._track_prediction_accuracy(action, context, actual_score_change, actual_success)

        # Store outcome for analysis
        self._store_prediction_outcome(action, coordinates, context, actual_score_change, actual_success)

    def _track_prediction_accuracy(self, action: str, context: PredictionContext,
                                  actual_score_change: float, actual_success: bool):
        """Track accuracy of predictions for model evaluation."""
        # Find corresponding prediction
        recent_predictions = [p for p in self.prediction_history[-10:] if p.action == action]

        if recent_predictions:
            prediction = recent_predictions[-1]  # Most recent matching prediction

            # Score change accuracy
            if OutcomeType.SCORE_CHANGE in prediction.predictions:
                pred_score = prediction.predictions[OutcomeType.SCORE_CHANGE]
                score_error = abs(pred_score.predicted_value - actual_score_change)
                self.prediction_errors[OutcomeType.SCORE_CHANGE].append(score_error)

                # Check if actual outcome falls within confidence interval
                ci_lower, ci_upper = pred_score.confidence_interval
                in_ci = ci_lower <= actual_score_change <= ci_upper
                self.calibration_data[OutcomeType.SCORE_CHANGE].append(in_ci)

            # Success probability accuracy
            if OutcomeType.SUCCESS_PROBABILITY in prediction.predictions:
                pred_success = prediction.predictions[OutcomeType.SUCCESS_PROBABILITY]
                success_error = abs(pred_success.predicted_value - (1.0 if actual_success else 0.0))
                self.prediction_errors[OutcomeType.SUCCESS_PROBABILITY].append(success_error)

            # Limit error history
            for error_type in self.prediction_errors:
                if len(self.prediction_errors[error_type]) > 500:
                    self.prediction_errors[error_type] = deque(list(self.prediction_errors[error_type])[-500:])

    def get_prediction_performance(self) -> Dict[str, Any]:
        """Get current prediction performance metrics."""
        performance = {}

        for outcome_type in [OutcomeType.SCORE_CHANGE, OutcomeType.SUCCESS_PROBABILITY]:
            errors = list(self.prediction_errors[outcome_type])
            calibration = self.calibration_data.get(outcome_type, [])

            if errors:
                performance[outcome_type.value] = {
                    "mean_absolute_error": np.mean(errors),
                    "rmse": np.sqrt(np.mean([e**2 for e in errors])),
                    "num_predictions": len(errors),
                    "calibration_rate": np.mean(calibration) if calibration else 0.0
                }

        # Overall metrics
        all_errors = []
        for error_list in self.prediction_errors.values():
            all_errors.extend(error_list)

        performance["overall"] = {
            "total_predictions": len(self.prediction_history),
            "mean_prediction_error": np.mean(all_errors) if all_errors else 0.0,
            "prediction_confidence": np.mean([
                np.mean([pred.confidence for pred in p.predictions.values()])
                for p in self.prediction_history[-100:]
            ]) if self.prediction_history else 0.0
        }

        return performance

    def compare_action_predictions(self, actions: List[str], context: PredictionContext) -> Dict[str, Any]:
        """Compare predictions for multiple actions to choose the best."""
        predictions = {}
        rankings = {}

        for action in actions:
            pred = self.predict_action_outcomes(action, None, context)
            predictions[action] = pred

            # Calculate ranking score
            ev = pred.overall_expected_value
            confidence = np.mean([p.confidence for p in pred.predictions.values()])
            risk = pred.risk_assessment["overall_risk"]

            ranking_score = ev * confidence * (1.0 - risk)
            rankings[action] = ranking_score

        # Sort by ranking score
        best_action = max(rankings.keys(), key=lambda a: rankings[a])

        return {
            "predictions": {action: pred.overall_expected_value for action, pred in predictions.items()},
            "rankings": rankings,
            "recommended_action": best_action,
            "confidence_analysis": {
                action: np.mean([p.confidence for p in pred.predictions.values()])
                for action, pred in predictions.items()
            },
            "risk_analysis": {
                action: pred.risk_assessment["overall_risk"]
                for action, pred in predictions.items()
            }
        }

    def _store_prediction_outcome(self, action: str, coordinates: Optional[Tuple[int, int]],
                                 context: PredictionContext, actual_score_change: float,
                                 actual_success: bool):
        """Store prediction and outcome for analysis."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_outcomes (
                    timestamp REAL,
                    action TEXT,
                    coordinates TEXT,
                    current_score REAL,
                    action_number INTEGER,
                    game_progress REAL,
                    actual_score_change REAL,
                    actual_success INTEGER
                )
            """)

            # Insert outcome
            cursor.execute("""
                INSERT INTO prediction_outcomes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                action,
                json.dumps(coordinates) if coordinates else None,
                context.current_score,
                context.action_number,
                context.game_progress,
                actual_score_change,
                1 if actual_success else 0
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing prediction outcome: {e}")

# Global instance
outcome_modeler = PredictiveOutcomeModeler()

def predict_action_outcome(action: str, coordinates: Optional[Tuple[int, int]],
                          current_score: float, action_number: int,
                          available_actions: List[int], recent_actions: List[str],
                          coordinate_history: List[Tuple[int, int]] = None,
                          visual_features: List[float] = None,
                          max_actions: int = 1500) -> Dict[str, Any]:
    """Predict outcomes for a proposed action."""
    # Create prediction context
    context = PredictionContext(
        current_score=current_score,
        action_number=action_number,
        available_actions=available_actions,
        recent_actions=recent_actions,
        coordinate_history=coordinate_history or [],
        visual_features=visual_features or [],
        game_progress=action_number / max_actions
    )

    # Get prediction
    prediction = outcome_modeler.predict_action_outcomes(action, coordinates, context)

    # Format results
    return {
        "action": action,
        "coordinates": coordinates,
        "expected_value": prediction.overall_expected_value,
        "predictions": {
            outcome_type.value: {
                "value": pred.predicted_value,
                "uncertainty": pred.uncertainty,
                "confidence_interval": pred.confidence_interval,
                "confidence": pred.confidence
            }
            for outcome_type, pred in prediction.predictions.items()
        },
        "risk_assessment": prediction.risk_assessment,
        "recommendation_strength": prediction.overall_expected_value > 0.1
    }

def record_prediction_outcome(action: str, coordinates: Optional[Tuple[int, int]],
                             current_score: float, action_number: int,
                             available_actions: List[int], recent_actions: List[str],
                             actual_score_change: float, actual_success: bool,
                             coordinate_history: List[Tuple[int, int]] = None,
                             visual_features: List[float] = None,
                             max_actions: int = 1500):
    """Record actual outcome for updating predictive models."""
    # Create context
    context = PredictionContext(
        current_score=current_score,
        action_number=action_number,
        available_actions=available_actions,
        recent_actions=recent_actions,
        coordinate_history=coordinate_history or [],
        visual_features=visual_features or [],
        game_progress=action_number / max_actions
    )

    # Update models
    outcome_modeler.update_predictions_with_outcome(
        action, coordinates, context, actual_score_change, actual_success
    )

def get_prediction_performance() -> Dict[str, Any]:
    """Get current prediction performance metrics."""
    return outcome_modeler.get_prediction_performance()

def compare_action_predictions(actions: List[str], current_score: float, action_number: int,
                             available_actions: List[int], recent_actions: List[str],
                             coordinate_history: List[Tuple[int, int]] = None,
                             visual_features: List[float] = None,
                             max_actions: int = 1500) -> Dict[str, Any]:
    """Compare predictions for multiple actions."""
    context = PredictionContext(
        current_score=current_score,
        action_number=action_number,
        available_actions=available_actions,
        recent_actions=recent_actions,
        coordinate_history=coordinate_history or [],
        visual_features=visual_features or [],
        game_progress=action_number / max_actions
    )

    return outcome_modeler.compare_action_predictions(actions, context)

if __name__ == "__main__":
    # Test the predictive outcome modeling system
    print("=== PREDICTIVE OUTCOME MODELING SYSTEM TEST ===")

    # Simulate game context
    score = 2.5
    action_num = 25
    available_actions = [1, 2, 3, 4, 6]
    recent_actions = ["ACTION1", "ACTION6", "ACTION2", "ACTION1", "ACTION4"]

    # Test single action prediction
    prediction = predict_action_outcome(
        "ACTION6", (32, 32), score, action_num, available_actions, recent_actions
    )

    print(f"Action Prediction for ACTION6:")
    print(f"  Expected Value: {prediction['expected_value']:.3f}")
    print(f"  Recommendation: {'Strong' if prediction['recommendation_strength'] else 'Weak'}")

    for outcome_type, pred_data in prediction['predictions'].items():
        print(f"  {outcome_type}:")
        print(f"    Value: {pred_data['value']:.3f} ± {pred_data['uncertainty']:.3f}")
        print(f"    Confidence: {pred_data['confidence']:.3f}")

    print(f"  Risk Assessment:")
    for risk_type, risk_value in prediction['risk_assessment'].items():
        print(f"    {risk_type}: {risk_value:.3f}")

    # Test action comparison
    print(f"\nAction Comparison:")
    comparison = compare_action_predictions(
        ["ACTION1", "ACTION2", "ACTION6"], score, action_num, available_actions, recent_actions
    )

    print(f"  Recommended: {comparison['recommended_action']}")
    print(f"  Rankings:")
    for action, ranking in comparison['rankings'].items():
        print(f"    {action}: {ranking:.3f}")

    # Simulate learning from outcome
    record_prediction_outcome(
        "ACTION6", (32, 32), score, action_num, available_actions, recent_actions,
        actual_score_change=0.2, actual_success=True
    )

    # Check performance
    performance = get_prediction_performance()
    print(f"\nPrediction Performance:")
    for metric_type, metrics in performance.items():
        if isinstance(metrics, dict):
            print(f"  {metric_type}:")
            for metric_name, value in metrics.items():
                print(f"    {metric_name}: {value:.3f}")
        else:
            print(f"  {metric_type}: {metrics:.3f}")