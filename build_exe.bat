@echo off
REM Windows Build Script for PZ Admin Tool
REM Creates a standalone .exe file

echo ====================================
echo PZ Admin Tool - Windows Build Script
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller already installed
)

echo.
echo [2/4] Cleaning previous build...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "PZ-Admin-Tool.spec" del /q PZ-Admin-Tool.spec

echo.
echo [3/4] Building executable...
echo This may take 1-2 minutes...
pyinstaller --onefile --windowed --name "PZ-Admin-Tool" pz_admin_tool.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying build...
if exist "dist\PZ-Admin-Tool.exe" (
    echo.
    echo ====================================
    echo SUCCESS! Build completed.
    echo ====================================
    echo.
    echo Executable location: dist\PZ-Admin-Tool.exe
    echo File size:
    dir "dist\PZ-Admin-Tool.exe" | find "PZ-Admin-Tool.exe"
    echo.
    echo You can now distribute this .exe file.
    echo Users do NOT need Python installed to run it.
    echo.
    echo To test: Double-click dist\PZ-Admin-Tool.exe
    echo.
) else (
    echo ERROR: Executable not found in dist folder
    pause
    exit /b 1
)

pause
