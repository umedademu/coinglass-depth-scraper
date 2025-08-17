#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第3段階：Supabaseデータとの比較・更新のテスト
"""

import sqlite3
import os
from datetime import datetime, timedelta

def check_timeframe_tables():
    """時間足テーブルのデータを確認"""
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("第3段階テスト：Supabaseデータとの比較・更新")
    print("=" * 60)
    
    # 各時間足テーブルの状態を確認
    tables = [
        ('order_book_5min', '5分足'),
        ('order_book_15min', '15分足'),
        ('order_book_30min', '30分足'),
        ('order_book_1hour', '1時間足'),
        ('order_book_2hour', '2時間足'),
        ('order_book_4hour', '4時間足'),
        ('order_book_daily', '日足')
    ]
    
    print("\n[時間足テーブルの状態]")
    print("-" * 60)
    
    for table_name, timeframe_name in tables:
        # テーブルが存在するか確認
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if not cursor.fetchone():
            print(f"\n{timeframe_name} ({table_name}): テーブルが存在しません")
            continue
        
        # レコード数を取得
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # 最新データを取得
        cursor.execute(f"""
            SELECT timestamp, ask_total, bid_total, price
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        latest_data = cursor.fetchall()
        
        print(f"\n{timeframe_name} ({table_name}):")
        print(f"  レコード数: {count}")
        
        if latest_data:
            print(f"  最新データ（上位5件）:")
            for row in latest_data:
                dt = datetime.fromisoformat(row[0])
                print(f"    {dt.strftime('%Y-%m-%d %H:%M')} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}, Price: ${row[3]:.2f}")
        else:
            print(f"  データなし")
    
    # 最大値の確認
    print("\n[各テーブルの最大値]")
    print("-" * 60)
    
    for table_name, timeframe_name in tables:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if not cursor.fetchone():
            continue
        
        cursor.execute(f"""
            SELECT MAX(ask_total), MAX(bid_total)
            FROM {table_name}
        """)
        
        max_values = cursor.fetchone()
        if max_values and max_values[0]:
            print(f"{timeframe_name}: Ask最大={max_values[0]:.0f}, Bid最大={max_values[1]:.0f}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("確認ポイント:")
    print("=" * 60)
    print("1. アプリケーション起動時のログを確認:")
    print("   - '[初期データ取得] 5分足: xxx件取得' が表示される")
    print("   - '[ローカルDB] 5分足: 新規xxx件、更新xxx件' が表示される")
    print("")
    print("2. 各時間足テーブルにデータが保存されている")
    print("")
    print("3. Supabaseでテストデータを更新した後:")
    print("   - 大きい値が採用されているか確認")
    print("   - 最大値比較が正しく機能しているか確認")
    print("")
    print("4. 1分足DB（order_book_history）に5分足以上のデータが")
    print("   混入していないことを確認")

def test_max_value_logic():
    """最大値比較ロジックのテスト"""
    print("\n" + "=" * 60)
    print("最大値比較ロジックのテスト")
    print("=" * 60)
    
    # テストケース
    test_cases = [
        {
            "name": "新規データ",
            "existing": None,
            "new": {"ask": 10000, "bid": 15000},
            "expected": {"ask": 10000, "bid": 15000, "action": "INSERT"}
        },
        {
            "name": "既存データより大きい",
            "existing": {"ask": 8000, "bid": 12000},
            "new": {"ask": 10000, "bid": 15000},
            "expected": {"ask": 10000, "bid": 15000, "action": "UPDATE"}
        },
        {
            "name": "既存データより小さい",
            "existing": {"ask": 10000, "bid": 15000},
            "new": {"ask": 8000, "bid": 12000},
            "expected": {"ask": 10000, "bid": 15000, "action": "NO_UPDATE"}
        },
        {
            "name": "一部だけ大きい",
            "existing": {"ask": 9000, "bid": 15000},
            "new": {"ask": 10000, "bid": 14000},
            "expected": {"ask": 10000, "bid": 15000, "action": "UPDATE"}
        }
    ]
    
    for test in test_cases:
        print(f"\nテスト: {test['name']}")
        print(f"  既存: {test['existing']}")
        print(f"  新規: {test['new']}")
        
        if test['existing'] is None:
            # 新規挿入
            result = test['new']
            action = "INSERT"
        else:
            # 最大値比較
            result = {
                "ask": max(test['new']['ask'], test['existing']['ask']),
                "bid": max(test['new']['bid'], test['existing']['bid'])
            }
            
            if result['ask'] > test['existing']['ask'] or result['bid'] > test['existing']['bid']:
                action = "UPDATE"
            else:
                action = "NO_UPDATE"
        
        print(f"  結果: Ask={result['ask']}, Bid={result['bid']}, Action={action}")
        
        # 期待値との比較
        if result['ask'] == test['expected']['ask'] and \
           result['bid'] == test['expected']['bid'] and \
           action == test['expected']['action']:
            print(f"  判定: ✓ OK")
        else:
            print(f"  判定: ✗ NG")
            print(f"  期待: {test['expected']}")

if __name__ == "__main__":
    # 時間足テーブルの確認
    check_timeframe_tables()
    
    # 最大値比較ロジックのテスト
    test_max_value_logic()