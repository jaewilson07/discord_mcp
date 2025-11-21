"""
Runtime helpers for zero-context discovery pattern.

These helpers are injected into the Python sandbox and allow the LLM to:
1. Discover available MCP servers (without loading schemas)
2. Query tool documentation on-demand
3. Search for tools across servers
4. Execute tools via proxies

This follows elusznik's zero-context discovery pattern:
~200 tokens overhead regardless of server count.
"""

import json
from typing import Optional, List, Dict, Any


# Registry of available MCP servers
_SERVERS_REGISTRY = {
    "url_ping": {
        "name": "url_ping",
        "description": "MCP server for pinging URLs and checking their availability",
        "module": "src.mcp_ce.tools.url_ping.ping_url",
        "tools": ["ping_url"],
    },
    "youtube": {
        "name": "youtube",
        "description": "MCP server for YouTube video search, transcripts, metadata, and research planning",
        "module": "src.mcp_ce.tools.youtube",
        "tools": [
            "search_youtube",
            "get_transcript",
            "get_video_metadata",
            "create_youtube_research_plan",
        ],
    },
    "notion": {
        "name": "notion",
        "description": "MCP server for Notion workspace integration (search, pages, databases, comments)",
        "module": "src.mcp_ce.tools.notion",
        "tools": [
            "search_notion",
            "get_notion_page",
            "create_notion_page",
            "update_notion_page",
            "query_notion_database",
            "add_notion_comment",
        ],
    },
    "crawl4ai": {
        "name": "crawl4ai",
        "description": "MCP server for web scraping and article extraction",
        "module": "src.mcp_ce.tools.crawl4ai",
        "tools": ["crawl_website", "save_article", "chunk_markdown", "extract_code_blocks"],
    },
    "discord": {
        "name": "discord",
        "description": "MCP server for Discord bot operations (servers, messages, roles, channels, events)",
        "module": "src.mcp_ce.tools.discord",
        "tools": [
            "get_server_info",
            "get_channels",
            "list_members",
            "list_servers",
            "get_user_info",
            "send_message",
            "read_messages",
            "add_reaction",
            "add_multiple_reactions",
            "remove_reaction",
            "moderate_message",
            "add_role",
            "remove_role",
            "create_text_channel",
            "upsert_text_channel",
            "delete_channel",
            "create_category",
            "move_channel",
            "create_scheduled_event",
            "edit_scheduled_event",
            "send_message_with_image",
            "repost_tumblr",
        ],
    },
    "supabase": {
        "name": "supabase",
        "description": "MCP server for Supabase document storage, retrieval, and search (for crawl4ai scraped content)",
        "module": "src.mcp_ce.tools.supabase",
        "tools": [
            "add_document",
            "get_document",
            "search_documents",
            "get_available_sources",
            "perform_rag_query",
            "add_code_example",
            "search_code_examples",
            "check_tumblr_post_duplicate",
            "store_tumblr_post_url",
        ],
    },
    "agents": {
        "name": "agents",
        "description": "MCP server for AI agents (scraper, extraction, validation, code summarizer) using Pydantic-AI with Logfire integration",
        "module": "src.mcp_ce.tools.agents",
        "tools": [
            "scraper_agent",
            "extraction_agent",
            "validation_agent",
            "code_summarizer",
        ],
    },
    "tumblr": {
        "name": "tumblr",
        "description": "MCP server for Tumblr blog operations (extracting post URLs from feeds)",
        "module": "src.mcp_ce.tools.tumblr",
        "tools": ["extract_post_urls"],
    },
}


def discovered_servers() -> List[Dict[str, str]]:
    """
    Discover available MCP servers without loading their schemas.

    Returns:
        List of server dictionaries with 'name' and 'description'.
        Does NOT include tool schemas - use query_tool_docs() for that.

    Example:
        >>> servers = discovered_servers()
        >>> for server in servers:
        ...     print(f"{server['name']}: {server['description']}")
    """
    return [
        {"name": name, "description": info["description"]}
        for name, info in _SERVERS_REGISTRY.items()
    ]


def list_servers() -> List[str]:
    """
    List names of all available MCP servers.

    Returns:
        List of server names as strings.

    Example:
        >>> servers = list_servers()
        >>> print(servers)
        ['url_ping']
    """
    return list(_SERVERS_REGISTRY.keys())


# Synchronous version (alias)
def list_servers_sync() -> List[str]:
    """Synchronous version of list_servers()"""
    return list_servers()


def query_tool_docs(
    server_name: str, tool: Optional[str] = None, detail: str = "summary"
) -> str:
    """
    Query documentation for tools in a specific server.
    Load schemas on-demand (zero-context discovery).

    Args:
        server_name: Name of the MCP server (from discovered_servers)
        tool: Specific tool name (None for all tools)
        detail: Level of detail - "summary" or "full"

    Returns:
        JSON string with tool documentation

    Example:
        >>> docs = query_tool_docs("url_ping")
        >>> print(docs)
        {"tools": [{"name": "ping_url", ...}]}

        >>> docs = query_tool_docs("url_ping", tool="ping_url", detail="full")
    """
    if server_name not in _SERVERS_REGISTRY:
        return json.dumps({"error": f"Server '{server_name}' not found"})

    server_info = _SERVERS_REGISTRY[server_name]

    # Load tool documentation on-demand
    tools_docs = {}

    if server_name == "url_ping":
        tools_docs = {
            "ping_url": {
                "name": "ping_url",
                "description": "Ping a URL and return the response status, timing, and headers",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "The URL to ping (must include protocol, e.g., https://example.com)",
                        "required": True,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds (default: 10)",
                        "required": False,
                        "default": 10,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "status_code": "integer (HTTP status)",
                        "response_time_seconds": "float",
                        "headers": "dict",
                        "error": "string (if failed)",
                    },
                },
            }
        }

    elif server_name == "youtube":
        tools_docs = {
            "search_youtube": {
                "name": "search_youtube",
                "description": "Search YouTube videos by query and return video details including titles, descriptions, and URLs",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query for YouTube videos",
                        "required": True,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, max: 50)",
                        "required": False,
                        "default": 10,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "videos": "list of dicts with keys: video_id, title, description, channel_title, published_at, url",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_transcript": {
                "name": "get_transcript",
                "description": "Retrieve the transcript/captions for a YouTube video",
                "parameters": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID (11 characters)",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "transcript": "string (full transcript text)",
                        "video_id": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_video_metadata": {
                "name": "get_video_metadata",
                "description": "Retrieve detailed metadata for a YouTube video including statistics and content details",
                "parameters": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID (11 characters)",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "metadata": "dict with keys: title, description, channel_title, published_at, duration, view_count, like_count, comment_count, tags",
                        "video_id": "string",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "notion":
        tools_docs = {
            "search_notion": {
                "name": "search_notion",
                "description": "Search for pages and databases in Notion workspace",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query text",
                        "required": True,
                    },
                    "filter_type": {
                        "type": "string",
                        "description": "Type filter: 'page', 'database', or 'all' (default: 'all')",
                        "required": False,
                        "default": "all",
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "results": "list of dicts with keys: id, title, type, url",
                        "count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_notion_page": {
                "name": "get_notion_page",
                "description": "Retrieve full details of a Notion page by ID",
                "parameters": {
                    "page_id": {
                        "type": "string",
                        "description": "Notion page ID (UUID or short ID)",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "page": "dict with keys: id, created_time, last_edited_time, properties, parent",
                        "error": "string (if failed)",
                    },
                },
            },
            "create_notion_page": {
                "name": "create_notion_page",
                "description": "Create a new page in Notion workspace",
                "parameters": {
                    "title": {
                        "type": "string",
                        "description": "Page title",
                        "required": True,
                    },
                    "parent_page_id": {
                        "type": "string",
                        "description": "Parent page ID (optional, creates in workspace root if omitted)",
                        "required": False,
                        "default": None,
                    },
                    "content": {
                        "type": "string",
                        "description": "Page content text (optional)",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "page_id": "string",
                        "url": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "update_notion_page": {
                "name": "update_notion_page",
                "description": "Update properties of an existing Notion page",
                "parameters": {
                    "page_id": {
                        "type": "string",
                        "description": "Notion page ID to update",
                        "required": True,
                    },
                    "properties": {
                        "type": "string or dict",
                        "description": "JSON string or dict with property updates",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "page_id": "string",
                        "updated_properties": "list of property names",
                        "error": "string (if failed)",
                    },
                },
            },
            "query_notion_database": {
                "name": "query_notion_database",
                "description": "Query a Notion database with optional filters and sorts",
                "parameters": {
                    "database_id": {
                        "type": "string",
                        "description": "Notion database ID",
                        "required": True,
                    },
                    "filter_json": {
                        "type": "string",
                        "description": "Optional filter JSON string",
                        "required": False,
                        "default": None,
                    },
                    "sorts_json": {
                        "type": "string",
                        "description": "Optional sorts JSON string",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "results": "list of page objects",
                        "count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "add_notion_comment": {
                "name": "add_notion_comment",
                "description": "Add a comment to a Notion page",
                "parameters": {
                    "page_id": {
                        "type": "string",
                        "description": "Notion page ID",
                        "required": True,
                    },
                    "comment_text": {
                        "type": "string",
                        "description": "Comment text content",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "comment_id": "string",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "crawl4ai":
        tools_docs = {
            "crawl_website": {
                "name": "crawl_website",
                "description": "Extract content from a website including markdown, images, and links",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to crawl",
                        "required": True,
                    },
                    "extract_images": {
                        "type": "boolean",
                        "description": "Extract image URLs (default: True)",
                        "required": False,
                        "default": True,
                    },
                    "extract_links": {
                        "type": "boolean",
                        "description": "Extract hyperlinks (default: True)",
                        "required": False,
                        "default": True,
                    },
                    "word_count_threshold": {
                        "type": "integer",
                        "description": "Minimum words per content block (default: 10)",
                        "required": False,
                        "default": 10,
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "Run browser in headless mode (default: True)",
                        "required": False,
                        "default": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "url": "string",
                        "title": "string",
                        "content": "dict with keys: markdown, markdown_length",
                        "images": "list of image URLs",
                        "links": "list of link URLs",
                        "error": "string (if failed)",
                    },
                },
            },
            "save_article": {
                "name": "save_article",
                "description": "Save extracted article content to JSON file with metadata",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "Article source URL",
                        "required": True,
                    },
                    "title": {
                        "type": "string",
                        "description": "Article title",
                        "required": True,
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content (markdown or text)",
                        "required": True,
                    },
                    "description": {
                        "type": "string",
                        "description": "Article description (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "author": {
                        "type": "string",
                        "description": "Article author (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "published_date": {
                        "type": "string",
                        "description": "Publication date (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "keywords": {
                        "type": "list",
                        "description": "List of keywords (optional)",
                        "required": False,
                        "default": None,
                    },
                    "images": {
                        "type": "list",
                        "description": "List of image URLs (optional)",
                        "required": False,
                        "default": None,
                    },
                    "links": {
                        "type": "list",
                        "description": "List of links (optional)",
                        "required": False,
                        "default": None,
                    },
                    "custom_filename": {
                        "type": "string",
                        "description": "Custom filename (optional)",
                        "required": False,
                        "default": None,
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory path (default: './articles')",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "filepath": "string (full path)",
                        "filename": "string",
                        "article_id": "string (unique ID)",
                        "content_length": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "summarizer":
        tools_docs = {
            "summarize_transcript": {
                "name": "summarize_transcript",
                "description": "Generate AI-powered summary of video transcript using LangChain and GPT-3.5",
                "parameters": {
                    "transcript": {
                        "type": "string",
                        "description": "Video transcript text",
                        "required": True,
                    },
                    "video_title": {
                        "type": "string",
                        "description": "Video title for context",
                        "required": True,
                    },
                    "summary_length": {
                        "type": "string",
                        "description": "Length: 'short' (2-3 sentences), 'medium' (1 paragraph), 'long' (multiple paragraphs). Default: 'medium'",
                        "required": False,
                        "default": "medium",
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "summary": "string (generated summary)",
                        "video_title": "string",
                        "summary_length": "string",
                        "original_length": "integer (character count)",
                        "error": "string (if failed)",
                    },
                },
            },
            "extract_key_points": {
                "name": "extract_key_points",
                "description": "Extract structured key points from transcript using GPT-3.5",
                "parameters": {
                    "transcript": {
                        "type": "string",
                        "description": "Video transcript text",
                        "required": True,
                    },
                    "max_points": {
                        "type": "integer",
                        "description": "Maximum number of key points (3-20, default: 10)",
                        "required": False,
                        "default": 10,
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Optional focus area (e.g., 'technical details', 'business strategy')",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "key_points": "list of strings",
                        "count": "integer",
                        "focus_area": "string or None",
                        "error": "string (if failed)",
                    },
                },
            },
            "compare_videos": {
                "name": "compare_videos",
                "description": "Compare multiple video summaries to identify themes, insights, and differences",
                "parameters": {
                    "video_summaries": {
                        "type": "string or list",
                        "description": "JSON string or list of dicts with keys: title, summary, url (optional)",
                        "required": True,
                    },
                    "comparison_criteria": {
                        "type": "string",
                        "description": "Optional specific aspects to compare",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "comparison": "string (analysis text with themes/insights/differences)",
                        "video_count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "research":
        tools_docs = {
            "create_research_plan": {
                "name": "create_research_plan",
                "description": "Generate a comprehensive research plan for a topic using GPT-3.5",
                "parameters": {
                    "research_topic": {
                        "type": "string",
                        "description": "Research topic or question",
                        "required": True,
                    },
                    "scope": {
                        "type": "string",
                        "description": "Research scope: 'quick' (1-3 videos), 'moderate' (5-10 videos), 'comprehensive' (15-25 videos). Default: 'comprehensive'",
                        "required": False,
                        "default": "comprehensive",
                    },
                    "specific_questions": {
                        "type": "string",
                        "description": "Optional specific questions to answer",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "plan": "string (structured plan with sections: Search Strategy, Selection Criteria, Analysis Approach, Deliverables, Estimated Time)",
                        "target_videos": "dict with keys: min, max",
                        "error": "string (if failed)",
                    },
                },
            },
            "compile_research_report": {
                "name": "compile_research_report",
                "description": "Synthesize research findings into a formatted report using GPT-4o",
                "parameters": {
                    "research_topic": {
                        "type": "string",
                        "description": "Research topic",
                        "required": True,
                    },
                    "video_insights": {
                        "type": "string or list",
                        "description": "JSON string or list of dicts with keys: title, summary, key_points (list), url (optional)",
                        "required": True,
                    },
                    "additional_context": {
                        "type": "string",
                        "description": "Optional additional context or findings",
                        "required": False,
                        "default": None,
                    },
                    "report_format": {
                        "type": "string",
                        "description": "Format: 'executive_summary' (1-2 pages), 'standard' (3-5 pages), 'detailed' (5-10 pages). Default: 'standard'",
                        "required": False,
                        "default": "standard",
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "report": "string (markdown formatted report with header, executive summary, key findings, detailed analysis, conclusions, sources)",
                        "source_count": "integer",
                        "date": "string (ISO format)",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "discord":
        tools_docs = {
            "get_server_info": {
                "name": "get_server_info",
                "description": "Get detailed information about a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "data": "dict with keys: name, id, owner_id, member_count, created_at, description, premium_tier, explicit_content_filter",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_channels": {
                "name": "get_channels",
                "description": "Get a list of all channels in a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "channels": "list of dicts with keys: name, id, type",
                        "error": "string (if failed)",
                    },
                },
            },
            "list_members": {
                "name": "list_members",
                "description": "List members in a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of members to retrieve (default: 100, max: 1000)",
                        "required": False,
                        "default": 100,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "members": "list of dicts with keys: id, name, nick, joined_at, roles",
                        "count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "list_servers": {
                "name": "list_servers",
                "description": "List all Discord servers the bot has access to",
                "parameters": {},
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "servers": "list of dicts with keys: id, name, member_count, owner",
                        "count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_user_info": {
                "name": "get_user_info",
                "description": "Get information about a Discord user",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "Discord user ID",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "user": "dict with keys: id, name, discriminator, bot, created_at",
                        "error": "string (if failed)",
                    },
                },
            },
            "send_message": {
                "name": "send_message",
                "description": "Send a message to a Discord channel",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content (max 2000 characters)",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "message_id": "string",
                        "channel_id": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "read_messages": {
                "name": "read_messages",
                "description": "Read recent messages from a Discord channel",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to retrieve (default: 10, max: 100)",
                        "required": False,
                        "default": 10,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "messages": "list of dicts with keys: id, author_name, author_id, content, created_at, attachments, embeds",
                        "count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "add_reaction": {
                "name": "add_reaction",
                "description": "Add a reaction to a Discord message",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Discord message ID",
                        "required": True,
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to react with (Unicode or custom emoji ID)",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "add_multiple_reactions": {
                "name": "add_multiple_reactions",
                "description": "Add multiple reactions to a Discord message",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Discord message ID",
                        "required": True,
                    },
                    "emojis": {
                        "type": "list",
                        "description": "List of emojis to add as reactions",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "added_count": "integer",
                        "error": "string (if failed)",
                    },
                },
            },
            "remove_reaction": {
                "name": "remove_reaction",
                "description": "Remove a reaction from a Discord message",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Discord message ID",
                        "required": True,
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji reaction to remove",
                        "required": True,
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID whose reaction to remove (optional, defaults to bot)",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "moderate_message": {
                "name": "moderate_message",
                "description": "Moderate a Discord message (delete or pin/unpin)",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                        "required": True,
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Discord message ID",
                        "required": True,
                    },
                    "action": {
                        "type": "string",
                        "description": "Moderation action: 'delete', 'pin', or 'unpin'",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "action": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "add_role": {
                "name": "add_role",
                "description": "Add a role to a Discord user",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Discord user ID",
                        "required": True,
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Discord role ID to add",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "remove_role": {
                "name": "remove_role",
                "description": "Remove a role from a Discord user",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Discord user ID",
                        "required": True,
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Discord role ID to remove",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "create_text_channel": {
                "name": "create_text_channel",
                "description": "Create a new text channel in a Discord server. Prevents duplicates by checking for existing channels with the same name. If duplicate found, returns existing channel unless force_create_duplicate=True.",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "name": {
                        "type": "string",
                        "description": "Channel name",
                        "required": True,
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to create channel under",
                        "required": False,
                        "default": None,
                    },
                    "force_create_duplicate": {
                        "type": "boolean",
                        "description": "If True, creates a duplicate even if channel with same name exists. If False (default), returns existing channel if found.",
                        "required": False,
                        "default": False,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "channel_id": "string",
                        "channel_name": "string",
                        "error": "string (if duplicate found, contains warning message but success=True)",
                    },
                },
            },
            "upsert_text_channel": {
                "name": "upsert_text_channel",
                "description": "Create or return existing text channel in a Discord server. Checks for existing channels first and returns existing channel if found, unless force_create_duplicate=True.",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "name": {
                        "type": "string",
                        "description": "Channel name",
                        "required": True,
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to create channel under",
                        "required": False,
                        "default": None,
                    },
                    "force_create_duplicate": {
                        "type": "boolean",
                        "description": "If True, creates a duplicate even if channel with same name exists. If False (default), returns existing channel if found.",
                        "required": False,
                        "default": False,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "channel_id": "string",
                        "channel_name": "string",
                        "error": "string (if duplicate found, contains warning message but success=True)",
                    },
                },
            },
            "delete_channel": {
                "name": "delete_channel",
                "description": "Delete a Discord channel",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID to delete",
                        "required": True,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "create_category": {
                "name": "create_category",
                "description": "Create a new category channel in a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "name": {
                        "type": "string",
                        "description": "Category name",
                        "required": True,
                    },
                    "position": {
                        "type": "integer",
                        "description": "Optional position in the channel list (0-indexed)",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "category_id": "string",
                        "category_name": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "move_channel": {
                "name": "move_channel",
                "description": "Move a Discord channel to a different category or position",
                "parameters": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID to move",
                        "required": True,
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Target category ID (null to remove from category)",
                        "required": False,
                        "default": None,
                    },
                    "position": {
                        "type": "integer",
                        "description": "Optional position in the channel list",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "error": "string (if failed)",
                    },
                },
            },
            "create_scheduled_event": {
                "name": "create_scheduled_event",
                "description": "Create a scheduled event in a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "name": {
                        "type": "string",
                        "description": "Event name",
                        "required": True,
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description",
                        "required": False,
                        "default": None,
                    },
                    "start_time": {
                        "type": "string",
                        "description": "ISO format datetime string for event start",
                        "required": True,
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO format datetime string for event end (required for external events)",
                        "required": False,
                        "default": None,
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Event type: 'voice', 'stage_instance', or 'external' (default: 'external')",
                        "required": False,
                        "default": "external",
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID (required for voice/stage_instance)",
                        "required": False,
                        "default": None,
                    },
                    "location": {
                        "type": "string",
                        "description": "Location (required for external events)",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "event_id": "string",
                        "event_name": "string",
                        "error": "string (if failed)",
                    },
                },
            },
            "edit_scheduled_event": {
                "name": "edit_scheduled_event",
                "description": "Edit a scheduled event in a Discord server",
                "parameters": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID",
                        "required": True,
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Event ID to edit",
                        "required": True,
                    },
                    "name": {
                        "type": "string",
                        "description": "New event name",
                        "required": False,
                        "default": None,
                    },
                    "description": {
                        "type": "string",
                        "description": "New event description",
                        "required": False,
                        "default": None,
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time (ISO format)",
                        "required": False,
                        "default": None,
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time (ISO format)",
                        "required": False,
                        "default": None,
                    },
                    "status": {
                        "type": "string",
                        "description": "Event status: 'scheduled', 'active', 'completed', 'canceled'",
                        "required": False,
                        "default": None,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "event_id": "string",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    elif server_name == "supabase":
        tools_docs = {
            "add_document": {
                "name": "add_document",
                "description": "Add a document to Supabase database (typically from crawl4ai scraping)",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "Source URL of the document",
                        "required": True,
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title",
                        "required": True,
                    },
                    "content": {
                        "type": "string",
                        "description": "Document content (markdown or text)",
                        "required": True,
                    },
                    "description": {
                        "type": "string",
                        "description": "Document description/summary (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "author": {
                        "type": "string",
                        "description": "Document author (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "published_date": {
                        "type": "string",
                        "description": "Publication date in ISO format (default: '')",
                        "required": False,
                        "default": "",
                    },
                    "keywords": {
                        "type": "list",
                        "description": "List of keywords/tags (optional)",
                        "required": False,
                        "default": None,
                    },
                    "metadata": {
                        "type": "dict",
                        "description": "Additional metadata as dictionary (optional)",
                        "required": False,
                        "default": None,
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Name of the Supabase table (default: 'documents')",
                        "required": False,
                        "default": "documents",
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "result": "Document object with id, url, title, content, metadata",
                        "error": "string (if failed)",
                    },
                },
            },
            "get_document": {
                "name": "get_document",
                "description": "Retrieve a document from Supabase by its ID",
                "parameters": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document to retrieve",
                        "required": True,
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Name of the Supabase table (default: 'documents')",
                        "required": False,
                        "default": "documents",
                    },
                    "override_cache": {
                        "type": "boolean",
                        "description": "Whether to bypass cache (default: False)",
                        "required": False,
                        "default": False,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "result": "Document object with all fields",
                        "error": "string (if failed)",
                    },
                },
            },
            "search_documents": {
                "name": "search_documents",
                "description": "Search for documents in Supabase using text search or filters",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Text search query (searches in title, content, description)",
                        "required": False,
                        "default": None,
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Name of the Supabase table (default: 'documents')",
                        "required": False,
                        "default": "documents",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10, max: 100)",
                        "required": False,
                        "default": 10,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of results to skip for pagination (default: 0)",
                        "required": False,
                        "default": 0,
                    },
                    "filters": {
                        "type": "dict",
                        "description": "Optional dictionary of filters (e.g., {'author': 'John Doe'})",
                        "required": False,
                        "default": None,
                    },
                    "override_cache": {
                        "type": "boolean",
                        "description": "Whether to bypass cache (default: False)",
                        "required": False,
                        "default": False,
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "success": "boolean",
                        "result": "DocumentSearchResult with list of matching documents",
                        "error": "string (if failed)",
                    },
                },
            },
        }

    # Filter by specific tool if requested
    if tool:
        if tool in tools_docs:
            result = tools_docs[tool]
            if detail == "summary":
                # Return summary only
                return json.dumps(
                    {"name": result["name"], "description": result["description"]},
                    indent=2,
                )
            else:
                # Return full documentation
                return json.dumps(result, indent=2)
        else:
            return json.dumps(
                {"error": f"Tool '{tool}' not found in server '{server_name}'"}
            )
    else:
        # Return all tools
        if detail == "summary":
            return json.dumps(
                {
                    "server": server_name,
                    "tools": [
                        {"name": name, "description": info["description"]}
                        for name, info in tools_docs.items()
                    ],
                },
                indent=2,
            )
        else:
            return json.dumps(
                {"server": server_name, "tools": list(tools_docs.values())},
                indent=2,
            )

    return json.dumps(
        {"error": f"No documentation available for server '{server_name}'"}
    )


# Synchronous version
def query_tool_docs_sync(
    server_name: str, tool: Optional[str] = None, detail: str = "summary"
) -> str:
    """Synchronous version of query_tool_docs()"""
    return query_tool_docs(server_name, tool, detail)


def search_tool_docs(query: str, limit: Optional[int] = None) -> str:
    """
    Search for tools across all servers using fuzzy matching.

    Args:
        query: Search query (matches against tool names and descriptions)
        limit: Maximum number of results (None for all matches)

    Returns:
        JSON string with matching tools

    Example:
        >>> results = search_tool_docs("ping")
        >>> print(results)
        {"matches": [{"server": "url_ping", "tool": "ping_url", ...}]}
    """
    query_lower = query.lower()
    matches = []

    for server_name in _SERVERS_REGISTRY.keys():
        # Get full docs for this server
        docs_json = query_tool_docs(server_name, detail="full")
        docs = json.loads(docs_json)

        if "tools" in docs:
            for tool_info in docs["tools"]:
                # Check if query matches tool name or description
                if (
                    query_lower in tool_info["name"].lower()
                    or query_lower in tool_info["description"].lower()
                ):
                    matches.append(
                        {
                            "server": server_name,
                            "tool": tool_info["name"],
                            "description": tool_info["description"],
                        }
                    )

    # Apply limit if specified
    if limit:
        matches = matches[:limit]

    return json.dumps({"matches": matches}, indent=2)


# Synchronous version
def search_tool_docs_sync(query: str, limit: Optional[int] = None) -> str:
    """Synchronous version of search_tool_docs()"""
    return search_tool_docs(query, limit)


def capability_summary() -> str:
    """
    Return a one-paragraph summary of available capabilities.

    This is advertised in SANDBOX_HELPERS_SUMMARY.

    Returns:
        Human-readable summary string
    """
    server_count = len(_SERVERS_REGISTRY)
    tool_count = sum(len(info["tools"]) for info in _SERVERS_REGISTRY.values())

    return (
        f"MCP Code Execution Sandbox with {server_count} server(s) providing {tool_count} tool(s). "
        f"Available helpers: discovered_servers() to list servers, query_tool_docs(server, tool) "
        f"to load schemas on-demand, search_tool_docs(query) for fuzzy search. "
        f"Zero-context discovery: ~200 token overhead regardless of server count."
    )


# Tool execution proxies
async def _execute_tool(server_name: str, tool_name: str, **kwargs) -> Any:
    """
    Execute a tool via proxy (called by sandbox code).

    Args:
        server_name: Server name from discovered_servers()
        tool_name: Tool name from query_tool_docs()
        **kwargs: Tool arguments

    Returns:
        Tool execution result
    """
    if server_name not in _SERVERS_REGISTRY:
        raise ValueError(f"Server '{server_name}' not found")

    server_info = _SERVERS_REGISTRY[server_name]

    if tool_name not in server_info["tools"]:
        raise ValueError(f"Tool '{tool_name}' not found in server '{server_name}'")

    # Import and execute tool dynamically
    if server_name == "url_ping":
        if tool_name == "ping_url":
            from .tools.url_ping.ping_url import ping_url

            return await ping_url(**kwargs)

    elif server_name == "youtube":
        if tool_name == "search_youtube":
            from .tools.youtube.search_youtube import search_youtube

            return await search_youtube(**kwargs)
        elif tool_name == "get_transcript":
            from .tools.youtube.get_transcript import get_transcript

            return await get_transcript(**kwargs)
        elif tool_name == "get_video_metadata":
            from .tools.youtube.get_video_metadata import get_video_metadata

            return await get_video_metadata(**kwargs)

    elif server_name == "notion":
        if tool_name == "search_notion":
            from .tools.notion.search_notion import search_notion

            return await search_notion(**kwargs)
        elif tool_name == "get_notion_page":
            from .tools.notion.get_page import get_notion_page

            return await get_notion_page(**kwargs)
        elif tool_name == "create_notion_page":
            from .tools.notion.create_page import create_notion_page

            return await create_notion_page(**kwargs)
        elif tool_name == "update_notion_page":
            from .tools.notion.update_page import update_notion_page

            return await update_notion_page(**kwargs)
        elif tool_name == "query_notion_database":
            from .tools.notion.query_database import query_notion_database

            return await query_notion_database(**kwargs)
        elif tool_name == "add_notion_comment":
            from .tools.notion.add_comment import add_notion_comment

            return await add_notion_comment(**kwargs)

    elif server_name == "crawl4ai":
        if tool_name == "crawl_website":
            from .tools.crawl4ai.crawl_website import crawl_website

            return await crawl_website(**kwargs)
        elif tool_name == "save_article":
            from .tools.crawl4ai.save_article import save_article

            return await save_article(**kwargs)
        elif tool_name == "chunk_markdown":
            from .tools.crawl4ai.chunk_markdown import chunk_markdown

            return await chunk_markdown(**kwargs)
        elif tool_name == "extract_code_blocks":
            from .tools.crawl4ai.extract_code_blocks import extract_code_blocks_tool

            return await extract_code_blocks_tool(**kwargs)

    elif server_name == "discord":
        # Discord tools - wrapper functions that handle bot client internally
        if tool_name == "get_server_info":
            from .tools.discord.get_server_info import get_server_info

            return await get_server_info(**kwargs)
        elif tool_name == "get_channels":
            from .tools.discord.get_channels import get_channels

            return await get_channels(**kwargs)
        elif tool_name == "list_members":
            from .tools.discord.list_members import list_members

            return await list_members(**kwargs)
        elif tool_name == "list_servers":
            from .tools.discord.list_servers import list_servers

            return await list_servers(**kwargs)
        elif tool_name == "get_user_info":
            from .tools.discord.get_user_info import get_user_info

            return await get_user_info(**kwargs)
        elif tool_name == "send_message":
            from .tools.discord.send_message import send_message

            return await send_message(**kwargs)
        elif tool_name == "send_message_with_image":
            from .tools.discord.send_message_with_image import send_message_with_image

            return await send_message_with_image(**kwargs)
        elif tool_name == "read_messages":
            from .tools.discord.read_messages import read_messages

            return await read_messages(**kwargs)
        elif tool_name == "add_reaction":
            from .tools.discord.add_reaction import add_reaction

            return await add_reaction(**kwargs)
        elif tool_name == "add_multiple_reactions":
            from .tools.discord.add_multiple_reactions import add_multiple_reactions

            return await add_multiple_reactions(**kwargs)
        elif tool_name == "remove_reaction":
            from .tools.discord.remove_reaction import remove_reaction

            return await remove_reaction(**kwargs)
        elif tool_name == "moderate_message":
            from .tools.discord.moderate_message import moderate_message

            return await moderate_message(**kwargs)
        elif tool_name == "add_role":
            from .tools.discord.add_role import add_role

            return await add_role(**kwargs)
        elif tool_name == "remove_role":
            from .tools.discord.remove_role import remove_role

            return await remove_role(**kwargs)
        elif tool_name == "create_text_channel":
            from .tools.discord.create_text_channel import create_text_channel

            return await create_text_channel(**kwargs)
        elif tool_name == "upsert_text_channel":
            from .tools.discord.upsert_text_channel import upsert_text_channel

            return await upsert_text_channel(**kwargs)
        elif tool_name == "delete_channel":
            from .tools.discord.delete_channel import delete_channel

            return await delete_channel(**kwargs)
        elif tool_name == "create_category":
            from .tools.discord.create_category import create_category

            return await create_category(**kwargs)
        elif tool_name == "move_channel":
            from .tools.discord.move_channel import move_channel

            return await move_channel(**kwargs)
        elif tool_name == "create_scheduled_event":
            from .tools.discord.create_scheduled_event import create_scheduled_event

            return await create_scheduled_event(**kwargs)
        elif tool_name == "edit_scheduled_event":
            from .tools.discord.edit_scheduled_event import edit_scheduled_event

            return await edit_scheduled_event(**kwargs)

    elif server_name == "supabase":
        if tool_name == "add_document":
            from .tools.supabase.add_document import add_document

            return await add_document(**kwargs)
        elif tool_name == "get_document":
            from .tools.supabase.get_document import get_document

            return await get_document(**kwargs)
        elif tool_name == "search_documents":
            from .tools.supabase.search_documents import search_documents

            return await search_documents(**kwargs)
        elif tool_name == "get_available_sources":
            from .tools.supabase.get_available_sources import get_available_sources

            return await get_available_sources(**kwargs)
        elif tool_name == "perform_rag_query":
            from .tools.supabase.perform_rag_query import perform_rag_query

            return await perform_rag_query(**kwargs)
        elif tool_name == "add_code_example":
            from .tools.supabase.add_code_example import add_code_example

            return await add_code_example(**kwargs)
        elif tool_name == "search_code_examples":
            from .tools.supabase.search_code_examples import search_code_examples

            return await search_code_examples(**kwargs)

    elif server_name == "agents":
        if tool_name == "scraper_agent":
            from .tools.agents.scraper_agent_tool import scraper_agent_tool

            return await scraper_agent_tool(**kwargs)
        elif tool_name == "extraction_agent":
            from .tools.agents.extraction_agent_tool import extraction_agent_tool

            return await extraction_agent_tool(**kwargs)
        elif tool_name == "validation_agent":
            from .tools.agents.validation_agent_tool import validation_agent_tool

            return await validation_agent_tool(**kwargs)
        elif tool_name == "code_summarizer":
            from .tools.agents.code_summarizer_tool import code_summarizer_tool

            return await code_summarizer_tool(**kwargs)

    raise NotImplementedError(f"Tool '{tool_name}' not implemented")


# Synchronous wrapper for tools that don't need async
def _execute_tool_sync(server_name: str, tool_name: str, **kwargs) -> Any:
    """Synchronous version of _execute_tool (for non-async tools)"""
    import asyncio

    return asyncio.run(_execute_tool(server_name, tool_name, **kwargs))


# Helper to create tool proxy (used in sandbox)
def create_tool_proxy(server_name: str, tool_name: str):
    """
    Create a callable proxy for a tool.

    This allows sandbox code to call tools naturally:
        ping = create_tool_proxy("url_ping", "ping_url")
        result = await ping(url="https://example.com")
    """

    async def proxy(**kwargs):
        return await _execute_tool(server_name, tool_name, **kwargs)

    proxy.__name__ = tool_name
    proxy.__doc__ = f"Proxy for {server_name}.{tool_name}"

    return proxy


# SANDBOX_HELPERS_SUMMARY - advertised to LLM
SANDBOX_HELPERS_SUMMARY = {
    "description": capability_summary(),
    "helpers": [
        {
            "name": "discovered_servers",
            "description": "List available MCP servers without loading schemas",
            "signature": "() -> List[Dict[str, str]]",
        },
        {
            "name": "list_servers",
            "description": "Get names of all available servers",
            "signature": "() -> List[str]",
        },
        {
            "name": "query_tool_docs",
            "description": "Load tool documentation on-demand for a specific server",
            "signature": "(server_name: str, tool: Optional[str] = None, detail: str = 'summary') -> str",
        },
        {
            "name": "search_tool_docs",
            "description": "Search for tools across all servers",
            "signature": "(query: str, limit: Optional[int] = None) -> str",
        },
        {
            "name": "create_tool_proxy",
            "description": "Create a callable proxy for executing a tool",
            "signature": "(server_name: str, tool_name: str) -> Callable",
        },
    ],
}
