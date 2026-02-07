# 🌐 SFTP Remote Server Support Guide

The PZ Admin Tool now supports managing remote servers via SFTP! This allows you to edit server configurations on remote/hosted servers.

## 📋 Requirements

### Install paramiko library:

**Linux:**
```bash
pip install paramiko --break-system-packages
```

**Windows:**
```bash
pip install paramiko
```

## 🚀 Quick Start

### 1. Switch to SFTP Mode

In the "📁 Server Files Access" section:
- Select: **🌐 SFTP (Remote Server)**

### 2. Enter Connection Details

- **Host:** Your server IP or hostname (e.g., `123.456.789.0` or `myserver.com`)
- **Port:** SSH port (default: `22`)
- **Username:** Your SSH username (e.g., `steam`, `root`, `ubuntu`)
- **Password:** Your SSH password
- **Remote Path:** Path to Zomboid server (e.g., `/home/steam/Zomboid`)

### 3. Test Connection

Click **🔗 Test Connection**

✅ Success: "Connected! Path exists."
⚠️ Warning: "Connected, but path not found" - check your remote path
❌ Error: Check credentials and firewall settings

### 4. Use Features Normally

Once connected, all features work the same:
- ✅ Edit Server Settings (downloads files, lets you edit, uploads back)
- ✅ Manage Mods
- ✅ View/Edit Ban Lists
- ✅ View Logs

## 🔐 SSH Key Authentication (Coming Soon)

Currently supports password authentication. SSH key support will be added in a future update.

## 💡 Tips

### Finding Your Remote Path

Common paths:
- **SteamCMD:** `/home/steam/.steam/steamapps/common/Project Zomboid Dedicated Server`
- **Steam User:** `/home/steam/Zomboid`
- **Custom:** Wherever you installed the server

### Testing SSH Connection Manually

Before using the tool, test your SSH connection:
```bash
ssh username@yourserver.com
```

If this works, SFTP will work too!

### Firewall Rules

Ensure port 22 (or your custom SSH port) is open in your firewall.

### Security

⚠️ **Password Security:**
- Your password is stored in memory only (not saved)
- Re-enter password after restarting the tool
- Consider using SSH keys once that feature is added

## 🔧 How It Works

1. **Connect:** Tool establishes SSH/SFTP connection to your server
2. **Download:** When you edit settings, files are downloaded to temp folder
3. **Edit:** You edit files locally in the GUI
4. **Upload:** On save, files are uploaded back to the server
5. **Cleanup:** Temp files are automatically deleted

## 📊 Features That Work With SFTP

✅ **Fully Supported:**
- Settings Editor (all 140+ settings)
- Mod Manager
- Ban List Editor
- Log Viewer

❌ **Not Applicable:**
- Server Control commands (start/stop/restart)
  - Use these via RCON instead
  - Or SSH directly to your server

## 🐛 Troubleshooting

### "Missing Library" Error
Install paramiko:
```bash
pip install paramiko --break-system-packages
```

### "Authentication Failed"
- Double-check username and password
- Ensure SSH password authentication is enabled
- Check: `/etc/ssh/sshd_config` should have `PasswordAuthentication yes`

### "Connection Timeout"
- Check firewall rules
- Verify server is running
- Try connecting with regular SSH first

### "Path Not Found"
- Verify the remote path is correct
- Use absolute paths (starting with `/`)
- Check directory exists: `ls -la /path/to/zomboid`

### Files Not Saving
- Check file permissions on server
- Ensure user has write access
- Test: `touch /path/to/zomboid/test.txt`

## 🎯 Example Setup

### Typical VPS Setup:

```
Host: 123.45.67.89
Port: 22
Username: steam
Password: ********
Remote Path: /home/steam/Zomboid
```

### AWS/Cloud Setup:

```
Host: ec2-12-345-67-89.compute-1.amazonaws.com
Port: 22
Username: ubuntu
Password: ********
Remote Path: /home/ubuntu/zomboid-server
```

### Dedicated Server:

```
Host: myserver.example.com
Port: 22
Username: pzadmin
Password: ********
Remote Path: /opt/zomboid/server
```

## 🔄 Workflow Example

1. **Connect to RCON** (for player commands)
   - Host: your-server.com
   - Port: 16261
   - Password: your-rcon-pass

2. **Connect to SFTP** (for file access)
   - Host: your-server.com
   - Port: 22
   - Username: steam
   - Remote Path: /home/steam/Zomboid

3. **Use Features:**
   - Kick/ban players via RCON ✅
   - Edit server settings via SFTP ✅
   - Change mods via SFTP ✅
   - View logs via SFTP ✅

4. **Restart Server:**
   - SSH to server: `ssh steam@your-server.com`
   - Run: `systemctl restart zomboid` (or your restart command)

## 🎉 Benefits

- ✅ **No need to SSH manually** for file edits
- ✅ **GUI interface** for all settings
- ✅ **Automatic backups** before saving
- ✅ **Same interface** for local and remote servers
- ✅ **Works with any hosting provider** that allows SSH

## 📝 Notes

- SFTP connection stays open while tool is running
- Files are temporarily downloaded for editing
- Backups are created on the remote server
- Connection is closed when tool closes

---

**Need Help?** Open an issue on GitHub or check the main README.md
