#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第2段階：データ保存先の振り分けテスト
時間足に応じたテーブルへの保存が正しく動作するかを確認
"""

import sqlite3
from datetime import datetime, timedelta

def check_database_state():
    """データベースの現在の状態を確認"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[データベース状態確認]")
    print("=" * 60)
    
    # 各テーブルのレコード数を確認
    tables = [
        'order_book_history',   # 1分足
        'order_book_5min',      # 5分足
        'order_book_15min',     # 15分足
        'order_book_30min',     # 30分足
        'order_book_1hour',     # 1時間足
        'order_book_2hour',     # 2時間足
        'order_book_4hour',     # 4時間足
        'order_book_daily'      # 日足
    ]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # 最新データの取得
        cursor.execute(f"""
            SELECT timestamp, ask_total, bid_total 
            FROM {table} 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        latest = cursor.fetchone()
        
        print(f"\n[{table}]")
        print(f"  レコード数: {count}")
        if latest:
            print(f"  最新データ: {latest[0]}")
            print(f"  Ask: {latest[1]:.0f}, Bid: {latest[2]:.0f}")
        else:
            print(f"  データなし")
    
    conn.close()

def test_routing_logic():
    """時間足判定ロジックのテスト"""
    print("\n[時間足判定ロジックテスト]")
    print("=" * 60)
    
    # テスト用のタイムスタンプ
    test_cases = [
        ("2025-01-17 13:01:00", ["order_book_history"]),
        ("2025-01-17 13:05:00", ["order_book_history", "order_book_5min"]),
        ("2025-01-17 13:15:00", ["order_book_history", "order_book_5min", "order_book_15min"]),
        ("2025-01-17 13:30:00", ["order_book_history", "order_book_5min", "order_book_15min", "order_book_30min"]),
        ("2025-01-17 14:00:00", ["order_book_history", "order_book_5min", "order_book_15min", "order_book_30min", "order_book_1hour"]),
        ("2025-01-17 16:00:00", ["order_book_history", "order_book_5min", "order_book_15min", "order_book_30min", "order_book_1hour", "order_book_2hour", "order_book_4hour"]),
        ("2025-01-18 00:00:00", ["order_book_history", "order_book_5min", "order_book_15min", "order_book_30min", "order_book_1hour", "order_book_2hour", "order_book_4hour", "order_book_daily"]),
    ]
    
    for timestamp_str, expected_tables in test_cases:
        dt = datetime.fromisoformat(timestamp_str)
        actual_tables = ["order_book_history"]  # 1分足は常に保存
        
        # 実際の判定ロジック（coinglass_scraper.pyのロジックを再現）
        if dt.minute % 5 == 0:
            actual_tables.append("order_book_5min")
        if dt.minute % 15 == 0:
            actual_tables.append("order_book_15min")
        if dt.minute % 30 == 0:
            actual_tables.append("order_book_30min")
        if dt.minute == 0:
            actual_tables.append("order_book_1hour")
            if dt.hour % 2 == 0:
                actual_tables.append("order_book_2hour")
            if dt.hour % 4 == 0:
                actual_tables.append("order_book_4hour")
            if dt.hour == 0:
                actual_tables.append("order_book_daily")
        
        # 結果の比較
        success = set(actual_tables) == set(expected_tables)
        status = "[OK]" if success else "[NG]"
        
        print(f"\n{status} {timestamp_str}")
        print(f"  期待値: {', '.join(expected_tables)}")
        print(f"  実際値: {', '.join(actual_tables)}")
        
        if not success:
            print(f"  エラー: テーブルリストが一致しません")

def check_recent_data():
    """最近のデータ保存状況を確認"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[最近のデータ保存状況（過去1時間）]")
    print("=" * 60)
    
    # 現在時刻から1時間前までのデータを確認
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # 5分足データの確認
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_5min
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    """, (one_hour_ago.isoformat(),))
    
    five_min_data = cursor.fetchall()
    
    if five_min_data:
        print(f"\n[5分足データ] {len(five_min_data)}件")
        for row in five_min_data[:5]:  # 最新5件表示
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("\n[5分足データ] なし")
    
    # 15分足データの確認
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_15min
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    """, (one_hour_ago.isoformat(),))
    
    fifteen_min_data = cursor.fetchall()
    
    if fifteen_min_data:
        print(f"\n[15分足データ] {len(fifteen_min_data)}件")
        for row in fifteen_min_data[:3]:  # 最新3件表示
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("\n[15分足データ] なし")
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("第2段階テスト：データ保存先の振り分け")
    print("=" * 60)
    
    # データベース状態確認
    check_database_state()
    
    # 時間足判定ロジックのテスト
    test_routing_logic()
    
    # 最近のデータ保存状況確認
    check_recent_data()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    print("\n[確認ポイント]")
    print("1. アプリケーションを5分以上実行してください")
    print("2. 5分経過後、order_book_5minテーブルにデータが保存されているか確認")
    print("3. 15分経過後、order_book_15minテーブルにデータが保存されているか確認")
    print("4. 時間足判定ロジックが正しく動作しているか確認")