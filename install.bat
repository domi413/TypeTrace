@echo off
setlocal enabledelayedexpansion

:: -----------------------------
:: CONFIGURATION
:: -----------------------------
set ZIPFILE=typetrace.zip
set INSTALLDIR=C:\Program Files\typetrace
set MSYS2_ROOT=C:\tools\msys64
set SHORTCUT_NAME=TypeTrace.lnk
set ICON_PATH=%INSTALLDIR%\icon.ico

:: -----------------------------
:: ERROR HANDLING SETUP
:: -----------------------------
set CLEANUP_NEEDED=0

goto :main

:cleanup
if %CLEANUP_NEEDED% EQU 1 (
    echo [ERROR] Installation failed. Cleaning up...
    if exist "%INSTALLDIR%" (
        rmdir /s /q "%INSTALLDIR%"
    )
    if exist "%USERPROFILE%\Desktop\%SHORTCUT_NAME%" (
        del "%USERPROFILE%\Desktop\%SHORTCUT_NAME%"
    )
)
exit /b %1

:main
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
    set CLEANUP_NEEDED=1
    choco install -y msys2
    if %errorlevel% NEQ 0 (
        call :cleanup 1
    )
) else (
    echo [INFO] MSYS2 already installed.
)

:: -----------------------------
:: UNZIP APPLICATION
:: -----------------------------
echo [INFO] Extracting %ZIPFILE% to %INSTALLDIR%...
pushd "%~dp0"
set CLEANUP_NEEDED=1
powershell -Command "Expand-Archive -LiteralPath '%ZIPFILE%' -DestinationPath '%INSTALLDIR%' -Force"
if %errorlevel% NEQ 0 (
    call :cleanup 1
)

:: -----------------------------
:: CREATE START MENU SHORTCUT
:: -----------------------------
set VBS_CREATE=%TEMP%\create_shortcut.vbs
(
    echo Set oWS = WScript.CreateObject("WScript.Shell")
    echo sLinkFile = oWS.SpecialFolders("Programs") ^& "\%SHORTCUT_NAME%"
    echo Set oLink = oWS.CreateShortcut(sLinkFile)
    echo oLink.TargetPath = "%MSYS2_ROOT%\\usr\\bin\\bash.exe"
    echo oLink.Arguments = "-lc \"cd '%INSTALLDIR%' && /mingw64/bin/python typetrace.py\""
    echo oLink.IconLocation = "%ICON_PATH%"
    echo oLink.Save
) > "%VBS_CREATE%"
cscript //nologo "%VBS_CREATE%"
del "%VBS_CREATE%"
if %errorlevel% NEQ 0 (
    call :cleanup 1
)

echo "[INFO] Dependencies will be installed shortly
echo [SUCCESS] TypeTrace installed. You can launch it from the Start Menu.

:: -----------------------------
:: INSTALL REQUIRED PACKAGES IN MSYS
:: -----------------------------
"%MSYS2_ROOT%\msys2_shell.cmd" -defterm -here -no-start -mingw64 -c "pacman -Syuu --noconfirm && pacman -Sy --noconfirm --needed mingw-w64-x86_64-toolchain mingw-w64-x86_64-gtk4 mingw-w64-x86_64-libadwaita mingw-w64-x86_64-python mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-gobject mingw-w64-x86_64-meson mingw-w64-x86_64-glib2 mingw-w64-x86_64-make mingw-w64-x86_64-desktop-file-utils"
if %errorlevel% NEQ 0 (
    echo [WARNING] Some packages failed to install. You may need to install them manually.
)
pause
