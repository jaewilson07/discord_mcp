"""Discord MCP tool definitions."""

from typing import List
from mcp.types import Tool


def get_tool_definitions() -> List[Tool]:
    """Get all Discord MCP tool definitions."""
    return [
        # Server Information Tools
        Tool(
            name="get_server_info",
            description="Get information about a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID",
                    }
                },
                "required": ["server_id"],
            },
        ),
        Tool(
            name="get_channels",
            description="Get a list of all channels in a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID",
                    }
                },
                "required": ["server_id"],
            },
        ),
        Tool(
            name="list_members",
            description="Get a list of members in a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of members to fetch",
                        "minimum": 1,
                        "maximum": 1000,
                    },
                },
                "required": ["server_id"],
            },
        ),
        Tool(
            name="list_servers",
            description="Get a list of all Discord servers the bot has access to with their details such as name, id, member count, and creation date.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_user_info",
            description="Get information about a Discord user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Discord user ID"}
                },
                "required": ["user_id"],
            },
        ),
        # Message Management Tools
        Tool(
            name="send_message",
            description="Send a message to a specific channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                    },
                    "content": {"type": "string", "description": "Message content"},
                },
                "required": ["channel_id", "content"],
            },
        ),
        Tool(
            name="read_messages",
            description="Read recent messages from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of messages to fetch (max 100)",
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="add_reaction",
            description="Add a reaction to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message",
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to",
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to react with (Unicode or custom emoji ID)",
                    },
                },
                "required": ["channel_id", "message_id", "emoji"],
            },
        ),
        Tool(
            name="add_multiple_reactions",
            description="Add multiple reactions to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message",
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to",
                    },
                    "emojis": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Emoji to react with (Unicode or custom emoji ID)",
                        },
                        "description": "List of emojis to add as reactions",
                    },
                },
                "required": ["channel_id", "message_id", "emojis"],
            },
        ),
        Tool(
            name="remove_reaction",
            description="Remove a reaction from a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message",
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to remove reaction from",
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to remove (Unicode or custom emoji ID)",
                    },
                },
                "required": ["channel_id", "message_id", "emoji"],
            },
        ),
        Tool(
            name="moderate_message",
            description="Delete a message and optionally timeout the user",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID containing the message",
                    },
                    "message_id": {
                        "type": "string",
                        "description": "ID of message to moderate",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for moderation",
                    },
                    "timeout_minutes": {
                        "type": "number",
                        "description": "Optional timeout duration in minutes",
                        "minimum": 0,
                        "maximum": 40320,  # Max 4 weeks
                    },
                },
                "required": ["channel_id", "message_id", "reason"],
            },
        ),
        # Role Management Tools
        Tool(
            name="add_role",
            description="Add a role to a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "user_id": {"type": "string", "description": "User to add role to"},
                    "role_id": {"type": "string", "description": "Role ID to add"},
                },
                "required": ["server_id", "user_id", "role_id"],
            },
        ),
        Tool(
            name="remove_role",
            description="Remove a role from a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "user_id": {
                        "type": "string",
                        "description": "User to remove role from",
                    },
                    "role_id": {"type": "string", "description": "Role ID to remove"},
                },
                "required": ["server_id", "user_id", "role_id"],
            },
        ),
        # Channel Management Tools
        Tool(
            name="create_text_channel",
            description="Create a new text channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "name": {"type": "string", "description": "Channel name"},
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to place channel in",
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional channel topic",
                    },
                },
                "required": ["server_id", "name"],
            },
        ),
        Tool(
            name="delete_channel",
            description="Delete a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "ID of channel to delete",
                    },
                    "reason": {"type": "string", "description": "Reason for deletion"},
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="create_category",
            description="Create a new category channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "name": {"type": "string", "description": "Category name"},
                    "position": {
                        "type": "number",
                        "description": "Optional position in the channel list (0-indexed)",
                    },
                },
                "required": ["server_id", "name"],
            },
        ),
        Tool(
            name="move_channel",
            description="Move a channel to a different category or remove it from a category",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "ID of the channel to move",
                    },
                    "category_id": {
                        "type": "string",
                        "description": "ID of the target category. Use 'null' or omit to remove from category.",
                    },
                    "sync_permissions": {
                        "type": "boolean",
                        "description": "Whether to sync permissions with the new category (default: false)",
                    },
                },
                "required": ["channel_id"],
            },
        ),
        # Event Management Tools
        Tool(
            name="create_scheduled_event",
            description="Create a scheduled event for a server. Supports three types: 'external' (location-based), 'voice' (voice channel), or 'stage' (stage channel). For external events, provide location and end_time. For voice/stage events, provide channel_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "name": {
                        "type": "string",
                        "description": "Name of the scheduled event",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (e.g., '2024-12-25T15:00:00+00:00')",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Type of event: 'external', 'voice', or 'stage'",
                        "enum": ["external", "voice", "stage"],
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID (required for voice/stage events)",
                    },
                    "location": {
                        "type": "string",
                        "description": "Location (required for external events)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format (required for external events, optional for others)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the event",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for audit log",
                    },
                },
                "required": ["server_id", "name", "start_time", "entity_type"],
            },
        ),
        Tool(
            name="edit_scheduled_event",
            description="Edit an existing scheduled event. Can update name, description, times, location, channel, entity type, or status. Provide only the fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Discord server ID"},
                    "event_id": {
                        "type": "string",
                        "description": "ID of the scheduled event to edit",
                    },
                    "name": {"type": "string", "description": "New name for the event"},
                    "description": {
                        "type": "string",
                        "description": "New description for the event",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time in ISO 8601 format",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time in ISO 8601 format (or 'null' to remove for voice/stage events)",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Change event type: 'external', 'voice', or 'stage'",
                        "enum": ["external", "voice", "stage"],
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "New channel ID (for voice/stage events)",
                    },
                    "location": {
                        "type": "string",
                        "description": "New location (for external events)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Change event status: 'scheduled', 'active', 'completed', 'cancelled'",
                        "enum": ["scheduled", "active", "completed", "cancelled"],
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for audit log",
                    },
                },
                "required": ["server_id", "event_id"],
            },
        ),
    ]
