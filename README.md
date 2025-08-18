# Depth - BTC/USDT オーダーブック分析ツール

## 概要
DepthはBTC/USDTのオーダーブック（板情報）をリアルタイムで収集・分析するツールです。
CoinglassのAPIからデータを取得し、ローカルとSupabaseクラウドの両方に保存します。

## 主な機能
- リアルタイムオーダーブック収集
- 複数時間足での集計（5分、15分、30分、1時間、2時間、4時間、日足）
- Supabaseクラウド同期
- Webダッシュボード表示

## 最近の更新履歴

### v1.30 (2025-08-18) - Realtime同期ロジックの改善
本バージョンでは、Supabase Realtime同期のロジックを改善し、手動でのデータ修正を可能にしました。

#### 主な変更点
- **Realtime同期ロジックの改善**: SupabaseからのRealtimeデータを絶対値として受け入れるように変更
- **手動データ修正対応**: Supabase上で異常値を手動修正した場合、その値がそのまま反映されるように
- **スクレイピングロジックの維持**: 通常のスクレイピング時は従来通り最大値を採用する仕組みを維持

### v1.21 (2025-08-19) - UTC タイムゾーン統一とテーブル構造改善
本バージョンでは、すべてのタイムスタンプをUTCに統一し、データベース構造を改善しました。

#### 主な変更点

##### 1. タイムゾーンの統一
- **問題**: 5分足データのみJSTで保存されており、他の時間足（UTC）との不整合が発生
- **解決**: すべてのタイムスタンプをUTC（+00:00）に統一
- **影響**: グラフ表示の「can't compare offset-naive and offset-aware datetimes」エラーを解消

##### 2. テーブル命名の統一
- **変更前**: 5分足のみ `order_book_shared` という異なる命名
- **変更後**: `order_book_5min` として他の時間足と命名を統一
- **メリット**: コードの一貫性向上とメンテナンス性の改善

##### 3. 実装内容
- **Supabase**:
  - 新テーブル `order_book_5min` を作成
  - 既存データをJSTからUTCに変換して移行（-9時間）
  - `order_book_shared` は旧版互換性のため維持
  
- **デスクトップアプリ (Python)**:
  - `coinglass_scraper.py`: UTC対応のタイムスタンプ生成
  - `cloud_sync.py`: 5分足の送信先を `order_book_5min` に変更
  - `migrate_to_utc_timestamps.py`: 既存データの移行スクリプト
  
- **Webアプリ (Next.js)**:
  - `lib/supabase.ts`: 5分足参照を `order_book_5min` に更新

##### 4. データ移行
- ローカルDB: 38,018件のレコードをUTCタイムゾーン付きに変換
- Supabase: 6,684件の5分足データを新テーブルに移行

#### 技術仕様
- タイムスタンプ形式: ISO 8601 with UTC timezone (例: `2025-08-18T21:35:00+00:00`)
- Python: `datetime.now(timezone.utc)` を使用
- JavaScript: Date constructorがUTC付き/なし両方を自動解釈

#### 互換性
- 旧版アプリとの互換性: `order_book_shared` テーブルを維持
- 新版アプリ: `order_book_5min` テーブルを使用
- データ同期: 両テーブル間での同期は行わない（新版への移行を推奨）

## システム構成

### デスクトップアプリ
- `coinglass_scraper.py`: メインスクレイピング処理
- `cloud_sync.py`: Supabaseとの同期処理
- `realtime_sync.py`: リアルタイム同期処理

### Webアプリ  
- Next.js 13以降
- Supabase クライアント
- リアルタイムグラフ表示

### データベース
- ローカル: SQLite (`AppData/Roaming/CoinglassScraper/btc_usdt_order_book.db`)
- クラウド: Supabase PostgreSQL

## 開発者向け情報

### ブランチ戦略
- `main`: 本番環境
- `refactor/unified-chart`: 開発ブランチ（UTC統一作業完了）
- `draft`: ドラフト版

### 環境変数
- Webアプリ: `.env.local`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### テスト環境
- デスクトップアプリ: `http://192.168.0.39:3000`
- Webアプリ: `http://localhost:3000`

## ライセンス
Private Project

## 作成者
USER

---
最終更新: 2025-08-19