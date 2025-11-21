#!/bin/bash
# Bash script to configure Cursor with MCP servers

set -e

echo "🔧 Configuring Cursor MCP Servers..."

# Determine OS and set config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CURSOR_CONFIG_DIR="$HOME/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURSOR_CONFIG_DIR="$HOME/.config/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

CURSOR_CONFIG_FILE="$CURSOR_CONFIG_DIR/cline_mcp_settings.json"

# Create directory if it doesn't exist
mkdir -p "$CURSOR_CONFIG_DIR"

# Check if config file exists
if [ -f "$CURSOR_CONFIG_FILE" ]; then
    echo "⚠️  Existing Cursor MCP config found at:"
    echo "   $CURSOR_CONFIG_FILE"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing config. Exiting."
        exit 0
    fi
    
    # Backup existing config
    BACKUP_FILE="${CURSOR_CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
    cp "$CURSOR_CONFIG_FILE" "$BACKUP_FILE"
    echo "✅ Backed up existing config to: $BACKUP_FILE"
fi

# Read template config
TEMPLATE_PATH="$(dirname "$0")/cursor-mcp-config.json"
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo "❌ Template config not found at: $TEMPLATE_PATH"
    exit 1
fi

# Copy template
cp "$TEMPLATE_PATH" "$CURSOR_CONFIG_FILE"

# Prompt for tokens
echo ""
echo "Enter your API keys/tokens:"
echo "(Press Enter to skip and configure manually later)"
echo ""

# Discord Token
read -p "Discord Bot Token: " DISCORD_TOKEN
if [ -n "$DISCORD_TOKEN" ]; then
    # Update Discord token in config (requires jq or manual edit)
    if command -v jq &> /dev/null; then
        PROJECT_PATH=$(pwd)
        jq ".mcpServers.\"mcp-discord\".env.DISCORD_TOKEN = \"$DISCORD_TOKEN\"" \
           "$CURSOR_CONFIG_FILE" > "${CURSOR_CONFIG_FILE}.tmp" && \
        mv "${CURSOR_CONFIG_FILE}.tmp" "$CURSOR_CONFIG_FILE"
        jq ".mcpServers.\"mcp-discord\".args[1] = \"$PROJECT_PATH\"" \
           "$CURSOR_CONFIG_FILE" > "${CURSOR_CONFIG_FILE}.tmp" && \
        mv "${CURSOR_CONFIG_FILE}.tmp" "$CURSOR_CONFIG_FILE"
    else
        echo "⚠️  jq not found. Please edit $CURSOR_CONFIG_FILE manually to set DISCORD_TOKEN"
    fi
fi

# Linear API Key
read -p "Linear API Key: " LINEAR_KEY
if [ -n "$LINEAR_KEY" ] && command -v jq &> /dev/null; then
    jq ".mcpServers.linear.env.LINEAR_API_KEY = \"$LINEAR_KEY\"" \
       "$CURSOR_CONFIG_FILE" > "${CURSOR_CONFIG_FILE}.tmp" && \
    mv "${CURSOR_CONFIG_FILE}.tmp" "$CURSOR_CONFIG_FILE"
fi

# Context7 API Key
read -p "Context7 API Key: " CONTEXT7_KEY
if [ -n "$CONTEXT7_KEY" ] && command -v jq &> /dev/null; then
    jq ".mcpServers.context7.env.CONTEXT7_API_KEY = \"$CONTEXT7_KEY\"" \
       "$CURSOR_CONFIG_FILE" > "${CURSOR_CONFIG_FILE}.tmp" && \
    mv "${CURSOR_CONFIG_FILE}.tmp" "$CURSOR_CONFIG_FILE"
fi

echo ""
echo "✅ Cursor MCP config created at:"
echo "   $CURSOR_CONFIG_FILE"
echo ""
echo "Next steps:"
echo "1. Restart Cursor to load the new MCP servers"
echo "2. Verify MCP servers are connected in Cursor settings"
echo "3. If you skipped any keys, edit the config file manually"

