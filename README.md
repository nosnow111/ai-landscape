# AI Landscape Dashboard

A static site that auto-generates daily comparisons of the AI ecosystem using Claude and GPT-4o. Content refreshes nightly via GitHub Actions and is served free on GitHub Pages.

**Live site:** https://nosnow111.github.io/ai-landscape

## What It Covers (17 sections)

**Ranked by adoption:**
- **Code Generation Tools** — Claude Code, GitHub Copilot, Cursor, Devin Desktop, etc.
- **Major AI Models** — GPT-4o, Claude, Gemini, Llama, Grok, DeepSeek, etc.
- **Image Generation** — Midjourney, DALL-E, Stable Diffusion, Flux, Adobe Firefly, etc.
- **Video Generation** — Runway, Pika, Kling, Luma, HeyGen, Synthesia, etc.
- **MCP Tools & Servers** — Composio, Smithery, GitHub MCP, Stripe MCP, Figma MCP, n8n MCP, etc.
- **Web Scrapers & Automation** — Firecrawl, Apify, Browserbase, Playwright, etc.
- **Workspace & Productivity** — Gemini Notebook, M365 Copilot, Notion AI, Perplexity, Otter.ai, etc.
- **Fine-Tuning Platforms** — OpenAI fine-tuning API, Hugging Face AutoTrain, Axolotl, Unsloth, etc.
- **Enterprise AI APIs** — AWS Bedrock, Azure OpenAI, Google Vertex AI, Snowflake Cortex, etc.
- **ML Training & Deployment** — SageMaker, Vertex AI, Databricks, Azure ML, Modal, etc.
- **Emerging AI Trends** — reasoning models, agents, inference scaling, multimodal, etc.
- **Token Prices** — current input/output pricing per 1M tokens across major commercial LLMs, sorted by adoption

**Reference sections:**
- **Model Repositories** — HuggingFace, Ollama, Replicate, Together AI, Groq, etc.
- **AI in Databases** — Snowflake Cortex, BigQuery ML, pgvector, Aurora ML, etc.
- **Observability & Cost** — LangSmith, Helicone, Weights & Biases, Arize AI, etc.
- **LLM Optimization** — prompt caching, semantic caching, model right-sizing, RAG vs long context, etc.
- **Daily AI News** — headlines from Reuters, AP News, WSJ, Bloomberg, CNBC and more, split into Industry and Vendor columns

## How Rankings Work

Rankings use real-world adoption signals (API volume, developer surveys, GitHub stars, enterprise deployment patterns) grounded by live web research before every generation. Each ranked section is independently scored by two models from different companies:

- **Claude Opus 4.8** — primary ranking
- **GPT-4o** — independent cross-check

Each tool shows an agreement badge:
- ✅ **Consensus** — both models agree on rank
- 🟡 **Minor diff** — ranked within 2 positions of each other
- 🔴 **Disagree** — ranked 3+ positions apart
- ⚪ **GPT-4o excluded** — GPT-4o didn't include this tool in its top list

Using two models from different companies matters: Claude and GPT-4o have different training data, so disagreements are meaningful signals rather than noise.

## Architecture

```
pipeline.py          # Orchestrator: research → generate → validate → build
generator.py         # Claude Opus + GPT-4o → writes content/*.json (parallel)
research.py          # Web search (Firecrawl → Tavily → Serper) — live grounding
validate_links.py    # URL checker: fetches pages, judges relevance via Haiku
build.py             # Reads JSON → renders docs/ via Jinja2
build_standalone.py  # Generates self-contained offline HTML versions
config.json          # Site identity: title, author, tagline, about URL
url_overrides.json   # Permanent fix/skip registry for known problem URLs
include.json         # Whitelist of authoritative domains for auto-fixer
templates/           # Tailwind CSS dashboard + news templates
checkpoints/         # Pipeline stage checkpoints (skip completed stages on re-run)
content/             # Auto-generated JSON (committed by Actions)
docs/                # Static site served by GitHub Pages
.github/workflows/refresh.yml  # Daily cron at midnight UTC
```

## Running Locally

### 1. Clone and install
```bash
git clone https://github.com/nosnow111/ai-landscape.git
cd ai-landscape
pip install -r requirements.txt
```

### 2. Add API keys
```bash
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=   (required — Claude Opus primary generation)
#   TAVILY_API_KEY=      (required — live web research)
#   OPENAI_API_KEY=      (recommended — GPT-4o cross-check; falls back to Sonnet if missing)
#   FIRECRAWL_API_KEY=   (optional — research primary; Tavily used if missing)
#   SERPER_API_KEY=      (optional — research tertiary fallback)
```

### 3. Run
```bash
python pipeline.py              # full pipeline: research → generate → validate → build
open docs/index.html

# Partial runs (saves API quota):
python pipeline.py --only=build      # rebuild HTML only — zero API calls
python pipeline.py --from=generate   # skip research, re-generate from cached data
python pipeline.py --from=validate   # re-validate + rebuild only
python pipeline.py --force           # ignore checkpoints, run everything fresh

# Link validation only:
python validate_links.py             # check all URLs, print report
python validate_links.py --fix       # auto-fix broken (404) links only
```

## Running Your Own Instance (Fork & Deploy)

Want your own live version? Takes about 10 minutes.

### 1. Fork the repo
Click **Fork** on GitHub. The `content/` and `docs/` folders are already committed so your site will be live immediately with the last generated content.

### 2. Enable GitHub Pages
Go to your fork → **Settings** → **Pages** → Source: **Deploy from a branch** → Branch: `main` / folder: `/docs` → Save.

Your site will be live at `https://<your-username>.github.io/ai-landscape` within a minute.

### 3. Add your API keys as secrets
Go to your fork → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Where to get it | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com | ✅ Required |
| `TAVILY_API_KEY` | app.tavily.com | ✅ Required |
| `OPENAI_API_KEY` | platform.openai.com | Recommended |
| `FIRECRAWL_API_KEY` | firecrawl.dev | Optional |
| `SERPER_API_KEY` | serper.dev | Optional |

### 4. Trigger the first run
Go to **Actions** → **Refresh AI Landscape** → **Run workflow**. It takes 2-3 minutes. After that it runs automatically every night at midnight UTC.

### What it costs to run
| Item | Cost |
|---|---|
| GitHub Actions + Pages | Free |
| Tavily (research) | Free tier — 1,000 req/month; nightly run uses ~35 |
| Firecrawl (research) | Free tier — 1,000 req/month |
| Anthropic (Claude Opus) | ~$1–3/night depending on section count |
| OpenAI (GPT-4o cross-check) | ~$0.50–1/night; skip by omitting `OPENAI_API_KEY` |

To run more cheaply: omit `OPENAI_API_KEY` (drops cross-check badges) and use `--only=build` locally to rebuild HTML without any API calls.
