from agency_swarm import Agent


crawl4ai_agent = Agent(
    name="Crawl4AIAgent",
    description="An intelligent web crawling and article extraction agent powered by Crawl4AI. Specializes in extracting structured content from websites and saving articles with rich metadata to local JSON files.",
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model="gpt-4o",
    max_tokens=25000,
)
