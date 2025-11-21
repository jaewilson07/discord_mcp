# Running the Tumblr Posts Table Migration

## Quick Method: Supabase Dashboard (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor** (left sidebar)
4. Click **New query**
5. Copy the entire contents of `docs/supabase/tumblr_feed_schema.sql`
6. Paste into the SQL editor
7. Click **Run** (or press Ctrl+Enter)

## Automated Method: Using psycopg2

If you have the direct Postgres connection string:

1. Set `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
   ```
   
   Or add to `.env`:
   ```
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   ```

2. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```

3. Run the migration script:
   ```bash
   python scripts/run_tumblr_schema_migration.py
   ```

## Getting the Database Connection String

From Supabase Dashboard:
1. Go to **Settings** → **Database**
2. Scroll to **Connection string**
3. Select **URI** format
4. Copy the connection string
5. Replace `[YOUR-PASSWORD]` with your actual database password

## Verify Migration

After running the migration, verify the table exists:

```sql
SELECT * FROM tumblr_posts LIMIT 1;
```

Or check table structure:

```sql
\d tumblr_posts
```

