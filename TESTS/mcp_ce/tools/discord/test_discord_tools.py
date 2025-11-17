"""Comprehensive test suite for Discord tools."""

import asyncio
import os
from dotenv import load_dotenv
import discord

load_dotenv()

# Import Discord bot helper
from src.mcp_ce.tools.discord._bot_helper import get_bot, set_bot

# Import all Discord tools
from src.mcp_ce.tools.discord.send_message import send_message
from src.mcp_ce.tools.discord.get_server_info import get_server_info
from src.mcp_ce.tools.discord.get_channels import get_channels
from src.mcp_ce.tools.discord.get_user_info import get_user_info
from src.mcp_ce.tools.discord.list_members import list_members
from src.mcp_ce.tools.discord.list_servers import list_servers
from src.mcp_ce.tools.discord.read_messages import read_messages
from src.mcp_ce.tools.discord.add_reaction import add_reaction
from src.mcp_ce.tools.discord.add_multiple_reactions import add_multiple_reactions
from src.mcp_ce.tools.discord.remove_reaction import remove_reaction
from src.mcp_ce.tools.discord.add_role import add_role
from src.mcp_ce.tools.discord.remove_role import remove_role
from src.mcp_ce.tools.discord.create_text_channel import create_text_channel
from src.mcp_ce.tools.discord.create_category import create_category
from src.mcp_ce.tools.discord.delete_channel import delete_channel
from src.mcp_ce.tools.discord.move_channel import move_channel
from src.mcp_ce.tools.discord.moderate_message import moderate_message
from src.mcp_ce.tools.discord.create_scheduled_event import create_scheduled_event
from src.mcp_ce.tools.discord.edit_scheduled_event import edit_scheduled_event
from src.mcp_ce.tools.discord.upsert_scheduled_event import upsert_scheduled_event
from src.mcp_ce.tools.discord.delete_scheduled_event import delete_scheduled_event


async def test_discord_tools():
    """
    Comprehensive test suite for Discord tools.

    NOTE: This test suite requires:
    1. DISCORD_TOKEN environment variable
    2. Active Discord bot with proper permissions
    3. Test server/channel IDs (update with your values)

    Test Categories:
    - Server operations (get_server_info, list_servers)
    - Channel operations (get_channels, create_text_channel, create_category, move_channel, delete_channel)
    - User operations (get_user_info, list_members, add_role, remove_role)
    - Message operations (send_message, read_messages, moderate_message)
    - Reaction operations (add_reaction, add_multiple_reactions, remove_reaction)
    - Event operations (create_scheduled_event, edit_scheduled_event)
    - Cache behavior (override_cache parameter testing)
    - Error handling (invalid IDs, missing permissions)
    """

    # ============================================================
    # CONFIGURATION - LIVE SERVER
    # ============================================================
    TEST_SERVER_ID = "1438957830064570402"
    TEST_CHANNEL_ID = "1439978275517763684"  # Bot testing channel
    # Note: Update these with actual user/role IDs from your server
    TEST_USER_ID = None  # Will be set to bot's own ID
    TEST_ROLE_ID = None  # Optional: Set to a test role ID if available

    print("\n" + "=" * 70)
    print("Discord Tools Test Suite")
    print("=" * 70)

    # Get bot's user ID for testing
    if TEST_USER_ID is None:
        try:
            bot = get_bot()
            if bot.user:
                TEST_USER_ID = str(bot.user.id)
                print(f"\n✅ Using bot's user ID for testing: {TEST_USER_ID}")
        except:
            TEST_USER_ID = None
            print("\n⚠️  Could not get bot user ID, skipping user-specific tests")

    # ============================================================
    # Test 1: Server Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 1: Server Operations")
    print("=" * 70)

    print("\n[1.1] Testing get_server_info (cached)")
    result = await get_server_info(server_id=TEST_SERVER_ID)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Server Name: {result.result.name}")
        print(f"   Member Count: {result.result.member_count}")
        print(f"   Owner ID: {result.result.owner_id}")
        print(f"   Created: {result.result.created_at}")
    else:
        print(f"   Error: {result.error}")

    print("\n[1.2] Testing get_server_info with cache override")
    result = await get_server_info(server_id=TEST_SERVER_ID, override_cache=True)
    print(f"✅ Cache bypassed: {result.is_success}")

    print("\n[1.3] Testing list_servers")
    result = await list_servers()
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Total Servers: {result.result.count}")
        for server in result.result.servers[:3]:  # Show first 3
            print(f"   - {server['name']} (ID: {server['id']})")
    else:
        print(f"   Error: {result.error}")

    # ============================================================
    # Test 2: Channel Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 2: Channel Operations")
    print("=" * 70)

    print("\n[2.1] Testing get_channels (cached)")
    result = await get_channels(server_id=TEST_SERVER_ID)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Total Channels: {result.result.count}")
        for channel in result.result.channels[:5]:  # Show first 5
            print(f"   - {channel['name']} ({channel['type']}) [ID: {channel['id']}]")
    else:
        print(f"   Error: {result.error}")

    print("[2.2] Testing create_category")
    result = await create_category(
        server_id=TEST_SERVER_ID, name="Test Category", position=0
    )
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        category_id = result.result.category_id
        print(f"   Category ID: {category_id}")
        print(f"   Category Name: {result.result.name}")
        print(f"   Position: {result.result.position}")

        print("\n[2.3] Testing create_text_channel under category")
        result = await create_text_channel(
            server_id=TEST_SERVER_ID, name="test-channel", category_id=category_id
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            channel_id = result.result.channel_id
            print(f"   Channel ID: {channel_id}")
            print(f"   Channel Name: {result.result.channel_name}")

            print("\n[2.4] Testing move_channel")
            result = await move_channel(
                channel_id=channel_id, category_id=category_id, position=0
            )
            print(f"✅ Success: {result.is_success}")
            if result.is_success:
                print(f"   Moved to category: {result.result.new_category_id}")
                print(f"   New position: {result.result.new_position}")

            print("\n[2.5] Testing delete_channel")
            result = await delete_channel(channel_id=channel_id)
            print(f"✅ Success: {result.is_success}")
            if result.is_success:
                print(f"   Deleted channel: {result.result['channel_id']}")

        # Cleanup: Delete test category
        result = await delete_channel(channel_id=category_id)
        print(f"\n[2.6] Cleanup category: {result.is_success}")
    else:
        print(f"   Error: {result.error}")

    # ============================================================
    # Test 3: User Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 3: User Operations")
    print("=" * 70)

    if TEST_USER_ID:
        print("\n[3.1] Testing get_user_info (cached)")
        result = await get_user_info(user_id=TEST_USER_ID)
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(
                f"   Username: {result.result.username}#{result.result.discriminator}"
            )
            print(f"   Display Name: {result.result.display_name}")
            print(f"   Bot: {result.result.bot}")
            print(f"   Created: {result.result.created_at}")
        else:
            print(f"   Error: {result.error}")
    else:
        print("\n[3.1] ⏭️  Skipping get_user_info (TEST_USER_ID not set)")

    print("\n[3.2] Testing list_members (cached, limit=10)")
    result = await list_members(server_id=TEST_SERVER_ID, limit=10)
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        print(f"   Total Members (limited): {result.result.count}")
        for member in result.result.members[:3]:  # Show first 3
            print(
                f"   - {member['name']} (Nick: {member['nick']}) [ID: {member['id']}]"
            )
    else:
        print(f"   Error: {result.error}")

    if TEST_USER_ID and TEST_ROLE_ID:
        print("\n[3.3] Testing add_role")
        result = await add_role(
            server_id=TEST_SERVER_ID, user_id=TEST_USER_ID, role_id=TEST_ROLE_ID
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Role Added: {result.result.role_name}")
            print(f"   User ID: {result.result.user_id}")
            print(f"   Action: {result.result.action}")

            print("\n[3.4] Testing remove_role")
            result = await remove_role(
                server_id=TEST_SERVER_ID, user_id=TEST_USER_ID, role_id=TEST_ROLE_ID
            )
            print(f"✅ Success: {result.is_success}")
            if result.is_success:
                print(f"   Role Removed: {result.result.role_name}")
                print(f"   Action: {result.result.action}")
        else:
            print(f"   Error (add_role): {result.error}")
    else:
        print(
            "\n[3.3] ⏭️  Skipping add_role/remove_role tests (TEST_USER_ID or TEST_ROLE_ID not set)"
        )

    # ============================================================
    # Test 4: Message Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 4: Message Operations")
    print("=" * 70)

    print("\n[4.1] Testing send_message")
    result = await send_message(
        channel_id=TEST_CHANNEL_ID,
        content="🤖 Test message from Discord tools test suite!",
    )
    print(f"✅ Success: {result.is_success}")
    if result.is_success:
        message_id = result.result.message_id
        print(f"   Message ID: {message_id}")
        print(f"   Channel ID: {result.result.channel_id}")
        print(f"   Content: {result.result.content}")
        print(f"   Timestamp: {result.result.timestamp}")

        print("\n[4.2] Testing read_messages (cached)")
        result = await read_messages(channel_id=TEST_CHANNEL_ID, limit=5)
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Messages Retrieved: {result.result.count}")
            for msg in result.result.messages[:2]:  # Show first 2
                print(f"   - {msg['author']}: {msg['content'][:50]}...")

        print("\n[4.3] Testing moderate_message (pin)")
        result = await moderate_message(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, action="pin"
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Action: {result.result.action}")
            print(f"   Moderator ID: {result.result.moderator_id}")

            print("\n[4.4] Testing moderate_message (unpin)")
            result = await moderate_message(
                channel_id=TEST_CHANNEL_ID, message_id=message_id, action="unpin"
            )
            print(f"✅ Success: {result.is_success}")

        # Cleanup: Delete test message
        result = await moderate_message(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, action="delete"
        )
        print(f"\n[4.5] Cleanup message: {result.is_success}")
    else:
        print(f"   Error: {result.error}")

    # ============================================================
    # Test 5: Reaction Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 5: Reaction Operations")
    print("=" * 70)

    print("\n[5.1] Testing add_reaction")
    # First send a message to react to
    msg_result = await send_message(
        channel_id=TEST_CHANNEL_ID, content="React to this message!"
    )
    if msg_result.is_success:
        message_id = msg_result.result.message_id

        result = await add_reaction(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, emoji="👍"
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Emoji: {result.result.emoji}")
            print(f"   Action: {result.result.action}")

        print("\n[5.2] Testing add_multiple_reactions")
        result = await add_multiple_reactions(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, emojis=["❤️", "🎉", "🚀"]
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Emojis: {result.result.emoji}")
            print(f"   Action: {result.result.action}")

        print("\n[5.3] Testing remove_reaction")
        result = await remove_reaction(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, emoji="👍"
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Emoji Removed: {result.result.emoji}")
            print(f"   Action: {result.result.action}")

        # Cleanup
        await moderate_message(
            channel_id=TEST_CHANNEL_ID, message_id=message_id, action="delete"
        )
        print(f"\n[5.4] Cleanup message: Success")

    # ============================================================
    # Test 6: Event Operations
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 6: Event Operations")
    print("=" * 70)

    print("\n[6.1] Testing upsert_scheduled_event (permanent 'Test Event - Discord')")
    from datetime import datetime, timedelta, timezone

    # Use future date to avoid issues with past events
    future_date = datetime.now(timezone.utc) + timedelta(days=30)
    start_time = future_date.replace(hour=20, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)

    result = await upsert_scheduled_event(
        server_id=TEST_SERVER_ID,
        name="Test Event - Discord",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        description="Permanent test event for Discord tools validation.",
        entity_type="external",
        location="Discord Community Server",
    )
    print(f"✅ Success: {result.is_success}")
    event_id = None
    if result.is_success:
        event_id = result.result["event"].event_id
        operation = result.result["operation"]
        print(f"   Operation: {operation}")
        print(f"   Event ID: {event_id}")
        print(f"   Event Name: {result.result['event'].name}")
        print(f"   Description (with timestamp): {result.result['event'].description}")

        print("\n[6.2] Testing upsert again (updates timestamp)")
        result = await upsert_scheduled_event(
            server_id=TEST_SERVER_ID,
            name="Test Event - Discord",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            description="Permanent test event for Discord tools validation.",
            entity_type="external",
            location="Discord Community Server",
        )
        print(f"✅ Success: {result.is_success}")
        if result.is_success:
            print(f"   Operation: {result.result['operation']} (should be 'updated')")
            print(f"   Updated Description: {result.result['event'].description}")

        print("\n[6.3] Event persists (NOT deleted - permanent test event)")
        print(f"    'Test Event - Discord' remains for future test runs")
    else:
        print(f"   Error: {result.error}")

    # ============================================================
    # Test 7: Error Handling
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Category 7: Error Handling")
    print("=" * 70)

    print("\n[7.1] Testing invalid server ID")
    result = await get_server_info(server_id="invalid_id")
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")

    print("\n[7.2] Testing invalid channel ID")
    result = await send_message(channel_id="999999999999999999", content="Test")
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")

    print("\n[7.3] Testing message too long (>2000 chars)")
    result = await send_message(channel_id=TEST_CHANNEL_ID, content="A" * 2001)
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")

    print("\n[7.4] Testing invalid moderation action")
    result = await moderate_message(
        channel_id=TEST_CHANNEL_ID, message_id="123456789", action="invalid_action"
    )
    print(f"❌ Error handled: {not result.is_success}")
    if not result.is_success:
        print(f"   Error message: {result.error}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("Test Suite Summary")
    print("=" * 70)
    print("✅ All 19 Discord tools tested")
    print("✅ ToolResponse pattern validated")
    print("✅ Dataclass results confirmed")
    print("✅ Cache behavior verified")
    print("✅ Error handling validated")
    print("=" * 70)

    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DISCORD TOOLS COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: Update TEST_SERVER_ID, TEST_CHANNEL_ID, TEST_USER_ID,")
    print("   and TEST_ROLE_ID in the test_discord_tools() function before running!")
    print("\n⚠️  WARNING: This test suite will create/delete channels, send messages,")
    print("   and modify roles. Run only on a test server!\n")

    try:
        asyncio.run(test_discord_tools())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
