# Quick Start Guide: Notion Integration

This guide will help you quickly set up and test the Notion MCP integration.

## Step 1: Install Node.js (if not already installed)

Download and install Node.js 18 or higher from: https://nodejs.org/

Verify installation:
```powershell
node --version
npm --version
```

## Step 2: Create Notion Integration

1. Visit: https://www.notion.so/my-integrations
2. Click **"+ New integration"**
3. Fill in:
   - Name: `My Agency Integration` (or any name)
   - Associated workspace: Select your workspace
   - Capabilities: Keep defaults (Read content, Update content, Insert content)
4. Click **"Submit"**
5. **Copy the "Internal Integration Token"** (starts with `secret_`)

## Step 3: Connect Pages to Integration

For each page/database you want the agent to access:

1. Open the page in Notion
2. Click the **"..."** (three dots) menu in the top right
3. Hover over **"Connections"** or **"Add connections"**
4. Find and click your integration name
5. Click **"Confirm"**

💡 **Tip**: Start by connecting your main workspace page to give broad access.

## Step 4: Set Environment Variable

Open PowerShell and set the token:

```powershell
$env:NOTION_TOKEN = "secret_YOUR_TOKEN_HERE"
```

Or for permanent setup, add to a `.env` file in the project root:

```
NOTION_TOKEN=secret_YOUR_TOKEN_HERE
```

## Step 5: Test the Integration

### Option A: Run Example Script

```powershell
cd d:\GitHub\mcp-discord
python -m src.notion_mcp.example
```

This will:
- Connect to Notion MCP Server
- List available tools
- Search for pages
- Display results

### Option B: Test Individual Tools

```powershell
cd d:\GitHub\mcp-discord\src\agency\notion_agent\tools

# Search for pages
python SearchNotionTool.py

# Get page details (replace with your page ID)
python GetNotionPageTool.py "abc123..."

# Create a test page
python CreateNotionPageTool.py
```

### Option C: Use in Agency

```python
from agency_swarm import Agency
from agency.notion_agent import notion_agent

# Create a simple agency with just the Notion agent
agency = Agency([notion_agent])

# Run interactive demo
agency.run_demo()
```

Then try commands like:
- "Search for pages about projects"
- "Create a new page called Test Page"
- "Show me details about page abc123"

## Common Issues & Solutions

### ❌ "NOTION_TOKEN environment variable not set"
**Solution**: Run `$env:NOTION_TOKEN = "secret_..."` in PowerShell before running scripts

### ❌ "Page not found" or "Object not found"
**Solution**: The integration doesn't have access. Go to the page → "..." → "Connections" → Add your integration

### ❌ "Node.js not found" or "npx not found"
**Solution**: Install Node.js from https://nodejs.org/ and restart your terminal

### ❌ "Could not connect to MCP server"
**Solution**: 
1. Check internet connection (first run downloads the MCP server)
2. Ensure Node.js 18+ is installed: `node --version`
3. Try running manually: `npx -y @notionhq/notion-mcp-server`

### ❌ "Validation error" when updating pages
**Solution**: Property names/types must match the database schema. Use `GetNotionPageTool` to see current properties.

## Next Steps

Once everything is working:

1. **Explore the tools**: Try each tool individually to understand capabilities
2. **Create workflows**: Combine tools in agent instructions for complex tasks
3. **Build an agency**: Connect Notion agent with other agents (e.g., Crawl4AI agent)
4. **Automate tasks**: Use the agent for recurring Notion management tasks

## Example: Article Collection Workflow

Combine Crawl4AI and Notion agents to collect articles and save to Notion:

```python
from agency_swarm import Agency
from agency.crawl4ai_agent import crawl4ai_agent
from agency.notion_agent import notion_agent

# Create agency with both agents
agency = Agency([
    [crawl4ai_agent, notion_agent],  # They can work together
])

# User: "Crawl https://example.com/article and save it to my Reading List in Notion"
# 
# Flow:
# 1. Crawl4AI agent extracts article content
# 2. Notion agent searches for "Reading List" database
# 3. Notion agent creates new page with article content
```

## Support

- Check `README.md` in `notion_agent/` for detailed documentation
- Check `notion_mcp/README.md` for MCP client details
- Review `instructions.md` for agent behavior guidelines

---

**Ready to go!** 🚀 Try running the example script or testing individual tools.
