# Run Tumblr migration using Supabase CLI (PowerShell)

# For local Supabase - we need to create a migration first
# The CLI expects migrations in supabase/migrations/ directory

Write-Host "Creating Supabase migration..."

# Initialize if needed
if (-not (Test-Path "supabase")) {
    supabase init
}

# Create migration directory if it doesn't exist
if (-not (Test-Path "supabase\migrations")) {
    New-Item -ItemType Directory -Path "supabase\migrations" -Force
}

# Copy SQL file to migrations directory with timestamp
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$migrationFile = "supabase\migrations\${timestamp}_create_tumblr_posts_table.sql"
Copy-Item "docs\supabase\tumblr_feed_schema.sql" -Destination $migrationFile

Write-Host "Migration file created: $migrationFile"
Write-Host ""
Write-Host "Now run:"
Write-Host "  supabase db push --local"
Write-Host ""
Write-Host "Or for remote database:"
Write-Host "  supabase db push --linked"

