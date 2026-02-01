# How to Push to GitHub - Quick Guide

## Prerequisites
- Git installed: `sudo apt-get install git`
- GitHub account created
- SSH key added to GitHub (recommended) OR Personal Access Token ready

## Step-by-Step Instructions

### 1. Navigate to the Release Folder
```bash
cd /path/to/pz-admin-tool-release
```

### 2. Run the Push Script
```bash
./push_to_github.sh
```

The script will:
- Ask for your name and email (for git commits)
- Ask for your GitHub username
- Create the initial commit
- Connect to your GitHub repository
- Push everything to GitHub

### 3. When Prompted for Password

**Option A: Personal Access Token (Recommended)**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: `repo` (all)
4. Copy the token
5. Use it as your password when git asks

**Option B: SSH (One-time setup, more convenient)**
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your.email@example.com"`
2. Copy key: `cat ~/.ssh/id_ed25519.pub`
3. Add to GitHub: https://github.com/settings/keys
4. Change remote: `git remote set-url origin git@github.com:Cadmus1920/pz-admin-tool.git`
5. Push: `git push -u origin main`

## Creating the GitHub Repository

Before running the script, create the repository on GitHub:

1. Go to: https://github.com/new
2. Repository name: `pz-admin-tool`
3. Description: `GUI-based administration tool for Project Zomboid servers`
4. Choose Public or Private
5. **❌ Do NOT initialize with README, .gitignore, or license** (we already have these)
6. Click "Create repository"

## Troubleshooting

### "Repository not found"
- Make sure you created the repo on GitHub first
- Check the username is correct

### "Authentication failed"
- GitHub no longer accepts password authentication
- Use a Personal Access Token (see above)
- Or switch to SSH

### "Permission denied"
- Check your SSH key is added to GitHub
- Or use Personal Access Token with HTTPS

## After Successfully Pushing

Your repository is now live at:
```
https://github.com/YOUR-USERNAME/pz-admin-tool
```

### Optional: Create a Release
1. Go to your repo → Releases
2. Click "Create a new release"
3. Tag: `v1.0.0`
4. Title: `PZ Admin Tool v1.0.0 - Initial Release`
5. Describe the features
6. Click "Publish release"

### Optional: Add Topics
Add these topics to help people find your project:
- `project-zomboid`
- `server-admin`
- `rcon`
- `python`
- `gui`
- `game-server`

## Making Future Updates

When you make changes to the code:

```bash
cd /path/to/pz-admin-tool-release
git add .
git commit -m "Description of changes"
git push
```

That's it! 🎉
