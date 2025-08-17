"""
Supabase Realtime同期用の非同期実装
同期版クライアントの制限を回避するため、別スレッドで非同期版を動作させる
"""

import asyncio
import threading
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# 非同期版Supabaseクライアントのインポート
try:
    from supabase import create_async_client, AsyncClient
    ASYNC_SUPABASE_AVAILABLE = True
except ImportError:
    ASYNC_SUPABASE_AVAILABLE = False
    AsyncClient = None
    create_async_client = None


class RealtimeSync:
    """非同期版Supabaseクライアントを使用したRealtime同期"""
    
    def __init__(self, config: Dict[str, Any], log_callback: Optional[Callable] = None):
        self.config = config
        self.log_callback = log_callback
        self.logger = logging.getLogger(__name__)
        
        # 非同期クライアント
        self.client: Optional[AsyncClient] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
        # 設定
        self.enabled = config.get("cloud_sync", {}).get("realtime_enabled", True)
        self.group_id = config.get("cloud_sync", {}).get("group_id", "default-group")
        
        # チャンネル管理
        self.channels = {}
        self.is_running = False
        
        # コールバック
        self.update_callback: Optional[Callable] = None
        
    async def _initialize_client(self):
        """非同期クライアントを初期化"""
        if not ASYNC_SUPABASE_AVAILABLE:
            msg = "[Realtime] 非同期版Supabaseが利用できません"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return False
            
        try:
            cloud_config = self.config.get("cloud_sync", {})
            self.client = await create_async_client(
                cloud_config["url"],
                cloud_config["anon_key"]
            )
            
            msg = "[Realtime] 非同期クライアントを初期化しました"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
                
            return True
            
        except Exception as e:
            msg = f"[Realtime] クライアント初期化エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return False
    
    async def _setup_channels(self):
        """Realtimeチャンネルを設定"""
        if not self.client:
            return False
            
        tables = [
            ('order_book_shared', '5分足'),
            ('order_book_15min', '15分足'),
            ('order_book_30min', '30分足'),
            ('order_book_1hour', '1時間足'),
            ('order_book_2hour', '2時間足'),
            ('order_book_4hour', '4時間足'),
            ('order_book_daily', '日足')
        ]
        
        try:
            for table_name, timeframe_name in tables:
                channel_name = f'realtime-{table_name}-{self.group_id}'
                
                # チャンネルを作成
                channel = self.client.channel(channel_name)
                
                # コールバック関数を作成（非同期版用）
                def create_handler(tn, tfn):
                    def handler(payload):
                        # 非同期関数を同期的に処理
                        try:
                            self._process_update(tn, tfn, payload)
                        except Exception as e:
                            self.logger.error(f"[Realtime] 更新処理エラー: {e}")
                    return handler
                
                # 非同期版のAPIに合わせて修正
                try:
                    # on_postgres_changesメソッドを使用
                    channel.on_postgres_changes(
                        event='*',  # INSERT, UPDATE, DELETE
                        schema='public',
                        table=table_name,
                        filter=f'group_id=eq.{self.group_id}',
                        callback=create_handler(table_name, timeframe_name)
                    )
                    
                    # 購読を開始
                    await channel.subscribe()
                    
                except AttributeError:
                    # 新しいAPIの場合
                    try:
                        # 代替メソッドを試す
                        await channel.on_broadcast(
                            event=f'table-{table_name}',
                            callback=create_handler(table_name, timeframe_name)
                        ).subscribe()
                    except:
                        msg = f"[Realtime] {table_name}のチャンネル設定をスキップ（API非対応）"
                        self.logger.warning(msg)
                        continue
                
                self.channels[table_name] = channel
                
                msg = f"[Realtime] {timeframe_name}の監視を開始しました"
                self.logger.info(msg)
                if self.log_callback:
                    self.log_callback(msg, "INFO")
            
            return True
            
        except Exception as e:
            msg = f"[Realtime] チャンネル設定エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            return False
    
    def _process_update(self, table_name: str, timeframe_name: str, payload: Dict[str, Any]):
        """更新イベントを同期的に処理"""
        try:
            # デバッグ: ペイロード全体を出力
            self.logger.debug(f"[Realtime] ペイロードのキー: {list(payload.keys())}")
            self.logger.debug(f"[Realtime] ペイロード詳細: {payload}")
            
            # 正しいペイロード構造に対応
            event_type = payload.get('data', {}).get('type', 'UNKNOWN')
            
            self.logger.debug(f"[Realtime] イベントタイプ: {event_type}")
            
            if event_type in ['INSERT', 'UPDATE']:
                # 正しいペイロード構造からデータを取得
                new_data = payload.get('data', {}).get('record', {})
                
                if new_data and self.update_callback:
                    # メインスレッドのコールバックを呼び出す（event_typeも渡す）
                    self.update_callback(table_name, timeframe_name, new_data, event_type)
                    
                    msg = f"[Realtime] {timeframe_name}の更新を検出"
                    self.logger.info(msg)  # debugからinfoに変更して確実に表示
                    if self.log_callback:
                        self.log_callback(msg, "INFO")
                    
        except Exception as e:
            msg = f"[Realtime] 更新処理エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
    
    async def _run_async(self):
        """非同期イベントループを実行"""
        try:
            # クライアントを初期化
            if not await self._initialize_client():
                return
            
            # チャンネルを設定
            if not await self._setup_channels():
                return
            
            msg = "[Realtime] 同期を開始しました"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            
            # イベントループを維持
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            msg = f"[Realtime] 実行エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """クリーンアップ処理"""
        try:
            # チャンネルの購読を解除
            for table_name, channel in self.channels.items():
                try:
                    await channel.unsubscribe()
                    msg = f"[Realtime] {table_name}の監視を停止"
                    self.logger.debug(msg)
                except Exception as e:
                    self.logger.warning(f"[Realtime] {table_name}のクリーンアップエラー: {e}")
            
            self.channels.clear()
            
            # クライアントを閉じる
            if self.client:
                await self.client.auth.sign_out()
                
        except Exception as e:
            msg = f"[Realtime] クリーンアップエラー: {e}"
            self.logger.error(msg)
    
    def _thread_target(self):
        """別スレッドで実行されるターゲット関数"""
        # 新しいイベントループを作成
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            # 非同期関数を実行
            self.loop.run_until_complete(self._run_async())
        finally:
            self.loop.close()
    
    def start(self, update_callback: Optional[Callable] = None):
        """Realtime同期を開始"""
        if not self.enabled:
            msg = "[Realtime] Realtime同期が無効です"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
            return False
            
        if self.is_running:
            msg = "[Realtime] 既に実行中です"
            self.logger.warning(msg)
            return False
        
        try:
            self.update_callback = update_callback
            self.is_running = True
            
            # 別スレッドで非同期処理を開始
            self.thread = threading.Thread(
                target=self._thread_target,
                daemon=True,
                name="RealtimeSync"
            )
            self.thread.start()
            
            return True
            
        except Exception as e:
            msg = f"[Realtime] 開始エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")
            self.is_running = False
            return False
    
    def stop(self):
        """Realtime同期を停止"""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # イベントループに停止を通知
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._cleanup(),
                    self.loop
                )
            
            # スレッドの終了を待つ（最大5秒）
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            msg = "[Realtime] 同期を停止しました"
            self.logger.info(msg)
            if self.log_callback:
                self.log_callback(msg, "INFO")
                
        except Exception as e:
            msg = f"[Realtime] 停止エラー: {e}"
            self.logger.error(msg)
            if self.log_callback:
                self.log_callback(msg, "ERROR")