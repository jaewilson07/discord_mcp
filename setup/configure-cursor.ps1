# PowerShell script to configure Cursor with MCP servers

$ErrorActionPreference = "Stop"

Write-Host "🔧 Configuring Cursor MCP Servers..." -ForegroundColor Cyan

# Cursor MCP config location
$cursorConfigDir = "$env:APPDATA\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings"
$cursorConfigFile = Join-Path $cursorConfigDir "cline_mcp_settings.json"

# Create directory if it doesn't exist
if (-not (Test-Path $cursorConfigDir)) {
    Write-Host "Creating Cursor config directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $cursorConfigDir -Force | Out-Null
}

# Check if config file exists
$configExists = Test-Path $cursorConfigFile

if ($configExists) {
    Write-Host "⚠️  Existing Cursor MCP config found at:" -ForegroundColor Yellow
    Write-Host "   $cursorConfigFile" -ForegroundColor Gray
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Keeping existing config. Exiting." -ForegroundColor Yellow
        exit 0
    }
    
    # Backup existing config
    $backupFile = "$cursorConfigFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $cursorConfigFile $backupFile
    Write-Host "✅ Backed up existing config to: $backupFile" -ForegroundColor Green
}

# Read template config
$templatePath = Join-Path $PSScriptRoot "cursor-mcp-config.json"
if (-not (Test-Path $templatePath)) {
    Write-Host "❌ Template config not found at: $templatePath" -ForegroundColor Red
    exit 1
}

$config = Get-Content $templatePath | ConvertFrom-Json

# Prompt for tokens
Write-Host ""
Write-Host "Enter your API keys/tokens:" -ForegroundColor Cyan
Write-Host "(Press Enter to skip and configure manually later)" -ForegroundColor Gray
Write-Host ""

# Discord Token
$discordToken = Read-Host "Discord Bot Token"
if ($discordToken) {
    $config.mcpServers."mcp-discord".env.DISCORD_TOKEN = $discordToken
    # Update path to current directory
    $projectPath = (Get-Location).Path
    $config.mcpServers."mcp-discord".args[1] = $projectPath
}

# Linear API Key
$linearKey = Read-Host "Linear API Key"
if ($linearKey) {
    $config.mcpServers.linear.env.LINEAR_API_KEY = $linearKey
}

# Context7 API Key
$context7Key = Read-Host "Context7 API Key"
if ($context7Key) {
    $config.mcpServers.context7.env.CONTEXT7_API_KEY = $context7Key
}

# Write config
$configJson = $config | ConvertTo-Json -Depth 10
$configJson | Out-File -FilePath $cursorConfigFile -Encoding utf8

Write-Host ""
Write-Host "✅ Cursor MCP config created at:" -ForegroundColor Green
Write-Host "   $cursorConfigFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart Cursor to load the new MCP servers"
Write-Host "2. Verify MCP servers are connected in Cursor settings"
Write-Host "3. If you skipped any keys, edit the config file manually"

