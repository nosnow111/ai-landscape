# AI Landscape Dashboard

A personal site that auto-generates daily comparisons of the AI ecosystem using the Claude API. Content is refreshed on a schedule via GitHub Actions and served as a static site on GitHub Pages.

## Live Site
https://nosnow111.github.io/ai-landscape

## What It Covers (13 sections)
- **Code Generation Tools** — Claude Code, GitHub Copilot, Cursor, Codeium, etc.
- **Major AI Models** — GPT-4o, Claude, Gemini, Llama, Grok, DeepSeek, etc.
- **Model Repositories** — HuggingFace, Ollama, Replicate, Together AI, etc.
- **Enterprise AI APIs** — AWS Bedrock, Azure OpenAI, Google Vertex AI, Snowflake Cortex, etc.
- **ML Training & Deployment** — SageMaker, Vertex AI, Databricks, Azure ML, etc.
- **AI in Databases** — Snowflake Cortex, BigQuery ML, pgvector, Aurora ML, etc.
- **Observability & Cost** — LangSmith, Helicone, Weights & Biases, Arize AI, etc.
- **Image Generation** — Midjourney, DALL-E, Stable Diffusion, Flux, Adobe Firefly, etc.
- **Video Generation** — Sora, Runway, Pika, Kling, Luma, HeyGen, etc.
- **Web Scrapers & Automation** — Firecrawl, Apify, AgentQL, Browserbase, etc.
- **Workspace & Productivity** — NotebookLM, M365 Copilot, Notion AI, Perplexity, Otter.ai, etc.
- **Fine-Tuning Platforms** — platforms for permanently adapting a base model on your own data (OpenAI fine-tuning API, Hugging Face AutoTrain, Axolotl, Unsloth, etc.)
- **LLM Optimization** — inference-time techniques to cut costs without retraining: prompt caching, model right-sizing, semantic caching, batching, RAG vs long context, output length control, quantization

## How Rankings Work
Rankings are based on real-world adoption data (API volume, developer surveys, HuggingFace downloads) grounded by live Tavily web search. Each ranked section is independently scored by two models from different companies — **Claude Opus 4.8** (primary) and **GPT-4o** (cross-check) — and each tool shows an agreement badge:
- ✅ **Consensus** — both models agree on rank
- 🟡 **Minor diff** — ranked within 2 positions of each other
- 🔴 **Disagree** — ranked 3+ positions apart
- ⚪ **GPT-4o excluded** — GPT-4o didn't include this tool in its top list

## Architecture
```
pipeline.py          # Orchestrator: research → generate → validate → build
generator.py         # Claude Opus + GPT-4o → writes content/*.json (parallel)
research.py          # Tavily web search — live grounding before each generation
validate_links.py    # URL checker: fetches pages, judges relevance, auto-fixes
build.py             # Reads JSON → renders docs/index.html via Jinja2
templates/index.html # Tailwind CSS dashboard template
checkpoints/         # Pipeline stage checkpoints (skip completed stages on re-run)
.github/workflows/refresh.yml  # Daily cron job (GitHub Actions)
docs/                # Static site served by GitHub Pages
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
#   ANTHROPIC_API_KEY=your_key_here   (required — Claude Opus primary generation)
#   TAVILY_API_KEY=your_key_here      (required — live web research grounding)
#   OPENAI_API_KEY=your_key_here      (recommended — GPT-4o cross-check; falls back to Sonnet)
```

### 3. Run locally
```bash
python pipeline.py            # full pipeline: research → generate → validate → build
open docs/index.html

# Pipeline options:
python pipeline.py --force            # re-run all stages
python pipeline.py --from=generate   # restart from generate onward
python pipeline.py --from=validate   # re-validate + rebuild only
python pipeline.py --only=build      # rebuild HTML only

# Link validation:
python validate_links.py             # check all URLs, print report
python validate_links.py --fix       # check + auto-fix wrong-page URLs
python validate_links.py --dry-run   # show what would be fixed without writing
```

## Auto-Refresh
GitHub Actions runs daily at midnight UTC (`python pipeline.py --force`). To trigger manually:
- Go to **Actions** → **Refresh AI Landscape** → **Run workflow**

Required secrets in repo Settings → Secrets → Actions: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `OPENAI_API_KEY`

## Cost
- **Hosting:** Free (GitHub Pages)
- **Content generation:** ~$0.70/day (Opus + GPT-4o × 9 ranked sections + Tavily searches)
