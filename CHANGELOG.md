# Changelog

All notable changes to the Project Zomboid Server Admin Tool will be documented in this file.

## [1.1.0] - 2026-01-31

### Added
- **Dark Theme Support**: Toggle between light and dark themes via View menu
- **Font Scaling**: Adjust font size from 8pt to 12pt for accessibility
- **Task Scheduler**: Schedule recurring announcements and RCON commands
- **Server Control**: Start/Stop/Restart server with configurable commands
- **Live Log Streaming**: Real-time server log viewer with auto-scroll
- **Ban List Manager**: View, unban, and manage banned players
- **Settings Editor**: Edit 30+ gameplay and zombie sandbox settings
- **Mod Manager**: Simple text-based editor for mods and Workshop IDs
- **Appearance Preferences**: Persistent theme and font size settings
- **Menu Bar**: Professional menu system with Help and About dialogs

### Improved
- Teleport dialog now supports player-to-player teleportation
- Enhanced error handling with detailed error messages
- Better RCON connection stability
- Improved log file detection with multiple fallback paths

### Fixed
- Entry widgets now properly styled in dark theme
- Lua sandbox settings now correctly save to file
- Live log streaming now updates reliably
- Workshop ID browser integration with multiple fallback methods

## [1.0.0] - 2026-01-24

### Added
- Initial release
- Player management (kick, ban, admin privileges, god mode)
- RCON command executor
- Server info viewer
- Mods viewer with Workshop ID integration
- Server logs viewer
- Persistent RCON connection
- Config file support
- Auto-refresh functionality
- Password show/hide toggle
- Server path auto-detection

### Technical
- Pure Python standard library implementation
- Source RCON protocol implementation
- Dual-packet authentication handling
- SQLite database reading for server data
- Cross-platform compatibility (Linux, Windows, macOS)
