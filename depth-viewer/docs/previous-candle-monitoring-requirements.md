# 1個前の足監視機能 - 要件定義書

## 📌 概要
「早い者負け問題」を解決するため、現在の足に加えて1個前の足までRealtime監視を継続し、後から到着した正しいデータ（最大値）を反映する機能を実装する。

## 🔴 現在の問題：早い者負け問題

### 問題のシナリオ
```
時系列（5分足の例）:
12:00:00 - ユーザーA（自分）が1番乗りでアップロード
         → Supabaseに自分のデータが採用される
         → ローカルDBも自分のデータで確定

12:00:30 - ユーザーB～Z（99人）が後からアップロード
         → Supabaseで最大値が更新される（正しい値）
         → しかしユーザーAは既に12:00のデータを確定済み

12:05:00 - ユーザーAは12:00のデータを更新しない
         → 99人の正しいデータを反映できない！
```

### データ不整合の例
- **ユーザーA（1番乗り）**: Ask 7,344 / Bid 11,907（小さい値のまま）
- **Supabase（最大値）**: Ask 7,962 / Bid 14,001（正しい値）
- **差分**: Ask +618 / Bid +2,094（この差分が反映されない）

## 💡 解決策：1個前の足まで監視

### 基本コンセプト
```
現在時刻: 12:10の場合

【従来の監視範囲】
- 12:10の足のみ（現在の足）

【新しい監視範囲】
- 12:10の足（現在の足）
- 12:05の足（1個前の足）← 追加で監視！
```

### 時間足ごとの監視範囲

| 時間足 | 監視範囲 | 例（現在12:30の場合） |
|--------|----------|------------------------|
| 5分足 | 過去5分前まで | 12:25～12:30を監視 |
| 15分足 | 過去15分前まで | 12:15～12:30を監視 |
| 30分足 | 過去30分前まで | 12:00～12:30を監視 |
| 1時間足 | 過去1時間前まで | 11:00～12:00を監視 |
| 2時間足 | 過去2時間前まで | 10:00～12:00を監視 |
| 4時間足 | 過去4時間前まで | 08:00～12:00を監視 |
| 日足 | 過去1日前まで | 前日00:00～今日00:00を監視 |

## ✅ 実装方針

### 1. Realtime監視範囲の計算
```python
def calculate_monitoring_range(timeframe: str, current_time: datetime):
    """監視すべきタイムスタンプ範囲を計算"""
    
    timeframe_minutes = {
        'order_book_shared': 5,    # 5分足
        'order_book_15min': 15,
        'order_book_30min': 30,
        'order_book_1hour': 60,
        'order_book_2hour': 120,
        'order_book_4hour': 240,
        'order_book_daily': 1440   # 日足
    }
    
    minutes = timeframe_minutes.get(table_name, 5)
    
    # 現在の足の開始時刻
    current_candle_start = floor_to_timeframe(current_time, minutes)
    
    # 1個前の足の開始時刻
    previous_candle_start = current_candle_start - timedelta(minutes=minutes)
    
    return (previous_candle_start, current_candle_start)
```

### 2. Realtime購読の修正
```python
def setup_realtime_monitoring():
    """1個前の足まで監視するRealtime設定"""
    
    # 監視範囲を計算
    start_time, end_time = calculate_monitoring_range(table_name, now)
    
    # フィルタ条件を設定
    channel.on_postgres_changes(
        event='*',  # INSERT, UPDATE, DELETE
        schema='public',
        table=table_name,
        filter=f'group_id=eq.{group_id}',
        # タイムスタンプ範囲のフィルタは別途処理で実装
        callback=handle_realtime_update
    )
```

### 3. データ更新処理
```python
def handle_realtime_update(payload):
    """Realtimeイベントの処理"""
    
    new_data = payload.get('new', {})
    timestamp = new_data.get('timestamp')
    
    # 監視範囲内かチェック
    start_time, end_time = calculate_monitoring_range(table_name, now)
    
    if start_time <= timestamp <= end_time:
        # 最大値比較して更新
        update_local_db_with_max_values(new_data)
        
        # 1個前の足の更新の場合はログ出力
        if timestamp < current_candle_start:
            log(f"[1個前の足更新] {timestamp}のデータを最大値で更新")
```

## 📊 期待される効果

### Before（現在の問題）
- 1番乗りユーザーは自分のデータで固定
- 後から来た正しいデータを反映できない
- データの不整合が発生

### After（改善後）
- 1番乗りでも後から正しいデータに更新
- 全ユーザーで一貫したデータ
- 最大値（正しい値）の確実な反映

## 🎯 実装優先度

1. **第1段階**: Realtimeエラーの修正（前提条件）
2. **第2段階**: 1個前の足監視機能の実装
3. **第3段階**: 動作検証とログ監視

## 📝 テスト計画

### シナリオ1: 基本動作確認
1. 12:00にユーザーAがデータアップロード
2. 12:01にユーザーBがより大きい値をアップロード
3. ユーザーAのローカルDBが更新されることを確認

### シナリオ2: 境界条件テスト
1. 12:05になった瞬間の動作確認
2. 12:00のデータがまだ監視対象であることを確認
3. 11:55のデータは監視対象外であることを確認

### シナリオ3: 全時間足での動作確認
- 5分足、15分足、30分足、1時間足、2時間足、4時間足、日足
- それぞれで1個前の足が正しく監視されることを確認

## ⚠️ 考慮事項

### パフォーマンス
- 監視範囲を1個前に限定（それ以前は極めて稀）
- 不要な古いデータの監視を避ける

### タイミング問題
- 足の切り替わりタイミングでの処理
- タイムゾーンの考慮（JSTで統一）

### エラーハンドリング
- Realtime接続断時の処理
- データ不整合時の警告

## 🔗 関連ファイル
- `realtime_sync.py`: Realtime監視ロジック
- `cloud_sync.py`: データ同期管理
- `coinglass_scraper.py`: ローカルDB更新

## 📚 参考情報
- 現在は全時間足の全INSERTイベントを監視（時間範囲制限なし）
- `fetch_initial_data()`で起動時に最新1000件を取得
- この機能により「早い者負け問題」が根本的に解決される