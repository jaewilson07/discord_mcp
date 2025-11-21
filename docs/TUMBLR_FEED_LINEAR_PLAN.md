# Tumblr Feed Workflow - Linear Project Plan

This document outlines the Linear issues needed to track the Tumblr feed recreation project.

## Project Overview

**Project Name:** Tumblr Feed Recreation  
**Description:** Create a workflow that scrapes, extracts, stores, and posts Tumblr feed content to Discord  
**Target URL:** https://www.tumblr.com/soyeahbluesdance

## Linear Issues Breakdown

### Epic: Tumblr Feed Workflow Implementation

#### Phase 1: Foundation & Setup

**Issue 1: Set up Supabase storage schema**
- **Type:** Task
- **Priority:** High
- **Description:**
  - Create Supabase table/source for Tumblr posts
  - Define document schema with metadata fields
  - Set up indexes for post_id lookups
- **Acceptance Criteria:**
  - [ ] Supabase source "tumblr_feed" created
  - [ ] Schema supports: post_id, post_type, content, image_urls, original_poster, post_url, timestamp, tags
  - [ ] Can query by post_id for duplicate checking
- **Estimated Points:** 3

**Issue 2: Create Tumblr post extraction schema**
- **Type:** Task
- **Priority:** High
- **Description:**
  - Register Pydantic schema for Tumblr post extraction
  - Define fields: post_id, post_type, content, image_urls, original_poster, post_url, timestamp, tags, likes, reblogs
  - Test extraction agent with sample content
- **Acceptance Criteria:**
  - [ ] Extraction schema registered in agent registry
  - [ ] Can extract structured posts from markdown content
  - [ ] Handles text, image, GIF, and reblog post types
- **Estimated Points:** 5

**Issue 3: Test Tumblr feed scraping**
- **Type:** Task
- **Priority:** Medium
- **Description:**
  - Test crawl_website tool on Tumblr feed URL
  - Verify image extraction works
  - Test JavaScript scrolling for lazy-loaded content
  - Identify correct CSS selectors for posts
- **Acceptance Criteria:**
  - [ ] Can successfully scrape Tumblr feed
  - [ ] Images/GIFs are extracted
  - [ ] Post content is captured in markdown
  - [ ] Lazy-loaded content loads properly
- **Estimated Points:** 3

#### Phase 2: Core Workflow Implementation

**Issue 4: Implement sync_tumblr_feed workflow function**
- **Type:** Task
- **Priority:** High
- **Description:**
  - Create main workflow function in `sync_tumblr_feed.py`
  - Implement step-by-step workflow:
    1. Scrape Tumblr feed
    2. Extract posts using agent
    3. Check duplicates in Supabase
    4. Store new posts
    5. Post to Discord
  - Add error handling and logging
- **Acceptance Criteria:**
  - [ ] Workflow function implemented
  - [ ] All 5 steps execute in sequence
  - [ ] Error handling for each step
  - [ ] Returns structured results dict
- **Estimated Points:** 8

**Issue 5: Implement duplicate checking logic**
- **Type:** Task
- **Priority:** High
- **Description:**
  - Query Supabase by post_id before storing
  - Skip posts that already exist
  - Track sync timestamp for incremental updates
- **Acceptance Criteria:**
  - [ ] Duplicate posts are detected
  - [ ] Only new posts are stored and posted
  - [ ] Last sync timestamp tracked
- **Estimated Points:** 3

**Issue 6: Implement Discord posting with formatting**
- **Type:** Task
- **Priority:** Medium
- **Description:**
  - Format Tumblr posts for Discord messages
  - Handle different post types (text, image, GIF, reblog)
  - Include attribution for reblogs
  - Add tags and post URL
  - Handle image attachments
- **Acceptance Criteria:**
  - [ ] Text posts formatted correctly
  - [ ] Images/GIFs included in messages
  - [ ] Reblog attribution shown
  - [ ] Tags and links included
- **Estimated Points:** 5

#### Phase 3: Testing & Refinement

**Issue 7: End-to-end workflow testing**
- **Type:** Task
- **Priority:** High
- **Description:**
  - Test complete workflow from scraping to Discord posting
  - Test with real Tumblr feed
  - Verify duplicate detection works
  - Test error scenarios
- **Acceptance Criteria:**
  - [ ] Complete workflow runs successfully
  - [ ] Posts appear in Discord channel
  - [ ] Duplicates are skipped
  - [ ] Error handling works correctly
- **Estimated Points:** 5

**Issue 8: Add rate limiting and error recovery**
- **Type:** Task
- **Priority:** Medium
- **Description:**
  - Add delays between Discord posts to avoid rate limits
  - Implement retry logic for failed operations
  - Add exponential backoff for API errors
- **Acceptance Criteria:**
  - [ ] Rate limiting prevents Discord API errors
  - [ ] Failed operations retry with backoff
  - [ ] Errors are logged and reported
- **Estimated Points:** 3

**Issue 9: Optimize extraction for Tumblr-specific content**
- **Type:** Task
- **Priority:** Low
- **Description:**
  - Fine-tune extraction agent prompts for Tumblr posts
  - Improve detection of post types
  - Better handling of reblog chains
  - Extract engagement metrics if available
- **Acceptance Criteria:**
  - [ ] Post type detection is accurate
  - [ ] Reblog attribution is correct
  - [ ] Engagement metrics extracted when available
- **Estimated Points:** 5

#### Phase 4: Scheduling & Automation

**Issue 10: Implement scheduling mechanism**
- **Type:** Task
- **Priority:** Medium
- **Description:**
  - Create periodic sync function
  - Options: cron job, Discord bot command, or asyncio periodic task
  - Add configuration for sync interval
- **Acceptance Criteria:**
  - [ ] Can run sync on schedule
  - [ ] Configurable sync interval
  - [ ] Can be triggered manually via Discord command
- **Estimated Points:** 5

**Issue 11: Add Discord bot command for manual sync**
- **Type:** Task
- **Priority:** Low
- **Description:**
  - Create `!sync_tumblr` Discord command
  - Allow specifying channel ID
  - Show sync results in Discord
- **Acceptance Criteria:**
  - [ ] Command triggers sync workflow
  - [ ] Results posted to Discord
  - [ ] Error messages shown if sync fails
- **Estimated Points:** 3

**Issue 12: Add monitoring and logging**
- **Type:** Task
- **Priority:** Low
- **Description:**
  - Add structured logging for sync operations
  - Track sync statistics (posts scraped, posted, errors)
  - Store sync history in Supabase
- **Acceptance Criteria:**
  - [ ] Sync operations are logged
  - [ ] Statistics tracked and queryable
  - [ ] Sync history stored
- **Estimated Points:** 3

#### Phase 5: Documentation & Polish

**Issue 13: Create user documentation**
- **Type:** Task
- **Priority:** Low
- **Description:**
  - Document workflow usage
  - Add configuration examples
  - Create troubleshooting guide
- **Acceptance Criteria:**
  - [ ] README updated with workflow docs
  - [ ] Configuration examples provided
  - [ ] Troubleshooting guide created
- **Estimated Points:** 2

**Issue 14: Add workflow to MCP tool registry**
- **Type:** Task
- **Priority:** Low
- **Description:**
  - Register workflow as MCP tool if needed
  - Add to runtime tool docs
  - Make accessible via MCP protocol
- **Acceptance Criteria:**
  - [ ] Workflow accessible via MCP
  - [ ] Tool documentation updated
  - [ ] Can be called via MCP client
- **Estimated Points:** 3

## Linear Project Setup

### Create Project in Linear

1. **Create Project:**
   - Name: "Tumblr Feed Workflow"
   - Description: "Recreate Tumblr feed (soyeahbluesdance) in Discord"
   - Team: [Your team]

2. **Create Epic:**
   - Title: "Tumblr Feed Workflow Implementation"
   - Description: "Complete workflow for scraping, storing, and posting Tumblr content to Discord"

3. **Create Issues:**
   - Use the issues above as templates
   - Link all issues to the Epic
   - Set appropriate priorities and estimates
   - Assign to team members

### Labels to Create

- `tumblr-feed` - All issues related to this project
- `phase-1-foundation` - Foundation & Setup phase
- `phase-2-core` - Core Implementation phase
- `phase-3-testing` - Testing & Refinement phase
- `phase-4-automation` - Scheduling & Automation phase
- `phase-5-docs` - Documentation & Polish phase

### Milestones

- **Milestone 1: Foundation Complete** (Issues 1-3)
- **Milestone 2: Core Workflow** (Issues 4-6)
- **Milestone 3: Testing Complete** (Issues 7-9)
- **Milestone 4: Production Ready** (Issues 10-12)
- **Milestone 5: Documentation Complete** (Issues 13-14)

## Quick Start: Create Issues in Linear

You can use the Linear MCP server in Cursor to create these issues:

1. **Enable Linear MCP** (if not already):
   - Ensure `LINEAR_API_KEY` is set in your environment
   - Linear MCP server should be configured in Cursor

2. **Create Issues via Chat:**
   - "Create a Linear issue: Set up Supabase storage schema for Tumblr feed project"
   - "Create a Linear issue: Implement sync_tumblr_feed workflow function"
   - etc.

3. **Or use the script below** to create all issues programmatically

## Next Steps

1. Create the Linear project and epic
2. Create issues from the list above
3. Start with Phase 1 issues (Foundation & Setup)
4. Track progress as you implement each issue
5. Update issues with progress and blockers

