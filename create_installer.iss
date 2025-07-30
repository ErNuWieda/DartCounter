; Inno Setup Script für Dartcounter Deluxe
; Dieses Skript wird vom CI/CD-Workflow verwendet, um einen Windows-Installer zu erstellen.

#define AppName "DartCounter"
; Die Versionsnummer wird vom CI-Workflow dynamisch ersetzt.
#define AppVersion "0.0.0"
#define AppPublisher "Martin Hehl (airnooweeda)"
#define AppURL "https://github.com/ErNuWieda/DartCounter"
; Der Name der finalen Setup-Datei.
#define OutputName "DartCounter-v" + AppVersion + "-setup"

[Setup]
AppId={{F2A7A6F0-7B3A-4E1C-9B0A-5A7A7E0B6C1D}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputBaseFilename={#OutputName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Der Quellpfad wird vom CI-Workflow dynamisch ersetzt.
; Er zeigt auf das Verzeichnis, das von build.py erstellt wurde.
Source: "SOURCE_PATH\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppName}.exe"
Name: "{group}\{cm:ProgramOnTheWeb,{#AppName}}"; Filename: "{#AppURL}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppName}.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppName}.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent