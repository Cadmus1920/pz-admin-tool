# Building Windows Executable

This guide explains how to create a standalone Windows `.exe` file that users can run without installing Python.

## Prerequisites

- Python 3.7+ installed on Windows
- Internet connection (for installing PyInstaller)

## Quick Build (Automated)

Simply run the build script:

```batch
build_exe.bat
```

This will:
1. Install PyInstaller if needed
2. Create the executable
3. Place it in the `dist/` folder

## Manual Build Instructions

### 1. Install PyInstaller

Open Command Prompt or PowerShell:

```bash
pip install pyinstaller
```

### 2. Build the Executable

Navigate to the project directory and run:

```bash
pyinstaller --onefile --windowed --name "PZ-Admin-Tool" --icon=icon.ico pz_admin_tool.py
```

**Options explained:**
- `--onefile` - Creates a single .exe file (not a folder)
- `--windowed` - No console window (GUI only)
- `--name` - Name of the executable
- `--icon` - Custom icon (optional, if you have one)

### 3. Find Your Executable

The `.exe` will be in the `dist/` folder:
```
dist/PZ-Admin-Tool.exe
```

### 4. Test It

Double-click the `.exe` to launch. It should work without Python installed!

## Distribution

### For GitHub Releases

1. Build the executable on Windows
2. Create a release on GitHub (e.g., v1.3.0)
3. Upload `PZ-Admin-Tool.exe` as an asset
4. Users can download and run directly!

### File Size

The executable will be approximately 15-30 MB due to bundled Python interpreter and libraries.

## Troubleshooting

### Antivirus False Positives

Windows Defender or other antivirus may flag the .exe as suspicious. This is common with PyInstaller executables.

**Solutions:**
1. Add exception in antivirus
2. Submit to Microsoft for analysis: https://www.microsoft.com/wdsi/filesubmission
3. Code-sign the executable (requires certificate, costs money)

### Missing DLL Errors

If users get DLL errors, they may need:
- Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe

### "Not a valid Win32 application"

Build for the correct architecture:
- For 64-bit Windows (most common): Use 64-bit Python
- For 32-bit Windows: Use 32-bit Python

## Advanced Options

### Smaller File Size

Use UPX compression (reduces size by ~40%):

```bash
pip install upx
pyinstaller --onefile --windowed --upx-dir="C:\path\to\upx" --name "PZ-Admin-Tool" pz_admin_tool.py
```

### Custom Icon

Create or download a `.ico` file and use:

```bash
pyinstaller --onefile --windowed --icon=pz_icon.ico --name "PZ-Admin-Tool" pz_admin_tool.py
```

### Debug Mode

If the .exe crashes silently, build with console to see errors:

```bash
pyinstaller --onefile --console --name "PZ-Admin-Tool-Debug" pz_admin_tool.py
```

## Clean Build

If you need to rebuild from scratch:

```bash
# Delete build artifacts
rmdir /s /q build
rmdir /s /q dist
del PZ-Admin-Tool.spec

# Rebuild
pyinstaller --onefile --windowed --name "PZ-Admin-Tool" pz_admin_tool.py
```

## Automated Builds with GitHub Actions

See `.github/workflows/build-windows.yml` for automated building on every release.

## Notes

- The executable is **portable** - no installation needed
- It can be run from USB drive, desktop, anywhere
- All dependencies are bundled inside
- First launch may be slower (unpacking)
- User settings still save to `%USERPROFILE%\.pz_admin_tool_*` files

## Testing the Executable

Before distributing:

1. Test on a clean Windows VM (no Python installed)
2. Test on Windows 10 and Windows 11
3. Test with antivirus enabled
4. Verify all features work (RCON, settings, themes, etc.)

## Support

If users have issues running the .exe:
1. Check if antivirus is blocking it
2. Try "Run as Administrator"
3. Fall back to Python version: `python pz_admin_tool.py`
