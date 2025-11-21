"""Helper to get Supabase client for tool execution."""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Singleton client instance
_client_instance: Optional[Client] = None


def get_client() -> Client:
    """
    Get or create the Supabase client instance.
    
    The client is initialized with SUPABASE_URL and SUPABASE_KEY from environment variables.
    This is a singleton pattern - the same client is reused across calls.
    
    Returns:
        Client: The Supabase client instance
        
    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_KEY are not configured
    """
    global _client_instance
    
    if _client_instance is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url:
            raise RuntimeError(
                "SUPABASE_URL not configured. "
                "Please set SUPABASE_URL in your .env file."
            )
        
        if not supabase_key:
            raise RuntimeError(
                "SUPABASE_KEY not configured. "
                "Please set SUPABASE_KEY in your .env file."
            )
        
        _client_instance = create_client(supabase_url, supabase_key)
    
    return _client_instance


def set_client(client: Client) -> None:
    """
    Set the Supabase client instance (for testing or custom initialization).
    
    Args:
        client: The Supabase client instance
    """
    global _client_instance
    _client_instance = client


def is_client_ready() -> bool:
    """Check if client is initialized."""
    return _client_instance is not None

