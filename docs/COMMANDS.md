# Project Zomboid RCON Commands Reference

Complete reference for RCON commands available in Project Zomboid.

## Player Management

### Kick Player
```
kickuser "username"
```
Kicks a player from the server.

### Ban Player
```
banuser "username" [-ip] [-r "reason"]
```
Bans a player. Optional flags:
- `-ip` - Also ban IP address
- `-r "reason"` - Specify ban reason

### Unban Player
```
unbanuser "username"
```
Removes a player from the ban list.

### Set Access Level
```
setaccesslevel "username" <level>
```
Levels:
- `admin` - Full admin powers
- `moderator` - Limited admin
- `observer` - Can observe only
- `none` - Regular player (removes admin)

### Grant/Revoke Admin
```
grantadmin "username"
removeadmin "username"
```

## Player Abilities

### God Mode
```
godmod "username"
```
Toggles invincibility.

### Invisibility
```
invisible "username"
```
Makes player invisible to zombies.

### No Clip
```
noclip "username"
```
Allows flying through walls.

### Teleport
```
teleport "player1" "player2"
```
Teleports player1 to player2's location.

### Teleport to Coordinates
```
teleportto <x> <y> <z>
```
Teleports you to specific coordinates.

## Item Management

### Add Item
```
additem "username" "module.item" [count]
```
Examples:
```
additem "Randy" "Base.Axe" 1
additem "Randy" "Base.Pistol" 1
additem "Randy" "Base.Shotgun" 5
```

### Add XP
```
addxp "username" <skill>=<amount>
```
Example:
```
addxp "Randy" Woodwork=2
addxp "Randy" Fitness=5
```

## Vehicle Management

### Add Vehicle
```
addvehicle "script" "username"
```
Examples:
```
addvehicle "Base.VanAmbulance" "Randy"
addvehicle "Base.PickUpTruck" "Randy"
```

## Server Control

### Save Server
```
save
```
Saves the current game state.

### Server Message
```
servermsg "message"
```
Broadcasts a message to all players.
**Note:** Spaces are converted to underscores.

### Reload Options
```
reloadoptions
```
Reloads server configuration without restart.

### Quit
```
quit
```
Shuts down the server gracefully.

## Weather & Time

### Start Rain
```
startrain
```

### Stop Rain
```
stoprain
```

### Set Time
```
settime <hour> <minute>
```
Example: `settime 12 0` (sets to noon)

## Server Information

### Players
```
players
```
Lists connected players.

### Help
```
help
```
Shows available commands (may return empty in some versions).

### Server Info
```
serverinfo
```
Displays server information (may not be available in all versions).

## Advanced Commands

### Chopper Event
```
chopper
```
Triggers helicopter event.

### Gunshot
```
gunshot <x> <y> <z>
```
Creates gunshot sound at coordinates.

### Alarm
```
alarm
```
Sounds building alarm at admin position (must be in a room).

### Add User (Whitelist)
```
adduser "username" "password"
```
Adds user to whitelist.

### Add All White List
```
addalltowhitelist
```
Adds all connected users to whitelist.

### Remove White List
```
removewhitelist "username"
```

### Ban List
```
banlist
```
Shows all banned users.

### Show Options
```
showoptions
```
Displays server options.

### Change Options
```
changeoption <option> "<value>"
```
Changes server option.

### Voice Ban
```
voiceban "username" [-true/-false]
```

## Command Notes

### Common Issues

1. **Empty Responses:**
   - Many commands execute successfully but return no text
   - Check server logs or in-game to verify

2. **Spacing:**
   - Always use quotes around usernames: `"username"`
   - Server messages replace spaces with underscores
   - Commands are case-sensitive

3. **Player Names:**
   - Use exact username (case-sensitive)
   - Players must be fully loaded in-game
   - Main menu doesn't count as "connected"

### Testing Commands

Use the Commands tab in the admin tool to:
1. See raw command output
2. Test commands before using action buttons
3. Execute custom/advanced commands not in UI

### Useful Command Combinations

**Remove All Admin Powers:**
```
setaccesslevel "username" none
godmod "username"
invisible "username"
noclip "username"
```

**Prepare for Server Restart:**
```
servermsg "Server restarting in 5 minutes"
save
quit
```

**Give Full Admin Setup:**
```
setaccesslevel "username" admin
godmod "username"
noclip "username"
```

## References

- [Project Zomboid Wiki](https://pzwiki.net/)
- [Official Forums](https://theindiestone.com/forums/)
- [Steam Discussions](https://steamcommunity.com/app/108600/discussions/)
