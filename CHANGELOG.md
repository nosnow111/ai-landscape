# Changelog

## [Unreleased]

## [0.3.0] - 2026-10-24
### Changed
- Switched to static site architecture (GitHub Pages + GitHub Actions)
- Removed Flask, Gunicorn, APScheduler server dependencies
- Added `build.py` to render static HTML from generated JSON
- Added GitHub Actions workflow for daily content refresh
- Added placeholder `docs/index.html` shown while content generates

### Removed
- `app.py` (Flask server)
- `Procfile`, `start.sh`, `Dockerfile` (server deployment files)
- `railway.json`, `render.yaml`, `fly.toml` (unused hosting configs)

## [0.2.0] - 2026-10-24
### Added
- `render.yaml` for Render deployment (later removed)
- `fly.toml` and `Dockerfile` for Fly.io deployment (later removed)

### Notes
- Render removed free tier
- Koyeb acquired by Mistral AI and shut down
- Fly.io requires credit card (free trial only)
- Railway not accepting new signups

## [0.1.0] - 2026-10-24
### Added
- Initial project scaffold
- `generator.py` — calls Claude API to generate 5 content sections as JSON
- `app.py` — Flask web server with APScheduler for periodic refresh
- `templates/index.html` — Tailwind CSS dashboard
- `requirements.txt`, `.env.example`
- `Procfile` for Railway/Render deployment
