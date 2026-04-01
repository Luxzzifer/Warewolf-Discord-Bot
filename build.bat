@echo off
title Werewolf Bot Builder
color 0A

echo.
echo ========================================
echo   🐺 WEREWOLF DISCORD BOT BUILDER
echo ========================================
echo.

REM Check icon
if exist icon.ico (
    echo [OK] Icon file found: icon.ico
) else (
    echo [WARNING] Icon file not found!
    echo Creating default icon...
    python create_icon.py 2>nul
    if exist icon.ico (
        echo [OK] Default icon created
    ) else (
        echo [ERROR] Cannot create icon
        pause
        exit /b 1
    )
)

echo.
echo [1/4] Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

echo.
echo [2/4] Installing requirements...
pip install -r requirements.txt

echo.
echo [3/4] Building executable with icon...
pyinstaller --onefile --windowed --name "WerewolfBot" --icon="icon.ico" --add-data "Lang;Lang" --add-data "Pic;Pic" --add-data "bot;bot" --hidden-import discord --hidden-import requests --hidden-import PIL --hidden-import asyncio --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.scrolledtext main.py

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Creating release package...
set VERSION=v1.0.0
set RELEASE_NAME=WerewolfBot-%VERSION%

rmdir /s /q release 2>nul
mkdir release

copy dist\WerewolfBot.exe release\
copy icon.ico release\ 2>nul

if exist Lang xcopy Lang release\Lang\ /E /I /Y
if exist Pic xcopy Pic release\Pic\ /E /I /Y

powershell Compress-Archive -Path release\* -DestinationPath %RELEASE_NAME%.zip -Force

echo.
echo ========================================
echo   🎉 BUILD COMPLETE! 🎉
echo ========================================
echo.
echo   📁 Executable: dist\WerewolfBot.exe
echo   🖼️ Icon: Applied successfully
echo   📦 Release ZIP: %RELEASE_NAME%.zip
echo.
echo   Icon will appear in:
echo   - Windows File Explorer
echo   - Taskbar while running
echo   - Alt+Tab switcher
echo   - Desktop shortcut
echo.
echo ========================================
pause