#!/usr/bin/env python3
"""
Auto-Infer Question Taxonomy from Rung READ Patterns

Phase 0.5 Deliverable - Cognitive Routing Implementation

This script analyzes the rung_dependency_matrix.json to automatically generate
a question taxonomy based on which rungs READ which slots. The insight is:

    If rung X reads slot Y, then rung X can ANSWER questions about Y.

This inverts the traditional approach of manually defining questions. Instead,
we let the rung structure DEFINE what questions are answerable.

Usage:
    python manual_tools/infer_answerable_by.py [--output OUTPUT_PATH]
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class InferredQuestion:
    """A question inferred from rung READ patterns."""
    question_id: str
    natural_language: str
    target_slots: List[str]
    answerable_by: List[str]  # Rung names that READ these slots
    category: str  # orientation, hypothesis, exploitation, filter, metacognition
    complexity: str  # simple (1 slot), compound (2+ slots), meta (requires inference)
    rumsfeld_relevance: str  # KK, KU, UK, UU - which quadrant this question probes


@dataclass
class QuestionTaxonomy:
    """The full taxonomy of inferrable questions."""
    questions: List[InferredQuestion] = field(default_factory=list)
    slot_to_questions: Dict[str, List[str]] = field(default_factory=dict)
    rung_to_questions: Dict[str, List[str]] = field(default_factory=dict)
    category_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self):
        return {
            "questions": [asdict(q) for q in self.questions],
            "slot_to_questions": dict(self.slot_to_questions),
            "rung_to_questions": dict(self.rung_to_questions),
            "category_counts": dict(self.category_counts),
            "total_questions": len(self.questions)
        }


# Question templates mapped to slot patterns
SLOT_TO_QUESTION_TEMPLATES = {
    # Orientation slots
    "survey": ("Q_SURVEY", "What objects and colors exist in this frame?", "orientation"),
    "sparse_grid": ("Q_SPARSE", "What is the sparse structure of the frame?", "orientation"),
    "sparse_hash": ("Q_FRAME_ID", "What is the structural signature of this frame?", "orientation"),
    "detected_palette": ("Q_PALETTE", "Is there a legend/palette encoding transformation rules?", "orientation"),
    "extracted_objects": ("Q_OBJECTS", "What distinct objects were extracted from the frame?", "orientation"),
    "controlled_objects": ("Q_CONTROL", "What object(s) does the agent control?", "orientation"),
    "likely_physics_game": ("Q_PHYSICS", "Is this a physics simulation or direct control game?", "orientation"),
    "visual_features": ("Q_VISUAL", "What visual features (symmetry, patterns) are present?", "orientation"),

    # Identity slots
    "game_type": ("Q_GAME_TYPE", "What type of game is this?", "orientation"),
    "player_position": ("Q_PLAYER_POS", "Where is the player/controlled object?", "orientation"),
    "goal_position": ("Q_GOAL_POS", "Where is the goal/target?", "orientation"),
    "target_position": ("Q_TARGET", "What position should the agent move toward?", "orientation"),

    # Hypothesis slots
    "active_beliefs": ("Q_BELIEFS", "What beliefs does the agent currently hold?", "hypothesis"),
    "untested_hypotheses": ("Q_UNTESTED", "What hypotheses haven't been tested yet?", "hypothesis"),
    "causal_model": ("Q_CAUSALITY", "What causes what in this game?", "hypothesis"),
    "click_rules": ("Q_CLICK_RULES", "What are the rules for clicking objects?", "hypothesis"),
    "trigger_chains": ("Q_TRIGGERS", "What trigger sequences have been learned?", "hypothesis"),
    "key_lock_pairs": ("Q_SYMBOLIC", "What key/lock symbolic relationships exist?", "hypothesis"),
    "good_objects": ("Q_VALENCE", "Which objects are good vs bad?", "hypothesis"),

    # Exploitation slots
    "checkpoint_sequence": ("Q_CHECKPOINT", "What is the current checkpoint/winning sequence?", "exploitation"),
    "active_sequence": ("Q_ACTIVE_SEQ", "What sequence is currently being followed?", "exploitation"),
    "winning_sequences": ("Q_WIN_SEQS", "What winning sequences are known for this game?", "exploitation"),
    "matched_stage": ("Q_STAGE", "What stage/state does the current frame match?", "exploitation"),
    "subgoal_path": ("Q_SUBGOALS", "What is the planned path to the goal?", "exploitation"),
    "frontier_target": ("Q_FRONTIER", "What unexplored frontier is being targeted?", "exploitation"),
    "reachable_cells": ("Q_REACHABLE", "What cells can the agent reach from here?", "exploitation"),

    # Filter slots
    "death_weights": ("Q_DEATH", "What positions/actions lead to death?", "filter"),
    "pariah_actions": ("Q_PARIAH", "What actions are known to fail?", "filter"),
    "theory_blocked_actions": ("Q_BLOCKED", "What actions contradict current theory?", "filter"),
    "collision_map": ("Q_COLLISION", "Where are the obstacles/walls?", "filter"),
    "terminal_patterns": ("Q_TERMINAL", "What patterns indicate terminal/death states?", "filter"),
    "avoided_contexts": ("Q_AVOID", "What contexts should be avoided?", "filter"),

    # Metacognition slots
    "frustration_level": ("Q_FRUSTRATION", "How frustrated/stuck is the agent?", "metacognition"),
    "confidence_level": ("Q_CONFIDENCE", "How confident is the agent in its strategy?", "metacognition"),
    "predicted_outcome": ("Q_PREDICT", "What outcome does the agent predict?", "metacognition"),
    "near_miss_patterns": ("Q_NEAR_MISS", "What near-misses could be improved?", "metacognition"),
    "resonance_patterns": ("Q_RESONANCE", "What patterns resonate across games?", "metacognition"),
    "exploration_stats": ("Q_EXPLORATION", "How much has been explored?", "metacognition"),
    "trust_weight_a": ("Q_TRUST_A", "How much should Stream A (private) be trusted?", "metacognition"),
    "trust_weight_b": ("Q_TRUST_B", "How much should Stream B (collective) be trusted?", "metacognition"),
    "completion_probability": ("Q_COMPLETION", "What's the probability of completing from here?", "metacognition"),

    # History slots
    "action_history": ("Q_HISTORY", "What actions have been taken?", "metacognition"),
    "score_history": ("Q_SCORES", "What scores have been achieved?", "metacognition"),
    "action_count": ("Q_ACTION_CT", "How many actions have been used?", "metacognition"),
    "action_budget": ("Q_BUDGET", "How many actions remain?", "metacognition"),
}

# Compound questions (require multiple slots)
COMPOUND_QUESTIONS = [
    {
        "question_id": "Q_PATH_TO_GOAL",
        "natural_language": "What is the best path from player position to goal?",
        "target_slots": ["player_position", "goal_position", "sparse_grid", "collision_map"],
        "category": "exploitation",
        "complexity": "compound",
        "rumsfeld_relevance": "KK"  # Only answerable when all slots populated
    },
    {
        "question_id": "Q_SAFE_EXPLORATION",
        "natural_language": "What unexplored areas are safe to explore?",
        "target_slots": ["reachable_cells", "death_weights", "visited_cells"],
        "category": "exploitation",
        "complexity": "compound",
        "rumsfeld_relevance": "KU"  # Partially known (we know safe, not what's there)
    },
    {
        "question_id": "Q_STRATEGY_CHOICE",
        "natural_language": "Should the agent explore or exploit?",
        "target_slots": ["winning_sequences", "exploration_stats", "frustration_level"],
        "category": "metacognition",
        "complexity": "compound",
        "rumsfeld_relevance": "KU"
    },
    {
        "question_id": "Q_STREAM_INTEGRATION",
        "natural_language": "How should private and collective knowledge be weighted?",
        "target_slots": ["trust_weight_a", "trust_weight_b", "stream_a_action", "stream_b_action"],
        "category": "metacognition",
        "complexity": "meta",
        "rumsfeld_relevance": "KU"
    },
    {
        "question_id": "Q_CLICK_EFFECT",
        "natural_language": "What will happen if I click this object?",
        "target_slots": ["click_rules", "extracted_objects", "causal_model"],
        "category": "hypothesis",
        "complexity": "compound",
        "rumsfeld_relevance": "UK"  # We know we don't know
    },
    {
        "question_id": "Q_GAME_SOLVED",
        "natural_language": "Is there a known winning strategy for this game?",
        "target_slots": ["winning_sequences", "game_type", "level"],
        "category": "exploitation",
        "complexity": "compound",
        "rumsfeld_relevance": "KK"
    },
    {
        "question_id": "Q_WHY_STUCK",
        "natural_language": "Why is the agent stuck?",
        "target_slots": ["frustration_level", "action_history", "pariah_actions", "death_weights"],
        "category": "metacognition",
        "complexity": "meta",
        "rumsfeld_relevance": "UK"
    },
    {
        "question_id": "Q_TRANSFORMATION_RULE",
        "natural_language": "What transformation rule does the palette encode?",
        "target_slots": ["detected_palette", "detected_transformations", "extracted_objects"],
        "category": "hypothesis",
        "complexity": "compound",
        "rumsfeld_relevance": "UK"
    },
]


def load_dependency_matrix(matrix_path: Path) -> dict:
    """Load the rung dependency matrix."""
    with open(matrix_path, 'r') as f:
        return json.load(f)


def invert_reads_to_answerable(matrix: dict) -> Dict[str, List[str]]:
    """
    Invert the rung->reads mapping to slot->answerable_by.

    If rung X reads slot Y, then X can answer questions about Y.
    """
    slot_to_rungs: Dict[str, List[str]] = defaultdict(list)

    for rung_name, rung_info in matrix.get("rungs", {}).items():
        for slot in rung_info.get("reads", []):
            slot_to_rungs[slot].append(rung_name)

    return dict(slot_to_rungs)


def infer_rumsfeld_relevance(slot: str, answerable_by: List[str]) -> str:
    """
    Infer which Rumsfeld quadrant this question probes.

    - KK: Many rungs can answer (well-understood)
    - KU: Some rungs answer but with uncertainty
    - UK: We know we need this but few can answer
    - UU: Implicit/rarely queried slots
    """
    if len(answerable_by) >= 5:
        return "KK"
    elif len(answerable_by) >= 2:
        return "KU"
    elif len(answerable_by) >= 1:
        return "UK"
    else:
        return "UU"


def generate_taxonomy(matrix: dict) -> QuestionTaxonomy:
    """Generate the full question taxonomy from the dependency matrix."""
    taxonomy = QuestionTaxonomy()
    slot_to_answerable = invert_reads_to_answerable(matrix)

    # 1. Generate simple questions (one slot each)
    for slot, (qid, natural_lang, category) in SLOT_TO_QUESTION_TEMPLATES.items():
        answerable_by = slot_to_answerable.get(slot, [])

        question = InferredQuestion(
            question_id=qid,
            natural_language=natural_lang,
            target_slots=[slot],
            answerable_by=answerable_by,
            category=category,
            complexity="simple",
            rumsfeld_relevance=infer_rumsfeld_relevance(slot, answerable_by)
        )
        taxonomy.questions.append(question)

        # Index
        if slot not in taxonomy.slot_to_questions:
            taxonomy.slot_to_questions[slot] = []
        taxonomy.slot_to_questions[slot].append(qid)

        for rung in answerable_by:
            if rung not in taxonomy.rung_to_questions:
                taxonomy.rung_to_questions[rung] = []
            taxonomy.rung_to_questions[rung].append(qid)

    # 2. Add compound questions
    for compound in COMPOUND_QUESTIONS:
        # Find all rungs that read ALL required slots
        slot_sets = [set(slot_to_answerable.get(s, [])) for s in compound["target_slots"]]
        if slot_sets:
            answerable_by = list(set.intersection(*slot_sets)) if all(slot_sets) else []
        else:
            answerable_by = []

        question = InferredQuestion(
            question_id=compound["question_id"],
            natural_language=compound["natural_language"],
            target_slots=compound["target_slots"],
            answerable_by=answerable_by,
            category=compound["category"],
            complexity=compound["complexity"],
            rumsfeld_relevance=compound["rumsfeld_relevance"]
        )
        taxonomy.questions.append(question)

        # Index
        for slot in compound["target_slots"]:
            if slot not in taxonomy.slot_to_questions:
                taxonomy.slot_to_questions[slot] = []
            taxonomy.slot_to_questions[slot].append(compound["question_id"])

    # 3. Count by category
    for q in taxonomy.questions:
        taxonomy.category_counts[q.category] = taxonomy.category_counts.get(q.category, 0) + 1

    return taxonomy


def main():
    parser = argparse.ArgumentParser(description="Infer question taxonomy from rung READ patterns")
    parser.add_argument("--output", "-o", type=str,
                       default="config/question_taxonomy.json",
                       help="Output path for taxonomy JSON")
    parser.add_argument("--matrix", "-m", type=str,
                       default="architecture/rung_dependency_matrix.json",
                       help="Path to rung dependency matrix")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Print detailed output")
    args = parser.parse_args()

    matrix_path = PROJECT_ROOT / args.matrix
    output_path = PROJECT_ROOT / args.output

    if not matrix_path.exists():
        print(f"[ERROR] Matrix not found: {matrix_path}")
        sys.exit(1)

    print(f"[INFO] Loading dependency matrix from {matrix_path}")
    matrix = load_dependency_matrix(matrix_path)

    print("[INFO] Generating question taxonomy...")
    taxonomy = generate_taxonomy(matrix)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(taxonomy.to_dict(), f, indent=2)

    print(f"[OK] Generated taxonomy with {len(taxonomy.questions)} questions")
    print(f"     Categories: {taxonomy.category_counts}")
    print(f"     Output: {output_path}")

    if args.verbose:
        print("\n--- Questions by Rumsfeld Quadrant ---")
        quadrants = defaultdict(list)
        for q in taxonomy.questions:
            quadrants[q.rumsfeld_relevance].append(q.question_id)

        for quad in ["KK", "KU", "UK", "UU"]:
            qs = quadrants.get(quad, [])
            print(f"\n{quad} ({len(qs)} questions):")
            for qid in qs[:5]:  # Show first 5
                print(f"  - {qid}")
            if len(qs) > 5:
                print(f"  ... and {len(qs) - 5} more")


if __name__ == "__main__":
    main()
