from agency_swarm import Agent

youtube_agent = Agent(
    name="YouTubeAgent",
    description="Video Content Specialist responsible for discovering, accessing, and extracting content from YouTube videos. Searches YouTube's catalog, retrieves video information, and extracts transcripts for analysis.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-4o",
    max_tokens=16000,
)
