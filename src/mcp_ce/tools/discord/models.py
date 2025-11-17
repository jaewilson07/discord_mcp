"""Discord result models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..model import ToolResult


@dataclass
class ServerInfo(ToolResult):
    """
    Discord server (guild) information.

    Attributes:
        server_id: Server ID
        name: Server name
        description: Server description
        member_count: Number of members
        owner_id: Server owner ID
        created_at: Server creation date (ISO format)
        icon_url: Server icon URL
        features: List of server features
    """

    server_id: str
    name: str
    description: str = ""
    member_count: int = 0
    owner_id: str = ""
    created_at: str = ""
    icon_url: str = ""
    features: List[str] = field(default_factory=list)


@dataclass
class UserInfo(ToolResult):
    """
    Discord user information.

    Attributes:
        user_id: User ID
        username: Username
        discriminator: User discriminator
        display_name: Display name
        avatar_url: Avatar URL
        bot: Whether user is a bot
        created_at: Account creation date (ISO format)
    """

    user_id: str
    username: str
    discriminator: str
    display_name: str = ""
    avatar_url: str = ""
    bot: bool = False
    created_at: str = ""


@dataclass
class ChannelInfo(ToolResult):
    """
    Discord channel information.

    Attributes:
        channel_id: Channel ID
        name: Channel name
        type: Channel type (text, voice, category, etc.)
        category: Category name
        position: Channel position
        topic: Channel topic
        nsfw: Whether channel is marked as NSFW
    """

    channel_id: str
    name: str
    type: str
    category: str = ""
    position: int = 0
    topic: str = ""
    nsfw: bool = False


@dataclass
class MessageInfo(ToolResult):
    """
    Discord message information.

    Attributes:
        message_id: Message ID
        channel_id: Channel ID
        author_id: Author user ID
        content: Message content
        timestamp: Message timestamp (ISO format)
        edited_timestamp: Edit timestamp (ISO format), empty if not edited
        attachments: List of attachment URLs
        embeds: Number of embeds
        reactions: List of reaction emoji
    """

    message_id: str
    channel_id: str
    author_id: str
    content: str
    timestamp: str
    edited_timestamp: str = ""
    attachments: List[str] = field(default_factory=list)
    embeds: int = 0
    reactions: List[str] = field(default_factory=list)


@dataclass
class MessageResult(ToolResult):
    """
    Result from sending a Discord message.

    Attributes:
        message_id: ID of the sent message
        channel_id: ID of the channel
        content: Message content
        timestamp: Message timestamp (ISO format)
    """

    message_id: str
    channel_id: str
    content: str
    timestamp: str


@dataclass
class ChannelResult(ToolResult):
    """
    Result from creating a Discord channel.

    Attributes:
        channel_id: ID of the created channel
        name: Channel name
        type: Channel type
        category_id: Category ID (if applicable)
        position: Channel position
    """

    channel_id: str
    name: str
    type: str
    category_id: str = ""
    position: int = 0


@dataclass
class CategoryResult(ToolResult):
    """
    Result from creating a Discord category.

    Attributes:
        category_id: ID of the created category
        name: Category name
        position: Category position
    """

    category_id: str
    name: str
    position: int


@dataclass
class EventResult(ToolResult):
    """
    Result from creating/editing a Discord scheduled event.

    Attributes:
        event_id: Event ID
        name: Event name
        description: Event description
        start_time: Event start time (ISO format)
        end_time: Event end time (ISO format)
        location: Event location
        url: Event URL
    """

    event_id: str
    name: str
    description: str
    start_time: str
    end_time: str = ""
    location: str = ""
    url: str = ""


@dataclass
class MemberInfo(ToolResult):
    """
    Discord server member information.

    Attributes:
        user_id: User ID
        username: Username
        display_name: Display name in the server
        joined_at: When member joined (ISO format)
        roles: List of role names
        avatar_url: Avatar URL
        bot: Whether user is a bot
    """

    user_id: str
    username: str
    display_name: str
    joined_at: str
    roles: List[str] = field(default_factory=list)
    avatar_url: str = ""
    bot: bool = False


@dataclass
class ServerListResult(ToolResult):
    """
    Result from listing Discord servers.

    Attributes:
        servers: List of server info dictionaries
        count: Number of servers
    """

    servers: List[Dict[str, Any]]
    count: int


@dataclass
class ChannelListResult(ToolResult):
    """
    Result from listing Discord channels.

    Attributes:
        channels: List of channel info dictionaries
        count: Number of channels
    """

    channels: List[Dict[str, Any]]
    count: int


@dataclass
class MemberListResult(ToolResult):
    """
    Result from listing Discord members.

    Attributes:
        members: List of member info dictionaries
        count: Number of members
    """

    members: List[Dict[str, Any]]
    count: int


@dataclass
class MessageListResult(ToolResult):
    """
    Result from reading Discord messages.

    Attributes:
        messages: List of message info dictionaries
        count: Number of messages
        channel_id: Channel ID
    """

    messages: List[Dict[str, Any]]
    count: int
    channel_id: str


@dataclass
class ReactionResult(ToolResult):
    """
    Result from adding/removing Discord reactions.

    Attributes:
        message_id: Message ID
        channel_id: Channel ID
        emoji: Reaction emoji
        action: Action performed (added/removed)
    """

    message_id: str
    channel_id: str
    emoji: str
    action: str


@dataclass
class RoleResult(ToolResult):
    """
    Result from adding/removing Discord roles.

    Attributes:
        user_id: User ID
        role_name: Role name
        action: Action performed (added/removed)
    """

    user_id: str
    role_name: str
    action: str


@dataclass
class ModerationResult(ToolResult):
    """
    Result from Discord moderation actions.

    Attributes:
        message_id: Message ID
        action: Action performed (deleted/pinned/unpinned)
        channel_id: Channel ID
    """

    message_id: str
    action: str
    channel_id: str


@dataclass
class ChannelMoveResult(ToolResult):
    """
    Result from moving a Discord channel.

    Attributes:
        channel_id: Channel ID
        new_category: New category name
        new_position: New position
    """

    channel_id: str
    new_category: str
    new_position: int
