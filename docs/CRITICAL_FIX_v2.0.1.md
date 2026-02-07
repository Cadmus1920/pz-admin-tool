# ⚠️ CRITICAL FIX - Skill XP Variable Names v2.0.1

## 🚨 Issue Found
The skill XP multipliers had INCORRECT variable names that would have corrupted user config files!

## ❌ What Was Wrong (v2.0.0)

**Variable Name Errors:**
- Used `Lightfooted` → WRONG, should be `Lightfoot`
- Used `Sneaking` → WRONG, should be `Sneak`
- Used `Foraging` → WRONG, should be `PlantScavenging`
- Used `Metalworking` → WRONG, should be `MetalWelding`

**Missing Skills:**
- Masonry
- FlintKnapping (Knapping)
- Glassmaking
- Husbandry (Animal Care)
- Tracking

**Wrong Max Value:**
- Had max of 10.0 → Should be 1000.0 (actual game max)

## ✅ Fixed in v2.0.1

### All 34 Skills with EXACT Variable Names:

**Physical & Movement (6):**
1. ✅ Fitness
2. ✅ Strength
3. ✅ Sprinting
4. ✅ Lightfoot (in-game: "Lightfooted")
5. ✅ Nimble
6. ✅ Sneak (in-game: "Sneaking")

**Weapon Skills (9):**
7. ✅ Axe
8. ✅ Blunt (in-game: "Long Blunt")
9. ✅ SmallBlunt (in-game: "Short Blunt")
10. ✅ LongBlade (in-game: "Long Blade")
11. ✅ SmallBlade (in-game: "Short Blade")
12. ✅ Spear
13. ✅ Maintenance
14. ✅ Aiming
15. ✅ Reloading

**Crafting & Building (12):**
16. ✅ Woodwork (in-game: "Carpentry")
17. ✅ Cooking
18. ✅ Doctor (in-game: "First Aid")
19. ✅ Electricity (in-game: "Electrical")
20. ✅ MetalWelding (in-game: "Metalworking" or "Welding")
21. ✅ Mechanics
22. ✅ Tailoring
23. ✅ Blacksmith (in-game: "Blacksmithing")
24. ✅ Pottery
25. ✅ Carving
26. ✅ Masonry
27. ✅ FlintKnapping (in-game: "Knapping")
28. ✅ Glassmaking

**Survival & Gathering (7):**
29. ✅ Farming (in-game: "Agriculture")
30. ✅ Fishing
31. ✅ Trapping
32. ✅ PlantScavenging (in-game: "Foraging")
33. ✅ Butchering
34. ✅ Husbandry (in-game: "Animal Care")
35. ✅ Tracking

## 📝 Key Points

**Why Variable Names ≠ In-Game Names:**
- The Lua config uses programmer variable names
- The game UI shows friendly display names
- Example: Variable `Lightfoot` displays as "Lightfooted" in-game
- Using wrong variable names = settings don't save properly!

**Range Fixed:**
- Min: 0.01 (essentially disabled)
- Max: 1000.0 (actual Build 42 maximum)
- Default: 1.0 (normal XP gain)

**UI Labels Now Show Both:**
- Format: `VariableName (In-Game Name)`
- Example: "Lightfoot (Lightfooted)"
- This helps users understand the mapping!

## 🎯 Testing Confirmation

Verified against actual Build 42.13.2 SandboxVars.lua:
```lua
MultiplierConfig = {
    Lightfoot = 1.0,     -- NOT "Lightfooted"
    Sneak = 1.0,         -- NOT "Sneaking"
    PlantScavenging = 1.0,  -- NOT "Foraging"
    MetalWelding = 1.0,  -- NOT "Metalworking"
    ...
}
```

## 🚀 Impact

**Before (v2.0.0):**
- Would create invalid Lua files
- Settings wouldn't load properly
- Could corrupt server configs

**After (v2.0.1):**
- ✅ All 34 skills use exact Build 42 variable names
- ✅ Files save and load correctly
- ✅ Complete skill coverage
- ✅ Proper value ranges

## ⚠️ Migration Note

If you used v2.0.0 and changed skill XP settings:
1. Delete or backup your SandboxVars.lua
2. Use v2.0.1 to regenerate with correct variable names
3. The tool will now use proper Build 42 format

---

**This was a critical fix - thank you for catching it!** 🙏
