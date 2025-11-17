# Notion Integration Setup for YouTube Analysis Agent

This guide explains how to set up Notion to receive YouTube video analysis exports.

## Prerequisites

- A Notion account
- The `notion-client` Python package (already installed)

## Step 1: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Name it "YouTube Video Analyzer" (or any name you prefer)
4. Select the workspace where you want to use it
5. Click "Submit"
6. Copy the **Internal Integration Token** (starts with `secret_`)
7. Save this as `NOTION_TOKEN` in your `.env` file

## Step 2: Create a Notion Database

1. Open Notion and create a new page
2. Add a **Database - Full page**
3. Name it "YouTube Video Analysis" (or any name you prefer)
4. Add the following properties to your database:

### Required Properties

| Property Name | Property Type | Description |
|--------------|---------------|-------------|
| **Name** | Title | Video title (auto-created) |
| **URL** | URL | YouTube video URL (used as unique ID for duplicate detection) |
| **Video ID** | Text | YouTube video ID |
| **Analysis Depth** | Select | "summary" or "detailed" |
| **Status** | Select | "Analyzed", "Updated", "Pending", etc. |
| **Lock** | Checkbox | Prevent automatic updates (check to protect manual edits) |

### Property Setup Instructions

1. Click the **"..."** menu at the top right of the database
2. Click **"+ New property"** for each property
3. Set the property name and type as specified above
4. For **Select** properties, add the options:
   - Analysis Depth: "summary", "detailed"
   - Status: "Analyzed", "Updated", "Pending", "Error"
5. For **Checkbox** property (Lock):
   - Just create it with the name "Lock"
   - Leave it unchecked by default

## Step 3: Share Database with Integration

1. Click the **"..."** menu at the top right of your database page
2. Scroll down and click **"Connections"** or **"Add connections"**
3. Find and select your "YouTube Video Analyzer" integration
4. Click **"Confirm"**

## Step 4: Get Database ID

1. Open your database as a full page in Notion
2. Look at the URL in your browser:
   ```
   https://www.notion.so/[workspace-name]/[DATABASE_ID]?v=...
   ```
3. Copy the **DATABASE_ID** (it's a 32-character string with hyphens)
4. Save this as `NOTION_DATABASE_ID` in your `.env` file

## Step 5: Configure Environment Variables

Add these to your `.env` file in the project root:

```env
# Notion Configuration
NOTION_TOKEN=secret_your_integration_token_here
NOTION_DATABASE_ID=your_database_id_here

# YouTube API (if not already set)
YOUTUBE_API_KEY=your_youtube_api_key_here

# OpenAI API (if not already set)
OPENAI_API_KEY=your_openai_api_key_here
```

## What Gets Exported

When a video is analyzed, the agent creates a Notion page with:

1. **Title**: Video title from YouTube
2. **Properties**:
   - Video URL (for duplicate detection)
   - Video ID
   - Analysis Depth
   - Status: "Analyzed"
3. **Page Content**:
   - **Embedded Video**: YouTube video player embedded in the page
   - **Video Information**: Metadata (title, channel, views, etc.)
   - **Key Findings**: AI-extracted insights
   - **Full Transcript**: Complete transcript with paragraph formatting

## UPSERT Behavior (Smart Updates)

The agent implements intelligent update logic:

### When a Video Already Exists:
1. **If Lock is UNCHECKED (default)**:
   - ✅ The page will be **UPDATED** with the latest analysis
   - Status changes to "Updated"
   - All content is refreshed with new data
   - Perfect for re-analyzing videos with better prompts

2. **If Lock is CHECKED**:
   - 🔒 The existing page is **PROTECTED** from updates
   - A **NEW PAGE** is created instead
   - Useful if you've made manual edits you want to preserve
   - Both versions will exist in the database

### Best Practices:
- Leave **Lock unchecked** for most videos (allows improvements)
- **Check Lock** if you've manually edited the page and want to keep your changes
- Status will show "Analyzed" for new pages, "Updated" for refreshed pages

## Duplicate Detection

## Testing

Run the YouTube analysis agent:

```bash
python src\mcp_ce\agents\youtube_analysis_agent.py
```

If configured correctly, you should see:
```
✅ Success: Exported to Notion - https://notion.so/...
```

## Troubleshooting

### "NOTION_TOKEN or NOTION_DATABASE_ID not configured"
- Check your `.env` file has both variables set
- Ensure `.env` is in the project root directory
- Try restarting your terminal/IDE

### "Could not find database"
- Verify the DATABASE_ID is correct (32 characters with hyphens)
- Ensure the integration is connected to the database (Step 3)
- Check you're using the database ID, not the page ID

### "Property does not exist"
- Verify all required properties are created in your database
- Property names must match exactly (case-sensitive)
- Property types must match (URL, Text, Select)

### "Unauthorized"
- Verify your NOTION_TOKEN is correct and starts with `secret_`
- Regenerate the integration token if needed
- Ensure the integration has been shared with the database

## Optional: Custom Database Views

You can create custom views in Notion to organize your analyzed videos:

- **By Status**: Filter by "Analyzed", "Pending", etc.
- **By Analysis Depth**: Group by "summary" or "detailed"
- **Recent**: Sort by "Created time" descending
- **Gallery View**: Show video thumbnails (if available)

## Example Database

Here's what your final database might look like:

| Name | Video URL | Video ID | Analysis Depth | Status |
|------|-----------|----------|----------------|--------|
| 30 PROVEN Discord Hacks | https://youtube.com/... | SJi469BuU6g | detailed | Analyzed |
| Building Communities | https://youtube.com/... | abc123XYZ | summary | Analyzed |
