; OpenSeismo Lite Installer Script
; This script creates a professional Windows installer for OpenSeismo Lite
; Requires NSIS: https://nsis.sourceforge.io/

; General
Name "OpenSeismo Lite"
OutFile "OpenSeismoLite-Setup.exe"
InstallDir "$PROGRAMFILES\OpenSeismo Lite"
InstallDirRegKey HKCU "Software\OpenSeismo Lite" ""

; Request admin privileges
RequestExecutionLevel admin

; Pages
Page directory
Page instfiles

; Installation section
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "dist\OpenSeismo Lite.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\OpenSeismo Lite"
    CreateShortcut "$SMPROGRAMS\OpenSeismo Lite\OpenSeismo Lite.lnk" "$INSTDIR\OpenSeismo Lite.exe"
    CreateShortcut "$SMPROGRAMS\OpenSeismo Lite\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\OpenSeismo Lite.lnk" "$INSTDIR\OpenSeismo Lite.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\OpenSeismo Lite" "" "$INSTDIR"
    
    ; Add to Add/Remove Programs
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenSeismo Lite" "DisplayName" "OpenSeismo Lite"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenSeismo Lite" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenSeismo Lite" "InstallLocation" "$INSTDIR"
    
SectionEnd

; Uninstall section
Section "Uninstall"
    ; Delete files
    Delete "$INSTDIR\OpenSeismo Lite.exe"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Delete shortcuts
    Delete "$SMPROGRAMS\OpenSeismo Lite\OpenSeismo Lite.lnk"
    Delete "$SMPROGRAMS\OpenSeismo Lite\Uninstall.lnk"
    RMDir "$SMPROGRAMS\OpenSeismo Lite"
    Delete "$DESKTOP\OpenSeismo Lite.lnk"
    
    ; Delete directory
    RMDir "$INSTDIR"
    
    ; Remove registry
    DeleteRegKey HKCU "Software\OpenSeismo Lite"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenSeismo Lite"
    
SectionEnd
