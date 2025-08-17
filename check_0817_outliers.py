#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2025-08-17の10000超えデータを詳細確認
"""

import sqlite3
import os

def check_0817_outliers():
    """2025-08-17の外れ値を詳細確認"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[2025-08-17のASK値10000超えデータ]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17%' AND ask_total > 10000
        ORDER BY timestamp
    """)
    
    outliers = cursor.fetchall()
    
    if outliers:
        print(f"見つかった外れ値: {len(outliers)}件\n")
        for row in outliers:
            print(f"時刻: {row[0]}")
            print(f"  Ask: {row[1]:.0f}, Bid: {row[2]:.0f}, Price: {row[3]:.2f}")
            
            # 前後のデータを確認
            cursor.execute("""
                SELECT timestamp, ask_total, bid_total
                FROM order_book_history
                WHERE timestamp != ? 
                AND timestamp BETWEEN datetime(?, '-2 minutes') AND datetime(?, '+2 minutes')
                ORDER BY timestamp
            """, (row[0], row[0], row[0]))
            
            nearby = cursor.fetchall()
            if nearby:
                print("  前後のデータ:")
                for n in nearby:
                    print(f"    {n[0]} - Ask: {n[1]:.0f}, Bid: {n[2]:.0f}")
            print()
    else:
        print("2025-08-17に10000を超えるASK値はありません")
    
    conn.close()

if __name__ == "__main__":
    check_0817_outliers()