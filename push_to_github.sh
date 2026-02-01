#!/bin/bash

echo "======================================================================"
echo "PZ Admin Tool - GitHub Push Script"
echo "======================================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "Install with: sudo apt-get install git"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pz_admin_tool.py" ]; then
    echo "❌ Error: pz_admin_tool.py not found"
    echo "Please run this script from the pz-admin-tool-release directory"
    exit 1
fi

echo "Step 1: Configure Git Identity"
echo "======================================================================"
echo ""
read -p "Enter your name (for git commits): " git_name
read -p "Enter your email (for git commits): " git_email

git config user.name "$git_name"
git config user.email "$git_email"

echo ""
echo "✅ Git identity configured!"
echo ""

echo "Step 2: Create Initial Commit"
echo "======================================================================"
echo ""

# Check if already committed
if git rev-parse HEAD >/dev/null 2>&1; then
    echo "✅ Repository already has commits"
else
    git add .
    git commit -m "Initial release - PZ Admin Tool v1.0.0

Complete GUI administration tool for Project Zomboid servers.

Features:
- Player management (kick, ban, admin privileges, god mode, teleport)
- Server settings editor (30+ gameplay and zombie settings)
- Mod manager (simple text-based editor)
- Ban list viewer and manager
- RCON command executor
- Server logs viewer
- Workshop ID browser integration
- Persistent RCON connection
- Auto-refresh support
- Config file backup system

Technical:
- Python 3.7+ with tkinter
- Source RCON protocol implementation
- Dual-packet authentication handling
- .ini and .lua file editing
- No external dependencies"

    echo "✅ Initial commit created!"
fi

echo ""
echo "Step 3: Connect to GitHub Repository"
echo "======================================================================"
echo ""
echo "IMPORTANT: Make sure you've created the repository on GitHub first!"
echo "Go to: https://github.com/new"
echo ""
echo "Repository settings:"
echo "  - Name: pz-admin-tool"
echo "  - Description: GUI-based administration tool for Project Zomboid servers"
echo "  - Public or Private (your choice)"
echo "  - ❌ Do NOT initialize with README, .gitignore, or license"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " created

if [ "$created" != "y" ]; then
    echo ""
    echo "Please create the repository first, then run this script again."
    exit 0
fi

echo ""
read -p "Enter your GitHub username: " github_user

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Remote 'origin' already configured"
else
    git remote add origin "https://github.com/$github_user/pz-admin-tool.git"
    echo "✅ Remote 'origin' added!"
fi

echo ""
echo "Step 4: Push to GitHub"
echo "======================================================================"
echo ""
echo "Pushing to: https://github.com/$github_user/pz-admin-tool.git"
echo ""

git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ SUCCESS! Your code is now on GitHub!"
    echo "======================================================================"
    echo ""
    echo "View your repository at:"
    echo "https://github.com/$github_user/pz-admin-tool"
    echo ""
    echo "Next steps:"
    echo "1. Add a description and topics to your repo"
    echo "2. (Optional) Create a release: Releases → Create new release"
    echo "3. (Optional) Add screenshots to docs/screenshots/"
    echo "4. Share with the Project Zomboid community!"
    echo ""
else
    echo ""
    echo "======================================================================"
    echo "❌ Push failed"
    echo "======================================================================"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Authentication Required:"
    echo "   GitHub now requires a Personal Access Token for HTTPS."
    echo "   Generate one at: https://github.com/settings/tokens"
    echo "   Use it as your password when prompted."
    echo ""
    echo "2. SSH Alternative:"
    echo "   You can use SSH instead of HTTPS."
    echo "   Run: git remote set-url origin git@github.com:$github_user/pz-admin-tool.git"
    echo "   Then: git push -u origin main"
    echo ""
    echo "3. Repository Doesn't Exist:"
    echo "   Make sure you created it on GitHub first."
    echo ""
fi
