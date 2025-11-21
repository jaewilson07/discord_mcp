# Mobile Development Guide

This guide covers multiple options for continuing development on this MCP Discord project from your mobile device.

## Quick Reference

| Method | Best For | Setup Time | Full IDE | Cost |
|--------|----------|------------|----------|------|
| **GitHub Codespaces** | Full development | 5 min | ✅ Yes | Free tier available |
| **Gitpod** | Full development | 5 min | ✅ Yes | Free tier available |
| **Mobile Git Apps** | Quick edits/commits | 2 min | ❌ No | Free |
| **SSH + Termux** | Android full dev | 15 min | ⚠️ Terminal | Free |
| **Remote Desktop** | Access dev machine | 10 min | ✅ Yes | Free/Varies |

---

## Option 1: GitHub Codespaces (Recommended)

**Best for:** Full development environment with VS Code in browser

### Setup

1. **Enable Codespaces:**
   - Go to your GitHub repo: `https://github.com/hanweg/mcp-discord`
   - Click "Code" → "Codespaces" → "Create codespace on main"
   - Wait 2-3 minutes for environment to spin up

2. **Configure Environment:**
   ```bash
   # Codespace will auto-detect Python and uv
   # Install dependencies
   uv sync
   
   # Set up environment variables
   echo "DISCORD_TOKEN=your_token_here" > .env
   ```

3. **Access from Phone:**
   - Open Codespace URL in mobile browser
   - Use GitHub mobile app or browser
   - Full VS Code experience optimized for mobile

### Advantages
- ✅ Full VS Code experience
- ✅ Pre-configured with Python/uv
- ✅ Free tier: 60 hours/month
- ✅ Works on any device with browser
- ✅ Auto-saves to GitHub

### Mobile Tips
- Use landscape mode for better code view
- Enable "Desktop site" in mobile browser
- Use external keyboard if available
- Pin Codespace to home screen

---

## Option 2: Gitpod

**Best for:** Alternative cloud IDE with similar features

### Setup

1. **Install Gitpod Extension:**
   - Add `https://gitpod.io/#` before your repo URL
   - Or install Gitpod browser extension

2. **First Launch:**
   ```bash
   # Gitpod will auto-setup based on .gitpod.yml (create if needed)
   uv sync
   ```

3. **Create `.gitpod.yml`** (optional, for auto-setup):
   ```yaml
   tasks:
     - init: uv sync
       command: echo "Ready to code!"
   
   vscode:
     extensions:
       - ms-python.python
   ```

### Advantages
- ✅ Free tier: 50 hours/month
- ✅ Fast workspace creation
- ✅ Good mobile browser support

---

## Option 3: Mobile Git Apps (Quick Edits)

**Best for:** Quick file edits, commits, and pushes

### iOS: Working Copy or GitHawk

**Working Copy:**
1. Clone repo: `https://github.com/hanweg/mcp-discord`
2. Edit files with built-in editor
3. Commit and push directly
4. Sync with main dev machine

**GitHawk:**
- GitHub-native app
- Edit files directly in GitHub
- Create branches and PRs

### Android: GitJournal or Termux

**GitJournal:**
- Markdown-focused but supports any text
- Git integration built-in
- Good for quick edits

**Termux:**
- Full terminal environment
- Can run `git`, `python`, etc.
- See Option 4 for details

### Workflow
```bash
# On phone:
1. Edit file in app
2. Commit: git commit -m "Quick fix from mobile"
3. Push: git push origin main

# On main dev machine:
git pull origin main
```

---

## Option 4: Termux (Android Only)

**Best for:** Full terminal development on Android

### Setup

1. **Install Termux:**
   - From F-Droid (recommended) or Play Store
   - Grant storage permissions

2. **Install Dependencies:**
   ```bash
   # Update packages
   pkg update && pkg upgrade
   
   # Install Python and git
   pkg install python git
   
   # Install uv (Python package manager)
   pip install uv
   
   # Clone repo
   git clone https://github.com/hanweg/mcp-discord.git
   cd mcp-discord
   
   # Install project dependencies
   uv sync
   ```

3. **Set Up Environment:**
   ```bash
   # Create .env file
   nano .env
   # Add: DISCORD_TOKEN=your_token_here
   
   # Test run
   uv run mcp-discord --info
   ```

4. **Install Code Editor:**
   ```bash
   # Option 1: Vim (built-in)
   # Option 2: Nano (simpler)
   # Option 3: Install code-server for VS Code
   pkg install code-server
   code-server --bind-addr 0.0.0.0:8080
   # Access at http://localhost:8080
   ```

### Advantages
- ✅ Full terminal access
- ✅ Can run Python scripts
- ✅ Free and open source
- ✅ Works offline

### Limitations
- ⚠️ Terminal-only (unless using code-server)
- ⚠️ Android only
- ⚠️ Smaller screen challenges

---

## Option 5: Remote Desktop Access

**Best for:** Accessing your existing dev machine

### Options

**Chrome Remote Desktop:**
1. Install on dev machine and phone
2. Access full desktop from phone
3. Use touch or external mouse/keyboard

**TeamViewer:**
- Similar to Chrome Remote Desktop
- Good mobile app

**SSH Access:**
```bash
# On phone (Termux or SSH client):
ssh user@your-dev-machine-ip

# Then work normally in terminal
cd ~/mcp-discord
uv run mcp-discord
```

### Setup SSH Server (Windows)

1. **Enable OpenSSH Server:**
   ```powershell
   # Run as Administrator
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Start-Service sshd
   Set-Service -Name sshd -StartupType 'Automatic'
   ```

2. **Configure Firewall:**
   ```powershell
   New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
   ```

3. **Find Your IP:**
   ```powershell
   ipconfig
   # Look for IPv4 address
   ```

---

## Option 6: Hybrid Approach (Recommended)

**Combine multiple methods for best experience:**

1. **Quick Edits:** Use GitHub mobile app or Working Copy
2. **Full Development:** Use Codespaces when needed
3. **Testing:** Use SSH to dev machine or Codespaces
4. **Review:** Use GitHub mobile app for PRs

### Workflow Example

```bash
# Morning: Quick fix from phone
1. Open GitHub app
2. Edit file directly
3. Commit and push
4. Codespace auto-updates

# Afternoon: Full development session
1. Open Codespace from phone browser
2. Full IDE experience
3. Run tests, debug, etc.
4. Commit and push

# Evening: Review on phone
1. Check PRs in GitHub app
2. Review changes
3. Merge if approved
```

---

## Mobile-Specific Tips

### Code Editing on Mobile

1. **Use Landscape Mode:** Better for viewing code
2. **External Keyboard:** Bluetooth keyboard helps significantly
3. **Code Folding:** Collapse functions you're not editing
4. **Search & Replace:** Use IDE search instead of manual editing
5. **Voice Input:** Use for commit messages and comments

### Git Workflow

```bash
# Quick commit from mobile
git add .
git commit -m "Fix: [description]"
git push

# Create feature branch
git checkout -b mobile-fix
# ... make changes ...
git push -u origin mobile-fix
# Create PR from GitHub app
```

### Testing on Mobile

**Option 1: Codespaces**
```bash
# Run tests in Codespace terminal
uv run pytest
```

**Option 2: GitHub Actions**
- Push code
- Tests run automatically
- Check results in GitHub app

**Option 3: SSH to Dev Machine**
```bash
ssh user@dev-machine
cd mcp-discord
uv run pytest
```

---

## Recommended Setup for This Project

### Minimum Setup (Quick Start)
1. Install **GitHub mobile app**
2. Enable **GitHub Codespaces** on repo
3. Use Codespaces for development
4. Use GitHub app for quick edits

### Full Setup (Best Experience)
1. **GitHub Codespaces** - Primary development
2. **Working Copy** (iOS) or **Termux** (Android) - Quick edits
3. **SSH access** to dev machine - For testing
4. **GitHub mobile app** - For PRs and reviews

---

## Troubleshooting

### Codespaces Issues

**Slow Performance:**
- Use smaller instance (2-core instead of 4-core)
- Close unused browser tabs
- Use "Rebuild" if workspace is corrupted

**Mobile Browser Issues:**
- Enable "Desktop site" mode
- Use Chrome or Safari (best mobile support)
- Clear browser cache

### Termux Issues

**Python Not Found:**
```bash
pkg install python
python --version
```

**uv Installation Fails:**
```bash
pip install --upgrade pip
pip install uv
```

**Permission Denied:**
```bash
# Grant storage permission in Termux settings
# Or use: termux-setup-storage
```

### Git Issues on Mobile

**Authentication:**
- Use SSH keys (recommended)
- Or use GitHub Personal Access Token
- Store securely in app keychain

**Large Files:**
- Use Git LFS if needed
- Or commit from main dev machine

---

## Security Considerations

1. **Environment Variables:**
   - Never commit `.env` files
   - Use Codespaces secrets or environment variables
   - Use secure storage in mobile apps

2. **SSH Keys:**
   - Use strong passphrases
   - Store keys securely (app keychain)
   - Rotate keys regularly

3. **Remote Access:**
   - Use VPN if accessing dev machine remotely
   - Enable firewall rules
   - Use strong passwords

---

## Quick Commands Reference

### Git (Mobile)
```bash
# Status
git status

# Quick commit
git add . && git commit -m "message" && git push

# Create branch
git checkout -b feature-name

# Switch branch
git checkout main
```

### Project (Mobile)
```bash
# Install dependencies
uv sync

# Run server
uv run mcp-discord

# Run tests
uv run pytest

# Check Python version
python --version
```

---

## Next Steps

1. **Choose your method** based on needs
2. **Set up Codespaces** (easiest start)
3. **Test workflow** with a small change
4. **Optimize** for your specific use case

## Support

- GitHub Issues: Report problems with mobile development
- Discord: Ask in project Discord server
- Documentation: Check `docs/` folder for more guides

---

**Happy coding from your phone! 📱💻**

