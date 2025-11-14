import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from agency.agency import create_agency
from agency.youtube_agency import create_agency as create_youtube_agency
from agency_swarm.integrations.fastapi import run_fastapi


def main():
    """Main entry point for FastAPI deployment of agencies."""
    run_fastapi(
        agencies={
            "example-agency": create_agency,
            "youtube-research": create_youtube_agency,
        },
        port=8080,
        enable_logging=True
    )


if __name__ == "__main__":
    main()

