#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特定の値（60000, 80000など）を検索
"""

import sqlite3

def search_specific_values():
    """特定の値を検索"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[特定の値を検索]")
    print("=" * 60)
    
    # 60000付近の値を検索
    print("\n60000付近（59000-61000）の値を検索:")
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE (ask_total BETWEEN 59000 AND 61000) OR (bid_total BETWEEN 59000 AND 61000)
        ORDER BY timestamp DESC
    """)
    
    data = cursor.fetchall()
    if data:
        print(f"見つかりました: {len(data)}件")
        for row in data[:5]:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("見つかりませんでした")
    
    # 80000付近の値を検索
    print("\n80000付近（79000-81000）の値を検索:")
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE (ask_total BETWEEN 79000 AND 81000) OR (bid_total BETWEEN 79000 AND 81000)
        ORDER BY timestamp DESC
    """)
    
    data = cursor.fetchall()
    if data:
        print(f"見つかりました: {len(data)}件")
        for row in data[:5]:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("見つかりませんでした")
    
    # 50000付近の値を検索
    print("\n50000付近（49000-51000）の値を検索:")
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE (ask_total BETWEEN 49000 AND 51000) OR (bid_total BETWEEN 49000 AND 51000)
        ORDER BY timestamp DESC
    """)
    
    data = cursor.fetchall()
    if data:
        print(f"見つかりました: {len(data)}件")
        for row in data[:5]:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("見つかりませんでした")
    
    # 今日のデータがあるか確認（2025-08-17）
    print("\n2025-08-17のデータを検索:")
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17%'
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    data = cursor.fetchall()
    if data:
        print(f"見つかりました: {len(data)}件")
        for row in data:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("2025-08-17のデータは見つかりませんでした")
    
    # 最新の100件から異常値を探す
    print("\n最新100件のデータから平均の3倍以上の値を検索:")
    cursor.execute("""
        WITH recent_avg AS (
            SELECT AVG(ask_total) as avg_ask, AVG(bid_total) as avg_bid
            FROM (
                SELECT ask_total, bid_total
                FROM order_book_history
                ORDER BY timestamp DESC
                LIMIT 100
            )
        )
        SELECT h.timestamp, h.ask_total, h.bid_total, a.avg_ask, a.avg_bid
        FROM order_book_history h, recent_avg a
        WHERE h.ask_total > a.avg_ask * 3 OR h.bid_total > a.avg_bid * 3
        ORDER BY h.timestamp DESC
        LIMIT 10
    """)
    
    data = cursor.fetchall()
    if data:
        print(f"異常値の可能性があるデータ: {len(data)}件")
        for row in data:
            print(f"  {row[0]}")
            print(f"    Ask: {row[1]:.0f} (平均: {row[3]:.0f})")
            print(f"    Bid: {row[2]:.0f} (平均: {row[4]:.0f})")
    else:
        print("異常値は見つかりませんでした")
    
    conn.close()

if __name__ == "__main__":
    search_specific_values()