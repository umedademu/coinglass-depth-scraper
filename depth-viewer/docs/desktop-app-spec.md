# デスクトップアプリ（Pythonスクレーパー）改修仕様書

## 📌 概要

現在5分間隔でBTC-USDT板情報を収集しているPythonスクレーパーを改修し、各時間足（15分、1時間、4時間、日足）のデータも同時に集約・アップロードする機能を追加します。

## 🎯 改修の目的

### 現状の問題
- Webアプリでデータ取得時に毎回グルーピング計算が必要
- 大量データの場合、パフォーマンスが低下
- SupabaseのVIEWでは計算負荷が高い

### 解決策
- デスクトップアプリ側で事前に各時間足データを集約
- 個別テーブルにアップロードすることで高速アクセスを実現

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

### 🟡 **第2段階：全時間足の実装**（難易度：★★☆ 中）

#### 実装内容
- 15分足、4時間足、日足テーブルの追加作成
- 各タイミングでのデータアップロード実装
- エラーハンドリングの追加

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
            
            # 1時間足（毎時00分）
            if now.minute == 0:
                self.save_1hour_data(current_data)
                self.logger.info(f"1時間足データ保存: {now}")
            
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
    
    def save_1hour_data(self, data):
        """1時間足データの保存"""
        now = datetime.datetime.now()
        rounded_time = now.replace(minute=0, second=0, microsecond=0)
        self._upsert_data('order_book_1hour', rounded_time, data)
    
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
        """共通のUPSERT処理"""
        try:
            self.supabase.table(table_name).upsert({
                'timestamp': timestamp.isoformat(),
                'ask_total': data['ask_total'],
                'bid_total': data['bid_total'],
                'price': data['price'],
                'group_id': self.group_id
            }).execute()
        except Exception as e:
            self.logger.error(f"{table_name}へのデータ保存失敗: {e}")
            raise
```

#### アップロードタイミング表

| 時間 | 分 | 5分足 | 15分足 | 1時間足 | 4時間足 | 日足 |
|-----|-----|-------|--------|---------|---------|------|
| 00 | 00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 00 | 15 | ✓ | ✓ | - | - | - |
| 00 | 30 | ✓ | ✓ | - | - | - |
| 00 | 45 | ✓ | ✓ | - | - | - |
| 01 | 00 | ✓ | ✓ | ✓ | - | - |
| 04 | 00 | ✓ | ✓ | ✓ | ✓ | - |
| ... | ... | ✓ | ... | ... | ... | ... |

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
        self._migrate_1hour(df)
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
    
    def _migrate_1hour(self, df):
        """1時間足データの生成と保存"""
        df_1hour = df.groupby(pd.Grouper(
            key='timestamp',
            freq='1h',
            label='left'
        )).last().dropna()
        
        self._bulk_insert('order_book_1hour', df_1hour)
        self.logger.info(f"1時間足: {len(df_1hour)}件移行")
    
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
    tables = ['order_book_15min', 'order_book_1hour', 
              'order_book_4hour', 'order_book_daily']
    
    for table in tables:
        count = supabase.table(table).select('*', count='exact').execute()
        print(f"{table}: {count.count}件")
```

---

### 🟦 **第4段階：最適化と監視**（難易度：★★☆ 中）

#### 実装内容
- リトライ機能の実装
- ログ記録の強化
- データ整合性チェック
- パフォーマンス監視

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
        tables = ['order_book_shared', 'order_book_15min',
                 'order_book_1hour', 'order_book_4hour', 
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

## 📊 実装順序と期待効果

| 段階 | 難易度 | 作業時間 | 期待効果 |
|------|--------|---------|----------|
| 第1段階 | ★☆☆ | 2-3時間 | 1時間足の高速化（12倍） |
| 第2段階 | ★★☆ | 4-5時間 | 全時間足の高速化 |
| 第3段階 | ★★★ | 6-8時間 | 過去データの活用 |
| 第4段階 | ★★☆ | 3-4時間 | 安定性向上 |

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

## 📚 関連ドキュメント

- [Web版実装計画](./implementation-plan.md)
- [Supabase公式ドキュメント](https://supabase.com/docs)

---

**このドキュメントは実装の進捗に応じて更新してください。**