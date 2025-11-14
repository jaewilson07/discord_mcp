# YouTube Research Agency - PRD

---

## Agency Overview

- **Purpose:** A multi-agent system that enables comprehensive YouTube video research through automated video discovery, transcript extraction, content summarization, and deep research compilation. Target users include researchers, content creators, educators, and businesses needing to extract insights from YouTube content at scale.

- **Communication Flows:**
  - **Between Agents:**
    - **Research Coordinator → YouTube Agent:** Sends research topics, keywords, and video criteria
    - **YouTube Agent → Summarizer Agent:** Forwards video transcripts and metadata for analysis
    - **Summarizer Agent → Research Coordinator:** Returns summaries, key points, and insights
    - **Research Coordinator → All Agents:** Coordinates multi-phase research projects
  - **Agent to User Communication:** 
    - Primary interface through Research Coordinator agent
    - Users submit research topics or video URLs
    - Receive structured reports with summaries, insights, and source citations
    - Can request deep research for comprehensive analysis or quick summaries for rapid insights

---

## YouTube Agent

### Role within the Agency

Video Content Specialist - Responsible for discovering, accessing, and extracting content from YouTube videos. Functions like a digital video librarian who can search YouTube's catalog, retrieve video information, and extract transcripts for analysis.

### Tools

- **SearchYouTubeTool:**
  - **Description**: Searches YouTube for videos matching a topic or keywords. Returns video metadata including IDs, titles, descriptions, URLs, and view counts. Used when researching a topic or gathering multiple videos on a subject.
  - **Inputs**:
    - query (str) - Search query or topic
    - max_results (int, default=5) - Number of videos to return (1-50)
    - order_by (str, default="relevance") - Sort order: "relevance", "date", "viewCount", "rating"
    - published_after (str, optional) - ISO date string to filter recent videos
  - **Validation**:
    - query must not be empty
    - max_results must be between 1 and 50
    - published_after must be valid ISO date format if provided
  - **Core Functions:** 
    - Connects to YouTube Data API v3
    - Executes search query
    - Parses and structures response
    - Returns list of video objects
  - **APIs**: YouTube Data API v3
  - **Output**: JSON array of video objects containing {id, title, description, url, published_at, view_count}

- **GetTranscriptTool:**
  - **Description**: Extracts the full transcript text from a YouTube video using its video ID or URL. Retrieves auto-generated or manual captions. Used after finding videos to get complete content for analysis.
  - **Inputs**:
    - video_id (str) - YouTube video ID or full URL
    - languages (list, default=["en"]) - Preferred transcript languages in priority order
  - **Validation**:
    - video_id must not be empty
    - Must extract valid 11-character video ID from URL if full URL provided
  - **Core Functions:** 
    - Parses video ID from URL or uses direct ID
    - Calls youtube-transcript-api library
    - Concatenates transcript segments into full text
    - Handles language preferences
  - **APIs**: youtube-transcript-api (no API key needed - direct scraping)
  - **Output**: String containing full transcript text, or error message if transcript unavailable

- **GetVideoMetadataTool:**
  - **Description**: Retrieves detailed metadata for a specific YouTube video including title, description, duration, tags, channel info, and statistics. Used to gather context about videos before or after transcript extraction.
  - **Inputs**:
    - video_id (str) - YouTube video ID
  - **Validation**:
    - video_id must be valid 11-character YouTube ID
  - **Core Functions:** 
    - Calls YouTube Data API videos endpoint
    - Extracts metadata fields
    - Formats statistics (views, likes, comments)
  - **APIs**: YouTube Data API v3
  - **Output**: JSON object with {title, description, channel, duration, tags, view_count, like_count, comment_count, published_at}

---

## Summarizer Agent

### Role within the Agency

Content Analyst - Responsible for processing video transcripts and extracting meaningful insights. Functions like a research analyst who reads through content, identifies key points, and creates concise summaries that preserve essential information while reducing length.

### Tools

- **SummarizeTranscriptTool:**
  - **Description**: Creates a concise summary of a video transcript using AI. Employs map-reduce strategy to handle long transcripts by chunking, summarizing parts, then combining. Used to quickly understand video content without reading full transcripts.
  - **Inputs**:
    - transcript (str) - Full video transcript text
    - video_title (str) - Video title for context
    - summary_length (str, default="medium") - Desired length: "short" (2-3 sentences), "medium" (1 paragraph), "long" (multiple paragraphs)
  - **Validation**:
    - transcript must not be empty
    - summary_length must be one of: "short", "medium", "long"
  - **Core Functions:** 
    - Splits transcript into chunks (2000 chars, 200 overlap)
    - Uses LangChain's map-reduce summarization
    - Calls OpenAI API for each chunk and final combination
    - Adjusts detail based on summary_length parameter
  - **APIs**: OpenAI API (GPT-3.5-turbo or GPT-4)
  - **Output**: String containing formatted summary

- **ExtractKeyPointsTool:**
  - **Description**: Analyzes transcript and extracts main ideas, important facts, and key takeaways as a structured list. Used when specific insights are more valuable than narrative summary.
  - **Inputs**:
    - transcript (str) - Full video transcript text
    - max_points (int, default=10) - Maximum number of key points to extract
    - focus_area (str, optional) - Specific topic to focus extraction on
  - **Validation**:
    - transcript must not be empty
    - max_points must be between 3 and 20
  - **Core Functions:** 
    - Uses LLM with structured output to identify key points
    - Ranks points by importance
    - Filters by focus_area if provided
  - **APIs**: OpenAI API
  - **Output**: JSON array of strings, each containing one key point

- **CompareVideosTool:**
  - **Description**: Analyzes multiple video summaries to find common themes, differences, and unique insights across videos. Used for research that involves multiple sources on the same topic.
  - **Inputs**:
    - video_summaries (list) - Array of summary objects with {title, summary, url}
    - comparison_criteria (str, optional) - Specific aspect to compare (e.g., "technical accuracy", "viewpoint", "completeness")
  - **Validation**:
    - video_summaries must contain at least 2 summaries
    - Each summary object must have title and summary fields
  - **Core Functions:** 
    - Compiles all summaries into comparison prompt
    - Identifies themes and differences using LLM
    - Structures findings into categories
  - **APIs**: OpenAI API
  - **Output**: JSON object with {common_themes: [], unique_insights: {video_title: [insights]}, comparison_summary: str}

---

## Research Coordinator Agent

### Role within the Agency

Research Project Manager - Orchestrates the entire research process from planning through final report delivery. Functions like a senior researcher who designs research methodology, coordinates specialists, synthesizes findings, and produces comprehensive reports. This is the primary agent users interact with.

### Tools

- **CreateResearchPlanTool:**
  - **Description**: Generates a structured research plan based on user's research question or topic. Defines search strategy, number of sources, analysis approach, and expected deliverables. Used at the start of research projects to organize work.
  - **Inputs**:
    - research_topic (str) - Main research question or topic
    - scope (str, default="comprehensive") - "quick" (1-3 videos), "moderate" (5-10 videos), "comprehensive" (15-25 videos)
    - specific_questions (list, optional) - Specific questions to answer
  - **Validation**:
    - research_topic must not be empty
    - scope must be one of: "quick", "moderate", "comprehensive"
  - **Core Functions:** 
    - Analyzes topic to determine search keywords
    - Calculates video count based on scope
    - Structures research phases (discovery, analysis, synthesis)
    - Creates checklist of deliverables
  - **APIs**: OpenAI API
  - **Output**: JSON object with {search_queries: [], video_count: int, analysis_approach: str, deliverables: [], estimated_time: str}

- **CompileResearchReportTool:**
  - **Description**: Synthesizes all gathered information into a comprehensive research report. Combines video summaries, key insights, and web research into structured document with citations. Used to create final deliverable.
  - **Inputs**:
    - research_topic (str) - Original research question
    - video_insights (list) - Array of video summaries and key points
    - additional_context (str, optional) - Web research or supplementary information
    - report_format (str, default="standard") - "executive_summary", "standard", "detailed"
  - **Validation**:
    - research_topic must not be empty
    - video_insights must contain at least 1 item
    - report_format must be one of the three options
  - **Core Functions:** 
    - Structures content by themes
    - Synthesizes across sources
    - Formats with sections (intro, findings, conclusions)
    - Adds source citations
    - Adjusts detail level based on format
  - **APIs**: OpenAI API
  - **Output**: String containing formatted markdown report

- **WebSearchTool** (Built-in Agency Swarm Tool):
  - **Description**: Performs web searches to supplement YouTube research with additional context, fact-checking, or related information.
  - **Core Functions:** Searches web, returns relevant results
  - **Output**: List of search results with titles, URLs, snippets

---

## API Requirements & Environment Setup

### Required API Keys (add to .env):
```
YOUTUBE_API_KEY=<your_youtube_api_key>
OPENAI_API_KEY=<your_openai_api_key>
```

### How to Obtain API Keys:

**YouTube API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Copy key and add to .env

**OpenAI API Key:**
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create new secret key
5. Copy key and add to .env

### Additional Dependencies:
```
youtube-transcript-api
google-api-python-client
langchain
langchain-openai
langchain-text-splitters
```

---

## Usage Examples

### Quick Summary (1-3 videos):
User: "Summarize the latest videos on LangChain"
→ Research Coordinator creates quick plan
→ YouTube Agent searches and gets transcripts
→ Summarizer creates summaries
→ Research Coordinator returns report

### Deep Research (15-25 videos):
User: "Do comprehensive research on multi-agent AI systems"
→ Research Coordinator creates detailed plan with multiple search queries
→ YouTube Agent finds 20+ relevant videos
→ Summarizer analyzes all transcripts
→ Research Coordinator synthesizes themes, compares approaches
→ Uses WebSearch for supplementary info
→ Returns comprehensive report with citations

### Specific Video Analysis:
User: "Analyze this video: [URL] and extract key technical points"
→ YouTube Agent gets transcript
→ Summarizer extracts key points with technical focus
→ Returns structured insights

---

## Notes

- YouTube API has quota limits (10,000 units/day free tier, ~90 searches/day)
- Transcript extraction works on videos with captions only
- Consider caching transcripts to avoid re-fetching
- Batch processing recommended for multiple videos
- Cost consideration: OpenAI API usage scales with video count and transcript length
