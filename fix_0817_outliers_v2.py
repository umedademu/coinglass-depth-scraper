#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2025-08-17の13時台の外れ値を修正（範囲を広げて）
"""

import sqlite3
import os

def fix_outliers():
    """外れ値を修正"""
    
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[2025-08-17 13時台の外れ値を修正]")
    print("=" * 60)
    
    # 修正対象を確認
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%' AND ask_total > 10000
        ORDER BY timestamp
    """)
    
    outliers = cursor.fetchall()
    
    if not outliers:
        print("外れ値は見つかりませんでした（既に修正済みの可能性）")
        return
    
    print(f"修正対象: {len(outliers)}件\n")
    
    for row in outliers:
        timestamp = row[0]
        print(f"{timestamp}:")
        print(f"  現在: Ask={row[1]:.0f}, Bid={row[2]:.0f}")
        
        # 同じ13時台の正常なデータ（ASK < 10000）から平均を計算
        cursor.execute("""
            SELECT AVG(ask_total), AVG(bid_total), AVG(price)
            FROM order_book_history
            WHERE timestamp LIKE '2025-08-17T13:%'
            AND ask_total < 10000
            AND timestamp != ?
        """, (timestamp,))
        
        avg_data = cursor.fetchone()
        
        if avg_data and avg_data[0]:
            avg_ask = avg_data[0]
            avg_bid = avg_data[1]
            avg_price = avg_data[2]
            
            # データベースを更新
            cursor.execute("""
                UPDATE order_book_history
                SET ask_total = ?, bid_total = ?, price = ?
                WHERE timestamp = ?
            """, (avg_ask, avg_bid, avg_price, timestamp))
            
            print(f"  修正後: Ask={avg_ask:.0f}, Bid={avg_bid:.0f}")
        else:
            print("  修正用データが見つかりません")
    
    conn.commit()
    
    # 修正後の確認
    print("\n[修正後の13時台データ（一部）]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
        ORDER BY timestamp
        LIMIT 20
    """)
    
    data = cursor.fetchall()
    
    for row in data:
        time_str = row[0][11:16]  # HH:MM部分のみ
        print(f"  {time_str} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    
    # 残っている外れ値を確認
    cursor.execute("""
        SELECT COUNT(*)
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17%' AND ask_total > 10000
    """)
    
    remaining = cursor.fetchone()[0]
    
    print(f"\n2025-08-17の10000超えASK値: {remaining}件")
    
    conn.close()

if __name__ == "__main__":
    fix_outliers()