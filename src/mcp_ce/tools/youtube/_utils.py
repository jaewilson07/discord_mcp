"""
Shared YouTube utility functions used across YouTube tools.
"""

import re
from typing import Optional


def extract_video_id(input_str: str) -> Optional[str]:
    """
    Extracts 11-character video ID from various YouTube URL formats or direct ID.
    
    Args:
        input_str: YouTube URL or video ID
        
    Returns:
        11-character video ID or None if invalid
    """
    input_str = input_str.strip()

    # Check if it's already a valid 11-character ID
    if len(input_str) == 11 and input_str.replace('-', '').replace('_', '').isalnum():
        return input_str

    # Try various URL patterns
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    return None
