import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST

import logging
import json
import hashlib
from typing import Iterable, List, Optional

from database_interface import DatabaseInterface
from event_bus import Event, EventType
from plugin_interfaces import ModeAwarePlugin

logger = logging.getLogger(__name__)


class LessonExtractionPlugin(ModeAwarePlugin):
    """Emit-only lesson extraction and contradiction logging.

    Idempotent, mode-aware, and intentionally conservative: captures signals
    from gap detection without mutating gameplay. Writes are limited to LIVE
    mode via ModeAwarePlugin.
    """

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [
            EventType.COMPREHENSION_GAP_DETECTED,
            EventType.RUN_FINALIZED,
            EventType.LESSON_INTERPRETATION_READY,
        ]

    def handle(self, event: Event) -> None:
        try:
            gap_type = event.payload.get("gap_type")
            game_id = event.payload.get("game_id")
            attempt_id = event.payload.get("attempt_id")
            level = event.payload.get("level")
            resonance_tags = event.payload.get("resonance_tags")
            contradictions = event.payload.get("contradictions")
            consensus = event.payload.get("consensus")
            score_delta = event.payload.get("score_delta")
            high_consensus_low_score = None
            if isinstance(consensus, (int, float)) and isinstance(score_delta, (int, float)):
                if consensus >= 0.7 and score_delta <= 0:
                    high_consensus_low_score = True
            if event.event_type == EventType.COMPREHENSION_GAP_DETECTED:
                logger.debug(
                    "[PLUGIN:LESSON] Gap detected (type=%s) game=%s attempt=%s",
                    gap_type,
                    game_id,
                    attempt_id,
                )
                if high_consensus_low_score:
                    resonance_tags = json.dumps(
                        {
                            "gap_detected": resonance_tags,
                            "high_consensus_low_score": high_consensus_low_score,
                        }
                    )
                if self.db and attempt_id:
                    try:
                        self.db.execute_query(
                            """
                            INSERT INTO lesson_interpretations (
                              attempt_id, game_id, level, interpretation,
                              explains_examples, fails_examples, confidence,
                              contradictions, coverage_notes, resonance_tags,
                              source_mode, reasoning_tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                attempt_id,
                                game_id,
                                level,
                                gap_type or "unknown_gap",
                                0,
                                1,
                                0.3,
                                str(contradictions) if contradictions is not None else None,
                                None,
                                resonance_tags if isinstance(resonance_tags, str) else None,
                                event.payload.get("mode"),
                                event.payload.get("reasoning_tags"),
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:LESSON] DB insert skipped: {db_exc}")
            elif event.event_type == EventType.LESSON_INTERPRETATION_READY:
                interpretation = event.payload.get("interpretation") or "lesson_stub"
                score_delta = event.payload.get("score_delta")
                resonance_tags = event.payload.get("resonance_tags")
                reasoning_tags = event.payload.get("reasoning")
                structure_tag = event.payload.get("structure_tag") or event.payload.get("structure_tags")
                pctl_stage = event.payload.get("pctl_stage") or event.payload.get("pctl_stage_tag")
                explains_examples = 1 if isinstance(score_delta, (int, float)) and score_delta > 0 else 0
                fails_examples = 1 if isinstance(score_delta, (int, float)) and score_delta < 0 else 0
                confidence = float(abs(score_delta)) if isinstance(score_delta, (int, float)) else 0.25
                if structure_tag or pctl_stage:
                    resonance_tags = json.dumps(
                        {
                            "lesson_stub": resonance_tags,
                            "structure_tag": structure_tag,
                            "pctl_stage": pctl_stage,
                        }
                    )
                if self.db and attempt_id:
                    try:
                        self.db.execute_query(
                            """
                            INSERT INTO lesson_interpretations (
                              attempt_id, game_id, level, interpretation,
                              explains_examples, fails_examples, confidence,
                              contradictions, coverage_notes, resonance_tags,
                              source_mode, reasoning_tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                attempt_id,
                                game_id,
                                level,
                                interpretation,
                                explains_examples,
                                fails_examples,
                                confidence,
                                str(event.payload.get("contradictions")) if event.payload.get("contradictions") is not None else None,
                                None,
                                resonance_tags if isinstance(resonance_tags, str) else str(resonance_tags) if resonance_tags is not None else None,
                                event.payload.get("mode"),
                                reasoning_tags,
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:LESSON] DB lesson_stub insert skipped: {db_exc}")
            elif event.event_type == EventType.RUN_FINALIZED:
                logger.debug(
                    "[PLUGIN:LESSON] Run finalized for game=%s attempt=%s score=%s",
                    game_id,
                    attempt_id,
                    event.payload.get("score"),
                )
                structure_tag = event.payload.get("structure_tag") or event.payload.get("structure_tags")
                pctl_stage = event.payload.get("pctl_stage") or event.payload.get("pctl_stage_tag")
                final_resonance = resonance_tags
                if structure_tag or pctl_stage:
                    final_resonance = json.dumps(
                        {
                            "run_summary": resonance_tags,
                            "structure_tag": structure_tag,
                            "pctl_stage": pctl_stage,
                        }
                    )
                if self.db and attempt_id:
                    try:
                        self.db.execute_query(
                            """
                            INSERT INTO lesson_interpretations (
                              attempt_id, game_id, level, interpretation,
                              explains_examples, fails_examples, confidence,
                              contradictions, coverage_notes, resonance_tags,
                              source_mode, reasoning_tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                attempt_id,
                                game_id,
                                level,
                                "run_summary",
                                1 if event.payload.get("win") else 0,
                                0 if event.payload.get("win") else 1,
                                float(event.payload.get("score") or 0.0),
                                None,
                                "run_finalized",
                                final_resonance if isinstance(final_resonance, str) else str(final_resonance) if final_resonance is not None else None,
                                event.payload.get("mode"),
                                event.payload.get("reasoning_tags"),
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:LESSON] DB run_summary insert skipped: {db_exc}")
        except Exception as exc:
            raise exc


class PriorsPlugin(ModeAwarePlugin):
    """Weak priors tracker for attention/proposals; no mutations."""

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [EventType.ACTION_PROPOSALS, EventType.ACTION_CHOSEN]

    def handle(self, event: Event) -> None:
        try:
            if event.event_type == EventType.ACTION_PROPOSALS:
                priors = event.payload.get("priors") or {}
                logger.debug(
                    "[PLUGIN:PRIORS] proposals=%s priors=%s",
                    event.payload.get("proposal_count"),
                    list(priors.keys()),
                )
                if self.db and event.payload.get("attempt_id"):
                    try:
                        self.db.execute_query(
                            """
                            INSERT INTO action_proposals_log (
                              attempt_id, step_idx, proposed_actions, chosen_action,
                              chosen_reason, role_compliance, theory_validation_state,
                              resonance_tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                event.payload.get("attempt_id"),
                                event.payload.get("step_idx", 0),
                                None,
                                None,
                                "priors_tracking",
                                None,
                                None,
                                str(list(priors.keys())),
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:PRIORS] DB insert skipped: {db_exc}")
            elif event.event_type == EventType.ACTION_CHOSEN:
                logger.debug(
                    "[PLUGIN:PRIORS] chosen=%s source=%s",
                    event.payload.get("action"),
                    event.payload.get("source"),
                )
        except Exception as exc:
            raise exc


class ResonanceMetaOperatorPlugin(ModeAwarePlugin):
    """Detect resonance/meta-operator signals without altering actions."""

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [EventType.ACTION_EXECUTED, EventType.RUN_FINALIZED]

    def handle(self, event: Event) -> None:
        try:
            if event.event_type == EventType.ACTION_EXECUTED:
                logger.debug(
                    "[PLUGIN:RESONANCE] action=%s w_R=%s",
                    event.payload.get("action"),
                    event.payload.get("w_R_weight"),
                )
                operator_hint = event.payload.get("operator_hint")
                decomposition_hint = event.payload.get("decomposition_hint")
                domain_tag = event.payload.get("operator_domain") or event.payload.get("domain_tag")
                lineage = event.payload.get("operator_lineage")
                decay_score = event.payload.get("operator_decay") or event.payload.get("decay_score")
                operator_name = operator_hint.get("operator") if isinstance(operator_hint, dict) else operator_hint
                if isinstance(operator_hint, dict) and not domain_tag:
                    domain_tag = operator_hint.get("operator_domain") or operator_hint.get("pattern_type")
                operator_description = json.dumps(operator_hint) if operator_hint else None
                resonance_score = event.payload.get("w_R_weight")
                generation = event.payload.get("generation") or 0
                source_attempt_id = event.payload.get("attempt_id")
                source_mode = event.payload.get("mode")
                parent_package_id = lineage if isinstance(lineage, str) else None
                package_id = None
                if operator_name:
                    try:
                        package_id = "metaop_" + hashlib.sha256(
                            f"{operator_name}:{domain_tag}".encode("utf-8", "ignore")
                        ).hexdigest()[:12]
                    except Exception:
                        package_id = None
                resonance_tags = json.dumps(
                    {
                        "resonance": resonance_score,
                        "operator_hint": operator_hint,
                        "decomposition_hint": decomposition_hint,
                        "domain_tag": domain_tag,
                        "lineage": lineage,
                        "decay_score": decay_score,
                    }
                )
                if self.db and event.payload.get("attempt_id"):
                    try:
                        if package_id:
                            try:
                                self.db.execute_query(
                                    """
                                    INSERT OR IGNORE INTO viral_information_packages (
                                        package_id, package_name, package_type, meta_strategy_description,
                                        virulence, transmission_rate, mutation_rate, success_rate,
                                        avg_score_contribution, total_infections, active_infections,
                                        discovery_generation, generation_discovered, source_attempt_id,
                                        source_mode, obsolescence_score, parent_package_id
                                    ) VALUES (?, ?, 'meta_strategy', ?, ?, 0.3, 0.05, 0.0, 0.0, 0, 0, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        package_id,
                                        str(operator_name),
                                        operator_description,
                                        resonance_score or 0.5,
                                        generation,
                                        generation,
                                        source_attempt_id,
                                        source_mode,
                                        decay_score or 0.0,
                                        parent_package_id,
                                    ),
                                )
                                self.db.execute_query(
                                    """
                                    UPDATE viral_information_packages
                                    SET last_successful_use_generation = COALESCE(?, last_successful_use_generation),
                                        obsolescence_score = COALESCE(?, obsolescence_score, 0.0)
                                    WHERE package_id = ?
                                    """,
                                    (generation, decay_score or 0.0, package_id),
                                )
                            except Exception as pkg_exc:
                                logger.debug(f"[PLUGIN:RESONANCE] Package insert skipped: {pkg_exc}")
                        self.db.execute_query(
                            """
                            INSERT INTO action_proposals_log (
                              attempt_id, step_idx, proposed_actions, chosen_action,
                              chosen_reason, role_compliance, theory_validation_state,
                              resonance_tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                event.payload.get("attempt_id"),
                                event.payload.get("step_idx", 0),
                                None,
                                event.payload.get("action"),
                                "resonance_tracking",
                                None,
                                None,
                                resonance_tags,
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:RESONANCE] DB insert skipped: {db_exc}")
            elif event.event_type == EventType.RUN_FINALIZED:
                logger.debug(
                    "[PLUGIN:RESONANCE] finalized game=%s attempt=%s w_R=%s",
                    event.payload.get("game_id"),
                    event.payload.get("attempt_id"),
                    event.payload.get("w_R_weight"),
                )
        except Exception as exc:
            raise exc


class BudgetPacingPlugin(ModeAwarePlugin):
    """Budget/pacing telemetry wrapper around adaptive limits (read-only)."""

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [EventType.RUN_INIT, EventType.RUN_FINALIZED]

    def handle(self, event: Event) -> None:
        try:
            if event.event_type == EventType.RUN_INIT:
                logger.debug(
                    "[PLUGIN:BUDGET] init actions_budget=%s role=%s mode=%s",
                    event.payload.get("actions_budget"),
                    event.payload.get("role"),
                    event.payload.get("mode"),
                )
            elif event.event_type == EventType.RUN_FINALIZED:
                logger.debug(
                    "[PLUGIN:BUDGET] finalized actions_used=%s guard_budget_ok=%s",
                    event.payload.get("actions_used"),
                    event.payload.get("guard_budget_ok"),
                )
                if self.db and event.payload.get("attempt_id"):
                    try:
                        self.db.execute_query(
                            """
                            UPDATE attempts
                            SET actions_used = COALESCE(actions_used, ?),
                                guard_budget_ok = COALESCE(guard_budget_ok, ?)
                            WHERE attempt_id = ?
                            """,
                            (
                                event.payload.get("actions_used"),
                                1 if event.payload.get("guard_budget_ok") else 0,
                                event.payload.get("attempt_id"),
                            ),
                        )
                    except Exception as db_exc:
                        logger.debug(f"[PLUGIN:BUDGET] DB update skipped: {db_exc}")
        except Exception as exc:
            raise exc


class MetacogObserverPlugin(ModeAwarePlugin):
    """Observer plugin: captures metacog/ladder/ambiguity telemetry in DB."""

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [
            EventType.ACTION_CHOSEN,
            EventType.ACTION_EXECUTED,
            EventType.STEP_COMPLETE,
            EventType.RUN_FINALIZED,
        ]

    def handle(self, event: Event) -> None:
        try:
            attempt_id = event.payload.get("attempt_id")
            if not self.db or not attempt_id:
                return

            step_idx = event.payload.get("step_idx", 0) or 0
            mode = event.payload.get("mode")
            role = event.payload.get("role")
            available_actions = event.payload.get("available_actions") or []
            ambiguity_metrics = event.payload.get("ambiguity_metrics") or {}
            ambiguity = (
                ambiguity_metrics.get("ambiguity")
                if isinstance(ambiguity_metrics, dict)
                else len(available_actions) if isinstance(available_actions, (list, tuple)) else None
            )
            consensus_proxy = ambiguity_metrics.get("consensus_proxy") if isinstance(ambiguity_metrics, dict) else None
            accuracy_proxy = ambiguity_metrics.get("accuracy_proxy") if isinstance(ambiguity_metrics, dict) else None
            if ambiguity is None and isinstance(available_actions, (list, tuple)):
                ambiguity = len(available_actions)
            ladder_rung = event.payload.get("ladder_rung")
            ladder_trace = event.payload.get("ladder_trace")
            chosen_action = event.payload.get("action") or event.payload.get("state") or event.event_type.name
            cause_effect_tags = event.payload.get("cause_effect_tags") or event.payload.get("cause_effect")
            compare_contrast_tags = event.payload.get("compare_contrast_tags") or event.payload.get("compare_contrast")

            structure_tag = event.payload.get("structure_tag") or event.payload.get("structure_tags")
            pctl_stage = event.payload.get("pctl_stage") or event.payload.get("pctl_stage_tag")

            resonance_tags = {
                "meta_observer": {
                    "event": event.event_type.name,
                    "ladder_rung": ladder_rung,
                    "ambiguity": ambiguity,
                    "w_A": event.payload.get("w_A_weight"),
                    "w_B": event.payload.get("w_B_weight"),
                    "w_R": event.payload.get("w_R_weight"),
                    "operator_hint": event.payload.get("operator_hint"),
                    "decomposition_hint": event.payload.get("decomposition_hint"),
                    "ladder_trace": ladder_trace,
                    "cause_effect": cause_effect_tags,
                    "compare_contrast": compare_contrast_tags,
                    "structure_tag": structure_tag,
                    "pctl_stage": pctl_stage,
                    "ambiguity_metrics": ambiguity_metrics,
                    "consensus_proxy": consensus_proxy,
                    "accuracy_proxy": accuracy_proxy,
                }
            }

            try:
                self.db.execute_query(
                    """
                    INSERT INTO action_proposals_log (
                      attempt_id, step_idx, available_actions, proposals, chosen_action,
                      chosen_reason, w_A, w_B, w_R, resonance_tags, role_compliance,
                      theory_validation_state, attention_window_id, mode
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt_id,
                        step_idx,
                        json.dumps(available_actions) if available_actions else None,
                        json.dumps(ladder_trace) if ladder_trace else None,
                        str(chosen_action),
                        "meta_observer",
                        event.payload.get("w_A_weight"),
                        event.payload.get("w_B_weight"),
                        event.payload.get("w_R_weight"),
                        json.dumps(resonance_tags),
                        role,
                        event.payload.get("theory_validation_state"),
                        event.payload.get("attention_window_id"),
                        mode,
                    ),
                )
            except Exception as db_exc:
                logger.warning(f"[HOOK_FAILURE][PLUGIN:METACOG] DB insert failed: {db_exc}")
        except Exception as exc:
            raise exc


class ThoughtExperimentPlugin(ModeAwarePlugin):
    """Capture intrinsic milestones / thought experiments as DB-only telemetry."""

    def __init__(self, db: Optional[DatabaseInterface] = None, allowed_modes: Iterable[str] = ("LIVE",)) -> None:
        super().__init__(allowed_modes)
        self.db: Optional[DatabaseInterface] = db

    def interested_events(self) -> Iterable[EventType]:
        return [EventType.STEP_COMPLETE, EventType.RUN_FINALIZED]

    @staticmethod
    def _normalize_entries(payload: Optional[object]) -> List[dict]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    def handle(self, event: Event) -> None:
        try:
            if not self.db:
                return

            entries = self._normalize_entries(
                event.payload.get("intrinsic_milestones") or event.payload.get("thought_experiments")
            )
            if not entries:
                return

            attempt_id = event.payload.get("attempt_id")
            game_type = event.payload.get("game_type")
            level_number = event.payload.get("level") or event.payload.get("level_number")
            agent_id = event.payload.get("agent_id")
            generation = event.payload.get("generation")
            mode = event.payload.get("mode")

            for entry in entries:
                try:
                    hypothesis = (
                        entry.get("hypothesis")
                        or entry.get("theory")
                        or entry.get("question")
                        or "thought_experiment"
                    )
                    self.db.record_intrinsic_milestone(
                        attempt_id=entry.get("attempt_id") or attempt_id,
                        agent_id=entry.get("agent_id") or agent_id,
                        game_type=entry.get("game_type") or game_type,
                        level_number=entry.get("level_number") or level_number,
                        hypothesis=hypothesis,
                        expected_signal=entry.get("expected_signal") or entry.get("expected_outcome"),
                        observed_signal=entry.get("observed_signal") or entry.get("observed_outcome"),
                        outcome=entry.get("outcome") or entry.get("result"),
                        status=entry.get("status")
                        or ("observed" if entry.get("observed_outcome") is not None else "pending"),
                        milestone_tag=entry.get("milestone_tag")
                        or entry.get("milestone")
                        or entry.get("tag"),
                        confidence=entry.get("confidence"),
                        evidence=entry.get("evidence"),
                        source_mode=entry.get("source_mode") or mode,
                        generation=entry.get("generation") or generation,
                        decay_score=entry.get("decay_score"),
                        reliability=entry.get("reliability"),
                        consensus=entry.get("consensus"),
                        source_attempt_id=entry.get("source_attempt_id") or attempt_id,
                    )
                except Exception as db_exc:
                    logger.debug(f"[PLUGIN:THOUGHT] DB insert skipped: {db_exc}")
        except Exception as exc:
            raise exc


class PluginFailureProbe(ModeAwarePlugin):
    """Optional failure injector to validate HOOK_FAILURE_DETECTED plumbing."""

    def __init__(self, allowed_modes: Iterable[str] = ("LIVE",), env_flag: str = "OBSERVABILITY_PLUGIN_FAIL") -> None:
        super().__init__(allowed_modes)
        self.env_flag = env_flag

    def interested_events(self) -> Iterable[EventType]:
        return [EventType.RUN_INIT]

    def handle(self, event: Event) -> None:
        flag = os.getenv(self.env_flag, "0").lower()
        if flag in ("1", "true", "yes", "on"):
            raise RuntimeError(f"observability plugin failure injected via {self.env_flag}")


def default_observability_plugins(db: Optional[DatabaseInterface] = None) -> List[ModeAwarePlugin]:
    """Factory for safe, mode-aware observability plugins (emit-only)."""
    return [
        LessonExtractionPlugin(db=db),
        PriorsPlugin(db=db),
        ResonanceMetaOperatorPlugin(db=db),
        BudgetPacingPlugin(db=db),
        MetacogObserverPlugin(db=db),
        ThoughtExperimentPlugin(db=db),
        PluginFailureProbe(),
    ]

