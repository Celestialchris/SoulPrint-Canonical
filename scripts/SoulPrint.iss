[Setup]
AppName=SoulPrint
AppVersion=0.3.1
AppVerName=SoulPrint 0.3.1
AppPublisher=Celestialchris
AppPublisherURL=https://soulprint.dev
AppSupportURL=https://github.com/Celestialchris/SoulPrint-Canonical
DefaultDirName={autopf}\SoulPrint
DefaultGroupName=SoulPrint
OutputDir=..\dist
OutputBaseFilename=SoulPrint-Setup
SetupIconFile=soulprint.ico
UninstallDisplayIcon={app}\SoulPrint.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
LicenseFile=..\LICENSE

[Files]
Source: "..\dist\SoulPrint\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SoulPrint"; Filename: "{app}\SoulPrint.exe"
Name: "{group}\Uninstall SoulPrint"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SoulPrint"; Filename: "{app}\SoulPrint.exe"; \
  Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\SoulPrint.exe"; Description: "Launch SoulPrint"; \
  Flags: nowait postinstall skipifsilent
