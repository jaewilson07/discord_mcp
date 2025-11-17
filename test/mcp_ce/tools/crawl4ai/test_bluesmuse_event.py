import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_event_extraction():
    """Test scraping bluesmuse.dance and extracting event details"""

    # Step 1: Scrape the page
    print("📡 Step 1: Scraping https://www.bluesmuse.dance/...")
    from mcp_ce.tools.crawl4ai.crawl_website import crawl_website

    result = await crawl_website(
        url="https://www.bluesmuse.dance/",
        extract_images=False,
        extract_links=False,
        word_count_threshold=5,
        headless=True,
        save_to_notion=False,
    )

    if not result.get("success"):
        print(f"❌ Scraping failed: {result.get('error')}")
        return

    content = result.get("content", {}).get("markdown", "")
    print(f"✅ Scraped {len(content)} characters")
    print(f"\n📄 Preview:\n{content[:500]}...\n")

    # Step 2: Extract event details using AI
    print("🤖 Step 2: Extracting event details with AI...")
    from mcp_ce.agents.extract_structured_data import extract_event_details

    event = await extract_event_details(
        text=content, url="https://www.bluesmuse.dance/"
    )

    print(f"✅ Extracted event: {event.title}")
    print(f"\n📋 Event Details:")
    print(f"  Date: {event.date}")
    print(f"  Time: {event.start_time} - {event.end_time}")
    print(f"  Location: {event.get_full_location()}")
    print(f"  Online: {event.is_online}")
    print(
        f"  Description: {event.description[:200] if event.description else 'N/A'}..."
    )

    # Step 3: Parse datetime for Discord
    print(f"\n⏰ Step 3: Parsing datetime for Discord...")
    start_dt, end_dt = event.get_datetime_for_discord()

    if start_dt:
        print(f"  Start: {start_dt.isoformat()}")
        print(f"  End: {end_dt.isoformat() if end_dt else 'N/A'}")
    else:
        print(f"  ⚠️ Could not parse datetime")

    # Step 4: Create Discord event
    if start_dt:
        print(f"\n📅 Step 4: Creating Discord event...")
        try:
            from mcp_ce.tools.discord._bot_helper import get_bot

            bot = get_bot()

            # Get first guild
            if not bot.guilds:
                print("❌ Bot is not in any servers")
                return

            guild = bot.guilds[0]
            print(f"  Using server: {guild.name}")

            # Create scheduled event
            location = event.get_full_location() or "See event details"
            if len(location) > 100:
                location = location[:97] + "..."

            description = (
                event.description[:950] + "..."
                if event.description and len(event.description) > 950
                else event.description
            )

            scheduled_event = await guild.create_scheduled_event(
                name=event.title[:100],
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                entity_type=discord.EntityType.external,
                location=location,
            )

            print(f"✅ Discord event created!")
            print(f"   ID: {scheduled_event.id}")
            print(f"   URL: {scheduled_event.url}")

        except Exception as e:
            print(f"❌ Failed to create Discord event: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("\n⚠️ Skipping Discord event creation - no valid datetime")

    print("\n🎉 Test complete!")


if __name__ == "__main__":
    asyncio.run(test_event_extraction())
