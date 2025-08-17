#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AppDataフォルダ内のテストデータ（異常に高い値）を修正
"""

import sqlite3
import os
from datetime import datetime

def fix_test_data():
    """AppDataのデータベース内のテストデータを修正"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[異常に高い値を検索（50000以上）]")
    print("=" * 60)
    
    # 50000以上の値を検索
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE ask_total > 50000 OR bid_total > 50000
        ORDER BY timestamp
    """)
    
    abnormal_data = cursor.fetchall()
    
    if abnormal_data:
        print(f"異常値を持つレコード: {len(abnormal_data)}件\n")
        for row in abnormal_data[:10]:  # 最初の10件表示
            print(f"{row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
        
        print(f"\n異常値を修正しています...")
        
        # 各異常データを修正
        for row in abnormal_data:
            timestamp = row[0]
            
            # 前後10件の正常なデータを取得
            cursor.execute("""
                SELECT ask_total, bid_total, price
                FROM order_book_history
                WHERE timestamp != ?
                AND ask_total < 30000 AND bid_total < 30000
                ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?))
                LIMIT 10
            """, (timestamp, timestamp))
            
            nearby_data = cursor.fetchall()
            
            if nearby_data:
                # 周辺データの平均値を計算
                avg_ask = sum(d[0] for d in nearby_data) / len(nearby_data)
                avg_bid = sum(d[1] for d in nearby_data) / len(nearby_data)
                avg_price = sum(d[2] for d in nearby_data) / len(nearby_data)
                
                # データベースを更新
                cursor.execute("""
                    UPDATE order_book_history
                    SET ask_total = ?, bid_total = ?, price = ?
                    WHERE timestamp = ?
                """, (avg_ask, avg_bid, avg_price, timestamp))
        
        conn.commit()
        print(f"{len(abnormal_data)}件のデータを修正しました")
    else:
        print("50000以上の異常値は見つかりませんでした")
    
    # 8/17の13時台のデータも確認
    print("\n[8/17 13時台のデータを確認]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
        ORDER BY timestamp
        LIMIT 20
    """)
    
    data_13 = cursor.fetchall()
    
    if data_13:
        print(f"8/17 13時台のデータ: {len(data_13)}件")
        for row in data_13[:10]:
            print(f"{row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("8/17 13時台のデータは見つかりませんでした")
    
    # 修正後の統計
    print("\n[修正後の統計]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(ask_total) as avg_ask,
            AVG(bid_total) as avg_bid,
            MAX(ask_total) as max_ask,
            MAX(bid_total) as max_bid
        FROM order_book_history
    """)
    
    stats = cursor.fetchone()
    print(f"総レコード数: {stats[0]}")
    print(f"Ask平均: {stats[1]:.0f}, Bid平均: {stats[2]:.0f}")
    print(f"Ask最大: {stats[3]:.0f}, Bid最大: {stats[4]:.0f}")
    
    # 最新のデータを確認
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    latest_data = cursor.fetchall()
    
    print("\n[最新10件のデータ]")
    for row in latest_data:
        print(f"{row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    
    conn.close()
    print("\n修正完了！")

if __name__ == "__main__":
    fix_test_data()