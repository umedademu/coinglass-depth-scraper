[Setup]
AppName=Coinglass BTC-USDT Order Book Monitor
AppVersion=1.19
AppPublisher=CoinglassScraper
DefaultDirName={userappdata}\CoinglassScraper
DefaultGroupName=CoinglassScraper
UninstallDisplayIcon={app}\CoinglassScraper.exe
OutputDir=installer
OutputBaseFilename=CoinglassScraper_Setup_v1.19
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Files]
Source: "dist\CoinglassScraper.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Coinglass BTC-USDT Monitor"; Filename: "{app}\CoinglassScraper.exe"
Name: "{group}\アンインストール"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Coinglass Monitor"; Filename: "{app}\CoinglassScraper.exe"

[Run]
Filename: "{app}\CoinglassScraper.exe"; Description: "アプリケーションを起動"; Flags: nowait postinstall skipifsilent

[Code]
var
  PrevDataPage: TInputOptionWizardPage;

procedure InitializeWizard();
begin
  PrevDataPage := CreateInputOptionPage(wpSelectDir,
    'データ移行オプション',
    '以前のバージョンのデータをどのように処理しますか？',
    '以前のバージョンのデータベースファイルが存在する場合の処理を選択してください。',
    True, False);
  
  PrevDataPage.Add('データを保持する（推奨）');
  PrevDataPage.Add('データを削除して新規インストール');
  
  PrevDataPage.Values[0] := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  OldDataFile: String;
begin
  if CurStep = ssPostInstall then
  begin
    // データベースファイルのパスを設定（AppData使用）
    OldDataFile := ExpandConstant('{userappdata}\CoinglassScraper\btc_usdt_order_book.db');
    
    // ユーザーがデータ削除を選択した場合
    if PrevDataPage.Values[1] then
    begin
      if FileExists(OldDataFile) then
      begin
        DeleteFile(OldDataFile);
      end;
    end;
  end;
end;