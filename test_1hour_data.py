#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1時間足データ保存機能のテストスクリプト
"""

import json
import os
from datetime import datetime
from cloud_sync import CloudSyncManager

def test_hourly_data_save():
    """1時間足データ保存のテスト"""
    
    # AppDataフォルダのconfig.jsonを使用
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    config_path = os.path.join(appdata_dir, 'config.json')
    
    # CloudSyncManagerのインスタンス作成
    sync_manager = CloudSyncManager(config_path)
    
    if not sync_manager.enabled:
        print("クラウド同期が無効になっています。config.jsonを確認してください。")
        return
    
    # テスト用のデータ
    test_timestamp = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
    test_ask_total = 5432.1
    test_bid_total = 8765.4
    test_price = 118234.5
    
    print(f"テストデータ:")
    print(f"  Timestamp: {test_timestamp}")
    print(f"  Ask Total: {test_ask_total}")
    print(f"  Bid Total: {test_bid_total}")
    print(f"  Price: {test_price}")
    print()
    
    # 1時間足データの保存をテスト
    print("1時間足データを保存中...")
    sync_manager._save_hourly_data(test_timestamp, test_ask_total, test_bid_total, test_price)
    
    print("\n処理完了！")
    print("Supabaseの管理画面で order_book_1hour テーブルを確認してください。")

def check_existing_data():
    """既存の1時間足データを確認"""
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    config_path = os.path.join(appdata_dir, 'config.json')
    
    # CloudSyncManagerのインスタンス作成
    sync_manager = CloudSyncManager(config_path)
    
    if not sync_manager.enabled or not sync_manager.client:
        print("クラウド同期が無効になっています。")
        return
    
    try:
        # 1時間足テーブルからデータを取得
        result = sync_manager.client.table('order_book_1hour')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(10)\
            .execute()
        
        if result.data:
            print(f"\n最新の1時間足データ（{len(result.data)}件）:")
            for record in result.data:
                print(f"  {record['timestamp']}: Ask={record['ask_total']:.1f}, Bid={record['bid_total']:.1f}, Price={record['price']:.1f}")
        else:
            print("\n1時間足データはまだありません。")
    except Exception as e:
        print(f"\nデータ取得エラー: {e}")

if __name__ == "__main__":
    print("=== 1時間足データ保存機能のテスト ===\n")
    
    # 設定ファイルの確認
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    config_path = os.path.join(appdata_dir, 'config.json')
    
    if not os.path.exists(config_path):
        print(f"設定ファイルが見つかりません: {config_path}")
        print("CoinglassScraperを一度起動して設定ファイルを生成してください。")
        exit(1)
    
    # テストの実行
    test_hourly_data_save()
    
    # 既存データの確認
    print("\n=== 既存データの確認 ===")
    check_existing_data()