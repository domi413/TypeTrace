!include "MUI2.nsh"

Name "TypeTrace"
OutFile "TypeTrace-Installer.exe"
InstallDir "$PROGRAMFILES\TypeTrace"

Section
  SetOutPath $INSTDIR
  File "..\..\dist\TypeTrace.exe"
  File /r "C:\GTK\bin\*.dll"
  CreateShortcut "$SMPROGRAMS\TypeTrace.lnk" "$INSTDIR\TypeTrace.exe"
SectionEnd