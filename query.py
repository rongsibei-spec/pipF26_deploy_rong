#!/usr/bin/env python3
"""Run starter or ad-hoc SQL against DATABASE_URL from .env."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

STARTER_QUERIES = {
    "1": (
        "All students",
        """
        SELECT netid, full_name, school_year, intro_programming, submitted_at
        FROM student
        ORDER BY school_year, full_name
        """,
    ),
    "2": (
        "Skill averages by school year",
        """
        SELECT
            school_year,
            COUNT(*) AS students,
            ROUND(AVG(skill_programming), 2) AS avg_programming,
            ROUND(AVG(skill_data_stats), 2) AS avg_data_stats,
            ROUND(AVG(skill_frontend_design), 2) AS avg_frontend,
            ROUND(AVG(skill_business_pitch), 2) AS avg_pitch
        FROM student
        GROUP BY school_year
        ORDER BY school_year
        """,
    ),
    "3": (
        "How many students listed each tool",
        """
        SELECT t.name AS tool, COUNT(st.netid) AS students
        FROM tool t
        LEFT JOIN student_tool st ON st.tool_name = t.name
        GROUP BY t.name
        ORDER BY students DESC, t.name
        """,
    ),
    "4": (
        "Students available on weekend mornings",
        """
        SELECT s.netid, s.full_name, s.school_year
        FROM student s
        JOIN student_availability sa ON sa.netid = s.netid
        WHERE sa.slot_label = 'Weekend mornings'
        ORDER BY s.full_name
        """,
    ),
    "5": (
        "Intro programming background",
        """
        SELECT intro_programming, COUNT(*) AS students
        FROM student
        GROUP BY intro_programming
        ORDER BY students DESC
        """,
    ),
    "6": (
        "Students with programming skill 4+",
        """
        SELECT netid, full_name, school_year, skill_programming, skill_data_stats
        FROM student
        WHERE skill_programming >= 4
        ORDER BY skill_programming DESC, full_name
        """,
    ),
}


def load_database_url() -> str:
    if not ENV_PATH.exists():
        sys.exit("Missing .env. Copy .env.example and set DATABASE_URL.")
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            url = value.strip().strip('"').strip("'")
            if url:
                return url
    sys.exit("DATABASE_URL is not set in .env.")


def connect():
    return psycopg2.connect(load_database_url())


def format_table(rows: list[dict]) -> str:
    if not rows:
        return "(no rows)"
    columns = list(rows[0].keys())
    cells = [[("" if row[col] is None else str(row[col])) for col in columns] for row in rows]
    widths = [len(col) for col in columns]
    for row in cells:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    rule = "-+-".join("-" * widths[i] for i in range(len(columns)))
    body = "\n".join(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in cells)
    return f"{header}\n{rule}\n{body}\n({len(rows)} row{'s' if len(rows) != 1 else ''})"


def run_sql(sql: str) -> None:
    conn = connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                if cur.description is None:
                    print(f"OK, {cur.rowcount} row(s) affected.")
                    return
                print(format_table(list(cur.fetchall())))
    finally:
        conn.close()


def print_menu() -> None:
    print("Starter queries")
    for key, (title, _) in STARTER_QUERIES.items():
        print(f"  {key}) {title}")
    print("  sql) run custom SQL")
    print("  q) quit")


def interactive() -> None:
    print("Connected. Student intake database.")
    print_menu()
    while True:
        try:
            choice = input("\nquery> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not choice or choice in {"q", "quit", "exit"}:
            return
        if choice in {"h", "help", "menu"}:
            print_menu()
            continue
        if choice in {"sql", "s"}:
            print("Enter SQL. End with a blank line.")
            lines: list[str] = []
            while True:
                try:
                    line = input("sql> ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    lines = []
                    break
                if line.strip() == "":
                    break
                lines.append(line)
            sql = "\n".join(lines).strip()
            if not sql:
                continue
            try:
                run_sql(sql)
            except Exception as exc:
                print(f"Error: {exc}")
            continue
        if choice not in STARTER_QUERIES:
            print("Unknown choice. Type help for the menu.")
            continue
        title, sql = STARTER_QUERIES[choice]
        print(f"-- {title}")
        try:
            run_sql(sql)
        except Exception as exc:
            print(f"Error: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the class intake database.")
    parser.add_argument("--list", action="store_true", help="list starter queries")
    parser.add_argument("--run", metavar="N", help="run starter query by number (1-6)")
    parser.add_argument("--sql", metavar="SQL", help="run a custom SQL statement")
    args = parser.parse_args()

    if args.list:
        print_menu()
        return
    if args.run:
        if args.run not in STARTER_QUERIES:
            sys.exit(f"Unknown query {args.run!r}. Use --list.")
        title, sql = STARTER_QUERIES[args.run]
        print(f"-- {title}")
        run_sql(sql)
        return
    if args.sql:
        run_sql(args.sql)
        return
    interactive()


if __name__ == "__main__":
    main()
