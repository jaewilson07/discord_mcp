"""
Complete test: Extract event from website and create Discord event
"""

import asyncio
import os


async def extract_and_create_discord_event():
    """
    Complete workflow:
    1. Smart extract event from URL (with cache + deep crawl)
    2. Create Discord event
    3. Save to Notion
    """
    
    url = "https://www.bluesmuse.dance/"
    
    print("🎯 Complete Event Workflow Test")
    print(f"URL: {url}\n")
    
    # Step 1: Smart extraction with quality control
    print("="*60)
    print("STEP 1: Smart Event Extraction")
    print("="*60)
    
    from mcp_ce.tools.events.smart_extract import smart_extract_event
    
    try:
        event, metadata = await smart_extract_event(
            url=url,
            force_refresh=False,  # Use cache if available
            max_cache_age_hours=24,
            quality_threshold=0.7,
            max_optimization_iterations=2,
            enable_deep_crawl=False,  # Disable for now (needs playwright)
            max_deep_crawl_depth=2
        )
        
        print(f"\n✅ Extraction Complete!")
        print(f"   Event: {event.title}")
        print(f"   Date: {event.date}")
        print(f"   Time: {event.start_time} - {event.end_time}")
        print(f"   Location: {event.get_full_location()}")
        print(f"   Quality: {metadata['quality_score']['overall']:.2f}")
        print(f"   Cache hit: {metadata['cache_hit']}")
        print(f"   Deep crawled: {metadata['deep_crawled']}")
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Save to Notion
    print(f"\n{'='*60}")
    print("STEP 2: Save to Notion")
    print("="*60)
    
    try:
        from mcp_ce.tools.notion._client_helper import (
            get_data_source_id_from_database,
            query_data_source,
            create_page,
            update_page,
            delete_all_blocks,
            append_blocks
        )
        from notion_blockify import Blockizer
        from datetime import datetime
        
        notion_database_id = os.getenv("NOTION_DATABASE_ID")
        if not notion_database_id:
            print("   ⚠️ NOTION_DATABASE_ID not configured")
        else:
            # Get data source
            data_source_id = await get_data_source_id_from_database(notion_database_id)
            
            # Check for existing
            existing = await query_data_source(
                data_source_id,
                filter_obj={
                    "property": "URL",
                    "url": {"equals": url}
                }
            )
            
            # Prepare content
            blockizer = Blockizer()
            
            content_md = f"""## 📅 Event Details

**Date**: {event.date or 'TBD'}
**Time**: {event.start_time or 'TBD'} - {event.end_time or 'TBD'}
**Location**: {event.get_full_location() or 'TBD'}

## 📝 Description

{event.description or 'No description available'}

## 🎫 Event Info

**Organizer**: {event.organizer or 'N/A'}
**Price**: {event.price or 'N/A'}
**Category**: {event.category or 'N/A'}

## 🔍 Quality Metrics

**Overall Score**: {metadata['quality_score']['overall']:.2f}
**Completeness**: {metadata['quality_score']['completeness']:.2f}
**Accuracy**: {metadata['quality_score']['accuracy']:.2f}
**Confidence**: {metadata['quality_score']['confidence']:.2f}
"""
            
            blocks = blockizer.convert(content_md)
            
            # Properties
            properties = {
                "Name": {
                    "title": [{"text": {"content": event.title[:100]}}]
                },
                "URL": {
                    "url": url
                },
                "Status": {
                    "select": {"name": "Event"}
                },
                "Scrape Date": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
            
            existing_pages = existing.get("results", [])
            
            if existing_pages:
                existing_page = existing_pages[0]
                page_id = existing_page["id"]
                lock_status = existing_page.get("properties", {}).get("Lock", {}).get("checkbox", False)
                
                if not lock_status:
                    # Update
                    await update_page(page_id, properties)
                    await delete_all_blocks(page_id)
                    for i in range(0, len(blocks), 100):
                        chunk = blocks[i:i + 100]
                        await append_blocks(page_id, chunk)
                    print(f"   ✅ Updated Notion page: {page_id}")
                else:
                    # Create new (locked)
                    initial_blocks = blocks[:100]
                    remaining = blocks[100:]
                    created = await create_page(notion_database_id, properties, initial_blocks)
                    page_id = created["id"]
                    for i in range(0, len(remaining), 100):
                        await append_blocks(page_id, remaining[i:i + 100])
                    print(f"   ✅ Created new Notion page (locked): {page_id}")
            else:
                # Create new
                initial_blocks = blocks[:100]
                remaining = blocks[100:]
                created = await create_page(notion_database_id, properties, initial_blocks)
                page_id = created["id"]
                for i in range(0, len(remaining), 100):
                    await append_blocks(page_id, remaining[i:i + 100])
                print(f"   ✅ Created Notion page: {page_id}")
                
    except Exception as e:
        print(f"   ⚠️ Notion save failed: {e}")
    
    # Step 3: Create Discord event
    print(f"\n{'='*60}")
    print("STEP 3: Create Discord Event")
    print("="*60)
    
    try:
        from mcp_ce.tools.discord._bot_helper import get_bot, is_bot_ready
        
        if not is_bot_ready():
            print("   ⚠️ Discord bot not running")
            print("   ℹ️ Start the bot first to create Discord events")
            print("\nEvent data that would be created:")
            print(f"   Name: {event.title[:100]}")
            
            start_dt, end_dt = event.get_datetime_for_discord()
            if start_dt:
                print(f"   Start: {start_dt.isoformat()}")
                print(f"   End: {end_dt.isoformat() if end_dt else 'N/A'}")
            else:
                print(f"   ⚠️ Could not parse datetime")
            
            location = event.get_full_location() or "See event details"
            if len(location) > 100:
                location = location[:97] + "..."
            print(f"   Location: {location}")
            
            description_parts = []
            if event.organizer:
                description_parts.append(f"Host: {event.organizer}")
            if event.price:
                description_parts.append(f"Price: {event.price}")
            if event.description:
                desc = event.description[:200]
                description_parts.append(desc)
            
            description = "\n\n".join(description_parts) if description_parts else None
            print(f"   Description: {description[:100] if description else 'N/A'}...")
            
        else:
            bot = get_bot()
            
            if not bot.guilds:
                print("   ❌ Bot is not in any servers")
                return
            
            guild = bot.guilds[0]
            print(f"   Using server: {guild.name}")
            
            # Parse datetime
            start_dt, end_dt = event.get_datetime_for_discord()
            
            if start_dt:
                # Prepare event details
                location = event.get_full_location() or "See event details"
                if len(location) > 100:
                    location = location[:97] + "..."
                
                description_parts = []
                if event.organizer:
                    description_parts.append(f"Host: {event.organizer}")
                if event.price:
                    description_parts.append(f"Price: {event.price}")
                if event.description:
                    desc = event.description[:900] if len(event.description) > 900 else event.description
                    description_parts.append(desc)
                
                description = "\n\n".join(description_parts) if description_parts else None
                
                # Create event
                import discord
                scheduled_event = await guild.create_scheduled_event(
                    name=event.title[:100],
                    start_time=start_dt,
                    end_time=end_dt,
                    description=description,
                    entity_type=discord.EntityType.external,
                    location=location
                )
                
                print(f"   ✅ Discord event created!")
                print(f"   ID: {scheduled_event.id}")
                print(f"   URL: {scheduled_event.url}")
            else:
                print(f"   ⚠️ Could not parse event date/time")
                
    except Exception as e:
        print(f"   ❌ Discord event creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ Workflow Complete!")
    print("="*60)
    print(f"\nFinal Summary:")
    print(f"  Event: {event.title}")
    print(f"  Date: {event.date}")
    print(f"  Location: {event.get_full_location()}")
    print(f"  Quality Score: {metadata['quality_score']['overall']:.2f}")
    print(f"  Cached: {metadata['cache_hit']}")
    print(f"  Deep Crawled: {metadata['deep_crawled']}")
    print(f"  Pages Crawled: {metadata['pages_crawled']}")


if __name__ == "__main__":
    asyncio.run(extract_and_create_discord_event())
