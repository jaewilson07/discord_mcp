# YouTube Analysis MCP Agent

An AI-powered MCP agent that performs comprehensive YouTube video analysis. Built with [mcp-agent](https://github.com/lastmile-ai/mcp-agent) and exposed as an MCP tool.

## Features

🎥 **Video Metadata Extraction** - Gets title, channel, views, likes, and description  
📝 **Transcript Extraction** - Pulls full video captions/transcripts  
🤖 **AI-Powered Analysis** - GPT-4 analyzes content and extracts insights  
🔍 **Key Findings** - Identifies 3-20 important points with detailed explanations  
📊 **Comprehensive Reports** - Generates markdown reports with video links  
⚡ **MCP-Agent Workflows** - Orchestrates multi-step analysis workflows  

## Architecture

This agent uses the **mcp-agent** library which implements Model Context Protocol (MCP) with effective agent patterns. The workflow:

1. **Agent Creation** - Creates a specialized YouTube analyzer agent
2. **Tool Attachment** - Attaches custom functions for video operations
3. **LLM Integration** - Uses OpenAI GPT-4 for intelligent analysis
4. **Workflow Orchestration** - Coordinates multi-step analysis pipeline
5. **MCP Exposure** - Exposes as standard MCP tool for any client

### vs Agency Swarm

| Feature | MCP-Agent (This) | Agency Swarm |
|---------|------------------|--------------|
| Protocol | MCP-native | Custom |
| Pattern | Composable workflows | Multi-agent orchestration |
| Execution | Durable (Temporal optional) | Synchronous |
| Integration | Any MCP client | FastAPI |
| Complexity | Simple, focused | Full agency system |

**When to use MCP-Agent:**
- Single-purpose tool exposed via MCP
- Integration with Claude Desktop, Cursor
- Composable with other MCP servers
- Need durable execution

**When to use Agency Swarm:**
- Complex multi-agent workflows
- Need agent-to-agent communication
- Building complete agency systems
- Custom tool orchestration

## Installation

```bash
# Install with MCP-Agent support
pip install -e ".[mcp-agent,youtube]"

# Or install all features
pip install -e ".[all]"
```

## Configuration

Add to `.env`:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Get API Keys

**YouTube API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable "YouTube Data API v3"
3. Create credentials → API Key

**OpenAI API:**
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Navigate to API Keys
3. Create new secret key

## Usage

### As MCP Server (Recommended)

Run the enhanced MCP server that includes the YouTube analysis agent:

```bash
# Start the MCP server
python -m mcp_ce.server_enhanced

# Or use the CLI command (after install)
mcp-server-enhanced
```

### Connect from Claude Desktop

Add to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "youtube-analysis": {
      "command": "python",
      "args": ["-m", "mcp_ce.server_enhanced"]
    }
  }
}
```

Then in Claude Desktop:
```
Analyze this YouTube video in detail:
https://www.youtube.com/watch?v=SJi469BuU6g
```

### Programmatic Usage

```python
from mcp_ce.youtube_analysis_agent import analyze_youtube_video

async def main():
    report = await analyze_youtube_video(
        video_url="https://www.youtube.com/watch?v=SJi469BuU6g",
        max_key_points=15,
        analysis_depth="detailed"
    )
    print(report)

import asyncio
asyncio.run(main())
```

### MCP Tool Parameters

```python
analyze_youtube_video(
    video_url: str,           # YouTube URL
    max_key_points: int = 15, # 3-20 key findings
    analysis_depth: str = "detailed"  # "summary" or "detailed"
)
```

## Output Format

The agent returns a comprehensive markdown report:

```markdown
# Video Analysis Report

**Video URL**: https://www.youtube.com/watch?v=...
**Video ID**: VIDEO_ID

## Video Information
- Title, channel, views, etc.

## Executive Summary
2-3 sentence overview

## Key Findings (Detailed Analysis)
1. Finding one with detailed explanation...
2. Finding two with supporting evidence...
...

## Transcript Analysis
Transcript statistics and quality assessment

## Detailed Insights
3-5 paragraphs connecting findings

## Conclusions
Main takeaways and applications

## Source
**Video Link**: [URL](URL)
```

## Architecture Deep Dive

### MCP-Agent Workflow

```python
app = MCPApp(name="youtube_video_analyzer")

@app.tool
async def analyze_youtube_video(...) -> str:
    async with app.run() as running_app:
        # 1. Create specialized agent
        analyzer_agent = Agent(
            name="youtube_analyzer",
            instruction="...",
            server_names=[]
        )
        
        # 2. Add custom tools
        analyzer_agent.add_function_tool(_get_video_metadata)
        analyzer_agent.add_function_tool(_get_video_transcript)
        analyzer_agent.add_function_tool(_extract_key_findings)
        
        # 3. Attach LLM
        async with analyzer_agent:
            llm = await analyzer_agent.attach_llm(OpenAIAugmentedLLM)
            
            # 4. Execute multi-step workflow
            metadata = await llm.generate_str("Get metadata...")
            transcript = await llm.generate_str("Get transcript...")
            analysis = await llm.generate_str("Analyze...")
            report = await llm.generate_str("Generate report...")
            
            return report
```

### Key Components

1. **MCPApp** - Application runtime, manages context and logging
2. **Agent** - Specialized analyzer with instructions and tools
3. **OpenAIAugmentedLLM** - Wraps OpenAI API with agent tools
4. **Custom Functions** - YouTube API and transcript extraction
5. **Workflow** - Multi-step orchestrated analysis

## MCP Server Tools

The enhanced server exposes 2 tools:

### 1. `run_python`
Execute Python code with zero-context MCP discovery (from original server)

### 2. `analyze_youtube_video`
AI-powered video analysis (NEW - this agent)

Both tools are exposed via standard MCP protocol.

## Examples

### Quick Summary
```python
result = await analyze_youtube_video(
    video_url="https://www.youtube.com/watch?v=SJi469BuU6g",
    max_key_points=5,
    analysis_depth="summary"
)
```

### Detailed Analysis  
```python
result = await analyze_youtube_video(
    video_url="https://www.youtube.com/watch?v=SJi469BuU6g",
    max_key_points=15,
    analysis_depth="detailed"
)
```

### From Claude Desktop
Simply ask:
```
Please analyze this YouTube video in great detail:
https://www.youtube.com/watch?v=SJi469BuU6g

Extract all key findings and provide comprehensive insights.
```

## Comparison: MCP-Agent vs Agency Swarm

This project now has **both** implementations:

### MCP-Agent Implementation (`src/mcp_ce/youtube_analysis_agent.py`)
✅ Single-purpose tool  
✅ MCP-native protocol  
✅ Works with any MCP client  
✅ Simple, focused workflow  
✅ Optional durable execution  
✅ ~100 lines of code  

### Agency Swarm Implementation (`src/agency/`)
✅ Multi-agent system  
✅ 3 specialized agents  
✅ Complex workflows  
✅ Agent coordination  
✅ FastAPI deployment  
✅ Full research pipeline  

**Choose MCP-Agent when:**
- Building MCP tools
- Single-purpose agents
- Integration with MCP clients
- Want simplicity

**Choose Agency Swarm when:**
- Need multiple coordinating agents
- Complex research workflows
- Custom agent communication
- Building complete agencies

## Troubleshooting

### "YOUTUBE_API_KEY not found"
Add to `.env` file or set environment variable

### "No transcript available"
Video doesn't have captions. Try a different video.

### "OpenAI API error"
Check API key is valid and has credits

### Import errors
```bash
pip install -e ".[mcp-agent,youtube]"
```

## Documentation

- [MCP-Agent Docs](https://docs.mcp-agent.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Agency Swarm](../agency/YOUTUBE_RESEARCH_README.md)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

## License

MIT License - see main project LICENSE file
