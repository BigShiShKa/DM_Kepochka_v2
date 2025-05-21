[Setup]
AppName=Кепочка  by _BaDRiVeR_
AppVersion=1.1
DefaultDirName={pf}\Kepochka
DefaultGroupName=Кепочка
OutputDir=.
OutputBaseFilename=KepochkaInstaller
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico
WizardStyle=modern
LanguageDetectionMethod=locale
DisableDirPage=no

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи"
Name: "autorun"; Description: "Добавить в автозагрузку"; GroupDescription: "Дополнительные задачи"

[Files]
Source: "DesktopMateReplacer.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "oi.wav"; DestDir: "{app}"; Flags: ignoreversion
Source: "ok.wav"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "custom_png.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "error.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "Desktop Mate\*"; DestDir: "{app}\Desktop Mate"; Flags: recursesubdirs ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "windowsdesktop-runtime-6.0.36-win-x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: not IsDotNet6Detected

[Run]
Filename: "{tmp}\windowsdesktop-runtime-6.0.36-win-x64.exe"; \
  Parameters: "/install"; \
  Check: not IsDotNet6Detected; \
  StatusMsg: "Устанавливается .NET Desktop Runtime 6.0. Подождите..."

Filename: "{app}\launch.bat"; Description: "Запустить Кепочку"; \
    Flags: shellexec postinstall skipifsilent nowait

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: files; Name: "{userstartup}\Кепочка.lnk"
Type: files; Name: "{userdesktop}\Кепочка.lnk"

[Code]
function IsDotNet6Detected: Boolean;
var
  InstallVersion: string;
begin
  Result := RegQueryStringValue(HKLM64, 'SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost', 'Version', InstallVersion)
            and (Pos('6.', InstallVersion) = 1);
end;

function InitializeSetup(): Boolean;
begin
  if not IsDotNet6Detected then begin
    MsgBox('Не найден .NET Desktop Runtime 6.0. Установщик попробует установить его автоматически.', mbInformation, MB_OK);
  end;
  Result := True;
end;

var
  SteamPathPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  // Создаём страницу после выбора директории установки и группы
  SteamPathPage := CreateInputDirPage(
    wpSelectProgramGroup,  // <= Ключевой момент!
    'Укажите папку Steam',
    'Путь к Steam нужен для работы Кепочки',
    'Выберите папку, где установлен Steam. Обычно это "C:\Program Files (x86)\Steam" или "SteamLibrary".',
    False, ''
  );
  SteamPathPage.Add('');
end;


procedure CreateShortcut(FileName, Description, WorkingDir, Icon: string; TaskCheck: Boolean);
var
  Shell: Variant;
  Shortcut: Variant;
begin
  if not TaskCheck then Exit;
  Shell := CreateOleObject('WScript.Shell');
  Shortcut := Shell.CreateShortcut(FileName);
  Shortcut.TargetPath := ExpandConstant('{app}\launch.bat');
  Shortcut.WorkingDirectory := WorkingDir;
  Shortcut.IconLocation := Icon;
  Shortcut.WindowStyle := 7;
  Shortcut.Save;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SteamDirFile, AppDir: string;
begin
  if CurStep = ssPostInstall then begin
    AppDir := ExpandConstant('{app}');
    SteamDirFile := AppDir + '\steam_dir.txt';
    SaveStringToFile(SteamDirFile, SteamPathPage.Values[0], False);

    CreateShortcut(ExpandConstant('{userstartup}\Кепочка.lnk'), '', AppDir, AppDir + '\icon.ico', IsTaskSelected('autorun'));
    CreateShortcut(ExpandConstant('{userdesktop}\Кепочка.lnk'), '', AppDir, AppDir + '\icon.ico', IsTaskSelected('desktopicon'));
    CreateShortcut(AppDir + '\Кепочка.lnk', '', AppDir, AppDir + '\icon.ico', True);
  end;
end;
