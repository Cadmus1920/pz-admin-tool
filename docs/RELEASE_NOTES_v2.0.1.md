# PZ Admin Tool v2.0.1 - Critical Skills Fix

## 🚨 Critical Update

This version fixes a **critical bug** in v2.0.0 where skill XP multipliers used incorrect variable names that would have corrupted server configuration files.

**If you used v2.0.0, please update immediately!**

## ✅ What's Fixed in v2.0.1

### Skill XP Variable Names Corrected
- ✅ Fixed `Lightfooted` → `Lightfoot`
- ✅ Fixed `Sneaking` → `Sneak`
- ✅ Fixed `Foraging` → `PlantScavenging`
- ✅ Fixed `Metalworking` → `MetalWelding`

### Added Missing Skills (5)
- ✅ Masonry
- ✅ FlintKnapping (Knapping)
- ✅ Glassmaking
- ✅ Husbandry (Animal Care)
- ✅ Tracking

### Complete Coverage
**All 34 Build 42 Skills Included:**
- Physical & Movement (6): Fitness, Strength, Sprinting, Lightfoot, Nimble, Sneak
- Weapon Skills (9): Axe, Blunt, SmallBlunt, LongBlade, SmallBlade, Spear, Maintenance, Aiming, Reloading
- Crafting & Building (12): Woodwork, Cooking, Doctor, Electricity, MetalWelding, Mechanics, Tailoring, Blacksmith, Pottery, Carving, Masonry, FlintKnapping, Glassmaking
- Survival & Gathering (7): Farming, Fishing, Trapping, PlantScavenging, Butchering, Husbandry, Tracking

### UI Improvements
- Labels now show both variable name and in-game name
- Example: "Lightfoot (Lightfooted)" helps users understand the mapping
- Fixed max value from 10.0 to 1000.0 (actual game maximum)

## 📦 What's New in v2.0 Series

### Removed Invalid Settings (10)
Cleaned out Build 41 settings that don't exist in Build 42:
- AimTime, BaseFirearmRecoil, FirearmDamage
- LootRespawn, MeleeWeaponConditionLowerChance, MeleeWeaponDamage
- ProperZombies, RecoilDelay, ZombiesHours, ZombiesRespawnPercent

### Added Critical Settings (30+)

**Build 42 Loot System:**
- HoursForLootRespawn (0-2000 hours)
- ExtremeLootFactor, RareLootFactor, CommonLootFactor, AbundantLootFactor

**Utilities:**
- WaterShutModifier, ElecShutModifier

**Start Date:**
- StartYear (1993-2000)

**All 34 Skill XP Multipliers** (Build 42)

### Features from v1.6
- ✅ SFTP remote server support
- ✅ Build 41/42 version selector
- ✅ Animals & Nature tab (18 settings)
- ✅ Mod search functionality
- ✅ Dark theme for raw file viewer
- ✅ Complete RCON player management

## 📊 Coverage

- **Valid Settings:** 100+ (all verified against actual Build 42.13.2)
- **Build 42 Coverage:** ~37% of all settings
- **Critical Settings:** 100% coverage

## 🎯 Verified Against

All settings verified using actual vanilla Build 42.13.2 server files:
- servertest_SandboxVars.lua
- servertest.ini

## ⚠️ Migration from v2.0.0

If you used v2.0.0 and changed skill XP settings:
1. Backup your current SandboxVars.lua
2. Update to v2.0.1
3. Reconfigure skill settings using the tool
4. The tool will now save with correct Build 42 variable names

## 📥 Installation

**Windows:**
```bash
pip install paramiko --break-system-packages
python pz_admin_tool.py
```

**Linux/Mac:**
```bash
pip3 install paramiko
python3 pz_admin_tool.py
```

## 🐛 Known Issues / TODO for v2.1

- [ ] Move XP multipliers to separate tab
- [ ] Reorganize some multipliers to their respective tabs
- [ ] Add remaining 170+ Build 42 settings
- [ ] Add save format validation

## 🙏 Credits

Special thanks to the community for testing and catching the critical variable name issues!

---

**Full Changelog:** See CHANGELOG_v2.0.0.md and CRITICAL_FIX_v2.0.1.md for complete details.
