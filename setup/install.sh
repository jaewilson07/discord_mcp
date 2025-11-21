#!/bin/bash
# Installation script for MCP Discord Server

set -e

echo "🚀 Installing MCP Discord Server..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# Discord Bot Token
DISCORD_TOKEN=your_bot_token_here

# Optional: OpenAI API Key for AI features
# OPENAI_API_KEY=your_openai_key_here

# Optional: Notion API Key
# NOTION_API_KEY=your_notion_key_here
EOF
    echo "✅ Created .env file. Please edit it and add your Discord token."
else
    echo "✅ .env file exists"
fi

# Verify installation
echo "🔍 Verifying installation..."
uv run mcp-discord --info

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your DISCORD_TOKEN"
echo "2. Run: uv run mcp-discord"
echo "3. Configure your MCP client (see setup/README.md)"

