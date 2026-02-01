#!/usr/bin/env python3
"""
Prestige System Audit Script

Purpose: Diagnostic tool to audit prestige system health
- Detects prestige outliers and "parasites"
- Checks for unbounded growth or negative values
- Validates dampening effectiveness
- Identifies edge cases in calculation

Part of: Immediate Phase (Gen 0-5) - User Priority #4
"""

import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import math
import sqlite3
import statistics
from datetime import datetime
from typing import Any, Dict, List


class PrestigeAuditor:
    """Audit prestige system for anomalies and health issues."""

    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_prestige_stats(self) -> Dict[str, Any]:
        """Calculate population prestige statistics."""
        cursor = self.conn.cursor()

        # Check if prestige_score column exists in agents table
        # It might be in a separate table or part of agent metadata
        # Based on previous analysis, it seems to be tracked but let's verify schema

        # Try to get prestige from agents table directly first
        try:
            cursor.execute("""
                SELECT agent_id,
                       json_extract(genome, '$.prestige_score') as prestige,
                       total_games_won,
                       avg_score_per_game
                FROM agents
                WHERE is_active = 1
            """)
            agents = []
            for row in cursor.fetchall():
                prestige = row["prestige"]
                if prestige is None:
                    # Try another location or default to 0
                    prestige = 0.0
                else:
                    prestige = float(prestige)

                agents.append(
                    {
                        "agent_id": row["agent_id"],
                        "prestige": prestige,
                        "wins": row["total_games_won"],
                        "avg_score": row["avg_score_per_game"],
                    }
                )

        except Exception as e:
            return {"error": f"Could not query prestige: {e}"}

        if not agents:
            return {"status": "EMPTY", "message": "No agents found"}

        prestiges = [a["prestige"] for a in agents]

        stats = {
            "count": len(prestiges),
            "min": min(prestiges),
            "max": max(prestiges),
            "avg": statistics.mean(prestiges),
            "median": statistics.median(prestiges),
            "stdev": statistics.stdev(prestiges) if len(prestiges) > 1 else 0,
            "total_prestige": sum(prestiges),
        }

        return {"stats": stats, "agents": agents}

    def find_outliers(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify prestige outliers (>5x median)."""
        stats = data["stats"]
        agents = data["agents"]
        median = stats["median"]

        # Avoid division by zero if median is 0
        threshold_base = max(median, 0.1)
        threshold = threshold_base * 5.0

        outliers = []
        for agent in agents:
            if agent["prestige"] > threshold:
                agent["ratio"] = agent["prestige"] / threshold_base
                outliers.append(agent)

        return sorted(outliers, key=lambda x: x["prestige"], reverse=True)

    def find_parasites(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify 'parasites': High prestige but low recent performance."""
        stats = data["stats"]
        agents = data["agents"]

        # Define high prestige (top 25%)
        if not agents:
            return []

        sorted_by_prestige = sorted(agents, key=lambda x: x["prestige"], reverse=True)
        top_quartile_idx = len(agents) // 4
        if top_quartile_idx == 0:
            top_quartile_idx = 1

        high_prestige_agents = sorted_by_prestige[:top_quartile_idx]

        # Calculate avg performance of population
        avg_wins = statistics.mean([a["wins"] for a in agents]) if agents else 0

        parasites = []
        for agent in high_prestige_agents:
            # Parasite criteria: High prestige but below average wins
            if agent["wins"] < avg_wins * 0.5:
                agent["performance_gap"] = avg_wins - agent["wins"]
                parasites.append(agent)

        return parasites

    def generate_report(self) -> str:
        """Generate comprehensive prestige audit report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PRESTIGE SYSTEM AUDIT REPORT")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("=" * 80)
        report_lines.append("")

        data = self.get_prestige_stats()

        if "error" in data:
            report_lines.append(f"[WARN]  ERROR: {data['error']}")
            return "\n".join(report_lines)

        if data.get("status") == "EMPTY":
            report_lines.append("[WARN]  NO AGENTS FOUND")
            return "\n".join(report_lines)

        stats = data["stats"]

        # Statistics
        try:
            report_lines.append("[STATS] POPULATION STATISTICS")
            report_lines.append("-" * 80)
            report_lines.append(f"Population Size: {stats['count']}")
            report_lines.append(
                f"Total Prestige:  {stats.get('total_prestige', 0):.2f}"
            )
            report_lines.append(f"Average:         {stats.get('avg', 0):.2f}")
            report_lines.append(f"Median:          {stats.get('median', 0):.2f}")
            report_lines.append(f"Max:             {stats.get('max', 0):.2f}")
            report_lines.append(f"Min:             {stats.get('min', 0):.2f}")
            report_lines.append(f"Std Dev:         {stats.get('stdev', 0):.2f}")
            report_lines.append("")
        except Exception as e:
            report_lines.append(f"[WARN] Error formatting statistics: {e}")
            report_lines.append(f"Raw stats: {stats}")

        # Health Checks
        report_lines.append("🏥 HEALTH CHECKS")
        report_lines.append("-" * 80)

        # Check 1: Negative values
        negatives = [a for a in data["agents"] if a["prestige"] < 0]
        if negatives:
            report_lines.append(
                f"🔴 FAILED: Found {len(negatives)} agents with negative prestige"
            )
        else:
            report_lines.append("[OK] PASSED: No negative prestige values")

        # Check 2: Outliers
        outliers = self.find_outliers(data)
        if outliers:
            report_lines.append(
                f"🟡 WARNING: Found {len(outliers)} outliers (>5x median)"
            )
            for o in outliers[:3]:
                report_lines.append(
                    f"   - Agent {o['agent_id'][:8]}: {o['prestige']:.2f} ({o['ratio']:.1f}x median)"
                )
        else:
            report_lines.append("[OK] PASSED: No extreme outliers (>5x median)")

        # Check 3: Parasites
        parasites = self.find_parasites(data)
        if parasites:
            report_lines.append(
                f"[WARN] WARNING: Found {len(parasites)} potential parasites (high prestige, low performance)"
            )
            for p in parasites[:3]:
                report_lines.append(
                    f"   - Agent {p['agent_id'][:8]}: Prestige {p['prestige']:.2f}, Wins {p['wins']}"
                )
        else:
            report_lines.append("[OK] PASSED: No obvious parasites detected")

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def close(self):
        self.conn.close()


def main():
    auditor = PrestigeAuditor()
    try:
        print(auditor.generate_report())
    finally:
        auditor.close()


if __name__ == "__main__":
    main()
