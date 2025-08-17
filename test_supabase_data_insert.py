#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第3段階テスト用：Supabaseにテストデータを挿入
最大値比較機能をテストするため、大きな値のデータを挿入
"""

from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

def insert_test_data():
    """テストデータをSupabaseに挿入"""
    
    # 環境変数を読み込み
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("環境変数が設定されていません")
        return
    
    # Supabaseクライアントを作成
    supabase = create_client(supabase_url, supabase_key)
    
    print("\n" + "=" * 60)
    print("第3段階テストデータ挿入")
    print("=" * 60)
    
    # テストデータの定義（通常より大きな値）
    test_records = [
        {
            'timestamp': '2025-08-17T16:05:00',  # 既存のデータを更新
            'ask_total': 99999,  # 大きなテスト値
            'bid_total': 88888,  # 大きなテスト値
            'price': 117850,
            'group_id': 'default-group'
        },
        {
            'timestamp': '2025-08-17T16:10:00',  # 新規データ
            'ask_total': 77777,
            'bid_total': 66666,
            'price': 117900,
            'group_id': 'default-group'
        }
    ]
    
    # 5分足テーブル（order_book_shared）に挿入
    print("\n[5分足テーブルへのテストデータ挿入]")
    for record in test_records:
        try:
            # upsertを使用（存在する場合は更新、なければ挿入）
            result = supabase.table('order_book_shared').upsert(
                record,
                on_conflict='timestamp,group_id'
            ).execute()
            
            print(f"✓ {record['timestamp']}: Ask={record['ask_total']}, Bid={record['bid_total']}")
            
        except Exception as e:
            print(f"✗ エラー: {e}")
    
    # 他の時間足にもテストデータを挿入
    other_tables = ['order_book_15min', 'order_book_30min', 'order_book_1hour']
    
    for table_name in other_tables:
        print(f"\n[{table_name}へのテストデータ挿入]")
        
        test_record = {
            'timestamp': '2025-08-17T16:00:00',
            'ask_total': 55555,
            'bid_total': 44444,
            'price': 117900,
            'group_id': 'default-group'
        }
        
        try:
            result = supabase.table(table_name).upsert(
                test_record,
                on_conflict='timestamp,group_id'
            ).execute()
            
            print(f"✓ {test_record['timestamp']}: Ask={test_record['ask_total']}, Bid={test_record['bid_total']}")
            
        except Exception as e:
            print(f"✗ エラー: {e}")
    
    print("\n" + "=" * 60)
    print("テストデータ挿入完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. アプリケーションを起動（または再起動）")
    print("2. 起動時のログを確認")
    print("3. test_stage3_max_comparison.pyを実行してデータを確認")

if __name__ == "__main__":
    insert_test_data()