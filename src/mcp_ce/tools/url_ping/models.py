"""URL Ping result models."""

from dataclasses import dataclass, field
from typing import Dict
from ..model import ToolResult


@dataclass
class PingResult(ToolResult):
    """
    Result from pinging a URL.

    Attributes:
        url: The URL that was pinged
        status_code: HTTP status code (e.g., 200, 404, 500)
        status_text: HTTP status text (e.g., "OK", "Not Found")
        response_time_seconds: Time taken for the request in seconds
        headers: Dictionary of response headers
    """

    url: str
    status_code: int
    status_text: str
    response_time_seconds: float
    headers: Dict[str, str] = field(default_factory=dict)
