# AI Landscape Dashboard

## What this project does
A static website that auto-generates daily comparisons of the AI ecosystem.
Claude API generates structured JSON content; a build script renders it to HTML;
GitHub Actions runs everything on a schedule and commits the result to GitHub Pages.

## Project structure
```
pipeline.py          # Orchestrator: research → generate → validate → build (with checkpoints)
generator.py         # Calls Claude Opus + GPT-4o → writes content/*.json
research.py          # Web search (Firecrawl → Tavily → Serper) — runs before generation for live grounding
validate_links.py    # Validates all URLs via Claude Haiku; auto-fixes only broken (404) links
build.py             # Reads content/*.json → renders docs/index.html via Jinja2
build_standalone.py  # Generates self-contained offline HTML (standalone.html, about-standalone.html)
config.json          # Site identity: title, author, tagline, about URL — used by build scripts
url_overrides.json   # Permanent fix/skip registry for known problem URLs
include.json         # Whitelist of authoritative domains the auto-fixer may use for replacements
templates/index.html # Tailwind CSS dashboard with tab navigation
content/             # Auto-generated JSON files (committed by GitHub Actions)
docs/                # Auto-generated static site (served by GitHub Pages)
checkpoints/         # Pipeline stage checkpoints (research, generate, validate, build)
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
python pipeline.py --from=generate    # restart from generate onward
python pipeline.py --from=validate    # re-validate + rebuild only
python pipeline.py --only=build       # rebuild HTML only

python validate_links.py              # validate links only, print report
python validate_links.py --fix        # validate + auto-fix broken (404) links
python validate_links.py --dry-run    # show what would be fixed without applying
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
- `mcp_tools` — Top 10 MCP tools ranked by adoption (aggregators, gateways, and individual servers)
- `web_scrapers` — Top 10 AI web scraping and browser automation tools
- `workspace` — Top 10 AI productivity and workspace tools ranked by adoption
- `fine_tuning` — Top 10 LLM fine-tuning platforms ranked by adoption; includes when-to-fine-tune guidance
- `llm_optimization` — LLM cost & performance optimization techniques, quick wins, and tooling
- `enterprise_apis` — Top enterprise AI API aggregators (Bedrock, Azure OpenAI, Vertex AI, etc.)
- `ml_platforms` — Top ML training & deployment platforms (SageMaker, Vertex AI, Databricks, etc.)
- `model_pricing` — Current token pricing per 1M tokens for major commercial LLMs, sorted by adoption
- `ai_news` — Up to 20 recent AI news items (headline, summary, source, date, url); powers the top-of-page news strip and `docs/news.html`
- `emerging_trends` — Top 10 emerging AI technologies/trends ranked by momentum (reasoning models, agents, etc.)

## Adding a new section
1. Add an entry to `SECTIONS` dict in `generator.py` with a prompt and title
2. Add research queries to `QUERIES` dict in `research.py`
3. Add a new tab button and panel in `templates/index.html`
4. Add the new key to the `sections` dict in `build.py` and `build_standalone.py`

## Deployment
- **Hosting:** GitHub Pages — serves from `docs/` on the `main` branch
- **Refresh:** GitHub Actions workflow (`refresh.yml`) runs daily at midnight UTC
  and can be triggered manually from the Actions tab
- **Secrets required** in repo Settings → Secrets → Actions:
  - `ANTHROPIC_API_KEY` — Claude Opus (primary generation)
  - `OPENAI_API_KEY` — GPT-4o cross-check (falls back to Sonnet if missing)
  - `FIRECRAWL_API_KEY` — web research primary (1,000 free/month)
  - `TAVILY_API_KEY` — web research fallback (1,000 free/month)
  - `SERPER_API_KEY` — web research tertiary fallback

## Ranking rule (all sections)
Rankings use a 10–15 smart cutoff defined in `_RANK_RULE` in `generator.py`:
- Always include top 10 by adoption
- Extend to #11–15 only if their adoption is within ~25% of #10 (no clear gap)
- Stop at the first significant drop-off; never pad to fill 15

## Section design rationale

### Fine-Tuning vs LLM Optimization — why two separate sections
- **Fine-Tuning** (`fine_tuning`) — permanently adapting a base model on your own data. Changes model weights. High cost, high payoff for domain-specific behavior.
- **LLM Optimization** (`llm_optimization`) — inference-time techniques (prompt caching, semantic caching, model right-sizing, RAG instead of long context). No model weights changed.

### Knowledge cutoff and web research grounding
Claude's training data cuts off at August 2025. The pipeline addresses this: web search (Stage 1) runs before every generation, pulling current stats and recent announcements. That research context is passed directly into the Opus and GPT-4o prompts.

## Research strategy (research.py)
Each section fires 2 queries per run (~34 total with ai_news at 6). Provider priority: Firecrawl (primary, 1,000 free/month) → Tavily (fallback) → Serper (tertiary). Queries support `(query, days, domains)` tuple syntax for variable Tavily parameters.

## Key decisions
- Static site (no server) keeps hosting free forever on GitHub Pages
- Content JSON is committed to the repo so the site survives even if the API is unavailable
- `max_tokens=8192` prevents JSON truncation on longer sections
- Prompts explicitly request unbiased rankings based on actual usage data
- Web search (Firecrawl → Tavily → Serper) runs before each Claude call to ground content in live data
- Enterprise/aggregator reach (AWS Bedrock, Azure OpenAI, Snowflake Cortex, Google Vertex AI) is weighted as a positive ranking signal in the models prompt
- Research and generation both parallelized with `ThreadPoolExecutor` — all sections run concurrently (~5× faster than sequential)
- Workflow stashes generated files before `git pull --rebase` to avoid "unstaged changes" error, then rebuilds with latest template before committing
- **config.json**: centralizes site identity (title, author, tagline, about URL). Build scripts load it and pass `config=SITE_CONFIG` to all template renders. Template uses `{{ config.* }}`. Branding changes touch one file only.
- **News strip**: dark blue bar between nav and main content; two-column Industry | Vendor layout; links to `docs/news.html` for full 20 items. Rendered only on Overview tab.
- **News full page** (`docs/news.html`): shows all 20 items with full summaries, source links, and back-to-dashboard nav.
- **Header**: "Curated by Vlad Meyman · Ranked by Claude AI · How rankings work →" — the about link helps users who question rankings.
- **Dual-model cross-check**: Claude Opus 4.8 is primary; GPT-4o cross-checks all ranked sections. Each tool shows ✅ Consensus / 🟡 Minor diff / 🔴 Disagree / ⚪ GPT-4o excluded badge. Opus + GPT-4o chosen over two Anthropic models because different training data makes disagreements more meaningful.
- **Pipeline orchestrator** (`pipeline.py`): 4-stage pipeline with checkpoint files. Stages skip automatically if already complete; `--from=<stage>` to restart from any point.
- **Link validator — auto-fixer scope**: only searches for replacements on truly broken links (404/unreachable). Wrong-page judgments (Haiku false-positives) are reported only and handled via `url_overrides.json`. This prevents the fixer from making things worse.
- **Link validator — whitelist** (`include.json`): auto-fixer replacement candidates must come from domains in `include.json`. Any unlisted domain is rejected. Add a domain to `include.json` to trust it; no blocklist maintenance needed.
- **url_overrides.json**: two sections — `fixes` (bad URL → correct replacement applied every run) and `skip` (known valid pages with false-positive validator judgment). Shared pricing pages (anthropic.com/pricing, openai.com/api/pricing, etc.) are in skip — validator can't match per-model names on combined pages.
- **URL rule** (`_URL_RULE`): injected into all ranked section prompts — models must have verifiable official pages or be omitted. Blocks comparison article domains (g2.com, capterra.com, technologymatch.com, kingdee.com, shivojha.com, techradar.com).
- **News source policy**: `ai_news` Tier 1 sources: Reuters, AP News, TechCrunch, The Verge, Wired, Ars Technica, MIT Technology Review, VentureBeat, Fortune, Forbes, CNBC, MarketWatch, BBC, The Guardian, Bloomberg, WSJ, FT, NYT, Washington Post, Axios, The Economist, Fast Company, Business Insider, Nature, Science. Tier 2: official vendor blogs for first-party product announcements only.
- **Tavily news mode**: `ai_news` skips Firecrawl and Serper. Uses Tavily with `topic="news"`, `days=14`, `max_results=10`, and `include_domains=_NEWS_DOMAINS`. Without `include_domains`, Tavily returned junk domains instead of Reuters/WSJ/Bloomberg.
- **ai_news vendor queries**: 6 total queries — 4 standard news, 1 vendor+news-outlet 30-day window (`_VENDOR_DOMAINS_EARLY`), 1 direct vendor blogs only 30-day window (`_VENDOR_BLOGS_ONLY`). Ensures vendor announcements aren't crowded out by market news.
- **News two-column layout**: items tagged `category: "vendor"` or `"industry"`. Dashboard strip shows Industry | Vendor side-by-side. Full summaries on news.html only.
- **ai_news post-gen filter**: items older than 14 days dropped if ≥5 remain; falls back to 30-day; keeps all if fewer than 5 pass. `ai_news.json` never overwritten if 0 items generated.
- **Generation fallbacks**: GPT-4o promoted to primary for ranked sections if Opus returns empty. Sonnet 4.6 fallback for `ai_news` if Opus fails.
- **`--only` flag**: always force-runs the named stage regardless of checkpoint state.
- **`model_pricing` section**: requires research queries — without live pricing data Opus returns non-JSON. Validator skips shared pricing pages (anthropic.com/pricing, openai.com/api/pricing, etc.) via url_overrides.json skip list.

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
