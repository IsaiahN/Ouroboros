"""Seed the relationship graph tables (module_contracts + relationship_graph).

Idempotent: uses INSERT OR REPLACE. Safe to run repeatedly.
Run after schema rebuild from complete_database_schema.sql to restore structural knowledge.

Usage:
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe lab/seed_relationship_graph.py

Maintenance:
    When the Code Modifier adds new edges to the live DB, update the lists below to match.
    This script is the recovery path -- if it falls out of sync, a schema rebuild loses data.
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "core_data.db"


def seed(db_path=None):
    conn = sqlite3.connect(str(db_path or DB_PATH))
    c = conn.cursor()

    # Ensure tables exist (in case this runs before full schema import)
    c.execute("""
        CREATE TABLE IF NOT EXISTS module_contracts (
            module_name TEXT PRIMARY KEY,
            role TEXT,
            stream_a TEXT NOT NULL,
            stream_b_produces TEXT,
            stream_b_consumes TEXT,
            stream_b_side_effects TEXT,
            stream_b_promises TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS relationship_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_module TEXT NOT NULL,
            target_module TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            contract TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'live',
            last_verified_gen INTEGER,
            broke_at_exp TEXT,
            fixed_at_exp TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_module, target_module, edge_type)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_rg_source ON relationship_graph(source_module)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rg_target ON relationship_graph(target_module)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rg_status ON relationship_graph(status)")

    # =========================================================================
    # MODULE CONTRACTS (Stream A + Stream B)
    # =========================================================================
    modules = [
        ("evolution_runner", "optimizer",
         "Manages population lifecycle: selection, mutation, crossover, fitness evaluation across generations",
         "Spawns game sessions, triggers fitness calculation, writes generation metadata",
         "game_results (fitness data), agents table (genomes), fitness_calculator output",
         "Writes to agents table, updates generation counter, calls safe_cleanup",
         "Every agent plays games_per_generation games before selection. Generation counter monotonically increases."),

        ("cognitive_game_player", "pioneer",
         "Plays a single game session using cognitive rung system. Active production path via EvolutionRunner.",
         "game_results row (session_id, game_id, generation, final_score, level_completions, frame_changes, total_actions), action_traces rows, trace JSON files",
         "Agent genome, game environment frames, decision_rung_system output, sequence_abstraction templates",
         "Writes game_results, action_traces, trace files. Calls epistemic_tracker. 20% chance: calls _replay_winning_sequences.",
         "Every game session produces exactly one game_results row. frame_changes uses meaningful_change (5% pixel threshold). context['frame_changed'] reflects meaningful_change."),

        ("decision_rung_system", "generalist",
         "Builds context dict from frame data + DB history, selects cognitive rung, delegates action selection",
         "context dict with frame, game_state, epistemic state; selected action from chosen rung",
         "Current frame (ndarray), game history from DB, epistemic tracker state, agent genome",
         "Passes context dict to rungs. Calls epistemic_tracker.update().",
         "game_state is always a DICT (not object). Use game_state.get() not getattr(). Context always contains 'frame' key."),

        ("epistemic_tracker", "optimizer",
         "Tracks agent epistemic state (KK/KU/UK/UU quadrant) based on action outcomes",
         "kk_confidence, uu_confidence, epistemic_quadrant, _no_change_streak",
         "meaningful_change boolean from cognitive_game_player (NOT raw frame hash)",
         "Updates internal confidence scores. Feeds back to decision_rung_system context.",
         "kk_confidence decays 0.95x per decision (never one-way trap). meaningful_change = 5% pixel threshold (not raw hash)."),

        ("fitness_calculator", "optimizer",
         "Computes fitness scores for agents based on game performance, blended with exploration proxy",
         "Fitness score per agent (float)",
         "game_results (final_score, level_completions, frame_changes), agent genome (role)",
         "None (pure computation, no side effects)",
         "Blended at 20% weight with evolution. Genre bonus for click games. Exploration proxy active when scores=0, auto-disengages on scoring."),

        ("sequence_abstraction", "exploiter",
         "Extracts and stores replayable action sequences from successful game completions",
         "Replay templates (action sequences with invariant/variant position annotations)",
         "game_results with level_completions >= 1, action_traces from successful sessions",
         "Writes to sequence_abstractions table. Takes db_path STRING not DatabaseInterface.",
         "Templates preserve action order. Invariant positions are actions present in all successful sequences. Variant positions are exploratory."),

        ("game_player", "pioneer",
         "Fallback game player when CognitiveGamePlayer fails. Simpler action selection.",
         "game_results row, action_traces rows",
         "Agent genome, game environment frames",
         "Writes game_results, action_traces. Has _is_meaningful_frame_change() with game-type thresholds.",
         "Only activates on CognitiveGamePlayer failure. Same meaningful_change thresholds as cognitive path."),

        ("safe_cleanup", "exploiter",
         "Periodic DB maintenance: prunes old data to prevent unbounded growth (Seal 5 prevention)",
         "None (cleanup only)",
         "game_results, action_traces, world_model_states, autopoiesis_snapshots",
         "DELETES rows from multiple tables based on generation age. Runs every 30 gens via health_monitor.",
         "_clean_zero_score_games() is DISABLED (was deleting all score=0 game_results). Generation-bounded deletes only."),

        ("game_results", "generalist",
         "DB table: central record of every game session played. The primary data contract.",
         "Rows consumed by: fitness_calculator, sequence_abstraction, metrics, comparative_analyst, trend_tracker",
         "Written by: cognitive_game_player, game_player",
         "N/A (table, not module)",
         "Columns: session_id, game_id, generation, final_score, level_completions, frame_changes, total_actions, game_status. game_id encodes game type (SUBSTR(game_id,1,4))."),

        ("action_traces", "generalist",
         "DB table: per-action trace data for each game session",
         "Rows consumed by: sequence_abstraction, code_tracer, comparative_analyst",
         "Written by: cognitive_game_player, game_player",
         "N/A (table, not module)",
         "Columns include: session_id, action_type, frame_changed. frame_changed is independent hash comparison (differs from meaningful_change)."),
    ]

    c.executemany("""
        INSERT OR REPLACE INTO module_contracts
        (module_name, role, stream_a, stream_b_produces, stream_b_consumes, stream_b_side_effects, stream_b_promises)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, modules)

    # =========================================================================
    # RELATIONSHIP GRAPH EDGES
    # =========================================================================
    edges = [
        # --- Production path: evolution -> game play ---
        ("evolution_runner", "cognitive_game_player", "calls",
         "Spawns CognitiveGamePlayer with agent genome + game assignment. Passes db_path, agent_id, game_type.",
         "live", None, None, None, None),

        ("evolution_runner", "game_player", "calls",
         "Fallback: spawns GamePlayer when CognitiveGamePlayer raises exception.",
         "live", None, None, None, None),

        ("evolution_runner", "fitness_calculator", "calls",
         "Calls fitness calculation after all agents complete games. Passes generation game_results.",
         "live", None, None, None,
         "Exp #10: was disconnected, reconnected at 20% weight"),

        # --- Game player -> DB writes ---
        ("cognitive_game_player", "game_results", "writes_db",
         "INSERT row: session_id, game_id, generation, final_score, level_completions, frame_changes, total_actions, game_status",
         "live", None, "Exp #2", "Exp #2",
         "frame_changes column was missing from INSERT statement"),

        ("cognitive_game_player", "action_traces", "writes_db",
         "INSERT row per action: session_id, step, action_type, frame_changed, timestamp",
         "live", None, None, None, None),

        ("game_player", "game_results", "writes_db",
         "INSERT row: same schema as cognitive_game_player writes",
         "live", None, None, None, None),

        # --- Cognitive pipeline: context flow ---
        ("cognitive_game_player", "decision_rung_system", "calls",
         "Passes game_state dict: {frame: ndarray, game_type: str, frame_changed: bool (meaningful_change), ...context}",
         "live", None, None, None,
         "game_state is a DICT not object. frame_changed is meaningful_change (5% pixel threshold)."),

        ("decision_rung_system", "rungs", "passes_context",
         "Passes context dict to selected rung. Contains frame, game_state, epistemic state, stuck_count.",
         "live", None, "Exp #3", "Exp #3",
         "game_state was dict but rungs used getattr (returns None). Fixed with _get_frame() helper."),

        # --- Epistemic feedback loop (THE critical loop) ---
        ("cognitive_game_player", "epistemic_tracker", "calls",
         "Passes meaningful_change (bool, 5% pixel threshold) after each action. NOT raw frame hash.",
         "live", None, "Exp #9", "Exp #9",
         "ROOT CAUSE of KK trap. Raw hash always True -> tracker thought every action confirmed knowledge."),

        ("epistemic_tracker", "decision_rung_system", "returns",
         "Returns kk_confidence, uu_confidence, epistemic_quadrant. kk_confidence decays 0.95x per decision.",
         "live", None, "Exp #9", "Exp #9",
         "Without decay, agents permanently locked in KK. 0.95x decay is the anti-stasis mechanism."),

        # --- report_outcome (was completely dead) ---
        ("cognitive_game_player", "report_outcome", "calls",
         "Calls report_outcome() after game completion to set GAP 4D flags.",
         "live", None, "Exp #9", "Exp #9",
         "Classic dead pipeline. Function existed, passed unit tests, but was never invoked in production."),

        # --- Replay / template path ---
        ("sequence_abstraction", "game_results", "reads_db",
         "Reads game_results WHERE level_completions >= 1 to find successful sessions for template extraction.",
         "live", None, None, None, None),

        ("sequence_abstraction", "action_traces", "reads_db",
         "Reads action_traces for successful session_ids to extract action sequences.",
         "live", None, None, None, None),

        ("cognitive_game_player", "sequence_abstraction", "calls",
         "Calls for replay templates. 20% of games enter _replay_winning_sequences(). Takes db_path STRING.",
         "live", None, None, None,
         "Exp #11: SequenceAbstraction takes db_path STRING not DatabaseInterface."),

        # --- Fitness reads ---
        ("fitness_calculator", "game_results", "reads_db",
         "Reads final_score, level_completions, frame_changes for fitness calculation. Genre bonus for click games.",
         "live", None, None, None, None),

        # --- safe_cleanup edges ---
        ("safe_cleanup", "game_results", "writes_db",
         "DELETES rows: zero-score sessions older than N generations. _clean_zero_score_games() is DISABLED.",
         "live", None, "Exp #10", "Exp #10",
         "CRITICAL: was deleting ALL score=0 rows every 30 gens (data loss). Now disabled."),

        ("safe_cleanup", "action_traces", "writes_db",
         "DELETES rows: action_traces from zero-score sessions older than 20 generations.",
         "live", None, None, None, None),

        # --- Lab scripts read paths ---
        ("lab_metrics", "game_results", "reads_db",
         "Reads all 5 benchmark metrics: level_completions, final_score, total_actions, game_status.",
         "live", None, None, None, None),

        ("lab_comparative_analyst", "game_results", "reads_db",
         "Reads success vs failure cohorts, ranks features by effect size.",
         "live", None, None, None, None),

        ("lab_code_tracer", "action_traces", "reads_db",
         "Scans traces to compute subsystem engagement rates, find dead subsystems.",
         "live", None, None, None, None),
    ]

    c.executemany("""
        INSERT OR REPLACE INTO relationship_graph
        (source_module, target_module, edge_type, contract, status, last_verified_gen, broke_at_exp, fixed_at_exp, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, edges)

    conn.commit()

    # Report
    c.execute("SELECT COUNT(*) FROM module_contracts")
    n_modules = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM relationship_graph")
    n_edges = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM relationship_graph WHERE broke_at_exp IS NOT NULL")
    n_broken = c.fetchone()[0]
    print(f"[OK] Seeded {n_modules} module contracts, {n_edges} edges ({n_broken} historically broken)")

    conn.close()
    return n_modules, n_edges


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    seed(path)
