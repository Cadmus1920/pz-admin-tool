# 🔄 PZ Server Restart Timer - Standalone

A lightweight, dedicated application for scheduling automatic Project Zomboid server restarts.

## 🎯 Purpose

This is a **separate program** from the main admin tool, designed to:
- Run in the background continuously
- Handle automatic repeating server restarts
- Persist across program restarts/crashes
- Lightweight and focused on one task

## 🆚 Main Tool vs Standalone Timer

### Use Main Admin Tool When:
- ✅ Managing players, mods, bans
- ✅ Editing server settings
- ✅ Viewing logs
- ✅ One-time restarts
- ✅ Need full admin features

### Use Standalone Timer When:
- ✅ Just need automated restarts
- ✅ Want it running 24/7
- ✅ Don't need other admin features
- ✅ Minimal resource usage
- ✅ Simple "set and forget" solution

## 📋 Features

- **Repeating Restarts**: Set interval (5 min to 8 hours)
- **Player Warnings**: 30min, 15min, 10min, 5min, 1min
- **Auto-Save**: Saves server 1 minute before restart
- **Persistent State**: Survives program crashes/restarts
- **Timer Recovery**: Automatically resumes if program closes
- **RCON Integration**: Sends warnings to players
- **Next Restart Display**: Shows exact time of next restart

## 🚀 Usage

### Basic Setup

```bash
python3 pz_restart_timer.py
```

1. **Enter RCON details** (for sending warnings to players)
   - Host, Port, Password
   - Click "Connect"

2. **Enter Restart Command**
   - Example: `systemctl restart zomboid`
   - Example: `sudo /home/steam/restart_server.sh`

3. **Set Restart Interval**
   - Choose minutes (or use presets: 30m, 1h, 2h, 3h, 6h)

4. **Configure Warnings**
   - Check which warnings you want (30min, 15min, etc.)
   - Enable auto-save option

5. **Click "Start Repeating Restart Timer"**
   - Timer starts immediately
   - Runs continuously
   - Restarts automatically after each cycle

### Running in Background

**Linux (systemd service):**

Create `/etc/systemd/system/pz-restart-timer.service`:

```ini
[Unit]
Description=PZ Server Restart Timer
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/pz-admin-tool
Environment="DISPLAY=:0"
ExecStart=/usr/bin/python3 /path/to/pz_restart_timer.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pz-restart-timer
sudo systemctl start pz-restart-timer
```

**Linux (screen/tmux):**

```bash
screen -dmS restart-timer python3 pz_restart_timer.py
# Reattach with: screen -r restart-timer
```

**Windows:**

1. Create shortcut to `pz_restart_timer.py`
2. Place in `shell:startup` folder
3. Runs on Windows startup

## 💾 Configuration Files

Settings saved to:
- `~/.pz_restart_timer_config.json` - RCON, restart command, preferences
- `~/.pz_restart_timer_state.json` - Active timer state (for recovery)

## 🔄 Timer Recovery

If the program closes (crash, reboot, etc.):

1. **Reopen the program**
2. **Popup appears**: "Resume Timer? Time remaining: 45m 30s"
3. **Click Yes**: Timer resumes with correct time
4. **Click No**: Timer cancelled

Your scheduled restart will NEVER be lost!

## ⚙️ Example Use Cases

### Daily 3AM Restarts

Set interval to **24 hours** (1440 minutes), start at 3 AM.

### Every 3 Hours

Set interval to **180 minutes**, click start. Runs indefinitely.

### Maintenance Window

Set interval to **6 hours** (360 minutes) during off-peak times.

## 🆘 Troubleshooting

### Timer doesn't resume after restart
- Check if state file exists: `~/.pz_restart_timer_state.json`
- Make sure you clicked "Yes" on resume prompt

### Warnings not appearing in-game
- Verify RCON connection (status should show "Connected")
- Test RCON manually from main admin tool
- Check RCON port/password

### Restart command not working
- Test command manually in terminal first
- May need `sudo` permissions
- Check logs/output for errors

## 🔐 Security Notes

- **RCON password** is saved in plaintext in config file
- Config file location: `~/.pz_restart_timer_config.json`
- Use appropriate file permissions (chmod 600)

## 📊 Resource Usage

- **Memory**: ~20-30 MB
- **CPU**: Minimal (checks every second)
- **Network**: Only RCON traffic for warnings

## 🎨 Building Windows .exe

```bash
pyinstaller --onefile --windowed --name "PZ-Restart-Timer" pz_restart_timer.py
```

Creates standalone `.exe` for Windows users!

## 🤝 Integration

Can run **alongside the main admin tool**:
- Main tool: For administration and management
- Standalone timer: For automatic restarts

Both use separate config files and don't interfere with each other.

## 📝 Notes

- **Always test your restart command** before relying on it
- **Use repeating mode** - it's the main purpose of this tool
- **Keep it running** - minimize to tray or run as service
- **Monitor occasionally** - check that restarts are working

---

**Simple, lightweight, reliable** - just for server restarts! 🔄⏰
