#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テストデータ（異常に高い値）を検索
"""

import sqlite3

def find_abnormal_data():
    """異常に高い値を持つデータを検索"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[異常に高い値（50000以上）を検索]")
    print("=" * 60)
    
    # 50000以上の値を持つデータを検索
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_history
        WHERE ask_total > 50000 OR bid_total > 50000
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    
    data = cursor.fetchall()
    
    if data:
        print(f"異常値を持つレコード: {len(data)}件（最大20件表示）\n")
        for row in data:
            # タイムスタンプから日時を抽出
            ts = row[0]
            print(f"時刻: {ts}")
            print(f"  Ask: {row[1]:.0f}, Bid: {row[2]:.0f}, Price: {row[3]:.2f}")
            print()
    else:
        print("50000以上の値は見つかりませんでした")
    
    # 30000以上の値も検索
    print("\n[30000以上の値を検索]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE ask_total > 30000 OR bid_total > 30000
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    data = cursor.fetchall()
    
    if data:
        print(f"30000以上の値を持つレコード: {len(data)}件（最大10件表示）\n")
        for row in data:
            print(f"{row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("30000以上の値は見つかりませんでした")
    
    # 全体の統計情報
    print("\n[データベース全体の統計]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(ask_total) as avg_ask,
            AVG(bid_total) as avg_bid,
            MAX(ask_total) as max_ask,
            MAX(bid_total) as max_bid,
            MIN(timestamp) as oldest,
            MAX(timestamp) as newest
        FROM order_book_history
    """)
    
    stats = cursor.fetchone()
    print(f"総レコード数: {stats[0]}")
    print(f"Ask平均: {stats[1]:.0f}, Bid平均: {stats[2]:.0f}")
    print(f"Ask最大: {stats[3]:.0f}, Bid最大: {stats[4]:.0f}")
    print(f"最古データ: {stats[5]}")
    print(f"最新データ: {stats[6]}")
    
    conn.close()

if __name__ == "__main__":
    find_abnormal_data()