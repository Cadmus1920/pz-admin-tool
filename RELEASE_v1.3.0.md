# 🚀 Version 1.3.0 Release Instructions

## Summary
Major release with scheduled restart timer, vehicle settings, code cleanup, and improvements.

## Files Changed
- `pz_admin_tool.py` - Updated to v1.3.0
- `CHANGELOG.md` - Added v1.3.0 entry
- All other files ready to commit

## Git Commands

```bash
cd pz-admin-tool-release

# Stage all changes
git add .

# Commit with detailed message
git commit -m "Release v1.3.0 - Scheduled Restart Timer & Major Improvements

New Features:
- Scheduled Restart Timer with countdown and warnings
  * Configurable time (1-480 min) with quick presets
  * Customizable warning intervals (30min to 30sec)
  * Live countdown window with progress bar
  * Admin status indicator in main window
  * Auto-save option before restart
  * Repeating mode for daily/scheduled restarts
  * Cancel anytime with player broadcast

- Complete Vehicles Tab (14 settings)
  * Spawn rate, condition, locks, alarms
  * Gas consumption, engine noise
  * Traffic jams, damage settings

- Precise Slider Input
  * Entry boxes next to all sliders
  * Type exact values and press Enter

Improvements:
- Expanded zombie settings (25 total)
  * Random variants for sight/hearing/memory
  * Advanced stealth, fake dead, etc.
- Enhanced world settings
  * Day/night cycle, weather cycle, fog cycle
- Dropdown menus now match theme colors
- Complete code cleanup
  * Organized imports
  * Fixed 15 bare except clauses
  * Better error handling
  * Production-ready quality

Total Settings: 100+ across 8 organized tabs"

# Create version tag
git tag -a v1.3.0 -m "Version 1.3.0 - Scheduled Restart Timer & Major Improvements

Highlights:
- ⏰ Scheduled restart countdown system
- 🚗 Complete vehicle settings (14 options)
- 🎯 Precise slider inputs
- 🧟 Expanded zombie settings (25 total)
- 🌍 Climate/weather cycle controls
- 💻 Production-ready code quality
- 🎨 Full theme consistency

100+ server settings across 8 tabs!"

# Push everything
git push origin main
git push origin v1.3.0
```

## Create GitHub Release

1. Go to: https://github.com/Cadmus1920/pz-admin-tool/releases
2. Click "Draft a new release"
3. Select tag: `v1.3.0`
4. Title: **Version 1.3.0 - Scheduled Restart Timer & Major Improvements**
5. Description:

```markdown
## 🎉 What's New in v1.3.0

### ⏰ Scheduled Restart Timer (Major Feature!)
Set up automatic server restarts with countdown warnings:
- 🕐 Configurable time: 5min to 8 hours (quick presets: 5m, 15m, 30m, 1h, 2h, 3h)
- 📢 Customizable warnings: 30min, 15min, 10min, 5min, 1min, 30sec
- 📊 Live countdown with progress bar
- 👁️ Admin indicator in main window shows time remaining
- 💾 Auto-save option (1 minute before restart)
- 🔄 Repeating mode for daily/scheduled maintenance
- ❌ Cancel anytime with broadcast to players

Perfect for daily restarts, performance maintenance, or scheduled updates!

### 🚗 Vehicle Settings Tab
Complete control over vehicle spawning and behavior:
- Enable/disable vehicles
- Spawn rate and condition
- Gas consumption and engine noise
- Traffic jams and car alarms
- Vehicle and player damage settings
- 14 total vehicle options

### 🎯 Precise Slider Controls
- Entry boxes next to every slider
- Type exact values (e.g., "1.0") and press Enter
- No more fighting with sliders!

### 🧟 Expanded Zombie Settings (25 Total)
- Random variants: "Random between Normal and Poor" for sight/hearing/memory
- Crawl under vehicles frequency
- Distribution mode (Urban vs Uniform)
- Advanced options: stealth mechanics, fake dead zombies, spawn removal
- Armor factor, max defense, fall damage

### 🌍 Enhanced World Controls
- Day/Night Cycle: Normal, Endless Day, Endless Night
- Weather Cycle: Normal, No Weather, Endless Rain/Storm/Snow/Blizzard
- Fog Cycle: Normal, No Fog, Endless Fog

### 🎨 Theme Improvements
- Dropdown menus now match dark/light theme
- All text areas properly themed
- Complete visual consistency

### 💻 Code Quality Overhaul
- All imports organized at top
- Fixed 15 bare exception handlers
- Specific error handling throughout
- Production-ready code quality
- Better debugging and maintenance

## 📊 By The Numbers
- **100+ server settings** across 8 organized tabs
- **3,999 lines** of clean, professional code
- **109 methods** for comprehensive functionality
- Full cross-platform support (Windows, Linux, Mac)

## 📥 Installation

**Windows (No Python Required):**
Download `PZ-Admin-Tool-v1.3.0-Windows.exe` and double-click!

**All Platforms (Python):**
```bash
python pz_admin_tool.py
```

See [Installation Guide](https://github.com/Cadmus1920/pz-admin-tool#installation) for details.

## 🔄 Upgrading from v1.2.0
Simply replace your old file - all settings are preserved!

---

**Full Changelog:** [CHANGELOG.md](https://github.com/Cadmus1920/pz-admin-tool/blob/main/CHANGELOG.md)
```

6. Click "Publish release"
7. GitHub Actions will automatically build Windows .exe

## What's Included

### Tabs (8 Total):
1. Players - Manage connected players
2. Commands - Quick commands and custom execution
3. Scheduler - Scheduled announcements and commands
4. Mods - Mod manager
5. Bans - Ban list management
6. Logs - Live log streaming
7. Server Info - Server control and restart timer
8. Settings - 100+ settings across sub-tabs:
   - Basic Server
   - Gameplay
   - Zombies (25 settings)
   - Advanced
   - Loot Details (19 categories)
   - World & Environment (14 settings)
   - Vehicles (14 settings)
   - Survival & Health

### Features:
- RCON connection management
- Player administration
- Server control (start/stop/restart/status)
- **Scheduled restart timer** (NEW!)
- Mod management
- Ban list management
- Task scheduler
- Live log streaming
- Dark/light themes
- Windows executable available

## After Release

Update README badges if needed:
```markdown
![Version](https://img.shields.io/badge/version-1.3.0-blue)
![Downloads](https://img.shields.io/github/downloads/Cadmus1920/pz-admin-tool/total)
```

🎊 Version 1.3.0 is ready!
