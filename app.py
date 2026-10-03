import logging
import os
import random
import socket
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "local")
PORT = int(os.getenv("PORT", "5000"))
DATABASE_URL = os.getenv("DATABASE_URL")
START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        cur.execute("SELECT COUNT(*) FROM tasks")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("""
                INSERT INTO tasks (title, done) VALUES
                ('Build the Flask app', TRUE),
                ('Push code to GitHub', TRUE),
                ('Containerize with Docker', TRUE),
                ('Add PostgreSQL', FALSE)
            """)
    conn.close()


@app.context_processor
def inject_globals():
    return {
        "version": APP_VERSION,
        "env": APP_ENV,
        "hostname": socket.gethostname(),
    }


@app.after_request
def log_request(response):
    app.logger.info(
        "%s %s -> %s", request.method, request.path, response.status_code
    )
    return response


@app.route("/")
def home():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        task_count = cur.fetchone()[0]
    conn.close()
    return render_template("index.html", task_count=task_count)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    conn = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO tasks (title, done) VALUES (%s, FALSE)", (title,))
            app.logger.info("Task added: %s", title)
        conn.close()
        return redirect(url_for("tasks_page"))

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
        tasks = cur.fetchall()
    conn.close()
    return render_template("tasks.html", tasks=tasks)


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE tasks SET done = NOT done WHERE id = %s", (task_id,))
    conn.close()
    app.logger.info("Task %s toggled", task_id)
    return redirect(url_for("tasks_page"))


@app.route("/api/tasks", methods=["GET"])
def api_list_tasks():
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
        tasks = cur.fetchall()
    conn.close()
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="title is required"), 400

    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done",
            (title,),
        )
        task = cur.fetchone()
    conn.close()
    app.logger.info("Task added via API: %s", title)
    return jsonify(task), 201


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/version")
def version():
    return jsonify(
        version=APP_VERSION,
        environment=APP_ENV,
        hostname=socket.gethostname(),
        uptime_seconds=round(time.time() - START_TIME),
    )


@app.route("/slow")
def slow():
    delay = round(random.uniform(1, 3), 2)
    time.sleep(delay)
    return jsonify(message="slow response", delay_seconds=delay)


@app.route("/error")
def error():
    app.logger.error("Deliberate error triggered on /error")
    return jsonify(error="deliberate failure"), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)