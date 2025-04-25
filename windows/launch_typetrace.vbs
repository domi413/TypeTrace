Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /k ""C:\tools\msys64\usr\bin\bash.exe"" --login -c 'cd ""/c/Program Files/typetrace"" && /mingw64/bin/python ./_install/bin/typetrace -b'", 1, True

WshShell.Run "cmd /k ""C:\tools\msys64\usr\bin\bash.exe"" --login -c 'cd ""/c/Program Files/typetrace"" && /mingw64/bin/python ./_install/bin/typetrace'", 1, True