"""
Realtimeエラー修正のテストスクリプト
実行して5分待ってエラーが出ないことを確認
"""

import sys
import time
import logging
from datetime import datetime
from realtime_sync import RealtimeSync

# ログ設定をDEBUGレベルに
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def log_callback(msg, level):
    """ログコールバック"""
    print(f"[{level}] {msg}")

def update_callback(table_name, timeframe_name, data):
    """更新コールバック"""
    print(f"\n{'='*60}")
    print(f"[UPDATE] {timeframe_name}のデータ更新を受信！")
    print(f"  テーブル: {table_name}")
    print(f"  タイムスタンプ: {data.get('timestamp')}")
    print(f"  Ask: {data.get('ask_total')}")
    print(f"  Bid: {data.get('bid_total')}")
    print(f"  価格: {data.get('price')}")
    print(f"{'='*60}\n")

def main():
    print("\n=== Realtime同期エラー修正テスト ===\n")
    print("1. ペイロード構造の確認")
    print("2. イベントタイプの正しい取得")
    print("3. データ保存フィルタの動作確認")
    print("\n5分間監視を続けます...\n")
    
    # 設定を読み込み
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # RealtimeSync初期化
    sync = RealtimeSync(
        config=config,
        log_callback=log_callback
    )
    
    # 同期開始
    if sync.start(update_callback=update_callback):
        print("[OK] Realtime同期を開始しました")
        print("[WAIT] データ更新を待機中...")
        print("（5分ごとにデータが更新されます）")
        print("\nCtrl+Cで終了\n")
        
        try:
            # 5分間待機
            for i in range(300):
                time.sleep(1)
                if i % 60 == 0:
                    remaining = (300 - i) // 60
                    print(f"残り {remaining} 分...")
        except KeyboardInterrupt:
            print("\n[INFO] ユーザーによる中断")
    else:
        print("[ERROR] Realtime同期の開始に失敗しました")
        return 1
    
    # 同期停止
    sync.stop()
    print("\n[OK] テスト完了")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())