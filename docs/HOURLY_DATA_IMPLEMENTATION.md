# 1時間足データ実装ドキュメント

## 📌 概要
2025年8月17日、デスクトップアプリ（Pythonスクレーパー）に1時間足データ保存機能を実装しました。
これは`desktop-app-spec.md`の第1段階実装です。

## ✅ 実装内容

### 1. Supabaseテーブルの作成
- **テーブル名**: `order_book_1hour`
- **構造**: 5分足テーブル(`order_book_shared`)と同じ構造
- **主要カラム**:
  - `timestamp`: タイムスタンプ（TIMESTAMP WITH TIME ZONE）
  - `ask_total`: 売り板総量（NUMERIC）
  - `bid_total`: 買い板総量（NUMERIC）
  - `price`: 価格（NUMERIC）
  - `group_id`: グループID（デフォルト: 'default-group'）
- **ユニーク制約**: `(timestamp, group_id)`

### 2. cloud_sync.pyの拡張
以下の機能を追加:
- `_check_and_save_hourly_data()`: 毎時00分のデータを検出
- `_save_hourly_data()`: 1時間足データをSupabaseに保存

**動作仕様**:
- 5分ごとのデータ同期時に、分が00の場合は1時間足テーブルにも保存
- 別スレッドで非同期処理
- upsert（存在する場合は更新、なければ挿入）

### 3. データ移行スクリプト
- **ファイル名**: `migrate_1hour_data.py`
- **機能**: 既存の5分足データから1時間足データを生成
- **実績**: 83件の1時間足データを正常に移行

## 📊 データ保存タイミング

| 時刻 | 5分足 | 1時間足 | 備考 |
|------|-------|---------|------|
| 00:00 | ✓ | ✓ | 毎時00分は両方に保存 |
| 00:05 | ✓ | - | 5分足のみ |
| 00:10 | ✓ | - | 5分足のみ |
| ... | ✓ | - | 5分足のみ |
| 00:55 | ✓ | - | 5分足のみ |
| 01:00 | ✓ | ✓ | 毎時00分は両方に保存 |

## 🔧 使用方法

### 通常運用
CoinglassScraperを通常通り起動するだけで、自動的に1時間足データも保存されます。

### 過去データの移行
```bash
python migrate_1hour_data.py
```

### テスト実行
```bash
python test_1hour_data.py
```

## 📈 Webアプリでの利用

Webアプリ側では、1時間足を選択した際に`order_book_1hour`テーブルから直接データを取得できます:

```javascript
// 1時間足データの取得
const { data, error } = await supabase
  .from('order_book_1hour')
  .select('*')
  .eq('group_id', 'default-group')
  .order('timestamp', { ascending: false })
  .limit(300);
```

## ⚠️ 注意事項

1. **初回実行時**: 1時間足データは毎時00分にのみ保存されるため、最初のデータは次の00分まで待つ必要があります
2. **データ移行**: 過去の5分足データがある場合は、`migrate_1hour_data.py`を実行して1時間足データを生成してください
3. **時刻同期**: サーバーの時刻が正確であることを確認してください

## 📊 動作確認結果

- ✅ Supabaseテーブル作成: 成功
- ✅ cloud_sync.py拡張: 成功
- ✅ データ移行スクリプト: 83件のデータを移行
- ✅ テストデータ挿入: 成功

## 🚀 次のステップ

第2段階の実装（15分足、4時間足、日足）に進む準備ができています。
詳細は`desktop-app-spec.md`を参照してください。