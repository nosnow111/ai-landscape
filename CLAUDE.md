# AI Landscape Dashboard

## What this project does
A static website that auto-generates daily comparisons of the AI ecosystem.
Claude API generates structured JSON content; a build script renders it to HTML;
GitHub Actions runs everything on a schedule and commits the result to GitHub Pages.

## Project structure
```
generator.py        # Calls Claude API → writes content/*.json (one file per section)
build.py            # Reads content/*.json → renders docs/index.html via Jinja2
templates/index.html # Tailwind CSS dashboard with tab navigation
content/            # Auto-generated JSON files (committed by GitHub Actions)
docs/               # Auto-generated static site (served by GitHub Pages)
.github/workflows/refresh.yml  # Daily cron + manual trigger
```

## How to run locally
```bash
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY
python generator.py           # generates content/*.json
python build.py               # generates docs/index.html
open docs/index.html
```

## Content sections
Each section maps to a JSON file in content/ and a tab in the UI:
- `code_tools` — Top 10 AI code generation tools ranked by adoption
- `models` — Top 10 LLMs ranked by real-world usage
- `repositories` — Model repositories and deployment platforms
- `databases` — AI capabilities in major databases
- `observability` — AI observability and cost monitoring tools
- `image_gen` — Top 10 AI image generation tools ranked by adoption
- `video_gen` — Top 10 AI video generation tools ranked by adoption
- `web_scrapers` — Top 10 AI web scraping and browser automation tools

## Adding a new section
1. Add an entry to `SECTIONS` dict in `generator.py` with a prompt and title
2. Add a new tab button and panel in `templates/index.html`
3. Add the new key to the `sections` dict in `build.py`

## Deployment
- **Hosting:** GitHub Pages — serves from `docs/` on the `main` branch
- **Refresh:** GitHub Actions workflow (`refresh.yml`) runs daily at midnight UTC
  and can be triggered manually from the Actions tab
- **Secret required:** `ANTHROPIC_API_KEY` must be set in repo Settings → Secrets → Actions

## Key decisions
- Static site (no server) keeps hosting free forever on GitHub Pages
- Content JSON is committed to the repo so the site survives even if the API is unavailable
- `max_tokens=8192` prevents JSON truncation on longer sections
- Prompts explicitly request unbiased rankings based on actual usage data
- Tavily web search runs before each Claude call to ground content in live data

## Hosting platforms evaluated (and why rejected)
| Platform | Reason rejected |
|---|---|
| **Railway** | Not accepting new signups at time of setup |
| **Render** | Removed free tier; cheapest plan is $7/month |
| **Koyeb** | Acquired by Mistral AI and shut down their hosting platform |
| **Fly.io** | Free trial only — requires credit card, not permanently free |
| **Hugging Face Spaces** | Docker tier (needed for Flask) is paid; free tiers are static or Gradio only |
| **Google Sites** | UI-only drag-and-drop builder — no GitHub integration, no automation support |
| **GitHub Pages** ✅ | 100% free, integrates directly with Actions workflow, zero ops overhead |
