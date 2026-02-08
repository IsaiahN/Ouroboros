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
