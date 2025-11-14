from dotenv import load_dotenv
from agency_swarm import Agency

from .youtube_agent import youtube_agent
from .summarizer_agent import summarizer_agent
from .research_coordinator import research_coordinator

load_dotenv()

def create_agency(load_threads_callback=None):
    agency = Agency(
        [
            research_coordinator,
            [research_coordinator, youtube_agent],
            [research_coordinator, summarizer_agent],
            [youtube_agent, summarizer_agent]
        ],
        shared_instructions="youtube_shared_instructions.md",
        name="YouTubeResearchAgency",
        load_threads_callback=load_threads_callback,
    )

    return agency


def main():
    """Main entry point for running YouTube Research Agency in terminal mode."""
    agency = create_agency()
    agency.terminal_demo()


if __name__ == "__main__":
    main()

