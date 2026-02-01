# Changelog

All notable changes to the Project Zomboid Server Admin Tool will be documented in this file.

## [1.2.0] - 2026-01-31

### Added
- **70+ Server Settings**: Expanded settings editor with 7 tabs
  - Loot Details: 19 granular loot categories with sliders
  - World & Environment: Weather, erosion, temperature, fog, generators
  - Survival & Health: Nutrition, injuries, character points, blood level
- **Slider Controls**: Visual sliders for decimal values (loot abundance, etc.)
- **Comprehensive Theme Support**: All dialogs, text areas, and canvas widgets now properly themed

### Improved
- **Dark Theme**: Completely redesigned for consistency
  - All Canvas widgets themed
  - All ScrolledText widgets themed
  - All dialog windows themed
  - Raw file viewer themed
  - Server info, logs, and command output themed
- **Light Theme**: Cleaner, more professional appearance
- **Dialog Sizes**: Increased default sizes for better visibility
  - File selection: 600x400 → 700x500
  - Settings editor: 800x600 → 900x700
  - Server control: 600x400 → 700x500

### Fixed
- Canvas backgrounds now match theme (no more white rectangles)
- Text widget colors properly applied at creation
- All popup dialogs inherit theme correctly
- Button visibility in dialogs improved

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
