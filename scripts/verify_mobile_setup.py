#!/usr/bin/env python3
"""Verify mobile development setup for MCP Discord project."""

import os
import sys
import subprocess
from pathlib import Path


def check_command(cmd, name):
    """Check if a command is available."""
    try:
        subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        print(f"✅ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print(f"❌ {name} is not installed")
        return False


def check_file_exists(path, name):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✅ {name} exists")
        return True
    else:
        print(f"❌ {name} not found")
        return False


def check_env_var(var, name):
    """Check if environment variable is set."""
    if os.getenv(var):
        print(f"✅ {name} is set")
        return True
    else:
        print(f"⚠️  {name} is not set (may be in .env file)")
        return False


def main():
    """Run all checks."""
    print("🔍 Verifying Mobile Development Setup\n")
    print("=" * 50)
    
    checks = {
        "python": check_command("python", "Python"),
        "uv": check_command("uv", "uv (package manager)"),
        "git": check_command("git", "Git"),
    }
    
    print("\n📁 Project Files:")
    print("-" * 50)
    file_checks = {
        "pyproject.toml": check_file_exists("pyproject.toml", "pyproject.toml"),
        ".devcontainer": check_file_exists(".devcontainer/devcontainer.json", "Codespaces config"),
        ".gitpod.yml": check_file_exists(".gitpod.yml", "Gitpod config"),
        "docs/MOBILE_DEVELOPMENT.md": check_file_exists("docs/MOBILE_DEVELOPMENT.md", "Mobile dev guide"),
    }
    
    print("\n🔐 Environment Variables:")
    print("-" * 50)
    env_checks = {
        "DISCORD_TOKEN": check_env_var("DISCORD_TOKEN", "DISCORD_TOKEN"),
    }
    
    # Check .env file
    if Path(".env").exists():
        print("✅ .env file exists")
        try:
            with open(".env", "r") as f:
                content = f.read()
                if "DISCORD_TOKEN" in content:
                    print("✅ DISCORD_TOKEN found in .env")
                else:
                    print("⚠️  DISCORD_TOKEN not found in .env")
        except Exception as e:
            print(f"⚠️  Could not read .env: {e}")
    else:
        print("⚠️  .env file not found (create it with DISCORD_TOKEN)")
    
    print("\n📊 Summary:")
    print("=" * 50)
    all_checks = list(checks.values()) + list(file_checks.values())
    passed = sum(all_checks)
    total = len(all_checks)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready for mobile development.")
        print("\nNext steps:")
        print("1. Enable GitHub Codespaces on your repo")
        print("2. Or use Gitpod: https://gitpod.io/#<your-repo-url>")
        print("3. See docs/MOBILE_DEVELOPMENT.md for details")
    else:
        print("\n⚠️  Some checks failed. See above for details.")
        print("\nQuick fixes:")
        if not checks.get("uv"):
            print("- Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        if not file_checks.get(".env"):
            print("- Create .env file with DISCORD_TOKEN")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

