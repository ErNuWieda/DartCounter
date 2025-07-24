; -- Inno Setup Script for DartCounter --
; Dieses Skript definiert, wie der Windows-Installer erstellt wird.
; Weitere Informationen: https://jrsoftware.org/ishelp/

#define MyAppName "DartCounter"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "airnooweeda"
#define MyAppURL "https://github.com/ErNuWieda/DartCounter"
#define MyAppExeName "DartCounter.exe"

[Setup]
; HINWEIS: Die AppId identifiziert diese Anwendung eindeutig.
; Um eine neue GUID zu generieren, klicken Sie in der Inno Setup IDE auf Tools | Generate GUID.
AppId={{A4B8C1D2-E3F4-5A6B-7C8D-9E0F1A2B3C4D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Die Lizenzdatei wird im Installer angezeigt. Der Pfad muss relativ zum Skript sein.
LicenseFile=..\LICENSE
OutputBaseFilename=DartCounter_v{#MyAppVersion}_setup
; Das Verzeichnis, in dem der fertige Installer gespeichert wird.
OutputDir=Output
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; HINWEIS: Passen Sie den folgenden Pfad an!
; Er muss auf den Ordner zeigen, in den Sie die Build-Dateien entpackt haben.
Source: "C:\Pfad\zum\entpackten\build_output\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; "{app}" ist das Installationsverzeichnis (z.B. C:\Program Files\DartCounter)

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent