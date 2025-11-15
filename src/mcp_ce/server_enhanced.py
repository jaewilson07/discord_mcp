"""
Enhanced MCP Server with YouTube Video Analysis Agent

Combines code execution sandbox with YouTube video analysis capabilities.
"""

from fastmcp import FastMCP
from typing import Optional
import json

# Create FastMCP server instance
mcp = FastMCP("MCP Enhanced Server - Code Execution + YouTube Analysis")

# Import runtime and sandbox for code execution
from .runtime import SANDBOX_HELPERS_SUMMARY
from .sandbox import execute_python

# Import YouTube analysis agent
from .youtube_analysis_agent import analyze_youtube_video as youtube_agent_analyze


@mcp.tool()
async def run_python(code: str, timeout: Optional[int] = 30) -> str:
    """
    Execute Python code in a sandboxed environment with MCP runtime helpers.

    The sandbox provides discovery helpers for zero-context MCP access:

    **Discovery Helpers:**
    - `discovered_servers()` - List available MCP servers (no schemas loaded)
    - `list_servers()` - Get server names only
    - `query_tool_docs(server, tool=None, detail="summary")` - Load tool schemas on-demand
    - `search_tool_docs(query, limit=None)` - Fuzzy search for tools
    - `create_tool_proxy(server, tool)` - Create callable for tool execution

    **Workflow:**
    1. Discover servers: `servers = discovered_servers()`
    2. Query tools: `docs = query_tool_docs("url_ping")`
    3. Create proxy: `ping = create_tool_proxy("url_ping", "ping_url")`
    4. Execute: `result = await ping(url="https://example.com")`

    **Example:**
    ```python
    # Discover available servers
    import json
    servers = discovered_servers()
    print(f"Available servers: {json.dumps(servers, indent=2)}")

    # Query tool docs for url_ping server
    docs = query_tool_docs("url_ping", detail="full")
    print(f"Tool docs: {docs}")

    # Create tool proxy and call it
    async def main():
        ping = create_tool_proxy("url_ping", "ping_url")
        result = await ping(url="https://www.google.com", timeout=10)
        return result

    # main() will be automatically awaited if defined
    ```

    Args:
        code: Python code to execute (can define async main() function)
        timeout: Execution timeout in seconds (default: 30)

    Returns:
        JSON string with execution results:
        - success: bool
        - stdout: captured output
        - stderr: captured errors
        - result: return value from main() if defined
        - error: error message if failed
    """
    result = await execute_python(code, timeout)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def analyze_youtube_video(
    video_url: str,
    max_key_points: int = 15,
    analysis_depth: str = "detailed"
) -> str:
    """
    Analyze a YouTube video in great detail using an AI agent.
    
    This tool uses an MCP-Agent powered workflow to:
    1. Extract video metadata (title, channel, stats)
    2. Get the full video transcript
    3. Perform deep content analysis
    4. Extract key findings and insights
    5. Generate a comprehensive report with the video link
    
    The agent uses:
    - YouTube Data API for metadata
    - YouTube Transcript API for captions
    - OpenAI GPT-4 for intelligent analysis
    - MCP-Agent workflow orchestration
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=SJi469BuU6g)
        max_key_points: Maximum number of key findings to extract (3-20, default: 15)
        analysis_depth: Level of analysis detail:
            - 'summary': Quick overview with key points
            - 'detailed': Comprehensive analysis with in-depth insights (default)
    
    Returns:
        Markdown-formatted comprehensive analysis report including:
        - Video metadata and link
        - Executive summary
        - Detailed key findings (with explanations if detailed mode)
        - Transcript analysis
        - Conclusions and takeaways
        - Source attribution
    
    Example:
        ```python
        report = await analyze_youtube_video(
            video_url="https://www.youtube.com/watch?v=SJi469BuU6g",
            max_key_points=15,
            analysis_depth="detailed"
        )
        print(report)
        ```
    
    Requirements:
        - YOUTUBE_API_KEY environment variable (get from Google Cloud Console)
        - OPENAI_API_KEY environment variable (get from OpenAI)
        - Video must have captions/transcripts available
    """
    # Validate parameters
    if max_key_points < 3 or max_key_points > 20:
        return json.dumps({
            "error": "max_key_points must be between 3 and 20",
            "provided": max_key_points
        }, indent=2)
    
    if analysis_depth not in ["summary", "detailed"]:
        return json.dumps({
            "error": "analysis_depth must be 'summary' or 'detailed'",
            "provided": analysis_depth
        }, indent=2)
    
    try:
        # Call the MCP-Agent powered analysis
        result = await youtube_agent_analyze(
            video_url=video_url,
            max_key_points=max_key_points,
            analysis_depth=analysis_depth
        )
        return result
    except Exception as e:
        return json.dumps({
            "error": f"Analysis failed: {str(e)}",
            "video_url": video_url,
            "help": "Ensure YOUTUBE_API_KEY and OPENAI_API_KEY are set in environment"
        }, indent=2)


# Discovery helper for CLI
def show_server_info():
    """Display server capabilities"""
    print("=" * 80)
    print("MCP ENHANCED SERVER - CAPABILITIES")
    print("=" * 80)
    print()
    print("🔧 TOOL 1: run_python")
    print("   Execute Python code with zero-context MCP discovery")
    print("   - Sandbox execution with timeout")
    print("   - Runtime helpers for MCP server discovery")
    print("   - ~200 token overhead")
    print()
    print("🎥 TOOL 2: analyze_youtube_video")
    print("   AI-powered YouTube video analysis agent")
    print("   - Extracts video metadata")
    print("   - Gets full transcript")
    print("   - Performs intelligent content analysis")
    print("   - Extracts key findings and insights")
    print("   - Generates comprehensive reports")
    print("   - Powered by MCP-Agent + GPT-4")
    print()
    print("=" * 80)
    print("Available Runtime Helpers (in run_python sandbox):")
    print("-" * 80)
    
    for helper in SANDBOX_HELPERS_SUMMARY["helpers"]:
        print(f"\n{helper['name']}{helper['signature']}")
        print(f"  {helper['description']}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    # Show server info
    if "--info" in sys.argv or "--discover" in sys.argv:
        show_server_info()
    else:
        # Run the FastMCP server
        mcp.run()
