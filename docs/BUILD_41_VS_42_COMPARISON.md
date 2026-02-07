# Project Zomboid: Build 41 vs Build 42 Settings Comparison

## 📋 Overview

This document outlines the key differences between Build 41 (Stable) and Build 42 (Unstable) for server administration.

**Current Status (Feb 2026):**
- **Build 41.78+** - Stable, full multiplayer support, extensive mod library
- **Build 42.13.2** - Unstable beta, single-player only (MP coming), breaking changes

---

## 🔧 Server File Structure

### Both Builds Use:
- `servertest.ini` - Main server configuration
- `servertest_SandboxVars.lua` - Gameplay/sandbox settings  
- `servertest_spawnregions.lua` - Spawn point definitions
- `servertest_spawnpoints.lua` - Detailed spawn coordinates

### Key Difference:
**Build 42 servers are NOT compatible with Build 41 saves!**
- Upgrading requires a fresh world/server
- File formats are different
- Settings have different default values

---

## ⚙️ ServerOptions.ini Differences

### Settings That Are THE SAME:

**Basic Server Config:**
- `PublicName` - Server name
- `PublicDescription` - Server description
- `Password` - Server password
- `MaxPlayers` - Player limit (1-32)
- `Public` - Listed in server browser
- `Open` - Whitelist on/off
- `PVP` - PvP enabled
- `PauseEmpty` - Pause when no players
- `GlobalChat` - Global chat enabled
- `ServerWelcomeMessage` - Welcome message
- `RCONPort` - RCON port (16261 default)
- `RCONPassword` - RCON password

**Admin & Security:**
- `SafetySystem` - PvP safety toggle system
- `ShowSafety` - Show PvP status icons
- `SafetyToggleTimer` - Time to toggle PvP
- `SafetyCooldownTimer` - Cooldown between toggles

**File/Save Settings:**
- `SaveWorldEveryMinutes` - Auto-save interval
- `BackupsOnStart` - Backup on server start
- `BackupsOnVersionChange` - Backup on version change

### Settings Removed/Changed in Build 42:

**Removed in 41.66+ (Both builds):**
- `SteamPort1` and `SteamPort2` - Steam networking changed
- Various deprecated network settings

**Build 42 Specific Changes:**
- Better save file handling (automatic)
- Improved chunk caching
- Enhanced multiplayer infrastructure (when MP releases)

---

## 🧟 SandboxVars.lua - Major Differences

### Build 41 Settings (Stable)

**Core Zombie Settings:**
```lua
Zombies = 4              -- 1=Insane, 2=Very High, 3=High, 4=Normal, 5=Low, 6=None
Distribution = 1         -- 1=Urban Focused, 2=Uniform
Speed = 2                -- 1=Sprinters, 2=Fast Shamblers, 3=Shamblers, 4=Random
Strength = 2             -- 1=Superhuman, 2=Normal, 3=Weak, 4=Random
Toughness = 2            -- 1=Tough, 2=Normal, 3=Fragile, 4=Random
Transmission = 1         -- 1=Blood+Saliva, 2=Saliva Only, 3=Everyone Infected, 4=None
Mortality = 5            -- 1=Instant, 2=0-30sec, 3=0-1min, 4=0-12hrs, 5=2-3days, 6=1-2weeks, 7=Never
Cognition = 3            -- 1=Navigate+UseDoors, 2=Navigate, 3=Basic, 4=Random
Memory = 2               -- 1=Long, 2=Normal, 3=Short, 4=None, 5=Random
Sight = 2                -- 1=Eagle, 2=Normal, 3=Poor, 4=Random
Hearing = 2              -- 1=Pinpoint, 2=Normal, 3=Poor, 4=Random
```

**World Settings:**
```lua
DayLength = 3            -- 1=15min, 2=30min, 3=1hr, 4=1.5hr, 5=2hr, 6=3hr, 7=4hr, 8=5hr
StartMonth = 7           -- 1-12 (July default)
StartDay = 9             -- 1-31
WaterShut = 2            -- 1=Instant, 2=0-30days, 3=0-2mo, 4=0-6mo, 5=6-12mo, 6=Never
ElecShut = 2             -- Same as above
Temperature = 3          -- 1=VCold, 2=Cold, 3=Normal, 4=Hot
Rain = 3                 -- 1=VDry, 2=Dry, 3=Normal, 4=Rainy
```

**Loot Settings:**
```lua
LootRespawn = 1          -- 1=None, 2=EveryDay, 3=EveryWeek, 4=EveryMonth
FoodLoot = 1.0           -- Multiplier (0.5 to 3.0)
WeaponLoot = 1.0         -- Multiplier
OtherLoot = 1.0          -- Multiplier
CarSpawnRate = 3         -- 1=None, 2=Low, 3=Normal, 4=High
```

### Build 42 NEW/Changed Settings

**New Features:**
```lua
-- Animals (NEW in Build 42)
AnimalSpawn = true       -- Enable animals
AnimalPopulation = 3     -- 1=Low, 2=Normal, 3=High

-- Crafting Overhaul
CraftingDifficulty = 2   -- 1=Easy, 2=Normal, 3=Hard (Build 42 has more complex crafting)

-- Hunting/Fishing (Enhanced)
FishingDifficulty = 2    -- More detailed fishing mechanics
HuntingEnabled = true    -- Hunting system

-- Farming Changes
FarmingSpeed = 3         -- Growth rate changes
AnimalBreeding = true    -- Breed animals for resources

-- New Resource Management
WaterSource = 2          -- 1=Scarce, 2=Normal, 3=Abundant (well mechanics changed)
ClaySource = 2           -- Clay for pottery/crafting
```

**Balance Changes:**
```lua
-- Build 42 rebalanced these defaults:
XpMultiplier = 1.0       -- Same, but XP progression feels different
CalorieBurn = 1.0        -- NEW - Calorie system more important in B42
HungerRate = 3           -- Rebalanced from B41
ThirstRate = 3           -- Rebalanced from B41
```

**Removed/Deprecated:**
- Some Build 41 settings don't exist or work differently in B42
- Loot balancing changed significantly
- Book locations changed (fewer skill books)

---

## 🎮 Gameplay Differences

### Build 41 Characteristics:
- **Stable multiplayer** - 32 players max
- **Extensive mod support** - Thousands of mods available
- **Proven balance** - Years of community feedback
- **Infinite farming** - Plant once, harvest forever
- **Simpler crafting** - Straightforward recipes
- **Static world** - No animals, limited late-game

### Build 42 Characteristics:
- **No multiplayer yet** - Single-player only (MP in development)
- **Limited mods** - Most B41 mods not compatible yet
- **Experimental balance** - Actively being tuned
- **Animal husbandry** - Cows, sheep, pigs, chickens
- **Complex crafting** - Multi-step recipes, pottery, glassmaking
- **Dynamic late-game** - Animals, expanded tech tree
- **Better graphics** - Improved lighting, 3D depth buffer
- **Voice acting** - Character sounds/voices
- **New cities** - Brandenburg, Ekron, Irvington

---

## 🗺️ Map Differences

### Build 41 Map:
- Muldraugh, West Point, Riverside
- Louisville (added in later B41 updates)
- Well-established, stable

### Build 42 Map:
- All B41 locations PLUS:
  - **Brandenburg** (new city)
  - **Ekron** (new city)  
  - **Irvington** (new city)
  - **Echo Creek** (new starting location)
- Expanded southwest region
- Louisville enhancements
- More basements, bunkers, panic rooms

---

## 🔧 Admin Tool Compatibility

### What Works on Both:
✅ RCON commands (same protocol)
✅ Player management (kick, ban, admin)
✅ Basic server settings (name, password, ports)
✅ Mod manager (Workshop IDs work similarly)

### Build-Specific Differences:

**Build 41:**
- Settings editor: All settings tested and stable
- Presets: Community-verified presets
- Mods: Full compatibility

**Build 42:**
- Settings editor: May have new options
- Presets: Need adjustment for balance changes
- Mods: Limited compatibility
- Some settings may not work as expected (beta)

---

## 💡 Recommendations

### Use Build 41 If:
- ✅ You want to play multiplayer NOW
- ✅ You want stable, proven gameplay
- ✅ You want extensive mod support
- ✅ You want to avoid bugs/save wipes
- ✅ You're running a public/RP server

### Use Build 42 If:
- ✅ You're playing single-player
- ✅ You want new features (animals, crafting)
- ✅ You don't mind bugs/experimental balance
- ✅ You can tolerate save wipes
- ✅ You want to test new content
- ✅ You're okay with limited mods

### Admin Tool Usage:
**For Build 41 servers:**
- All features fully supported
- Presets work perfectly
- Settings well-tested

**For Build 42 servers:**
- Core features work (RCON, player management)
- Settings editor works but some values may differ
- Presets may need manual adjustment
- Tool shows warning about Build 42
- Some new B42 settings not in tool yet

---

## 🔮 Future: When Build 42 Goes Stable

Expected timeline: **Months to a year+** (no official date)

**What will happen:**
1. Multiplayer will be added to B42 beta
2. Extensive MP testing phase
3. Mod ecosystem will catch up
4. Balance will be finalized
5. Build 42 becomes new "Stable"
6. Build 41 becomes legacy/optional

**When that happens:**
- Servers will need fresh worlds
- Mods will need updates
- Admin tools will need updates
- Community will migrate over time

---

## 📝 Settings Migration Notes

**Cannot directly convert:**
- Build 41 saves → Build 42 (incompatible)
- Build 41 settings → Build 42 (need review)

**Can manually copy:**
- Server name, password, admin settings
- Basic gameplay preferences
- Mod lists (but mods may not work)

**Must reconfigure:**
- Sandbox values (different defaults)
- Loot balance (changed significantly)
- Crafting-related settings (new system)
- Animal settings (don't exist in B41)

---

## 🎯 Quick Reference

| Feature | Build 41 | Build 42 |
|---------|----------|----------|
| **Status** | Stable | Unstable Beta |
| **Multiplayer** | ✅ Full support | ❌ Coming soon |
| **Mods** | ✅ Thousands | ⚠️ Limited |
| **Animals** | ❌ None | ✅ Farming |
| **Crafting** | Simple | Complex |
| **Graphics** | Good | Better |
| **Stability** | Stable | Buggy |
| **Save Wipes** | None | Possible |
| **Admin Tool** | Fully supported | Mostly supported |

---

## 🆘 Support

**Build 41 Issues:**
- Check PZwiki.net (extensive documentation)
- Steam forums (very active)
- Discord communities

**Build 42 Issues:**
- Expect bugs (it's beta!)
- Report on official forums
- Check patch notes frequently
- Backup saves regularly!

---

## 📚 Resources

- **PZwiki:** https://pzwiki.net/
- **Server Settings:** https://pzwiki.net/wiki/Server_settings
- **Dedicated Server:** https://pzwiki.net/wiki/Dedicated_server
- **Build 42 Info:** https://pzwiki.net/wiki/Build_42
- **Steam Community Guides:** Extensive server setup guides
- **Reddit:** r/projectzomboid

---

**Last Updated:** February 2026 (Build 42.13.2 Unstable)

**Note:** Build 42 is actively being developed. Settings and features may change with updates!
