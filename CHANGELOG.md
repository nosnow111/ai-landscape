# Changelog

## [1.2.0] - 2026-11-20

### Added
- **AI Assistants & Chatbots section** (`ai_assistants`) — ranks consumer AI products (ChatGPT, Claude.ai, Gemini, Copilot, Grok, Perplexity, Meta AI, etc.) by monthly active users; includes MAU estimates, platforms, and dual-model cross-check
- **`--sections` pipeline flag** — `python pipeline.py --sections=ai_news --force` scopes research + generate to named sections; validate stage skipped for speed; enables targeted partial refreshes

### Changed
- **Refresh schedule** — switched from weekly full refresh to monthly full (1st of month, 00:00 UTC) + daily news-only (05:00 UTC, `--sections=ai_news`); reduces LLM calls ~56% vs prior weekly schedule
- Section count: 17 → 18

---

## [1.1.0] - 2026-11-03

Current production state of all features below.

### Content
- 18 sections: Code Tools, Models, AI Assistants, Image Gen, Video Gen, MCP Tools, Web Scrapers, Workspace, Fine-Tuning, Enterprise APIs, ML Platforms, Emerging Trends, Token Prices (ranked) + Repositories, Databases, Observability, LLM Optimization, AI News (reference/news)
- Smart 10–15 ranking cutoff — extends past 10 only when adoption clusters tightly, stops at natural drop-off
- Rankings grounded by live web research before every generation run

### Generation
- Claude Opus 4.8 primary; GPT-4o cross-check on all ranked sections
- Agreement badges per tool: ✅ Consensus / 🟡 Minor diff / 🔴 Disagree / ⚪ GPT-4o excluded
- GPT-4o promoted to primary if Opus returns empty; Sonnet 4.6 fallback for `ai_news`
- All sections generated in parallel with `ThreadPoolExecutor`

### Pipeline
- 4-stage orchestrator (`pipeline.py`): research → generate → validate → build
- Checkpoint files — completed stages skipped on re-run; `--force` / `--from=<stage>` / `--only=<stage>` / `--sections=<keys>` flags
- `config.json` — site identity (title, author, tagline, about URL) loaded by build scripts; template uses `{{ config.* }}`

### Research
- Provider priority: Firecrawl → Tavily → Serper
- `ai_news` uses Tavily news mode with `include_domains` restricted to ~25 trusted publications; 6 queries including direct vendor blog pulls on 30-day window
- Research queries date-anchored to today's date for same-day/yesterday news coverage

### News
- Up to 20 items per day; each tagged `category: "vendor"` or `"industry"`
- Dashboard strip: two-column layout (🌐 Industry | 🏢 Vendor), visible on Overview tab only
- Full summaries on `news.html` only; sorted newest-first
- 14-day recency filter (falls back to 30-day if fewer than 5 pass)

### Validation
- `validate_links.py` fetches every URL, judges relevance via Claude Haiku
- HTTP 403s treated as valid (major platforms block scrapers)
- `url_overrides.json` — permanent fix and skip registry for known problem URLs
- Auto-fixer scope: only searches for replacements on truly broken links (404/unreachable)
- Auto-fixer whitelist: replacement candidates must come from domains listed in `include.json`

### Infrastructure
- GitHub Pages (free) + GitHub Actions cron (monthly full + daily news)
- `build_standalone.py` generates offline single-file versions (`standalone.html`, `about-standalone.html`)
- Header: "Curated by Vlad Meyman · Ranked by Claude AI · How rankings work →" linking to `about.html`
