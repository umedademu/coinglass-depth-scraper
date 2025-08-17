"""
Realtime同期のテストスクリプト
"""

import sys
import os
import time
import logging

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def log_callback(msg, level="INFO"):
    """ログコールバック"""
    print(f"[{level}] {msg}")

def main():
    """テストメイン関数"""
    try:
        # まず非同期版がインポートできるか確認
        print("非同期版Supabaseのインポートをテスト...")
        try:
            from supabase import create_async_client, AsyncClient
            print("[OK] 非同期版Supabaseがインポートできました")
        except ImportError as e:
            print(f"[ERROR] 非同期版Supabaseのインポートに失敗: {e}")
            print("同期版と非同期版は同じパッケージに含まれています")
        
        # Realtime同期クラスのインポート
        print("\nRealtime同期クラスのインポートをテスト...")
        try:
            from realtime_sync import RealtimeSync
            print("[OK] RealtimeSyncがインポートできました")
        except ImportError as e:
            print(f"[ERROR] RealtimeSyncのインポートに失敗: {e}")
            return
        
        # CloudSyncManagerのテスト
        print("\nCloudSyncManagerのテスト...")
        try:
            from cloud_sync import CloudSyncManager
            print("[OK] CloudSyncManagerがインポートできました")
            
            # インスタンス作成
            cloud_sync = CloudSyncManager(log_callback=log_callback)
            
            if cloud_sync.enabled:
                print("[OK] クラウド同期が有効です")
                
                # Realtime同期のテスト
                print("\nRealtime同期を開始...")
                
                def test_callback(table_name, records):
                    print(f"テストコールバック: {table_name} - {len(records)}件")
                
                result = cloud_sync.setup_realtime_sync(test_callback)
                
                if result:
                    print("[OK] Realtime同期が開始されました")
                    print("10秒間待機中...")
                    time.sleep(10)
                    
                    # クリーンアップ
                    cloud_sync.cleanup_realtime()
                    print("[OK] Realtime同期を停止しました")
                else:
                    print("[ERROR] Realtime同期の開始に失敗しました")
            else:
                print("[WARNING] クラウド同期が無効です")
                
        except Exception as e:
            print(f"[ERROR] CloudSyncManagerのテストでエラー: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"[ERROR] テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()