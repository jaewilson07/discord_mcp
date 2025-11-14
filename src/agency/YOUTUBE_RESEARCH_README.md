# YouTube Research Agency

A multi-agent AI system for conducting comprehensive research using YouTube videos as primary sources. Built with Agency Swarm.

## Features

- 🔍 **Smart Video Discovery** - Searches YouTube using multiple strategies and filters
- 📝 **Automatic Transcript Extraction** - Extracts full transcripts from videos
- 🤖 **AI-Powered Analysis** - Summarizes content and extracts key insights
- 📊 **Comparative Analysis** - Analyzes themes across multiple videos
- 📄 **Professional Reports** - Generates structured research reports with citations
- ⚡ **Flexible Scope** - From quick summaries to deep research projects

## Architecture

### Three Specialized Agents:

1. **Research Coordinator** (Project Manager)
   - Orchestrates the research process
   - Creates research plans
   - Compiles final reports
   - Primary user interface

2. **YouTube Agent** (Video Specialist)
   - Searches for relevant videos
   - Extracts transcripts
   - Retrieves video metadata

3. **Summarizer Agent** (Content Analyst)
   - Summarizes video transcripts
   - Extracts key points
   - Compares multiple videos

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```env
# Required
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Discord (if using Discord MCP)
DISCORD_TOKEN=your_discord_token_here
```

### 3. Get API Keys

#### YouTube API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Copy key and add to `.env`

#### OpenAI API Key:
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create new secret key
5. Copy key and add to `.env`

## Usage

### Terminal Demo

Run the agency in terminal mode for interactive testing:

```bash
python -m src.agency.youtube_agency
```

### FastAPI Deployment

Deploy as an API service:

```bash
# Update main.py to include YouTube agency
python -m src.agency.main
```

### Example Queries

**Quick Summary:**
```
"Summarize the latest LangChain tutorial videos"
```

**Deep Research:**
```
"Do comprehensive research on multi-agent AI systems - analyze 15-20 videos"
```

**Specific Analysis:**
```
"Analyze this video and extract technical key points: https://youtube.com/watch?v=..."
```

**Comparative Study:**
```
"Compare approaches to RAG implementation across top tutorials"
```

## Research Scopes

- **Quick** (1-3 videos): Fast overview of a topic
- **Moderate** (5-10 videos): Balanced research with multiple perspectives
- **Comprehensive** (15-25 videos): Deep dive with thorough analysis

## Tools Available

### YouTube Agent Tools:
- `SearchYouTubeTool` - Find videos by topic
- `GetTranscriptTool` - Extract video transcripts
- `GetVideoMetadataTool` - Get detailed video information

### Summarizer Agent Tools:
- `SummarizeTranscriptTool` - Create video summaries
- `ExtractKeyPointsTool` - Pull out main insights
- `CompareVideosTool` - Analyze multiple videos

### Research Coordinator Tools:
- `CreateResearchPlanTool` - Design research approach
- `CompileResearchReportTool` - Generate final reports
- `WebSearchTool` - Supplement with web research

## Output Formats

- **Executive Summary**: Brief overview (1-2 pages)
- **Standard Report**: Balanced analysis (3-5 pages)
- **Detailed Report**: Comprehensive study (5-10 pages)

All reports include:
- Executive summary
- Key findings organized by theme
- Analysis and insights
- Conclusions and recommendations
- Source citations with URLs

## Limitations

- **YouTube API Quota**: Free tier allows ~90 searches/day
- **Transcript Availability**: Only works with videos that have captions
- **OpenAI Costs**: API usage scales with video count and transcript length
- **Language Support**: Primarily English, but can handle other languages if transcripts available

## Best Practices

1. **Start Small**: Test with quick scope before comprehensive research
2. **Be Specific**: Clear research questions yield better results
3. **Check Quotas**: Monitor YouTube API usage
4. **Cache Results**: Save reports to avoid re-processing
5. **Verify Sources**: Always check video URLs and citations

## Troubleshooting

### "YOUTUBE_API_KEY not found"
- Verify `.env` file exists in project root
- Check API key is correctly formatted
- Ensure no extra spaces or quotes

### "No transcript available"
- Video doesn't have captions enabled
- Try different videos on the same topic
- Use metadata and descriptions instead

### "Rate limit exceeded"
- YouTube API quota reached (resets daily)
- Reduce number of searches
- Use more specific search queries

### "OpenAI API error"
- Check API key is valid
- Verify billing is set up
- Check rate limits haven't been exceeded

## Project Structure

```
src/agency/
├── youtube_agency.py              # Main agency configuration
├── youtube_shared_instructions.md # Shared agent guidelines
├── youtube_agent/
│   ├── youtube_agent.py
│   ├── instructions.md
│   └── tools/
│       ├── SearchYouTubeTool.py
│       ├── GetTranscriptTool.py
│       └── GetVideoMetadataTool.py
├── summarizer_agent/
│   ├── summarizer_agent.py
│   ├── instructions.md
│   └── tools/
│       ├── SummarizeTranscriptTool.py
│       ├── ExtractKeyPointsTool.py
│       └── CompareVideosTool.py
└── research_coordinator/
    ├── research_coordinator.py
    ├── instructions.md
    └── tools/
        ├── CreateResearchPlanTool.py
        └── CompileResearchReportTool.py
```

## Documentation

- [PRD](youtube_research_prd.md) - Complete product requirements
- [Planning Notes](instructions/youtube-research-notes.md) - Technical analysis
- [Agency Swarm Docs](https://agency-swarm.ai/)

## License

MIT License - see main project LICENSE file
