#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移行データの検証スクリプト
各時間足テーブルのデータ件数と最新データを確認
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

def verify_migration():
    """移行データの検証"""
    
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
        print("Supabaseに接続しました\n")
    except Exception as e:
        print(f"Supabase接続エラー: {e}")
        return
    
    group_id = cloud_config.get("group_id", "default-group")
    
    # 各時間足テーブルの定義
    tables = [
        ('order_book_shared', '5分足'),
        ('order_book_15min', '15分足'),
        ('order_book_30min', '30分足'),
        ('order_book_1hour', '1時間足'),
        ('order_book_2hour', '2時間足'),
        ('order_book_4hour', '4時間足'),
        ('order_book_daily', '日足')
    ]
    
    print("=" * 60)
    print(" 時間足別データ件数と最新データ確認")
    print("=" * 60)
    print()
    
    results = {}
    
    for table_name, timeframe_name in tables:
        try:
            # データ件数を取得
            count_result = client.table(table_name)\
                .select('*', count='exact')\
                .eq('group_id', group_id)\
                .execute()
            
            # 最新データを取得
            latest_result = client.table(table_name)\
                .select('*')\
                .eq('group_id', group_id)\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()
            
            # 最古データを取得
            oldest_result = client.table(table_name)\
                .select('*')\
                .eq('group_id', group_id)\
                .order('timestamp', desc=False)\
                .limit(1)\
                .execute()
            
            count = count_result.count
            
            print(f"【{timeframe_name}】({table_name})")
            print(f"  データ件数: {count:,}件")
            
            if latest_result.data:
                latest = latest_result.data[0]
                latest_dt = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00'))
                print(f"  最新データ: {latest_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    - Ask: {latest['ask_total']:,.1f} BTC")
                print(f"    - Bid: {latest['bid_total']:,.1f} BTC")
                print(f"    - Price: ${latest['price']:,.1f}")
            
            if oldest_result.data:
                oldest = oldest_result.data[0]
                oldest_dt = datetime.fromisoformat(oldest['timestamp'].replace('Z', '+00:00'))
                print(f"  最古データ: {oldest_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # データ期間を計算
                if latest_result.data:
                    duration = latest_dt - oldest_dt
                    days = duration.total_seconds() / 86400
                    print(f"  データ期間: {days:.1f}日間")
            
            print()
            
            results[table_name] = {
                'count': count,
                'latest': latest_dt if latest_result.data else None,
                'oldest': oldest_dt if oldest_result.data else None
            }
            
        except Exception as e:
            print(f"{timeframe_name}: エラー - {e}\n")
            results[table_name] = {'error': str(e)}
    
    # 統計サマリー
    print("=" * 60)
    print(" 統計サマリー")
    print("=" * 60)
    print()
    
    # 期待されるデータ比率を確認
    if 'order_book_shared' in results and results['order_book_shared'].get('count'):
        base_count = results['order_book_shared']['count']
        print(f"基準（5分足）: {base_count:,}件")
        print("\n期待される比率と実際の件数:")
        
        expected_ratios = {
            'order_book_15min': 3,    # 15分は5分の3倍の間隔
            'order_book_30min': 6,    # 30分は5分の6倍の間隔
            'order_book_1hour': 12,   # 1時間は5分の12倍の間隔
            'order_book_2hour': 24,   # 2時間は5分の24倍の間隔
            'order_book_4hour': 48,   # 4時間は5分の48倍の間隔
            'order_book_daily': 288   # 日足は5分の288倍の間隔
        }
        
        for table_name, ratio in expected_ratios.items():
            if table_name in results and results[table_name].get('count'):
                actual_count = results[table_name]['count']
                expected_count = base_count // ratio
                percentage = (actual_count / expected_count * 100) if expected_count > 0 else 0
                
                timeframe = [t[1] for t in tables if t[0] == table_name][0]
                print(f"  {timeframe:8s}: 期待 {expected_count:4,}件, 実際 {actual_count:4,}件 ({percentage:.1f}%)")
    
    print("\n移行検証完了！")
    
    # 移行の健全性チェック
    print("\n" + "=" * 60)
    print(" 健全性チェック")
    print("=" * 60)
    print()
    
    issues = []
    
    # 各時間足でデータが存在するか確認
    for table_name, timeframe_name in tables:
        if table_name in results:
            if results[table_name].get('count', 0) == 0:
                issues.append(f"[WARNING] {timeframe_name}にデータがありません")
            elif results[table_name].get('count', 0) < 10:
                issues.append(f"[WARNING] {timeframe_name}のデータが少なすぎます（{results[table_name]['count']}件）")
    
    if issues:
        print("問題が見つかりました:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("[OK] すべての時間足にデータが正常に存在します")
    
    return results

if __name__ == "__main__":
    print("=== 移行データの検証 ===\n")
    verify_migration()