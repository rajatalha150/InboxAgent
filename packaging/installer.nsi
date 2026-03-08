!define APPNAME "InboxAgent"
!define APPVERSION "0.1.0"
!define COMPNAME "Peak Services Inc."
!define DESCRIPTION "Privacy-first local AI email organization agent."
!define INSTALLSIZE 80000

OutFile "InboxAgent_Setup_0.1.0_x64.exe"
Name "${APPNAME}"
InstallDir "$PROGRAMFILES64\${APPNAME}"

Page directory
Page instfiles

Section "Desktop, Start Menu, and install files"
    SetOutPath $INSTDIR
    
    ; Copy the executable
    File "dist\inbox-agent.exe"
    
    ; Write the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\inbox-agent.exe"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\inbox-agent.exe"
    
    ; Registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPNAME}"
SectionEnd

Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\inbox-agent.exe"
    Delete "$INSTDIR\uninstall.exe"
    
    ; Remove config folder completely? Let's leave user data alone.
    
    ; Remove the installation directory
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"
    
    ; Clean registry bindings
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
