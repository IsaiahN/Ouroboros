"""
Agent Revival Mechanism (Task #9)

This script implements the agent revival mechanism for autonomous_evolution_runner.py.
It queries high-prestige dead agents and revives them with slight mutations.
"""

import sqlite3
import json
import random
from datetime import datetime

DB_PATH = "core_data.db"


def get_revival_candidates(db_conn, max_candidates=5):
    """
    Query high-prestige dead agents for revival.

    Args:
        db_conn: Database connection
        max_candidates: Maximum number of candidates to return

    Returns:
        List of agent records suitable for revival
    """
    cursor = db_conn.cursor()
    cursor.row_factory = sqlite3.Row

    # Query dead agents with high prestige
    # Prioritize: high prestige, recent death, good performance
    query = """
        SELECT a.*, 
               COALESCE(p.prestige_score, 0) as prestige,
               COALESCE(p.total_discoveries, 0) as discoveries,
               COALESCE(p.total_validations, 0) as validations
        FROM agents a
        LEFT JOIN prestige_scores p ON a.agent_id = p.agent_id
        WHERE a.is_alive = 0
        AND COALESCE(p.prestige_score, 0) > 10.0  -- Minimum prestige threshold
        ORDER BY 
            p.prestige_score DESC,
            a.death_timestamp DESC
        LIMIT ?
    """

    cursor.execute(query, (max_candidates,))
    return cursor.fetchall()


def clone_and_mutate_agent(agent_record, generation):
    """
    Clone an agent's genome and epigenetics with slight mutations.

    Args:
        agent_record: Original agent record
        generation: Current generation number

    Returns:
        Dict with new agent data
    """
    # Parse genome and epigenetics
    genome = json.loads(agent_record["genome"]) if agent_record["genome"] else {}
    epigenetics = (
        json.loads(agent_record["epigenetics"]) if agent_record["epigenetics"] else {}
    )

    # Apply mutations (5-10% change)
    mutation_rate = random.uniform(0.05, 0.10)

    # Mutate genome (static traits)
    for key in genome:
        if isinstance(genome[key], (int, float)):
            if random.random() < mutation_rate:
                genome[key] *= random.uniform(0.9, 1.1)

    # Mutate epigenetics (learning parameters)
    for key in epigenetics:
        if isinstance(epigenetics[key], (int, float)):
            if random.random() < mutation_rate:
                epigenetics[key] *= random.uniform(0.95, 1.05)

    # Generate new agent ID
    import uuid

    new_agent_id = f"revived_{uuid.uuid4().hex[:12]}"

    return {
        "agent_id": new_agent_id,
        "genome": json.dumps(genome),
        "epigenetics": json.dumps(epigenetics),
        "generation": generation,
        "parent_agent_id": agent_record["agent_id"],
        "is_revived": True,
        "original_prestige": agent_record["prestige"],
    }


def revive_agents(max_revivals=3):
    """
    Revive high-prestige dead agents.

    Args:
        max_revivals: Maximum number of agents to revive

    Returns:
        List of revived agent IDs
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get current generation
        cursor.execute("SELECT MAX(generation) as max_gen FROM agents")
        current_gen = cursor.fetchone()["max_gen"] or 0
        next_gen = current_gen + 1

        # Get revival candidates
        candidates = get_revival_candidates(conn, max_candidates=max_revivals * 2)

        if not candidates:
            print("No suitable candidates for revival")
            return []

        print(f"Found {len(candidates)} revival candidates")

        revived_ids = []
        for i, candidate in enumerate(candidates[:max_revivals]):
            # Clone and mutate
            new_agent = clone_and_mutate_agent(candidate, next_gen)

            # Insert new agent
            cursor.execute(
                """
                INSERT INTO agents (
                    agent_id, genome, epigenetics, generation,
                    parent_agent_id, is_alive, created_at,
                    agent_type, social_rule_adherence
                )
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
            """,
                (
                    new_agent["agent_id"],
                    new_agent["genome"],
                    new_agent["epigenetics"],
                    new_agent["generation"],
                    new_agent["parent_agent_id"],
                    candidate["agent_type"],
                    candidate["social_rule_adherence"],
                ),
            )

            revived_ids.append(new_agent["agent_id"])

            print(
                f"✅ Revived agent {new_agent['agent_id']} "
                f"(parent: {candidate['agent_id']}, "
                f"prestige: {new_agent['original_prestige']:.1f})"
            )

        conn.commit()
        print(f"\n🔄 Successfully revived {len(revived_ids)} agents")
        return revived_ids

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Revive high-prestige dead agents")
    parser.add_argument("--max", type=int, default=3, help="Maximum agents to revive")
    args = parser.parse_args()

    revived = revive_agents(args.max)
    for agent_id in revived:
        print(f"  - {agent_id}")
