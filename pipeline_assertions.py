"""
Pipeline Assertions -- Real-time write-through verification.

The pattern across ALL silent data disconnections found in sessions 7n-7s:
  - No crashes, no errors, just zero signal flowing through a pipeline
  - Tests pass because they test units, not end-to-end flow
  - The system looks alive but is braindead

Health checks detect problems AFTER thousands of silent generations.
Pipeline assertions detect problems THE MOMENT they happen.

Usage in evolution_runner._store_game_result:
    from pipeline_assertions import PipelineAssertions
    pa = PipelineAssertions(db)
    pa.assert_game_result_stored(session_id, game_id, agent_id)

Every assertion:
  - Verifies data actually landed in the expected table
  - Prints [PIPE-BREAK] on failure (loud, immediate)
  - Returns bool (True = OK) so caller can take corrective action
  - NEVER raises (assertions are diagnostic, not fatal)
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Optional


class PipelineAssertions:
    """
    Real-time write-through verification for critical data pipelines.

    Each method verifies a specific producer -> consumer junction.
    Call IMMEDIATELY after the write operation.
    """

    # Tag prefix for all assertion output
    TAG_OK = "[PIPE-OK]"
    TAG_BREAK = "[PIPE-BREAK]"

    def __init__(self, db, verbose: bool = False):
        """
        Args:
            db: DatabaseInterface instance (uses execute_query)
            verbose: If True, print OK messages too (not just failures)
        """
        self.db = db
        self.verbose = verbose
        # Counters for end-of-generation summary
        self.checks_run = 0
        self.checks_failed = 0

    def reset_counters(self):
        """Reset per-generation counters."""
        self.checks_run = 0
        self.checks_failed = 0

    # ------------------------------------------------------------------
    # Junction 1: game_results + agent_arc_performance dual write
    # ------------------------------------------------------------------
    def assert_game_result_stored(
        self,
        session_id: str,
        game_id: str,
        agent_id: str,
    ) -> bool:
        """
        Verify BOTH game_results AND agent_arc_performance received the write.

        Call after _store_game_result completes.
        Detects the Session 7p bug: game_results written but
        agent_arc_performance empty (fitness = 0.0 forever).
        """
        self.checks_run += 1
        ok = True

        # Check game_results
        try:
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM game_results "
                "WHERE session_id = ? AND game_id = ?",
                [session_id, game_id],
            )
            gr_count = rows[0]['cnt'] if rows else 0
            if gr_count == 0:
                print(f"  {self.TAG_BREAK} game_results missing for "
                      f"session={session_id[:16]}.. game={game_id}")
                ok = False
        except Exception as e:
            print(f"  {self.TAG_BREAK} game_results check failed: {e}")
            ok = False

        # Check agent_arc_performance
        try:
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM agent_arc_performance "
                "WHERE session_id = ? AND game_id = ? AND agent_id = ?",
                [session_id, game_id, agent_id],
            )
            arc_count = rows[0]['cnt'] if rows else 0
            if arc_count == 0:
                print(f"  {self.TAG_BREAK} agent_arc_performance missing for "
                      f"agent={agent_id[:12]}.. game={game_id} "
                      f"-- FITNESS WILL BE ZERO")
                ok = False
        except Exception as e:
            print(f"  {self.TAG_BREAK} agent_arc_performance check failed: {e}")
            ok = False

        if not ok:
            self.checks_failed += 1
        elif self.verbose:
            print(f"  {self.TAG_OK} game_result + arc_performance stored "
                  f"for {agent_id[:12]}.. / {game_id}")

        return ok

    # ------------------------------------------------------------------
    # Junction 4: training_sessions FK dependency
    # ------------------------------------------------------------------
    def assert_session_exists(self, session_id: str) -> bool:
        """
        Verify training_sessions row exists before downstream FK-dependent writes.

        Call AFTER training_sessions INSERT, BEFORE game_results/arc_performance.
        Detects Junction 4: if session INSERT silently fails, ALL downstream
        writes fail with FK violations (also silently caught).
        """
        self.checks_run += 1

        try:
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM training_sessions WHERE session_id = ?",
                [session_id],
            )
            count = rows[0]['cnt'] if rows else 0
            if count == 0:
                print(f"  {self.TAG_BREAK} training_sessions missing for "
                      f"session={session_id[:16]}.. "
                      f"-- ALL downstream writes will fail (FK violation)")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"  {self.TAG_BREAK} session check failed: {e}")
            self.checks_failed += 1
            return False

        return True

    # ------------------------------------------------------------------
    # Junction 2 + 3: Population health after evolution
    # ------------------------------------------------------------------
    def assert_population_size(
        self,
        expected_size: int,
        generation: int,
        tolerance: float = 0.2,
    ) -> bool:
        """
        Verify active agent count matches expected population after evolution.

        Call after evolve() completes.
        Detects Session 7p population bloat bug.
        """
        self.checks_run += 1

        try:
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM agents WHERE is_active = 1"
            )
            actual = rows[0]['cnt'] if rows else 0
            ratio = actual / max(expected_size, 1)

            if ratio > (1 + tolerance):
                print(f"  {self.TAG_BREAK} Population bloat after evolution: "
                      f"{actual} active vs {expected_size} expected "
                      f"(gen {generation}, {ratio:.1f}x)")
                self.checks_failed += 1
                return False
            elif actual == 0:
                print(f"  {self.TAG_BREAK} Population extinct after evolution! "
                      f"0 active agents (gen {generation})")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"  {self.TAG_BREAK} population check failed: {e}")
            self.checks_failed += 1
            return False

        return True

    # ------------------------------------------------------------------
    # Junction 6: Winning sequence stored on win
    # ------------------------------------------------------------------
    def assert_win_sequence_stored(
        self,
        game_id: str,
        session_id: str,
        is_full_game_win: bool = False,
    ) -> bool:
        """
        Verify winning sequence was actually stored after a win.

        Call after _store_game_result when result.is_win == True.
        Detects Junction 6: wins happen but sequences never saved.
        """
        self.checks_run += 1

        try:
            # Check partial sequences
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM winning_sequences "
                "WHERE session_id = ?",
                [session_id],
            )
            ws_count = rows[0]['cnt'] if rows else 0

            if is_full_game_win:
                # Also check full-game sequences
                fg_rows = self.db.execute_query(
                    "SELECT COUNT(*) as cnt FROM winning_sequences_full_game "
                    "WHERE session_id = ?",
                    [session_id],
                )
                fg_count = fg_rows[0]['cnt'] if fg_rows else 0

                if fg_count == 0 and ws_count == 0:
                    print(f"  {self.TAG_BREAK} FULL GAME WIN for {game_id} but "
                          f"no winning sequence stored in EITHER table! "
                          f"Knowledge is being lost.")
                    self.checks_failed += 1
                    return False
                elif fg_count == 0:
                    print(f"  {self.TAG_BREAK} Full game win for {game_id} stored "
                          f"in winning_sequences but NOT winning_sequences_full_game. "
                          f"Full-game replay path is dead.")
                    self.checks_failed += 1
                    return False
            else:
                if ws_count == 0:
                    print(f"  {self.TAG_BREAK} Win for {game_id} but "
                          f"no winning sequence stored!")
                    self.checks_failed += 1
                    return False
        except Exception as e:
            print(f"  {self.TAG_BREAK} win sequence check failed: {e}")
            self.checks_failed += 1
            return False

        if self.verbose:
            print(f"  {self.TAG_OK} Winning sequence stored for {game_id}")
        return True

    # ------------------------------------------------------------------
    # Generation-level flow counters
    # ------------------------------------------------------------------
    def assert_generation_flow(
        self,
        generation: int,
        games_played_in_memory: int,
    ) -> bool:
        """
        End-of-generation invariant: in-memory game count must match DB
        for BOTH game_results AND agent_arc_performance.

        Call at end of run_generation().
        Detects any silent write failure across the entire generation.
        """
        self.checks_run += 1
        ok = True

        # Check game_results
        try:
            rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM game_results WHERE generation = ?",
                [generation],
            )
            gr_count = rows[0]['cnt'] if rows else 0

            if gr_count < games_played_in_memory:
                dropped = games_played_in_memory - gr_count
                print(f"  {self.TAG_BREAK} Generation {generation}: "
                      f"{games_played_in_memory} games played in memory but "
                      f"only {gr_count} in game_results. "
                      f"{dropped} game results SILENTLY DROPPED.")
                ok = False
        except Exception as e:
            print(f"  {self.TAG_BREAK} generation flow game_results check failed: {e}")
            ok = False

        # Check agent_arc_performance (fitness signal)
        # Uses session_id join since arc_performance has no generation column
        try:
            rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM agent_arc_performance ap
                WHERE EXISTS (
                    SELECT 1 FROM game_results gr
                    WHERE gr.session_id = ap.session_id
                    AND gr.generation = ?
                )
            """, [generation])
            arc_count = rows[0]['cnt'] if rows else 0

            if arc_count < games_played_in_memory:
                dropped = games_played_in_memory - arc_count
                print(f"  {self.TAG_BREAK} Generation {generation}: "
                      f"{games_played_in_memory} games played but only "
                      f"{arc_count} agent_arc_performance rows. "
                      f"{dropped} fitness records SILENTLY DROPPED "
                      f"-- evolution has partial/zero signal.")
                ok = False
        except Exception as e:
            print(f"  {self.TAG_BREAK} generation flow arc_performance check failed: {e}")
            ok = False

        if not ok:
            self.checks_failed += 1
        return ok

    # ------------------------------------------------------------------
    # Phase 6.2: Data Contract Assertions
    # ------------------------------------------------------------------
    # Validate that data structures flowing between components match their
    # expected schema.  Run on a SAMPLE every generation (not every action).
    # ------------------------------------------------------------------

    # Required keys for a DecisionContext dict (the 11 no-default fields)
    _CONTEXT_REQUIRED = frozenset({
        'game_id', 'game_type', 'level', 'score', 'levels_completed',
        'win_levels', 'game_state', 'action_count', 'budget_remaining',
        'budget_used_percent', 'phase',
    })

    def assert_context_contract(self, context) -> bool:
        """Verify a DecisionContext (dict or dataclass) has all required keys.

        Call on a sample context each generation to detect interface drift.
        """
        self.checks_run += 1
        data = context if isinstance(context, dict) else vars(context)
        missing = self._CONTEXT_REQUIRED - set(data.keys())
        if missing:
            print(f"  {self.TAG_BREAK} DecisionContext missing keys: {missing}")
            self.checks_failed += 1
            return False
        return True

    _VIRAL_REQUIRED = frozenset({
        'package_id', 'package_name', 'package_type',
        'discovery_generation', 'generation_discovered',
    })

    def assert_viral_package_contract(self, package: dict) -> bool:
        """Verify a viral package dict has all required columns."""
        self.checks_run += 1
        if not isinstance(package, dict):
            print(f"  {self.TAG_BREAK} Viral package is not a dict: {type(package)}")
            self.checks_failed += 1
            return False
        missing = self._VIRAL_REQUIRED - set(package.keys())
        if missing:
            print(f"  {self.TAG_BREAK} Viral package missing keys: {missing}")
            self.checks_failed += 1
            return False
        return True

    _RESONANCE_REQUIRED = frozenset({
        'pattern_hash', 'resonance_score',
    })

    def assert_resonance_pattern_contract(self, pattern: dict) -> bool:
        """Verify a resonance pattern dict has required fields."""
        self.checks_run += 1
        if not isinstance(pattern, dict):
            print(f"  {self.TAG_BREAK} Resonance pattern is not a dict: {type(pattern)}")
            self.checks_failed += 1
            return False
        missing = self._RESONANCE_REQUIRED - set(pattern.keys())
        if missing:
            print(f"  {self.TAG_BREAK} Resonance pattern missing keys: {missing}")
            self.checks_failed += 1
            return False
        score = pattern.get('resonance_score')
        if not isinstance(score, (int, float)):
            print(f"  {self.TAG_BREAK} Resonance score is not numeric: {type(score)}")
            self.checks_failed += 1
            return False
        return True

    _SEQUENCE_REQUIRED = frozenset({
        'sequence_id', 'game_id', 'level_number',
        'action_sequence', 'agent_id', 'session_id',
        'total_actions', 'total_score',
    })

    def assert_sequence_contract(self, sequence: dict) -> bool:
        """Verify a winning sequence dict has required fields and valid actions."""
        self.checks_run += 1
        if not isinstance(sequence, dict):
            print(f"  {self.TAG_BREAK} Sequence is not a dict: {type(sequence)}")
            self.checks_failed += 1
            return False
        missing = self._SEQUENCE_REQUIRED - set(sequence.keys())
        if missing:
            print(f"  {self.TAG_BREAK} Winning sequence missing keys: {missing}")
            self.checks_failed += 1
            return False
        # Validate action_sequence is a non-empty string/list
        actions = sequence.get('action_sequence')
        if not actions:
            print(f"  {self.TAG_BREAK} Winning sequence has empty action_sequence")
            self.checks_failed += 1
            return False
        return True

    def run_contract_spot_check(self, generation: int) -> dict:
        """Run contract assertions on a sample of live DB data.

        Checks one random row from each of: viral packages, resonance
        patterns, and winning sequences.  Returns a summary dict.
        Persists violation stats to system_logs for historical tracking.

        Call this once per generation from the evolution runner.
        """
        stats = {'checked': 0, 'passed': 0, 'failed': 0, 'generation': generation}

        # Sample viral package
        try:
            rows = self.db.execute_query("""
                SELECT * FROM viral_information_packages
                WHERE is_active = 1
                ORDER BY RANDOM() LIMIT 1
            """)
            if rows:
                stats['checked'] += 1
                if self.assert_viral_package_contract(rows[0]):
                    stats['passed'] += 1
                else:
                    stats['failed'] += 1
        except Exception:
            pass

        # Sample resonance pattern
        try:
            rows = self.db.execute_query("""
                SELECT * FROM resonance_patterns
                ORDER BY RANDOM() LIMIT 1
            """)
            if rows:
                stats['checked'] += 1
                if self.assert_resonance_pattern_contract(rows[0]):
                    stats['passed'] += 1
                else:
                    stats['failed'] += 1
        except Exception:
            pass

        # Sample winning sequence
        try:
            rows = self.db.execute_query("""
                SELECT * FROM winning_sequences
                WHERE is_active = 1
                ORDER BY RANDOM() LIMIT 1
            """)
            if rows:
                stats['checked'] += 1
                if self.assert_sequence_contract(rows[0]):
                    stats['passed'] += 1
                else:
                    stats['failed'] += 1
        except Exception:
            pass

        # Phase 6.2: Sample decision context from recent action trace
        try:
            rows = self.db.execute_query("""
                SELECT game_id, agent_id, action_number, level_number
                FROM action_traces
                ORDER BY ROWID DESC LIMIT 1
            """)
            if rows:
                # Build a minimal context dict that mirrors DecisionContext keys
                sample_ctx = {
                    'game_id': rows[0].get('game_id', ''),
                    'agent_id': rows[0].get('agent_id', ''),
                    'action_count': rows[0].get('action_number', 0),
                    'level_number': rows[0].get('level_number', 0),
                    'available_actions': [1, 2, 3, 4, 5, 6, 7],
                }
                stats['checked'] += 1
                if self.assert_context_contract(sample_ctx):
                    stats['passed'] += 1
                else:
                    stats['failed'] += 1
        except Exception:
            pass

        # G4+G5: Persist violation stats to system_logs for historical tracking
        if stats['checked'] > 0:
            try:
                import logging as _logging
                _logger = _logging.getLogger('pipeline_assertions')
                if stats['failed'] > 0:
                    _logger.warning(
                        "[CONTRACT] Gen %d: %d/%d contract violations",
                        generation, stats['failed'], stats['checked'],
                    )
                else:
                    _logger.debug(
                        "[CONTRACT] Gen %d: %d/%d contracts OK",
                        generation, stats['passed'], stats['checked'],
                    )
            except Exception:
                pass

        return stats

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def print_summary(self):
        """Print end-of-generation pipeline health summary."""
        if self.checks_failed > 0:
            print(f"  {self.TAG_BREAK} Pipeline: {self.checks_failed}/{self.checks_run} "
                  f"assertions FAILED this generation")
        elif self.checks_run > 0 and self.verbose:
            print(f"  {self.TAG_OK} Pipeline: {self.checks_run}/{self.checks_run} "
                  f"assertions passed")
