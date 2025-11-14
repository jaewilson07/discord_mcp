# YouTube Research MCP - Planning Notes

## Analysis Date: 2025-11-14

## Research Summary

### Key Repositories Analyzed
1. **camballe/youtube-research-agent** - Simple YouTube search + transcript extraction + summarization
2. **langchain-ai/open_deep_research** - Advanced deep research system with LangGraph

### Core Capabilities Needed

#### 1. YouTube Transcript Extraction
- **Library**: `youtube-transcript-api`
- **Function**: Extract full transcript text from video ID
- **Handles**: Auto-generated and manual captions
- **Error handling**: Falls back gracefully if transcript unavailable

#### 2. YouTube Search
- **API**: YouTube Data API v3
- **Requires**: YOUTUBE_API_KEY
- **Capabilities**:
  - Search by topic/keyword
  - Filter by date, view count, relevance
  - Get video metadata (title, description, ID, URL)
  - Returns video IDs for transcript extraction

#### 3. Video Summarization
- **Approach**: LangChain's map-reduce summarization
- **Process**:
  1. Split transcript into chunks (2000 chars, 200 overlap)
  2. Summarize each chunk
  3. Combine summaries into final summary
- **Model**: GPT-3.5/GPT-4 via OpenAI API

#### 4. Deep Research (from open_deep_research)
- **Pattern**: Plan → Search → Research → Compress → Report
- **Agents**:
  - Summarizer: Compresses search results
  - Researcher: Conducts searches and gathers info
  - Report Writer: Compiles final report
- **Tools**: Web search (Tavily/Brave), MCP servers optional

### MCP Server Considerations

#### Option 1: No existing YouTube MCP server found
Need to create custom tools that wrap:
- YouTube Data API (search)
- youtube-transcript-api library (transcripts)
- OpenAI API (summarization)

#### Option 2: Use existing MCP patterns
- Could use `@modelcontextprotocol/server-brave-search` for general web research
- But need custom YouTube tools for video-specific features

### Proposed Architecture

#### Three Agent System:

1. **YouTube Agent** (Video Specialist)
   - Tools:
     - SearchYouTubeTool - search videos by topic
     - GetTranscriptTool - extract transcript from video URL/ID
     - GetVideoMetadataTool - get video details
   - Role: Find and extract video content

2. **Summarizer Agent** (Content Analyst)
   - Tools:
     - SummarizeVideoTool - create concise video summaries
     - SummarizeMultipleVideosTool - batch summarize
     - ExtractKeyPointsTool - pull out main insights
   - Role: Analyze and compress video content

3. **Research Coordinator** (Project Manager)
   - Tools:
     - CreateResearchPlanTool - outline research approach
     - WebSearchTool (built-in) - supplement with web research
     - CompileReportTool - create final deliverable
   - Role: Orchestrate research project, coordinate agents

#### Communication Flows:
- User → Research Coordinator (initial request)
- Research Coordinator → YouTube Agent (get videos)
- YouTube Agent → Summarizer Agent (process transcripts)
- Summarizer Agent → Research Coordinator (return insights)
- Research Coordinator → User (final report)

### Technical Requirements

#### Dependencies:
```
youtube-transcript-api
google-api-python-client
langchain
langchain-openai
agency-swarm[fastapi]
```

#### Environment Variables:
```
YOUTUBE_API_KEY=<from Google Cloud Console>
OPENAI_API_KEY=<from OpenAI>
```

#### API Setup:
1. Google Cloud Console:
   - Enable YouTube Data API v3
   - Create API credentials
   - Copy API key

2. OpenAI:
   - Create account
   - Generate API key

### Key Implementation Notes

#### YouTube API Quotas:
- Free tier: 10,000 units/day
- Search: 100 units per request
- Video details: 1 unit per request
- ~90 searches per day on free tier

#### Transcript Extraction:
- No API key required
- Library directly scrapes YouTube
- May fail if:
  - Video has no captions
  - Video is private/deleted
  - YouTube changes structure

#### Best Practices:
1. Cache transcripts to avoid re-fetching
2. Batch process multiple videos
3. Handle API rate limits gracefully
4. Provide fallback if transcript unavailable
5. Validate video IDs before processing

### Comparison: Simple vs Advanced

#### Simple (camballe approach):
- Single script flow
- Email delivery
- Limited to batch processing
- Good for: Quick research tasks

#### Advanced (langchain approach):
- Multi-agent coordination
- Iterative research
- Quality checks and refinement
- Good for: Deep, comprehensive research

### Recommended Approach for MCP Server:

Create a **hybrid system**:
- YouTube-specific tools (simple, focused)
- Research coordination (inspired by deep research)
- Flexible: Can do quick summaries OR deep research
- MCP tools exposed for use in Claude Desktop or other MCP clients

### Tool Design Principles (from PRD instructions):

Each tool should be:
1. **Standalone** - Works independently
2. **Configurable** - Adjustable parameters
3. **Composable** - Outputs match other tool inputs

Example:
- SearchYouTubeTool → returns list of video IDs
- GetTranscriptTool → accepts video ID → returns transcript text
- SummarizeVideoTool → accepts transcript text → returns summary
- Agents can chain: Search → Get Transcript → Summarize

### Next Steps:
1. Create PRD document
2. Define exact tool specifications
3. Map out agent instructions
4. Implement tools
5. Configure agents
6. Test workflows
