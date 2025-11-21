"""
YouTube Video Analysis MCP Agent

This agent orchestrates YouTube video analysis workflows using existing tools.
It does NOT duplicate tool logic - it USES the existing YouTube tools.
"""

import asyncio
import os
from typing import Optional
from pydantic import BaseModel, Field

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Import existing YouTube tools - NO DUPLICATION
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.youtube._utils import extract_video_id
from tools.youtube.get_video_metadata import get_video_metadata
from tools.youtube.get_transcript import get_transcript

# Import Pydantic models for consistency
from models.youtube import (
    VideoMetadata,
    VideoTranscript,
    VideoAnalysisSummary,
    VideoAnalysisReport,
    NotionExportRequest,
    NotionExportResult,
)

from dotenv import load_dotenv
load_dotenv()

# Create the MCP app
app = MCPApp(name="youtube_video_analyzer")


@app.tool
async def analyze_youtube_video(
    video_url: str,
    max_key_points: int = 15,
    analysis_depth: str = "detailed"
) -> str:
    """
    Analyze a YouTube video in great detail and extract key findings.
    
    This tool orchestrates the analysis workflow:
    1. Extract video ID
    2. Get metadata (using existing tool)
    3. Get transcript (using existing tool)
    4. Generate AI-powered summary
    5. Extract key findings
    6. Export to Notion (if configured)
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        max_key_points: Maximum number of key findings to extract (default: 15)
        analysis_depth: Level of analysis - 'summary' or 'detailed' (default: 'detailed')
    
    Returns:
        Comprehensive analysis report in markdown format with video link
    """
    async with app.run() as running_app:
        logger = running_app.logger
        
        # Extract video ID from URL using shared utility (no duplication!)
        video_id = extract_video_id(video_url)
        if not video_id:
            return f"Error: Could not extract video ID from URL: {video_url}"
        
        logger.info(f"Analyzing video", data={"video_id": video_id, "url": video_url})
        
        try:
            # Step 1: Get video metadata using existing tool (no duplication!)
            logger.info("Step 1: Getting video metadata...")
            metadata_dict = await get_video_metadata(video_id)
            
            if not metadata_dict.get("success"):
                return f"Error getting metadata: {metadata_dict.get('error', 'Unknown error')}"
            
            # Convert to Pydantic model for consistency
            # Convert view/like counts to int (YouTube API returns strings)
            def safe_int(value, default=0):
                try:
                    return int(value) if value and value != "N/A" else default
                except (ValueError, TypeError):
                    return default
            
            metadata = VideoMetadata(
                video_id=video_id,
                title=metadata_dict['title'],
                channel=metadata_dict['channel'],
                published_at=metadata_dict['published_at'],
                duration=metadata_dict['duration'],
                view_count=safe_int(metadata_dict.get('view_count')),
                like_count=safe_int(metadata_dict.get('like_count')),
                description=metadata_dict.get('description', '')
            )
            
            # Step 2: Get transcript using existing tool (no duplication!)
            logger.info("Step 2: Extracting transcript...")
            transcript_dict = await get_transcript(video_id)
            
            if not transcript_dict.get("success"):
                return f"Error getting transcript: {transcript_dict.get('error', 'Unknown error')}"
            
            # Convert to Pydantic model for consistency
            transcript = VideoTranscript(
                video_id=video_id,
                transcript=transcript_dict['transcript'],
                language=transcript_dict.get('language', 'Unknown')
            )
            
            # Step 3: Generate AI-powered analysis (returns Pydantic model)
            logger.info(f"Step 3: Extracting summary and {max_key_points} key findings...")
            analysis = await _generate_analysis(
                transcript=transcript.transcript,
                title=metadata.title,
                channel=metadata.channel,
                max_key_points=max_key_points,
                analysis_depth=analysis_depth
            )
            
            # Step 4: Build comprehensive report using Pydantic model
            logger.info("Step 4: Generating comprehensive report...")
            report = VideoAnalysisReport(
                video_url=video_url,
                video_id=video_id,
                metadata=metadata,
                transcript=transcript,
                analysis=analysis,
                analysis_depth=analysis_depth,
                max_key_points=max_key_points
            )
            
            # Step 5: Export to Notion if configured
            logger.info("Step 5: Exporting to Notion...")
            export_result = await _export_to_notion_with_models(report)
            
            if export_result.success:
                logger.info(f"Exported to Notion: {export_result.message}")
            else:
                logger.warning(f"Notion export: {export_result.message}")
            
            # Return markdown report with Notion status
            markdown_report = report.to_markdown()
            
            if export_result.success:
                markdown_report += f"\n\n✅ {export_result.message}"
            else:
                markdown_report += f"\n\n⚠️ {export_result.message}"
            
            logger.info("Analysis complete!")
            return markdown_report
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return f"Error analyzing video: {str(e)}"


# ===== AI-POWERED ANALYSIS FUNCTIONS (agent-specific logic) =====

async def _generate_analysis(
    transcript: str,
    title: str,
    channel: str,
    max_key_points: int = 15,
    analysis_depth: str = "detailed"
) -> VideoAnalysisSummary:
    """
    Generate AI-powered analysis from transcript using Pydantic model.
    
    Args:
        transcript: Full transcript text
        title: Video title
        channel: Channel name
        max_key_points: Maximum number of key findings to extract
        analysis_depth: 'summary' or 'detailed'
    
    Returns:
        VideoAnalysisSummary with summary text and key findings list
    """
    from openai import AsyncOpenAI
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return VideoAnalysisSummary(
            summary="Summary not available (OPENAI_API_KEY not configured)",
            key_findings=["Error: OPENAI_API_KEY not configured"],
            transcript_length=len(transcript)
        )
    
    client = AsyncOpenAI(api_key=api_key)
    
    prompt = f"""Analyze this YouTube video transcript and provide a {'comprehensive detailed' if analysis_depth == 'detailed' else 'concise'} summary.

Video Title: {title}
Channel: {channel}

Transcript:
{transcript[:10000]}  # Limit to ~10k chars for context

Please provide:
1. A comprehensive summary paragraph (3-5 sentences)
2. Exactly {max_key_points} key findings/insights as a numbered list

Format your response EXACTLY like this:

SUMMARY:
[Your summary paragraph here]

KEY FINDINGS:
1. [First finding]
2. [Second finding]
...
{max_key_points}. [Last finding]
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing video content and extracting key insights. Follow the format exactly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content
        
        # Parse the structured response
        lines = content.split('\n')
        summary_text = ""
        key_findings = []
        
        parsing_summary = False
        parsing_findings = False
        
        for line in lines:
            line = line.strip()
            
            if line == "SUMMARY:":
                parsing_summary = True
                parsing_findings = False
                continue
            elif line == "KEY FINDINGS:":
                parsing_summary = False
                parsing_findings = True
                continue
            
            if parsing_summary and line:
                summary_text += line + " "
            elif parsing_findings and line:
                # Extract numbered list items (e.g., "1. Finding text")
                import re
                match = re.match(r'^\d+\.\s*(.+)$', line)
                if match:
                    key_findings.append(match.group(1))
        
        summary_text = summary_text.strip()
        
        # Fallback if parsing failed
        if not summary_text:
            summary_text = content[:500]  # Use first 500 chars
        if not key_findings:
            key_findings = [f"Finding {i+1}: Analysis generated but could not be parsed" for i in range(min(5, max_key_points))]
        
        return VideoAnalysisSummary(
            summary=summary_text,
            key_findings=key_findings,
            transcript_length=len(transcript)
        )
        
    except Exception as e:
        # Return error in structured format
        return VideoAnalysisSummary(
            summary=f"Error generating summary: {str(e)}",
            key_findings=["Error: Could not generate key findings"],
            transcript_length=len(transcript)
        )


# ===== NOTION EXPORT FUNCTIONS (agent-specific integration) =====

async def _get_data_source_id(client: "AsyncClient", database_id: str) -> str:
    """
    Convert database_id to data_source_id for querying.
    As of 2025-09-03, database_id and data_source_id are not synonymous.
    """
    res = await client.request(
        path=f'databases/{database_id}',
        method='GET',
    )
    return res['data_sources'][0]['id']


async def _export_to_notion_with_models(report: VideoAnalysisReport) -> NotionExportResult:
    """
    Export video analysis to Notion database using Pydantic models.
    
    Args:
        report: VideoAnalysisReport containing all analysis data
    
    Returns:
        NotionExportResult with success/error status
    """
    import os
    from notion_client import AsyncClient
    from notion_blockify import Blockizer
    
    # Check for required environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_token or not notion_database_id:
        return NotionExportResult.skipped_result("Notion credentials not configured")
    
    try:
        notion = AsyncClient(auth=notion_token)
        blockizer = Blockizer()
        
        # Convert database_id to data_source_id for querying
        data_source_id = await _get_data_source_id(notion, notion_database_id)
        
        # Create export request from report
        export_request = NotionExportRequest.from_report(report)
        
        # Check for existing page with this video URL using data_source_id
        existing_pages = await notion.request(
            path=f'data_sources/{data_source_id}/query',
            method='POST',
            body={}
        )
        
        # Find matching page by URL
        matching_page = None
        for page in existing_pages.get("results", []):
            props = page.get('properties', {})
            for prop_name, prop_data in props.items():
                if prop_data.get('type') == 'url':
                    url_value = prop_data.get('url', '')
                    if url_value == report.video_url:
                        matching_page = page
                        break
            if matching_page:
                break
        
        if matching_page:
            # Update existing page
            page_id = matching_page["id"]
            
            # Archive all existing blocks
            existing_blocks = await notion.blocks.children.list(block_id=page_id)
            for block in existing_blocks.get("results", []):
                await notion.blocks.delete(block_id=block["id"])
            
            # Add new content
            content_markdown = export_request.get_page_content().to_markdown()
            blocks = blockizer.convert(content_markdown)
            await notion.blocks.children.append(block_id=page_id, children=blocks)
            
            # Update properties
            properties = export_request.get_page_properties().to_notion_properties()
            await notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            return NotionExportResult.success_result(page_id=page_id, is_update=True)
        
        # Create new page
        properties = export_request.get_page_properties().to_notion_properties()
        content_markdown = export_request.get_page_content().to_markdown()
        blocks = blockizer.convert(content_markdown)
        
        # Create the page using data_source_id as parent
        new_page = await notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": data_source_id},
            properties=properties,
            children=blocks[:100]  # Notion has a limit on initial blocks
        )
        
        return NotionExportResult.success_result(page_id=new_page['id'], is_update=False)
        
    except Exception as e:
        return NotionExportResult.error_result(str(e))


# Export the tool for use in MCP server
__all__ = ['analyze_youtube_video', 'app']


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with a sample video
        result = await analyze_youtube_video(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            max_key_points=10,
            analysis_depth="detailed"
        )
        print(result)
    
    asyncio.run(test())
