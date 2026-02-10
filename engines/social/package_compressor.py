import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Package Compressor - Viral Package Clustering and Template Extraction
=====================================================================

Clusters similar viral packages by sequence alignment, merges them into
template packages with wildcards, and marks originals as merged.

This IS the compression that forces abstraction: when individual packages
are merged, only the invariant structure survives. The specific details
that varied are replaced with wildcards. General principles emerge.

Following Rule 2: All data in database (no log files).
Following Rule 3: Enhances existing viral_information_packages, no replace.
Following Rule 10: No duplicate functionality.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sequence alignment utilities
# ---------------------------------------------------------------------------

def _lcs_length(a: List, b: List) -> int:
    """Longest Common Subsequence length (dynamic programming)."""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0
    # Space-optimized: only keep two rows
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (n + 1)
    return prev[n]


def sequence_similarity(a: List, b: List) -> float:
    """Normalized LCS similarity between two sequences. 0.0-1.0."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    lcs = _lcs_length(a, b)
    return (2.0 * lcs) / (len(a) + len(b))


def _extract_actions(raw: Any) -> List:
    """Parse action_sequence from DB (JSON string or list)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


# ---------------------------------------------------------------------------
# Template extraction
# ---------------------------------------------------------------------------

def build_template_from_cluster(sequences: List[List]) -> Tuple[List, List[int], List[int]]:
    """Build a template from a cluster of similar action sequences.

    This is the *social-layer* invariant/variant detection, operating on
    raw action lists from viral packages.  It complements the richer
    *planning-layer* implementation in
    ``engines.planning.sequence_abstraction`` which adds coordinate
    analysis, gap tolerance, and concept-discovery notifications.
    The two implementations intentionally target different data types:

    - **Here (package_compressor)**: lightweight, list-of-ints, clustering
    - **sequence_abstraction**: rich, DB-backed, relational-pattern aware

    Returns:
        (template, invariant_positions, variant_positions)
        template: list where each element is the consensus action or '*' (wildcard)
        invariant_positions: indices that are fixed across all sequences
        variant_positions: indices that vary
    """
    if not sequences:
        return [], [], []

    min_len = min(len(s) for s in sequences)
    template = []
    invariants = []
    variants = []

    for pos in range(min_len):
        actions_at_pos = [s[pos] for s in sequences if pos < len(s)]
        unique = set(actions_at_pos)
        if len(unique) == 1:
            template.append(actions_at_pos[0])
            invariants.append(pos)
        else:
            # Most common action as default, marked as variant
            most_common = max(unique, key=lambda x: actions_at_pos.count(x))
            template.append(most_common)
            variants.append(pos)

    return template, invariants, variants


# ---------------------------------------------------------------------------
# Main compressor
# ---------------------------------------------------------------------------

class PackageCompressor:
    """Clusters and compresses similar viral packages.

    Usage:
        compressor = PackageCompressor(db)
        stats = compressor.compress_packages(game_type='ls20', similarity_threshold=0.85)
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db

    def compress_packages(
        self,
        game_type: Optional[str] = None,
        similarity_threshold: float = 0.85,
        min_cluster_size: int = 2,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Cluster similar viral packages and merge into templates.

        Args:
            game_type: Restrict to a specific game type (None = all).
            similarity_threshold: LCS similarity required to cluster (0.0-1.0).
            min_cluster_size: Minimum packages to form a cluster.
            dry_run: If True, report what would happen without mutating.

        Returns:
            Dict with compression statistics.
        """
        stats = {
            'packages_scanned': 0,
            'clusters_found': 0,
            'templates_created': 0,
            'packages_merged': 0,
            'dry_run': dry_run,
        }

        # Load active packages with action sequences
        where_clause = "WHERE is_active = 1 AND action_sequence IS NOT NULL"
        params: tuple = ()
        if game_type:
            where_clause += " AND (frontier_game_type = ? OR package_name LIKE ?)"
            params = (game_type, f"%{game_type}%")

        rows = self.db.execute_query(f"""
            SELECT package_id, package_name, package_type, action_sequence,
                   virulence, avg_score_contribution, total_infections,
                   generation_discovered, source_sequence_id,
                   frontier_game_type
            FROM viral_information_packages
            {where_clause}
            ORDER BY avg_score_contribution DESC
        """, params)

        if not rows:
            return stats

        # Parse sequences
        packages = []
        for row in rows:
            actions = _extract_actions(row.get('action_sequence'))
            if len(actions) < 2:
                continue  # Skip trivially short
            packages.append({**row, '_actions': actions})

        stats['packages_scanned'] = len(packages)
        if len(packages) < min_cluster_size:
            return stats

        # Greedy clustering by pairwise similarity
        used = set()
        clusters: List[List[Dict]] = []

        for i, pkg_a in enumerate(packages):
            if i in used:
                continue
            cluster = [pkg_a]
            used.add(i)
            for j, pkg_b in enumerate(packages):
                if j in used:
                    continue
                sim = sequence_similarity(pkg_a['_actions'], pkg_b['_actions'])
                if sim >= similarity_threshold:
                    cluster.append(pkg_b)
                    used.add(j)

            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)

        stats['clusters_found'] = len(clusters)
        if not clusters:
            return stats

        # Merge each cluster into a template package
        for cluster in clusters:
            if dry_run:
                stats['templates_created'] += 1
                stats['packages_merged'] += len(cluster)
                continue

            self._merge_cluster(cluster)
            stats['templates_created'] += 1
            stats['packages_merged'] += len(cluster)

        logger.info(
            f"[COMPRESS] {stats['templates_created']} templates from "
            f"{stats['packages_merged']} packages "
            f"({stats['clusters_found']} clusters)"
        )

        return stats

    def _merge_cluster(self, cluster: List[Dict]) -> Optional[str]:
        """Merge a cluster of similar packages into one template package.

        Returns template_id or None on failure.
        """
        sequences = [pkg['_actions'] for pkg in cluster]
        template_seq, invariant_pos, variant_pos = build_template_from_cluster(sequences)
        if not template_seq:
            return None

        # Aggregate metrics from cluster
        best_virulence = max(pkg.get('virulence', 0.5) for pkg in cluster)
        best_score = max(pkg.get('avg_score_contribution', 0.0) for pkg in cluster)
        total_infections = sum(pkg.get('total_infections', 0) for pkg in cluster)
        earliest_gen = min(pkg.get('generation_discovered', 0) for pkg in cluster)
        game_type = cluster[0].get('frontier_game_type', '')

        # Build template with wildcard notation for storage
        template_with_wildcards = []
        for pos, act in enumerate(template_seq):
            if pos in variant_pos:
                template_with_wildcards.append(f"*{act}")  # Wildcard with default
            else:
                template_with_wildcards.append(act)

        template_id = f"tpkg_{uuid.uuid4().hex[:12]}"
        member_ids = [pkg['package_id'] for pkg in cluster]

        try:
            self.db.execute_query("""
                INSERT INTO viral_information_packages (
                    package_id, package_name, package_type, action_sequence,
                    virulence, avg_score_contribution, total_infections,
                    generation_discovered, discovery_generation,
                    is_active, frontier_game_type
                ) VALUES (?, ?, 'template', ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                template_id,
                f"template_{game_type}_{len(cluster)}pkg",
                json.dumps(template_with_wildcards),
                best_virulence,
                best_score,
                total_infections,
                earliest_gen,
                earliest_gen,
                game_type or '',
            ))

            # Mark originals as merged
            for pkg in cluster:
                self.db.execute_query("""
                    UPDATE viral_information_packages
                    SET is_active = 0,
                        deactivated_reason = ?
                    WHERE package_id = ?
                """, (
                    f"merged_into={template_id}",
                    pkg['package_id'],
                ))

            logger.info(
                f"[COMPRESS] Template {template_id[:16]}: "
                f"{len(invariant_pos)} invariants, {len(variant_pos)} variants "
                f"from {len(cluster)} packages"
            )

            return template_id

        except Exception as e:
            logger.error(f"[COMPRESS] Merge failed: {e}")
            return None

    def compress_winning_sequences(
        self,
        game_type: Optional[str] = None,
        similarity_threshold: float = 0.85,
        min_cluster_size: int = 3,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Cluster and generalize winning_sequences for the same game/level.

        Creates generalized entries in sequence_concepts with invariant
        structure extracted from clusters of similar sequences.

        Returns compression statistics.
        """
        stats = {
            'sequences_scanned': 0,
            'game_levels_processed': 0,
            'concepts_created': 0,
            'dry_run': dry_run,
        }

        # Get distinct game_type + level combos
        where = "WHERE is_active = 1"
        params: tuple = ()
        if game_type:
            where += " AND game_type = ?"
            params = (game_type,)

        combos = self.db.execute_query(f"""
            SELECT game_type, level_number, COUNT(*) as seq_count
            FROM winning_sequences
            {where}
            GROUP BY game_type, level_number
            HAVING seq_count >= ?
            ORDER BY seq_count DESC
        """, (*params, min_cluster_size))

        if not combos:
            return stats

        for combo in combos:
            gt = combo['game_type']
            level = combo['level_number']

            rows = self.db.execute_query("""
                SELECT sequence_id, action_sequence, total_actions,
                       efficiency_score
                FROM winning_sequences
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY efficiency_score DESC
                LIMIT 20
            """, (gt, level))

            if not rows:
                continue

            parsed = []
            for r in rows:
                actions = _extract_actions(r.get('action_sequence'))
                if actions:
                    parsed.append({'actions': actions, 'seq_id': r['sequence_id']})

            stats['sequences_scanned'] += len(parsed)
            stats['game_levels_processed'] += 1

            if len(parsed) < min_cluster_size:
                continue

            # Build template from all sequences for this level
            all_actions = [p['actions'] for p in parsed]
            template, inv_pos, var_pos = build_template_from_cluster(all_actions)

            if not template:
                continue

            if dry_run:
                stats['concepts_created'] += 1
                continue

            # Store as sequence_concept
            concept_id = f"seqc_{uuid.uuid4().hex[:12]}"
            best_seq_id = parsed[0]['seq_id']  # Highest efficiency

            try:
                # Build descriptive fields
                invariant_desc = json.dumps([
                    {'pos': p, 'action': template[p]}
                    for p in inv_pos
                ])
                variant_desc = json.dumps([
                    {'pos': p, 'default': template[p]}
                    for p in var_pos
                ])

                self.db.execute_query("""
                    INSERT OR REPLACE INTO sequence_concepts (
                        concept_id, sequence_id, layout_signature,
                        goal_type, movement_pattern, constraints,
                        abstraction_level, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    concept_id,
                    best_seq_id,
                    json.dumps(template),  # layout_signature = template
                    f"{gt}_L{level}",
                    invariant_desc,        # movement_pattern = invariants
                    variant_desc,          # constraints = variants
                    len(parsed),           # abstraction_level = sample size
                ))

                stats['concepts_created'] += 1

                logger.info(
                    f"[COMPRESS] Concept {concept_id[:16]} for {gt}@L{level}: "
                    f"{len(inv_pos)} invariants, {len(var_pos)} variants "
                    f"from {len(parsed)} sequences"
                )

            except Exception as e:
                logger.error(f"[COMPRESS] Concept creation failed for {gt}@L{level}: {e}")

        return stats
