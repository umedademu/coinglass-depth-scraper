# タイムゾーン統一とテーブル構造改善 実装仕様書

## 📌 このドキュメントについて

DepthアプリケーションのタイムゾーンをUTCに統一し、5分足テーブルの命名を整合させるための実装仕様書です。
既存ユーザーへの影響をゼロに抑えながら、6つの段階で確実に修正を進めます。

**作成日**: 2025-08-18  
**対象**: デスクトップアプリ（Python）、Webアプリ（Next.js）、データベース（SQLite/Supabase）  
**開発ブランチ**: `refactor/unified-chart`  
**重要**: すべての変更は `refactor/unified-chart` ブランチで行い、完成後に `main` ブランチへマージします

## 🔍 現状の問題

### タイムゾーンの不整合
| データ種別 | ローカルDB | Supabase | 問題 |
|---------|----------|----------|------|
| 1分足 | UTC（正しい） | 存在しない | 問題なし |
| 5分足 | JST（タイムゾーンなし） | JST（order_book_shared） | 9時間のズレ |
| 15分〜日足 | UTC（正しい） | UTC（正しい） | 問題なし |

### テーブル命名の不整合
- 5分足のみ `order_book_shared` という異なる命名
- 他の時間足は `order_book_15min` のような統一された命名
- コードの一貫性が低下

## 🎯 修正方針

1. **すべてのタイムスタンプをUTCに統一**
2. **5分足テーブルを `order_book_5min` として新規作成**
3. **既存の `order_book_shared` は維持**（旧版ユーザー用）
4. **5分足のみ-9時間でUTCに変換**（他の時間足は既にUTC）

## 📋 実装の6段階

---

### 第1段階：バックアップ 🎯難易度: 10/100

#### 目標
修正前のローカルデータを確実にバックアップし、問題発生時のロールバックを可能にする。

#### タスク
- ローカルDB（btc_usdt_order_book.db）の完全バックアップ
- バックアップファイルにタイムスタンプを付けて保管
- 例：`btc_usdt_order_book_backup_20250818_1500.db`

#### 確認項目
```
✅ 確認指示：
1. ローカルDBのバックアップファイルが作成されている
2. バックアップファイルのサイズが元ファイルと同等である
3. バックアップファイルが別の場所に保管されている
```

---

### 第2段階：Supabaseの修正 🎯難易度: 30/100

#### 目標
新しい5分足テーブルを作成し、5分足データのタイムゾーンを修正する。

#### タスク
**新テーブルの作成と修正**
- テーブル名：`order_book_5min`
- 構造：`order_book_15min` と同一
- 初期データ：`order_book_shared` から全データをコピー
- **コピー後の処理**：全レコードのtimestampフィールドから **-9時間**（JSTからUTCへ変換）
- SQLサンプル：
  ```sql
  -- テーブル作成（構造をコピー）
  CREATE TABLE order_book_5min (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ask_total NUMERIC NOT NULL,
    bid_total NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    group_id VARCHAR DEFAULT 'default-group',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  
  -- インデックス作成
  CREATE INDEX idx_order_book_5min_timestamp ON order_book_5min(timestamp DESC);
  
  -- データコピーとタイムスタンプ修正を同時に実行
  INSERT INTO order_book_5min (timestamp, ask_total, bid_total, price, group_id, created_at)
  SELECT timestamp - INTERVAL '9 hours', ask_total, bid_total, price, group_id, created_at
  FROM order_book_shared;
  ```

**重要な注意点**
- `order_book_shared` は**一切変更しない**（旧版ユーザー用に維持）
- `order_book_15min`, `30min`, `1hour`, `2hour`, `4hour`, `daily` は**一切変更しない**（既にUTC）
- `order_book_1min` は**Supabaseに存在しない**

#### 確認項目
```
✅ 確認指示：
1. order_book_5min テーブルが作成されている
2. order_book_5min にデータがコピーされている
3. order_book_5min のタイムスタンプがUTCに変換されている（-9時間）
4. order_book_shared が変更されていない
5. 他の時間足テーブルが変更されていない
```

---

### 第3段階：ローカルDBの修正 🎯難易度: 25/100

#### 目標
ローカルデータベースの5分足データのタイムゾーンを修正する。

#### タスク
**場所**
- `AppData/Roaming/CoinglassScraper/btc_usdt_order_book.db`

**修正対象と処理**
- 対象テーブル：
  - order_book_5min のみ
- 処理：全レコードのtimestampフィールドから **-9時間**（JSTからUTCへ変換）
- SQLサンプル：
  ```sql
  UPDATE order_book_5min 
  SET timestamp = datetime(timestamp, '-9 hours');
  ```

**除外対象**
- `order_book_1min`：変更不要（既にUTC）
- `order_book_15min`, `30min`, `1hour`, `2hour`, `4hour`, `daily`：変更不要（既にUTC）

#### 確認項目
```
✅ 確認指示：
1. 5分足のタイムスタンプがUTCに変換されている（-9時間）
2. 他の時間足のタイムスタンプが変更されていない
3. SQLiteデータベースが正常に読み込める
```

---

### 第4段階：デスクトップアプリのコード修正 🎯難易度: 20/100

#### 目標
新規データがUTCで保存されるようにし、5分足の送信先を新テーブルに変更する。

#### タスク
**coinglass_scraper.py の修正**
- 時刻取得を `datetime.now()` から `datetime.now(timezone.utc)` に変更
- 対象箇所：データ保存時のタイムスタンプ生成（768行目付近、1114行目、1160行目など、すべての `datetime.now()` を修正）

**cloud_sync.py の修正**
- 5分足の送信先を `order_book_shared` から `order_book_5min` に変更
- 既存の逆同期処理（Supabase→ローカル）は維持

**realtime_sync.py の修正**（必要に応じて）
- 5分足の参照を `order_book_5min` に変更

#### 確認項目
```
✅ 確認指示：
1. コード修正後、構文エラーがないこと
2. アプリが正常に起動すること
3. 新規データがUTCタイムスタンプで保存されること
4. order_book_5min テーブルへの書き込みが成功すること
```

---

### 第5段階：Webアプリの修正 🎯難易度: 15/100

#### 目標
Webアプリが新しい5分足テーブルを参照するように修正する。

#### タスク
**lib/supabase.ts の修正**
- timeframes配列の5分足定義を変更：
  ```typescript
  // 変更前
  { key: '5min', label: '5分足', table: 'order_book_shared' }
  // 変更後
  { key: '5min', label: '5分足', table: 'order_book_5min' }
  ```

**フォールバック機能の追加**（オプション）
- `order_book_5min` が存在しない場合は `order_book_shared` を使用
- エラーハンドリングで実装

#### 確認項目
```
✅ 確認指示：
1. Webアプリが正常に起動する
2. 5分足データが正しく表示される
3. すべての時間足で時刻が一貫している
4. グラフの時系列が正しく表示される
```

---

### 第6段階：リリース前の最終処理 🎯難易度: 15/100

#### 目標
最新データの同期と動作確認を行い、本番環境への適用準備を完了する。

#### タスク
**データの最終同期**
- `order_book_shared` から `order_book_5min` へ最新データを再コピー
- 差分データのみをコピー（効率化のため）
- コピー後のタイムスタンプから **-9時間**（JSTからUTCへ変換）

**動作確認**
- デスクトップアプリ：新規データがUTCで保存される
- デスクトップアプリ：5分足が `order_book_5min` に書き込まれる
- Webアプリ：全時間足が正しい時刻で表示される

**ドキュメント更新**
- 変更内容をREADMEに記載
- 旧版ユーザー向けの案内を準備（必要に応じて）

#### 確認項目
```
✅ 確認指示：
1. order_book_5min に最新データが存在する
2. デスクトップアプリが正常に動作する
3. Webアプリが正常に動作する
4. 新旧両方のシステムが共存できている
```

## 📝 技術的な補足

### Python datetime の実装
```python
from datetime import datetime, timezone

# 変更前（JST）
now = datetime.now()  # 2025-08-18 19:00:00

# 変更後（UTC）
now = datetime.now(timezone.utc)  # 2025-08-18 10:00:00+00:00
```

### データベース別の注意点

**SQLite（ローカル）**
- datetime関数を使用：`datetime(timestamp, '+9 hours')`
- テキスト形式でタイムスタンプが保存されている

**PostgreSQL（Supabase）**
- INTERVAL句を使用：`timestamp + INTERVAL '9 hours'`
- timestamp型またはtimestamptz型

### 5分足データの特殊性
```
5分足のみのデータフロー：
ローカル生成（JST） → Supabase（JSTをUTCと誤認） → 9時間のズレ
※他の時間足と異なり、何らかの理由でJSTで保存されてしまっている

1分〜日足（5分以外）のデータフロー：
ローカル生成（UTC） → Supabase（UTC） → ズレなし
```

### 実装順序の重要性
この仕様書の段階順序は、以下の問題を防ぐよう設計されています：
1. **存在しないテーブルへの書き込みエラー**：Supabaseにテーブルを作成してからアプリを修正
2. **データの不整合**：既存データをUTCに修正してから新規データをUTCで保存
3. **テスト時の混乱**：各段階でデータの一貫性を保つ

### Git管理方針
```bash
# 開発ブランチでの作業
git checkout refactor/unified-chart

# 各段階完了時のコミット（例）
git add .
git commit -m "feat: 第2段階 - Supabaseテーブル作成とタイムゾーン修正"

# push先は必ず開発ブランチ
git push origin refactor/unified-chart

# mainブランチへのマージは全段階完了後
# ※ 個別にmainへpushしないこと（本番環境に影響）
```

## ⚠️ リスクと対策

### リスク
1. データ変換時の失敗によるデータ損失
2. 旧版アプリとの非互換性
3. タイムゾーン変換の計算ミス

### 対策
1. **必ず第1段階でバックアップを取る**
2. **order_book_shared を維持**することで旧版との互換性確保
3. **5分足のみ-9時間**という明確なルールで計算ミスを防ぐ

## 🔄 ロールバック手順

問題が発生した場合：

1. **即座に作業を停止**
2. **データの復元**
   - ローカルDB：第1段階のバックアップファイルで上書き
   - Supabase：管理画面から必要に応じて復元
3. **コード変更を元に戻す**
   - `git checkout refactor/unified-chart` で開発ブランチに移動
   - `git reset --hard HEAD~1` でコミット前の状態に戻す
   - **注意**: `main` ブランチには影響しないため、本番環境は安全
4. **order_book_5min テーブルを削除**（作成済みの場合）

---

**最終更新**: 2025-08-18  
**次回レビュー**: 実装完了後

この仕様書は実装の「何を」を定義しています。「どのように」実装するかは、各段階の実装者の判断に委ねられます。