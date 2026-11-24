#!/bin/sh
# Tool-X GUI launcher
# Installs Flask if missing (no sudo needed), then starts the dashboard.

cd "$(dirname "$0")"

if ! python3 -c "import flask" 2>/dev/null; then
  echo "Installing Flask (one-time, user-level, no sudo)..."
  pip3 install --user flask
fi

echo ""
echo "Starting Tool-X GUI..."
echo "Open this in your browser: http://127.0.0.1:5000"
echo ""

python3 app.py
