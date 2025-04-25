@echo off
set MSYS2_PATH=C:\tools\msys64
set TYPETRACE_PATH="C:\Program Files\typetrace"

%MSYS2_PATH%\usr\bin\bash.exe -lc "cd /c/Program\ Files/typetrace && /mingw64/bin/python ./_install/bin/typetrace -b"
pause