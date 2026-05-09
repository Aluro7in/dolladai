#!/bin/bash
# DolladAI — Start Script
# Installs dependencies and starts the web server on port 3000

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 Starting DolladAI..."

# Install pip if missing
if ! python3 -m pip --version &>/dev/null 2>&1; then
  echo "📦 Installing pip..."
  curl -sS https://bootstrap.pypa.io/pip/3.9/get-pip.py | python3 - --quiet
fi

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install flask flask-cors requests psutil markdown2 -q

echo "🚀 Launching DolladAI on port 3000..."
exec python3 server.py
