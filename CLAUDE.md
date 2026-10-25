# AI Landscape Dashboard

## What this project does
A static website that auto-generates daily comparisons of the AI ecosystem.
Claude API generates structured JSON content; a build script renders it to HTML;
GitHub Actions runs everything on a schedule and commits the result to GitHub Pages.

## Project structure
```
pipeline.py         # Orchestrator: research → generate → validate → build (with checkpoints)
generator.py        # Calls Claude Opus + GPT-4o → writes content/*.json
research.py         # Tavily web search — runs before generation for live grounding
validate_links.py   # Validates all URLs; auto-fixes wrong-page links via Tavily + Claude
build.py            # Reads content/*.json → renders docs/index.html via Jinja2
templates/index.html # Tailwind CSS dashboard with tab navigation
content/            # Auto-generated JSON files (committed by GitHub Actions)
docs/               # Auto-generated static site (served by GitHub Pages)
checkpoints/        # Pipeline stage checkpoints (research, generate, validate, build)
validation_report.json  # Latest link validation results
.github/workflows/refresh.yml  # Daily cron + manual trigger
```

## How to run locally
```bash
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY, TAVILY_API_KEY, OPENAI_API_KEY
python pipeline.py            # full pipeline: research → generate → validate → build
open docs/index.html
```

### Pipeline options
```bash
python pipeline.py                    # resume from last checkpoint
python pipeline.py --force            # re-run all stages
python pipeline.py --from=generate   # restart from generate onward
python pipeline.py --from=validate   # re-validate + rebuild only
python pipeline.py --only=build      # rebuild HTML only

python validate_links.py             # validate links only
python validate_links.py --fix       # validate + auto-fix wrong-page URLs
python validate_links.py --dry-run   # show what would be fixed
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
- `workspace` — Top 10 AI productivity and workspace tools ranked by adoption
- `fine_tuning` — Top 10 LLM fine-tuning platforms ranked by adoption; includes when-to-fine-tune guidance
- `llm_optimization` — LLM cost & performance optimization techniques, quick wins, and tooling
- `enterprise_apis` — Top enterprise AI API aggregators (Bedrock, Azure OpenAI, Vertex AI, etc.)
- `ml_platforms` — Top ML training & deployment platforms (SageMaker, Vertex AI, Databricks, etc.)

## Adding a new section
1. Add an entry to `SECTIONS` dict in `generator.py` with a prompt and title
2. Add a new tab button and panel in `templates/index.html`
3. Add the new key to the `sections` dict in `build.py`

## Deployment
- **Hosting:** GitHub Pages — serves from `docs/` on the `main` branch
- **Refresh:** GitHub Actions workflow (`refresh.yml`) runs daily at midnight UTC
  and can be triggered manually from the Actions tab
- **Secrets required** in repo Settings → Secrets → Actions:
  - `ANTHROPIC_API_KEY` — Claude Opus (primary generation)
  - `TAVILY_API_KEY` — web research grounding
  - `OPENAI_API_KEY` — GPT-4o cross-check (falls back to Sonnet if missing)

## Ranking rule (all sections)
Rankings use a 10–15 smart cutoff defined in `_RANK_RULE` in `generator.py`:
- Always include top 10 by adoption
- Extend to #11–15 only if their adoption is within ~25% of #10 (no clear gap)
- Stop at the first significant drop-off; never pad to fill 15

## Section design rationale

### Fine-Tuning vs LLM Optimization — why two separate sections
These are intentionally distinct concepts:
- **Fine-Tuning** (`fine_tuning`) — permanently adapting a base model on your own data using training platforms (OpenAI fine-tuning API, Hugging Face AutoTrain, Axolotl, Unsloth). Changes model weights. High cost, high payoff for domain-specific behavior.
- **LLM Optimization** (`llm_optimization`) — inference-time techniques that cut cost and latency without retraining anything: prompt compression, prompt caching, model right-sizing (Haiku/GPT-4o-mini for simple tasks), semantic caching (GPTCache/Redis), batching, RAG instead of long context, output length control, quantization (self-hosted only). No model weights are changed.

### Knowledge cutoff and Tavily grounding
Claude's training data cuts off at August 2025. Anything after that — new model releases, updated adoption numbers, pricing changes, new tools — requires live data. The pipeline addresses this: Tavily web search (Stage 1) runs before every generation, pulling current stats and recent announcements. That research context is passed directly into the Opus and GPT-4o prompts. Content/*.json files reflect what was current at generation time, not the training cutoff.

## Research strategy (research.py)
Each section fires 3–5 Tavily queries: targeted known-tool queries + broader
"complete list / alternatives / lesser known" discovery queries. Claude is
instructed to include tools found in research even if not named in the prompt.

## Key decisions
- Static site (no server) keeps hosting free forever on GitHub Pages
- Content JSON is committed to the repo so the site survives even if the API is unavailable
- `max_tokens=8192` prevents JSON truncation on longer sections
- Prompts explicitly request unbiased rankings based on actual usage data
- Tavily web search runs before each Claude call to ground content in live data
- Wave (wave.com) — AI meeting recorder — confirmed as workspace tool, not web scraper
- Enterprise/aggregator reach (AWS Bedrock, Azure OpenAI, Snowflake Cortex, Google Vertex AI) is weighted as a positive ranking signal in the models prompt — enterprise traffic via aggregators is invisible in public API stats but represents real adoption
- Research and generation both parallelized with `ThreadPoolExecutor` — all 13 sections run concurrently (~5× faster than sequential)
- Workflow stashes generated files before `git pull --rebase` to avoid "unstaged changes" error, then rebuilds with latest template before committing
- Header attribution: "Curated by Vlad Meyman · Ranked by Claude AI"
- Overview tab includes a collapsible "How Rankings Are Calculated" methodology box explaining signals, aggregator note, and the 10–15 cutoff rule
- **Dual-model cross-check**: Claude Opus 4.8 is primary (most accurate); GPT-4o cross-checks all 9 ranked sections. Each tool shows ✅ Consensus / 🟡 Minor diff / 🔴 Disagree / ⚪ GPT-4o excluded badge. Opus + GPT-4o chosen over two Anthropic models because different training data makes disagreements more meaningful.
- **Pipeline orchestrator** (`pipeline.py`): 4-stage pipeline with checkpoint files. Stages skip automatically if already complete; `--from=<stage>` to restart from any point. Prevents wasted API calls if a run fails partway.
- **Link validator** (`validate_links.py`): fetches every URL, checks page relevance via Claude Haiku, auto-fixes wrong-page links using Tavily search. HTTP 403s treated as valid (major platforms block scrapers). Runs after build; never blocks the commit.
- **URL rule** (`_URL_RULE`): injected into all ranked section prompts — models must have verifiable official pages or be omitted. Prevents hallucinated URLs for unreleased models.

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
