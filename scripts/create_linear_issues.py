"""
Script to create Linear issues for Tumblr Feed Workflow project.

This script uses the Linear API to create all issues for the project.
Requires LINEAR_API_KEY environment variable.

Usage:
    python scripts/create_linear_issues.py
"""

import os
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: uv add httpx")
    sys.exit(1)


LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
if not LINEAR_API_KEY:
    print("❌ LINEAR_API_KEY environment variable not set")
    print("   Get your API key from: https://linear.app/settings/api")
    sys.exit(1)

LINEAR_API_URL = "https://api.linear.app/graphql"
HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}


def get_team_id(team_key: str) -> Optional[str]:
    """Get team ID from team key."""
    query = """
    query {
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
    """

    response = httpx.post(
        LINEAR_API_URL,
        headers=HEADERS,
        json={"query": query},
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch teams: {response.status_code}")
        return None

    data = response.json()
    teams = data.get("data", {}).get("teams", {}).get("nodes", [])

    for team in teams:
        if team.get("key") == team_key:
            return team["id"]

    print(f"❌ Team '{team_key}' not found")
    print(f"   Available teams: {[t.get('key') for t in teams]}")
    return None


def create_issue(
    team_id: str,
    title: str,
    description: str,
    priority: int = 3,  # 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
    estimate: Optional[int] = None,
    labels: Optional[List[str]] = None,
    epic_id: Optional[str] = None,
) -> Optional[str]:
    """Create a Linear issue."""
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
        }
      }
    }
    """

    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
    }

    if estimate:
        variables["input"]["estimate"] = estimate

    if labels:
        # Get label IDs (would need separate query)
        # For now, skip labels
        pass

    if epic_id:
        variables["input"]["parentId"] = epic_id

    response = httpx.post(
        LINEAR_API_URL,
        headers=HEADERS,
        json={"query": mutation, "variables": variables},
    )

    if response.status_code != 200:
        print(f"❌ Failed to create issue '{title}': {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    data = response.json()
    if data.get("errors"):
        print(f"❌ Error creating issue '{title}': {data['errors']}")
        return None

    issue = data.get("data", {}).get("issueCreate", {}).get("issue")
    if issue:
        print(f"✅ Created: {issue['identifier']} - {issue['title']}")
        return issue["id"]

    return None


def create_epic(team_id: str, title: str, description: str) -> Optional[str]:
    """Create a Linear epic."""
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
        }
      }
    }
    """

    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": 2,  # High priority for epic
        }
    }

    response = httpx.post(
        LINEAR_API_URL,
        headers=HEADERS,
        json={"query": mutation, "variables": variables},
    )

    if response.status_code != 200:
        print(f"❌ Failed to create epic: {response.status_code}")
        return None

    data = response.json()
    if data.get("errors"):
        print(f"❌ Error creating epic: {data['errors']}")
        return None

    issue = data.get("data", {}).get("issueCreate", {}).get("issue")
    if issue:
        print(f"✅ Created Epic: {issue['identifier']} - {issue['title']}")
        return issue["id"]

    return None


# Issue definitions
ISSUES = [
    {
        "title": "Set up Supabase storage schema",
        "description": """Create Supabase table/source for Tumblr posts.

**Tasks:**
- Create Supabase source "tumblr_feed"
- Define document schema with metadata fields
- Set up indexes for post_id lookups

**Acceptance Criteria:**
- [ ] Supabase source "tumblr_feed" created
- [ ] Schema supports: post_id, post_type, content, image_urls, original_poster, post_url, timestamp, tags
- [ ] Can query by post_id for duplicate checking""",
        "priority": 2,  # High
        "estimate": 3,
        "phase": "Phase 1: Foundation & Setup",
    },
    {
        "title": "Create Tumblr post extraction schema",
        "description": """Register Pydantic schema for Tumblr post extraction.

**Tasks:**
- Define fields: post_id, post_type, content, image_urls, original_poster, post_url, timestamp, tags, likes, reblogs
- Register schema in agent registry
- Test extraction agent with sample content

**Acceptance Criteria:**
- [ ] Extraction schema registered in agent registry
- [ ] Can extract structured posts from markdown content
- [ ] Handles text, image, GIF, and reblog post types""",
        "priority": 2,  # High
        "estimate": 5,
        "phase": "Phase 1: Foundation & Setup",
    },
    {
        "title": "Test Tumblr feed scraping",
        "description": """Test crawl_website tool on Tumblr feed URL.

**Tasks:**
- Test crawl_website tool on Tumblr feed URL
- Verify image extraction works
- Test JavaScript scrolling for lazy-loaded content
- Identify correct CSS selectors for posts

**Acceptance Criteria:**
- [ ] Can successfully scrape Tumblr feed
- [ ] Images/GIFs are extracted
- [ ] Post content is captured in markdown
- [ ] Lazy-loaded content loads properly""",
        "priority": 3,  # Medium
        "estimate": 3,
        "phase": "Phase 1: Foundation & Setup",
    },
    {
        "title": "Implement sync_tumblr_feed workflow function",
        "description": """Create main workflow function in sync_tumblr_feed.py.

**Tasks:**
- Implement step-by-step workflow:
  1. Scrape Tumblr feed
  2. Extract posts using agent
  3. Check duplicates in Supabase
  4. Store new posts
  5. Post to Discord
- Add error handling and logging

**Acceptance Criteria:**
- [ ] Workflow function implemented
- [ ] All 5 steps execute in sequence
- [ ] Error handling for each step
- [ ] Returns structured results dict""",
        "priority": 2,  # High
        "estimate": 8,
        "phase": "Phase 2: Core Workflow Implementation",
    },
    {
        "title": "Implement duplicate checking logic",
        "description": """Query Supabase by post_id before storing.

**Tasks:**
- Query Supabase by post_id before storing
- Skip posts that already exist
- Track sync timestamp for incremental updates

**Acceptance Criteria:**
- [ ] Duplicate posts are detected
- [ ] Only new posts are stored and posted
- [ ] Last sync timestamp tracked""",
        "priority": 2,  # High
        "estimate": 3,
        "phase": "Phase 2: Core Workflow Implementation",
    },
    {
        "title": "Implement Discord posting with formatting",
        "description": """Format Tumblr posts for Discord messages.

**Tasks:**
- Format Tumblr posts for Discord messages
- Handle different post types (text, image, GIF, reblog)
- Include attribution for reblogs
- Add tags and post URL
- Handle image attachments

**Acceptance Criteria:**
- [ ] Text posts formatted correctly
- [ ] Images/GIFs included in messages
- [ ] Reblog attribution shown
- [ ] Tags and links included""",
        "priority": 3,  # Medium
        "estimate": 5,
        "phase": "Phase 2: Core Workflow Implementation",
    },
    {
        "title": "End-to-end workflow testing",
        "description": """Test complete workflow from scraping to Discord posting.

**Tasks:**
- Test complete workflow from scraping to Discord posting
- Test with real Tumblr feed
- Verify duplicate detection works
- Test error scenarios

**Acceptance Criteria:**
- [ ] Complete workflow runs successfully
- [ ] Posts appear in Discord channel
- [ ] Duplicates are skipped
- [ ] Error handling works correctly""",
        "priority": 2,  # High
        "estimate": 5,
        "phase": "Phase 3: Testing & Refinement",
    },
    {
        "title": "Add rate limiting and error recovery",
        "description": """Add delays between Discord posts to avoid rate limits.

**Tasks:**
- Add delays between Discord posts to avoid rate limits
- Implement retry logic for failed operations
- Add exponential backoff for API errors

**Acceptance Criteria:**
- [ ] Rate limiting prevents Discord API errors
- [ ] Failed operations retry with backoff
- [ ] Errors are logged and reported""",
        "priority": 3,  # Medium
        "estimate": 3,
        "phase": "Phase 3: Testing & Refinement",
    },
    {
        "title": "Optimize extraction for Tumblr-specific content",
        "description": """Fine-tune extraction agent prompts for Tumblr posts.

**Tasks:**
- Fine-tune extraction agent prompts for Tumblr posts
- Improve detection of post types
- Better handling of reblog chains
- Extract engagement metrics if available

**Acceptance Criteria:**
- [ ] Post type detection is accurate
- [ ] Reblog attribution is correct
- [ ] Engagement metrics extracted when available""",
        "priority": 4,  # Low
        "estimate": 5,
        "phase": "Phase 3: Testing & Refinement",
    },
    {
        "title": "Implement scheduling mechanism",
        "description": """Create periodic sync function.

**Tasks:**
- Create periodic sync function
- Options: cron job, Discord bot command, or asyncio periodic task
- Add configuration for sync interval

**Acceptance Criteria:**
- [ ] Can run sync on schedule
- [ ] Configurable sync interval
- [ ] Can be triggered manually via Discord command""",
        "priority": 3,  # Medium
        "estimate": 5,
        "phase": "Phase 4: Scheduling & Automation",
    },
    {
        "title": "Add Discord bot command for manual sync",
        "description": """Create !sync_tumblr Discord command.

**Tasks:**
- Create !sync_tumblr Discord command
- Allow specifying channel ID
- Show sync results in Discord

**Acceptance Criteria:**
- [ ] Command triggers sync workflow
- [ ] Results posted to Discord
- [ ] Error messages shown if sync fails""",
        "priority": 4,  # Low
        "estimate": 3,
        "phase": "Phase 4: Scheduling & Automation",
    },
    {
        "title": "Add monitoring and logging",
        "description": """Add structured logging for sync operations.

**Tasks:**
- Add structured logging for sync operations
- Track sync statistics (posts scraped, posted, errors)
- Store sync history in Supabase

**Acceptance Criteria:**
- [ ] Sync operations are logged
- [ ] Statistics tracked and queryable
- [ ] Sync history stored""",
        "priority": 4,  # Low
        "estimate": 3,
        "phase": "Phase 4: Scheduling & Automation",
    },
    {
        "title": "Create user documentation",
        "description": """Document workflow usage.

**Tasks:**
- Document workflow usage
- Add configuration examples
- Create troubleshooting guide

**Acceptance Criteria:**
- [ ] README updated with workflow docs
- [ ] Configuration examples provided
- [ ] Troubleshooting guide created""",
        "priority": 4,  # Low
        "estimate": 2,
        "phase": "Phase 5: Documentation & Polish",
    },
    {
        "title": "Add workflow to MCP tool registry",
        "description": """Register workflow as MCP tool if needed.

**Tasks:**
- Register workflow as MCP tool if needed
- Add to runtime tool docs
- Make accessible via MCP protocol

**Acceptance Criteria:**
- [ ] Workflow accessible via MCP
- [ ] Tool documentation updated
- [ ] Can be called via MCP client""",
        "priority": 4,  # Low
        "estimate": 3,
        "phase": "Phase 5: Documentation & Polish",
    },
]


def main():
    """Main function to create Linear issues."""
    print("🚀 Creating Linear issues for Tumblr Feed Workflow project\n")

    # Get team key from user
    team_key = input("Enter your Linear team key (e.g., 'ENG'): ").strip()
    if not team_key:
        print("❌ Team key is required")
        return

    # Get team ID
    print(f"\n📋 Fetching team information...")
    team_id = get_team_id(team_key)
    if not team_id:
        return

    # Create epic
    print(f"\n📦 Creating epic...")
    epic_id = create_epic(
        team_id=team_id,
        title="Tumblr Feed Workflow Implementation",
        description="""Complete workflow for scraping, storing, and posting Tumblr content to Discord.

**Project:** Recreate Tumblr feed (soyeahbluesdance) in Discord
**Target URL:** https://www.tumblr.com/soyeahbluesdance

**Workflow Steps:**
1. Scrape Tumblr feed
2. Extract posts (images, GIFs, text, reblogs)
3. Store posts in Supabase
4. Post to Discord channels
5. Run on schedule to check for new content""",
    )

    if not epic_id:
        print("⚠️  Continuing without epic...")

    # Create issues
    print(f"\n📝 Creating {len(ISSUES)} issues...\n")

    created_count = 0
    for issue_data in ISSUES:
        issue_id = create_issue(
            team_id=team_id,
            title=issue_data["title"],
            description=f"**{issue_data['phase']}**\n\n{issue_data['description']}",
            priority=issue_data["priority"],
            estimate=issue_data["estimate"],
            epic_id=epic_id,
        )
        if issue_id:
            created_count += 1

    print(f"\n✅ Created {created_count}/{len(ISSUES)} issues")
    if epic_id:
        print(f"📦 Epic created: {epic_id}")
    print(f"\n🎉 Done! Check your Linear workspace to see the issues.")


if __name__ == "__main__":
    main()
