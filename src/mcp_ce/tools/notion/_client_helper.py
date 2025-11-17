"""Helper to get Notion client for tool execution."""

import os
from typing import Optional
from notion_client import AsyncClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Singleton client instance
_client_instance: Optional[AsyncClient] = None


def get_client() -> AsyncClient:
    """
    Get or create the Notion AsyncClient instance.
    
    The client is initialized with NOTION_TOKEN from environment variables.
    This is a singleton pattern - the same client is reused across calls.
    
    Returns:
        AsyncClient: The Notion async client instance
        
    Raises:
        RuntimeError: If NOTION_TOKEN is not configured
    """
    global _client_instance
    
    if _client_instance is None:
        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            raise RuntimeError(
                "NOTION_TOKEN not configured. "
                "Please set NOTION_TOKEN in your .env file."
            )
        
        _client_instance = AsyncClient(auth=notion_token)
    
    return _client_instance


def set_client(client: AsyncClient) -> None:
    """
    Set the Notion client instance (for testing or custom initialization).
    
    Args:
        client: The Notion AsyncClient instance
    """
    global _client_instance
    _client_instance = client


def is_client_ready() -> bool:
    """Check if client is initialized."""
    return _client_instance is not None


async def get_data_source_id_from_database(database_id: str) -> str:
    """
    Get the data_source_id from a database_id.
    
    As of Notion API 2025-09-03 update, database_id and data_source_id 
    are not synonymous. This helper retrieves the data_source_id needed
    for querying.
    
    Args:
        database_id: The Notion database ID
        
    Returns:
        str: The data source ID for the database
        
    Raises:
        RuntimeError: If client is not initialized
        Exception: If the database cannot be accessed
    """
    client = get_client()
    
    response = await client.request(
        path=f'databases/{database_id}',
        method='GET'
    )
    
    return response['data_sources'][0]['id']


async def query_data_source(data_source_id: str, filter_obj: dict = None, sorts: list = None) -> dict:
    """
    Query a Notion data source (database).
    
    Args:
        data_source_id: The data source ID to query
        filter_obj: Optional filter object (Notion API filter format)
        sorts: Optional list of sort objects
        
    Returns:
        dict: The query response containing 'results' and pagination info
        
    Raises:
        RuntimeError: If client is not initialized
    """
    client = get_client()
    
    body = {}
    if filter_obj:
        body['filter'] = filter_obj
    if sorts:
        body['sorts'] = sorts
    
    return await client.request(
        path=f'data_sources/{data_source_id}/query',
        method='POST',
        body=body
    )


async def create_page(parent_database_id: str, properties: dict, children: list = None) -> dict:
    """
    Create a new page in a Notion database.
    
    Args:
        parent_database_id: The database ID to create the page in
        properties: Page properties (title, URL, etc.)
        children: Optional list of block objects for page content
        
    Returns:
        dict: The created page object
        
    Raises:
        RuntimeError: If client is not initialized
    """
    client = get_client()
    
    body = {
        "parent": {"database_id": parent_database_id},
        "properties": properties
    }
    
    if children:
        body['children'] = children
    
    return await client.request(
        path='pages',
        method='POST',
        body=body
    )


async def update_page(page_id: str, properties: dict = None) -> dict:
    """
    Update a Notion page's properties.
    
    Args:
        page_id: The page ID to update
        properties: Properties to update
        
    Returns:
        dict: The updated page object
        
    Raises:
        RuntimeError: If client is not initialized
    """
    client = get_client()
    
    body = {}
    if properties:
        body['properties'] = properties
    
    return await client.request(
        path=f'pages/{page_id}',
        method='PATCH',
        body=body
    )


async def append_blocks(page_id: str, children: list) -> dict:
    """
    Append blocks to a page.
    
    Args:
        page_id: The page ID to append blocks to
        children: List of block objects to append
        
    Returns:
        dict: Response with appended blocks
        
    Raises:
        RuntimeError: If client is not initialized
    """
    client = get_client()
    
    return await client.request(
        path=f'blocks/{page_id}/children',
        method='PATCH',
        body={'children': children}
    )


async def delete_all_blocks(page_id: str) -> None:
    """
    Delete all child blocks from a page.
    
    Args:
        page_id: The page ID to delete blocks from
        
    Raises:
        RuntimeError: If client is not initialized
    """
    client = get_client()
    
    # Get all child blocks
    blocks_response = await client.request(
        path=f'blocks/{page_id}/children',
        method='GET'
    )
    
    # Delete each block
    for block in blocks_response.get('results', []):
        try:
            await client.request(
                path=f'blocks/{block["id"]}',
                method='DELETE'
            )
        except Exception:
            # Some blocks might not be deletable, skip them
            pass
