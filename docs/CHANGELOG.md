# Changelog

All notable changes to the Project Zomboid Server Admin Tool will be documented in this file.

## [2.4.3] - 2026-02-10

### UI/UX Improvements
- **Better Status Indicator**: Connection status now more prominent with bold, larger font
- **Notification Helpers**: Added `notify_success()`, `notify_error()`, `notify_warning()` for consistent UI feedback
- **Visual Style**: Disconnect button now uses Danger style (red) for better visual clarity
- **State Management**: New `update_ui_state()` method for consistent UI updates

### User Experience
- Better visual feedback on connection success/failure
- Consistent emoji usage in notifications (✅ ❌ ⚠️)
- Improved accessibility with larger status font
- Better error messaging with styled notifications

## [2.4.2] - 2026-02-10

### Improved
- **Connection Validation**: Added `_ensure_connected()` helper for consistent connection checks across all command functions
- **Server Message Helper**: New `_send_server_message()` for centralized broadcast message sending
- **Better Logging**: Added structured logging for command execution and failures
- **Code Consistency**: Updated command functions to use connection validation helper

### Technical
- Reduced code duplication in command execution paths
- Better error tracking for debugging connection issues
- Consistent connection state validation across UI functions

## [2.4.1] - 2026-02-10

### Improved
- **Code Cleanup**: Integrated `utils.py` module into main application
- **Reduced Duplication**: Replaced inline mods/banlist parsing with reusable utility functions
- **Better Maintainability**: Path detection and file parsing now centralized in utils module

### Fixed
- **Missing Import**: Added `datetime` import (was causing startup error)
- **Treeview Font Scaling**: Fixed mods tab text clipping at larger font sizes

## [2.4.0] - 2026-02-10

### Added
- **Modular Architecture**: Extracted RCON protocol into separate `rcon.py` module for better code organization
- **Logging System**: Comprehensive logging throughout RCON client and main application for debugging
- **Utilities Module**: New `utils.py` with reusable file parsing and path detection functions
- **Test Suite**: 5 test suites covering RCON packets, socket handling, file parsing, and integration

### Improved
- **Code Quality**: Better separation of concerns with modular design
- **Maintainability**: Protocol logic now isolated and independently testable
- **Error Handling**: Explicit exception handling with detailed logging instead of silent failures
- **Documentation**: Comprehensive docstrings explaining RCON protocol implementation

### Security
- **Password Handling**: Ensured passwords are never persisted in config files (no behavioral change, but reinforced)

### Fixed
- **State Detection**: Changed from string comparison of button text to boolean `rcon.authenticated` check
- **Theme Reference**: Fixed SettingsEditorWindow accessing parent theme correctly

### Technical
- All RCON packet operations tested with unit tests
- Socket recv_all behavior validated for partial reads and EOF
- Mods/banlist file parsing tested
- Integration test with mock RCON server for full auth and command flow
- GUI smoke test validates main application still functional

## [2.3.0] - 2026-02-05

### Fixed
- **Logs Path Bug**: Fixed logs looking in wrong location (`~/Zomboid/Zomboid/Logs` instead of `~/Zomboid/Logs`)
- **Settings Editor**: Now searches multiple locations for INI and Lua files, shows where it searched
- **Path Detection**: Prioritizes `~/Zomboid` over `~/.local/share/Zomboid` when both exist
- **Smart Path Detection**: Auto-selects paths that contain actual server configuration files
- **Corruption Detection**: Now auto-fixes invalid values silently instead of showing popup every load
- **TriggerHouseAlarm Bug**: Fixed boolean settings saving correctly to Lua files
- **Ban List Path**: Fixed banlist search to use correct paths
- **Server Info**: Fixed file-based info to search correct log locations

### Improved
- **Better Error Messages**: Now shows exactly which paths were searched when files not found
- **File Selection Dialog**: Shows full paths and search locations for debugging
- **Browse Dialog**: Uses smarter starting directory based on known paths
- **Cleaner Code**: Removed all debug print statements and temp file creation
- **Better UX**: Corruption fixes logged to command output instead of blocking popups
- **Path Selection Dialog**: Pre-selects the best path option when multiple paths found

### Technical
- All file searches now use standardized multi-location search pattern
- Streamlined save_settings function (removed ~100 lines of debug code)
- Improved auto_detect_path to check for actual .ini files in Server directory
- Silent auto-repair of corrupted config values on load

## [2.2.2] - 2026-02-04

### Added
- Corruption detection and repair system
- Settings validation before saving
- Backup creation before save with verification

### Fixed
- Various settings editor improvements

## [2.1.0] - 2026-02-01

### Added
- Build 41/42 version selector
- Preset system for server settings
- Change preview before saving

### Improved
- Settings editor organization
- Tab layout and UI polish

## [2.0.0] - 2026-01-31

### Added
- **70+ Server Settings**: Expanded settings editor with 7 tabs
  - Loot Details: 19 granular loot categories with sliders
  - World & Environment: Weather, erosion, temperature, fog, generators
  - Survival & Health: Nutrition, injuries, character points, blood level
- **Slider Controls**: Visual sliders for decimal values (loot abundance, etc.)
- **Comprehensive Theme Support**: All dialogs, text areas, and canvas widgets now properly themed

### Improved
- **Dark Theme**: Completely redesigned for consistency
- **Light Theme**: Cleaner, more professional appearance
- **Dialog Sizes**: Increased default sizes for better visibility

### Fixed
- Canvas backgrounds now match theme
- Text widget colors properly applied
- All popup dialogs inherit theme correctly

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
