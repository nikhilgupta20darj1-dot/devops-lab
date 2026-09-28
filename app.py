import logging
import os
import random
import socket
import time

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "local")
PORT = int(os.getenv("PORT", "5001"))
START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

tasks = [
    {"id": 1, "title": "Build the Flask app", "done": True},
    {"id": 2, "title": "Push code to GitHub", "done": False},
    {"id": 3, "title": "Containerize with Docker", "done": False},
]


def next_id():
    return max((t["id"] for t in tasks), default=0) + 1


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
    return render_template("index.html", task_count=len(tasks))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            tasks.append({"id": next_id(), "title": title, "done": False})
            app.logger.info("Task added: %s", title)
        return redirect(url_for("tasks_page"))
    return render_template("tasks.html", tasks=tasks)


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = not t["done"]
            app.logger.info("Task %s toggled", task_id)
    return redirect(url_for("tasks_page"))


@app.route("/api/tasks", methods=["GET"])
def api_list_tasks():
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="title is required"), 400
    task = {"id": next_id(), "title": title, "done": False}
    tasks.append(task)
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
    app.run(host="0.0.0.0", port=PORT)