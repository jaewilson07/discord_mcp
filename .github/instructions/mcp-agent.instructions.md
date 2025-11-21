applyTo: "src/mcp_ce/agentic_tools/graphs/**/*.py"
excludeAgent: ["code-review"]
---

# MCP-Agent Development Instructions

These instructions apply when creating or modifying AI agents using the mcp-agent framework.

## MCP-Agent Pattern Overview

MCP-Agent uses a decorator-based pattern for defining tools that can be called by AI agents. It's different from MCP CE tools - agents are exposed as FastMCP tools themselves.

## Agent File Structure

```python
"""Agent description."""

from mcp_agent import MCPApp, Agent
from openai import OpenAI

# Create MCP app
app = MCPApp("agent-name")

# Define tools using decorators
@app.async_tool()
async def async_tool(param: str) -> str:
    """
    Asynchronous tool description.
    
    Args:
        param: Parameter description
        
    Returns:
        Result description
    """
    result = await async_operation(param)
    return result

# Create LLM instance
llm = OpenAI(api_key="...")

# Create agent with tools
agent = Agent(
    name="agent-name",
    instructions="Detailed agent behavior instructions",
    app=app,
    llm=llm,
)
```

## Tool Decorator Usage

### Synchronous Tools (@app.tool)

Use for CPU-bound operations or when no async operations are needed:

```python
@app.tool()
def process_text(text: str, operation: str = "uppercase") -> str:
    """
    Process text with the specified operation.
    
    Args:
        text: Input text to process
        operation: Operation to perform (uppercase, lowercase, reverse)
        
    Returns:
        Processed text
    """
    if operation == "uppercase":
        return text.upper()
    elif operation == "lowercase":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    else:
        return text
```

### Asynchronous Tools (@app.async_tool)

Use for I/O operations, API calls, or async libraries:

```python
@app.async_tool()
async def fetch_data(url: str, timeout: int = 10) -> dict:
    """
    Fetch data from a URL.
    
    Args:
        url: URL to fetch from
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Dictionary with response data
    """
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
```

## Agent Instructions

Write clear, detailed instructions that guide the agent's behavior:

```python
agent = Agent(
    name="research-assistant",
    instructions="""
You are a research assistant specialized in analyzing YouTube videos.

Your responsibilities:
1. Search for relevant videos based on user queries
2. Extract and summarize video transcripts
3. Identify key points and insights
4. Compare multiple videos on the same topic
5. Provide comprehensive research reports

Guidelines:
- Always verify video availability before analysis
- Cite specific timestamps when referencing content
- Highlight contradictions between sources
- Prioritize recent and authoritative content
- Use clear, academic language in reports

When asked to analyze a video:
1. Get metadata (title, channel, duration, views)
2. Retrieve full transcript
3. Summarize main points with timestamps
4. Extract key insights and quotes
5. Provide actionable takeaways
""",
    app=app,
    llm=llm,
)
```

## LLM Configuration

### OpenAI

```python
from openai import OpenAI

llm = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # Optional: specify model
    # model="gpt-4-turbo-preview"
)
```

### Anthropic Claude

```python
from anthropic import Anthropic

llm = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
```

## Exposing Agents as FastMCP Tools

To make an agent available in MCP CE, expose it via FastMCP in a separate server file:

```python
"""Enhanced MCP server with YouTube analysis agent."""

from fastmcp import FastMCP
from .youtube_analysis_agent import agent

# Create FastMCP server
mcp = FastMCP("YouTube Analysis Agent")

# Add agent as tool
@mcp.tool()
async def analyze_youtube_video(
    video_url: str,
    analysis_type: str = "comprehensive"
) -> str:
    """
    Analyze a YouTube video using AI agent.
    
    Args:
        video_url: YouTube video URL
        analysis_type: Type of analysis (comprehensive, summary, key-points)
        
    Returns:
        Analysis result as string
    """
    prompt = f"Analyze this video: {video_url}. Provide a {analysis_type} analysis."
    result = await agent.run(prompt)
    return result
```

## Error Handling in Agent Tools

Always handle errors gracefully:

```python
@app.async_tool()
async def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    """
    Fetch data with automatic retries.
    
    Args:
        url: URL to fetch
        max_retries: Maximum retry attempts (default: 3)
        
    Returns:
        Response data
        
    Raises:
        Exception: If all retries fail
    """
    import httpx
    import asyncio
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Type Hints and Documentation

Use comprehensive type hints for better IDE support and validation:

```python
from typing import List, Dict, Any, Optional

@app.tool()
def process_items(
    items: List[str],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a list of items with optional configuration.
    
    Args:
        items: List of items to process
        options: Processing options (optional):
            - filter_empty (bool): Remove empty items
            - sort (bool): Sort items alphabetically
            - deduplicate (bool): Remove duplicates
            
    Returns:
        Dictionary with:
        - processed_items: List of processed items
        - count: Number of items processed
        - removed: Number of items removed
    """
    options = options or {}
    processed = items.copy()
    removed = 0
    
    if options.get("filter_empty"):
        processed = [item for item in processed if item.strip()]
        removed = len(items) - len(processed)
    
    if options.get("deduplicate"):
        original_count = len(processed)
        processed = list(dict.fromkeys(processed))
        removed += original_count - len(processed)
    
    if options.get("sort"):
        processed.sort()
    
    return {
        "processed_items": processed,
        "count": len(processed),
        "removed": removed,
    }
```

## Agent Testing

Create tests for agent tools and behavior:

```python
import pytest
from .youtube_analysis_agent import agent, app

def test_tool_registration():
    """Test that tools are registered correctly."""
    tools = app.list_tools()
    assert "get_video_metadata" in [t.name for t in tools]
    assert "get_transcript" in [t.name for t in tools]

@pytest.mark.asyncio
async def test_video_analysis():
    """Test video analysis workflow."""
    result = await agent.run(
        "Analyze this video: https://youtube.com/watch?v=example"
    )
    assert result is not None
    assert len(result) > 0

def test_tool_execution():
    """Test individual tool execution."""
    # Test with mcp-agent's test runner
    from mcp_agent import test_tool
    
    result = test_tool(
        app,
        "get_video_metadata",
        video_url="https://youtube.com/watch?v=example"
    )
    assert "title" in result
```

## Common Patterns

### Multi-Step Analysis

```python
@app.async_tool()
async def comprehensive_analysis(topic: str) -> str:
    """
    Perform comprehensive multi-step analysis.
    
    Args:
        topic: Topic to analyze
        
    Returns:
        Detailed analysis report
    """
    # Step 1: Search
    videos = await search_youtube(topic)
    
    # Step 2: Analyze top results
    analyses = []
    for video in videos[:3]:
        transcript = await get_transcript(video["id"])
        summary = await summarize_transcript(transcript)
        analyses.append(summary)
    
    # Step 3: Compare and compile
    report = await compile_research_report(topic, analyses)
    
    return report
```

### Stateful Tools

```python
class AnalysisState:
    """Shared state for analysis tools."""
    def __init__(self):
        self.videos = []
        self.transcripts = {}
        self.summaries = {}

state = AnalysisState()

@app.async_tool()
async def add_video(video_id: str) -> str:
    """Add video to analysis queue."""
    state.videos.append(video_id)
    return f"Added video {video_id}. Queue: {len(state.videos)} videos"

@app.async_tool()
async def process_queue() -> str:
    """Process all queued videos."""
    results = []
    for video_id in state.videos:
        transcript = await get_transcript(video_id)
        state.transcripts[video_id] = transcript
        results.append(f"Processed {video_id}")
    return "\n".join(results)
```

### Tool Composition

```python
@app.async_tool()
async def extract_key_points(video_url: str) -> List[str]:
    """Extract key points from video."""
    transcript = await get_transcript(video_url)
    # Process transcript...
    return key_points

@app.async_tool()
async def compare_videos(url1: str, url2: str) -> str:
    """Compare two videos."""
    points1 = await extract_key_points(url1)
    points2 = await extract_key_points(url2)
    # Compare points...
    return comparison_report
```

## Best Practices

1. **Clear Tool Names**: Use descriptive, action-oriented names
2. **Comprehensive Docstrings**: Include Args, Returns, and examples
3. **Type Hints**: Always specify parameter and return types
4. **Error Handling**: Catch and report errors gracefully
5. **Async When Needed**: Use async tools for I/O operations
6. **Stateless Tools**: Prefer stateless tools for easier testing
7. **Modular Design**: Break complex operations into smaller tools
8. **Test Coverage**: Write tests for all tools and agent behaviors

## Validation Checklist

Before committing agent code:

- [ ] All tools have `@app.tool()` or `@app.async_tool()` decorators
- [ ] Tool functions have comprehensive docstrings
- [ ] Type hints on all parameters and return values
- [ ] Error handling with try/except blocks
- [ ] Agent has detailed instructions
- [ ] LLM properly configured with API key
- [ ] Tests written for tools and agent behavior
- [ ] Integration with FastMCP if exposing to MCP CE

## Example: Complete Agent

```python
"""YouTube video analysis agent using mcp-agent."""

from mcp_agent import MCPApp, Agent
from openai import OpenAI
import os
from typing import List, Dict, Any

# Create app
app = MCPApp("youtube-analyzer")

@app.async_tool()
async def search_videos(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for YouTube videos.
    
    Args:
        query: Search query
        max_results: Maximum results (default: 5)
        
    Returns:
        List of video dictionaries with id, title, channel
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    # Implementation...
    return results

@app.async_tool()
async def get_transcript(video_id: str) -> str:
    """
    Get video transcript.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Full transcript text
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry["text"] for entry in transcript])

@app.async_tool()
async def summarize_transcript(transcript: str, length: str = "medium") -> str:
    """
    Summarize video transcript.
    
    Args:
        transcript: Full transcript text
        length: Summary length (short, medium, long)
        
    Returns:
        Summary text
    """
    # Use LLM to summarize
    word_limits = {"short": 100, "medium": 250, "long": 500}
    limit = word_limits.get(length, 250)
    
    # Create summary using the agent's LLM
    summary = f"[Summary of ~{limit} words would be generated here]"
    return summary

# Create agent
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

agent = Agent(
    name="youtube-analyst",
    instructions="""
You are an expert YouTube video analyst. Your role is to:

1. Search for relevant videos based on user queries
2. Retrieve and analyze video transcripts
3. Extract key insights and main points
4. Compare multiple videos on similar topics
5. Provide clear, structured summaries

Always:
- Verify video availability before analysis
- Cite specific quotes from transcripts
- Highlight important timestamps
- Note contradictions between sources
- Present findings in organized formats
""",
    app=app,
    llm=llm,
)

if __name__ == "__main__":
    # Test the agent
    import asyncio
    
    async def test():
        result = await agent.run(
            "Find and summarize the top 3 videos about Python async programming"
        )
        print(result)
    
    asyncio.run(test())
```

## Reference

- **MCP-Agent Docs**: Check the mcp-agent package documentation
- **Example Agent**: `src/agency/youtube_analysis_agent.py`
- **FastMCP Integration**: `src/mcp_ce/server_enhanced.py`
- **Testing**: `tests/test_agents.py`
