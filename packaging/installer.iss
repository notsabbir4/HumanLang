; Inno Setup script: builds the Windows installer for HumanLang.
; Built by .github/workflows/installer.yml:  iscc /DAppVersion=0.3.1 /DExePath=... packaging\installer.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef ExePath
  #define ExePath "..\dist\hl-windows.exe"
#endif

[Setup]
AppId={{6F0B8C52-3D2A-4E5B-9C41-7A1E5D0B8F36}
AppName=HumanLang
AppVersion={#AppVersion}
AppPublisher=HumanLang
AppPublisherURL=https://github.com/notsabbir4/HumanLang
DefaultDirName={autopf}\HumanLang
DefaultGroupName=HumanLang
DisableProgramGroupPage=yes
; Installs just for you: no administrator password needed.
PrivilegesRequired=lowest
ChangesAssociations=yes
ChangesEnvironment=yes
OutputDir=..\installer-out
OutputBaseFilename=HumanLang-Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\hum.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "addpath"; Description: "Let me type ""hl"" in a terminal (adds HumanLang to PATH)"; GroupDescription: "Options:"
Name: "assoc"; Description: "Give .hum files the HumanLang icon, and run them when I double-click"; GroupDescription: "Options:"

[Files]
Source: "{#ExePath}"; DestName: "hl.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestName: "hum.ico"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
; .hum files -> HumanLang icon, double-click runs them and keeps the window open
Root: HKCU; Subkey: "Software\Classes\.hum"; ValueType: string; ValueData: "HumanLang.File"; Flags: uninsdeletekey; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\HumanLang.File"; ValueType: string; ValueData: "HumanLang program"; Flags: uninsdeletekey; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\HumanLang.File\DefaultIcon"; ValueType: string; ValueData: "{app}\hum.ico"; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\HumanLang.File\shell\open\command"; ValueType: string; ValueData: "cmd.exe /k """"{app}\hl.exe"" run ""%1"""""; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\HumanLang.File\shell\edit"; ValueType: string; ValueData: "Edit"; Tasks: assoc
Root: HKCU; Subkey: "Software\Classes\HumanLang.File\shell\edit\command"; ValueType: string; ValueData: "notepad.exe ""%1"""; Tasks: assoc
; PATH
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addpath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
function NeedsAddPath(Dir: string): Boolean;
var
  Paths: string;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', Paths) then
    Paths := '';
  Result := Pos(';' + Lowercase(Dir) + ';', ';' + Lowercase(Paths) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Paths, Dir: string;
  P: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegQueryStringValue(HKCU, 'Environment', 'Path', Paths) then
    begin
      Dir := ExpandConstant('{app}');
      P := Pos(';' + Lowercase(Dir), Lowercase(Paths));
      if P > 0 then
      begin
        Delete(Paths, P, Length(Dir) + 1);
        RegWriteExpandStringValue(HKCU, 'Environment', 'Path', Paths);
      end;
    end;
  end;
end;
