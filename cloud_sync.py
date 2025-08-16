import json
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Supabaseのインポートを試行
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None

class CloudSyncManager:
    def __init__(self, config_path: str = None, log_callback=None):
        # loggerを最初に初期化
        self.logger = logging.getLogger(__name__)
        self.log_callback = log_callback
        
        # config_pathが指定されていない場合は、AppDataから読み込む
        if config_path is None:
            import os
            appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
            config_path = os.path.join(appdata_dir, 'config.json')
        
        # 設定を読み込み
        self.config = self._load_config(config_path)
        # Supabaseが利用できない場合は無効化
        if not SUPABASE_AVAILABLE:
            self.enabled = False
            msg = "Supabaseモジュールが利用できないため、クラウド同期は無効です"
            self.logger.warning(msg)
            if self.log_callback:
                self.log_callback(msg, "WARNING")
        else:
            self.enabled = self.config.get("cloud_sync", {}).get("enabled", False)
        
        self.client: Optional[Client] = None
        self.last_sync: Optional[datetime] = None
        self.sync_interval = self.config.get("cloud_sync", {}).get("sync_interval_minutes", 5)
        self.group_id = self.config.get("cloud_sync", {}).get("group_id", "default-group")
        
        if self.enabled and SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            msg = f"設定ファイルの読み込みに失敗: {e}"
            self.logger.warning(msg)
            if self.log_callback:
                self.log_callback(msg, "WARNING")
            return {}
    
    def _initialize_client(self):
        if not SUPABASE_AVAILABLE or not create_client:
            return
        
        try:
            cloud_config = self.config.get("cloud_sync", {})
            self.client = create_client(
                cloud_config["url"],
                cloud_config["anon_key"]
            )
            msg = "Supabase接続を初期化しました"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
        except Exception as e:
            msg = f"Supabase初期化エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            self.enabled = False
    
    def should_sync(self) -> bool:
        if not self.enabled or not self.client:
            return False
        
        now = datetime.now()
        current_minute = now.minute
        
        # 5分間隔の固定タイミング（0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55分）
        if current_minute % 5 != 0:
            return False
        
        # 最初の同期または前回の同期から5分以上経過している場合
        if not self.last_sync:
            return True
        
        # 前回の同期から少なくとも4分以上経過していることを確認
        # （同じ5分間隔で複数回同期しないようにするため）
        elapsed = (now - self.last_sync).total_seconds()
        return elapsed >= 240  # 4分 = 240秒
    
    def sync_data_async(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        if not self.should_sync():
            return
        
        # 同期実行のログ
        msg = f"クラウド同期スレッドを起動: {timestamp}"
        self.logger.info(msg)
        if self.log_callback:
            self.log_callback(msg, "INFO")
        
        thread = threading.Thread(
            target=self._sync_to_cloud,
            args=(timestamp, ask_total, bid_total, price),
            daemon=True
        )
        thread.start()
        self.last_sync = datetime.now()
        
        # 1時間足データの保存チェック
        self._check_and_save_hourly_data(timestamp, ask_total, bid_total, price)
    
    def _check_and_save_hourly_data(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        """1時間足データの保存（毎時00分のみ）"""
        try:
            # タイムスタンプをdatetimeオブジェクトに変換
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # 00分の場合のみ1時間足データを保存
            if dt.minute == 0:
                # 1時間足用のタイムスタンプ（秒・ミリ秒を0に）
                hourly_timestamp = dt.replace(second=0, microsecond=0)
                
                msg = f"1時間足データを保存: {hourly_timestamp.isoformat()}"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                
                # 別スレッドで1時間足データを保存
                thread = threading.Thread(
                    target=self._save_hourly_data,
                    args=(hourly_timestamp.isoformat(), ask_total, bid_total, price),
                    daemon=True
                )
                thread.start()
        except Exception as e:
            msg = f"1時間足データ保存チェックエラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    def _save_hourly_data(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        """1時間足データをSupabaseに保存"""
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": ask_total,
                "bid_total": bid_total,
                "price": price,
                "group_id": self.group_id
            }
            
            # upsert（存在する場合は更新、なければ挿入）
            self.client.table('order_book_1hour').upsert(data).execute()
            
            msg = f"1時間足データを保存しました: {timestamp}"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
                
        except Exception as e:
            msg = f"1時間足データ保存エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    def _sync_to_cloud(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": ask_total,
                "bid_total": bid_total,
                "price": price,
                "group_id": self.group_id
            }
            
            # 同期開始のログ
            msg = f"Supabaseへの同期を開始: {timestamp}"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            
            # 既存データを確認
            existing = self.client.table('order_book_shared')\
                .select('*')\
                .eq('timestamp', timestamp)\
                .eq('group_id', self.group_id)\
                .execute()
            
            if existing.data:
                # 最大値を選択してアップデート
                existing_data = existing.data[0]
                if ask_total > existing_data['ask_total'] or bid_total > existing_data['bid_total']:
                    update_data = {
                        'ask_total': max(ask_total, existing_data['ask_total']),
                        'bid_total': max(bid_total, existing_data['bid_total']),
                        'price': price
                    }
                    self.client.table('order_book_shared')\
                        .update(update_data)\
                        .eq('timestamp', timestamp)\
                        .eq('group_id', self.group_id)\
                        .execute()
                    msg = f"データを更新しました: {timestamp} (ask: {existing_data['ask_total']} → {update_data['ask_total']}, bid: {existing_data['bid_total']} → {update_data['bid_total']})"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                else:
                    msg = f"データは既に最新です（更新スキップ）: {timestamp}"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
            else:
                # 新規データとして挿入
                self.client.table('order_book_shared').insert(data).execute()
                msg = f"新規データをアップロード: {timestamp} (ask: {ask_total}, bid: {bid_total}, price: {price})"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                
        except Exception as e:
            msg = f"クラウド同期エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    def fetch_all_data(self):
        """Supabaseから全データを取得"""
        if not self.enabled or not self.client:
            return []
        
        try:
            msg = "Supabaseから全データを取得中..."
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            
            # 全データを取得（最大10000件まで）
            result = self.client.table('order_book_shared')\
                .select('*')\
                .eq('group_id', self.group_id)\
                .order('timestamp')\
                .limit(10000)\
                .execute()
            
            if result.data:
                # 重複するタイムスタンプがある場合は最大値を選択
                consolidated_data = {}
                for record in result.data:
                    ts = record['timestamp']
                    if ts not in consolidated_data:
                        consolidated_data[ts] = record
                    else:
                        # 最大値を選択
                        existing = consolidated_data[ts]
                        consolidated_data[ts] = {
                            'timestamp': ts,
                            'ask_total': max(record['ask_total'], existing['ask_total']),
                            'bid_total': max(record['bid_total'], existing['bid_total']),
                            'price': record['price']
                        }
                
                result_list = list(consolidated_data.values())
                msg = f"Supabaseから{len(result_list)}件のデータを取得しました"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return result_list
            else:
                msg = "Supabaseにデータはありませんでした"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return []
                
        except Exception as e:
            msg = f"全データ取得エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return []
    
    def fetch_missing_data(self, start_time: datetime, end_time: datetime):
        if not self.enabled or not self.client:
            return []
        
        try:
            # データ取得開始のログ
            msg = f"Supabaseから欠損データを取得中: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ～ {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            
            # 指定期間のデータを取得
            result = self.client.table('order_book_shared')\
                .select('*')\
                .eq('group_id', self.group_id)\
                .gte('timestamp', start_time.strftime('%Y-%m-%d %H:%M:%S'))\
                .lte('timestamp', end_time.strftime('%Y-%m-%d %H:%M:%S'))\
                .order('timestamp')\
                .execute()
            
            if result.data:
                # 重複するタイムスタンプがある場合は最大値を選択
                consolidated_data = {}
                for record in result.data:
                    ts = record['timestamp']
                    if ts not in consolidated_data:
                        consolidated_data[ts] = record
                    else:
                        # 最大値を選択
                        existing = consolidated_data[ts]
                        consolidated_data[ts] = {
                            'timestamp': ts,
                            'ask_total': max(record['ask_total'], existing['ask_total']),
                            'bid_total': max(record['bid_total'], existing['bid_total']),
                            'price': record['price']
                        }
                
                result_list = list(consolidated_data.values())
                msg = f"Supabaseから{len(result_list)}件のデータを取得しました"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return result_list
            else:
                msg = "Supabaseに該当するデータはありませんでした"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return []
            
        except Exception as e:
            msg = f"データ取得エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return []
    
    def get_sync_status(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'connected': self.client is not None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'group_id': self.group_id,
            'next_sync': (self.last_sync + timedelta(minutes=self.sync_interval)).isoformat() 
                         if self.last_sync else None
        }