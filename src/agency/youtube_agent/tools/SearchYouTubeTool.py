from agency_swarm.tools import BaseTool
from pydantic import Field
from googleapiclient.discovery import build
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class SearchYouTubeTool(BaseTool):
    """
    Searches YouTube for videos matching a topic or keywords. Returns video metadata 
    including IDs, titles, descriptions, URLs, and view counts.
    """
    
    query: str = Field(
        ...,
        description="Search query or topic to find videos about"
    )
    
    max_results: int = Field(
        default=5,
        description="Number of videos to return (1-50)",
        ge=1,
        le=50
    )
    
    order_by: str = Field(
        default="relevance",
        description="Sort order: 'relevance', 'date', 'viewCount', or 'rating'"
    )
    
    published_after: str = Field(
        default=None,
        description="ISO date string to filter videos published after this date (e.g., '2024-01-01T00:00:00Z')"
    )

    def run(self):
        """
        Executes YouTube search and returns video metadata.
        """
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return "Error: YOUTUBE_API_KEY not found in environment variables"
        
        if not self.query.strip():
            return "Error: Search query cannot be empty"
        
        if self.order_by not in ["relevance", "date", "viewCount", "rating"]:
            return f"Error: Invalid order_by value. Must be one of: relevance, date, viewCount, rating"
        
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            search_params = {
                'part': 'snippet',
                'q': self.query,
                'type': 'video',
                'order': self.order_by,
                'maxResults': self.max_results
            }
            
            if self.published_after:
                try:
                    datetime.fromisoformat(self.published_after.replace('Z', '+00:00'))
                    search_params['publishedAfter'] = self.published_after
                except ValueError:
                    return f"Error: Invalid date format for published_after. Use ISO format like '2024-01-01T00:00:00Z'"
            
            request = youtube.search().list(**search_params)
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                video_data = {
                    'id': video_id,
                    'title': snippet['title'],
                    'description': snippet['description'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt']
                }
                videos.append(video_data)
            
            if not videos:
                return f"No videos found for query: {self.query}"
            
            result = f"Found {len(videos)} video(s) for '{self.query}':\n\n"
            for i, video in enumerate(videos, 1):
                result += f"{i}. {video['title']}\n"
                result += f"   Channel: {video['channel']}\n"
                result += f"   URL: {video['url']}\n"
                result += f"   ID: {video['id']}\n"
                result += f"   Published: {video['published_at']}\n"
                result += f"   Description: {video['description'][:200]}...\n\n"
            
            return result
            
        except Exception as e:
            return f"Error searching YouTube: {str(e)}"


if __name__ == "__main__":
    tool = SearchYouTubeTool(query="LangChain tutorial", max_results=3)
    print(tool.run())
