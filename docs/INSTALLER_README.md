# インストーラー作成ガイド

## 概要
Coinglass ScraperのWindowsインストーラーを作成するためのガイドです。
Inno Setupを使用して、プロフェッショナルなインストーラーを生成します。

## 必要なもの

### 1. Inno Setup
- [公式サイト](https://jrsoftware.org/isdl.php)からダウンロード
- バージョン6以降を推奨
- 日本語言語パックも同梱

### 2. ビルド済みファイル
- `dist\CoinglassScraper.exe` - メインの実行ファイル
- `icon.ico` - アイコンファイル
- `README.md`、`TRAY_README.md` - ドキュメント（オプション）

## インストーラーの作成手順

### 1. EXEファイルのビルド
```
build_exe.bat
```
※まだビルドしていない場合

### 2. インストーラーのビルド
```
build_installer.bat
```

### 3. 生成されるファイル
```
installer_output\CoinglassScraperSetup_1.0.0.exe
```

## インストーラーの特徴

### インストール先
- `%APPDATA%\Coinglass Scraper`
- 例: `C:\Users\ユーザー名\AppData\Roaming\Coinglass Scraper`
- 管理者権限不要

### ショートカット作成（チェックボックスで選択）
- □ デスクトップにショートカットを作成
- □ スタートメニューにショートカットを作成
- プログラム一覧には常に登録

### アンインストール
- コントロールパネル → プログラムと機能
- または設定 → アプリ → Coinglass Scraper

## カスタマイズ方法

### バージョン番号の変更
`installer.iss`の4行目：
```
#define MyAppVersion "1.0.0"
```

### デフォルトのチェックボックス状態
`installer.iss`の[Tasks]セクション：
- `Flags: checkedonce` - 初回のみチェック
- `Flags: unchecked` - デフォルトでチェックなし

### 追加ファイルの同梱
`installer.iss`の[Files]セクション：
```
Source: "追加ファイル.txt"; DestDir: "{app}"; Flags: ignoreversion
```

## トラブルシューティング

### Inno Setupが見つからない
1. [公式サイト](https://jrsoftware.org/isdl.php)からダウンロード
2. デフォルトの場所にインストール
3. `build_installer.bat`を再実行

### ビルドエラー
- `dist\CoinglassScraper.exe`が存在するか確認
- `icon.ico`が存在するか確認
- パスに日本語が含まれていないか確認

### インストーラーが起動しない
- Windows Defenderでブロックされていないか確認
- 署名なしのため警告が出る場合は「詳細情報」→「実行」

## 配布時の注意

### ファイルサイズ
- 約25-30MB（EXEファイルの圧縮版）

### 動作環境
- Windows Vista以降
- .NET Framework不要（Python含む）
- Google Chrome必須（スクレイピング用）

### セキュリティ
- 署名なしのため、SmartScreenで警告が出る可能性
- ウイルス対策ソフトによっては誤検知の可能性
- 公式の署名を取得する場合は別途手続きが必要