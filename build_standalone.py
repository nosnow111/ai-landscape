"""
Builds docs/standalone.html — a single self-contained file combining the
full dashboard, presentation slides, and news page.

No external dependencies: Tailwind is inlined, all content is embedded.
Safe to email, share via Slack, or open behind any corporate firewall.
"""

import os
import json
import urllib.request
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
DOCS_DIR    = os.path.join(os.path.dirname(__file__), "docs")
TAILWIND_URL = "https://cdn.tailwindcss.com"
TAILWIND_CACHE = "/tmp/tailwind_standalone.js"


def load_content(key):
    path = os.path.join(CONTENT_DIR, f"{key}.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def fetch_tailwind() -> str:
    if os.path.exists(TAILWIND_CACHE):
        with open(TAILWIND_CACHE) as f:
            return f.read()
    print("  Fetching Tailwind CSS...")
    req = urllib.request.Request(TAILWIND_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=20).read().decode()
    with open(TAILWIND_CACHE, "w") as f:
        f.write(data)
    return data


def extract_body(html: str) -> str:
    """Return the inner HTML of <body>, stripping the Tailwind CDN script tag."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove GA and Tailwind CDN script tags — they'll be inlined at the top level
    for tag in soup.find_all("script"):
        src = tag.get("src", "")
        if "tailwindcss" in src or "googletagmanager" in src or "gtag" in src.lower():
            tag.decompose()
    # Also remove inline gtag() config blocks
    for tag in soup.find_all("script"):
        if tag.string and ("gtag(" in tag.string or "dataLayer" in tag.string):
            tag.decompose()
    body = soup.find("body")
    return body.decode_contents() if body else ""


def extract_styles(html: str) -> str:
    """Return all <style> block contents from the page."""
    soup = BeautifulSoup(html, "html.parser")
    styles = []
    for tag in soup.find_all("style"):
        styles.append(tag.string or "")
    return "\n".join(styles)


def build_standalone():
    os.makedirs(DOCS_DIR, exist_ok=True)

    sections = {
        "code_tools":       load_content("code_tools"),
        "models":           load_content("models"),
        "repositories":     load_content("repositories"),
        "enterprise_apis":  load_content("enterprise_apis"),
        "ml_platforms":     load_content("ml_platforms"),
        "databases":        load_content("databases"),
        "observability":    load_content("observability"),
        "image_gen":        load_content("image_gen"),
        "video_gen":        load_content("video_gen"),
        "mcp_tools":        load_content("mcp_tools"),
        "web_scrapers":     load_content("web_scrapers"),
        "workspace":        load_content("workspace"),
        "fine_tuning":      load_content("fine_tuning"),
        "llm_optimization": load_content("llm_optimization"),
        "emerging_trends":  load_content("emerging_trends"),
        "ai_news":          load_content("ai_news"),
    }

    env = Environment(loader=FileSystemLoader("templates"))
    refresh_hours = int(os.environ.get("REFRESH_INTERVAL_HOURS", 24))

    print("  Rendering templates...")
    dashboard_html   = env.get_template("index.html").render(sections=sections, refresh_hours=refresh_hours)
    presentation_html = open(os.path.join(DOCS_DIR, "about.html")).read()
    news_html        = env.get_template("news.html").render(ai_news=sections["ai_news"], refresh_hours=refresh_hours)

    tailwind_js = fetch_tailwind()

    # Pull per-page custom styles
    dashboard_styles    = extract_styles(dashboard_html)
    presentation_styles = extract_styles(presentation_html)
    news_styles         = extract_styles(news_html)

    dashboard_body    = extract_body(dashboard_html)
    presentation_body = extract_body(presentation_html)
    news_body         = extract_body(news_html)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Landscape Dashboard · Standalone</title>
  <script>{tailwind_js}</script>
  <style>
    /* ── shared ── */
    html {{ scroll-behavior: smooth; }}
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    .top-nav-btn {{
      padding: 6px 16px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
      border: 2px solid transparent;
      color: #4338ca;
      background: transparent;
    }}
    .top-nav-btn:hover {{ background: #eef2ff; }}
    .top-nav-btn.active {{ background: #4f46e5; color: white; border-color: #4f46e5; }}

    /* ── dashboard styles ── */
    {dashboard_styles}

    /* ── presentation styles ── */
    {presentation_styles}

    /* ── news styles ── */
    {news_styles}
  </style>
</head>
<body class="bg-gray-50 text-gray-800 font-sans">

<!-- ── Top-level view switcher ── -->
<div style="position:sticky;top:0;z-index:100;background:white;border-bottom:2px solid #e0e7ff;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
  <div style="max-width:1280px;margin:0 auto;padding:6px 16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <span style="font-weight:800;font-size:0.85rem;color:#1e3a8a;margin-right:6px;">AI Landscape</span>
    <button class="top-nav-btn active" onclick="showView('dashboard')">📊 Dashboard</button>
    <button class="top-nav-btn" onclick="showView('presentation')">📋 About</button>
    <button class="top-nav-btn" onclick="showView('news')">📰 News</button>
    <span style="margin-left:auto;font-size:0.65rem;color:#94a3b8;">Standalone · {generated_at}</span>
  </div>
</div>

<!-- ── Dashboard ── -->
<div id="view-dashboard" class="view active">
{dashboard_body}
</div>

<!-- ── Presentation ── -->
<div id="view-presentation" class="view">
{presentation_body}
</div>

<!-- ── News ── -->
<div id="view-news" class="view">
{news_body}
</div>

<script>
  function showView(name) {{
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.top-nav-btn').forEach(b => {{
      b.classList.remove('active');
      if (b.getAttribute('onclick') === "showView('" + name + "')") b.classList.add('active');
    }});
    document.getElementById('view-' + name).classList.add('active');
    window.scrollTo(0, 0);
  }}

  // Fix internal links so "Back to Dashboard" etc. switch views instead of navigating
  document.querySelectorAll('a[href="index.html"]').forEach(a => {{
    a.href = '#';
    a.addEventListener('click', e => {{ e.preventDefault(); showView('dashboard'); }});
  }});
  document.querySelectorAll('a[href="news.html"]').forEach(a => {{
    a.href = '#';
    a.addEventListener('click', e => {{ e.preventDefault(); showView('news'); }});
  }});
  document.querySelectorAll('a[href="about.html"]').forEach(a => {{
    a.href = '#';
    a.addEventListener('click', e => {{ e.preventDefault(); showView('presentation'); }});
  }});
</script>
</body>
</html>"""

    out = os.path.join(DOCS_DIR, "standalone.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"  Built {out} ({os.path.getsize(out) // 1024} KB)")

    # Standalone presentation only — about.html with Tailwind inlined
    soup = BeautifulSoup(presentation_html, "html.parser")
    for tag in soup.find_all("script"):
        src = tag.get("src", "")
        if "tailwindcss" in src:
            tag.replace_with(BeautifulSoup(f"<script>{tailwind_js}</script>", "html.parser"))
        elif "googletagmanager" in src or "gtag(" in (tag.string or "") or "dataLayer" in (tag.string or ""):
            tag.decompose()
    # Reroute dashboard/news links to live site instead of local files
    for a in soup.find_all("a", href=True):
        if a["href"] == "index.html":
            a["href"] = "https://nosnow111.github.io/ai-landscape/"
        elif a["href"] == "news.html":
            a["href"] = "https://nosnow111.github.io/ai-landscape/news.html"
    pres_out = os.path.join(DOCS_DIR, "about-standalone.html")
    with open(pres_out, "w") as f:
        f.write(str(soup))
    print(f"  Built {pres_out} ({os.path.getsize(pres_out) // 1024} KB)")


if __name__ == "__main__":
    build_standalone()
