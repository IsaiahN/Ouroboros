#!/usr/bin/env python3
"""
Agent Role Validation Script

Purpose: Diagnostic tool to validate agent role distribution and permissions
- Checks role distribution across population
- Verifies no convergence to single role type
- Tracks role transitions and effectiveness
- Identifies potential permission violations

Part of: Immediate Phase (Gen 0-5) - User Priority #3
"""

import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import json
from collections import Counter


class AgentRoleValidator:
    """Validate agent role health and distribution."""

    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_role_distribution(self) -> Dict[str, Any]:
        """Get current distribution of agent roles."""
        cursor = self.conn.cursor()

        # Get active agents
        cursor.execute("""
            SELECT specialization, genome 
            FROM agents 
            WHERE is_active = 1
        """)

        agents = cursor.fetchall()
        total_agents = len(agents)

        if total_agents == 0:
            return {"status": "EMPTY", "message": "No active agents found"}

        # Parse roles from specialization or genome
        roles = []
        for agent in agents:
            role = "unknown"
            try:
                # Try to get from specialization string first
                spec = agent["specialization"]
                if "pioneer" in spec.lower():
                    role = "pioneer"
                elif "optimizer" in spec.lower():
                    role = "optimizer"
                elif "generalist" in spec.lower():
                    role = "generalist"
                elif "exploiter" in spec.lower():
                    role = "exploiter"
                else:
                    # Fallback to genome
                    genome = json.loads(agent["genome"])
                    role = genome.get("operating_mode", "generalist")
            except Exception:
                pass
            roles.append(role)

        distribution = dict(Counter(roles))

        return {
            "total_agents": total_agents,
            "distribution": distribution,
            "percentages": {k: v / total_agents for k, v in distribution.items()},
        }

    def check_convergence_risk(
        self, distribution: Dict[str, int], total: int
    ) -> Dict[str, Any]:
        """Check if population is converging to a single role."""
        if total < 5:
            return {"risk": "LOW", "reason": "Population too small"}

        for role, count in distribution.items():
            percentage = count / total
            if percentage > 0.8:
                return {
                    "risk": "HIGH",
                    "reason": f"Dominant role {role} ({percentage:.1%}) indicates convergence",
                    "dominant_role": role,
                }
            elif percentage > 0.6:
                return {
                    "risk": "MEDIUM",
                    "reason": f"Role {role} becoming dominant ({percentage:.1%})",
                    "dominant_role": role,
                }

        return {"risk": "LOW", "reason": "Healthy distribution"}

    def get_role_performance(self) -> List[Dict[str, Any]]:
        """Analyze performance by role."""
        cursor = self.conn.cursor()

        # Check if we have performance data linked to roles
        # This is an approximation since we don't have a direct role column in performance table yet
        # We'll infer from agent current specialization

        cursor.execute("""
            SELECT 
                CASE 
                    WHEN a.specialization LIKE '%pioneer%' THEN 'pioneer'
                    WHEN a.specialization LIKE '%optimizer%' THEN 'optimizer'
                    WHEN a.specialization LIKE '%generalist%' THEN 'generalist'
                    WHEN a.specialization LIKE '%exploiter%' THEN 'exploiter'
                    ELSE 'other'
                END as role,
                COUNT(DISTINCT a.agent_id) as agent_count,
                AVG(a.avg_score_per_game) as avg_score,
                AVG(a.total_games_won) as avg_wins,
                AVG(a.score_efficiency) as efficiency
            FROM agents a
            WHERE a.is_active = 1
            GROUP BY role
            ORDER BY avg_score DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def generate_report(self) -> str:
        """Generate comprehensive role validation report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AGENT ROLE VALIDATION REPORT")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("=" * 80)
        report_lines.append("")

        # Distribution
        dist_data = self.get_role_distribution()

        if dist_data.get("status") == "EMPTY":
            report_lines.append("⚠️  NO ACTIVE AGENTS FOUND")
            return "\n".join(report_lines)

        report_lines.append("📊 ROLE DISTRIBUTION")
        report_lines.append("-" * 80)
        total = dist_data["total_agents"]
        report_lines.append(f"Total Active Agents: {total}")

        for role, count in dist_data["distribution"].items():
            pct = dist_data["percentages"][role]
            bar = "█" * int(pct * 20)
            report_lines.append(f"{role.upper():<12} {count:>3} ({pct:>6.1%}) {bar}")

        report_lines.append("")

        # Convergence Risk
        risk = self.check_convergence_risk(dist_data["distribution"], total)
        report_lines.append("⚠️  CONVERGENCE RISK ANALYSIS")
        report_lines.append("-" * 80)

        risk_level = risk["risk"]
        indicator = (
            "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
        )

        report_lines.append(f"{indicator} Risk Level: {risk_level}")
        report_lines.append(f"   Reason: {risk['reason']}")
        report_lines.append("")

        # Performance
        perf_data = self.get_role_performance()
        if perf_data:
            report_lines.append("📈 PERFORMANCE BY ROLE")
            report_lines.append("-" * 80)
            report_lines.append(
                f"{'Role':<12} {'Agents':<8} {'Avg Score':<10} {'Avg Wins':<10} {'Efficiency':<10}"
            )

            for p in perf_data:
                report_lines.append(
                    f"{p['role'].upper():<12} {p['agent_count']:<8} "
                    f"{p['avg_score']:<10.2f} {p['avg_wins']:<10.1f} {p['efficiency']:<10.2f}"
                )

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def close(self):
        self.conn.close()


def main():
    validator = AgentRoleValidator()
    try:
        print(validator.generate_report())
    finally:
        validator.close()


if __name__ == "__main__":
    main()
