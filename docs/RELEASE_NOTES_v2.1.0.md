# PZ Admin Tool v2.1.0 - Major Reorganization & Build 42 Fixes

## 🎉 Major Update

Complete reorganization of settings with verified Build 42 compatibility! All settings now load correctly from actual server files.

## ✨ What's New

### 1. New "⭐ Skills & XP" Tab
- **Global XP Multiplier** at the top (overrides all individual skills when enabled)
- All 33 individual skill XP multipliers organized by category:
  - Physical & Movement (6 skills)
  - Weapon Skills (9 skills)
  - Crafting & Building (12 skills)
  - Survival & Gathering (7 skills)
- Moved from Animals tab for better organization

### 2. Cleaned Up Tabs
- **Gameplay Tab:** Now focused on Day/Time and Utilities only
- **Loot Tab:** All loot settings together (Build 42 + Build 41 legacy)
- **Skills Tab:** All XP-related settings in one place

### 3. Complete Settings Verification
- ✅ All 191 settings verified against actual Build 42.13.2 files
- ✅ 181 Lua settings correctly marked with `is_lua=True`
- ✅ 10 INI settings for server configuration
- ✅ No invalid or missing settings

## 🐛 Critical Fixes

### Zombie Settings (Build 42 Compatibility)
All zombie settings had **Build 41 options that don't exist in Build 42**, causing blank dropdowns:

**Fixed:**
- ✅ **Zombie Speed** - Removed non-existent option 5, now has correct 1-4 options
- ✅ **Zombie Strength** - Removed options 5-6, fixed naming conflict with Strength XP
- ✅ **Zombie Toughness** - Removed options 5-6, now has correct 1-4 options
- ✅ **Zombie Health Impact** - Changed from choice to boolean (true/false) as in Build 42
- ✅ **ZombieLore** - Removed (was a container, not an actual setting)

### Settings That Were Showing Blank
**Before v2.1:**
- Zombie Strength: BLANK (naming conflict)
- Zombie Health Impact: BLANK (wrong type)
- Speed/Toughness: Could show blank with extra options

**After v2.1:**
- ✅ All zombie settings load and display correctly
- ✅ Values match what's in your files
- ✅ No more blank dropdowns

### Global XP Feature Now Accessible
**Added to Skills Tab:**
- `GlobalToggle` - Enable/disable global multiplier (checkbox)
- `Global` - Global XP multiplier value (slider 0.01-1000)
- Clear UI showing when global overrides individual skills

## 📊 Tab Organization (v2.1)

1. **Basic Server** - Server configuration (INI)
2. **Gameplay** - Day/Time, Water/Elec shutoff (LUA)
3. **Zombies** - All zombie behavior (LUA)
4. **⭐ Skills & XP** - Global + 33 individual skills (LUA) ← NEW!
5. **Advanced** - Advanced options (LUA)
6. **Loot Details** - Build 42 + Build 41 loot (LUA)
7. **World & Environment** - World settings (LUA)
8. **Vehicles** - Vehicle settings (LUA)
9. **Survival & Health** - Health & survival (LUA)
10. **Combat & Meta** - Combat & meta events (LUA)
11. **🐄 Animals & Nature** - Build 42 animals (LUA)

## 🔧 Technical Changes

### Removed Settings
- **Strength XP** - Removed from Skills tab due to naming conflict with Zombie Strength. Users can use Global XP multiplier instead.
- **XpMultiplier, FoodLoot, WeaponLoot, OtherLoot, LootAbundance** - Moved from Gameplay to appropriate tabs
- **ZombieLore** - Removed (not a real setting, just a container)

### Added Settings to Correct Tabs
- Global XP settings → Skills & XP tab
- Build 41 loot settings → Loot Details tab
- Better organization overall

## ✅ Verified Against

- User's actual running Build 42.13.2 server
- Vanilla Build 42.13.2 default files  
- Build 41 comparison for legacy settings
- All nested structures (ZombieLore, MultiplierConfig) properly handled

## 📝 Known Limitations

### Naming Conflicts
Due to nested structures in the Lua file, some settings share names:
- `Strength` appears in both ZombieLore (zombie damage) and MultiplierConfig (XP multiplier)
- Tool prioritizes zombie behavior settings
- XP can still be adjusted via Global multiplier

### Nested Structures
Settings inside `ZombieLore` and `MultiplierConfig` are accessed with simple regex. This works for loading/saving but means:
- The tool doesn't understand the nesting hierarchy
- Settings with duplicate names will conflict
- Future versions may add proper nested structure support

## 🚀 Upgrade from v2.0.1

No breaking changes! Your existing configs work fine.

**Recommended steps:**
1. Update to v2.1.0
2. Load your server files
3. Check the new Skills & XP tab
4. Verify zombie settings display correctly
5. Save to ensure correct format

## 💡 Usage Tips

### For XP Adjustment:
**Option A - Simple:**
- Enable "Use Global Multiplier" in Skills tab
- Set Global to 2.0 → All skills gain XP 2x faster

**Option B - Custom:**
- Disable Global multiplier
- Adjust each skill individually (33 available)
- Note: Strength XP removed, use Global instead

### For Loot:
- Use **Build 42 settings** at top (better control)
- **Build 41 legacy** settings at bottom for compatibility

## 🐛 Bug Fixes

- Fixed Speed showing extra option that caused blank display
- Fixed Toughness showing extra options
- Fixed Zombie Health Impact type (choice → boolean)
- Fixed Zombie Strength naming conflict
- Fixed all settings now use correct `is_lua=True` marking
- Removed ZombieLore fake setting

## 📦 Files Changed

- `pz_admin_tool.py` - Main tool with all fixes and reorganization

---

## 🙏 Special Thanks

Thanks to the community for testing and reporting the blank settings issues! Your actual server files helped identify all the Build 41 vs Build 42 incompatibilities.

---

**Full Technical Details:**
- See BLANK_SETTINGS_FIX_COMPLETE.md for complete issue analysis
- See ZOMBIE_SETTINGS_FIX.md for Build 41 vs 42 comparison
- See v2.1.0_CLEANUP_SUMMARY.md for tab reorganization details
