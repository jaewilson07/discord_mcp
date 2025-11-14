from agency_swarm import Agent

summarizer_agent = Agent(
    name="SummarizerAgent",
    description="Content Analyst responsible for processing video transcripts and extracting meaningful insights. Analyzes content, identifies key points, and creates concise summaries that preserve essential information.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-4o",
    max_tokens=16000,
)
