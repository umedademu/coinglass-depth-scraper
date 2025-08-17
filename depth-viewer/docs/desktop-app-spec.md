# デスクトップアプリ（Pythonスクレーパー）改修仕様書

## 📌 概要

現在5分間隔でBTC-USDT板情報を収集しているPythonスクレーパーを改修し、各時間足（15分、1時間、4時間、日足）のデータも同時に集約・アップロードする機能を追加します。

**重要**: Supabase MCPツールを使用する際は、必ずプロジェクトID `rijqtostuemonbfcntck` を使用してください。

## 🎯 改修の目的

### 現状の問題
- Webアプリでデータ取得時に毎回グルーピング計算が必要
- 大量データの場合、パフォーマンスが低下
- SupabaseのVIEWでは計算負荷が高い
- **Supabase APIの制限**: 1リクエストあたり最大1000行まで（全プラン共通）
- **専用テーブルは書き込みのみで読み込みに使われていない**
- **リアルタイム欠損補完により1分と5分の異なる粒度データが混在**
- **複数ユーザー同時更新時の競合状態（レースコンディション）が発生**

### 解決策
- デスクトップアプリ側で事前に各時間足データを集約
- 個別テーブルにアップロードすることで高速アクセスを実現
- **起動時に各時間足テーブルから1000件ずつ取得**
- **時間足生成時に双方向の最大値同期を実装**
- **1分足はローカルのみ、5分足以上はSupabaseと同期**

---

## 📊 段階別実装計画

### 🟢 **第1段階：1時間足の実装**（難易度：★☆☆ 簡単）

#### 実装内容
- 1時間足テーブルの作成
- 毎時00分に1時間足データをアップロード
- 最小限の変更で動作確認

#### 必要な作業時間
- **約2-3時間**

#### Supabaseテーブル作成

```sql
-- 1時間足テーブルのみ作成
CREATE TABLE order_book_1hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);
```

#### Python実装（最小限の追加）

```python
# 既存のデータアップロード処理に以下を追加
def upload_data(self, current_data):
    """データアップロード処理（既存関数の修正）"""
    
    # 既存の5分足アップロード
    self.save_5min_data(current_data)
    
    # 新規追加：1時間足の処理
    now = datetime.datetime.now()
    if now.minute == 0:  # 毎時00分
        self.save_1hour_data(current_data)

def save_1hour_data(self, data):
    """1時間足データの保存（新規追加）"""
    now = datetime.datetime.now()
    rounded_time = now.replace(minute=0, second=0, microsecond=0)
    
    self.supabase.table('order_book_1hour').upsert({
        'timestamp': rounded_time.isoformat(),
        'ask_total': data['ask_total'],
        'bid_total': data['bid_total'],
        'price': data['price'],
        'group_id': 'default-group'
    }).execute()
```

#### テスト方法
1. テーブル作成を確認
2. 毎時00分にデータが入ることを確認
3. Web側で1時間足テーブルからデータ取得可能か確認

---

### 🟡 **第2段階：全時間足への書き込み実装**（難易度：★★☆ 中） ✅ 実装済み (2025/08/17)

#### 実装内容
- 15分足、30分足、2時間足、4時間足、日足テーブルの追加作成 ✅
- 各タイミングでのデータアップロード実装 ✅
- エラーハンドリングの追加 ✅
- **時間足生成時の最大値比較機能** ✅ 全時間足で実装済み

#### 必要な作業時間
- **約4-5時間**

#### 追加テーブル作成

```sql
-- 15分足テーブル
CREATE TABLE order_book_15min (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 30分足テーブル
CREATE TABLE order_book_30min (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 2時間足テーブル
CREATE TABLE order_book_2hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 4時間足テーブル
CREATE TABLE order_book_4hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 日足テーブル
CREATE TABLE order_book_daily (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);
```

#### Python実装（完全版）

```python
import datetime
import logging

class TimeframeAggregator:
    """時間足集約クラス"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.group_id = "default-group"
        self.logger = logging.getLogger(__name__)
    
    def process_all_timeframes(self, current_data):
        """全時間足の処理（メイン関数）"""
        now = datetime.datetime.now()
        
        try:
            # 5分足は常に保存（既存処理）
            self.save_5min_data(current_data)
            
            # 15分足（00, 15, 30, 45分）
            if now.minute in [0, 15, 30, 45]:
                self.save_15min_data(current_data)
                self.logger.info(f"15分足データ保存: {now}")
            
            # 30分足（00, 30分）
            if now.minute in [0, 30]:
                self.save_30min_data(current_data)
                self.logger.info(f"30分足データ保存: {now}")
            
            # 1時間足（毎時00分）
            if now.minute == 0:
                self.save_1hour_data(current_data)
                self.logger.info(f"1時間足データ保存: {now}")
            
            # 2時間足（0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22時の00分）
            if now.hour % 2 == 0 and now.minute == 0:
                self.save_2hour_data(current_data)
                self.logger.info(f"2時間足データ保存: {now}")
            
            # 4時間足（0, 4, 8, 12, 16, 20時の00分）
            if now.hour in [0, 4, 8, 12, 16, 20] and now.minute == 0:
                self.save_4hour_data(current_data)
                self.logger.info(f"4時間足データ保存: {now}")
            
            # 日足（毎日00:00）
            if now.hour == 0 and now.minute == 0:
                self.save_daily_data(current_data)
                self.logger.info(f"日足データ保存: {now}")
                
        except Exception as e:
            self.logger.error(f"時間足データ保存エラー: {e}")
    
    def save_15min_data(self, data):
        """15分足データの保存"""
        now = datetime.datetime.now()
        rounded_time = now.replace(
            minute=(now.minute // 15) * 15,
            second=0,
            microsecond=0
        )
        self._upsert_data('order_book_15min', rounded_time, data)
    
    def save_30min_data(self, data):
        """30分足データの保存"""
        now = datetime.datetime.now()
        rounded_time = now.replace(
            minute=(now.minute // 30) * 30,
            second=0,
            microsecond=0
        )
        self._upsert_data('order_book_30min', rounded_time, data)
    
    def save_1hour_data(self, data):
        """1時間足データの保存"""
        now = datetime.datetime.now()
        rounded_time = now.replace(minute=0, second=0, microsecond=0)
        self._upsert_data('order_book_1hour', rounded_time, data)
    
    def save_2hour_data(self, data):
        """2時間足データの保存"""
        now = datetime.datetime.now()
        rounded_hour = (now.hour // 2) * 2
        rounded_time = now.replace(
            hour=rounded_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        self._upsert_data('order_book_2hour', rounded_time, data)
    
    def save_4hour_data(self, data):
        """4時間足データの保存"""
        now = datetime.datetime.now()
        rounded_hour = (now.hour // 4) * 4
        rounded_time = now.replace(
            hour=rounded_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        self._upsert_data('order_book_4hour', rounded_time, data)
    
    def save_daily_data(self, data):
        """日足データの保存"""
        now = datetime.datetime.now()
        rounded_time = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        self._upsert_data('order_book_daily', rounded_time, data)
    
    def _upsert_data(self, table_name, timestamp, data):
        """共通のUPSERT処理（双方向最大値同期付き）"""
        try:
            # 既存データを確認
            existing = self.supabase.table(table_name)\
                .select('*')\
                .eq('timestamp', timestamp.isoformat())\
                .eq('group_id', self.group_id)\
                .execute()
            
            if existing.data:
                # 最大値を選択してアップデート
                existing_data = existing.data[0]
                if data['ask_total'] > existing_data['ask_total'] or data['bid_total'] > existing_data['bid_total']:
                    update_data = {
                        'ask_total': max(data['ask_total'], existing_data['ask_total']),
                        'bid_total': max(data['bid_total'], existing_data['bid_total']),
                        'price': data['price']
                    }
                    self.supabase.table(table_name).update(update_data)\
                        .eq('timestamp', timestamp.isoformat())\
                        .eq('group_id', self.group_id)\
                        .execute()
                    self.logger.info(f"{table_name}: 更新 (Ask: {existing_data['ask_total']:.1f}→{update_data['ask_total']:.1f})")
                else:
                    self.logger.info(f"{table_name}: スキップ (既に最新)")
            else:
                # 新規データとして挿入
                self.supabase.table(table_name).insert({
                    'timestamp': timestamp.isoformat(),
                    'ask_total': data['ask_total'],
                    'bid_total': data['bid_total'],
                    'price': data['price'],
                    'group_id': self.group_id
                }).execute()
                self.logger.info(f"{table_name}: 新規保存")
        except Exception as e:
            self.logger.error(f"{table_name}へのデータ保存失敗: {e}")
            raise
```

#### アップロードタイミング表

| 時間 | 分 | 5分足 | 15分足 | 30分足 | 1時間足 | 2時間足 | 4時間足 | 日足 |
|-----|-----|-------|--------|--------|---------|---------|---------|------|
| 00 | 00 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 00 | 15 | ✓ | ✓ | - | - | - | - | - |
| 00 | 30 | ✓ | ✓ | ✓ | - | - | - | - |
| 00 | 45 | ✓ | ✓ | - | - | - | - | - |
| 01 | 00 | ✓ | ✓ | ✓ | ✓ | - | - | - |
| 02 | 00 | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| 04 | 00 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| ... | ... | ✓ | ... | ... | ... | ... | ... | ... |

---

### 🔴 **第3段階：既存データの移行**（難易度：★★★ 難）

#### 実装内容
- 過去の5分足データから各時間足データを生成
- バッチ処理による効率的な移行
- データ整合性の検証

#### 必要な作業時間
- **約6-8時間**（データ量による）

#### 移行スクリプト

```python
import pandas as pd
from datetime import datetime, timedelta

class DataMigrator:
    """既存データ移行クラス"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)
    
    def migrate_all_timeframes(self, days_back=90):
        """全時間足のデータ移行"""
        self.logger.info(f"過去{days_back}日分のデータ移行開始")
        
        # 5分足データを取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # バッチサイズを設定（メモリ効率のため）
        batch_size = 1000
        offset = 0
        all_data = []
        
        while True:
            # データをバッチで取得
            response = self.supabase.table('order_book_shared')\
                .select('*')\
                .gte('timestamp', start_date.isoformat())\
                .lte('timestamp', end_date.isoformat())\
                .order('timestamp')\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not response.data:
                break
                
            all_data.extend(response.data)
            offset += batch_size
            
            self.logger.info(f"取得済み: {len(all_data)}件")
        
        # DataFrameに変換
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 各時間足に集約
        self._migrate_15min(df)
        self._migrate_30min(df)
        self._migrate_1hour(df)
        self._migrate_2hour(df)
        self._migrate_4hour(df)
        self._migrate_daily(df)
        
        self.logger.info("移行完了")
    
    def _migrate_15min(self, df):
        """15分足データの生成と保存"""
        # 15分単位でグループ化（最後の値を採用）
        df_15min = df.groupby(pd.Grouper(
            key='timestamp',
            freq='15min',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_15min', df_15min)
        self.logger.info(f"15分足: {len(df_15min)}件移行")
    
    def _migrate_30min(self, df):
        """30分足データの生成と保存"""
        df_30min = df.groupby(pd.Grouper(
            key='timestamp',
            freq='30min',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_30min', df_30min)
        self.logger.info(f"30分足: {len(df_30min)}件移行")
    
    def _migrate_1hour(self, df):
        """1時間足データの生成と保存"""
        df_1hour = df.groupby(pd.Grouper(
            key='timestamp',
            freq='1h',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_1hour', df_1hour)
        self.logger.info(f"1時間足: {len(df_1hour)}件移行")
    
    def _migrate_2hour(self, df):
        """2時間足データの生成と保存"""
        df_2hour = df.groupby(pd.Grouper(
            key='timestamp',
            freq='2h',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_2hour', df_2hour)
        self.logger.info(f"2時間足: {len(df_2hour)}件移行")
    
    def _migrate_4hour(self, df):
        """4時間足データの生成と保存"""
        df_4hour = df.groupby(pd.Grouper(
            key='timestamp',
            freq='4h',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_4hour', df_4hour)
        self.logger.info(f"4時間足: {len(df_4hour)}件移行")
    
    def _migrate_daily(self, df):
        """日足データの生成と保存"""
        df_daily = df.groupby(pd.Grouper(
            key='timestamp',
            freq='1D',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_daily', df_daily)
        self.logger.info(f"日足: {len(df_daily)}件移行")
    
    def _bulk_insert(self, table_name, df):
        """バルクインサート処理"""
        records = []
        for _, row in df.iterrows():
            records.append({
                'timestamp': row.name.isoformat(),  # インデックスがtimestamp
                'ask_total': float(row['ask_total']),
                'bid_total': float(row['bid_total']),
                'price': float(row['price']),
                'group_id': 'default-group'
            })
        
        # 100件ずつバッチ処理
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                self.supabase.table(table_name).upsert(batch).execute()
            except Exception as e:
                self.logger.error(f"{table_name}へのバッチ挿入失敗: {e}")
```

#### 移行実行手順

1. **データ量の確認**
```python
# 移行前にデータ量を確認
count = supabase.table('order_book_shared').select('*', count='exact').execute()
print(f"移行対象: {count.count}件")
```

2. **段階的な移行**
```python
# まず7日分でテスト
migrator.migrate_all_timeframes(days_back=7)

# 問題なければ90日分
migrator.migrate_all_timeframes(days_back=90)
```

3. **検証**
```python
def verify_migration():
    """移行データの検証"""
    tables = ['order_book_15min', 'order_book_30min', 'order_book_1hour',
              'order_book_2hour', 'order_book_4hour', 'order_book_daily']
    
    for table in tables:
        count = supabase.table(table).select('*', count='exact').execute()
        print(f"{table}: {count.count}件")
```

---

### 🟦 **第4段階：最適化と監視**（難易度：★★☆ 中） ✅ 実装済み (2025/08/17)

#### 実装内容
- リトライ機能の実装 ✅
- ログ記録の強化 ✅
- データ整合性チェック ✅
- パフォーマンス監視 ✅

#### 必要な作業時間
- **約3-4時間**

#### リトライ機能

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=5):
    """リトライデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class OptimizedAggregator(TimeframeAggregator):
    """最適化版アグリゲータ"""
    
    @retry_on_failure(max_retries=3, delay=5)
    def _upsert_data(self, table_name, timestamp, data):
        """リトライ機能付きUPSERT"""
        return super()._upsert_data(table_name, timestamp, data)
    
    def health_check(self):
        """ヘルスチェック機能"""
        tables = ['order_book_shared', 'order_book_15min', 'order_book_30min',
                 'order_book_1hour', 'order_book_2hour', 'order_book_4hour', 
                 'order_book_daily']
        
        results = {}
        for table in tables:
            try:
                # 最新データの確認
                latest = self.supabase.table(table)\
                    .select('timestamp')\
                    .order('timestamp', desc=True)\
                    .limit(1)\
                    .execute()
                
                if latest.data:
                    last_update = datetime.fromisoformat(
                        latest.data[0]['timestamp'].replace('Z', '+00:00')
                    )
                    age = datetime.now() - last_update
                    results[table] = {
                        'status': 'OK' if age.total_seconds() < 3600 else 'STALE',
                        'last_update': last_update,
                        'age_minutes': age.total_seconds() / 60
                    }
                else:
                    results[table] = {'status': 'EMPTY'}
            except Exception as e:
                results[table] = {'status': 'ERROR', 'error': str(e)}
        
        return results
```

---

### 🔵 **第5段階：専用テーブルからの読み込み実装**（難易度：★☆☆ 簡単）✅ 実装済み (2025/08/17)

#### 実装内容
- **起動時の初期データ取得**
  - 各時間足テーブルから1000件ずつ取得
  - ローカルDBへの格納
- **リアルタイム欠損補完の削除**
  - 現在の6分以上欠損補完機能を削除
  - 異なる粒度のデータ混在問題を解決
- **データ取得ロジックの改善**
  - 5分足以上は専用テーブルから取得
  - 1分足はローカルのみで管理

#### 必要な作業時間
- **約2-3時間**

#### 実装例

```python
def initialize_at_startup(self):
    """起動時の初期化処理"""
    # 各時間足テーブルからデータを取得
    initial_data = self.fetch_initial_data()
    
    # ローカルDBに保存
    for table_name, records in initial_data.items():
        self.save_to_local_db(table_name, records)
        self.logger.info(f"{table_name}: {len(records)}件をローカルDBに保存")
    
    # リアルタイム欠損補完を無効化
    self.disable_realtime_gap_fill = True
    
def fetch_initial_data(self):
    """各時間足テーブルからデータを取得（既に実装済み）"""
    # cloud_sync.pyの既存メソッドを使用
    return super().fetch_initial_data()

def save_to_local_db(self, table_name, records):
    """ローカルSQLiteデータベースに保存"""
    cursor = self.conn.cursor()
    
    for record in records:
        # 既存データをチェック
        cursor.execute("""
            SELECT ask_total, bid_total FROM order_book_history
            WHERE timestamp = ? AND timeframe = ?
        """, (record['timestamp'], self.get_timeframe_name(table_name)))
        
        existing = cursor.fetchone()
        
        if existing:
            # 最大値を選択して更新
            if record['ask_total'] > existing[0] or record['bid_total'] > existing[1]:
                cursor.execute("""
                    UPDATE order_book_history 
                    SET ask_total = ?, bid_total = ?, price = ?
                    WHERE timestamp = ? AND timeframe = ?
                """, (
                    max(record['ask_total'], existing[0]),
                    max(record['bid_total'], existing[1]),
                    record['price'],
                    record['timestamp'],
                    self.get_timeframe_name(table_name)
                ))
        else:
            # 新規挿入
            cursor.execute("""
                INSERT INTO order_book_history 
                (timestamp, ask_total, bid_total, price, timeframe)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record['timestamp'],
                record['ask_total'],
                record['bid_total'],
                record['price'],
                self.get_timeframe_name(table_name)
            ))
    
    self.conn.commit()
```

---

### 🟣 **第6段階：Realtime同期実装**（難易度：★★☆ 中） ✅ 実装済み (2025/08/17)

#### 実装内容
- **Supabase Realtimeによる同期** ✅
  - 各時間足の最新タイムスタンプを監視 ✅
  - 他ユーザーの更新をリアルタイムで受信 ✅
  - 競合状態（レースコンディション）の解決 ✅
- **効率的な同期戦略** ✅
  - 最新1件のみを監視（データ量を最小化） ✅
  - 新規データ検出時のみ差分取得 ✅
  - WebSocket接続の管理 ✅

#### 必要な作業時間
- **約3-4時間**

#### 実装例

```python
def setup_realtime_sync(self):
    """Realtime同期の設定"""
    tables = [
        'order_book_shared',    # 5分足
        'order_book_15min',     # 15分足  
        'order_book_30min',     # 30分足
        'order_book_1hour',     # 1時間足
        'order_book_2hour',     # 2時間足
        'order_book_4hour',     # 4時間足
        'order_book_daily'      # 日足
    ]
    
    for table_name in tables:
        # Realtime購読（最新1件のみ監視）
        channel = self.supabase.channel(f'sync-{table_name}')
        channel.on(
            'postgres_changes',
            {
                'event': 'INSERT',
                'schema': 'public', 
                'table': table_name,
                'filter': f"group_id=eq.{self.group_id}"
            },
            lambda payload: self.handle_realtime_update(table_name, payload)
        )
        channel.subscribe()
        self.logger.info(f"[Realtime] {table_name}の監視を開始")

def handle_realtime_update(self, table_name, payload):
    """他ユーザーからの更新を処理"""
    new_data = payload['new']
    
    # 最新タイムスタンプのデータのみ処理
    latest_local = self.get_latest_local_timestamp(table_name)
    
    if new_data['timestamp'] > latest_local:
        # より新しいデータなら差分を取得
        gap_data = self.fetch_gap_data(table_name, latest_local, new_data['timestamp'])
        
        # ローカルDBに保存
        self.save_to_local_db(table_name, gap_data)
        
        self.logger.info(f"[Realtime] {table_name}: {len(gap_data)}件の新規データを同期")

def fetch_gap_data(self, table_name, start_timestamp, end_timestamp):
    """指定期間のギャップデータを取得"""
    result = self.supabase.table(table_name)\
        .select('*')\
        .eq('group_id', self.group_id)\
        .gt('timestamp', start_timestamp)\
        .lte('timestamp', end_timestamp)\
        .order('timestamp')\
        .execute()
    
    return result.data if result.data else []
```

---

## 📊 実装順序と期待効果

| 段階 | 難易度 | 作業時間 | 期待効果 | 状態 |
|------|--------|---------|----------|------|
| 第1段階 | ★☆☆ | 2-3時間 | 1時間足の高速化（12倍） | ✅ 完了 |
| 第2段階 | ★★☆ | 4-5時間 | 全時間足への書き込み | ✅ 完了 |
| 第3段階 | ★★★ | 6-8時間 | 過去データの活用 | ✅ 完了 |
| 第4段階 | ★★☆ | 3-4時間 | 安定性向上 | ✅ 完了 |
| 第5段階 | ★☆☆ | 2-3時間 | 専用テーブルからの読み込み | ✅ 完了 |
| 第6段階 | ★★☆ | 3-4時間 | Realtime同期 | ✅ 完了 |

## 🚀 推奨実装アプローチ

### ステップ1：最小限の実装（第1段階）
- まず1時間足のみ実装
- 動作確認後、次の段階へ

### ステップ2：全機能実装（第2段階）
- 残りの時間足を追加
- エラーハンドリングを実装

### ステップ3：データ移行（第3段階）
- 週末など負荷の低い時間に実施
- 段階的に移行（7日→30日→90日）

### ステップ4：本番運用（第4段階）
- 監視機能の追加
- パフォーマンスの最適化

## ⚠️ 注意事項

- **第1段階から順番に実装**することを推奨
- 各段階で動作確認を必ず実施
- データ移行（第3段階）は慎重に実施
- タイムゾーンは日本時間（JST）で統一
- **Supabase API制限**: 1リクエストあたり最大1000行
- **各時間足での保持期間（1000行制限）**:
  - 5分足: 約3.5日分
  - 15分足: 約10.4日分
  - 30分足: 約20.8日分
  - 1時間足: 約41.7日分
  - 2時間足: 約83.3日分
  - 4時間足: 約166.7日分
  - 日足: 約2.7年分

## 💡 データ同期方針

### 現在の実装状況
- **1分足**: ローカルのみで管理（リアルタイムスクレイピング）✅
- **5分足以上の書き込み**: Supabaseへの書き込み実装済み ✅
- **全時間足の最大値比較**: 実装済み ✅
- **専用テーブルからの読み込み**: 実装済み ✅
- **リアルタイム欠損補完**: 削除済み（異なる粒度のデータ混在を防止）✅

### 推奨される実装（第5段階）
- **起動時処理**: fetch_initial_dataメソッドの呼び出し
- **ローカルDB保存**: 取得データをSQLiteに格納
- **欠損補完削除**: 異なる粒度のデータ混在を防ぐ

### 推奨される実装（第6段階）
- **Supabase Realtime**: 各時間足の最新タイムスタンプを監視
- **同期方式**: 他ユーザーの更新をリアルタイムで受信・同期
- **競合解決**: レースコンディションの解決

## 📚 関連ドキュメント

- [Web版実装計画](./implementation-plan.md)
- [Supabase公式ドキュメント](https://supabase.com/docs)

---

**このドキュメントは実装の進捗に応じて更新してください。**