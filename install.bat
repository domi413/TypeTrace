@echo off
setlocal enabledelayedexpansion

:: -----------------------------
:: CONFIGURATION
:: -----------------------------
set ZIPFILE=typetrace.zip
set INSTALLDIR=C:\ProgramFiles\typetrace
set MSYS2_ROOT=C:\tools\msys64
set SHORTCUT_NAME=TypeTrace.lnk
set ICON_PATH=%INSTALLDIR%\icon.ico

:: -----------------------------
:: CHECK FOR ADMIN RIGHTS
:: -----------------------------
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] Please run this script as Administrator.
    pause
    exit /b
)

:: -----------------------------
:: CHECK FOR CHOCOLATEY
:: -----------------------------
where choco >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] Chocolatey is not installed. Please install Chocolatey first: https://chocolatey.org/install
    pause
    exit /b
)

:: -----------------------------
:: INSTALL MSYS2 IF NEEDED VIA CHOCO
:: -----------------------------
if not exist "%MSYS2_ROOT%\msys2_shell.cmd" (
    echo [INFO] MSYS2 not found. Installing via Chocolatey...
    choco install -y msys2
) else (
    echo [INFO] MSYS2 already installed.
)

:: -----------------------------
:: UNZIP APPLICATION
:: -----------------------------
echo [INFO] Extracting %ZIPFILE% to %INSTALLDIR%...
powershell -Command "Expand-Archive -LiteralPath '%ZIPFILE%' -DestinationPath '%INSTALLDIR%' -Force"

:: -----------------------------
:: INSTALL REQUIRED PACKAGES
:: -----------------------------
"%MSYS2_ROOT%\usr\bin\bash.exe" -lc ^
"pacman -Syuu --noconfirm && \
 pacman -Sy --noconfirm \
  mingw-w64-x86_64-toolchain \
  mingw-w64-x86_64-gtk4 \
  mingw-w64-x86_64-libadwaita \
  mingw-w64-x86_64-python \
  mingw-w64-x86_64-python-pip \
  mingw-w64-x86_64-python-gobject \
  mingw-w64-x86_64-meson \
  mingw-w64-x86_64-glib2 \
  mingw-w64-x86_64-desktop-file-utils"

:: -----------------------------
:: CREATE START MENU SHORTCUT
:: -----------------------------
set VBS_CREATE=%TEMP%\create_shortcut.vbs
(
    echo Set oWS = WScript.CreateObject("WScript.Shell")
    echo sLinkFile = oWS.SpecialFolders("Programs") ^& "\%SHORTCUT_NAME%"
    echo Set oLink = oWS.CreateShortcut(sLinkFile)
    echo oLink.TargetPath = "%MSYS2_ROOT%\\usr\\bin\\bash.exe"
    echo oLink.Arguments = "-lc \"cd '%INSTALLDIR%' && /mingw64/bin/python dummtrace.py\""
    echo oLink.IconLocation = "%ICON_PATH%"
    echo oLink.Save
) > "%VBS_CREATE%"
cscript //nologo "%VBS_CREATE%"
del "%VBS_CREATE%"

echo [SUCCESS] TypeTrace installed. You can launch it from the Start Menu.
pause
