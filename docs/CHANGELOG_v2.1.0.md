# PZ Admin Tool v2.1.0 - Skills Tab & Settings Reorganization

## 🎯 Major Changes

### ✨ New Features

**1. New "⭐ Skills & XP" Tab**
- Dedicated tab for all 34 Build 42 skill XP multipliers
- Better organization by category:
  - Physical & Movement (6 skills)
  - Weapon Skills (9 skills)
  - Crafting & Building (12 skills)
  - Survival & Gathering (7 skills)
- Moved from Animals & Nature tab for better UX

**2. Settings Verification**
- ✅ ALL settings verified against actual Build 42.13.2 files
- ✅ Correct LUA/INI marking for every setting
- ✅ 181 settings now properly marked with `is_lua=True`

### 🔧 Fixes

**Fixed 70+ Incorrect Markings:**
- Added missing `is_lua=True` to 70+ settings that were in SandboxVars.lua
- Settings like Speed, Cognition, DayLength, Animals, etc. now correctly marked
- Tool will now save these to the correct file (Lua vs INI)

**Tab Organization:**
- 11 tabs total (was 10)
- Skills separated for easier access
- Clear visual indicators (⭐ for Skills, 🐄 for Animals)

## 📊 What's Changed

**Before v2.1:**
- 10 tabs
- Skills mixed in Animals tab
- 70 settings incorrectly marked as INI (should be LUA)

**After v2.1:**
- 11 tabs
- Dedicated Skills & XP tab
- ALL settings correctly marked
- Better organization

## ✅ Current Coverage

- **Total Settings:** 191
- **Lua Settings:** 181 (verified against Build 42.13.2)
- **INI Settings:** 10 (verified against Build 42.13.2)
- **Skill XP Multipliers:** All 34 Build 42 skills
- **Build 42 Coverage:** ~40% of all settings

## 🎮 Tab Layout (v2.1)

1. **Basic Server** - INI settings (server config)
2. **Gameplay** - Core gameplay (LUA)
3. **Zombies** - Zombie behavior (LUA)
4. **⭐ Skills & XP** - All 34 skill multipliers (LUA) ← NEW!
5. **Advanced** - Advanced options (LUA)
6. **Loot Details** - Loot categories & factors (LUA)
7. **World & Environment** - World settings (LUA)
8. **Vehicles** - Vehicle settings (LUA)
9. **Survival & Health** - Health & survival (LUA)
10. **Combat & Meta** - Combat & meta events (LUA)
11. **🐄 Animals & Nature** - Build 42 animals (LUA, skills removed)

## 🔍 Verification

All settings verified against:
- `/servertest_SandboxVars.lua` (Build 42.13.2)
- `/servertest.ini` (Build 42.13.2)

## ⚠️ Important Notes

**LUA vs INI:**
- **LUA settings** go in `SandboxVars.lua` (sandbox/gameplay settings)
- **INI settings** go in `server.ini` (server configuration)
- This was incorrectly mixed before v2.1

**Skill Variable Names:**
- Variable names in config ≠ in-game display names
- Example: `Lightfoot` in config = "Lightfooted" in-game
- Tool shows both: "Lightfoot (Lightfooted)"

## 🚀 Upgrade from v2.0.1

No breaking changes! Your existing config will work fine.

**Recommended:**
1. Update to v2.1.0
2. Open Settings Editor
3. Check new Skills & XP tab
4. Review animal settings (skills removed from that tab)
5. Save to ensure correct file placement

## 📝 TODO for v2.2

- [ ] Add remaining ~130 Build 42 LUA settings
- [ ] Add validation on save
- [ ] Build 41 compatibility toggle
- [ ] Import/export settings profiles

## 🙏 Thanks

Thanks to the community for catching the LUA/INI marking issues!

---

**Full details:** See v2.1.0_PLAN.md for complete technical breakdown.
