import os
import sqlite3
from typing import Any, Dict, List, Tuple

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
DB_PATH = "core_data.db"


def _safe_cast_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fetch_rows(conn: sqlite3.Connection, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, params)
    return [dict(row) for row in cur.fetchall()]


def _truncate(text: Any, limit: int = 120) -> str:
    value = "" if text is None else str(text)
    return value if len(value) <= limit else value[: limit - 3] + "..."


def summarize_agent_biographies(conn: sqlite3.Connection, limit: int = 10) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT agent_id, role, game_type, level_number, generation, created_at, timeline,
               wa_adoptions, wb_adoptions, wa_rejections, wb_rejections
        FROM agent_biographies
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[agent_biographies] most recent entries")
    for row in rows:
        wa = row.get("wa_adoptions") or ""
        wb = row.get("wb_adoptions") or ""
        print(
            f"  agent={row['agent_id']} role={row['role'] or 'n/a'} "
            f"game={row['game_type'] or 'n/a'} lvl={row['level_number'] or 'n/a'} "
            f"gen={row['generation'] or 'n/a'} at={row['created_at']} timeline={_truncate(row['timeline'])} "
            f"wa={_truncate(wa, 40)} wb={_truncate(wb, 40)}"
        )


def summarize_struggles(conn: sqlite3.Connection) -> None:
    grouped = fetch_rows(
        conn,
        """
        SELECT indicator_type, severity, resolved, COUNT(*) AS count
        FROM agent_struggle_indicators
        GROUP BY indicator_type, severity, resolved
        ORDER BY count DESC
        """,
    )
    print("[agent_struggle_indicators] type | severity | resolved | count")
    for row in grouped:
        resolved = "yes" if row["resolved"] else "no"
        print(f"  {row['indicator_type'] or 'unknown'} | {row['severity'] or 'n/a'} | {resolved} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, indicator_type, severity, signals, created_at
        FROM agent_struggle_indicators
        WHERE resolved = 0
        ORDER BY created_at DESC
        LIMIT 8
        """,
    )
    if recent:
        print("  recent unresolved (latest 8)")
        for row in recent:
            print(
                f"    agent={row['agent_id']} type={row['indicator_type'] or 'n/a'} "
                f"severity={row['severity'] or 'n/a'} signals={_truncate(row['signals'])} at={row['created_at']}"
            )


def summarize_competence(conn: sqlite3.Connection) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT
            ROUND(AVG(COALESCE(prediction_accuracy,0)),3) AS avg_pred,
            ROUND(AVG(COALESCE(theory_coherence,0)),3) AS avg_coh,
            ROUND(AVG(COALESCE(transfer_rate,0)),3) AS avg_transfer,
            ROUND(AVG(COALESCE(explanation_quality,0)),3) AS avg_explain,
            ROUND(AVG(COALESCE(metacog_calibration,0)),3) AS avg_meta,
            ROUND(AVG(COALESCE(recovery_rate,0)),3) AS avg_recovery,
            COUNT(*) AS rows
        FROM competence_metrics
        """,
    )
    if rollup:
        r = rollup[0]
        print("[competence_metrics] avg_pred | avg_coh | avg_transfer | avg_explain | avg_meta | avg_recovery | rows")
        print(
            f"  {r['avg_pred']} | {r['avg_coh']} | {r['avg_transfer']} | "
            f"{r['avg_explain']} | {r['avg_meta']} | {r['avg_recovery']} | {r['rows']}"
        )

    latest = fetch_rows(
        conn,
        """
        SELECT agent_id, game_id, level, prediction_accuracy, theory_coherence, transfer_rate,
               explanation_quality, metacog_calibration, recovery_rate, updated_at
        FROM competence_metrics
        ORDER BY updated_at DESC
        LIMIT 8
        """,
    )
    if latest:
        print("  recent competence entries (latest 8)")
        for row in latest:
            pred = _safe_cast_float(row.get("prediction_accuracy"))
            coh = _safe_cast_float(row.get("theory_coherence"))
            transfer = _safe_cast_float(row.get("transfer_rate"))
            explain = _safe_cast_float(row.get("explanation_quality"))
            meta = _safe_cast_float(row.get("metacog_calibration"))
            recovery = _safe_cast_float(row.get("recovery_rate"))
            print(
                f"    agent={row['agent_id']} game={row['game_id'] or 'n/a'} lvl={row['level'] or 'n/a'} "
                f"pred={pred} coh={coh} transfer={transfer} explain={explain} meta={meta} "
                f"recovery={recovery} at={row['updated_at']}"
            )


def summarize_competence_distribution(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT
            SUM(CASE WHEN prediction_accuracy >= 0.8 THEN 1 ELSE 0 END) AS pred_good,
            SUM(CASE WHEN prediction_accuracy BETWEEN 0.5 AND 0.8 THEN 1 ELSE 0 END) AS pred_mid,
            SUM(CASE WHEN prediction_accuracy < 0.5 THEN 1 ELSE 0 END) AS pred_low,
            SUM(CASE WHEN theory_coherence >= 0.8 THEN 1 ELSE 0 END) AS coh_good,
            SUM(CASE WHEN theory_coherence BETWEEN 0.5 AND 0.8 THEN 1 ELSE 0 END) AS coh_mid,
            SUM(CASE WHEN theory_coherence < 0.5 THEN 1 ELSE 0 END) AS coh_low,
            COUNT(*) AS rows
        FROM competence_metrics
        """,
    )
    if rows:
        r = rows[0]
        print("[competence_distribution] pred_good | pred_mid | pred_low | coh_good | coh_mid | coh_low | rows")
        print(
            f"  {r['pred_good']} | {r['pred_mid']} | {r['pred_low']} | "
            f"{r['coh_good']} | {r['coh_mid']} | {r['coh_low']} | {r['rows']}"
        )


def summarize_competence_trend(conn: sqlite3.Connection, limit: int = 5) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT generation,
               ROUND(AVG(COALESCE(prediction_accuracy,0)),3) AS avg_pred,
               ROUND(AVG(COALESCE(theory_coherence,0)),3) AS avg_coh,
               ROUND(AVG(COALESCE(transfer_rate,0)),3) AS avg_transfer,
               ROUND(AVG(COALESCE(explanation_quality,0)),3) AS avg_explain,
               ROUND(AVG(COALESCE(metacog_calibration,0)),3) AS avg_meta,
               ROUND(AVG(COALESCE(recovery_rate,0)),3) AS avg_recovery,
               COUNT(*) AS rows
        FROM competence_metrics
        WHERE generation IS NOT NULL
        GROUP BY generation
        ORDER BY generation DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[competence_trend] gen | pred | coh | transfer | explain | meta | recovery | rows")
    for row in rows:
        print(
            f"  {row['generation']} | {row['avg_pred']} | {row['avg_coh']} | {row['avg_transfer']} | "
            f"{row['avg_explain']} | {row['avg_meta']} | {row['avg_recovery']} | {row['rows']}"
        )


def summarize_peer_teaching(conn: sqlite3.Connection) -> None:
    outcomes = fetch_rows(
        conn,
        """
        SELECT outcome, adoption_success, COUNT(*) AS count
        FROM peer_teaching_graph
        GROUP BY outcome, adoption_success
        ORDER BY count DESC
        """,
    )
    print("[peer_teaching_graph] outcome | adoption_success | count")
    for row in outcomes:
        adoption = "yes" if row["adoption_success"] else "no"
        print(f"  {row['outcome'] or 'n/a'} | {adoption} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT teacher_agent_id, learner_agent_id, concept_id, outcome, adoption_success, created_at
        FROM peer_teaching_graph
        ORDER BY created_at DESC
        LIMIT 8
        """,
    )
    if recent:
        print("  recent peer teaching (latest 8)")
        for row in recent:
            adoption = "yes" if row["adoption_success"] else "no"
            print(
                f"    teacher={row['teacher_agent_id']} learner={row['learner_agent_id']} concept={row['concept_id'] or 'n/a'} "
                f"outcome={row['outcome'] or 'n/a'} adoption={adoption} at={row['created_at']}"
            )


def summarize_gaps(conn: sqlite3.Connection) -> None:
    gaps = fetch_rows(
        conn,
        """
        SELECT gap_type, severity, status, COUNT(*) AS count
        FROM gap_registry
        GROUP BY gap_type, severity, status
        ORDER BY count DESC
        """,
    )
    print("[gap_registry] type | severity | status | count")
    for row in gaps:
        print(f"  {row['gap_type'] or 'unknown'} | {row['severity'] or 'n/a'} | {row['status'] or 'n/a'} | {row['count']}")

    interventions = fetch_rows(
        conn,
        """
        SELECT intervention_type, outcome_status, COUNT(*) AS count
        FROM interventions
        GROUP BY intervention_type, outcome_status
        ORDER BY count DESC
        """,
    )
    print("[interventions] type | outcome | count")
    for row in interventions:
        print(f"  {row['intervention_type'] or 'unknown'} | {row['outcome_status'] or 'n/a'} | {row['count']}")


def summarize_gap_trend(conn: sqlite3.Connection, limit: int = 10) -> None:
    recent = fetch_rows(
        conn,
        """
        SELECT gap_type, severity, status, detected_at
        FROM gap_registry
        ORDER BY detected_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[gap_registry recent] type | severity | status | detected_at")
    for row in recent:
        print(
            f"  {row['gap_type'] or 'unknown'} | {row['severity'] or 'n/a'} | {row['status'] or 'n/a'} | {row['detected_at']}"
        )


def summarize_gap_severity_rollup(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT severity, COUNT(*) AS count
        FROM gap_registry
        GROUP BY severity
        ORDER BY count DESC
        """,
    )
    print("[gap_registry severity] severity | count")
    for row in rows:
        print(f"  {row['severity'] or 'n/a'} | {row['count']}")


def summarize_stuck_interventions(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT resolved, COUNT(*) AS count
        FROM stuck_game_interventions
        GROUP BY resolved
        """,
    )
    print("[stuck_game_interventions] resolved | count")
    for row in rollup:
        status = "yes" if row["resolved"] else "no"
        print(f"  {status} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT game_type, generation, bottleneck_level, agents_stuck, total_agents, stuck_ratio,
               resolved, resolution_generation, breakthrough_action, created_at
        FROM stuck_game_interventions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent stuck interventions (latest 8)")
        for row in recent:
            status = "yes" if row["resolved"] else "no"
            print(
                f"    game={row['game_type']} gen={row['generation']} lvl={row['bottleneck_level'] or 'n/a'} "
                f"stuck={row['agents_stuck']}/{row['total_agents']} ratio={row['stuck_ratio']} "
                f"resolved={status} res_gen={row['resolution_generation'] or 'n/a'} "
                f"break={row['breakthrough_action'] or 'n/a'} at={row['created_at']}"
            )


def summarize_concept_library(conn: sqlite3.Connection, limit: int = 10) -> None:
    concepts = fetch_rows(
        conn,
        """
        SELECT concept_id, concept_name, peer_review_status, ROUND(COALESCE(reliability_score,0),3) AS reliability,
               created_at
        FROM concept_library
        ORDER BY peer_review_status DESC, reliability DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[concept_library] status | reliability | concept | id | created_at")
    for row in concepts:
        print(
            f"  {row['peer_review_status'] or 'n/a'} | {row['reliability']} | "
            f"{_truncate(row['concept_name'])} | {row['concept_id']} | {row['created_at']}"
        )


def summarize_theory_versions(conn: sqlite3.Connection, limit: int = 10) -> None:
    versions = fetch_rows(
        conn,
        """
        SELECT theory_id, version_number, ROUND(COALESCE(confidence,0),3) AS confidence,
               status, change_summary, assumptions, created_at
        FROM theory_versions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[theory_versions] theory | ver | conf | status | change | assumptions | created")
    for row in versions:
        print(
            f"  {row['theory_id']} | v{row['version_number']} | {row['confidence']} | {row['status'] or 'n/a'} | "
            f"{_truncate(row['change_summary'], 60)} | {_truncate(row['assumptions'], 60)} | {row['created_at']}"
        )


def summarize_theory_timelines(conn: sqlite3.Connection, limit: int = 5) -> None:
    top = fetch_rows(
        conn,
        """
        SELECT theory_id, COUNT(*) AS versions, MAX(version_number) AS max_ver
        FROM theory_versions
        GROUP BY theory_id
        ORDER BY versions DESC, max_ver DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[theory_timelines] top theories by versions")
    if not top:
        print("  none")
        return
    for row in top:
        print(f"  theory={row['theory_id']} versions={row['versions']} max_ver={row['max_ver']}")

    for row in top:
        entries = fetch_rows(
            conn,
            """
            SELECT version_number, ROUND(COALESCE(confidence,0),3) AS confidence, status, change_summary, created_at
            FROM theory_versions
            WHERE theory_id = ?
            ORDER BY version_number DESC
            LIMIT 3
            """,
            (row["theory_id"],),
        )
        print(f"  recent for {row['theory_id']}")
        for entry in entries:
            print(
                f"    v{entry['version_number']} conf={entry['confidence']} status={entry['status'] or 'n/a'} "
                f"change={_truncate(entry['change_summary'], 60)} at={entry['created_at']}"
            )

def summarize_theory_version_contradictions(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN contradicting_evidence IS NOT NULL AND LENGTH(contradicting_evidence) > 0 THEN 1 ELSE 0 END) AS with_contradictions
        FROM theory_versions
        """,
    )
    r = rollup[0] if rollup else {"total": 0, "with_contradictions": 0}
    print("[theory_versions contradictions] total | with_contradictions")
    print(f"  {r['total']} | {r['with_contradictions']}")

    recent = fetch_rows(
        conn,
        """
        SELECT theory_id, version_number, status, confidence, contradicting_evidence, created_at
        FROM theory_versions
        WHERE contradicting_evidence IS NOT NULL AND LENGTH(contradicting_evidence) > 0
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent version contradictions (latest 8)")
        for row in recent:
            print(
                f"    theory={row['theory_id']} v{row['version_number']} status={row['status'] or 'n/a'} conf={row['confidence']} "
                f"contradictions={_truncate(row['contradicting_evidence'], 80)} at={row['created_at']}"
            )


def summarize_theory_contradiction_trend(conn: sqlite3.Connection, limit: int = 10) -> None:
    trend = fetch_rows(
        conn,
        """
        SELECT substr(created_at, 1, 10) AS day,
               COUNT(*) AS versions,
               SUM(CASE WHEN contradicting_evidence IS NOT NULL AND LENGTH(contradicting_evidence) > 0 THEN 1 ELSE 0 END) AS with_contradictions
        FROM theory_versions
        GROUP BY day
        ORDER BY day DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[theory_version contradiction trend] day | versions | with_contradictions")
    for row in trend:
        print(f"  {row['day']} | {row['versions']} | {row['with_contradictions']}")


def summarize_agent_hypotheses(conn: sqlite3.Connection, limit: int = 10) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT status, COUNT(*) AS count
        FROM agent_hypotheses
        GROUP BY status
        ORDER BY count DESC
        """,
    )
    print("[agent_hypotheses] status | count")
    for row in rollup:
        print(f"  {row['status'] or 'n/a'} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT hypothesis_id, agent_id, game_type, level_number, hypothesis_type, confidence, status, created_at
        FROM agent_hypotheses
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent hypotheses (latest 10)")
        for row in recent:
            print(
                f"    id={row['hypothesis_id']} agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"type={row['hypothesis_type']} conf={row['confidence']} status={row['status']} at={row['created_at']}"
            )


def summarize_knowledge_graph(conn: sqlite3.Connection, limit: int = 10) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT edge_type, COUNT(*) AS count
        FROM knowledge_graph_edges
        GROUP BY edge_type
        ORDER BY count DESC
        """,
    )
    print("[knowledge_graph_edges] type | count")
    for row in rollup:
        print(f"  {row['edge_type'] or 'n/a'} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT edge_id, source_knowledge_type, target_knowledge_type, edge_type, confidence, discovered_at
        FROM knowledge_graph_edges
        ORDER BY discovered_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent edges (latest 10)")
        for row in recent:
            print(
                f"    id={row['edge_id']} {row['source_knowledge_type']}->{row['target_knowledge_type']} type={row['edge_type']} "
                f"conf={row['confidence']} at={row['discovered_at']}"
            )


def summarize_gaps_by_concept(conn: sqlite3.Connection, limit: int = 10) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT concept_id, COUNT(*) AS count
        FROM gap_registry
        WHERE concept_id IS NOT NULL AND LENGTH(concept_id) > 0
        GROUP BY concept_id
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[gap_registry by concept] concept_id | count")
    for row in rows:
        print(f"  {row['concept_id']} | {row['count']}")


def summarize_agent_theories(conn: sqlite3.Connection, limit: int = 10) -> None:
    theories = fetch_rows(
        conn,
        """
        SELECT theory_id, theory_type, game_type, level_number, status,
               ROUND(COALESCE(confidence,0),3) AS confidence,
               tests_conducted, tests_successful, created_at
        FROM agent_theories
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[agent_theories] theory | type | game | lvl | status | conf | tests | created")
    for row in theories:
        print(
            f"  {row['theory_id']} | {row['theory_type']} | {row['game_type']} | {row['level_number']} | "
            f"{row['status'] or 'n/a'} | {row['confidence']} | {row['tests_successful']}/{row['tests_conducted']} | {row['created_at']}"
        )


def summarize_assumptions(conn: sqlite3.Connection) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT assumption_type, is_valid, COUNT(*) AS count
        FROM metacognitive_assumptions
        GROUP BY assumption_type, is_valid
        ORDER BY count DESC
        """,
    )
    print("[metacognitive_assumptions] type | valid | count")
    for row in rollup:
        valid = "yes" if row["is_valid"] else ("no" if row["is_valid"] == 0 else "untested")
        print(f"  {row['assumption_type'] or 'unknown'} | {valid} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, assumption_type, assumption_text, is_valid, created_at
        FROM metacognitive_assumptions
        ORDER BY created_at DESC
        LIMIT 8
        """,
    )
    if recent:
        print("  recent assumptions (latest 8)")
        for row in recent:
            valid = "yes" if row["is_valid"] else ("no" if row["is_valid"] == 0 else "untested")
            print(
                f"    agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"type={row['assumption_type']} valid={valid} text={_truncate(row['assumption_text'], 60)} at={row['created_at']}"
            )


def summarize_theory_contradictions(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN contradicting_observations IS NOT NULL AND LENGTH(contradicting_observations) > 0 THEN 1 ELSE 0 END) AS with_contradictions
        FROM agent_theories
        """,
    )
    r = rollup[0] if rollup else {"total": 0, "with_contradictions": 0}
    print("[agent_theories contradictions] total | with_contradictions")
    print(f"  {r['total']} | {r['with_contradictions']}")

    recent = fetch_rows(
        conn,
        """
        SELECT theory_id, game_type, level_number, status, confidence, contradicting_observations, created_at
        FROM agent_theories
        WHERE contradicting_observations IS NOT NULL AND LENGTH(contradicting_observations) > 0
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent contradictions (latest 8)")
        for row in recent:
            print(
                f"    theory={row['theory_id']} game={row['game_type']} lvl={row['level_number']} "
                f"status={row['status'] or 'n/a'} conf={row['confidence']} contradictions={_truncate(row['contradicting_observations'], 80)} "
                f"at={row['created_at']}"
            )


def summarize_population_health(conn: sqlite3.Connection) -> None:
    latest = fetch_rows(
        conn,
        """
        SELECT generation, measurement_timestamp, genetic_diversity_score, performance_variance,
               stagnation_indicator, improvement_rate, population_size, active_agents,
               best_win_rate, average_win_rate, worst_win_rate, win_rate_std_dev
        FROM population_health_metrics
        ORDER BY measurement_timestamp DESC
        LIMIT 1
        """,
    )
    print("[population_health_metrics] latest")
    if not latest:
        print("  none")
        return
    row = latest[0]
    print(
        f"  gen={row['generation']} ts={row['measurement_timestamp']} diversity={row['genetic_diversity_score']} "
        f"variance={row['performance_variance']} stagnation={row['stagnation_indicator']} improvement={row['improvement_rate']} "
        f"pop={row['population_size']} active={row['active_agents']} avg_win={row['average_win_rate']} "
        f"best={row['best_win_rate']} worst={row['worst_win_rate']} std={row['win_rate_std_dev']}"
    )


def summarize_success_insights(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT insight_type, COUNT(*) AS count, SUM(times_worked) AS worked, SUM(times_failed) AS failed
        FROM agent_success_insights
        GROUP BY insight_type
        ORDER BY count DESC
        """,
    )
    print("[agent_success_insights] type | count | worked | failed")
    for row in rollup:
        print(f"  {row['insight_type'] or 'n/a'} | {row['count']} | {row['worked'] or 0} | {row['failed'] or 0}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, insight_type, insight_text, confidence, created_at
        FROM agent_success_insights
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent success insights (latest 8)")
        for row in recent:
            print(
                f"    agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"type={row['insight_type']} conf={row['confidence']} text={_truncate(row['insight_text'], 80)} "
                f"at={row['created_at']}"
            )


def summarize_failure_patterns(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT common_factor, SUM(failure_count) AS failures, COUNT(*) AS rows
        FROM metacognitive_failure_patterns
        GROUP BY common_factor
        ORDER BY failures DESC
        LIMIT 5
        """,
    )
    print("[metacognitive_failure_patterns] factor | failures | rows")
    for row in rollup:
        print(f"  {row['common_factor'] or 'unknown'} | {row['failures'] or 0} | {row['rows'] or 0}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, common_factor, failure_count, insight_applied, created_at
        FROM metacognitive_failure_patterns
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent failure patterns (latest 8)")
        for row in recent:
            applied = "yes" if row["insight_applied"] else "no"
            print(
                f"    agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"factor={row['common_factor']} fails={row['failure_count']} applied={applied} at={row['created_at']}"
            )


def summarize_metacog_insights(conn: sqlite3.Connection, limit: int = 8) -> None:
    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, key_insight, winning_strategy, breakthrough_action,
               actions_before_breakthrough, is_transferable, created_at
        FROM metacognitive_insights
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    print("[metacognitive_insights] recent (latest 8)")
    if not recent:
        print("  none")
        return
    for row in recent:
        transferable = "yes" if row["is_transferable"] else "no"
        print(
            f"  agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
            f"insight={_truncate(row['key_insight'], 60)} strategy={_truncate(row['winning_strategy'], 60)} "
            f"break_action={row['breakthrough_action'] or 'n/a'} before={row['actions_before_breakthrough']} "
            f"transferable={transferable} at={row['created_at']}"
        )


def summarize_predictions(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT prediction_correct, COUNT(*) AS count
        FROM metacognitive_predictions
        GROUP BY prediction_correct
        """,
    )
    print("[metacognitive_predictions] correct | count")
    for row in rollup:
        status = "yes" if row["prediction_correct"] else ("no" if row["prediction_correct"] == 0 else "unknown")
        print(f"  {status} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, theory_text, predicted_outcome, actual_outcome,
               prediction_correct, theory_revised, created_at
        FROM metacognitive_predictions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent predictions (latest 8)")
        for row in recent:
            status = "yes" if row["prediction_correct"] else ("no" if row["prediction_correct"] == 0 else "unknown")
            revised = "yes" if row.get("theory_revised") else "no"
            print(
                f"    agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"pred={_truncate(row['predicted_outcome'], 50)} actual={_truncate(row['actual_outcome'], 50)} "
                f"correct={status} revised={revised} theory={_truncate(row['theory_text'], 50)} at={row['created_at']}"
            )


def summarize_eliminations(conn: sqlite3.Connection, limit: int = 8) -> None:
    rollup = fetch_rows(
        conn,
        """
        SELECT eliminated_action, COUNT(*) AS count
        FROM metacognitive_eliminations
        GROUP BY eliminated_action
        ORDER BY count DESC
        LIMIT 5
        """,
    )
    print("[metacognitive_eliminations] action | count")
    for row in rollup:
        print(f"  {row['eliminated_action']} | {row['count']}")

    recent = fetch_rows(
        conn,
        """
        SELECT agent_id, game_type, level_number, eliminated_action, reason, confidence, created_at
        FROM metacognitive_eliminations
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    if recent:
        print("  recent eliminations (latest 8)")
        for row in recent:
            print(
                f"    agent={row['agent_id']} game={row['game_type']} lvl={row['level_number']} "
                f"action={row['eliminated_action']} conf={row['confidence']} reason={_truncate(row['reason'], 60)} at={row['created_at']}"
            )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        summarize_agent_biographies(conn)
        print()
        summarize_struggles(conn)
        print()
        summarize_competence(conn)
        print()
        summarize_competence_distribution(conn)
        print()
        summarize_competence_trend(conn)
        print()
        summarize_peer_teaching(conn)
        print()
        summarize_gaps(conn)
        print()
        summarize_gap_severity_rollup(conn)
        print()
        summarize_gaps_by_concept(conn)
        print()
        summarize_gap_trend(conn)
        print()
        summarize_gap_severity_rollup(conn)
        print()
        summarize_stuck_interventions(conn)
        print()
        summarize_concept_library(conn)
        print()
        summarize_theory_versions(conn)
        print()
        summarize_theory_timelines(conn)
        print()
        summarize_theory_version_contradictions(conn)
        print()
        summarize_theory_contradiction_trend(conn)
        print()
        summarize_agent_hypotheses(conn)
        print()
        summarize_agent_theories(conn)
        print()
        summarize_knowledge_graph(conn)
        print()
        summarize_theory_contradictions(conn)
        print()
        summarize_assumptions(conn)
        print()
        summarize_population_health(conn)
        print()
        summarize_success_insights(conn)
        print()
        summarize_failure_patterns(conn)
        print()
        summarize_metacog_insights(conn)
        print()
        summarize_predictions(conn)
        print()
        summarize_eliminations(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
