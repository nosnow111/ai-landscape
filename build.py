import os
import json
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
REFRESH_HOURS = int(os.environ.get("REFRESH_INTERVAL_HOURS", 24))


def load_content(key):
    path = os.path.join(CONTENT_DIR, f"{key}.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def build():
    os.makedirs(DOCS_DIR, exist_ok=True)
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")

    sections = {
        "code_tools": load_content("code_tools"),
        "models": load_content("models"),
        "repositories": load_content("repositories"),
        "databases": load_content("databases"),
        "observability": load_content("observability"),
        "image_gen": load_content("image_gen"),
        "video_gen": load_content("video_gen"),
        "web_scrapers": load_content("web_scrapers"),
        "workspace": load_content("workspace"),
        "fine_tuning": load_content("fine_tuning"),
        "llm_optimization": load_content("llm_optimization"),
    }

    html = template.render(sections=sections, refresh_hours=REFRESH_HOURS)
    out = os.path.join(DOCS_DIR, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"Built {out}")


if __name__ == "__main__":
    build()
