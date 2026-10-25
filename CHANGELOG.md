# Changelog

## [0.10.0] - 2026-10-25
### Added
- LLM Cost & Performance Optimization section — techniques table (savings %, difficulty, providers), quick wins box, and optimization tools (GPTCache, LiteLLM, Helicone, etc.)

## [0.9.0] - 2026-10-25
### Added
- Fine-Tuning Platforms section — top 10 by adoption with "when to fine-tune vs RAG vs prompting" callout, table with supported models and local GPU requirement, and detail cards

### Changed
- Tab labels shortened and font/padding reduced further to fit all 12 tabs without scrolling

## [0.8.0] - 2026-10-25
### Added
- Dark themed header with circuit-dot pattern, 🤖🌍⚡ emoji, centered layout, and compact two-line design
- Attribution "Curated by Vlad Meyman · Ranked by Claude AI" in header and footer
- Collapsible "How Rankings Are Calculated" methodology box on Overview tab — signal table, enterprise/aggregator note, 10–15 cutoff explanation
- Enterprise/aggregator reach (AWS Bedrock, Azure OpenAI, Snowflake Cortex, Vertex AI) added as ranking signal to models prompt

### Changed
- Research (`research.py`) and generation (`generator.py`) parallelized with `ThreadPoolExecutor` — all 9 sections run concurrently (~5× faster)
- GitHub Actions workflow fixed: stash generated files → pull latest → rebuild with latest template → commit → push (eliminates push conflicts when template changes mid-run)
- `requirements.txt` loosened to minimum versions (`>=`) to avoid downgrading other tools on the machine
- Tab bar tightened: smaller font, less padding, tighter gap so all tabs fit without scrolling

## [0.7.0] - 2026-10-24
### Changed
- Smart 10–15 ranking cutoff: all ranked sections now extend beyond 10 only when adoption clusters tightly (within ~25%), cutting at natural drop-off
- Expanded Tavily research: 3–5 queries per section including "complete list / alternatives / lesser known" discovery queries
- Claude instructed to surface tools found in research even if not named in the prompt
- Wave (wave.com, AI meeting recorder) added to workspace section

## [0.6.0] - 2026-10-24
### Added
- AI Productivity & Workspace Tools section (NotebookLM, M365 Copilot, Notion AI, Perplexity, etc.)
- Workspace tab, overview column, and detail panel
- OpenAI Codex (agentic) and Devin/Devin Desktop added explicitly to code tools prompt
- Tavily research queries for workspace section

## [0.5.0] - 2026-10-24
### Added
- Image Generation section (top 10 by usage with Tavily research)
- Video Generation section (top 10 by usage with Tavily research)
- AI Web Scrapers & Browser Automation section (top 10 by usage)
- New tab buttons, detail panels, and overview columns for each new section

## [0.4.0] - 2026-10-24
### Added
- Tavily web search step in `research.py` — fetches live data before each Claude call
- Source citations displayed at the bottom of each detail tab
- Usage rankings (rank + popularity_notes) for models and code tools
- Gemini and DeepSeek added to models section
- Overview redesigned as colored column layout (one column per section)
- Fixed tab button and tag styling (replaced @apply with real CSS for CDN compatibility)

## [0.3.0] - 2026-10-24
### Changed
- Switched to static site architecture (GitHub Pages + GitHub Actions)
- Removed Flask server dependencies
- Added `build.py` to render static HTML from generated JSON
- Added GitHub Actions workflow for daily content refresh at midnight UTC

## [0.1.0] - 2026-10-24
### Added
- Initial project scaffold
- `generator.py` — calls Claude API to generate content sections as JSON
- `templates/index.html` — Tailwind CSS dashboard with tab navigation
- `build.py` — Jinja2 static site builder
- `requirements.txt`, `.env.example`
- GitHub Pages hosting from `docs/` folder
