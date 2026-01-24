# Installation & Setup Guide

Complete guide for setting up the PZ Admin Tool.

## Prerequisites

### System Requirements
- **OS:** Linux (tested on Ubuntu 24)
- **Python:** 3.7 or higher
- **Server:** Project Zomboid Dedicated Server
- **Access:** Server console/SSH access

### Check Python Version
```bash
python3 --version
# Should show 3.7 or higher
```

## Installation Steps

### 1. Install Dependencies

```bash
# Update package list
sudo apt-get update

# Install Python 3 and TkInter
sudo apt-get install python3 python3-tk

# Verify installation
python3 -c "import tkinter; print('TkInter OK')"
```

### 2. Download the Tool

**Option A: Git Clone (Recommended)**
```bash
cd ~
git clone https://github.com/yourusername/pz-admin-tool.git
cd pz-admin-tool
```

**Option B: Direct Download**
```bash
cd ~
wget https://github.com/yourusername/pz-admin-tool/archive/main.zip
unzip main.zip
cd pz-admin-tool-main
```

### 3. Configure Server RCON

#### Find Your Server Config

Common locations:
```bash
# Systemd service user
/home/zomboid/Zomboid/Server/servertest.ini

# Your user
~/Zomboid/Server/servertest.ini

# Custom location
/path/to/your/server/Zomboid/Server/servertest.ini
```

#### Edit the Config

```bash
# Edit with nano
nano ~/Zomboid/Server/servertest.ini

# Or with vim
vim ~/Zomboid/Server/servertest.ini
```

#### Add RCON Settings

Find and modify these lines (or add if missing):

```ini
RCONPort=16261
RCONPassword=YourSecurePassword123
```

**Password Guidelines:**
- Use **alphanumeric only** (A-Z, a-z, 0-9)
- Avoid special characters (!, @, #, $, etc.)
- Minimum 12 characters
- Examples: `ServerAdmin2025`, `PZAdmin123456`

**Save and exit:**
- Nano: `Ctrl+X`, then `Y`, then `Enter`
- Vim: `Esc`, then `:wq`, then `Enter`

### 4. Restart Server

Find your service name:
```bash
systemctl list-units --type=service | grep -i zomboid
```

Restart:
```bash
sudo systemctl restart zomboidserver
# or whatever your service is called
```

Wait 30 seconds for full startup:
```bash
sleep 30
```

### 5. Verify RCON is Working

Check if port is listening:
```bash
sudo netstat -tulpn | grep 16261
```

Should show something like:
```
tcp6  0  0 :::16261  :::*  LISTEN  12345/ProjectZomboid
```

### 6. Test RCON (Optional but Recommended)

Using rcon-cli:
```bash
# Download rcon-cli
wget https://github.com/gorcon/rcon-cli/releases/download/v0.10.3/rcon-0.10.3-amd64_linux.tar.gz
tar -xzf rcon-0.10.3-amd64_linux.tar.gz

# Test
./rcon -a 127.0.0.1:16261 -p YourPassword players
```

Should return:
```
Players connected (0):
```

### 7. Run the Admin Tool

```bash
python3 pz_admin_tool.py
```

## First Time Setup

### In the GUI:

1. **Connection Settings:**
   - Host: `127.0.0.1` (if on same server)
   - Port: `16261` (or your RCON port)
   - Password: Your RCON password
   - Check "Show" to verify password

2. **Click Connect**
   - Should show "Status: Connected" in green
   - If failed, see Troubleshooting below

3. **Set Server Path (Optional):**
   - Click "Auto-Detect"
   - Or manually enter: `/home/zomboid/Zomboid`
   - Needed for Mods and Logs tabs

4. **Test Features:**
   - Go to Commands tab
   - Click "Show Players"
   - Should see player list in output

## Configuration File

The tool creates `pz_admin_config.json`:

```json
{
    "host": "127.0.0.1",
    "port": "16261",
    "server_path": "/home/zomboid/Zomboid"
}
```

**Security:** Password is NOT saved - must be entered each session.

## Troubleshooting

### "Authentication Failed"

**Check password:**
```bash
# View current password (exactly as saved)
grep RCONPassword ~/Zomboid/Server/servertest.ini

# Check for hidden characters
cat -A ~/Zomboid/Server/servertest.ini | grep RCONPassword
```

Should show:
```
RCONPassword=YourPassword$
```

NOT:
```
RCONPassword=YourPassword $   (extra space)
RCONPassword= YourPassword$   (space before)
```

**Fix if needed:**
```bash
# Edit config
nano ~/Zomboid/Server/servertest.ini

# Remove ANY spaces around password
# Save and restart server
sudo systemctl restart zomboidserver
sleep 30
```

### "Connection Refused"

**Check server is running:**
```bash
sudo systemctl status zomboidserver
```

Should show `Active: active (running)`

**Check RCON port:**
```bash
sudo netstat -tulpn | grep 16261
```

If nothing shown, RCON not enabled or wrong port.

**Check server logs:**
```bash
sudo journalctl -u zomboidserver -n 50 | grep -i rcon
```

### "Port Already in Use"

Another application using port 16261:
```bash
# See what's using it
sudo lsof -i :16261

# Change port in servertest.ini
RCONPort=16262
```

### Can't See Players

**Requirements:**
- Players must be fully in-game (not menu)
- RCON connection must be active
- Server must be running

**Test:**
```bash
./rcon -a 127.0.0.1:16261 -p YourPassword players
```

### Python TkInter Missing

```bash
# Install TkInter
sudo apt-get install python3-tk

# Verify
python3 -c "import tkinter"
```

## Remote Access Setup

To access from a different computer:

### 1. Firewall Configuration

```bash
# Allow RCON port
sudo ufw allow 16261/tcp
```

### 2. Update Connection Settings

In the tool:
- Host: `your.server.ip` (instead of 127.0.0.1)
- Port: `16261`
- Password: (same)

### 3. Security Warning

**RCON gives full server control!**
- Use a strong password
- Don't expose RCON to public internet
- Consider VPN or SSH tunnel for remote access

**SSH Tunnel (Recommended):**
```bash
# On your local machine
ssh -L 16261:localhost:16261 user@your.server.ip

# Then connect to localhost:16261 in the tool
```

## Running as a Service (Advanced)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/pz-admin.service
```

```ini
[Unit]
Description=PZ Admin Tool
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/pz-admin-tool
Environment="DISPLAY=:0"
ExecStart=/usr/bin/python3 pz_admin_tool.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pz-admin.service
sudo systemctl start pz-admin.service
```

## Uninstallation

```bash
# Remove files
cd ~
rm -rf pz-admin-tool

# Remove config (optional)
rm -f ~/.config/pz_admin_config.json

# Remove RCON from server (optional)
# Edit servertest.ini and remove/comment out:
# RCONPort=16261
# RCONPassword=...
```

## Getting Help

- **GitHub Issues:** Report bugs or request features
- **Documentation:** Check docs/ folder
- **Server Logs:** `sudo journalctl -u zomboidserver -f`
- **Tool Output:** Run from terminal to see debug messages

## Next Steps

- Read [COMMANDS.md](COMMANDS.md) for available RCON commands
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Explore all tabs in the tool
- Set up auto-refresh for monitoring

Enjoy managing your Project Zomboid server! 🎮
