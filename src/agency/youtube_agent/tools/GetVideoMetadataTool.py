from agency_swarm.tools import BaseTool
from pydantic import Field
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import re

load_dotenv()

class GetVideoMetadataTool(BaseTool):
    """
    Retrieves detailed metadata for a specific YouTube video including title, description,
    duration, tags, channel info, and statistics.
    """
    
    video_id: str = Field(
        ...,
        description="YouTube video ID (11 characters) or full URL"
    )

    def run(self):
        """
        Retrieves and returns detailed video metadata.
        """
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return "Error: YOUTUBE_API_KEY not found in environment variables"
        
        if not self.video_id.strip():
            return "Error: video_id cannot be empty"
        
        video_id = self._extract_video_id(self.video_id)
        
        if not video_id or len(video_id) != 11:
            return "Error: Invalid video ID. Must be 11 characters"
        
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
            
            metadata = {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'channel': snippet['channelTitle'],
                'channel_id': snippet['channelId'],
                'published_at': snippet['publishedAt'],
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', 'Unknown'),
                'duration': content_details.get('duration', 'Unknown'),
                'view_count': statistics.get('viewCount', 'N/A'),
                'like_count': statistics.get('likeCount', 'N/A'),
                'comment_count': statistics.get('commentCount', 'N/A'),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
            result = f"Video Metadata for: {metadata['title']}\n\n"
            result += f"URL: {metadata['url']}\n"
            result += f"Channel: {metadata['channel']}\n"
            result += f"Published: {metadata['published_at']}\n"
            result += f"Duration: {metadata['duration']}\n"
            result += f"Views: {metadata['view_count']}\n"
            result += f"Likes: {metadata['like_count']}\n"
            result += f"Comments: {metadata['comment_count']}\n"
            
            if metadata['tags']:
                result += f"\nTags: {', '.join(metadata['tags'][:10])}\n"
            
            result += f"\nDescription:\n{metadata['description'][:500]}"
            if len(metadata['description']) > 500:
                result += "..."
            
            return result
            
        except Exception as e:
            return f"Error retrieving video metadata: {str(e)}"
    
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
    tool = GetVideoMetadataTool(video_id="dQw4w9WgXcQ")
    print(tool.run())
