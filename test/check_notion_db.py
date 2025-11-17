import asyncio
import os
from notion_client import AsyncClient
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    notion_token = os.getenv('NOTION_TOKEN')
    assert notion_token, "NOTION_TOKEN environment variable not set."
    return AsyncClient(auth=notion_token)

client = _get_client()

async def get_data_source_id_from_database(database_id) -> str:
    """
    retrieves the datasource_id for a database entity
    as of 2025-09-03 update to Notion database_id and data_source_id are not synonymous
    """
    res = await client.request(
            path=f'databases/{database_id}',
            method='GET',
        )

    return res['data_sources'][0]['id']

async def check_database():
    """
    retrieves all pages from a Notion database
    """

    database_id = os.getenv('NOTION_DATABASE_ID')

    data_source_id = await get_data_source_id_from_database(database_id)
    all_pages = await client.request(
            path=f'data_sources/{data_source_id}/query',
            method='POST',
            body={}
        )

    try:
        results = all_pages.get("results", [])
        print(f'✅ Success! Found {len(results)} total pages\n')
        
        if results:
            first_page = results[0]
            print('📋 Available properties in pages:')
            for prop_name, prop_data in first_page.get('properties', {}).items():
                prop_type = prop_data.get('type', 'unknown')
                print(f'  - "{prop_name}" ({prop_type})')
            
            # Count matches for target URL
            target_url = 'https://www.youtube.com/watch?v=SJi469BuU6g'
            matches = []
            
            print(f'\n🔍 Searching for: {target_url}')
            
            for page in results:
                props = page.get('properties', {})
                print(props)
                for prop_name, prop_data in props.items():
                    if prop_data.get('type') == 'url':
                        url_value = prop_data.get('url', '')
                        if url_value == target_url:
                            matches.append(page)
                            lock_status = props.get('Lock', {}).get('checkbox', False)
                            page_id = page['id'][:8]
                            print(f'  ✅ Match in "{prop_name}" - Page: {page_id}... Lock: {lock_status}')
                            break
            
            print(f'\n🎯 Total matches found: {len(matches)}')
            
            if len(matches) > 1:
                print(f'\n⚠️  WARNING: {len(matches)} duplicate entries found!')
                print('   Consider deleting extras or locking the ones you want to keep.')
            
            return True
    except Exception as e:
        print(f'❌ Failed with data_sources endpoint: {e}\n')
    
    return False

asyncio.run(check_database())
