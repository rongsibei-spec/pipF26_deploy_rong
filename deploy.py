#!/usr/bin/env python3
"""Apply schema.sql and load class_dataset.csv into DATABASE_URL from .env."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
SCHEMA_PATH = ROOT / "schema.sql"
CSV_PATH = ROOT / "class_dataset.csv"

SCHOOL_YEAR = {
    "first-year": "first_year",
    "first_year": "first_year",
    "sophomore": "sophomore",
    "junior": "junior",
    "senior": "senior",
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


def normalize_netid(raw: str) -> str:
    value = raw.strip().lower()
    if value.endswith("@nyu.edu"):
        value = value[: -len("@nyu.edu")]
    return value


def split_list(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    items = []
    seen: set[str] = set()
    for part in raw.split(";"):
        item = part.strip()
        if item and item not in seen:
            seen.add(item)
            items.append(item)
    return items


def nullable_text(raw: str) -> str | None:
    value = raw.strip()
    if not value or value == "#NAME?":
        return None
    return value


def load_students() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def deploy() -> None:
    if not SCHEMA_PATH.exists():
        sys.exit(f"Missing schema file: {SCHEMA_PATH}")
    if not CSV_PATH.exists():
        sys.exit(f"Missing dataset file: {CSV_PATH}")

    rows = load_students()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = psycopg2.connect(load_database_url())
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DROP TABLE IF EXISTS student_availability, student_tool,
                    student, availability_slot, tool CASCADE
                    """
                )
                cur.execute(schema_sql)

                student_sql = """
                    INSERT INTO student (
                        netid, full_name, school_year, intro_programming,
                        skill_programming, skill_data_stats, skill_frontend_design,
                        skill_business_pitch, working_style, interests,
                        semester_goal, submitted_at
                    ) VALUES (
                        %(netid)s, %(full_name)s, %(school_year)s, %(intro_programming)s,
                        %(skill_programming)s, %(skill_data_stats)s,
                        %(skill_frontend_design)s, %(skill_business_pitch)s,
                        %(working_style)s, %(interests)s, %(semester_goal)s,
                        %(submitted_at)s
                    )
                """
                tool_sql = """
                    INSERT INTO student_tool (netid, tool_name)
                    VALUES (%s, %s)
                """
                avail_sql = """
                    INSERT INTO student_availability (netid, slot_label)
                    VALUES (%s, %s)
                """

                tool_count = 0
                avail_count = 0
                null_working_style = 0
                seen_netids: set[str] = set()

                for row in rows:
                    netid = normalize_netid(row["netid"])
                    if not netid:
                        sys.exit("Encountered an empty netid in class_dataset.csv.")
                    if netid in seen_netids:
                        sys.exit(f"Duplicate netid after cleanup: {netid}")
                    seen_netids.add(netid)

                    school_year_raw = row["school_year"].strip().lower()
                    school_year = SCHOOL_YEAR.get(school_year_raw)
                    if school_year is None:
                        sys.exit(f"Unknown school_year {row['school_year']!r} for {netid}")

                    working_style = nullable_text(row["working_style"])
                    if working_style is None:
                        null_working_style += 1

                    cur.execute(
                        student_sql,
                        {
                            "netid": netid,
                            "full_name": row["name"].strip(),
                            "school_year": school_year,
                            "intro_programming": row["intro_programming"].strip(),
                            "skill_programming": int(row["skill_programming"]),
                            "skill_data_stats": int(row["skill_data_stats"]),
                            "skill_frontend_design": int(row["skill_frontend_design"]),
                            "skill_business_pitch": int(row["skill_business_pitch"]),
                            "working_style": working_style,
                            "interests": nullable_text(row["interests"]),
                            "semester_goal": nullable_text(row["semester_goal"]),
                            "submitted_at": row["submitted_at"].strip(),
                        },
                    )

                    for tool in split_list(row["tools"]):
                        cur.execute(tool_sql, (netid, tool))
                        tool_count += 1
                    for slot in split_list(row["availability"]):
                        cur.execute(avail_sql, (netid, slot))
                        avail_count += 1

                cur.execute("SELECT COUNT(*) FROM student")
                student_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM student_tool")
                db_tool_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM student_availability")
                db_avail_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM tool")
                lookup_tools = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM availability_slot")
                lookup_slots = cur.fetchone()[0]

        print("Deployed schema.sql and class_dataset.csv.")
        print(f"  lookup tools: {lookup_tools}")
        print(f"  lookup availability slots: {lookup_slots}")
        print(f"  students: {student_count}")
        print(f"  student_tool rows: {db_tool_count} (inserted {tool_count})")
        print(f"  student_availability rows: {db_avail_count} (inserted {avail_count})")
        print(f"  working_style stored as NULL: {null_working_style}")
    finally:
        conn.close()


if __name__ == "__main__":
    deploy()
