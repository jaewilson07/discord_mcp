"""
YouTube Video Analysis MCP Agent

This agent can be exposed as an MCP tool that analyzes YouTube videos in detail.
It uses MCP-Agent patterns to orchestrate video analysis workflows.
"""

import asyncio
from typing import Optional
from pydantic import BaseModel, Field

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Create the MCP app
app = MCPApp(name="youtube_video_analyzer")


class VideoAnalysisResult(BaseModel):
    """Structured result from video analysis"""
    video_url: str
    video_id: str
    title: str
    key_findings: list[str]
    detailed_analysis: str
    transcript_length: int
    
    
class VideoAnalysisRequest(BaseModel):
    """Request for video analysis"""
    video_url: str = Field(description="YouTube video URL to analyze")
    max_key_points: int = Field(default=15, description="Maximum number of key findings to extract")
    analysis_depth: str = Field(default="detailed", description="Analysis depth: 'summary' or 'detailed'")


@app.tool
async def analyze_youtube_video(
    video_url: str,
    max_key_points: int = 15,
    analysis_depth: str = "detailed"
) -> str:
    """
    Analyze a YouTube video in great detail and extract key findings.
    
    This tool extracts the video transcript, analyzes the content, and returns
    a comprehensive report including key findings, detailed analysis, and the video link.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        max_key_points: Maximum number of key findings to extract (default: 15)
        analysis_depth: Level of analysis - 'summary' or 'detailed' (default: 'detailed')
    
    Returns:
        Comprehensive analysis report in markdown format with video link
    """
    async with app.run() as running_app:
        logger = running_app.logger
        
        # Extract video ID from URL
        video_id = _extract_video_id(video_url)
        if not video_id:
            return f"Error: Could not extract video ID from URL: {video_url}"
        
        logger.info(f"Analyzing video", data={"video_id": video_id, "url": video_url})
        
        # Create YouTube analysis agent
        analyzer_agent = Agent(
            name="youtube_analyzer",
            instruction=f"""You are a YouTube video content analyst. Your task is to:
            1. Extract the full transcript from the video
            2. Analyze the content in {analysis_depth} detail
            3. Extract exactly {max_key_points} key findings
            4. Provide detailed insights for each finding
            5. Include the video link in all reports
            
            Be thorough, accurate, and provide actionable insights.""",
            server_names=[]  # We'll use custom functions
        )
        
        # Add custom tools to the agent
        analyzer_agent.add_function_tool(_get_video_metadata)
        analyzer_agent.add_function_tool(_get_video_transcript)
        analyzer_agent.add_function_tool(_extract_key_findings)
        
        async with analyzer_agent:
            # Attach OpenAI LLM
            llm = await analyzer_agent.attach_llm(OpenAIAugmentedLLM)
            
            # Step 1: Get video metadata
            logger.info("Step 1: Getting video metadata...")
            metadata_result = await llm.generate_str(
                message=f"Get the metadata for video ID: {video_id}"
            )
            
            # Step 2: Get transcript
            logger.info("Step 2: Extracting transcript...")
            transcript_result = await llm.generate_str(
                message=f"Get the full transcript for video ID: {video_id}"
            )
            
            # Step 3: Extract key findings
            logger.info(f"Step 3: Extracting {max_key_points} key findings...")
            if analysis_depth == "detailed":
                analysis_prompt = f"""
                Analyze the transcript in great detail and extract exactly {max_key_points} key findings.
                For each finding:
                - Provide a clear, concise statement of the finding
                - Explain why it's significant
                - Include supporting evidence from the transcript
                - Note any implications or applications
                
                Format as a numbered list with detailed explanations.
                """
            else:
                analysis_prompt = f"""
                Extract {max_key_points} key findings from the transcript.
                Each finding should be a clear, concise statement.
                Format as a numbered list.
                """
            
            key_findings = await llm.generate_str(message=analysis_prompt)
            
            # Step 4: Generate comprehensive report
            logger.info("Step 4: Generating comprehensive report...")
            report_prompt = f"""
            Create a comprehensive video analysis report with the following structure:
            
            # Video Analysis Report
            
            **Video URL**: {video_url}
            **Video ID**: {video_id}
            
            ## Video Information
            {metadata_result}
            
            ## Executive Summary
            [Write a 2-3 sentence executive summary of the video's main message]
            
            ## Key Findings (Detailed Analysis)
            {key_findings}
            
            ## Transcript Analysis
            - Transcript Length: [state the length]
            - Language: English
            - Quality: [assess transcript quality]
            
            ## Detailed Insights
            [Provide 3-5 paragraphs of detailed analysis connecting the key findings
             and explaining the overall significance of the content]
            
            ## Conclusions
            [Summarize the main takeaways and potential applications]
            
            ## Source
            **Video Link**: [{video_url}]({video_url})
            
            ---
            *Analysis Date: 2025-11-14*
            *Analysis Depth: {analysis_depth}*
            *Key Findings Extracted: {max_key_points}*
            
            Ensure all sections are filled out comprehensively with specific details from the video.
            """
            
            final_report = await llm.generate_str(message=report_prompt)
            
            logger.info("Analysis complete!")
            return final_report


def _extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If just the ID is provided
    if len(url) == 11 and url.replace('-', '').replace('_', '').isalnum():
        return url
    
    return None


async def _get_video_metadata(video_id: str) -> str:
    """Get YouTube video metadata using the YouTube Data API"""
    import os
    from googleapiclient.discovery import build
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return "Error: YOUTUBE_API_KEY not configured"
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            return f"Error: No video found with ID: {video_id}"
        
        video = response['items'][0]
        snippet = video['snippet']
        statistics = video.get('statistics', {})
        content_details = video.get('contentDetails', {})
        
        metadata = f"""
**Title**: {snippet['title']}
**Channel**: {snippet['channelTitle']}
**Published**: {snippet['publishedAt']}
**Duration**: {content_details.get('duration', 'Unknown')}
**Views**: {statistics.get('viewCount', 'N/A')}
**Likes**: {statistics.get('likeCount', 'N/A')}
**Comments**: {statistics.get('commentCount', 'N/A')}

**Description**:
{snippet['description'][:500]}...
"""
        return metadata
    except Exception as e:
        return f"Error retrieving metadata: {str(e)}"


async def _get_video_transcript(video_id: str) -> str:
    """Get YouTube video transcript"""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en'])
        except NoTranscriptFound:
            # Get first available transcript
            available = list(transcript_list)
            if not available:
                return "Error: No transcript available for this video"
            transcript = available[0]
        
        transcript_data = transcript.fetch()
        full_text = ' '.join([entry['text'] for entry in transcript_data])
        
        return f"""**Transcript** (Language: {transcript.language}, Length: {len(full_text)} characters):

{full_text}"""
    except TranscriptsDisabled:
        return "Error: Transcripts are disabled for this video"
    except NoTranscriptFound:
        return "Error: No transcript found for this video"
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"


async def _extract_key_findings(transcript: str, max_points: int = 15) -> str:
    """Extract key findings from transcript using OpenAI"""
    import os
    from openai import AsyncOpenAI
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not configured"
    
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing content and extracting key points."},
                {"role": "user", "content": f"""Analyze the following transcript and extract the {max_points} most important key points.

Each key point should be:
- Clear and concise (1-2 sentences max)
- Capture a distinct idea or fact
- Be actionable or informative

Transcript:
{transcript[:15000]}  # Limit to avoid token limits

Return as a numbered list."""}
            ],
            temperature=0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error extracting key points: {str(e)}"


# Export the tool for use in MCP server
__all__ = ['analyze_youtube_video', 'app']


if __name__ == "__main__":
    # Test the agent directly
    async def test():
        result = await analyze_youtube_video(
            video_url="https://www.youtube.com/watch?v=SJi469BuU6g",
            max_key_points=15,
            analysis_depth="detailed"
        )
        print(result)
    
    asyncio.run(test())
