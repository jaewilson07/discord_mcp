from agency_swarm import Agent

research_coordinator = Agent(
    name="ResearchCoordinator",
    description="Research Project Manager who orchestrates the entire research process from planning through final report delivery. Designs research methodology, coordinates specialists, synthesizes findings, and produces comprehensive reports. Primary agent for user interaction.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-4o",
    max_tokens=25000,
)
