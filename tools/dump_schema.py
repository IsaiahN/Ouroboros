import os
import sqlite3
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
DB_PATH = Path("core_data.db")
OUT_PATH = Path("complete_database_schema.sql")

def dump_schema(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE type IN ('table','index','trigger','view') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    lines = ["PRAGMA foreign_keys=ON;", ""]
    for _typ, _name, sql in rows:
        if not sql:
            continue
        sql_clean = sql.strip()
        if not sql_clean.endswith(";"):
            sql_clean += ";"
        lines.append(sql_clean)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    conn.close()
    print(f"wrote {len(lines)//2} statements (including pragma line) to {out_path}")

if __name__ == "__main__":
    dump_schema()
