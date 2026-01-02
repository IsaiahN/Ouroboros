import os
import sqlite3
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
DB_PATH = Path("core_data.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    dupes = cur.execute(
        """
        SELECT game_id, level_number, COUNT(*) AS c
        FROM winning_sequences
        WHERE is_active = 1
        GROUP BY game_id, level_number
        HAVING c > 1
        """
    ).fetchall()
    print(f"duplicate keys: {len(dupes)}")
    updated = 0
    for game_id, level_number, _ in dupes:
        rows = cur.execute(
            """
            SELECT rowid, total_actions, COALESCE(discovered_at,''), sequence_id
            FROM winning_sequences
            WHERE game_id = ? AND level_number = ? AND is_active = 1
            ORDER BY total_actions ASC, discovered_at ASC, rowid ASC
            """,
            (game_id, level_number),
        ).fetchall()
        keep_rowid = rows[0][0]
        to_deactivate = [r[0] for r in rows[1:]]
        if to_deactivate:
            cur.executemany(
                "UPDATE winning_sequences SET is_active = 0 WHERE rowid = ?",
                [(rid,) for rid in to_deactivate],
            )
            updated += len(to_deactivate)
            print(
                f"deactivated {len(to_deactivate)} duplicates for game {game_id} level {level_number}; kept rowid {keep_rowid}"
            )
    conn.commit()
    print(f"total deactivated: {updated}")
    conn.close()

if __name__ == "__main__":
    main()
