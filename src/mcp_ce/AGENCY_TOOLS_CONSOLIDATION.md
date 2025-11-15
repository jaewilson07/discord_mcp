# Agency Tools Consolidation Plan

## Overview
Consolidating all Agency Swarm tools from `src/agency/` into the MCP Code Execution server (`src/mcp_ce/`) following the zero-context discovery pattern.

## Tools Inventory

### ✅ Already Implemented
1. **URL Ping Server** (`url_ping`)
   - `ping_url` - Ping URLs and check availability

### 🚧 YouTube Server (`youtube`)
**Source:** `src/agency/youtube_agent/tools/`
- ✅ `search_youtube` - Search YouTube for videos
- ✅ `get_transcript` - Extract video transcripts
- ✅ `get_video_metadata` - Get detailed video information

**Dependencies:** `google-api-python-client`, `youtube-transcript-api`

### 📝 Notion Server (`notion`)
**Source:** `src/agency/notion_agent/tools/`
- `search_notion` - Search pages and databases
- `get_notion_page` - Retrieve page details
- `create_notion_page` - Create new pages
- `update_notion_page` - Update page properties
- `query_notion_database` - Query databases with filters
- `add_notion_comment` - Add comments to pages

**Dependencies:** `notion-mcp` (uses NotionMCPClient)

### 🕷️ Crawl4AI Server (`crawl4ai`)
**Source:** `src/agency/crawl4ai_agent/tools/`
- `crawl_website` - Crawl and extract website content
- `save_article` - Save extracted content to JSON

**Dependencies:** `crawl4ai`, `asyncio`

### 🤖 Summarizer Server (`summarizer`)
**Source:** `src/agency/summarizer_agent/tools/`
- `summarize_transcript` - Create AI summary of transcript
- `extract_key_points` - Extract main ideas from text
- `compare_videos` - Compare multiple video summaries

**Dependencies:** `langchain`, `langchain-openai`, `OPENAI_API_KEY`

### 📊 Research Server (`research`)
**Source:** `src/agency/research_coordinator/tools/`
- `create_research_plan` - Generate structured research plan
- `compile_research_report` - Synthesize findings into report

**Dependencies:** `langchain`, `langchain-openai`, `OPENAI_API_KEY`

## Implementation Status

### Phase 1: Tool File Creation ✅
- [x] Create YouTube tools (`search_youtube.py`, `get_transcript.py`, `get_video_metadata.py`)
- [ ] Create Notion tools (6 files)
- [ ] Create Crawl4AI tools (2 files)
- [ ] Create Summarizer tools (3 files)
- [ ] Create Research tools (2 files)

### Phase 2: Runtime Registry Update
- [ ] Add all servers to `_SERVERS_REGISTRY`
- [ ] Update `query_tool_docs()` with all tool schemas
- [ ] Update `_execute_tool()` with all tool imports

### Phase 3: Testing
- [ ] Test YouTube tools via discovery workflow
- [ ] Test Notion tools (requires `NOTION_TOKEN`)
- [ ] Test Crawl4AI tools
- [ ] Test Summarizer tools (requires `OPENAI_API_KEY`)
- [ ] Test Research tools (requires `OPENAI_API_KEY`)

## Migration Strategy

### Tool Conversion Pattern

**Before (Agency Swarm):**
```python
from agency_swarm.tools import BaseTool
class SearchYouTubeTool(BaseTool):
    query: str = Field(...)
    def run(self):
        # implementation
        return result_string
```

**After (MCP Code Execution):**
```python
async def search_youtube(query: str, ...) -> Dict[str, Any]:
    """Tool description"""
    # implementation
    return {
        "success": True,
        "data": result_dict,
        "error": None
    }
```

### Key Changes
1. Remove `BaseTool` inheritance
2. Change from `run()` method to async function
3. Return dicts instead of strings (native Python objects)
4. Remove Pydantic Field descriptions (move to docstrings)

## Environment Variables Required

```bash
# YouTube API
YOUTUBE_API_KEY=your_key_here

# Notion API
NOTION_TOKEN=your_token_here

# OpenAI API (for summarizer and research)
OPENAI_API_KEY=your_key_here
```

## Benefits of Consolidation

1. **Zero-Context Discovery**: ~200 token overhead vs ~30K for traditional MCP
2. **Progressive Disclosure**: Load only needed tool schemas
3. **Code Execution Pattern**: Tools called via Python code, not direct MCP calls
4. **Unified Interface**: All tools accessible through single `run_python` MCP tool
5. **Native Data Types**: Tools return Python dicts for easy manipulation

## Usage Example (After Consolidation)

```python
# Discover available servers
import json
servers = discovered_servers()
print(json.dumps(servers, indent=2))

# Query YouTube tools
docs = query_tool_docs("youtube", detail="full")
print(docs)

# Search YouTube
async def main():
    search_youtube = create_tool_proxy("youtube", "search_youtube")
    results = await search_youtube(query="LangChain tutorial", max_results=5)
    
    if results['success']:
        for video in results['videos']:
            print(f"{video['title']}: {video['url']}")
    
    # Get transcript for first video
    get_transcript = create_tool_proxy("youtube", "get_transcript")
    transcript = await get_transcript(video_id=results['videos'][0]['id'])
    
    # Summarize transcript
    summarize = create_tool_proxy("summarizer", "summarize_transcript")
    summary = await summarize(
        transcript=transcript['transcript'],
        video_title=results['videos'][0]['title'],
        summary_length="medium"
    )
    
    return summary

# main() will be auto-awaited by sandbox
```

## Next Steps

1. Complete tool file creation for remaining servers
2. Update runtime.py with comprehensive registry
3. Add tool schemas to query_tool_docs()
4. Add tool execution to _execute_tool()
5. Create comprehensive test suite
6. Update README with all available tools

## Notes

- All tools should return dicts with `success` field
- Async/await pattern required for all tools
- Error handling should return `{"success": False, "error": "message"}`
- Tool names should be snake_case for Python conventions
- Keep tool documentation in docstrings for query_tool_docs()
