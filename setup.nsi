!include "MUI2.nsh"

Name "TypeTrace"
OutFile "TypeTrace-Setup.exe"
InstallDir "$PROGRAMFILES\TypeTrace"

Section
  SetOutPath $INSTDIR
  File "dist\TypeTrace.exe"
  File "C:\gtk\bin\*.dll"
  CreateShortcut "$SMPROGRAMS\TypeTrace.lnk" "$INSTDIR\TypeTrace.exe"
SectionEnd