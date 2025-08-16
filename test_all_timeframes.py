#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全時間足データ保存機能のテストスクリプト
"""

import json
import os
from datetime import datetime
from supabase import create_client, Client

def load_config():
    """設定ファイルを読み込む"""
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    config_path = os.path.join(appdata_dir, 'config.json')
    
    if not os.path.exists(config_path):
        print(f"設定ファイルが見つかりません: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_all_timeframes():
    """全時間足テーブルにテストデータを挿入"""
    
    # 設定を読み込み
    config = load_config()
    if not config:
        return
    
    cloud_config = config.get("cloud_sync", {})
    if not cloud_config.get("enabled"):
        print("クラウド同期が無効になっています")
        return
    
    # Supabaseクライアントを初期化
    try:
        client = create_client(
            cloud_config["url"],
            cloud_config["anon_key"]
        )
        print("Supabaseに接続しました")
    except Exception as e:
        print(f"Supabase接続エラー: {e}")
        return
    
    group_id = cloud_config.get("group_id", "default-group")
    
    # テストデータ
    test_data = {
        "ask_total": 7777.7,
        "bid_total": 8888.8,
        "price": 99999.9,
        "group_id": group_id
    }
    
    # 各時間足テーブルの定義
    timeframes = [
        ('order_book_15min', '15分足', datetime(2025, 1, 16, 12, 15, 0)),
        ('order_book_30min', '30分足', datetime(2025, 1, 16, 12, 30, 0)),
        ('order_book_1hour', '1時間足', datetime(2025, 1, 16, 13, 0, 0)),
        ('order_book_2hour', '2時間足', datetime(2025, 1, 16, 14, 0, 0)),
        ('order_book_4hour', '4時間足', datetime(2025, 1, 16, 16, 0, 0)),
        ('order_book_daily', '日足', datetime(2025, 1, 17, 0, 0, 0))
    ]
    
    print("\n=== 各時間足テーブルへのテストデータ挿入 ===\n")
    
    for table_name, timeframe_name, test_timestamp in timeframes:
        try:
            # テストデータを挿入
            data = {
                "timestamp": test_timestamp.isoformat(),
                "ask_total": test_data["ask_total"],
                "bid_total": test_data["bid_total"],
                "price": test_data["price"],
                "group_id": test_data["group_id"]
            }
            
            print(f"{timeframe_name} ({table_name}): ", end="")
            
            # upsert実行
            client.table(table_name).upsert(data).execute()
            
            print(f"[OK] 成功 - {test_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 挿入したデータを確認
            result = client.table(table_name)\
                .select('*')\
                .eq('timestamp', test_timestamp.isoformat())\
                .eq('group_id', group_id)\
                .execute()
            
            if result.data:
                record = result.data[0]
                print(f"  確認: Ask={record['ask_total']}, Bid={record['bid_total']}, Price={record['price']}")
            
        except Exception as e:
            print(f"[ERROR] エラー: {e}")
    
    print("\n=== 各テーブルのデータ件数確認 ===\n")
    
    # 各テーブルのデータ件数を確認
    for table_name, timeframe_name, _ in timeframes:
        try:
            # データ件数を取得（最新10件）
            result = client.table(table_name)\
                .select('*')\
                .eq('group_id', group_id)\
                .order('timestamp', desc=True)\
                .limit(10)\
                .execute()
            
            print(f"{timeframe_name}: {len(result.data)}件")
            
            if result.data:
                # 最新データの時刻を表示
                latest = datetime.fromisoformat(result.data[0]['timestamp'].replace('Z', '+00:00'))
                print(f"  最新: {latest.strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"{timeframe_name}: エラー - {e}")
    
    print("\n=== テスト完了 ===")
    print("\n注意事項:")
    print("- 実際の運用では、各時間足の適切なタイミングでのみデータが保存されます")
    print("- 15分足: 00, 15, 30, 45分")
    print("- 30分足: 00, 30分")
    print("- 1時間足: 毎時00分")
    print("- 2時間足: 偶数時の00分")
    print("- 4時間足: 0, 4, 8, 12, 16, 20時の00分")
    print("- 日足: 毎日00:00")

if __name__ == "__main__":
    test_all_timeframes()