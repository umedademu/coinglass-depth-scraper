# 時間足専用ローカルデータベース実装計画

## 📌 このドキュメントについて

これはBTC-USDT板情報スクレーパーにおいて、各時間足専用のローカルデータベースを実装するための計画書です。
現在の混在したデータ構造を整理し、Realtime同期を正常に機能させることを目的としています。

**重要**: 実装を始める前に、必ずこのドキュメント全体を読んでください。

## 🎯 実装方針

1. **データの完全分離**: 各時間足のデータを独立したテーブルで管理
2. **既存機能の維持**: 1分足データ取得とグラフ表示機能はそのまま活用
3. **段階的移行**: 動作確認しながら着実に機能を追加
4. **最大値採用の徹底**: ローカルとSupabaseのデータを常に比較し、大きい値を採用
5. **Realtime同期の正常化**: 各時間足のUPDATEイベントを適切なテーブルに反映

## 📍 実装の前提条件

### 現在の問題点
- 1分足DBに5分足以上のデータが混入している
- グラフ表示のタイミングとSupabaseのデータタイミングがズレている
- Realtime同期で受信したデータが正しくグラフに反映されない
- データの粒度が混在し、グラフがギザギザになる

### 現在の構成
- **1分足**: ローカルでスクレイピング、`order_book_history`テーブルに保存
- **3分足**: 1分足から動的生成（DBなし）
- **5分足以上**: Supabaseに保存、Realtimeで同期（現在は1分足DBに誤って保存）

### 目標構成
- **1分足**: 現状維持（ローカルスクレイピング、`order_book_history`テーブル）
- **3分足**: 現状維持（1分足から動的生成）
- **5分足以上**: 各時間足専用のローカルテーブルを作成し、Supabaseと同期

## 📋 実装段階

### 第1段階：データベーステーブル作成 🎯難易度: 8/100

#### 目標
各時間足専用のテーブルをSQLiteデータベースに作成する。

#### タスク
- `btc_usdt_order_book.db`に7つの新規テーブルを追加
- テーブル名: `order_book_5min`, `order_book_15min`, `order_book_30min`, `order_book_1hour`, `order_book_2hour`, `order_book_4hour`, `order_book_daily`
- 既存の`order_book_history`と同じスキーマを使用
- インデックスを作成（timestamp）

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. アプリケーションを起動
2. ログに以下が表示される：
   - "時間足専用テーブルを作成しました: order_book_5min"
   - "時間足専用テーブルを作成しました: order_book_15min"
   - （全7テーブル分）
3. SQLiteブラウザで確認（任意）：
   - btc_usdt_order_book.dbを開く
   - 8つのテーブルが存在（order_book_history + 7つの新規）

問題なければOKです！」
```

---

### 第2段階：データ保存先の振り分け 🎯難易度: 12/100

#### 目標
スクレイピングしたデータを適切な時間足テーブルに保存する。

#### タスク
- `save_to_database`メソッドの拡張
- タイムスタンプから該当する時間足を判定
- 5分ごとのデータは`order_book_5min`に保存
- 15分ごとのデータは`order_book_15min`に保存（以下同様）
- 1分足データは従来通り`order_book_history`に保存

#### 実装内容
```python
# 保存先テーブルの判定ロジック
if dt.minute % 5 == 0:
    # order_book_5minに保存
if dt.minute in [0, 15, 30, 45]:
    # order_book_15minに保存
if dt.minute in [0, 30]:
    # order_book_30minに保存
# ... 以下同様
```

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. アプリケーションを5分以上実行
2. 5分経過後、ログに以下が表示される：
   - "[5分足DB] データを保存: 13:05:00"
3. 15分経過後、ログに以下が表示される：
   - "[15分足DB] データを保存: 13:15:00"
4. order_book_5minテーブルにデータが保存されている

データが正しく振り分けられていればOKです！」
```

---

### 第3段階：Supabaseデータとの比較・更新 🎯難易度: 18/100

#### 目標
Supabaseから取得したデータとローカルDBを比較し、最大値を採用する。

#### タスク
- `fetch_initial_timeframe_data`メソッドの修正
- 各時間足データを対応するローカルテーブルに保存
- 既存データがある場合は最大値比較
- INSERT OR REPLACEではなく、明示的な比較ロジックを実装

#### 実装内容
```python
# 既存データをチェック
existing = cursor.execute(
    "SELECT ask_total, bid_total FROM order_book_5min WHERE timestamp = ?",
    (timestamp,)
).fetchone()

if existing:
    # 最大値を選択
    ask = max(supabase_ask, existing[0])
    bid = max(supabase_bid, existing[1])
    # UPDATE実行
else:
    # INSERT実行
```

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. アプリケーションを起動
2. 起動時ログに以下が表示される：
   - "[初期データ取得] 5分足: 1000件取得"
   - "[ローカルDB] 5分足: 新規300件、更新50件"
3. ローカルDBの値がSupabaseの値以上になっている
4. テストデータ投入後、大きい値が採用されている

最大値比較が機能していればOKです！」
```

---

### 第4段階：Realtime同期の修正 🎯難易度: 15/100

#### 目標
Realtimeで受信したUPDATEイベントを適切な時間足テーブルに保存する。

#### タスク
- `save_realtime_data_to_local_db`メソッドの修正
- table_nameから保存先を判定
- 各時間足専用テーブルへの保存処理
- 最大値比較ロジックの適用

#### 実装内容
```python
# テーブル名マッピング
# 注: 5分足のSupabaseテーブル名'order_book_shared'は
#     将来的に'order_book_5min'に統一される予定
table_mapping = {
    'order_book_shared': 'order_book_5min',  # 将来的に'order_book_5min'に変更予定
    'order_book_15min': 'order_book_15min',
    'order_book_30min': 'order_book_30min',
    # ... 以下同様
}

local_table = table_mapping.get(supabase_table_name)
# local_tableに保存
```

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. アプリケーションを起動
2. Supabaseでテストデータを更新（50,000など大きい値）
3. ログに以下が表示される：
   - "[Realtime] 5分足の更新を検出"
   - "[5分足DB] Realtimeデータを保存: Ask=50,000"
4. order_book_5minテーブルに新しい値が保存されている
5. 1分足DBには混入していない

Realtime同期が正しく動作すればOKです！」
```

---

### 第5段階：グラフ表示の切り替え ✅完了 🎯難易度: 20/100

#### 目標
時間足選択に応じて、適切なテーブルからデータを読み込んでグラフを表示する。

#### タスク
- `update_graph`メソッドの修正
- 5分足以上は専用テーブルから読み込み
- 1分足・3分足は従来通り（`order_book_history`から動的生成）
- データ読み込みクエリの最適化
- **重要: 変数名の統一（filtered_times → times）**

#### ⚠️ 実装上の重要な注意事項
```
警告: 変数名の統一が必要です！
- 従来のコードでは filtered_times, filtered_asks, filtered_bids を使用
- 新実装では times, asks, bids に統一する
- グラフ描画処理の全箇所で変数名を確認・修正する必要があります
  - データ取得部分: times, asks, bids
  - グラフ描画部分: times, asks, bids
  - X軸ラベル設定: len(times), times[i] ← ここが見落としやすい！
```

#### 実装内容
```python
# 新しいメソッド1: 動的生成処理を分離
def generate_timeframe_data_from_memory(self, interval):
    """1分足・3分足用の動的生成（従来処理を別メソッド化）"""
    filtered_times = []  # この内部では filtered_* を使用
    # ... 処理 ...
    return filtered_times, filtered_asks, filtered_bids  # 戻り値

# 新しいメソッド2: DBからの直接読み込み
def load_timeframe_data_from_db(self, table_name, limit=300):
    """5分足以上の専用テーブルから読み込み"""
    # ... 処理 ...
    return times, asks, bids  # 直接 times として返す

# 修正されたupdate_graphメソッド
def update_graph(self):
    if timeframe in timeframe_tables:  # 5分足以上
        times, asks, bids = self.load_timeframe_data_from_db(table_name)
    else:  # 1分足・3分足
        times, asks, bids = self.generate_timeframe_data_from_memory(interval)
    
    # ⚠️ 以降、全てtimes/asks/bidsで統一（filtered_*は使わない）
    # グラフ描画処理...
    self.ax_ask.plot(times, asks, ...)  # OK
    
    # X軸ラベル設定（ここが重要！）
    data_count = len(times)  # len(filtered_times)ではない！
    tick_positions.append(times[i])  # filtered_times[i]ではない！
```

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. アプリケーションを起動
2. 5分足を選択：
   - order_book_5minからデータ読み込み
   - 50,000などの大きい値が正しく表示
   - グラフがギザギザにならない
3. 1時間足を選択：
   - order_book_1hourからデータ読み込み
   - 適切な間隔でデータ表示
4. 1分足を選択：
   - 従来通りの表示（変更なし）

各時間足が正しく表示されればOKです！」
```

---

### 第6段階：データ移行と最適化 🎯難易度: 25/100

#### 目標
既存の混在データをクリーンアップし、パフォーマンスを最適化する。

#### タスク
- 既存の`order_book_history`から5分足以上のデータを抽出
- 各時間足テーブルに移行
- 1分足DBから不要なデータを削除
- インデックスの最適化
- VACUUM実行

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. データ移行スクリプトを実行
2. ログに以下が表示される：
   - "データ移行開始"
   - "5分足: 1,000件を移行"
   - "1分足DB: 5,000件の不要データを削除"
   - "データベースを最適化しました"
3. グラフ表示が高速化している
4. 1分足グラフがギザギザでなくなっている

データ移行が完了していればOKです！」
```

---

## ⚠️ 実装上の重要な注意事項

### 1. データベース設計
- 既存の`btc_usdt_order_book.db`に新規テーブルを追加
- スキーマは`order_book_history`と同一
- PRIMARY KEYは`timestamp`
- トランザクション使用で整合性を保証

### 2. タイミングの統一
- **重要**: Supabaseと同じタイミング（開始時刻）でデータ保存
- 13:05の5分足 = 13:05:00のデータ
- グラフ表示も開始時刻を採用（終値ではなく）

### 3. 最大値採用の原則
- 常にローカルとSupabaseを比較
- 大きい値を採用
- UPDATEの場合も同様の処理

### 4. パフォーマンス考慮
- 各テーブルのデータは最大10,000件に制限
- 古いデータは定期的に削除
- インデックスを適切に設定

### 5. 互換性の維持
- 1分足と3分足の処理は変更しない
- 既存のグラフ表示ロジックを最大限活用
- エラー時は従来の動作にフォールバック

## 🔧 実装詳細

### テーブル作成SQL
```sql
CREATE TABLE IF NOT EXISTS order_book_5min (
    timestamp TEXT PRIMARY KEY,
    ask_total REAL NOT NULL,
    bid_total REAL NOT NULL,
    price REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_5min_timestamp 
ON order_book_5min(timestamp);

-- 他の時間足も同様に作成
```

### データ保存ロジック
```python
def save_to_timeframe_db(self, table_name, timestamp, ask, bid, price):
    """時間足専用DBへの保存"""
    cursor = self.conn.cursor()
    
    # 既存データチェック
    cursor.execute(f"""
        SELECT ask_total, bid_total FROM {table_name}
        WHERE timestamp = ?
    """, (timestamp,))
    
    existing = cursor.fetchone()
    if existing:
        # 最大値で更新
        if ask > existing[0] or bid > existing[1]:
            cursor.execute(f"""
                UPDATE {table_name}
                SET ask_total = ?, bid_total = ?, price = ?
                WHERE timestamp = ?
            """, (
                max(ask, existing[0]),
                max(bid, existing[1]),
                price,
                timestamp
            ))
    else:
        # 新規挿入
        cursor.execute(f"""
            INSERT INTO {table_name}
            (timestamp, ask_total, bid_total, price)
            VALUES (?, ?, ?, ?)
        """, (timestamp, ask, bid, price))
    
    self.conn.commit()
```

## 📊 データフロー

```
スクレイピング（1分ごと）
    ↓
1分足DB（order_book_history）
    ↓
5分ごとの判定
    ↓
5分足DB（order_book_5min）
    ↓
Supabaseと比較・最大値採用
    ↓
グラフ表示（専用DBから読み込み）
```

## 📚 関連ドキュメント

- [デスクトップアプリ仕様書](./desktop-app-spec.md)
- [Realtime同期仕様書](./realtime-error-fix-requirements.md)
- [早い者勝ち問題の解決](./previous-candle-monitoring-requirements.md)

---

**このドキュメントは実装の進捗に応じて更新してください。**