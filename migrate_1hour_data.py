#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存の5分足データから1時間足データを生成するスクリプト
"""

import json
import os
from datetime import datetime, timedelta
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

def migrate_hourly_data():
    """5分足データから1時間足データを生成"""
    
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
    
    try:
        # 5分足データを取得（最新1000件）
        print("5分足データを取得中...")
        result = client.table('order_book_shared')\
            .select('*')\
            .eq('group_id', group_id)\
            .order('timestamp', desc=True)\
            .limit(1000)\
            .execute()
        
        if not result.data:
            print("5分足データがありません")
            return
        
        print(f"{len(result.data)}件の5分足データを取得しました")
        
        # 時間ごとにグループ化
        hourly_data = {}
        for record in result.data:
            # タイムスタンプをパース
            ts_str = record['timestamp']
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            
            # 時間の境界（00分）にグループ化
            hourly_key = dt.replace(minute=0, second=0, microsecond=0)
            
            # 各時間で最後のデータ（終値）を保持
            if hourly_key not in hourly_data:
                hourly_data[hourly_key] = record
            else:
                # より新しいデータの場合は更新
                existing_dt = datetime.fromisoformat(hourly_data[hourly_key]['timestamp'].replace('Z', '+00:00'))
                if dt > existing_dt:
                    hourly_data[hourly_key] = record
        
        print(f"\n{len(hourly_data)}個の1時間足データを生成します")
        
        # 1時間足データをSupabaseに保存
        success_count = 0
        for hourly_key, record in sorted(hourly_data.items()):
            try:
                data = {
                    "timestamp": hourly_key.isoformat(),
                    "ask_total": record['ask_total'],
                    "bid_total": record['bid_total'],
                    "price": record['price'],
                    "group_id": group_id
                }
                
                # upsert（存在する場合は更新、なければ挿入）
                client.table('order_book_1hour').upsert(data).execute()
                success_count += 1
                print(f"保存: {hourly_key.strftime('%Y-%m-%d %H:%M')} - Ask: {record['ask_total']:.1f}, Bid: {record['bid_total']:.1f}")
                
            except Exception as e:
                print(f"エラー: {hourly_key} - {e}")
        
        print(f"\n完了: {success_count}/{len(hourly_data)}件の1時間足データを保存しました")
        
        # 保存されたデータを確認
        verify_result = client.table('order_book_1hour')\
            .select('*')\
            .eq('group_id', group_id)\
            .order('timestamp', desc=True)\
            .limit(10)\
            .execute()
        
        if verify_result.data:
            print(f"\n最新の1時間足データ（上位10件）:")
            for record in verify_result.data:
                dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                print(f"  {dt.strftime('%Y-%m-%d %H:%M')}: Ask={record['ask_total']}, Bid={record['bid_total']}, Price={record['price']}")
        
    except Exception as e:
        print(f"処理エラー: {e}")

if __name__ == "__main__":
    print("=== 1時間足データの移行 ===\n")
    migrate_hourly_data()