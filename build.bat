@echo off
title Werewolf Bot Builder
color 0A
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   WEREWOLF DISCORD BOT BUILDER
echo ========================================
echo.

REM ── Baca versi dari version.json ─────────────────────────────
set VERSION=v1.0.0
if exist version.json (
    for /f "tokens=2 delims=:, " %%A in ('findstr "version" version.json') do (
        set RAW=%%A
        set VERSION=!RAW:"=!
    )
)
echo [INFO] Versi: %VERSION%

REM ── Cek icon ─────────────────────────────────────────────────
echo.
if exist icon.ico (
    echo [OK] Icon ditemukan: icon.ico
) else (
    echo [WARN] Icon tidak ditemukan, membuat default...
    python create_icon.py 2>nul
    if exist icon.ico (
        echo [OK] Icon default berhasil dibuat
    ) else (
        echo [ERROR] Gagal membuat icon
        pause
        exit /b 1
    )
)

REM ── 1. Bersihkan build sebelumnya ────────────────────────────
echo.
echo [1/5] Membersihkan build sebelumnya...
rmdir /s /q build  2>nul
rmdir /s /q dist   2>nul
del   /q   *.spec  2>nul
echo [OK] Selesai

REM ── 2. Install requirements ──────────────────────────────────
echo.
echo [2/5] Menginstall requirements...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Gagal install requirements
    pause
    exit /b 1
)
echo [OK] Requirements terpasang

REM ── 3. Build executable ──────────────────────────────────────
echo.
echo [3/5] Membangun executable...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "WerewolfBot" ^
    --icon="icon.ico" ^
    --add-data "Lang;Lang" ^
    --add-data "Pic;Pic" ^
    --add-data "bot;bot" ^
    --add-data "gui;gui" ^
    --add-data "version.json;." ^
    --add-data "updater.py;." ^
    --add-data "gui\_secret.py;gui" ^
    --hidden-import discord ^
    --hidden-import requests ^
    --hidden-import PIL ^
    --hidden-import asyncio ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import xml.etree.ElementTree ^
    --hidden-import zipfile ^
    --hidden-import tempfile ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build gagal!
    pause
    exit /b 1
)
echo.
echo [OK] Build berhasil

REM ── 4. Siapkan folder release ────────────────────────────────
echo.
echo [4/5] Menyiapkan folder release...

set RELEASE_DIR=release
set RELEASE_NAME=WerewolfBot-%VERSION%

rmdir /s /q %RELEASE_DIR% 2>nul
mkdir %RELEASE_DIR%

REM File utama
copy dist\WerewolfBot.exe %RELEASE_DIR%\                  >nul
copy version.json          %RELEASE_DIR%\                  >nul
copy updater.py            %RELEASE_DIR%\                  >nul
if exist icon.ico   copy icon.ico   %RELEASE_DIR%\        >nul
if exist README.md  copy README.md  %RELEASE_DIR%\        >nul

REM Folder pendukung
if exist Lang xcopy Lang %RELEASE_DIR%\Lang\ /E /I /Y /Q  >nul
if exist Pic  xcopy Pic  %RELEASE_DIR%\Pic\  /E /I /Y /Q  >nul

echo [OK] Folder release siap

REM ── 5. Buat ZIP release ──────────────────────────────────────
echo.
echo [5/5] Membuat ZIP release...

powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%RELEASE_NAME%.zip' -Force"

if errorlevel 1 (
    echo [ERROR] Gagal membuat ZIP
    pause
    exit /b 1
)
echo [OK] ZIP berhasil: %RELEASE_NAME%.zip

REM ── Ringkasan ─────────────────────────────────────────────────
echo.
echo ========================================
echo   BUILD SELESAI!
echo ========================================
echo.
echo   Versi       : %VERSION%
echo   Executable  : dist\WerewolfBot.exe
echo   Release ZIP : %RELEASE_NAME%.zip
echo.
echo   Isi ZIP (untuk GitHub Release):
echo   - WerewolfBot.exe
echo   - updater.py
echo   - version.json
echo   - Lang\
echo   - Pic\
echo.
echo   Langkah upload ke GitHub:
echo   1. Buka repo GitHub kamu
echo   2. Releases ^> Create a new release
echo   3. Tag: %VERSION%
echo   4. Upload: %RELEASE_NAME%.zip
echo   5. Publish release
echo.
echo ========================================
pause