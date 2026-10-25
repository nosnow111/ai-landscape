# AI Landscape Dashboard

A personal site that auto-generates daily comparisons of the AI ecosystem using the Claude API. Content is refreshed on a schedule via GitHub Actions and served as a static site on GitHub Pages.

## Live Site
https://nosnow111.github.io/ai-landscape

## What It Covers
- **Code Generation Tools** — Claude Code, GitHub Copilot, Cursor, Codeium, etc.
- **Major AI Models** — GPT-4o, Claude, Gemini, Llama, Grok, DeepSeek, etc.
- **Model Repositories** — HuggingFace, Ollama, Replicate, Together AI, etc.
- **AI in Databases** — Snowflake Cortex, BigQuery ML, pgvector, Amazon Bedrock, etc.
- **Observability & Cost** — LangSmith, Helicone, Weights & Biases, Arize AI, etc.
- **Image Generation** — Midjourney, DALL-E, Stable Diffusion, Flux, Adobe Firefly, etc.
- **Video Generation** — Sora, Runway, Pika, Kling, Luma, HeyGen, etc.
- **Web Scrapers & Automation** — Firecrawl, Apify, AgentQL, Browserbase, etc.
- **Workspace & Productivity** — NotebookLM, M365 Copilot, Notion AI, Perplexity, Otter.ai, etc.

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

### 2. Add your API keys
```bash
cp .env.example .env
# Edit .env and set:
#   ANTHROPIC_API_KEY=your_key_here   (required)
#   TAVILY_API_KEY=your_key_here      (optional — enables live web research)
```

### 3. Run locally
```bash
# Generate + build + publish in one command:
python generator.py && python build.py && git add content/ docs/ && git commit -m "Regenerate content" && git push

# Or step by step:
python generator.py   # generate content (all 9 sections run in parallel)
python build.py       # build static site
open docs/index.html  # view in browser
```

## Auto-Refresh
GitHub Actions runs daily at midnight UTC. To trigger manually:
- Go to **Actions** → **Refresh AI Landscape** → **Run workflow**

## Cost
- **Hosting:** Free (GitHub Pages)
- **Content generation:** ~$0.10 per refresh via Claude API
