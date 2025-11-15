"""
YouTube transcript extraction tool for MCP code execution server.
Extracts the full transcript text from a YouTube video.
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
from typing import Dict, Any


async def get_transcript(video_id: str, languages: list = None) -> Dict[str, Any]:
    """
    Extracts the full transcript text from a YouTube video using its video ID or URL.
    Retrieves auto-generated or manual captions.

    Args:
        video_id: YouTube video ID (11 characters) or full YouTube URL
        languages: Preferred transcript languages in priority order (e.g., ['en', 'es']), defaults to ['en']

    Returns:
        dict with:
            - success: bool
            - video_id: str
            - transcript: full transcript text
            - language: language code of the transcript
            - length: character count
            - error: error message (if failed)
    """
    if languages is None:
        languages = ["en"]

    if not video_id.strip():
        return {"success": False, "error": "video_id cannot be empty"}

    # Extract video ID from URL if needed
    extracted_id = _extract_video_id(video_id)

    if not extracted_id:
        return {
            "success": False,
            "error": "Could not extract valid video ID from input",
        }

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
            return {
                "success": False,
                "error": f"No transcript available for video ID: {extracted_id}",
            }

        transcript_data = transcript.fetch()

        # Combine all transcript entries into full text
        full_text = " ".join([entry["text"] for entry in transcript_data])

        return {
            "success": True,
            "video_id": extracted_id,
            "transcript": full_text,
            "language": transcript.language,
            "length": len(full_text),
        }

    except TranscriptsDisabled:
        return {
            "success": False,
            "error": f"Transcripts are disabled for video ID: {extracted_id}",
        }
    except NoTranscriptFound:
        return {
            "success": False,
            "error": f"No transcript found for video ID: {extracted_id}",
        }
    except Exception as e:
        return {"success": False, "error": f"Error extracting transcript: {str(e)}"}


def _extract_video_id(input_str: str) -> str:
    """
    Extracts 11-character video ID from various YouTube URL formats or direct ID.
    """
    input_str = input_str.strip()

    # Check if it's already a valid 11-character ID
    if len(input_str) == 11 and input_str.isalnum():
        return input_str

    # Try various URL patterns
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    return None


if __name__ == "__main__":
    import asyncio
    import json

    # Test the tool
    result = asyncio.run(get_transcript(video_id="dQw4w9WgXcQ"))
    print(json.dumps(result, indent=2))
