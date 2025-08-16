# Coinglass Scraper EXE化ガイド

## 事前準備

1. **仮想環境のセットアップ**
   ```
   setup_scraper.bat
   ```

2. **（オプション）アイコンファイルの準備**
   - `icon.ico`ファイルを作成（詳細は`ICON_README.md`参照）
   - アイコンを使用する場合は`coinglass_scraper.spec`の56行目のコメントを解除

## EXEのビルド

### 配布用EXE（単一ファイル）
```
build_exe.bat
```
- 単一のEXEファイルを生成
- ファイルサイズ: 約50-100MB
- 起動時間: 数秒（初回は一時ファイル展開のため）

### 開発用EXE（フォルダ形式）
```
build_exe_dev.bat
```
- 複数ファイルのフォルダ構成
- 起動時間: 高速
- デバッグ向け

## ビルド後のファイル

### 配布用
```
CoinglassScraper.exe  # プロジェクトルートにコピーされる
dist/CoinglassScraper.exe  # オリジナル
```

### 開発用
```
dist/CoinglassScraperDev/
├── CoinglassScraperDev.exe
├── 各種DLLファイル
└── その他依存ファイル
```

## 実行方法

1. **EXEファイルをダブルクリック**
   - コンソールウィンドウは表示されません
   - GUIが直接起動します

2. **コマンドラインから実行**
   ```
   CoinglassScraper.exe
   ```

## トラブルシューティング

### ビルドエラーが発生する場合
1. アンチウイルスソフトを一時的に無効化
2. 管理者権限でコマンドプロンプトを実行
3. `pip install --upgrade pyinstaller`でPyInstallerを更新

### EXEが起動しない場合
1. Windows Defenderでブロックされていないか確認
2. 必要なランタイムがインストールされているか確認
3. `build_exe_dev.bat`でフォルダ形式でビルドして詳細を確認

### ChromeDriverエラー
- ユーザーのPCにGoogle Chromeがインストールされている必要があります

## 注意事項

- 初回起動時はWindows Defenderの警告が表示される場合があります
- 署名なしのEXEファイルのため、一部の環境では実行がブロックされる可能性があります
- データベースファイル（`btc_usdt_order_book.db`）はEXEと同じフォルダに作成されます