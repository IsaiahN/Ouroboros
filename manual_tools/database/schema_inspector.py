"""
Database Schema Inspector
=========================
Reusable tool for inspecting database schema and finding tables/columns.

Usage:
    python manual_tools/schema_inspector.py                     # List all tables
    python manual_tools/schema_inspector.py --table agents      # Show specific table
    python manual_tools/schema_inspector.py --find generation   # Find tables with column
    python manual_tools/schema_inspector.py --counts            # Show row counts
    python manual_tools/schema_inspector.py --full              # Full schema dump
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

import argparse
import os
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Get database connection."""
    if db_path is None:
        script_dir = Path(__file__).parent.parent
        db_path = str(script_dir / 'core_data.db')

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_tables(conn: sqlite3.Connection) -> list:
    """Get all table names."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [t[0] for t in tables]


def get_table_info(conn: sqlite3.Connection, table_name: str) -> dict:
    """Get detailed info about a table."""
    columns = conn.execute(f'PRAGMA table_info({table_name})').fetchall()

    # Get row count
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
    except:
        count = 'Error'

    # Get indexes
    indexes = conn.execute(f'PRAGMA index_list({table_name})').fetchall()

    return {
        'name': table_name,
        'columns': [
            {
                'cid': c[0],
                'name': c[1],
                'type': c[2],
                'notnull': c[3],
                'default': c[4],
                'pk': c[5]
            }
            for c in columns
        ],
        'row_count': count,
        'indexes': [dict(i) for i in indexes]
    }


def find_tables_with_column(conn: sqlite3.Connection, column_pattern: str) -> list:
    """Find all tables containing a column matching pattern."""
    tables = get_all_tables(conn)
    matches = []

    for table in tables:
        columns = conn.execute(f'PRAGMA table_info({table})').fetchall()
        col_names = [c[1] for c in columns]

        matching_cols = [c for c in col_names if column_pattern.lower() in c.lower()]
        if matching_cols:
            matches.append({
                'table': table,
                'matching_columns': matching_cols,
                'all_columns': col_names
            })

    return matches


def get_table_sample(conn: sqlite3.Connection, table_name: str, limit: int = 5) -> list:
    """Get sample rows from a table."""
    try:
        rows = conn.execute(f'SELECT * FROM {table_name} LIMIT ?', (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{'error': str(e)}]


def get_database_stats(conn: sqlite3.Connection) -> dict:
    """Get overall database statistics."""
    tables = get_all_tables(conn)

    stats = {
        'total_tables': len(tables),
        'tables': []
    }

    for table in tables:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            stats['tables'].append({'name': table, 'rows': count})
        except:
            stats['tables'].append({'name': table, 'rows': 'Error'})

    # Sort by row count descending
    stats['tables'].sort(key=lambda x: x['rows'] if isinstance(x['rows'], int) else 0, reverse=True)

    return stats


def print_table_list(conn: sqlite3.Connection, show_counts: bool = False):
    """Print list of all tables."""
    tables = get_all_tables(conn)

    print('=' * 70)
    print(f'DATABASE TABLES ({len(tables)} total)')
    print('=' * 70)

    if show_counts:
        stats = get_database_stats(conn)
        print(f'\n{"Table Name":45} | {"Rows":>10}')
        print('-' * 70)
        for t in stats['tables']:
            rows = f'{t["rows"]:,}' if isinstance(t['rows'], int) else t['rows']
            print(f'{t["name"]:45} | {rows:>10}')
    else:
        for i, table in enumerate(tables, 1):
            print(f'  {i:3}. {table}')

    print('\n' + '=' * 70)


def print_table_info(conn: sqlite3.Connection, table_name: str, show_sample: bool = False):
    """Print detailed info about a table."""
    info = get_table_info(conn, table_name)

    print('=' * 70)
    print(f'TABLE: {info["name"]}')
    print(f'Rows: {info["row_count"]:,}' if isinstance(info["row_count"], int) else f'Rows: {info["row_count"]}')
    print('=' * 70)

    print(f'\nCOLUMNS ({len(info["columns"])}):')
    print('-' * 70)
    print(f'{"#":3} | {"Name":30} | {"Type":12} | {"PK":2} | {"NotNull":7} | Default')
    print('-' * 70)
    for col in info['columns']:
        pk = '*' if col['pk'] else ''
        nn = 'YES' if col['notnull'] else ''
        default = col['default'] or ''
        print(f'{col["cid"]:3} | {col["name"]:30} | {col["type"]:12} | {pk:2} | {nn:7} | {default}')

    if info['indexes']:
        print(f'\nINDEXES ({len(info["indexes"])}):')
        print('-' * 70)
        for idx in info['indexes']:
            print(f'  - {idx.get("name", "unnamed")} (unique: {idx.get("unique", 0)})')

    if show_sample:
        sample = get_table_sample(conn, table_name)
        if sample and 'error' not in sample[0]:
            print(f'\nSAMPLE DATA (first {len(sample)} rows):')
            print('-' * 70)
            for i, row in enumerate(sample, 1):
                print(f'Row {i}:')
                for k, v in list(row.items())[:10]:  # Limit columns shown
                    val = str(v)[:50] if v else 'NULL'
                    print(f'  {k}: {val}')
                print()

    print('=' * 70)


def print_column_search(conn: sqlite3.Connection, column_pattern: str):
    """Print tables containing columns matching pattern."""
    matches = find_tables_with_column(conn, column_pattern)

    print('=' * 70)
    print(f'TABLES WITH COLUMNS MATCHING: "{column_pattern}"')
    print(f'Found {len(matches)} tables')
    print('=' * 70)

    for match in matches:
        print(f'\n{match["table"]}:')
        print(f'  Matching: {", ".join(match["matching_columns"])}')
        print(f'  All cols: {match["all_columns"][:8]}{"..." if len(match["all_columns"]) > 8 else ""}')

    print('\n' + '=' * 70)


def print_full_schema(conn: sqlite3.Connection):
    """Print complete schema dump."""
    tables = get_all_tables(conn)

    print('=' * 70)
    print('COMPLETE DATABASE SCHEMA')
    print(f'Total Tables: {len(tables)}')
    print('=' * 70)

    for table in tables:
        info = get_table_info(conn, table)
        cols = ', '.join([f'{c["name"]} {c["type"]}' for c in info['columns']])
        rows = info['row_count']
        print(f'\n{table} ({rows} rows):')
        print(f'  {cols[:100]}{"..." if len(cols) > 100 else ""}')

    print('\n' + '=' * 70)


def main():
    parser = argparse.ArgumentParser(description='Inspect database schema')
    parser.add_argument('--table', type=str, help='Show specific table details')
    parser.add_argument('--find', type=str, help='Find tables with column matching pattern')
    parser.add_argument('--counts', action='store_true', help='Show row counts for all tables')
    parser.add_argument('--sample', action='store_true', help='Show sample data (with --table)')
    parser.add_argument('--full', action='store_true', help='Full schema dump')
    parser.add_argument('--db', type=str, help='Path to database file')

    args = parser.parse_args()

    conn = get_db_connection(args.db)

    if args.table:
        print_table_info(conn, args.table, show_sample=args.sample)
    elif args.find:
        print_column_search(conn, args.find)
    elif args.full:
        print_full_schema(conn)
    else:
        print_table_list(conn, show_counts=args.counts)

    conn.close()


if __name__ == '__main__':
    main()
