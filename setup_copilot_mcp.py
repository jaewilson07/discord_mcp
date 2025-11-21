#!/usr/bin/env python3
"""
Quick setup script to configure this MCP server for GitHub Copilot.

This script generates the VS Code configuration needed to use the
MCP Discord server with GitHub Copilot Chat.

Usage:
    python setup_copilot_mcp.py [--global]

Options:
    --global    Install to user settings instead of workspace settings
"""

import json
import os
import sys
from pathlib import Path


def get_workspace_root() -> Path:
    """Get the workspace root directory."""
    return Path(__file__).parent.absolute()


def get_vscode_settings_path(global_config: bool = False) -> Path:
    """Get the path to VS Code settings file."""
    if global_config:
        # User settings location varies by platform
        if sys.platform == "win32":
            return Path(os.environ["APPDATA"]) / "Code" / "User" / "settings.json"
        elif sys.platform == "darwin":
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "Code"
                / "User"
                / "settings.json"
            )
        else:  # Linux
            return Path.home() / ".config" / "Code" / "User" / "settings.json"
    else:
        # Workspace settings
        workspace_root = get_workspace_root()
        vscode_dir = workspace_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        return vscode_dir / "settings.json"


def load_env_vars() -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    env_file = get_workspace_root() / ".env"

    if not env_file.exists():
        print(f"⚠️  Warning: .env file not found at {env_file}")
        print("   MCP server will need environment variables to function properly.")
        return env_vars

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:  # Only add if value is not empty
                    env_vars[key] = value

    return env_vars


def get_mcp_config(workspace_root: Path, include_env: bool = True) -> dict:
    """Generate MCP server configuration."""
    config = {
        "command": "uv",
        "args": ["run", "python", "run.py"],
        "cwd": str(workspace_root),
    }

    if include_env:
        env_vars = load_env_vars()
        if env_vars:
            config["env"] = env_vars

    return config


def update_settings(settings_path: Path, mcp_config: dict) -> bool:
    """Update VS Code settings with MCP configuration."""
    # Load existing settings
    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, "r") as f:
                content = f.read().strip()
                if content:
                    settings = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ Error reading {settings_path}: {e}")
            print("   Please fix the JSON syntax and try again.")
            return False

    # Add or update MCP server configuration
    if "github.copilot.chat.mcp.servers" not in settings:
        settings["github.copilot.chat.mcp.servers"] = {}

    settings["github.copilot.chat.mcp.servers"]["discord-mcp"] = mcp_config

    # Write updated settings
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error writing {settings_path}: {e}")
        return False


def verify_setup() -> dict[str, bool]:
    """Verify that the setup is complete."""
    workspace_root = get_workspace_root()
    checks = {
        ".env file exists": (workspace_root / ".env").exists(),
        "run.py exists": (workspace_root / "run.py").exists(),
        "src/mcp_ce exists": (workspace_root / "src" / "mcp_ce").exists(),
        "uv available": (
            os.system("uv --version > nul 2>&1") == 0
            if sys.platform == "win32"
            else os.system("uv --version > /dev/null 2>&1") == 0
        ),
    }
    return checks


def print_status(checks: dict[str, bool]):
    """Print verification status."""
    print("\n📋 Setup Verification:")
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        if not checks["uv available"]:
            print(
                "   Install uv: https://docs.astral.sh/uv/getting-started/installation/"
            )
        if not checks[".env file exists"]:
            print("   Create .env file with required tokens (see .env.example)")


def main():
    """Main setup function."""
    global_config = "--global" in sys.argv

    print("🚀 MCP Discord Server Setup for GitHub Copilot")
    print("=" * 50)

    workspace_root = get_workspace_root()
    print(f"📁 Workspace: {workspace_root}")

    # Verify prerequisites
    checks = verify_setup()
    print_status(checks)

    if not all(checks.values()):
        print("\n❌ Setup incomplete. Fix the issues above and try again.")
        return 1

    # Get settings path
    settings_path = get_vscode_settings_path(global_config)
    print(f"\n📝 Settings file: {settings_path}")

    # Generate MCP configuration
    print("\n⚙️  Generating MCP configuration...")
    mcp_config = get_mcp_config(workspace_root, include_env=True)

    # Ask user preference for environment variables
    env_vars = load_env_vars()
    if env_vars:
        print(f"\n🔑 Found {len(env_vars)} environment variables in .env")
        print("   Note: Tokens will be stored in VS Code settings (consider security)")
        response = (
            input("   Include environment variables in config? (y/n): ").lower().strip()
        )
        if response != "y":
            print(
                "   Using .env file loading instead (run.py loads .env automatically)"
            )
            mcp_config = get_mcp_config(workspace_root, include_env=False)

    # Update settings
    print("\n💾 Updating VS Code settings...")
    if update_settings(settings_path, mcp_config):
        print("✅ Configuration updated successfully!")

        print("\n📖 Next Steps:")
        print("   1. Reload VS Code window (Ctrl+Shift+P → 'Reload Window')")
        print("   2. Open Copilot Chat (Ctrl+Alt+I or Cmd+Alt+I)")
        print("   3. Type '@workspace' to see available tools")
        print("   4. Try: '@workspace Get Discord server info for server 123456789'")

        print("\n🔧 Available Tools:")
        print("   • Discord: send_message, create_scheduled_event, get_server_info")
        print("   • YouTube: get_video_metadata, get_transcript, search_youtube")
        print("   • Notion: create_notion_page, query_notion_database")
        print("   • Crawl4AI: crawl_website, deep_crawl, save_article")
        print("   • URL Ping: ping_url")
        print("   • Total: 34 tools available")

        print("\n📚 Configuration Details:")
        print(json.dumps({"discord-mcp": mcp_config}, indent=2))

        return 0
    else:
        print("❌ Failed to update settings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
