#!/bin/bash
set -e

echo "🚀 Setting up changelog-monitor development environment..."

# Install Python 3.13
echo "📦 Installing Python 3.13..."
uv python install 3.13

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Configure Git safe directory
echo "🔧 Configuring Git safe directory..."
git config --global --add safe.directory /workspaces/changelog-monitor

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys (GEMINI_API_KEY, LINE_NOTIFY_TOKEN)"
echo "2. Edit config/repositories.yml and add repositories to monitor"
echo "3. Run: uv run python scripts/monitor.py"
echo ""
