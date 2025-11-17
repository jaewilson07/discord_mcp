"""Discord MCP tools package."""

# Re-export all Discord tools for easy import
from .get_server_info import get_server_info
from .get_channels import get_channels
from .list_members import list_members
from .list_servers import list_servers
from .get_user_info import get_user_info
from .send_message import send_message
from .read_messages import read_messages
from .add_reaction import add_reaction
from .add_multiple_reactions import add_multiple_reactions
from .remove_reaction import remove_reaction
from .moderate_message import moderate_message
from .add_role import add_role
from .remove_role import remove_role
from .create_text_channel import create_text_channel
from .delete_channel import delete_channel
from .create_category import create_category
from .move_channel import move_channel
from .create_scheduled_event import create_scheduled_event
from .edit_scheduled_event import edit_scheduled_event

# Bot helper functions
from ._bot_helper import get_bot, set_bot, is_bot_ready

__all__ = [
    # Server info
    "get_server_info",
    "get_channels",
    "list_members",
    "list_servers",
    "get_user_info",
    # Messages
    "send_message",
    "read_messages",
    "add_reaction",
    "add_multiple_reactions",
    "remove_reaction",
    "moderate_message",
    # Roles
    "add_role",
    "remove_role",
    # Channels
    "create_text_channel",
    "delete_channel",
    "create_category",
    "move_channel",
    # Events
    "create_scheduled_event",
    "edit_scheduled_event",
    # Bot helpers
    "get_bot",
    "set_bot",
    "is_bot_ready",
]
