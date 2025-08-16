# Inno Setupのインストール方法

## インストーラービルドの準備状況

### ✅ 必要ファイル（準備完了）
- `dist\CoinglassScraper.exe` - メイン実行ファイル
- `icon.ico` - アイコンファイル
- `README.md` - ドキュメント
- `TRAY_README.md` - トレイ機能の説明
- `installer.iss` - Inno Setupスクリプト

### ❌ Inno Setup（未インストール）

## Inno Setupのインストール手順

### 1. ダウンロード
[Inno Setup公式サイト](https://jrsoftware.org/isdl.php)から最新版をダウンロード

推奨: **innosetup-6.x.x.exe** (通常版、約5MB)

### 2. インストール
1. ダウンロードしたexeファイルを実行
2. インストールウィザードに従ってインストール
3. デフォルトの設定で問題ありません
4. 日本語言語パックも自動的にインストールされます

### 3. インストール確認
インストール後、以下のパスにISCC.exeが存在することを確認：
- 32ビット: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
- 64ビット: `C:\Program Files\Inno Setup 6\ISCC.exe`

## インストーラーのビルド

Inno Setupインストール後：
```
build_installer.bat
```

## 手動でビルドする場合

1. Inno Setup Compilerを起動
2. File → Open → `installer.iss`を選択
3. Build → Compileを実行
4. `installer_output`フォルダに生成されます

## 予想される出力

```
installer_output\CoinglassScraperSetup_1.0.0.exe
```

サイズ: 約25-30MB（圧縮されたEXE）