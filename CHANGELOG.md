# Changelog

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
