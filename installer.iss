; Coinglass Scraper インストーラースクリプト
; Inno Setup 6用

#define MyAppName "Coinglass Scraper"
#define MyAppVersion "1.30"
#define MyAppPublisher "Coinglass Scraper Development Team"
#define MyAppURL "https://github.com/umedademu/coinglass-depth-scraper"
#define MyAppExeName "CoinglassScraper.exe"
#define MyAppIconName "icon.ico"

[Setup]
; アプリケーション情報
AppId={{E8F5D3A2-9B4C-4E7F-8A1D-2C6E9F3B8D5A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; インストール先（AppDataフォルダ）
DefaultDirName={userappdata}\{#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes

; アンインストール情報
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; 出力設定
OutputDir=installer_output
OutputBaseFilename=CoinglassScraperSetup_{#MyAppVersion}
SetupIconFile={#MyAppIconName}

; 圧縮設定
Compression=lzma2
SolidCompression=yes

; Windows 7以降が必要
MinVersion=6.1

; 管理者権限不要
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; その他の設定
WizardStyle=modern
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage

[Languages]
; 日本語を優先
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; ショートカット作成のオプション
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startmenuicon"; Description: "スタートメニューにショートカットを作成(&S)"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; メインの実行ファイル
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; アイコンファイル
Source: "{#MyAppIconName}"; DestDir: "{app}"; Flags: ignoreversion
; 設定ファイル（実際の認証情報を含む）
; Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
; ドキュメント（オプション）
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "TRAY_README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; プログラムフォルダのショートカット（常に作成）
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
; デスクトップショートカット（タスクで選択時のみ）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: desktopicon
; スタートメニューショートカット（タスクで選択時のみ）
Name: "{userstartmenu}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: startmenuicon

[Run]
; インストール完了後の実行オプション
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; アンインストール時にデータフォルダも削除するかの確認
Type: filesandordirs; Name: "{app}"

[Code]
// カスタムメッセージ
procedure InitializeWizard();
begin
  // 必要に応じてカスタム処理を追加
end;

// アンインストール時の確認
function InitializeUninstall(): Boolean;
begin
  Result := MsgBox('Coinglass Scraperをアンインストールしますか？' + #13#10 +
                   'データベースファイルとログファイルも削除されます。',
                   mbConfirmation, MB_YESNO) = IDYES;
end;

[Messages]
; 日本語カスタムメッセージ
japanese.BeveledLabel=Coinglass Scraper セットアップ

[CustomMessages]
; 追加のカスタムメッセージ
japanese.LaunchProgram=%1 を起動(&L)
english.LaunchProgram=&Launch %1