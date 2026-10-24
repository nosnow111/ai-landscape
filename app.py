import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
REFRESH_HOURS = int(os.environ.get("REFRESH_INTERVAL_HOURS", 24))


def load_content(key: str) -> dict:
    path = os.path.join(CONTENT_DIR, f"{key}.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


@app.route("/")
def index():
    sections = {
        "code_tools": load_content("code_tools"),
        "models": load_content("models"),
        "repositories": load_content("repositories"),
        "databases": load_content("databases"),
        "observability": load_content("observability"),
    }
    return render_template("index.html", sections=sections, refresh_hours=REFRESH_HOURS)


@app.route("/api/content/<key>")
def api_content(key):
    allowed = {"code_tools", "models", "repositories", "databases", "observability"}
    if key not in allowed:
        return jsonify({"error": "not found"}), 404
    return jsonify(load_content(key))


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    from generator import run_generation
    try:
        run_generation()
        return jsonify({"status": "ok", "refreshed_at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def scheduled_refresh():
    from generator import run_generation
    run_generation()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_refresh, "interval", hours=REFRESH_HOURS)
    scheduler.start()


if __name__ == "__main__":
    if os.environ.get("ANTHROPIC_API_KEY"):
        start_scheduler()
    app.run(debug=True, port=5000)
