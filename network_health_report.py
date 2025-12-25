#!/usr/bin/env python
"""
Network Health Report - Comprehensive metrics dashboard.

Run: python network_health_report.py
     python network_health_report.py --quick   # Just the essentials
     python network_health_report.py --json    # JSON output for automation

Based on: DOCS/Societal_Metrics_Implementation_Analysis.md
"""

import sqlite3
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path


class NetworkHealthReport:
    """Comprehensive network health metrics."""
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.results: Dict[str, Any] = {}
    
    def close(self):
        self.conn.close()
    
    # =========================================================================
    # TIER 1: CRITICAL SELF-REGULATION METRICS
    # =========================================================================
    
    def get_population_stats(self) -> Dict[str, Any]:
        """Basic population statistics."""
        self.cur.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
        active = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM agents")
        total = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT MAX(generation) FROM agents")
        max_gen = self.cur.fetchone()[0] or 0
        
        # Age distribution
        self.cur.execute("""
            SELECT 
                CASE 
                    WHEN (? - generation) <= 2 THEN 'young (0-2 gen)'
                    WHEN (? - generation) <= 10 THEN 'mature (3-10 gen)'
                    ELSE 'elder (10+ gen)'
                END as age_group,
                COUNT(*) as count
            FROM agents WHERE is_active = 1
            GROUP BY age_group
        """, (max_gen, max_gen))
        age_dist = {r['age_group']: r['count'] for r in self.cur.fetchall()}
        
        return {
            'active_agents': active,
            'total_agents': total,
            'current_generation': max_gen,
            'age_distribution': age_dist
        }
    
    def get_emergence_gain(self, lookback_gens: int = 10) -> Dict[str, Any]:
        """
        Emergence Gain: Is the network smarter than sum of individuals?
        Proxy: sequences used by agents other than discoverer / total sequence uses
        Target: > 1.0
        """
        # Sequences that have been reused (shared knowledge)
        self.cur.execute("""
            SELECT COUNT(*) as reused_count
            FROM winning_sequences
            WHERE is_active = 1 AND times_referenced > 1
        """)
        result = self.cur.fetchone()
        shared_sequences = result[0] if result else 0
        
        # Total sequences discovered
        self.cur.execute("""
            SELECT COUNT(*) as total
            FROM winning_sequences
            WHERE is_active = 1
        """)
        result = self.cur.fetchone()
        total_sequences = result[0] if result else 1
        
        # Wins in last 7 days
        self.cur.execute("""
            SELECT COUNT(*) FROM game_results
            WHERE win_detected = 1 AND created_at > datetime('now', '-7 days')
        """)
        recent_wins = self.cur.fetchone()[0]
        
        # Solo discoveries (new sequences) in last 7 days
        self.cur.execute("""
            SELECT COUNT(*) FROM winning_sequences
            WHERE discovered_at > datetime('now', '-7 days')
        """)
        solo_discoveries = self.cur.fetchone()[0] or 1
        
        # Emergence = how much shared knowledge amplifies wins
        share_rate = shared_sequences / max(total_sequences, 1)
        emergence = (recent_wins / max(solo_discoveries, 1)) * (1 + share_rate)
        
        return {
            'emergence_gain': round(emergence, 2),
            'shared_sequences': shared_sequences,
            'total_sequences': total_sequences,
            'share_rate': round(share_rate, 2),
            'recent_wins': recent_wins,
            'solo_discoveries': solo_discoveries,
            'status': 'HEALTHY' if emergence > 1.0 else 'WARNING' if emergence > 0.5 else 'CRITICAL',
            'interpretation': 'Network amplifying individual work' if emergence > 1.0 else 'Network not adding significant value'
        }
    
    def get_role_saturation(self) -> Dict[str, Any]:
        """
        Role Saturation Index: Are agent roles properly distributed?
        > 1.0 = oversaturated, < 1.0 = undersaturated
        """
        # Get most recent role distribution (latest generation per agent)
        self.cur.execute("""
            SELECT operating_mode, COUNT(DISTINCT agent_id) as count
            FROM agent_operating_modes
            WHERE generation = (SELECT MAX(generation) FROM agent_operating_modes)
            GROUP BY operating_mode
        """)
        actual = {r['operating_mode']: r['count'] for r in self.cur.fetchall()}
        total_agents = sum(actual.values()) or 1
        
        # Determine if we're in exploration or optimization mode
        self.cur.execute("""
            SELECT COUNT(*) as full_wins FROM winning_sequences_full_game WHERE is_active = 1
        """)
        full_wins = self.cur.fetchone()[0]
        
        # Get total unique game types
        self.cur.execute("""
            SELECT COUNT(DISTINCT SUBSTR(game_id, 1, 4)) as game_types 
            FROM game_results WHERE session_id IS NOT NULL
        """)
        game_types = self.cur.fetchone()[0] or 1
        
        mode = 'OPTIMIZATION' if full_wins >= game_types * 0.5 else 'EXPLORATION'
        
        ideal_ratios = {
            'EXPLORATION': {'pioneer': 0.60, 'optimizer': 0.25, 'generalist': 0.10, 'exploiter': 0.05},
            'OPTIMIZATION': {'pioneer': 0.05, 'optimizer': 0.65, 'generalist': 0.15, 'exploiter': 0.15}
        }
        
        saturation = {}
        for role, ideal_pct in ideal_ratios[mode].items():
            actual_pct = actual.get(role, 0) / total_agents
            saturation[role] = round(actual_pct / max(ideal_pct, 0.01), 2)
        
        return {
            'network_mode': mode,
            'role_distribution': {k: round(v/total_agents, 2) for k, v in actual.items()},
            'saturation_index': saturation,
            'ideal_ratios': ideal_ratios[mode],
            'issues': [f"{r} oversaturated ({s:.1f}x)" for r, s in saturation.items() if s > 1.5] +
                     [f"{r} undersaturated ({s:.1f}x)" for r, s in saturation.items() if s < 0.5]
        }
    
    def get_sequence_health(self) -> Dict[str, Any]:
        """
        Sequence System Health: Are winning sequences reliable?
        Target: success_rate > 0.7
        """
        self.cur.execute("SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1")
        partial = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM winning_sequences_full_game WHERE is_active = 1")
        full = self.cur.fetchone()[0]
        
        # Validation stats
        self.cur.execute("""
            SELECT 
                SUM(times_referenced) as total_validations,
                SUM(CASE WHEN times_referenced > 0 THEN 1 ELSE 0 END) as validated_sequences,
                COUNT(*) as total_sequences,
                AVG(success_rate_when_reused) as avg_success
            FROM winning_sequences WHERE is_active = 1
        """)
        val = self.cur.fetchone()
        
        # Recent sequence usage
        self.cur.execute("""
            SELECT COUNT(*) FROM winning_sequences 
            WHERE is_active = 1 AND last_referenced > datetime('now', '-7 days')
        """)
        recent_used = self.cur.fetchone()[0]
        
        success_rate = val[3] if val and val[3] else (val[1] / max(val[2], 1) if val else 0)
        
        return {
            'partial_sequences': partial,
            'full_game_sequences': full,
            'total_validations': val[0] if val else 0,
            'validated_sequences': val[1] if val else 0,
            'success_rate': round(success_rate, 2),
            'recently_used': recent_used,
            'status': 'HEALTHY' if success_rate > 0.7 else 'WARNING' if success_rate > 0.4 else 'CRITICAL'
        }
    
    def get_information_velocity(self) -> Dict[str, Any]:
        """
        Information Velocity: How fast does knowledge spread?
        """
        self.cur.execute("""
            SELECT 
                COUNT(*) as total_packages,
                SUM(CASE WHEN infection_count > 0 THEN 1 ELSE 0 END) as spread_packages,
                AVG(infection_count) as avg_infections,
                MAX(infection_count) as max_infections
            FROM viral_information_packages
            WHERE created_at > datetime('now', '-7 days')
        """)
        viral = self.cur.fetchone()
        
        # Pariah (failure) packages
        self.cur.execute("""
            SELECT COUNT(*) FROM pariahs WHERE is_active = 1
        """)
        pariahs = self.cur.fetchone()[0]
        
        return {
            'recent_packages': viral[0] if viral else 0,
            'packages_that_spread': viral[1] if viral else 0,
            'avg_infections': round(viral[2], 1) if viral and viral[2] else 0,
            'max_infections': viral[3] if viral else 0,
            'active_pariahs': pariahs,
            'spread_rate': round(viral[1] / max(viral[0], 1), 2) if viral else 0
        }
    
    # =========================================================================
    # TIER 2: GAME PERFORMANCE METRICS
    # =========================================================================
    
    def get_game_performance(self, limit: int = 100) -> Dict[str, Any]:
        """Recent game performance statistics."""
        self.cur.execute(f"""
            SELECT 
                COUNT(*) as games,
                SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as scored,
                SUM(CASE WHEN win_detected = 1 THEN 1 ELSE 0 END) as wins,
                AVG(final_score) as avg_score,
                AVG(total_actions) as avg_actions,
                MAX(final_score) as best_score
            FROM (SELECT * FROM game_results ORDER BY created_at DESC LIMIT {limit})
        """)
        r = self.cur.fetchone()
        
        return {
            'games_played': r[0],
            'games_with_score': r[1],
            'score_rate': round(r[1] / max(r[0], 1), 2),
            'full_wins': r[2],
            'win_rate': round(r[2] / max(r[0], 1), 3),
            'avg_score': round(r[3], 2) if r[3] else 0,
            'avg_actions': round(r[4], 1) if r[4] else 0,
            'best_score': r[5] if r[5] else 0
        }
    
    def get_game_type_breakdown(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Performance breakdown by game type."""
        self.cur.execute(f"""
            SELECT 
                SUBSTR(session_id, 1, 4) as game_type,
                COUNT(*) as attempts,
                AVG(final_score) as avg_score,
                MAX(final_score) as best_score,
                SUM(CASE WHEN win_detected = 1 THEN 1 ELSE 0 END) as wins,
                MAX(level_completions) as max_levels
            FROM game_results
            WHERE session_id IS NOT NULL AND session_id != ''
            GROUP BY SUBSTR(session_id, 1, 4)
            ORDER BY attempts DESC
            LIMIT {limit}
        """)
        
        return [
            {
                'game_type': r['game_type'],
                'attempts': r['attempts'],
                'avg_score': round(r['avg_score'], 2) if r['avg_score'] else 0,
                'best_score': r['best_score'] if r['best_score'] else 0,
                'wins': r['wins'],
                'max_levels': r['max_levels'] if r['max_levels'] else 0,
                'status': 'BEATEN' if r['wins'] > 0 else 'FRONTIER'
            }
            for r in self.cur.fetchall()
        ]
    
    def get_frontier_status(self) -> Dict[str, Any]:
        """Which games are beaten vs frontier?"""
        # Beaten game types (have full game win)
        self.cur.execute("""
            SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type
            FROM winning_sequences_full_game WHERE is_active = 1
        """)
        beaten = set(r[0] for r in self.cur.fetchall())
        
        # All attempted game types
        self.cur.execute("""
            SELECT DISTINCT SUBSTR(session_id, 1, 4) as game_type
            FROM game_results WHERE session_id IS NOT NULL AND session_id != ''
        """)
        all_types = set(r[0] for r in self.cur.fetchall())
        
        frontier = all_types - beaten
        
        return {
            'beaten_games': len(beaten),
            'frontier_games': len(frontier),
            'beaten_list': sorted(beaten),
            'frontier_list': sorted(frontier),
            'completion_rate': round(len(beaten) / max(len(all_types), 1), 2)
        }
    
    # =========================================================================
    # TIER 3: CODS & LEARNING METRICS
    # =========================================================================
    
    def get_cods_status(self) -> Dict[str, Any]:
        """CODS (Cognitive Operator Discovery System) status."""
        self.cur.execute("SELECT COUNT(*) FROM cods_game_outcomes")
        game_outcomes = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM cods_level_outcomes")
        level_outcomes = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM cods_failure_analyses")
        failure_analyses = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT primitive_name, status, times_used, avg_success_rate
            FROM primitive_status 
            ORDER BY times_used DESC LIMIT 10
        """)
        top_primitives = [
            {'name': r[0], 'status': r[1], 'uses': r[2], 'success': round(r[3], 2) if r[3] else 0}
            for r in self.cur.fetchall()
        ]
        
        self.cur.execute("SELECT COUNT(*) FROM primitive_status WHERE status = 'unlocked'")
        unlocked = self.cur.fetchone()[0]
        
        return {
            'game_outcomes_tracked': game_outcomes,
            'level_outcomes_tracked': level_outcomes,
            'failure_analyses': failure_analyses,
            'primitives_unlocked': unlocked,
            'top_primitives': top_primitives,
            'status': 'ACTIVE' if game_outcomes > 0 else 'INACTIVE'
        }
    
    def get_cognitive_development(self) -> Dict[str, Any]:
        """Agent cognitive development stages."""
        self.cur.execute("""
            SELECT current_stage, COUNT(*) 
            FROM agent_cognitive_stages 
            GROUP BY current_stage
        """)
        stages = {r[0]: r[1] for r in self.cur.fetchall()}
        
        self.cur.execute("SELECT COUNT(*) FROM agent_hypotheses WHERE status = 'active'")
        active_hyp = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM agent_hypotheses WHERE status = 'validated'")
        validated_hyp = self.cur.fetchone()[0]
        
        return {
            'stage_distribution': stages,
            'active_hypotheses': active_hyp,
            'validated_hypotheses': validated_hyp,
            'formal_operational_agents': stages.get('formal_operational', 0)
        }
    
    # =========================================================================
    # TIER 4: NETWORK HEALTH METRICS
    # =========================================================================
    
    def get_frustration_status(self) -> Dict[str, Any]:
        """Frustration detection - stuck agents."""
        self.cur.execute("SELECT COUNT(*) FROM agent_frustration_states WHERE is_frustrated = 1")
        frustrated = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM frustration_quorum_events")
        quorums = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM frustration_resolutions")
        resolutions = self.cur.fetchone()[0]
        
        return {
            'currently_frustrated': frustrated,
            'quorum_events': quorums,
            'resolutions': resolutions,
            'resolution_rate': round(resolutions / max(quorums, 1), 2)
        }
    
    def get_prestige_distribution(self) -> Dict[str, Any]:
        """Prestige distribution - vampire detection."""
        self.cur.execute("""
            SELECT 
                agent_id,
                discovery_prestige,
                innovation_score,
                validation_reputation
            FROM agents 
            WHERE is_active = 1 AND discovery_prestige > 0
            ORDER BY discovery_prestige DESC
            LIMIT 10
        """)
        top_agents = [
            {'agent': r[0][:12], 'prestige': round(r[1], 2), 
             'innovation': round(r[2], 2) if r[2] else 0,
             'validation': round(r[3], 2) if r[3] else 0}
            for r in self.cur.fetchall()
        ]
        
        # Gini coefficient for prestige
        self.cur.execute("""
            SELECT discovery_prestige FROM agents WHERE is_active = 1 AND discovery_prestige > 0
        """)
        scores = sorted([r[0] for r in self.cur.fetchall()])
        
        gini = 0.0
        if scores:
            n = len(scores)
            index_sum = sum((i + 1) * score for i, score in enumerate(scores))
            total = sum(scores)
            if total > 0:
                gini = (2 * index_sum) / (n * total) - (n + 1) / n
        
        return {
            'top_agents': top_agents,
            'gini_coefficient': round(gini, 3),
            'concentration': 'LOW' if gini < 0.3 else 'MODERATE' if gini < 0.5 else 'HIGH',
            'vampire_risk': gini > 0.6
        }
    
    def get_identity_drift(self) -> Dict[str, Any]:
        """
        Functional Identity Drift: Are we optimizing the right things?
        Target: < 0.3
        """
        # Positive: Frontier progress
        self.cur.execute("""
            SELECT COUNT(DISTINCT game_id || '-' || level_number)
            FROM winning_sequences 
            WHERE discovered_at > datetime('now', '-7 days')
        """)
        frontier_progress = self.cur.fetchone()[0]
        
        # Negative signals
        self.cur.execute("""
            SELECT COUNT(*) FROM game_results 
            WHERE final_score = 0 AND created_at > datetime('now', '-7 days')
        """)
        zero_score_games = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT COUNT(*) FROM winning_sequences 
            WHERE is_active = 1 AND times_referenced = 0 
              AND discovered_at < datetime('now', '-3 days')
        """)
        unused_sequences = self.cur.fetchone()[0]
        
        drift = (zero_score_games + unused_sequences) / max(frontier_progress * 10, 1)
        drift = min(1.0, drift)
        
        return {
            'drift_score': round(drift, 2),
            'frontier_progress_week': frontier_progress,
            'zero_score_games': zero_score_games,
            'unused_sequences': unused_sequences,
            'status': 'HEALTHY' if drift < 0.3 else 'WARNING' if drift < 0.5 else 'CRITICAL',
            'interpretation': 'Optimizing correct goals' if drift < 0.3 else 'Possible goal drift detected'
        }
    
    # =========================================================================
    # HUMAN SPOT-CHECK DASHBOARD
    # =========================================================================
    
    def get_quick_health_snapshot(self) -> Dict[str, Any]:
        """Quick snapshot for human review."""
        self.cur.execute("""
            SELECT 
                (SELECT COUNT(DISTINCT game_id || '-' || CAST(level_number AS TEXT)) 
                 FROM winning_sequences WHERE discovered_at > datetime('now', '-7 days')) as new_levels_week,
                (SELECT COUNT(*) FROM agents WHERE is_active = 1) as active_agents,
                (SELECT AVG(final_score) FROM game_results 
                 WHERE created_at > datetime('now', '-24 hours')) as avg_score_24h,
                (SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1) as total_sequences,
                (SELECT COUNT(*) FROM winning_sequences_full_game WHERE is_active = 1) as full_game_wins,
                (SELECT MAX(generation) FROM agents) as current_generation
        """)
        r = self.cur.fetchone()
        
        return {
            'new_levels_this_week': r[0] if r[0] else 0,
            'active_agents': r[1] if r[1] else 0,
            'avg_score_24h': round(r[2], 2) if r[2] else 0,
            'total_sequences': r[3] if r[3] else 0,
            'full_game_wins': r[4] if r[4] else 0,
            'current_generation': r[5] if r[5] else 0
        }
    
    def check_red_flags(self) -> List[Dict[str, Any]]:
        """Check for red flags requiring immediate attention."""
        flags = []
        
        # Check for zero frontier progress
        self.cur.execute("""
            SELECT COUNT(*) FROM winning_sequences 
            WHERE discovered_at > datetime('now', '-3 days')
        """)
        recent_discoveries = self.cur.fetchone()[0]
        if recent_discoveries == 0:
            flags.append({
                'severity': 'HIGH',
                'issue': 'No new frontier discoveries in 3 days',
                'action': 'Check if system is stuck or only optimizing'
            })
        
        # Check sequence success rate
        seq = self.get_sequence_health()
        if seq['success_rate'] < 0.4:
            flags.append({
                'severity': 'HIGH',
                'issue': f"Sequence success rate critically low ({seq['success_rate']})",
                'action': 'Review and prune failing sequences'
            })
        
        # Check CODS status
        cods = self.get_cods_status()
        if cods['status'] == 'INACTIVE':
            flags.append({
                'severity': 'HIGH',
                'issue': 'CODS not recording any data',
                'action': 'Check CODS initialization (set_context bug?)'
            })
        
        # Check identity drift
        drift = self.get_identity_drift()
        if drift['drift_score'] > 0.5:
            flags.append({
                'severity': 'MEDIUM',
                'issue': f"Identity drift detected ({drift['drift_score']})",
                'action': 'System may be optimizing wrong metrics'
            })
        
        # Check prestige concentration
        prestige = self.get_prestige_distribution()
        if prestige['vampire_risk']:
            flags.append({
                'severity': 'MEDIUM',
                'issue': f"High prestige concentration (Gini: {prestige['gini_coefficient']})",
                'action': 'Check for prestige vampires'
            })
        
        return flags
    
    # =========================================================================
    # FULL REPORT
    # =========================================================================
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        return {
            'generated_at': datetime.now().isoformat(),
            'population': self.get_population_stats(),
            'emergence': self.get_emergence_gain(),
            'roles': self.get_role_saturation(),
            'sequences': self.get_sequence_health(),
            'information_flow': self.get_information_velocity(),
            'game_performance': self.get_game_performance(),
            'game_types': self.get_game_type_breakdown(),
            'frontier': self.get_frontier_status(),
            'cods': self.get_cods_status(),
            'cognitive': self.get_cognitive_development(),
            'frustration': self.get_frustration_status(),
            'prestige': self.get_prestige_distribution(),
            'identity_drift': self.get_identity_drift(),
            'snapshot': self.get_quick_health_snapshot(),
            'red_flags': self.check_red_flags()
        }
    
    def print_report(self, quick: bool = False):
        """Print human-readable report."""
        print("=" * 60)
        print("  NETWORK HEALTH REPORT")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Quick snapshot
        snap = self.get_quick_health_snapshot()
        print(f"\n[SNAPSHOT] Gen {snap['current_generation']} | "
              f"{snap['active_agents']} agents | "
              f"{snap['total_sequences']} sequences | "
              f"{snap['full_game_wins']} full wins")
        print(f"           New levels this week: {snap['new_levels_this_week']} | "
              f"24h avg score: {snap['avg_score_24h']}")
        
        # Red flags
        flags = self.check_red_flags()
        if flags:
            print(f"\n{'!'*60}")
            print("  RED FLAGS DETECTED")
            print('!'*60)
            for f in flags:
                print(f"  [{f['severity']}] {f['issue']}")
                print(f"         Action: {f['action']}")
        else:
            print("\n[OK] No red flags detected")
        
        if quick:
            return
        
        # Population
        pop = self.get_population_stats()
        print(f"\n--- POPULATION ---")
        print(f"  Active: {pop['active_agents']} / {pop['total_agents']} total")
        print(f"  Generation: {pop['current_generation']}")
        print(f"  Age dist: {pop['age_distribution']}")
        
        # Emergence
        em = self.get_emergence_gain()
        print(f"\n--- EMERGENCE ({em['status']}) ---")
        print(f"  Emergence gain: {em['emergence_gain']} (target: > 1.0)")
        print(f"  Shared seqs: {em['shared_sequences']} / {em['total_sequences']} ({em['share_rate']*100:.0f}%)")
        print(f"  Recent wins: {em['recent_wins']} | New discoveries: {em['solo_discoveries']}")
        print(f"  {em['interpretation']}")
        
        # Roles
        roles = self.get_role_saturation()
        print(f"\n--- ROLES ({roles['network_mode']} mode) ---")
        print(f"  Distribution: {roles['role_distribution']}")
        print(f"  Saturation: {roles['saturation_index']}")
        if roles['issues']:
            for issue in roles['issues']:
                print(f"  [!] {issue}")
        
        # Sequences
        seq = self.get_sequence_health()
        print(f"\n--- SEQUENCES ({seq['status']}) ---")
        print(f"  Partial: {seq['partial_sequences']} | Full game: {seq['full_game_sequences']}")
        print(f"  Success rate: {seq['success_rate']} (target: > 0.7)")
        print(f"  Recently used: {seq['recently_used']}")
        
        # Game performance
        perf = self.get_game_performance()
        print(f"\n--- GAME PERFORMANCE (last 100) ---")
        print(f"  Games: {perf['games_played']} | Scored: {perf['games_with_score']} ({perf['score_rate']*100:.0f}%)")
        print(f"  Wins: {perf['full_wins']} ({perf['win_rate']*100:.1f}%)")
        print(f"  Avg score: {perf['avg_score']} | Best: {perf['best_score']}")
        
        # Frontier
        front = self.get_frontier_status()
        print(f"\n--- FRONTIER STATUS ---")
        print(f"  Beaten: {front['beaten_games']} | Frontier: {front['frontier_games']}")
        print(f"  Completion: {front['completion_rate']*100:.0f}%")
        if front['frontier_list']:
            print(f"  Frontier games: {', '.join(front['frontier_list'][:10])}")
        
        # CODS
        cods = self.get_cods_status()
        print(f"\n--- CODS ({cods['status']}) ---")
        print(f"  Game outcomes: {cods['game_outcomes_tracked']} | Level outcomes: {cods['level_outcomes_tracked']}")
        print(f"  Primitives unlocked: {cods['primitives_unlocked']}")
        
        # Cognitive development
        cog = self.get_cognitive_development()
        print(f"\n--- COGNITIVE DEVELOPMENT ---")
        print(f"  Stages: {cog['stage_distribution']}")
        print(f"  Hypotheses: {cog['active_hypotheses']} active | {cog['validated_hypotheses']} validated")
        
        # Prestige
        pres = self.get_prestige_distribution()
        print(f"\n--- PRESTIGE ({pres['concentration']}) ---")
        print(f"  Gini: {pres['gini_coefficient']} | Vampire risk: {pres['vampire_risk']}")
        if pres['top_agents']:
            print(f"  Top: {pres['top_agents'][0]}")
        
        # Identity drift
        drift = self.get_identity_drift()
        print(f"\n--- IDENTITY DRIFT ({drift['status']}) ---")
        print(f"  Drift score: {drift['drift_score']} (target: < 0.3)")
        print(f"  {drift['interpretation']}")
        
        # Game type breakdown
        print(f"\n--- GAME TYPE BREAKDOWN ---")
        for g in self.get_game_type_breakdown(10):
            status = '[WIN]' if g['wins'] > 0 else '[---]'
            print(f"  {status} {g['game_type']}: {g['attempts']} tries, "
                  f"avg={g['avg_score']}, best={g['best_score']}, max_L={g['max_levels']}")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Network Health Report')
    parser.add_argument('--quick', action='store_true', help='Quick summary only')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--db', default='core_data.db', help='Database path')
    args = parser.parse_args()
    
    report = NetworkHealthReport(args.db)
    
    try:
        if args.json:
            data = report.generate_full_report()
            print(json.dumps(data, indent=2, default=str))
        else:
            report.print_report(quick=args.quick)
    finally:
        report.close()


if __name__ == '__main__':
    main()
