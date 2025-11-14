from dotenv import load_dotenv
from agency_swarm import Agency

from .example_agent import example_agent
from .example_agent2 import example_agent2

import asyncio

load_dotenv()

def create_agency(load_threads_callback=None):
    agency = Agency(
        example_agent, example_agent2,
        communication_flows=[(example_agent, example_agent2)],
        name="ExampleAgency",
        shared_instructions="shared_instructions.md",
        load_threads_callback=load_threads_callback,
    )

    return agency


def main():
    """Main entry point for running Example Agency in terminal mode."""
    agency = create_agency()
    agency.terminal_demo()


if __name__ == "__main__":
    main()
