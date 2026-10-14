; Inno Setup 스크립트 - Desktop Pet 설치 프로그램
; 빌드: ISCC.exe /DAppVersion=1.0.0 installer\DesktopPet.iss
; 전제: dist\DesktopPet.exe, dist\quotes.txt 가 먼저 만들어져 있어야 한다.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#define AppName "Desktop Pet"
#define AppExe "DesktopPet.exe"
#define AppPublisher "cozyuj"
#define AppURL "https://github.com/cozyuj/windows-desktop-pet"

[Setup]
AppId={{7C1E0A52-3B7D-4D7E-9B61-0DE5C70B9E71}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
; 관리자 권한 없이 사용자 폴더에 설치 (UAC 창이 안 뜬다)
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\DesktopPet
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=..\dist
OutputBaseFilename=DesktopPet-Setup
SetupIconFile=..\assets\pet.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "ko"; MessagesFile: "Korean.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기 만들기"; GroupDescription: "추가 작업:"
Name: "autostart"; Description: "윈도우 시작할 때 자동으로 실행"; GroupDescription: "추가 작업:"

[Files]
Source: "..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\quotes.txt"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{#AppName} 제거"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "DesktopPet"; ValueData: """{app}\{#AppExe}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "지금 바로 실행"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /IM {#AppExe} /F"; Flags: runhidden; RunOnceId: "KillPet"

[Code]
// 설치 전에 실행 중인 펫을 종료한다 (exe 가 잠겨 있으면 덮어쓸 수 없음)
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{cmd}'), '/C taskkill /IM {#AppExe} /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
