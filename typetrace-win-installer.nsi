!include "MUI2.nsh"

Name "TypeTrace"
OutFile "typetrace-installer.exe"
InstallDir "$PROGRAMFILES64\TypeTrace"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  ; Hauptanwendung kopieren
  SetOutPath "$INSTDIR\bin"
  File "/oname=typetrace.exe" "_install\bin\typetrace"

  ; Startmenü-Verknüpfung
  CreateDirectory "$SMPROGRAMS\TypeTrace"
  CreateShortcut "$SMPROGRAMS\TypeTrace\TypeTrace.lnk" "$INSTDIR\bin\typetrace.exe"

  ; PATH Variable aktualisieren
  EnVar::AddValue "PATH" "$INSTDIR\bin"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\TypeTrace\*.*"
  RMDir "$SMPROGRAMS\TypeTrace"
  RMDir /r "$INSTDIR"
  EnVar::DeleteValue "PATH" "$INSTDIR\bin"
SectionEnd