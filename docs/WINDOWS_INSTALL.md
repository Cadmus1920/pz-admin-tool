# Windows Installation Guide

Two ways to run PZ Admin Tool on Windows:

## Option 1: Standalone Executable (Easiest)

**No Python installation required!**

1. Download `PZ-Admin-Tool-vX.X.X-Windows.exe` from [Releases](https://github.com/Cadmus1920/pz-admin-tool/releases)
2. Double-click to run
3. That's it!

**Note:** Windows Defender may show a warning (false positive). Click "More info" → "Run anyway"

## Option 2: Run Python Script

If you have Python installed:

1. Download `pz_admin_tool.py` from [Releases](https://github.com/Cadmus1920/pz-admin-tool/releases)
2. Open Command Prompt in the download folder
3. Run: `python pz_admin_tool.py`

### Installing Python (if needed)

1. Download Python from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation
3. Install with default options

## Troubleshooting

### "Windows protected your PC"

This is a false positive from Windows SmartScreen (common with PyInstaller).

**Solution:**
1. Click "More info"
2. Click "Run anyway"

### "VCRUNTIME140.dll was not found"

You need Visual C++ Redistributable.

**Solution:**
Download and install: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Antivirus Blocking

Some antivirus software may flag the executable.

**Solution:**
1. Add exception for PZ-Admin-Tool.exe
2. Or use the Python script version (Option 2)

### Can't Connect to Server

Make sure:
- Server RCON is enabled in server settings
- RCON password is correct
- Port 16261 (or your RCON port) is open
- Firewall allows the connection

## First Run

1. Launch the tool
2. Enter your server details:
   - Host: Your server IP (or `localhost` if local)
   - Port: 16261 (default RCON port)
   - Password: Your RCON password
3. Click "Connect"

## Configuration Files

Settings are saved in your user folder:
```
C:\Users\YourName\.pz_admin_tool_config.json
C:\Users\YourName\.pz_admin_tool_appearance.json
C:\Users\YourName\.pz_admin_tool_scheduler.json
C:\Users\YourName\.pz_admin_tool_server_control.json
```

You can delete these to reset settings.

## Server Path

For advanced features (mods, logs), you need to set the server path.

**Common paths:**
- Steam Windows: `C:\Program Files (x86)\Steam\steamapps\common\Project Zomboid Dedicated Server`
- Steam Linux (via WSL): `/mnt/c/path/to/server`

## Performance

- First launch may be slow (unpacking)
- Subsequent launches are faster
- Minimal CPU/RAM usage (~50MB)

## Updates

Download the latest .exe from Releases. No uninstall needed - just replace the old .exe.

## Need Help?

- Check [Documentation](https://github.com/Cadmus1920/pz-admin-tool/blob/main/README.md)
- Open an [Issue](https://github.com/Cadmus1920/pz-admin-tool/issues)
- Read [Commands Guide](https://github.com/Cadmus1920/pz-admin-tool/blob/main/docs/COMMANDS.md)
