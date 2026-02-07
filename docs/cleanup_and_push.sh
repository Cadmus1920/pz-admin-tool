#!/bin/bash
# Cleanup repo and push to GitHub

cd /home/claude/pz-admin-tool-release

echo "🧹 Cleaning up repo..."

# Remove files that are still being tracked by git
git rm --cached -f preset_data.json 2>/dev/null
git rm --cached -f preset_differences.json 2>/dev/null
git rm --cached -f settings_database.json 2>/dev/null
git rm --cached -f settings_manager.py 2>/dev/null
git rm --cached -f push_to_github.sh 2>/dev/null
git rm --cached -f setup_github.sh 2>/dev/null
git rm --cached -r preset_files_build42/ 2>/dev/null
git rm --cached -r __pycache__/ 2>/dev/null

# Update .gitignore to prevent these from being added again
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific - generated files
preset_data.json
preset_differences.json
preset_files_build42/
settings_database.json
settings_manager.py
push_to_github.sh
setup_github.sh
EOF

git add .gitignore

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "✅ No changes needed - repo already clean!"
else
    echo "💾 Committing cleanup..."
    git commit -m "Cleanup: Remove generated/internal files

Removed:
- preset_data.json, preset_differences.json
- preset_files_build42/ folder
- settings_database.json
- Internal scripts
- Updated .gitignore"
fi

echo ""
echo "📤 Pushing to GitHub..."
echo "This will push:"
echo "  - Cleanup commit (if any)"
echo "  - v2.1.0 tag"
echo "  - v2.2.2 tag"
echo ""

# Push main branch and tags
git push origin main
git push origin v2.1.0
git push origin v2.2.2

echo ""
echo "✅ Done!"
echo ""
echo "Now go to GitHub and:"
echo "1. Refresh the page - files should be gone"
echo "2. Create release for v2.1.0"
echo "3. Create release for v2.2.2"
