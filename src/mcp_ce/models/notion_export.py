class NotionPageProperties(BaseModel):
    """Properties for a Notion page"""

    title: str = Field(max_length=2000)
    url: str
    video_id: str
    analysis_depth: str
    key_points: int

    def to_notion_properties(self) -> Dict[str, Any]:
        """Convert to Notion API format"""
        return {
            "Name": {"title": [{"text": {"content": self.title}}]},
            "URL": {"url": self.url},
            "Video ID": {"rich_text": [{"text": {"content": self.video_id}}]},
            "Analysis Depth": {"select": {"name": self.analysis_depth.title()}},
            "Key Points": {"number": self.key_points},
        }


class NotionPageContent(BaseModel):
    """Content for a Notion page"""

    metadata: str
    summary: str
    key_findings: str
    transcript: str
    max_transcript_length: int = 15000

    def to_markdown(self) -> str:
        """Convert to markdown for Notion blockizer"""
        return f"""# Video Analysis

{self.metadata}

## Summary
{self.summary}

## Key Findings
{self.key_findings}

## Full Transcript
{self.transcript[:self.max_transcript_length]}
"""


class NotionExportRequest(BaseModel):
    """Request to export analysis to Notion"""

    video_url: str
    video_id: str
    summary: str
    metadata: str
    key_findings: str
    transcript: str
    analysis_depth: str
    max_key_points: int

    @classmethod
    def from_report(cls, report: VideoAnalysisReport) -> "NotionExportRequest":
        """Create from VideoAnalysisReport"""
        metadata_text = f"""**Title**: {report.metadata.title}
**Channel**: {report.metadata.channel}
**Published**: {report.metadata.published_at}
**Duration**: {report.metadata.duration}
**Views**: {report.metadata.view_count}
**Likes**: {report.metadata.like_count}"""

        key_findings_text = report._format_key_findings()

        return cls(
            video_url=report.video_url,
            video_id=report.video_id,
            summary=report.analysis.summary,
            metadata=metadata_text,
            key_findings=key_findings_text,
            transcript=report.transcript.transcript,
            analysis_depth=report.analysis_depth,
            max_key_points=report.max_key_points,
        )

    def get_page_properties(self) -> NotionPageProperties:
        """Get Notion page properties"""
        # Extract title from metadata
        title_line = [
            line for line in self.metadata.split("\n") if line.startswith("**Title**:")
        ]
        title = (
            title_line[0].replace("**Title**: ", "").strip()
            if title_line
            else f"Video Analysis: {self.video_id}"
        )

        return NotionPageProperties(
            title=title,
            url=self.video_url,
            video_id=self.video_id,
            analysis_depth=self.analysis_depth,
            key_points=self.max_key_points,
        )

    def get_page_content(self) -> NotionPageContent:
        """Get Notion page content"""
        return NotionPageContent(
            metadata=self.metadata,
            summary=self.summary,
            key_findings=self.key_findings,
            transcript=self.transcript,
        )


class NotionExportResult(BaseModel):
    """Result of Notion export operation"""

    success: bool
    message: str
    page_id: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def success_result(
        cls, page_id: str, is_update: bool = False
    ) -> "NotionExportResult":
        """Create success result"""
        action = "Updated" if is_update else "Exported to"
        return cls(
            success=True,
            message=f"Success: {action} Notion page (ID: {page_id})",
            page_id=page_id,
        )

    @classmethod
    def error_result(cls, error: str) -> "NotionExportResult":
        """Create error result"""
        return cls(
            success=False,
            message=f"Error: {error}",
            error=error,
        )

    @classmethod
    def skipped_result(
        cls, reason: str = "credentials not configured"
    ) -> "NotionExportResult":
        """Create skipped result"""
        return cls(
            success=False,
            message=f"Notion export skipped ({reason})",
            error=reason,
        )
