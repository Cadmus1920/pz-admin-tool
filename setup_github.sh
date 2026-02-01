#!/bin/bash

# GitHub Repository Setup Script
# This script initializes a git repository and prepares for push to GitHub

echo "======================================================================"
echo "PZ Admin Tool - GitHub Setup"
echo "======================================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed"
    echo "Install with: sudo apt-get install git"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pz_admin_tool.py" ]; then
    echo "Error: pz_admin_tool.py not found"
    echo "Please run this script from the pz-admin-tool-release directory"
    exit 1
fi

echo "Step 1: Initializing git repository..."
git init

echo ""
echo "Step 2: Adding files..."
git add .

echo ""
echo "Step 3: Creating initial commit..."
git commit -m "Initial commit - PZ Admin Tool v1.0.0

Features:
- Player management (kick, ban, admin, teleport)
- God mode toggle
- Server commands and monitoring
- Mods viewer with orphaned Workshop ID detection
- Logs viewer
- Persistent RCON connection
- Config file support"

echo ""
echo "======================================================================"
echo "Git repository initialized successfully!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name: pz-admin-tool"
echo "   - Description: GUI-based admin tool for Project Zomboid servers"
echo "   - Public or Private (your choice)"
echo "   - Do NOT initialize with README (we already have one)"
echo ""
echo "2. Connect this repository to GitHub:"
echo "   git remote add origin https://github.com/YOUR-USERNAME/pz-admin-tool.git"
echo ""
echo "3. Push to GitHub:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. (Optional) Create a release:"
echo "   - Go to your repo on GitHub"
echo "   - Click 'Releases' → 'Create a new release'"
echo "   - Tag: v1.0.0"
echo "   - Title: PZ Admin Tool v1.0.0"
echo "   - Describe the release"
echo "   - Attach pz_admin_tool.py as a binary"
echo ""
echo "======================================================================"
echo ""
echo "Your repository is ready to push!"
echo ""
