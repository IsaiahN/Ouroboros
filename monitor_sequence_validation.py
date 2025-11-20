#!/usr/bin/env python3
"""
Sequence Validation Monitoring Script

Purpose: Autonomous monitoring of sequence validation success rates
- Tracks validation success/failure per generation
- Identifies games/levels with highest failure rates
- Generates alerts if success rate falls below thresholds
- Provides diagnostic hypothesis about failure patterns

Part of: Immediate Phase (Gen 0-5) - User Priority #1
"""

import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import json


class SequenceValidationMonitor:
    """Monitor sequence validation health across evolution generations."""

    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get overall validation statistics."""
        cursor = self.conn.cursor()

        # Check if sequence_reputation table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sequence_reputation'
        """)

        if not cursor.fetchone():
            return {
                "table_exists": False,
                "message": "sequence_reputation table not found - validation tracking not yet implemented",
            }

        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sequences,
                SUM(successful_validations) as total_successes,
                SUM(total_validation_attempts) as total_attempts,
                CAST(SUM(successful_validations) AS FLOAT) / NULLIF(SUM(total_validation_attempts), 0) as overall_success_rate,
                AVG(CAST(successful_validations AS FLOAT) / NULLIF(total_validation_attempts, 0)) as avg_sequence_success_rate
            FROM sequence_reputation
            WHERE total_validation_attempts > 0
        """)

        stats = dict(cursor.fetchone())
        stats["table_exists"] = True

        return stats

    def get_validation_by_generation(self) -> List[Dict[str, Any]]:
        """Get validation success rates by generation."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT 
                a.generation,
                COUNT(DISTINCT sr.sequence_id) as sequences_validated,
                SUM(sr.successful_validations) as successes,
                SUM(sr.total_validation_attempts) as attempts,
                CAST(SUM(sr.successful_validations) AS FLOAT) / NULLIF(SUM(sr.total_validation_attempts), 0) as success_rate
            FROM sequence_reputation sr
            JOIN winning_sequences ws ON sr.sequence_id = ws.sequence_id
            JOIN agents a ON ws.agent_id = a.agent_id
            WHERE sr.total_validation_attempts > 0
            GROUP BY a.generation
            ORDER BY a.generation DESC
            LIMIT 10
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_failing_games(self, min_attempts: int = 3) -> List[Dict[str, Any]]:
        """Identify games with low validation success rates."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT 
                ws.game_id,
                ws.level_number,
                COUNT(DISTINCT sr.sequence_id) as sequence_count,
                SUM(sr.successful_validations) as successes,
                SUM(sr.total_validation_attempts) as attempts,
                CAST(SUM(sr.successful_validations) AS FLOAT) / NULLIF(SUM(sr.total_validation_attempts), 0) as success_rate
            FROM sequence_reputation sr
            JOIN winning_sequences ws ON sr.sequence_id = ws.sequence_id
            WHERE sr.total_validation_attempts >= ?
            GROUP BY ws.game_id, ws.level_number
            HAVING success_rate < 0.7 OR success_rate IS NULL
            ORDER BY attempts DESC, success_rate ASC
            LIMIT 20
        """,
            (min_attempts,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_proven_sequences(
        self, min_success_rate: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Get highly reliable sequences (>80% validation success)."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT 
                ws.sequence_id,
                ws.game_id,
                ws.level_number,
                sr.successful_validations,
                sr.total_validation_attempts,
                CAST(sr.successful_validations AS FLOAT) / NULLIF(sr.total_validation_attempts, 0) as success_rate,
                ws.total_score
            FROM sequence_reputation sr
            JOIN winning_sequences ws ON sr.sequence_id = ws.sequence_id
            WHERE sr.total_validation_attempts >= 3
                AND CAST(sr.successful_validations AS FLOAT) / NULLIF(sr.total_validation_attempts, 0) >= ?
            ORDER BY success_rate DESC, total_validation_attempts DESC
            LIMIT 10
        """,
            (min_success_rate,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def analyze_failure_patterns(self) -> Dict[str, Any]:
        """Generate hypothesis about validation failure patterns."""
        cursor = self.conn.cursor()

        # Check if we have any validation data
        cursor.execute(
            "SELECT COUNT(*) as count FROM sequence_reputation WHERE total_validation_attempts > 0"
        )
        validation_count = cursor.fetchone()["count"]

        if validation_count == 0:
            return {
                "hypothesis": "NO_DATA",
                "message": "No validation attempts recorded yet",
            }

        # Analyze by game type
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN ws.game_id LIKE 'ls%' THEN 'ls'
                    WHEN ws.game_id LIKE 'cw%' THEN 'cw'
                    WHEN ws.game_id LIKE 'dg%' THEN 'dg'
                    ELSE 'other'
                END as game_type,
                COUNT(DISTINCT sr.sequence_id) as sequence_count,
                SUM(sr.successful_validations) as successes,
                SUM(sr.total_validation_attempts) as attempts,
                CAST(SUM(sr.successful_validations) AS FLOAT) / NULLIF(SUM(sr.total_validation_attempts), 0) as success_rate
            FROM sequence_reputation sr
            JOIN winning_sequences ws ON sr.sequence_id = ws.sequence_id
            WHERE sr.total_validation_attempts > 0
            GROUP BY game_type
            ORDER BY success_rate ASC
        """)

        game_type_stats = [dict(row) for row in cursor.fetchall()]

        # Determine hypothesis
        if not game_type_stats:
            hypothesis = "INSUFFICIENT_DATA"
        elif all(
            row["success_rate"] and row["success_rate"] > 0.8 for row in game_type_stats
        ):
            hypothesis = "HEALTHY"
        elif any(
            row["success_rate"] and row["success_rate"] < 0.5 for row in game_type_stats
        ):
            worst_type = min(game_type_stats, key=lambda x: x["success_rate"] or 0)
            hypothesis = f"GAME_TYPE_SPECIFIC: {worst_type['game_type']} games failing ({worst_type['success_rate']:.1%})"
        else:
            hypothesis = "MODERATE_FAILURES: Some sequences unreliable"

        return {"hypothesis": hypothesis, "game_type_breakdown": game_type_stats}

    def generate_report(self) -> str:
        """Generate comprehensive validation monitoring report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SEQUENCE VALIDATION MONITORING REPORT")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("=" * 80)
        report_lines.append("")

        # Overall stats
        stats = self.get_validation_stats()

        if not stats.get("table_exists"):
            report_lines.append("⚠️  VALIDATION TRACKING NOT ACTIVE")
            report_lines.append(stats["message"])
            return "\n".join(report_lines)

        report_lines.append("📊 OVERALL STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Sequences Tracked: {stats['total_sequences']}")
        report_lines.append(f"Total Validation Attempts: {stats['total_attempts']}")
        report_lines.append(f"Successful Validations: {stats['total_successes']}")

        overall_rate = stats["overall_success_rate"] or 0.0
        report_lines.append(f"Overall Success Rate: {overall_rate:.1%}")

        # Alert thresholds
        if overall_rate < 0.5:
            report_lines.append("🔴 CRITICAL: Success rate below 50%!")
        elif overall_rate < 0.7:
            report_lines.append("🟡 WARNING: Success rate below 70%")
        else:
            report_lines.append("✅ HEALTHY: Success rate above 70%")

        report_lines.append("")

        # By generation
        gen_stats = self.get_validation_by_generation()
        if gen_stats:
            report_lines.append("📈 VALIDATION BY GENERATION (Last 10)")
            report_lines.append("-" * 80)
            report_lines.append(
                f"{'Gen':<6} {'Sequences':<12} {'Successes':<12} {'Attempts':<10} {'Rate':<10}"
            )
            for gen in gen_stats:
                rate = gen["success_rate"] or 0.0
                report_lines.append(
                    f"{gen['generation']:<6} {gen['sequences_validated']:<12} "
                    f"{gen['successes']:<12} {gen['attempts']:<10} {rate:.1%}"
                )
            report_lines.append("")

        # Failing games
        failing = self.get_failing_games()
        if failing:
            report_lines.append("❌ GAMES WITH LOW VALIDATION SUCCESS (<70%)")
            report_lines.append("-" * 80)
            report_lines.append(
                f"{'Game':<20} {'Level':<8} {'Seqs':<8} {'Rate':<10} {'Attempts':<10}"
            )
            for game in failing[:10]:
                rate = game["success_rate"] or 0.0
                report_lines.append(
                    f"{game['game_id']:<20} {game['level_number']:<8} "
                    f"{game['sequence_count']:<8} {rate:.1%} {game['attempts']}"
                )
            report_lines.append("")

        # Proven sequences
        proven = self.get_proven_sequences()
        if proven:
            report_lines.append("✅ PROVEN SEQUENCES (>80% validation success)")
            report_lines.append("-" * 80)
            report_lines.append(
                f"{'Game':<20} {'Level':<8} {'Rate':<10} {'Attempts':<10}"
            )
            for seq in proven[:5]:
                rate = seq["success_rate"] or 0.0
                report_lines.append(
                    f"{seq['game_id']:<20} {seq['level_number']:<8} "
                    f"{rate:.1%} {seq['total_validation_attempts']}"
                )
            report_lines.append("")

        # Failure pattern analysis
        analysis = self.analyze_failure_patterns()
        report_lines.append("🔬 FAILURE PATTERN ANALYSIS")
        report_lines.append("-" * 80)
        report_lines.append(f"Hypothesis: {analysis['hypothesis']}")

        if "game_type_breakdown" in analysis and analysis["game_type_breakdown"]:
            report_lines.append("\nBy Game Type:")
            for gt in analysis["game_type_breakdown"]:
                rate = gt["success_rate"] or 0.0
                report_lines.append(
                    f"  {gt['game_type']:<10}: {rate:.1%} ({gt['successes']}/{gt['attempts']})"
                )

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Run sequence validation monitoring and display report."""
    monitor = SequenceValidationMonitor()

    try:
        report = monitor.generate_report()
        print(report)

        # Also save to database for historical tracking
        stats = monitor.get_validation_stats()
        if stats.get("table_exists"):
            # Log monitoring run to database
            cursor = monitor.conn.cursor()
            
            # Ensure logs table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS database_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_level TEXT,
                    message TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute(
                """
                INSERT INTO database_logs (log_level, message, details)
                VALUES ('INFO', 'Sequence validation monitoring completed', ?)
            """,
                (
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "overall_success_rate": stats.get("overall_success_rate"),
                            "total_attempts": stats.get("total_attempts"),
                            "total_successes": stats.get("total_successes"),
                        }
                    ),
                ),
            )
            monitor.conn.commit()

    finally:
        monitor.close()


if __name__ == "__main__":
    main()
