-- Supabase Schema for Tumblr Feed Storage
-- This schema supports storing Tumblr posts with metadata for duplicate checking

-- Create tumblr_posts table
CREATE TABLE IF NOT EXISTS tumblr_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT NOT NULL UNIQUE,  -- Tumblr post ID (unique constraint for duplicate checking)
    post_type TEXT NOT NULL,  -- 'text', 'image', 'gif', 'reblog'
    content TEXT,  -- Post text content
    image_urls JSONB DEFAULT '[]'::jsonb,  -- Array of image/GIF URLs
    original_poster TEXT,  -- Username if reblogged
    post_url TEXT NOT NULL,  -- Full Tumblr post URL
    timestamp TIMESTAMPTZ,  -- Post timestamp from Tumblr
    tags JSONB DEFAULT '[]'::jsonb,  -- Array of tags
    likes INTEGER DEFAULT 0,
    reblogs INTEGER DEFAULT 0,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),  -- When we extracted this post
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on post_id for fast duplicate checking
CREATE INDEX IF NOT EXISTS idx_tumblr_posts_post_id ON tumblr_posts(post_id);

-- Create index on timestamp for sorting/querying
CREATE INDEX IF NOT EXISTS idx_tumblr_posts_timestamp ON tumblr_posts(timestamp DESC);

-- Create index on post_type for filtering
CREATE INDEX IF NOT EXISTS idx_tumblr_posts_post_type ON tumblr_posts(post_type);

-- Create index on extracted_at for sync tracking
CREATE INDEX IF NOT EXISTS idx_tumblr_posts_extracted_at ON tumblr_posts(extracted_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tumblr_posts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER tumblr_posts_updated_at
    BEFORE UPDATE ON tumblr_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_tumblr_posts_updated_at();

-- Enable Row Level Security (RLS) - adjust policies as needed
ALTER TABLE tumblr_posts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust based on your security needs)
-- For public read/write access:
CREATE POLICY "Allow all operations on tumblr_posts"
    ON tumblr_posts
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Or for authenticated users only:
-- CREATE POLICY "Allow authenticated users"
--     ON tumblr_posts
--     FOR ALL
--     TO authenticated
--     USING (true)
--     WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE tumblr_posts IS 'Stores Tumblr posts scraped from feeds';
COMMENT ON COLUMN tumblr_posts.post_id IS 'Unique Tumblr post identifier for duplicate checking';
COMMENT ON COLUMN tumblr_posts.post_type IS 'Type of post: text, image, gif, or reblog';
COMMENT ON COLUMN tumblr_posts.image_urls IS 'JSON array of image/GIF URLs';
COMMENT ON COLUMN tumblr_posts.tags IS 'JSON array of post tags';
COMMENT ON COLUMN tumblr_posts.timestamp IS 'Original post timestamp from Tumblr';
COMMENT ON COLUMN tumblr_posts.extracted_at IS 'When this post was extracted by our scraper';

