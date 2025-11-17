# Installation Guide

This project contains multiple components that can be installed separately or together.

## Components

1. **Discord MCP Server** - Discord bot integration with MCP
2. **Agency Framework** - Multi-agent orchestration system
3. **YouTube Research Agency** - AI-powered YouTube video research

## Installation Options

### Option 1: Install Everything

```bash
# Clone the repository
git clone https://github.com/jaewilson07/discord_mcp.git
cd discord_mcp

# Install with all optional dependencies
pip install -e ".[all]"
```

### Option 2: Install Only Discord MCP

```bash
pip install -e .
```

### Option 3: Install Discord MCP + Agency Framework

```bash
pip install -e ".[agency]"
```

### Option 4: Install Discord MCP + YouTube Research

```bash
pip install -e ".[youtube]"
```

Or install both agency and youtube features:

```bash
pip install -e ".[agency,youtube]"
```

## Setup

### 1. Configure Environment Variables

Copy the template:
```bash
cp .env.template .env
```

Edit `.env` and add your API keys:

```env
# Discord MCP Server
DISCORD_TOKEN=your_discord_bot_token_here

# YouTube Research Agency
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Get API Keys

#### Discord Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Create a bot and copy the token
4. Enable required privileged intents

#### YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys
4. Create a new secret key

## Usage

### Run Discord MCP Server

```bash
mcp-discord
```

Or with Python:
```bash
python -m discord_mcp.server
```

### Run YouTube Research Agency

Terminal mode (interactive):
```bash
youtube-research
```

Or with Python:
```bash
python -m agency.youtube_agency
```

### Run Example Agency

```bash
agency-demo
```

Or with Python:
```bash
python -m agency.agency
```

### Run FastAPI Server (All Agencies)

```bash
python -m agency.main
```

This starts a FastAPI server on port 8080 with both agencies available.

## Development Installation

For development with editable install:

```bash
# Install in editable mode with all dependencies
pip install -e ".[all]"

# Or use uv (faster)
uv pip install -e ".[all]"
```

## Verify Installation

Check that packages are installed:

```bash
pip list | grep -E "discord|agency|langchain|youtube"
```

Test imports:

```bash
python -c "from src.discord_mcp import server; print('Discord MCP: OK')"
python -c "from src.mcp_ce import runtime; print('MCP CE: OK')"
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Reinstall in editable mode
pip install -e .
```

### Missing Dependencies

If specific features don't work:
```bash
# Install all dependencies
pip install -r requirements.txt
```

### API Key Errors

- Verify `.env` file is in the project root directory
- Check that API keys don't have extra spaces or quotes
- Ensure environment variables are loaded before running

## Project Structure

```
mcp-discord/
├── src/
│   ├── discord_mcp/      # Discord MCP server
│   └── agency/           # Multi-agent framework
│       ├── agency.py     # Example agency
│       ├── youtube_agency.py  # YouTube research agency
│       ├── main.py       # FastAPI deployment
│       ├── youtube_agent/
│       ├── summarizer_agent/
│       └── research_coordinator/
├── pyproject.toml        # Package configuration
├── requirements.txt      # Pinned dependencies
└── .env.template         # Environment template
```

## Commands Reference

After installation, these commands become available:

- `mcp-discord` - Run Discord MCP server
- `youtube-research` - Run YouTube research agency (terminal)
- `agency-demo` - Run example agency (terminal)

## Documentation

- [Discord MCP README](README.md)
- [Agency Integration Guide](AGENCY_INTEGRATION.md)
- [YouTube Research Guide](src/agency/YOUTUBE_RESEARCH_README.md)
- [YouTube Agency PRD](src/agency/youtube_research_prd.md)
- [Implementation Notes](YOUTUBE_AGENCY_IMPLEMENTATION.md)

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/jaewilson07/discord_mcp/issues)
- Check existing documentation
- Review the examples in the repository
