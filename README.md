# Project Zomboid Server Admin Tool

A comprehensive GUI-based administration tool for Project Zomboid dedicated servers using RCON protocol.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### 🎮 Player Management
- View online players in real-time with auto-refresh
- Kick/ban/unban players
- Grant and remove admin privileges
- Toggle god mode, invisibility, and noclip
- Teleport players to each other
- Ban list viewer and manager

### ⚙️ Server Settings Editor
- Edit 30+ gameplay settings (loot abundance, XP multiplier, farming speed, etc.)
- Configure zombie settings (population, speed, strength, infection, cognition, etc.)
- Modify basic server settings (name, password, ports, max players)
- Auto-detects server configuration files
- Creates timestamped backups before saving
- Supports both .ini and .lua files

### 📋 Mods Management
- View installed mods and Workshop IDs side-by-side
- Simple text-based mod editor
- Add/remove mods easily
- Double-click Workshop IDs to open in browser
- Automatic browser integration with fallback methods

### ⏰ Task Scheduler
- Schedule recurring server announcements
- Schedule recurring RCON commands
- Perfect for restart warnings and auto-saves
- Enable/disable/remove scheduled tasks
- Persistent across application restarts

### 🎛️ Server Control
- Start/Stop/Restart server with one click
- Configurable commands (supports systemd, scripts, docker, screen, etc.)
- Check server status
- Execute shell commands with output logging

### 📺 Live Log Streaming
- Real-time server log viewer
- Auto-scrolling with new entries
- Shows last 50 lines of context
- Toggle on/off with checkbox
- Updates every second

### 🎨 Appearance Customization
- Dark theme for late-night admin sessions
- Light theme (default)
- Font size scaling (8pt to 12pt)
- Persistent theme preferences

### 🔧 Additional Features
- Execute any RCON command
- Send server-wide messages
- Save server state
- Real-time command output logging
- Persistent RCON connection
- Config file support for saved settings
- Show/hide password option
- Server path auto-detection

## Screenshots

![Main Interface](docs/screenshots/main-interface.png)
*Players management tab with admin controls*

## Requirements

- Python 3.7 or higher
- Linux server (tested on Ubuntu 24)
- Project Zomboid Dedicated Server
- RCON enabled on your server

### Python Dependencies

All standard library - no pip packages required!
- `tkinter` - GUI framework (may need: `apt-get install python3-tk`)
- `socket` - RCON communication
- `sqlite3` - Database reading
- `pathlib` - File operations

## Installation

### 1. Download

```bash
git clone https://github.com/yourusername/pz-admin-tool.git
cd pz-admin-tool
```

### 2. Install Python TkInter (if needed)

```bash
sudo apt-get update
sudo apt-get install python3-tk
```

### 3. Enable RCON on Your Server

Edit your server config file (usually `~/Zomboid/Server/servertest.ini`):

```ini
RCONPort=16261
RCONPassword=YourSecurePassword
```

**Important:** Use a strong password without special characters (alphanumeric recommended).

### 4. Restart Your Server

```bash
sudo systemctl restart your-pz-service
```

Wait 30 seconds for the server to fully start.

## Usage

### Quick Start

```bash
python3 pz_admin_tool.py
```

1. **Connect:**
   - Host: `127.0.0.1` (if running on same server)
   - Port: `16261` (or your RCON port)
   - Password: Your RCON password
   - Click **Connect**

2. **Manage Players:**
   - Switch to **Players** tab
   - Click **Refresh Players**
   - Enter username and use action buttons

3. **View Mods:**
   - Set server path (or use Auto-Detect)
   - Switch to **Mods** tab
   - Click **Refresh Mods**

### Configuration

The tool saves your connection settings to `pz_admin_config.json`:

```json
{
    "host": "127.0.0.1",
    "port": "16261",
    "server_path": "/home/zomboid/Zomboid"
}
```

**Note:** Passwords are NOT saved - you must enter them each time for security.

## Server Setup

### RCON Configuration

Your server config needs these settings:

```ini
# Required
RCONPort=16261
RCONPassword=YourPassword

# Optional but recommended
RCONMaxConnections=10
```

### Recommended Password Guidelines

- Use alphanumeric characters only (A-Z, a-z, 0-9)
- Avoid special characters (!, @, #, etc.) to prevent shell escaping issues
- Minimum 12 characters
- Example: `ServerAdmin2025`

### Testing RCON

Verify RCON is working:

```bash
# Check if port is listening
sudo netstat -tulpn | grep 16261

# Test with rcon-cli (optional)
./rcon -a 127.0.0.1:16261 -p YourPassword players
```

## Troubleshooting

### "Authentication Failed"

**Cause:** Wrong password or RCON not enabled.

**Solutions:**
1. Check password in config:
   ```bash
   grep RCONPassword ~/Zomboid/Server/servertest.ini
   ```
2. Restart server after config changes
3. Avoid special characters in password
4. Check for extra spaces: `cat -A ~/Zomboid/Server/servertest.ini | grep RCONPassword`

### "Connection Refused"

**Cause:** RCON port not listening or firewall blocking.

**Solutions:**
1. Verify server is running:
   ```bash
   sudo systemctl status your-pz-service
   ```
2. Check RCON port:
   ```bash
   sudo netstat -tulpn | grep 16261
   ```
3. Wait 30 seconds after server start

### Players Not Showing

**Cause:** Player list only shows when players are fully loaded into the game world.

**Solutions:**
1. Check **Commands** tab - raw output appears there
2. Players must be in-game, not just at menu
3. Use manual username entry if needed

### Mods Not Showing

**Cause:** Server path not set correctly.

**Solutions:**
1. Click **Auto-Detect** button
2. Manually set path to server **data** directory:
   - Usually: `/home/zomboid/Zomboid/`
   - NOT the steamcmd install directory
3. Check config file exists at `ServerPath/Server/servertest.ini`

## Architecture

### RCON Protocol Implementation

The tool uses the Source RCON protocol with Project Zomboid-specific handling:

1. **Connection:** Persistent connection stays open
2. **Authentication:** Handles dual-packet auth response
3. **Commands:** Builds proper packet structure with two null terminators

### Key Technical Details

- **Packet Structure:** Size (4 bytes) + ID (4 bytes) + Type (4 bytes) + Body + 2 null terminators
- **Auth Sequence:** Receives empty SERVERDATA_RESPONSE_VALUE, then SERVERDATA_AUTH_RESPONSE
- **Connection Management:** Fresh connection authenticates once, reused for all commands

## Development

### Project Structure

```
pz-admin-tool/
├── pz_admin_tool.py      # Main application
├── README.md             # This file
├── LICENSE               # MIT License
├── .gitignore           # Git ignore file
└── docs/
    ├── COMMANDS.md       # RCON command reference
    ├── TROUBLESHOOTING.md # Detailed troubleshooting
    └── screenshots/      # Application screenshots
```

### Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- Python 3.7+ compatibility
- Standard library only (no external dependencies except tkinter)
- Clear comments and docstrings
- Error handling for all RCON operations

## FAQ

**Q: Does this work on Windows?**
A: The tool is designed for Linux servers. Windows support untested but may work with minor modifications.

**Q: Can I run this remotely?**
A: Yes! Use your server's IP instead of `127.0.0.1`. Ensure RCON port is accessible (firewall/port forwarding).

**Q: Is my password stored?**
A: No. Only host, port, and server path are saved. Password must be entered each session.

**Q: Why do some commands not return output?**
A: Some PZ RCON commands execute silently. Check server logs or in-game to verify.

**Q: Can I manage multiple servers?**
A: Not simultaneously, but you can save different configs and switch between them.

## Known Limitations

- Player list doesn't show admin status or access levels (RCON limitation)
- Some RCON commands return empty responses (PZ limitation)
- Mods tab requires server file access (read-only)
- Auto-refresh is 30 seconds (can be adjusted in code)

## Roadmap

- [ ] Multi-server support
- [ ] Database player history viewer
- [ ] Scheduled commands/announcements
- [ ] Plugin system for custom actions
- [ ] Dark mode theme
- [ ] Export logs/reports

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the Project Zomboid community
- RCON protocol based on Valve's Source RCON specification
- Inspired by [gorcon/rcon-cli](https://github.com/gorcon/rcon-cli)

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/pz-admin-tool/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/pz-admin-tool/discussions)
- **Project Zomboid:** [Official Forums](https://theindiestone.com/forums/)

## Changelog

### v1.0.0 (2025-01-26)
- Initial release
- Player management (kick, ban, admin, teleport)
- Server commands and monitoring
- Mods viewer with orphaned Workshop ID detection
- Logs viewer
- Persistent RCON connection
- Config file support

---

**Made with ❤️ for the Project Zomboid community**
