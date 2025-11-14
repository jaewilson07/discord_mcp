from agency_swarm import Agent
from openai.types.shared import Reasoning


example_agent = Agent(
    name="ExampleAgent",
    description="A helpful and knowledgeable assistant that provides comprehensive support and guidance across various domains.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-4o",
    max_tokens=25000,
)
