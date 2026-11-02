# Changelog

## [1.0.0] - 2026-11-02

Current production state. Everything below reflects what is live today.

### Content
- 16 sections: Code Tools, Models, Image Gen, Video Gen, MCP Tools, Web Scrapers, Workspace, Fine-Tuning, Enterprise APIs, ML Platforms, Emerging Trends (ranked) + Repositories, Databases, Observability, LLM Optimization, AI News (reference/news)
- Smart 10–15 ranking cutoff — extends past 10 only when adoption clusters tightly, stops at natural drop-off
- Rankings grounded by live web research before every generation run

### Generation
- Claude Opus 4.8 primary; GPT-4o cross-check on all ranked sections
- Agreement badges per tool: ✅ Consensus / 🟡 Minor diff / 🔴 Disagree / ⚪ GPT-4o excluded
- GPT-4o promoted to primary if Opus returns empty; Sonnet 4.6 fallback for `ai_news`
- All 16 sections generated in parallel with `ThreadPoolExecutor`

### Pipeline
- 4-stage orchestrator (`pipeline.py`): research → generate → validate → build
- Checkpoint files — completed stages skipped on re-run; `--force` / `--from=<stage>` / `--only=<stage>` flags
- `--only=<stage>` always force-runs the named stage regardless of checkpoint

### Research
- Provider priority: Firecrawl → Tavily → Serper
- `ai_news` uses Tavily news mode (`topic="news"`, `days=14`) with `include_domains` restricted to ~25 trusted publications (Reuters, AP News, WSJ, Bloomberg, CNBC, MarketWatch, TechCrunch, The Verge, Wired, etc.) — prevents junk domains from surfacing
- Research queries date-anchored to today's date for same-day/yesterday news coverage

### News
- Up to 20 items per day; each tagged `category: "vendor"` or `"industry"`
- Dashboard strip: two-column table (🌐 Industry | 🏢 Vendor), visible on Overview tab only
- Full summaries on `news.html` only
- Sources sorted newest-first; 14-day recency filter (falls back to 30-day if fewer than 5 pass)
- Tier 1 sources include paywalled outlets (WSJ, FT, Bloomberg, NYT) — links provided even if behind paywall

### Validation
- `validate_links.py` fetches every URL, judges relevance via Claude Haiku, auto-fixes wrong-page links
- HTTP 403s treated as valid (major platforms block scrapers)
- `url_overrides.json`: permanent fix and skip registry for known problem URLs
- Auto-fixer domain blocklist — rejects replacements from non-authoritative domains (mcpservers.org, gate.ai, g2.com, medium.com, reddit.com, etc.)
- `_URL_RULE` in prompts blocks comparison article domains (g2.com, capterra.com, technologymatch.com, etc.)

### Infrastructure
- GitHub Pages (free) + GitHub Actions daily cron at midnight UTC
- `build.py` sorts news descending by date before rendering
- `build_standalone.py` generates offline single-file versions (`standalone.html`, `about-standalone.html`)
- Header attribution: "Curated by Vlad Meyman · Ranked by Claude AI"
