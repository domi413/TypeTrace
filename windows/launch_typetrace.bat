@echo off
set MSYS2_PATH=C:\tools\msys64
set TYPETRACE_PATH="C:\Program Files\typetrace"

"%MSYS2_ROOT%\msys2_shell.cmd" -lc "cd /c/Program\ Files/typetrace/TypeTrace-R4 && /mingw64/bin/python ./_install/bin/typetrace -b"
pause