# YouTube Video Analysis Request

## Video to Analyze
**URL:** https://www.youtube.com/watch?v=SJi469BuU6g&t=321s
**Video ID:** SJi469BuU6g

## Analysis Requirements
- Extract full transcript
- Detailed key findings analysis
- Include video link in the report

## Setup Required

Before running the agency, you need to configure API keys in `.env`:

```env
# Add these to your .env file:
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Getting API Keys:

#### OpenAI API Key:
1. Go to https://platform.openai.com/
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new secret key
5. Copy and paste into `.env`

#### YouTube API Key:
1. Go to https://console.cloud.google.com/
2. Create a new project (if needed)
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Copy and paste into `.env`

## How to Run the Analysis

Once API keys are configured:

```bash
# Option 1: Use the installed command
youtube-research

# Option 2: Run as Python module
python -m agency.youtube_agency
```

## What to Say to the Agency

When the terminal demo starts, enter:

```
Analyze this YouTube video in great detail and extract all key findings: 
https://www.youtube.com/watch?v=SJi469BuU6g&t=321s

Please:
1. Get the full transcript
2. Extract all key points and findings
3. Provide detailed analysis of each finding
4. Include the video link in your report
5. Format as a comprehensive research report
```

## Expected Workflow

The agency will:

1. **Research Coordinator** will receive your request
2. **YouTube Agent** will:
   - Extract video metadata
   - Get the full transcript
   - Return data to coordinator
3. **Summarizer Agent** will:
   - Analyze the transcript in detail
   - Extract all key findings
   - Identify important points
4. **Research Coordinator** will:
   - Compile everything into a detailed report
   - Include video link and citations
   - Present comprehensive analysis

## Alternative: Run Specific Tools Directly

If you want to test individual tools without the full agency:

```bash
# Test getting transcript
cd src/agency/youtube_agent/tools
python GetTranscriptTool.py

# Then manually edit the script to use your video ID
```

## Tools Available for This Task

1. **GetTranscriptTool** - Extracts video transcript
2. **GetVideoMetadataTool** - Gets video details
3. **ExtractKeyPointsTool** - Pulls out key findings
4. **SummarizeTranscriptTool** - Creates detailed summary
5. **CompileResearchReportTool** - Generates final report

## Expected Output

The agency will produce a markdown report containing:

- Video title and link
- Executive summary
- Detailed key findings (numbered/bulleted)
- Analysis of each finding
- Supporting quotes from transcript
- Conclusions
- Source citation

## Troubleshooting

### "OpenAI API key is not set"
- Add `OPENAI_API_KEY` to `.env` file
- Restart the agency

### "YOUTUBE_API_KEY not found"
- Add `YOUTUBE_API_KEY` to `.env` file
- Ensure API is enabled in Google Cloud Console

### "No transcript available"
- Video may not have captions
- Try a different video
- Check if video is private/deleted

## Status

✅ Agency implemented and ready
✅ All tools created
❌ API keys need to be configured (blocking execution)

Once you add the API keys, the agency will be fully functional!
