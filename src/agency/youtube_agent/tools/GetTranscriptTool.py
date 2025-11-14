from agency_swarm.tools import BaseTool
from pydantic import Field
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re

class GetTranscriptTool(BaseTool):
    """
    Extracts the full transcript text from a YouTube video using its video ID or URL.
    Retrieves auto-generated or manual captions.
    """
    
    video_id: str = Field(
        ...,
        description="YouTube video ID (11 characters) or full YouTube URL"
    )
    
    languages: list = Field(
        default=["en"],
        description="Preferred transcript languages in priority order (e.g., ['en', 'es'])"
    )

    def run(self):
        """
        Extracts and returns the full transcript from a YouTube video.
        """
        if not self.video_id.strip():
            return "Error: video_id cannot be empty"
        
        video_id = self._extract_video_id(self.video_id)
        
        if not video_id:
            return "Error: Could not extract valid video ID from input"
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            try:
                transcript = transcript_list.find_transcript(self.languages)
            except NoTranscriptFound:
                try:
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0]
                except:
                    pass
            
            if not transcript:
                return f"Error: No transcript available for video ID: {video_id}"
            
            transcript_data = transcript.fetch()
            
            full_text = ' '.join([entry['text'] for entry in transcript_data])
            
            result = f"Transcript for video ID: {video_id}\n"
            result += f"Language: {transcript.language}\n"
            result += f"Length: {len(full_text)} characters\n\n"
            result += f"Transcript:\n{full_text}"
            
            return result
            
        except TranscriptsDisabled:
            return f"Error: Transcripts are disabled for video ID: {video_id}"
        except NoTranscriptFound:
            return f"Error: No transcript found for video ID: {video_id}"
        except Exception as e:
            return f"Error extracting transcript: {str(e)}"
    
    def _extract_video_id(self, input_str: str) -> str:
        """
        Extracts 11-character video ID from various YouTube URL formats or direct ID.
        """
        input_str = input_str.strip()
        
        if len(input_str) == 11 and input_str.isalnum():
            return input_str
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)
        
        return None


if __name__ == "__main__":
    tool = GetTranscriptTool(video_id="dQw4w9WgXcQ")
    print(tool.run())
