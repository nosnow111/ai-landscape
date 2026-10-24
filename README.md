# AI Landscape Dashboard

A personal site that auto-generates daily comparisons of the AI ecosystem using the Claude API. Content is refreshed on a schedule via GitHub Actions and served as a static site on GitHub Pages.

## Live Site
https://nosnow111.github.io/ai-landscape

## What It Covers
- **Code Generation Tools** — Claude Code, GitHub Copilot, Cursor, Codeium, etc.
- **Major AI Models** — GPT-4o, Claude, Gemini, Llama, Mistral, etc.
- **Model Repositories** — HuggingFace, Ollama, Replicate, Together AI, etc.
- **AI in Databases** — Snowflake Cortex, BigQuery ML, pgvector, Amazon Bedrock, etc.
- **Observability & Cost** — LangSmith, Helicone, Weights & Biases, Arize AI, etc.

## Architecture
```
generator.py        # Calls Claude API → writes content/*.json
build.py            # Reads JSON → renders docs/index.html via Jinja2
templates/index.html # Tailwind CSS dashboard template
.github/workflows/refresh.yml  # Daily cron job (GitHub Actions)
docs/               # Static site served by GitHub Pages
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/nosnow111/ai-landscape.git
cd ai-landscape
pip install -r requirements.txt
```

### 2. Add your Anthropic API key
```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here
```

### 3. Run locally
```bash
python generator.py   # generate content
python build.py       # build static site
open docs/index.html  # view in browser
```

## Auto-Refresh
GitHub Actions runs daily at midnight UTC. To trigger manually:
- Go to **Actions** → **Refresh AI Landscape** → **Run workflow**

## Cost
- **Hosting:** Free (GitHub Pages)
- **Content generation:** ~$0.10 per refresh via Claude API
