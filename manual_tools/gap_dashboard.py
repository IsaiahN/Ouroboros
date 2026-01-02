import os
import sqlite3
from typing import Any, Dict, List, Tuple

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
DB_PATH = "core_data.db"


def fetch_rows(conn: sqlite3.Connection, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, params)
    return [dict(row) for row in cur.fetchall()]


def summarize_gap_registry(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT gap_type, severity, status, COUNT(*) AS count
        FROM gap_registry
        GROUP BY gap_type, severity, status
        ORDER BY count DESC
        """,
    )
    print("[gap_registry] type | severity | status | count")
    for row in rows:
        print(f"  {row['gap_type'] or 'unknown'} | {row['severity'] or 'n/a'} | {row['status'] or 'n/a'} | {row['count']}")


def summarize_interventions(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT intervention_type, outcome_status, COUNT(*) AS count
        FROM interventions
        GROUP BY intervention_type, outcome_status
        ORDER BY count DESC
        """,
    )
    print("[interventions] type | outcome | count")
    for row in rows:
        print(f"  {row['intervention_type'] or 'unknown'} | {row['outcome_status'] or 'n/a'} | {row['count']}")


def summarize_peer_teaching(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
        conn,
        """
        SELECT outcome, COUNT(*) AS count
        FROM peer_teaching_graph
        GROUP BY outcome
        ORDER BY count DESC
        """,
    )
    print("[peer_teaching] outcome | count")
    for row in rows:
        print(f"  {row['outcome'] or 'n/a'} | {row['count']}")


def summarize_competence(conn: sqlite3.Connection) -> None:
    rows = fetch_rows(
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
    if rows:
        row = rows[0]
        print("[competence_metrics] avg_pred | avg_coh | avg_transfer | avg_explain | avg_meta | avg_recovery | rows")
        print(
            f"  {row['avg_pred']} | {row['avg_coh']} | {row['avg_transfer']} | "
            f"{row['avg_explain']} | {row['avg_meta']} | {row['avg_recovery']} | {row['rows']}"
        )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        summarize_gap_registry(conn)
        print()
        summarize_interventions(conn)
        print()
        summarize_peer_teaching(conn)
        print()
        summarize_competence(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
