# Realtimeエラー解決 - 要件定義書

## 📌 概要
デスクトップアプリのRealtime同期機能でエラーが発生しており、他ユーザーのデータ更新を受信できない問題を解決する。

## 🔴 現在の問題

### エラー内容
```
[Realtime] ✗ Realtime更新エラー: 'eventType'
```

### 問題の影響
1. Realtime同期が全く機能していない
2. 他ユーザーがアップロードした最大値を受信できない
3. ローカルDBが古いデータのままになる

### データの不整合例
- **ローカル値**: Ask 7,344 / Bid 11,907
- **Supabase値**: Ask 7,962 / Bid 14,001（最大値）
- **他ユーザー値**: 約13,900

## 🔍 原因分析

### 1. ペイロード構造の不一致
**現在のコード（誤り）**:
```python
# realtime_sync.py:154
event_type = payload.get('eventType', 'UNKNOWN')
```

**実際のSupabaseペイロード構造**:
- Postgresイベントでは`eventType`ではなく`type`または`event`
- 非同期版APIの違いによる可能性

### 2. データ保存フィルタの問題
**現在のコード（誤り）**:
```python
# coinglass_scraper.py:1214
if table_name != 'order_book_1min':  # このテーブルは存在しない！
    return  # 全データが保存されない
```

## ✅ 解決策

### ステップ1: ペイロード構造の調査
1. 実際のRealtime WebSocketペイロードをログ出力
2. 正確なキー名を特定（`type`、`event`、`eventType`等）
3. ペイロード全体の構造を把握

### ステップ2: イベントタイプの修正
```python
# 修正案
def _process_update(self, table_name: str, timeframe_name: str, payload: Dict[str, Any]):
    # デバッグログを追加
    self.logger.debug(f"[Realtime] ペイロード: {payload}")
    
    # 複数のキー名に対応
    event_type = (
        payload.get('type') or 
        payload.get('event') or 
        payload.get('eventType', 'UNKNOWN')
    )
```

### ステップ3: データ保存フィルタの修正
```python
# coinglass_scraper.py:1214の修正
def save_realtime_data_to_local_db(self, table_name: str, records: list):
    # 5分足データ（order_book_shared）を1分足DBに保存
    if table_name == 'order_book_shared':
        # 5分足データを1分足DBに保存（最大値比較あり）
        self._save_to_1min_db(records)
```

## 📊 テスト手順

### 1. ログレベルをDEBUGに設定
```python
logging.basicConfig(level=logging.DEBUG)
```

### 2. Realtimeイベントの確認
1. デスクトップアプリを起動
2. ペイロード構造をログで確認
3. 正しいキー名を特定

### 3. データ同期の検証
1. 他ユーザーがデータをアップロード
2. ローカルDBに最大値が反映されることを確認
3. Supabaseの値と一致することを確認

## 🎯 期待される結果

### 修正後の動作
1. Realtimeエラーが解消
2. 他ユーザーのデータ更新をリアルタイムで受信
3. ローカルDBに最大値が自動反映
4. Supabaseとローカルのデータが一致

### ログ出力例（正常時）
```
[Realtime] 5分足の更新を検出
[Realtime同期] 5分足: 1件の新規データを同期
[ローカルDB] Ask: 7,344 → 7,962 に更新（最大値）
[ローカルDB] Bid: 11,907 → 14,001 に更新（最大値）
```

## 📝 実装優先度
**優先度: 高** - Realtime同期はデータ共有の核心機能のため、最優先で修正が必要

## 🔗 関連ファイル
- `realtime_sync.py`: イベント処理ロジック
- `coinglass_scraper.py`: データ保存ロジック
- `cloud_sync.py`: Realtime同期の初期化

## ⚠️ 注意事項
- Supabase非同期版APIのバージョンによって挙動が異なる可能性
- Python環境のsupabase-pyパッケージのバージョンを確認
- WebSocketイベントは環境依存性が高いため、実環境でのテストが必須