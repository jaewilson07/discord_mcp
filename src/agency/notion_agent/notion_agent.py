from agency_swarm import Agent
from pathlib import Path

# Initialize the Notion agent
notion_agent = Agent(
    name="NotionAgent",
    description="An agent that can interact with Notion workspace using the Notion API. Can search pages, create/update pages, query databases, and add comments.",
    instructions=Path(__file__).parent / "instructions.md",
    tools_folder=Path(__file__).parent / "tools",
    temperature=0.5,
    max_prompt_tokens=25000,
    model="gpt-4o",
)
