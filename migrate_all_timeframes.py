#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存の5分足データから全時間足データを生成するスクリプト
MCPツールも活用してSQL経由で効率的に処理
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

def migrate_all_timeframes():
    """5分足データから全時間足データを生成"""
    
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
    
    # 各時間足の処理
    timeframes = [
        ('15min', 'order_book_15min', '15分足'),
        ('30min', 'order_book_30min', '30分足'),
        ('2hour', 'order_book_2hour', '2時間足'),
        ('4hour', 'order_book_4hour', '4時間足'),
        ('daily', 'order_book_daily', '日足')
    ]
    
    print("\n=== 全時間足データの移行開始 ===\n")
    
    for interval, table_name, timeframe_name in timeframes:
        print(f"\n{timeframe_name}の処理を開始...")
        try:
            if interval == '15min':
                migrate_15min(client, group_id, table_name)
            elif interval == '30min':
                migrate_30min(client, group_id, table_name)
            elif interval == '2hour':
                migrate_2hour(client, group_id, table_name)
            elif interval == '4hour':
                migrate_4hour(client, group_id, table_name)
            elif interval == 'daily':
                migrate_daily(client, group_id, table_name)
                
        except Exception as e:
            print(f"{timeframe_name}の処理でエラー: {e}")
    
    print("\n=== 移行結果の確認 ===\n")
    
    # 各テーブルのデータ件数を確認
    for _, table_name, timeframe_name in timeframes:
        try:
            result = client.table(table_name)\
                .select('*', count='exact')\
                .eq('group_id', group_id)\
                .execute()
            
            print(f"{timeframe_name}: {result.count}件")
            
        except Exception as e:
            print(f"{timeframe_name}: エラー - {e}")
    
    print("\n=== 移行完了 ===")

def migrate_15min(client, group_id, table_name):
    """15分足データの移行"""
    print("  5分足データを取得中...")
    
    # 5分足データを取得（最新1000件）
    result = client.table('order_book_shared')\
        .select('*')\
        .eq('group_id', group_id)\
        .order('timestamp', desc=True)\
        .limit(1000)\
        .execute()
    
    if not result.data:
        print("  5分足データがありません")
        return
    
    print(f"  {len(result.data)}件の5分足データを取得")
    
    # 15分単位でグループ化
    grouped_data = {}
    for record in result.data:
        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        # 15分単位に丸める
        rounded_dt = dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0)
        key = rounded_dt.isoformat()
        
        # 各時間帯で最後のデータを保持（終値として使用）
        if key not in grouped_data or dt > datetime.fromisoformat(grouped_data[key]['timestamp'].replace('Z', '+00:00')):
            grouped_data[key] = record
    
    print(f"  {len(grouped_data)}個の15分足データを生成")
    
    # バッチ挿入
    success_count = 0
    for timestamp, record in grouped_data.items():
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": record['ask_total'],
                "bid_total": record['bid_total'],
                "price": record['price'],
                "group_id": group_id
            }
            client.table(table_name).upsert(data).execute()
            success_count += 1
        except Exception as e:
            print(f"  エラー: {timestamp} - {e}")
    
    print(f"  完了: {success_count}/{len(grouped_data)}件を保存")

def migrate_30min(client, group_id, table_name):
    """30分足データの移行"""
    print("  5分足データを取得中...")
    
    result = client.table('order_book_shared')\
        .select('*')\
        .eq('group_id', group_id)\
        .order('timestamp', desc=True)\
        .limit(1000)\
        .execute()
    
    if not result.data:
        print("  5分足データがありません")
        return
    
    print(f"  {len(result.data)}件の5分足データを取得")
    
    # 30分単位でグループ化
    grouped_data = {}
    for record in result.data:
        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        rounded_dt = dt.replace(minute=(dt.minute // 30) * 30, second=0, microsecond=0)
        key = rounded_dt.isoformat()
        
        if key not in grouped_data or dt > datetime.fromisoformat(grouped_data[key]['timestamp'].replace('Z', '+00:00')):
            grouped_data[key] = record
    
    print(f"  {len(grouped_data)}個の30分足データを生成")
    
    success_count = 0
    for timestamp, record in grouped_data.items():
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": record['ask_total'],
                "bid_total": record['bid_total'],
                "price": record['price'],
                "group_id": group_id
            }
            client.table(table_name).upsert(data).execute()
            success_count += 1
        except Exception as e:
            print(f"  エラー: {timestamp} - {e}")
    
    print(f"  完了: {success_count}/{len(grouped_data)}件を保存")

def migrate_2hour(client, group_id, table_name):
    """2時間足データの移行"""
    print("  1時間足データを取得中...")
    
    # 1時間足データから生成（効率化）
    result = client.table('order_book_1hour')\
        .select('*')\
        .eq('group_id', group_id)\
        .order('timestamp', desc=True)\
        .limit(500)\
        .execute()
    
    if not result.data:
        print("  1時間足データがありません")
        return
    
    print(f"  {len(result.data)}件の1時間足データを取得")
    
    # 2時間単位でグループ化
    grouped_data = {}
    for record in result.data:
        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        rounded_dt = dt.replace(hour=(dt.hour // 2) * 2, minute=0, second=0, microsecond=0)
        key = rounded_dt.isoformat()
        
        if key not in grouped_data or dt > datetime.fromisoformat(grouped_data[key]['timestamp'].replace('Z', '+00:00')):
            grouped_data[key] = record
    
    print(f"  {len(grouped_data)}個の2時間足データを生成")
    
    success_count = 0
    for timestamp, record in grouped_data.items():
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": float(record['ask_total']),
                "bid_total": float(record['bid_total']),
                "price": float(record['price']),
                "group_id": group_id
            }
            client.table(table_name).upsert(data).execute()
            success_count += 1
        except Exception as e:
            print(f"  エラー: {timestamp} - {e}")
    
    print(f"  完了: {success_count}/{len(grouped_data)}件を保存")

def migrate_4hour(client, group_id, table_name):
    """4時間足データの移行"""
    print("  1時間足データを取得中...")
    
    result = client.table('order_book_1hour')\
        .select('*')\
        .eq('group_id', group_id)\
        .order('timestamp', desc=True)\
        .limit(500)\
        .execute()
    
    if not result.data:
        print("  1時間足データがありません")
        return
    
    print(f"  {len(result.data)}件の1時間足データを取得")
    
    # 4時間単位でグループ化
    grouped_data = {}
    for record in result.data:
        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        rounded_dt = dt.replace(hour=(dt.hour // 4) * 4, minute=0, second=0, microsecond=0)
        key = rounded_dt.isoformat()
        
        if key not in grouped_data or dt > datetime.fromisoformat(grouped_data[key]['timestamp'].replace('Z', '+00:00')):
            grouped_data[key] = record
    
    print(f"  {len(grouped_data)}個の4時間足データを生成")
    
    success_count = 0
    for timestamp, record in grouped_data.items():
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": float(record['ask_total']),
                "bid_total": float(record['bid_total']),
                "price": float(record['price']),
                "group_id": group_id
            }
            client.table(table_name).upsert(data).execute()
            success_count += 1
        except Exception as e:
            print(f"  エラー: {timestamp} - {e}")
    
    print(f"  完了: {success_count}/{len(grouped_data)}件を保存")

def migrate_daily(client, group_id, table_name):
    """日足データの移行"""
    print("  1時間足データを取得中...")
    
    result = client.table('order_book_1hour')\
        .select('*')\
        .eq('group_id', group_id)\
        .order('timestamp', desc=True)\
        .limit(500)\
        .execute()
    
    if not result.data:
        print("  1時間足データがありません")
        return
    
    print(f"  {len(result.data)}件の1時間足データを取得")
    
    # 日単位でグループ化
    grouped_data = {}
    for record in result.data:
        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        rounded_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        key = rounded_dt.isoformat()
        
        if key not in grouped_data or dt > datetime.fromisoformat(grouped_data[key]['timestamp'].replace('Z', '+00:00')):
            grouped_data[key] = record
    
    print(f"  {len(grouped_data)}個の日足データを生成")
    
    success_count = 0
    for timestamp, record in grouped_data.items():
        try:
            data = {
                "timestamp": timestamp,
                "ask_total": float(record['ask_total']),
                "bid_total": float(record['bid_total']),
                "price": float(record['price']),
                "group_id": group_id
            }
            client.table(table_name).upsert(data).execute()
            success_count += 1
        except Exception as e:
            print(f"  エラー: {timestamp} - {e}")
    
    print(f"  完了: {success_count}/{len(grouped_data)}件を保存")

if __name__ == "__main__":
    print("=== 全時間足データの移行 ===\n")
    migrate_all_timeframes()