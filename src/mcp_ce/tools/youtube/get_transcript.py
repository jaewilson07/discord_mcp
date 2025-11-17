"""YouTube transcript extraction tool for MCP code execution server.
Extracts the full transcript text from a YouTube video.
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from typing import Optional
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from ._utils import extract_video_id as _extract_video_id
from .models import Transcript


@register_command("youtube", "get_transcript")
@cache_tool(ttl=7200, id_param="video_id")  # Cache for 2 hours
async def get_transcript(
    video_id: str, languages: Optional[list] = None, override_cache: bool = False
) -> ToolResponse:
    """
    Extracts the full transcript text from a YouTube video using its video ID or URL.
    Retrieves auto-generated or manual captions.

    Args:
        video_id: YouTube video ID (11 characters) or full YouTube URL
        languages: Preferred transcript languages in priority order (e.g., ['en', 'es']), defaults to ['en']
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with Transcript dataclass containing:
            - video_id: YouTube video ID
            - transcript: Full transcript text
            - language: Language code of the transcript
            - length: Character count of transcript
            - is_auto_generated: Whether transcript is auto-generated
            - entries: List of transcript entries with timestamps
    """
    if languages is None:
        languages = ["en"]

    if not video_id.strip():
        return ToolResponse(
            is_success=False, result=None, error="video_id cannot be empty"
        )

    # Extract video ID from URL if needed
    extracted_id = _extract_video_id(video_id)

    if not extracted_id:
        return ToolResponse(
            is_success=False,
            result=None,
            error="Could not extract valid video ID from input",
        )

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(extracted_id)

        transcript = None
        try:
            transcript = transcript_list.find_transcript(languages)
        except NoTranscriptFound:
            # Try to get any available transcript
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    transcript = available_transcripts[0]
            except:
                pass

        if not transcript:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"No transcript available for video ID: {extracted_id}",
            )

        transcript_data = transcript.fetch()

        # Combine all transcript entries into full text
        full_text = " ".join([entry["text"] for entry in transcript_data])

        transcript_result = Transcript(
            video_id=extracted_id,
            transcript=full_text,
            language=transcript.language,
            length=len(full_text),
            is_auto_generated=transcript.is_generated,
            entries=transcript_data,
        )

        return ToolResponse(is_success=True, result=transcript_result, error=None)

    except TranscriptsDisabled:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Transcripts are disabled for video ID: {extracted_id}",
        )
    except NoTranscriptFound:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"No transcript found for video ID: {extracted_id}",
        )
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Error extracting transcript: {str(e)}",
        )


if __name__ == "__main__":
    import asyncio

    # Test the tool
    result = asyncio.run(get_transcript(video_id="dQw4w9WgXcQ"))
    if result.is_success:
        print(f"✅ Success!")
        print(f"Video ID: {result.result.video_id}")
        print(f"Language: {result.result.language}")
        print(f"Length: {result.result.length} characters")
        print(f"Auto-generated: {result.result.is_auto_generated}")
        print(f"Transcript preview: {result.result.transcript[:200]}...")
    else:
        print(f"❌ Error: {result.error}")
