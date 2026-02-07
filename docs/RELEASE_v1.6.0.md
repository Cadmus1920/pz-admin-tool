# Version 1.6.0 - Remote Server Support & Major UI Improvements

## 🌐 Major New Feature: SFTP Remote Server Support

Manage your remote/hosted servers directly from the GUI! No more SSH + text editors.

### Remote Server Management
- **SFTP Connection Support** - Connect to VPS, dedicated servers, cloud instances
- **Seamless File Access** - Edit configs on remote servers as easily as local files
- **Auto Upload/Download** - Files automatically synced to/from remote server
- **Connection Testing** - Verify credentials and paths before use
- **Hybrid Mode** - Switch between local and remote file access instantly

### Perfect For
- VPS hosting (DigitalOcean, Linode, Vultr, etc.)
- Cloud servers (AWS, GCP, Azure)
- Dedicated game server hosting
- Any Linux server with SSH access

**Requires:** `pip install paramiko --break-system-packages`

See [SFTP_SETUP_GUIDE.md](SFTP_SETUP_GUIDE.md) for complete setup instructions.

---

## 🎨 UI/UX Improvements

### Friendly Modern Interface
- **Color-Coded Buttons** - Blue (primary), Green (success), Red (danger), Orange (warning)
- **Emoji Icons** - Friendly visual indicators throughout the interface
- **Better Spacing** - Increased padding for more comfortable layout (10→15px)
- **Visual Hierarchy** - Important actions stand out with accent colors

### Enhanced Sections
- **Banner Header** - Professional title bar with theme-aware colors
  - Dark mode: Dark grey with white text
  - Light mode: Blue accent with white text
- **Tab Icons** - Each tab has a unique emoji (👥 Players, ⚙️ Settings, etc.)
- **Button Styling** - Colored buttons for different action types:
  - 🔵 Connect, Teleport, Info (Blue/Accent)
  - 🟢 Start Server, Grant Admin, Save (Green/Success)
  - 🔴 Stop Server, Ban, Remove (Red/Danger)
  - 🟠 Restart, Kick (Orange/Warning)

### Theme Improvements
- **Fixed Mod Manager Theme** - Now properly supports dark/light modes
- **Consistent Widget Colors** - All text areas, inputs, and labels themed correctly
- **Tab Hover Fix** - Tabs no longer turn white text on hover in light mode

---

## 💾 Preset System Enhancements

### Custom Preset Management
- **Save Your Own Presets** - Create and name custom server configurations
- **Unlimited Custom Presets** - Save as many as you need
- **Easy Management** - Delete/rename/organize your presets
- **Preset Preview** - See what will change before applying
- **Persistent Storage** - Presets saved to `~/.pz_admin_tool_presets.json`

### Built-in Presets
All official PZ presets included:
- Apocalypse (hardcore default)
- Survivor (balanced challenge)
- Builder (creative/building focus)
- Beginner (easy mode)
- First Week (early apocalypse chaos)
- Six Months Later (post-apocalypse scavenging)
- Survival (maximum difficulty)

### Preset Features
- **Preview Before Apply** - See all settings that will change
- **Smart Dropdown** - Built-in presets + your custom presets organized
- **One-Click Apply** - Instantly apply any preset
- **Name Protection** - Can't overwrite built-in presets
- **Overwrite Warning** - Confirms before overwriting your presets

---

## ⚙️ Settings Editor Enhancements

### New Settings Tab: Combat & Meta (9th Tab)
**Combat Settings:**
- Melee Weapon Degradation
- Melee Weapon Damage
- Firearm Damage
- Firearm Recoil
- Recoil Recovery Delay
- Aiming Time Modifier
- Multi-Hit Zombies
- Rear Vulnerability

**Meta/Respawn Settings:**
- Zombie Respawn Hours
- Zombie Respawn Percentage
- Respawn Unseen Hours
- Helicopter Event Frequency
- Meta Events
- Events While Sleeping

**World Spawn Settings:**
- Zombie Lore
- Proper Zombie Count
- Rally Group Size/Distance/Separation/Radius

### Expanded Zombie Options
Added "Random Between" variants for more control:
- **Speed:** Random (Shamblers-Fast Shamblers)
- **Strength:** Random (Weak-Normal), Random (Normal-Superhuman)
- **Toughness:** Random (Fragile-Normal), Random (Normal-Tough)
- **Memory:** Random (Normal-None) ✓
- **Sight:** Random (Normal-Poor) ✓
- **Hearing:** Random (Normal-Poor) ✓

**Total: 150+ editable settings across 9 tabs!**

---

## 🔧 Quality of Life Fixes

### Dialog Management
- **Fixed Z-Order Issues** - Dialogs now always appear on top of their parent window
- **Proper Modal Behavior** - Parent windows blocked while dialogs are open
- **No More Hidden Dialogs** - All confirmations/warnings appear where expected

### Fixed Windows
- Settings Editor - All dialogs (presets, save, errors)
- Mod Manager - Save confirmation and messages
- Main Window - Save config confirmation
- All messageboxes now have proper parent windows

### Persistent Settings
- **Font Size Persistence** - Selected font size now applies on startup
- **Theme Persistence** - Dark/light mode preference saved
- **Connection Persistence** - Last server connection saved

---

## 📊 Complete Feature Summary

### Core Features (140+ Settings)
- 9 Settings Tabs: Basic, Gameplay, Zombies, Advanced, Loot, World, Vehicles, Survival, Combat
- 7 Built-in + Unlimited Custom Presets
- Full RCON command support
- Player management (kick, ban, teleport, admin)
- Mod manager with Workshop ID support
- Live log streaming
- Scheduled tasks & restart timer
- Ban list management

### Connectivity Options
- **Local File Access** - Direct file system access
- **SFTP Remote Access** - Connect to hosted/remote servers
- **RCON Protocol** - Remote command execution
- **Persistent Connections** - SFTP stays connected during session

### UI Features
- Dark/Light theme support
- Adjustable font sizes (9-12pt)
- Color-coded action buttons
- Emoji icons throughout
- Responsive layout
- 140+ server settings with descriptions

---

## 🚀 Installation & Upgrade

### New Installation
```bash
git clone https://github.com/yourusername/pz-admin-tool.git
cd pz-admin-tool
pip install -r requirements.txt
python pz_admin_tool.py
```

### Upgrade from v1.3.0 or Earlier
```bash
cd pz-admin-tool
git pull origin main
pip install paramiko --break-system-packages  # For SFTP support
python pz_admin_tool.py
```

### Windows Users
Download **PZ-Admin-Tool-v1.6.0-Windows.exe** from the releases page.
For SFTP support: `pip install paramiko` in your terminal first.

---

## 📋 Requirements

### Python Dependencies
- Python 3.7+
- tkinter (usually included)
- **New:** paramiko (for SFTP support - optional)

### SFTP Support
```bash
# Linux
pip install paramiko --break-system-packages

# Windows
pip install paramiko
```

**Note:** SFTP is optional - local file access works without it.

---

## 📖 Documentation

- **README.md** - Main documentation and features
- **SFTP_SETUP_GUIDE.md** - Complete SFTP setup guide
- **CHANGELOG.md** - Detailed version history
- **docs/RESTART_TIMER.md** - Restart timer documentation

---

## 🐛 Bug Fixes

- Fixed dialog z-order issues (no more buried confirmations)
- Fixed mod manager theme in dark mode
- Fixed tab hover colors in light mode
- Fixed font size persistence across restarts
- Fixed banner theme inconsistency
- Improved error handling for SFTP connections
- Better messagebox parent window associations

---

## 🎯 Coming Soon

- SSH key authentication for SFTP
- Multi-server profile management
- Server monitoring dashboard
- Performance metrics & graphs
- Backup/restore configurations
- Scheduled backup automation

---

## 💡 Tips

### Using Remote Servers
1. Connect RCON for player commands (host:16261)
2. Connect SFTP for file editing (host:22)
3. Edit settings/mods in GUI
4. Restart server via SSH or server control panel

### Performance
- SFTP downloads files only when needed
- Local changes are instant
- Remote changes upload automatically on save
- Connection stays open for multiple operations

### Security
- Use strong passwords for SFTP
- Consider SSH keys (coming soon)
- RCON password separate from SFTP
- No credentials stored to disk

---

## 🙏 Acknowledgments

Thank you to everyone who:
- Reported bugs and suggested features
- Tested the SFTP implementation
- Provided feedback on the UI improvements
- Contributed to the preset configurations

---

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.

**Upgrade today to manage your remote servers with ease!** 🎮✨
