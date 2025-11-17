"""
Pydantic models for YouTube video analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class VideoMetadata(BaseModel):
    """YouTube video metadata"""

    video_id: str
    title: str
    channel: str
    published_at: str
    duration: str
    view_count: int  # Changed to int for proper type
    like_count: int  # Changed to int for proper type
    description: Optional[str] = None


class VideoTranscript(BaseModel):
    """YouTube video transcript"""

    video_id: str
    transcript: str
    language: str = "en"


class VideoAnalysisSummary(BaseModel):
    """AI-generated summary of video content"""

    summary: str = Field(description="2-3 paragraph summary of video content")
    key_findings: List[str] = Field(description="List of key findings/takeaways")
    transcript_length: int = Field(description="Length of transcript in characters")


class VideoAnalysisReport(BaseModel):
    """Complete video analysis report"""

    video_url: str
    video_id: str
    metadata: VideoMetadata
    transcript: VideoTranscript
    analysis: VideoAnalysisSummary
    analysis_depth: str = "detailed"
    max_key_points: int = 15

    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        return f"""# Video Analysis Report

**Video URL**: {self.video_url}
**Video ID**: {self.video_id}

## Summary
{self.analysis.summary}

## Video Information
**Title**: {self.metadata.title}
**Channel**: {self.metadata.channel}
**Published**: {self.metadata.published_at}
**Duration**: {self.metadata.duration}
**Views**: {self.metadata.view_count}
**Likes**: {self.metadata.like_count}

## Key Findings ({self.analysis_depth.title()} Analysis)
{self._format_key_findings()}

## Transcript Summary
- Transcript Length: {self.analysis.transcript_length} characters
- Language: {self.transcript.language}
- Analysis Depth: {self.analysis_depth}
- Key Points Extracted: {self.max_key_points}

## Source
**Video Link**: [{self.video_url}]({self.video_url})

---
*Analysis completed successfully*
"""

    def _format_key_findings(self) -> str:
        """Format key findings as numbered list"""
        if isinstance(self.analysis.key_findings, list):
            return "\n".join(
                f"{i+1}. {finding}"
                for i, finding in enumerate(self.analysis.key_findings)
            )
        return self.analysis.key_findings
