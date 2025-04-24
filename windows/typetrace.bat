@echo off
set MSYS2_ROOT=C:\tools\msys64
set INSTALLDIR=C:\Program Files\typetrace

"%MSYS2_ROOT%\usr\bin\bash.exe" -lc "cd '/C/Program Files/typetrace' && /mingw64/bin/python ./_install/bin/typetrace -b"

"%MSYS2_ROOT%\usr\bin\bash.exe" -lc "cd '/C/Program Files/typetrace' && /mingw64/bin/python ./_install/bin/typetrace"