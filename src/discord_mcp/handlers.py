"""Discord MCP tool handlers."""

import logging
import discord
from datetime import datetime, timedelta
from typing import Any, List
from mcp.types import TextContent
from discord.ext import commands

logger = logging.getLogger("discord-mcp-server")


# Server Information Handlers
async def handle_get_server_info(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Get detailed information about a Discord server."""
    guild = await discord_client.fetch_guild(int(arguments["server_id"]))
    info = {
        "name": guild.name,
        "id": str(guild.id),
        "owner_id": str(guild.owner_id),
        "member_count": guild.member_count,
        "created_at": guild.created_at.isoformat(),
        "description": guild.description,
        "premium_tier": guild.premium_tier,
        "explicit_content_filter": str(guild.explicit_content_filter),
    }
    return [
        TextContent(
            type="text",
            text=f"Server Information:\n"
            + "\n".join(f"{k}: {v}" for k, v in info.items()),
        )
    ]


async def handle_get_channels(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Get a list of all channels in a server."""
    try:
        guild = discord_client.get_guild(int(arguments["server_id"]))
        if guild:
            channel_list = []
            for channel in guild.channels:
                channel_list.append(
                    f"#{channel.name} (ID: {channel.id}) - {channel.type}"
                )

            return [
                TextContent(
                    type="text",
                    text=f"Channels in {guild.name}:\n" + "\n".join(channel_list),
                )
            ]
        else:
            return [TextContent(type="text", text="Guild not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_list_members(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """List members in a server."""
    guild = await discord_client.fetch_guild(int(arguments["server_id"]))
    limit = min(int(arguments.get("limit", 100)), 1000)

    members = []
    async for member in guild.fetch_members(limit=limit):
        members.append(
            {
                "id": str(member.id),
                "name": member.name,
                "nick": member.nick,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "roles": [str(role.id) for role in member.roles[1:]],  # Skip @everyone
            }
        )

    return [
        TextContent(
            type="text",
            text=f"Server Members ({len(members)}):\n"
            + "\n".join(
                f"{m['name']} (ID: {m['id']}, Roles: {', '.join(m['roles'])})"
                for m in members
            ),
        )
    ]


async def handle_list_servers(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """List all servers the bot has access to."""
    servers = []
    for guild in discord_client.guilds:
        servers.append(
            {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat(),
            }
        )

    return [
        TextContent(
            type="text",
            text=f"Available Servers ({len(servers)}):\n"
            + "\n".join(
                f"{s['name']} (ID: {s['id']}, Members: {s['member_count']})"
                for s in servers
            ),
        )
    ]


async def handle_get_user_info(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Get information about a Discord user."""
    user = await discord_client.fetch_user(int(arguments["user_id"]))
    user_info = {
        "id": str(user.id),
        "name": user.name,
        "discriminator": user.discriminator,
        "bot": user.bot,
        "created_at": user.created_at.isoformat(),
    }
    return [
        TextContent(
            type="text",
            text=f"User information:\n"
            + f"Name: {user_info['name']}#{user_info['discriminator']}\n"
            + f"ID: {user_info['id']}\n"
            + f"Bot: {user_info['bot']}\n"
            + f"Created: {user_info['created_at']}",
        )
    ]


# Message Management Handlers
async def handle_send_message(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Send a message to a channel."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    message = await channel.send(arguments["content"])
    return [
        TextContent(
            type="text", text=f"Message sent successfully. Message ID: {message.id}"
        )
    ]


async def handle_read_messages(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Read recent messages from a channel."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    limit = min(int(arguments.get("limit", 10)), 100)
    fetch_users = arguments.get("fetch_reaction_users", False)

    messages = []
    async for message in channel.history(limit=limit):
        reaction_data = []
        for reaction in message.reactions:
            emoji_str = (
                str(reaction.emoji.name)
                if hasattr(reaction.emoji, "name") and reaction.emoji.name
                else (
                    str(reaction.emoji.id)
                    if hasattr(reaction.emoji, "id")
                    else str(reaction.emoji)
                )
            )
            reaction_info = {"emoji": emoji_str, "count": reaction.count}
            logger.error(f"Emoji: {emoji_str}")
            reaction_data.append(reaction_info)
        messages.append(
            {
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data,
            }
        )

    def format_reaction(r):
        return f"{r['emoji']}({r['count']})"

    return [
        TextContent(
            type="text",
            text=f"Retrieved {len(messages)} messages:\n\n"
            + "\n".join(
                [
                    f"{m['author']} ({m['timestamp']}): {m['content']}\n"
                    + f"Reactions: {', '.join([format_reaction(r) for r in m['reactions']]) if m['reactions'] else 'No reactions'}"
                    for m in messages
                ]
            ),
        )
    ]


async def handle_add_reaction(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Add a reaction to a message."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    message = await channel.fetch_message(int(arguments["message_id"]))
    await message.add_reaction(arguments["emoji"])
    return [
        TextContent(type="text", text=f"Added reaction {arguments['emoji']} to message")
    ]


async def handle_add_multiple_reactions(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Add multiple reactions to a message."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    message = await channel.fetch_message(int(arguments["message_id"]))
    for emoji in arguments["emojis"]:
        await message.add_reaction(emoji)
    return [
        TextContent(
            type="text",
            text=f"Added reactions: {', '.join(arguments['emojis'])} to message",
        )
    ]


async def handle_remove_reaction(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Remove a reaction from a message."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    message = await channel.fetch_message(int(arguments["message_id"]))
    await message.remove_reaction(arguments["emoji"], discord_client.user)
    return [
        TextContent(
            type="text", text=f"Removed reaction {arguments['emoji']} from message"
        )
    ]


async def handle_moderate_message(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Delete a message and optionally timeout the user."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    message = await channel.fetch_message(int(arguments["message_id"]))

    # Delete the message
    await message.delete(reason=arguments["reason"])

    # Handle timeout if specified
    if "timeout_minutes" in arguments and arguments["timeout_minutes"] > 0:
        if isinstance(message.author, discord.Member):
            duration = discord.utils.utcnow() + timedelta(
                minutes=arguments["timeout_minutes"]
            )
            await message.author.timeout(duration, reason=arguments["reason"])
            return [
                TextContent(
                    type="text",
                    text=f"Message deleted and user timed out for {arguments['timeout_minutes']} minutes.",
                )
            ]

    return [TextContent(type="text", text="Message deleted successfully.")]


# Role Management Handlers
async def handle_add_role(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Add a role to a user."""
    guild = await discord_client.fetch_guild(int(arguments["server_id"]))
    member = await guild.fetch_member(int(arguments["user_id"]))
    role = guild.get_role(int(arguments["role_id"]))

    await member.add_roles(role, reason="Role added via MCP")
    return [
        TextContent(type="text", text=f"Added role {role.name} to user {member.name}")
    ]


async def handle_remove_role(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Remove a role from a user."""
    guild = await discord_client.fetch_guild(int(arguments["server_id"]))
    member = await guild.fetch_member(int(arguments["user_id"]))
    role = guild.get_role(int(arguments["role_id"]))

    await member.remove_roles(role, reason="Role removed via MCP")
    return [
        TextContent(
            type="text", text=f"Removed role {role.name} from user {member.name}"
        )
    ]


# Channel Management Handlers
async def handle_create_text_channel(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Create a new text channel."""
    guild = await discord_client.fetch_guild(int(arguments["server_id"]))
    category = None
    if "category_id" in arguments:
        category = guild.get_channel(int(arguments["category_id"]))

    channel = await guild.create_text_channel(
        name=arguments["name"],
        category=category,
        topic=arguments.get("topic"),
        reason="Channel created via MCP",
    )

    return [
        TextContent(
            type="text", text=f"Created text channel #{channel.name} (ID: {channel.id})"
        )
    ]


async def handle_delete_channel(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Delete a channel."""
    channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
    await channel.delete(reason=arguments.get("reason", "Channel deleted via MCP"))
    return [TextContent(type="text", text=f"Deleted channel successfully")]


async def handle_create_category(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Create a new category channel."""
    guild = discord_client.get_guild(int(arguments["server_id"]))
    if not guild:
        return [TextContent(type="text", text="Server not found")]

    name = arguments["name"]
    position = arguments.get("position")

    # Create category with optional position
    if position is not None:
        category = await guild.create_category(name=name, position=int(position))
    else:
        category = await guild.create_category(name=name)

    return [
        TextContent(
            type="text",
            text=f"Category '{category.name}' created successfully (ID: {category.id})",
        )
    ]


async def handle_move_channel(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Move a channel to a different category."""
    channel = discord_client.get_channel(int(arguments["channel_id"]))
    if not channel:
        return [TextContent(type="text", text="Channel not found")]

    # Get category if specified
    category_id = arguments.get("category_id")
    sync_permissions = arguments.get("sync_permissions", False)

    if category_id and category_id.lower() != "null":
        category = discord_client.get_channel(int(category_id))
        if not category:
            return [TextContent(type="text", text="Category not found")]

        # Move to category
        await channel.edit(category=category, sync_permissions=sync_permissions)
        return [
            TextContent(
                type="text",
                text=f"Channel '{channel.name}' moved to category '{category.name}' successfully",
            )
        ]
    else:
        # Remove from category
        await channel.edit(category=None)
        return [
            TextContent(
                type="text",
                text=f"Channel '{channel.name}' removed from category successfully",
            )
        ]


# Event Management Handlers
async def handle_create_scheduled_event(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Create a scheduled event."""
    from datetime import datetime as dt

    guild = discord_client.get_guild(int(arguments["server_id"]))
    if not guild:
        return [TextContent(type="text", text="Server not found")]

    name = arguments["name"]
    entity_type_str = arguments["entity_type"].lower()

    # Parse start time
    try:
        start_time = dt.fromisoformat(arguments["start_time"])
        # Ensure timezone-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=discord.utils.utcnow().tzinfo)
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"Invalid start_time format. Use ISO 8601 format (e.g., '2024-12-25T15:00:00+00:00'): {str(e)}",
            )
        ]

    # Parse end time if provided
    end_time = None
    if "end_time" in arguments:
        try:
            end_time = dt.fromisoformat(arguments["end_time"])
            # Ensure timezone-aware
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=discord.utils.utcnow().tzinfo)
        except ValueError as e:
            return [
                TextContent(
                    type="text",
                    text=f"Invalid end_time format. Use ISO 8601 format: {str(e)}",
                )
            ]

    # Map entity type string to EntityType enum
    from discord import EntityType

    entity_type_map = {
        "external": EntityType.external,
        "voice": EntityType.voice,
        "stage": EntityType.stage_instance,
    }
    entity_type = entity_type_map.get(entity_type_str)
    if not entity_type:
        return [
            TextContent(
                type="text",
                text=f"Invalid entity_type. Must be 'external', 'voice', or 'stage'",
            )
        ]

    # Prepare kwargs for create_scheduled_event
    kwargs = {
        "name": name,
        "start_time": start_time,
        "entity_type": entity_type,
    }

    # Add optional parameters
    if "description" in arguments:
        kwargs["description"] = arguments["description"]
    if "reason" in arguments:
        kwargs["reason"] = arguments["reason"]

    # Entity-type specific parameters
    if entity_type == EntityType.external:
        # External events require location and end_time
        if "location" not in arguments:
            return [
                TextContent(
                    type="text",
                    text="location is required for external events",
                )
            ]
        if not end_time:
            return [
                TextContent(
                    type="text",
                    text="end_time is required for external events",
                )
            ]
        kwargs["location"] = arguments["location"]
        kwargs["end_time"] = end_time
    elif entity_type in (EntityType.voice, EntityType.stage_instance):
        # Voice/Stage events require channel
        if "channel_id" not in arguments:
            return [
                TextContent(
                    type="text",
                    text="channel_id is required for voice/stage events",
                )
            ]
        channel = guild.get_channel(int(arguments["channel_id"]))
        if not channel:
            return [TextContent(type="text", text="Channel not found")]
        kwargs["channel"] = channel
        if end_time:
            kwargs["end_time"] = end_time

    # Create the scheduled event
    try:
        event = await guild.create_scheduled_event(**kwargs)
        return [
            TextContent(
                type="text",
                text=f"Scheduled event '{event.name}' created successfully!\nID: {event.id}\nURL: {event.url}",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating event: {str(e)}")]


async def handle_edit_scheduled_event(
    discord_client: commands.Bot, arguments: dict
) -> List[TextContent]:
    """Edit an existing scheduled event."""
    from datetime import datetime as dt

    guild = discord_client.get_guild(int(arguments["server_id"]))
    if not guild:
        return [TextContent(type="text", text="Server not found")]

    # Fetch the event
    try:
        event = await guild.fetch_scheduled_event(int(arguments["event_id"]))
    except Exception as e:
        return [TextContent(type="text", text=f"Event not found: {str(e)}")]

    # Prepare kwargs for edit
    kwargs = {}

    # Handle name
    if "name" in arguments:
        kwargs["name"] = arguments["name"]

    # Handle description
    if "description" in arguments:
        kwargs["description"] = arguments["description"]

    # Handle start_time
    if "start_time" in arguments:
        try:
            start_time = dt.fromisoformat(arguments["start_time"])
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=discord.utils.utcnow().tzinfo)
            kwargs["start_time"] = start_time
        except ValueError as e:
            return [
                TextContent(
                    type="text",
                    text=f"Invalid start_time format. Use ISO 8601 format: {str(e)}",
                )
            ]

    # Handle end_time
    if "end_time" in arguments:
        if arguments["end_time"].lower() == "null":
            kwargs["end_time"] = None
        else:
            try:
                end_time = dt.fromisoformat(arguments["end_time"])
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=discord.utils.utcnow().tzinfo)
                kwargs["end_time"] = end_time
            except ValueError as e:
                return [
                    TextContent(
                        type="text",
                        text=f"Invalid end_time format. Use ISO 8601 format: {str(e)}",
                    )
                ]

    # Handle entity_type
    if "entity_type" in arguments:
        from discord import EntityType

        entity_type_map = {
            "external": EntityType.external,
            "voice": EntityType.voice,
            "stage": EntityType.stage_instance,
        }
        entity_type = entity_type_map.get(arguments["entity_type"].lower())
        if not entity_type:
            return [
                TextContent(
                    type="text",
                    text="Invalid entity_type. Must be 'external', 'voice', or 'stage'",
                )
            ]
        kwargs["entity_type"] = entity_type

    # Handle channel_id
    if "channel_id" in arguments:
        channel = guild.get_channel(int(arguments["channel_id"]))
        if not channel:
            return [TextContent(type="text", text="Channel not found")]
        kwargs["channel"] = channel

    # Handle location
    if "location" in arguments:
        kwargs["location"] = arguments["location"]

    # Handle status
    if "status" in arguments:
        from discord import EventStatus

        status_map = {
            "scheduled": EventStatus.scheduled,
            "active": EventStatus.active,
            "completed": EventStatus.completed,
            "cancelled": EventStatus.cancelled,
        }
        status = status_map.get(arguments["status"].lower())
        if not status:
            return [
                TextContent(
                    type="text",
                    text="Invalid status. Must be 'scheduled', 'active', 'completed', or 'cancelled'",
                )
            ]
        kwargs["status"] = status

    # Handle reason
    if "reason" in arguments:
        kwargs["reason"] = arguments["reason"]

    # Edit the event
    try:
        updated_event = await event.edit(**kwargs)
        return [
            TextContent(
                type="text",
                text=f"Scheduled event '{updated_event.name}' updated successfully!\nID: {updated_event.id}\nURL: {updated_event.url}",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error editing event: {str(e)}")]


# Tool routing
TOOL_HANDLERS = {
    "get_server_info": handle_get_server_info,
    "get_channels": handle_get_channels,
    "list_members": handle_list_members,
    "list_servers": handle_list_servers,
    "get_user_info": handle_get_user_info,
    "send_message": handle_send_message,
    "read_messages": handle_read_messages,
    "add_reaction": handle_add_reaction,
    "add_multiple_reactions": handle_add_multiple_reactions,
    "remove_reaction": handle_remove_reaction,
    "moderate_message": handle_moderate_message,
    "add_role": handle_add_role,
    "remove_role": handle_remove_role,
    "create_text_channel": handle_create_text_channel,
    "delete_channel": handle_delete_channel,
    "create_category": handle_create_category,
    "move_channel": handle_move_channel,
    "create_scheduled_event": handle_create_scheduled_event,
    "edit_scheduled_event": handle_edit_scheduled_event,
}


async def handle_tool_call(
    discord_client: commands.Bot, name: str, arguments: Any
) -> List[TextContent]:
    """Route tool calls to appropriate handlers."""
    if name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {name}")

    handler = TOOL_HANDLERS[name]
    return await handler(discord_client, arguments)
