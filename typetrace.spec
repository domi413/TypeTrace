# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['_install/bin/typetrace'],
    pathex=['.venv/lib/python3.13/site-packages/'],
    binaries=[],
    datas=[],
    hiddenimports=['appdirs', 'dbus', 'sqlite3', 'evdev'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='typetrace',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
