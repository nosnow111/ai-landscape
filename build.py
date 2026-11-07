import os
import json
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
VENDOR_CACHE_PATH = os.path.join(CONTENT_DIR, "vendor_news_cache.json")
REFRESH_HOURS = int(os.environ.get("REFRESH_INTERVAL_HOURS", 24))

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(_CONFIG_PATH) as _f:
    SITE_CONFIG = json.load(_f)


def load_content(key):
    path = os.path.join(CONTENT_DIR, f"{key}.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def build():
    os.makedirs(DOCS_DIR, exist_ok=True)
    env = Environment(loader=FileSystemLoader("templates"))

    def load_news_sorted(key):
        data = load_content(key)
        if "items" in data:
            data["items"] = sorted(data["items"], key=lambda x: x.get("date", ""), reverse=True)
        return data

    sections = {
        "code_tools": load_content("code_tools"),
        "models": load_content("models"),
        "repositories": load_content("repositories"),
        "enterprise_apis": load_content("enterprise_apis"),
        "ml_platforms": load_content("ml_platforms"),
        "databases": load_content("databases"),
        "observability": load_content("observability"),
        "image_gen": load_content("image_gen"),
        "video_gen": load_content("video_gen"),
        "mcp_tools": load_content("mcp_tools"),
        "web_scrapers": load_content("web_scrapers"),
        "workspace": load_content("workspace"),
        "fine_tuning": load_content("fine_tuning"),
        "llm_optimization": load_content("llm_optimization"),
        "emerging_trends": load_content("emerging_trends"),
        "model_pricing": load_content("model_pricing"),
        "ai_news": load_news_sorted("ai_news"),
    }

    # Vendor news rolling cache — if today has no vendor items, inject cached ones
    ai_news_items = sections.get("ai_news", {}).get("items", [])
    vendor_items = [i for i in ai_news_items if i.get("category") == "vendor"]
    vendor_cache_date = None
    if vendor_items:
        with open(VENDOR_CACHE_PATH, "w") as _vf:
            json.dump({"items": vendor_items, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}, _vf, indent=2)
    elif os.path.exists(VENDOR_CACHE_PATH):
        _cache = json.load(open(VENDOR_CACHE_PATH))
        _cached = _cache.get("items", [])
        vendor_cache_date = _cache.get("date")
        if _cached:
            sections["ai_news"]["items"] = ai_news_items + _cached

    html = env.get_template("index.html").render(
        sections=sections, refresh_hours=REFRESH_HOURS, config=SITE_CONFIG,
        vendor_cache_date=vendor_cache_date
    )
    out = os.path.join(DOCS_DIR, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"Built {out}")

    news_html = env.get_template("news.html").render(
        ai_news=sections["ai_news"], refresh_hours=REFRESH_HOURS, config=SITE_CONFIG
    )
    news_out = os.path.join(DOCS_DIR, "news.html")
    with open(news_out, "w") as f:
        f.write(news_html)
    print(f"Built {news_out}")



if __name__ == "__main__":
    build()
