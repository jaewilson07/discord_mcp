#!/usr/bin/env python3
"""
Run the Tumblr posts table migration in Supabase.

This script creates the tumblr_posts table and all necessary indexes.
Uses psycopg2 to connect directly to the Postgres database.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent.parent


def read_sql_file(file_path: Path) -> str:
    """Read SQL file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def run_migration():
    """Run the SQL migration using psycopg2."""
    print("=" * 70)
    print("Running Tumblr Posts Table Migration")
    print("=" * 70)
    print()
    
    # Read SQL migration file
    sql_file = project_root / "docs" / "supabase" / "tumblr_feed_schema.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)
    
    print(f"📄 Reading SQL file: {sql_file}")
    sql_content = read_sql_file(sql_file)
    
    # Get database connection string from Supabase URL
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL not set in environment")
        print_manual_instructions(sql_content)
        sys.exit(1)
    
    # Extract database connection info from Supabase URL
    # Supabase URL format: https://[project-ref].supabase.co
    # We need the direct Postgres connection string
    # Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    
    db_url = os.getenv("DATABASE_URL")  # Direct Postgres connection string
    
    if not db_url:
        # Try to construct for local Supabase (common development setup)
        if "127.0.0.1" in supabase_url or "localhost" in supabase_url:
            print("🔍 Detected local Supabase instance")
            print("   Trying default local connection...")
            
            # Local Supabase default Postgres connection
            # API runs on 54321, Postgres direct on 54322
            db_password = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
            db_url = f"postgresql://postgres:{db_password}@127.0.0.1:54322/postgres"
            print(f"   Using: postgresql://postgres:***@127.0.0.1:54322/postgres")
        else:
            print("⚠️  DATABASE_URL not set.")
            print()
            print("To run this migration automatically, you need:")
            print("1. DATABASE_URL environment variable with Postgres connection string")
            print("   Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres")
            print()
            print("   Or get it from Supabase Dashboard:")
            print("   Settings → Database → Connection string → URI")
            print()
            print_manual_instructions(sql_content)
            sys.exit(0)
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install it with: pip install psycopg2-binary")
        print()
        print_manual_instructions(sql_content)
        sys.exit(1)
    
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected")
        print()
        
        # Execute the SQL (it's already a complete script with multiple statements)
        print("📋 Executing SQL migration...")
        cursor.execute(sql_content)
        
        print("✅ Migration completed successfully!")
        print()
        print("Verifying table exists...")
        
        # Verify table was created
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tumblr_posts'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ tumblr_posts table exists")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM tumblr_posts;")
            count = cursor.fetchone()[0]
            print(f"   Current row count: {count}")
        else:
            print("⚠️  Table might not have been created. Check for errors above.")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 70)
        print("✅ Migration completed!")
        print("=" * 70)
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print()
        print_manual_instructions(sql_content)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        print_manual_instructions(sql_content)
        sys.exit(1)


def print_manual_instructions(sql_content: str):
    """Print instructions for manual SQL execution."""
    print("=" * 70)
    print("Manual Migration Instructions")
    print("=" * 70)
    print()
    print("Copy and paste this SQL into your Supabase Dashboard SQL Editor:")
    print()
    print("-" * 70)
    print(sql_content)
    print("-" * 70)
    print()
    print("Steps:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to SQL Editor (left sidebar)")
    print("4. Click 'New query'")
    print("5. Paste the SQL above")
    print("6. Click 'Run' (or press Ctrl+Enter)")
    print()
    print("Or use Supabase CLI:")
    print("  supabase db push docs/supabase/tumblr_feed_schema.sql")
    print()


if __name__ == "__main__":
    run_migration()

