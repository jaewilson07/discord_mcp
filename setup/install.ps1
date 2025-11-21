# Installation script for MCP Discord Server (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Installing MCP Discord Server..." -ForegroundColor Cyan

# Check for uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
    exit 1
}

# Check Python version
try {
    $pythonVersion = python --version 2>&1 | ForEach-Object { $_ -replace "Python ", "" }
    $major, $minor = $pythonVersion -split '\.'
    $versionNum = [int]$major * 10 + [int]$minor
    
    if ($versionNum -lt 310) {
        Write-Host "❌ Python 3.10+ is required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
uv sync

# Check for .env file
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found. Creating template..." -ForegroundColor Yellow
    @"
# Discord Bot Token
DISCORD_TOKEN=your_bot_token_here

# Optional: OpenAI API Key for AI features
# OPENAI_API_KEY=your_openai_key_here

# Optional: Notion API Key
# NOTION_API_KEY=your_notion_key_here
"@ | Out-File -FilePath .env -Encoding utf8
    Write-Host "✅ Created .env file. Please edit it and add your Discord token." -ForegroundColor Green
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}

# Verify installation
Write-Host "🔍 Verifying installation..." -ForegroundColor Cyan
uv run mcp-discord --info

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env and add your DISCORD_TOKEN"
Write-Host "2. Run: uv run mcp-discord"
Write-Host "3. Configure your MCP client (see setup/README.md)"

