import json
import threading
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

# Supabaseのインポートを試行
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None

# リトライデコレータ
def retry_on_failure(max_retries: int = 3, delay: int = 5):
    """失敗時に自動リトライするデコレータ"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # selfがある場合のログ処理
                        if args and hasattr(args[0], 'logger'):
                            self = args[0]
                            msg = f"[リトライ {attempt + 1}/{max_retries}] {func.__name__} 失敗: {e}"
                            self.logger.warning(msg)
                            if hasattr(self, 'log_callback') and self.log_callback:
                                self.log_callback(msg, "WARNING")
                        time.sleep(delay)
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator

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
        
        # 各時間足の最終保存時刻を記録
        self.last_save_times = {
            'order_book_15min': None,
            'order_book_30min': None,
            'order_book_1hour': None,
            'order_book_2hour': None,
            'order_book_4hour': None,
            'order_book_daily': None
        }
        
        # 統計情報
        self.stats = {
            'total_saves': 0,
            'successful_saves': 0,
            'failed_saves': 0,
            'retry_count': 0,
            'last_health_check': None
        }
        
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
    
    @retry_on_failure(max_retries=3, delay=5)
    def _initialize_client(self):
        if not SUPABASE_AVAILABLE or not create_client:
            return
        
        try:
            cloud_config = self.config.get("cloud_sync", {})
            self.client = create_client(
                cloud_config["url"],
                cloud_config["anon_key"]
            )
            msg = "[接続成功] Supabase接続を初期化しました"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
        except Exception as e:
            msg = f"[接続エラー] Supabase初期化失敗: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            self.enabled = False
            raise e
    
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
        elapsed = (now - self.last_sync).total_seconds()
        return elapsed >= 240  # 4分 = 240秒
    
    def sync_data_async(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        if not self.should_sync():
            return
        
        # 同期実行のログ（詳細化）
        msg = f"[同期開始] {timestamp} | Ask: {ask_total:.1f} BTC | Bid: {bid_total:.1f} BTC | Price: ${price:,.1f}"
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
        
        # 各時間足データの保存チェック
        self._check_and_save_all_timeframes(timestamp, ask_total, bid_total, price)
    
    def _check_and_save_all_timeframes(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        """全時間足データの保存チェック（改良版）"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            saved_timeframes = []
            
            # 15分足（00, 15, 30, 45分）
            if dt.minute in [0, 15, 30, 45]:
                self._save_timeframe_data('order_book_15min', dt, 15, ask_total, bid_total, price)
                saved_timeframes.append('15分足')
            
            # 30分足（00, 30分）
            if dt.minute in [0, 30]:
                self._save_timeframe_data('order_book_30min', dt, 30, ask_total, bid_total, price)
                saved_timeframes.append('30分足')
            
            # 1時間足（毎時00分）
            if dt.minute == 0:
                self._save_timeframe_data('order_book_1hour', dt, 60, ask_total, bid_total, price)
                saved_timeframes.append('1時間足')
            
            # 2時間足（偶数時の00分）
            if dt.hour % 2 == 0 and dt.minute == 0:
                self._save_timeframe_data('order_book_2hour', dt, 120, ask_total, bid_total, price)
                saved_timeframes.append('2時間足')
            
            # 4時間足（0, 4, 8, 12, 16, 20時の00分）
            if dt.hour in [0, 4, 8, 12, 16, 20] and dt.minute == 0:
                self._save_timeframe_data('order_book_4hour', dt, 240, ask_total, bid_total, price)
                saved_timeframes.append('4時間足')
            
            # 日足（毎日00:00）
            if dt.hour == 0 and dt.minute == 0:
                self._save_timeframe_data('order_book_daily', dt, 1440, ask_total, bid_total, price)
                saved_timeframes.append('日足')
            
            # 保存した時間足をまとめてログ出力
            if saved_timeframes:
                msg = f"[時間足保存] {', '.join(saved_timeframes)} を保存対象として検出"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                
        except Exception as e:
            msg = f"[エラー] 時間足データ保存チェック失敗: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    def _save_timeframe_data(self, table_name: str, dt: datetime, interval_minutes: int, 
                            ask_total: float, bid_total: float, price: float):
        """指定された時間足データをSupabaseに保存（改良版）"""
        try:
            # タイムスタンプを適切な時間足に丸める
            if interval_minutes <= 60:  # 分足の場合
                minutes = (dt.minute // interval_minutes) * interval_minutes
                rounded_timestamp = dt.replace(minute=minutes, second=0, microsecond=0)
            elif interval_minutes < 1440:  # 時間足の場合
                hours = (dt.hour // (interval_minutes // 60)) * (interval_minutes // 60)
                rounded_timestamp = dt.replace(hour=hours, minute=0, second=0, microsecond=0)
            else:  # 日足の場合
                rounded_timestamp = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 時間足の名前を取得
            timeframe_names = {
                'order_book_15min': '15分足',
                'order_book_30min': '30分足',
                'order_book_1hour': '1時間足',
                'order_book_2hour': '2時間足',
                'order_book_4hour': '4時間足',
                'order_book_daily': '日足'
            }
            timeframe_name = timeframe_names.get(table_name, table_name)
            
            # 統計情報を更新
            self.stats['total_saves'] += 1
            
            # 別スレッドでデータを保存
            thread = threading.Thread(
                target=self._save_to_table_with_retry,
                args=(table_name, timeframe_name, rounded_timestamp.isoformat(), ask_total, bid_total, price),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            self.stats['failed_saves'] += 1
            msg = f"[{timeframe_name}] データ保存準備エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    @retry_on_failure(max_retries=3, delay=5)
    def _save_to_table_with_retry(self, table_name: str, timeframe_name: str, timestamp: str, 
                                 ask_total: float, bid_total: float, price: float):
        """指定されたテーブルにデータを保存（リトライ機能付き・最大値比較付き）"""
        try:
            # 既存データを確認
            existing = self.client.table(table_name)\
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
                    self.client.table(table_name)\
                        .update(update_data)\
                        .eq('timestamp', timestamp)\
                        .eq('group_id', self.group_id)\
                        .execute()
                    
                    # 成功ログ（詳細化）
                    dt = datetime.fromisoformat(timestamp)
                    msg = f"[{timeframe_name}] ✓ 更新: {dt.strftime('%Y-%m-%d %H:%M:%S')} (Ask: {existing_data['ask_total']:.1f}→{update_data['ask_total']:.1f}, Bid: {existing_data['bid_total']:.1f}→{update_data['bid_total']:.1f})"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                else:
                    msg = f"[{timeframe_name}] - スキップ: {timestamp} (既に最新)"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
            else:
                # 新規データとして挿入
                data = {
                    "timestamp": timestamp,
                    "ask_total": ask_total,
                    "bid_total": bid_total,
                    "price": price,
                    "group_id": self.group_id
                }
                self.client.table(table_name).insert(data).execute()
                
                # 成功ログ（詳細化）
                dt = datetime.fromisoformat(timestamp)
                msg = f"[{timeframe_name}] ✓ 新規保存: {dt.strftime('%Y-%m-%d %H:%M:%S')} | Ask: {ask_total:.1f} | Bid: {bid_total:.1f}"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
            
            # 統計情報と最終保存時刻を更新
            self.stats['successful_saves'] += 1
            self.last_save_times[table_name] = datetime.now()
                
        except Exception as e:
            self.stats['failed_saves'] += 1
            msg = f"[{timeframe_name}] ✗ 保存失敗: {timestamp} - {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            raise e  # リトライのために例外を再発生
    
    @retry_on_failure(max_retries=3, delay=5)
    def _sync_to_cloud(self, timestamp: str, ask_total: float, bid_total: float, price: float):
        """5分足データの同期（リトライ機能付き）"""
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": ask_total,
                "bid_total": bid_total,
                "price": price,
                "group_id": self.group_id
            }
            
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
                    msg = f"[5分足] ✓ 更新: {timestamp} (Ask: {existing_data['ask_total']:.1f}→{update_data['ask_total']:.1f}, Bid: {existing_data['bid_total']:.1f}→{update_data['bid_total']:.1f})"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                else:
                    msg = f"[5分足] - スキップ: {timestamp} (既に最新)"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
            else:
                # 新規データとして挿入
                self.client.table('order_book_shared').insert(data).execute()
                msg = f"[5分足] ✓ 新規保存: {timestamp} | Ask: {ask_total:.1f} | Bid: {bid_total:.1f} | Price: ${price:,.1f}"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
            
            self.stats['successful_saves'] += 1
                
        except Exception as e:
            self.stats['failed_saves'] += 1
            msg = f"[5分足] ✗ 同期エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            raise e  # リトライのために例外を再発生
    
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック機能"""
        if not self.enabled or not self.client:
            return {
                'status': 'DISABLED',
                'message': 'クラウド同期が無効です'
            }
        
        try:
            results = {
                'status': 'OK',
                'timestamp': datetime.now().isoformat(),
                'statistics': self.stats.copy(),
                'table_status': {}
            }
            
            # 各テーブルの最新データをチェック
            tables = [
                ('order_book_shared', '5分足', 300),  # 5分データは5時間以内が正常
                ('order_book_15min', '15分足', 900),  # 15分データは15時間以内が正常
                ('order_book_30min', '30分足', 1800),  # 30分データは30時間以内が正常
                ('order_book_1hour', '1時間足', 3600),  # 1時間データは60時間以内が正常
                ('order_book_2hour', '2時間足', 7200),  # 2時間データは120時間以内が正常
                ('order_book_4hour', '4時間足', 14400),  # 4時間データは240時間以内が正常
                ('order_book_daily', '日足', 86400)  # 日足データは10日以内が正常
            ]
            
            for table_name, timeframe_name, max_age_seconds in tables:
                try:
                    # 最新データを取得
                    latest = self.client.table(table_name)\
                        .select('timestamp')\
                        .eq('group_id', self.group_id)\
                        .order('timestamp', desc=True)\
                        .limit(1)\
                        .execute()
                    
                    if latest.data:
                        last_update = datetime.fromisoformat(latest.data[0]['timestamp'].replace('Z', '+00:00'))
                        age = (datetime.now() - last_update).total_seconds()
                        
                        if age < max_age_seconds:
                            status = 'OK'
                        elif age < max_age_seconds * 2:
                            status = 'WARNING'
                        else:
                            status = 'STALE'
                        
                        results['table_status'][table_name] = {
                            'name': timeframe_name,
                            'status': status,
                            'last_update': last_update.isoformat(),
                            'age_minutes': round(age / 60, 1)
                        }
                    else:
                        results['table_status'][table_name] = {
                            'name': timeframe_name,
                            'status': 'EMPTY',
                            'message': 'データがありません'
                        }
                        
                except Exception as e:
                    results['table_status'][table_name] = {
                        'name': timeframe_name,
                        'status': 'ERROR',
                        'error': str(e)
                    }
            
            # 全体のステータスを判定
            statuses = [t.get('status', 'ERROR') for t in results['table_status'].values()]
            if all(s == 'OK' for s in statuses):
                results['status'] = 'HEALTHY'
                results['message'] = 'すべてのテーブルが正常です'
            elif any(s == 'ERROR' for s in statuses):
                results['status'] = 'ERROR'
                results['message'] = 'エラーが発生しているテーブルがあります'
            elif any(s == 'STALE' for s in statuses):
                results['status'] = 'WARNING'
                results['message'] = '古いデータのテーブルがあります'
            else:
                results['status'] = 'OK'
                results['message'] = '概ね正常です'
            
            # ヘルスチェック実行をログに記録
            msg = f"[ヘルスチェック] {results['status']}: {results['message']}"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            
            self.stats['last_health_check'] = datetime.now().isoformat()
            return results
            
        except Exception as e:
            msg = f"[ヘルスチェック] エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        stats = self.stats.copy()
        
        # 成功率を計算
        if stats['total_saves'] > 0:
            stats['success_rate'] = round(
                (stats['successful_saves'] / stats['total_saves']) * 100, 1
            )
        else:
            stats['success_rate'] = 0
        
        # 各テーブルの最終保存からの経過時間
        stats['last_save_ages'] = {}
        for table_name, last_time in self.last_save_times.items():
            if last_time:
                age = (datetime.now() - last_time).total_seconds()
                stats['last_save_ages'][table_name] = round(age / 60, 1)  # 分単位
            else:
                stats['last_save_ages'][table_name] = None
        
        return stats
    
    def fetch_all_data(self):
        """Supabaseから全データを取得"""
        if not self.enabled or not self.client:
            return []
        
        try:
            msg = "[データ取得] Supabaseから全データを取得中..."
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
                msg = f"[データ取得] ✓ {len(result_list)}件のデータを取得しました"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return result_list
            else:
                msg = "[データ取得] データはありませんでした"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return []
                
        except Exception as e:
            msg = f"[データ取得] ✗ エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return []
    
    def fetch_missing_data(self, start_time: datetime, end_time: datetime):
        if not self.enabled or not self.client:
            return []
        
        try:
            # データ取得開始のログ
            msg = f"[欠損データ取得] {start_time.strftime('%Y-%m-%d %H:%M:%S')} ～ {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
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
                msg = f"[欠損データ取得] ✓ {len(result_list)}件のデータを取得"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return result_list
            else:
                msg = "[欠損データ取得] 該当するデータはありませんでした"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                return []
            
        except Exception as e:
            msg = f"[欠損データ取得] ✗ エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return []
    
    def fetch_initial_data(self) -> Dict[str, list]:
        """起動時に各時間足テーブルからデータを取得"""
        if not self.enabled or not self.client:
            return {}
        
        tables = [
            ('order_book_shared', '5分足'),
            ('order_book_15min', '15分足'),
            ('order_book_30min', '30分足'),
            ('order_book_1hour', '1時間足'),
            ('order_book_2hour', '2時間足'),
            ('order_book_4hour', '4時間足'),
            ('order_book_daily', '日足')
        ]
        
        all_data = {}
        
        for table_name, timeframe_name in tables:
            try:
                msg = f"[初期データ取得] {timeframe_name}を取得中..."
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
                
                # 各テーブルから最新1000件を取得
                result = self.client.table(table_name)\
                    .select('*')\
                    .eq('group_id', self.group_id)\
                    .order('timestamp', desc=True)\
                    .limit(1000)\
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
                    
                    all_data[table_name] = list(consolidated_data.values())
                    msg = f"[初期データ取得] ✓ {timeframe_name}: {len(all_data[table_name])}件取得"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                else:
                    all_data[table_name] = []
                    msg = f"[初期データ取得] {timeframe_name}: データなし"
                    self.logger.info(msg)
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                        
            except Exception as e:
                msg = f"[初期データ取得] ✗ {timeframe_name}取得エラー: {e}"
                self.logger.error(msg)
                if self.log_callback:
                    self.log_callback(msg, "ERROR")
                all_data[table_name] = []
        
        return all_data
    
    def get_sync_status(self) -> Dict[str, Any]:
        """同期ステータスを取得（拡張版）"""
        status = {
            'enabled': self.enabled,
            'connected': self.client is not None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'group_id': self.group_id,
            'next_sync': (self.last_sync + timedelta(minutes=self.sync_interval)).isoformat() 
                         if self.last_sync else None
        }
        
        # 統計情報を追加
        status['statistics'] = self.get_statistics()
        
        return status