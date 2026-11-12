import os
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


def database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL is not set")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/names")
def names():
    conn = psycopg2.connect(database_url())
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT full_name FROM student ORDER BY full_name")
            return jsonify([row[0] for row in cur.fetchall()])
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
