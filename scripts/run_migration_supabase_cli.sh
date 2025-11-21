#!/bin/bash
# Run Tumblr migration using Supabase CLI

# For local Supabase
supabase db push --local --db-url "postgresql://postgres:postgres@127.0.0.1:54322/postgres" < docs/supabase/tumblr_feed_schema.sql

# Or for remote (if linked):
# supabase db push --linked

