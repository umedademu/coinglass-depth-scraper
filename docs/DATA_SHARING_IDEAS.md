# データ共有機能のアイディア

## 概要
Coinglass Scraperのユーザー間でデータを共有し、24時間365日のデータ収集を実現する協調型システムの設計案。

## 現在の仕様
- **データ保存**: SQLiteローカルDB（`btc_usdt_order_book.db`）
- **保存間隔**: 1分に1レコード
- **データ構造**: timestamp, ask_total, bid_total, price
- **保存期間**: 300日（自動削除）

## データ共有の基本コンセプト
```
ユーザーA（稼働中） → データ取得 → クラウドDB → ユーザーB（起動時に取得）
                         ↓
                    ローカルSQLite（バックアップ）
```

## クラウドサービス別の制限

### Supabase
- **無料枠**: 500MB、50,000行/月、2GB帯域幅
- **1ユーザー/月**: 43,200行（ギリギリ）
- **複数ユーザー**: 重複排除すれば同じ行数

### 代替サービス
1. **Firebase Realtime Database**
   - 1GB無料、同時接続100
   - リアルタイム同期に最適

2. **Google Sheets API**
   - 無料、制限緩い
   - 簡易的なデータ共有に便利

3. **MongoDB Atlas**
   - 512MB無料
   - より高度なクエリが可能

## 推奨実装パターン

### パターン1: 階層型データ保存
```
ローカルDB:
- 全期間: 1分単位で保存

クラウドDB:
- 直近24時間: 1分単位
- 1週間前まで: 5分単位
- 1ヶ月前まで: 15分単位
- それ以前: 1時間単位
```

### パターン2: 間引き保存
```python
# ローカル: 毎分保存
save_to_local_db(data)  # 既存処理

# クラウド: 5分ごとに保存
if datetime.now().minute % 5 == 0:
    save_to_cloud_db(data)
```
月間使用量: 8,640行（余裕あり）

### パターン3: オンデマンド同期
- 通常時: ローカルのみ保存
- 起動時: 欠損期間をクラウドから取得
- 終了時: 自分のデータをアップロード

## 実装に必要な変更

### 1. 設定ファイル追加
```json
{
  "cloud_sync": {
    "enabled": true,
    "service": "supabase",
    "api_key": "your-api-key",
    "url": "your-project-url",
    "group_id": "friends-group-001"
  }
}
```

### 2. 同期モジュール
```python
class CloudSync:
    def __init__(self, config):
        self.supabase = create_client(config['url'], config['api_key'])
    
    def upload_data(self, data):
        # 重複チェック後アップロード
        pass
    
    def download_missing_data(self, start_time, end_time):
        # 欠損期間のデータ取得
        pass
```

### 3. UIの追加要素
- 同期状態の表示
- グループ設定
- 同期ON/OFF切り替え

## セキュリティ考慮事項

1. **APIキーの管理**
   - 環境変数または暗号化設定ファイル
   - ユーザーには見せない

2. **グループ機能**
   - グループIDによるアクセス制御
   - 招待制またはパスワード保護

3. **データ検証**
   - 異常値の検出
   - タイムスタンプの整合性チェック

## メリット
- **24時間データ収集**: 誰か1人でも動いていればOK
- **データ欠損なし**: PC停止中も他ユーザーが補完
- **負荷分散**: 複数人で監視の信頼性向上
- **コスト削減**: 無料枠で十分運用可能

## デメリット・課題
- **プライバシー**: データ共有の範囲設定
- **依存性**: クラウドサービスへの依存
- **複雑性**: 同期ロジックの実装
- **帯域幅**: アップロード/ダウンロードの通信量

## データ信頼性の確保

### 現在の実装
- **3回試行**: 15秒、30秒、45秒でスクレイピング
- **最大値選択**: `select_best_values()`で3回の中から最大値を選択
- **理由**: スクレイピングエラーは値が小さくなる方向にしか発生しない

### クラウド同期での信頼性
- **同じ原則を適用**: 複数ユーザーのデータから最大値を選択
- **conflict resolution**: タイムスタンプが同じデータは`MAX(ask_total, bid_total)`を採用
- **データクリーニング**: 異常に小さい値は自動的に除外される

## パフォーマンス影響

### 最小限の影響を実現する設計
1. **非同期処理**: 別スレッドでSupabase通信（UIブロックなし）
2. **低頻度**: 5分に1回のみ（スクレイピングは1分ごと）
3. **軽量データ**: 1レコード数十バイト程度
4. **ローカルファースト**: 通信エラー時もローカル動作は継続

### 実装例
```python
import threading
from datetime import datetime

class CloudSyncManager:
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.sync_interval = 5  # minutes
        self.last_sync = None
        
    def should_sync(self):
        if not self.last_sync:
            return True
        return (datetime.now() - self.last_sync).seconds >= self.sync_interval * 60
    
    def sync_data_async(self, data):
        """非同期でデータを同期"""
        if self.should_sync():
            thread = threading.Thread(target=self._sync_to_cloud, args=(data,))
            thread.daemon = True
            thread.start()
            self.last_sync = datetime.now()
    
    def _sync_to_cloud(self, data):
        """実際の同期処理（別スレッド）"""
        try:
            # 既存データとの比較
            existing = self.client.table('order_book_shared').select('*').eq('timestamp', data['timestamp']).execute()
            
            if existing.data:
                # 最大値を選択してアップデート
                if data['ask_total'] > existing.data[0]['ask_total'] or data['bid_total'] > existing.data[0]['bid_total']:
                    self.client.table('order_book_shared').update({
                        'ask_total': max(data['ask_total'], existing.data[0]['ask_total']),
                        'bid_total': max(data['bid_total'], existing.data[0]['bid_total'])
                    }).eq('timestamp', data['timestamp']).execute()
            else:
                # 新規データとして挿入
                self.client.table('order_book_shared').insert(data).execute()
        except Exception as e:
            # エラーはログに記録するが、メイン処理は継続
            logger.error(f"Cloud sync error: {e}")
```

## 今後の実装計画

### フェーズ1: 基本実装（推奨）
- **Supabase統合**: 非同期アップロード実装
- **5分間隔同期**: パフォーマンス影響を最小化
- **起動時データ取得**: 欠損期間の自動補完
- **最大値選択ロジック**: データ信頼性の確保
- **設定ファイル**: Supabase認証情報の管理

### フェーズ2: UI改善
- **同期状態表示**: ステータスバーに同期アイコン
- **同期設定画面**: ON/OFF切り替え、間隔調整
- **データ統計**: 共有ユーザー数、カバー率表示

### フェーズ3: 高度な機能
- **グループ管理**: プライベートグループ作成
- **データ分析**: 複数ユーザーの傾向分析
- **自動フェイルオーバー**: 複数クラウドサービス対応