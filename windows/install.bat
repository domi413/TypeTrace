@echo off
setlocal enabledelayedexpansion

:: -----------------------------
:: CONFIGURATION
:: -----------------------------
set ZIPFILE=typetrace.zip
set INSTALLDIR=C:\Program Files\typetrace
set MSYS2_ROOT=C:\tools\msys64
set SHORTCUT_NAME=TypeTrace.lnk
set RELEASE_NAME=TypeTrace-R4
set RELEASE_DIR=%INSTALLDIR%\%RELEASE_NAME%
set ICON_PATH=%INSTALLDIR%\%RELEASE_NAME%\windows\edu.ost.typetrace.ico
set RELEASE_LINK=https://github.com/domi413/TypeTrace/archive/refs/tags/R4.zip

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
:: Check if we have admin rights, if not request elevation
fltmc >nul 2>&1 || (
    echo Requesting administrator privileges...
    :: Re-launch as admin
    PowerShell -Command "Start-Process -FilePath '%~dpnx0' -Verb RunAs"
    exit /b
)

:: -----------------------------
:: Check for Chocolatey, offer to install if missing
:: -----------------------------
where choco >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Chocolatey is not installed.
    set /p install="Do you want to install Chocolatey now? (y/n):"
    if /i "%install%"=="y" (
        echo Installing Chocolatey...
        PowerShell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    ) else (
        echo [ERROR] Chocolatey is required to continue.
        pause
        exit /b
    )
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
:: DOWNLOAD ZIPFILE IF NOT EXISTS
:: -----------------------------
if not exist "%ZIPFILE%" (
    echo [INFO] Downloading %ZIPFILE% to %TEMP%...
    powershell -Command "Invoke-WebRequest -Uri '%RELEASE_LINK%' -OutFile '%TEMP%\%ZIPFILE%' -UseBasicParsing"
    set ZIPPED_FILE=%TEMP%\%ZIPFILE%
    if %errorlevel% NEQ 0 (
        call :cleanup 1
    )
) else (
    echo [INFO] %ZIPFILE% already exists in %cd%\%ZIPFILE%
    set ZIPPED_FILE=%cd%\%ZIPFILE%
)

:: -----------------------------
:: UNZIP APPLICATION
:: -----------------------------
echo [INFO] Extracting %ZIPFILE% to %INSTALLDIR%...
pushd "%~dp0"
set CLEANUP_NEEDED=1
powershell -Command "Expand-Archive -LiteralPath '%ZIPPED_FILE%' -DestinationPath '%INSTALLDIR%' -Force"
if %errorlevel% NEQ 0 (
    call :cleanup 1
)

:: -----------------------------
:: CREATE START MENU SHORTCUT
:: -----------------------------
set VBS_CREATE=%TEMP%\create_shortcut.vbs
(
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo sLinkFile = oWS.SpecialFolders^("Programs"^) ^& "\%SHORTCUT_NAME%"
    echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
    echo oLink.TargetPath = "%RELEASE_DIR%\windows\launch_typetrace.vbs%"
    echo oLink.WorkingDirectory = "%RELEASE_DIR%"
    echo oLink.IconLocation = "%ICON_PATH%"
    echo oLink.Save
) > "%VBS_CREATE%"

cscript //nologo "%VBS_CREATE%"
del "%VBS_CREATE%"
if %errorlevel% NEQ 0 (
    call :cleanup 1
)

echo [INFO] Dependencies will be installed shortly
echo [SUCCESS] TypeTrace installed. You can launch it from the Start Menu.

:: -----------------------------
:: INSTALL REQUIRED PACKAGES IN MSYS
:: -----------------------------
"%MSYS2_ROOT%\msys2_shell.cmd" -defterm -here -no-start -mingw64 -c "pacman -Syuu --noconfirm && pacman -Sy --noconfirm --needed mingw-w64-x86_64-toolchain mingw-w64-x86_64-gtk4 mingw-w64-x86_64-libadwaita mingw-w64-x86_64-python mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-gobject mingw-w64-x86_64-meson mingw-w64-x86_64-glib2 mingw-w64-x86_64-make mingw-w64-x86_64-desktop-file-utils mingw-w64-x86_64-python-cairo"
if %errorlevel% NEQ 0 (
    echo [WARNING] Some packages failed to install. You may need to install them manually.
)
pause
