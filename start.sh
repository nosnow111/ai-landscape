#!/bin/bash
# Generate content on first boot if content dir is empty, then start the web server
if [ -z "$(ls -A content 2>/dev/null)" ]; then
  echo "No content found — running initial generation..."
  python generator.py
fi
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
