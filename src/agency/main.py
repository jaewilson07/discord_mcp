import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

from .agency import create_agency
from agency_swarm.integrations.fastapi import run_fastapi


if __name__ == "__main__":
    run_fastapi(
        agencies={
            "my-agency": create_agency,
        },
        port=8080,
        enable_logging=True
    )
