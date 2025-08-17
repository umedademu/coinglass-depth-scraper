#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テストデータのクリーンアップスクリプト
8/17の13時台の異常な値（80000など）を周辺の値に置換
"""

import sqlite3
from datetime import datetime

def find_and_fix_test_data():
    """テストデータを検索して修正"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[8/17 13時台のデータを検索]")
    print("=" * 60)
    
    # 8/17の13時台のデータを取得
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
        ORDER BY timestamp
    """)
    
    data = cursor.fetchall()
    print(f"検索結果: {len(data)}件")
    
    # 異常な値（50000以上）を持つ行を特定
    abnormal_rows = []
    for row in data:
        if row[1] > 50000 or row[2] > 50000:  # ask_total > 50000 or bid_total > 50000
            abnormal_rows.append(row)
            print(f"\n異常値を検出: {row[0]}")
            print(f"  Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    
    if not abnormal_rows:
        print("\n異常な値は見つかりませんでした")
        conn.close()
        return
    
    print(f"\n異常な値を持つ行: {len(abnormal_rows)}件")
    
    # 各異常行について、前後の正常な値を取得して置換
    for abnormal_row in abnormal_rows:
        timestamp = abnormal_row[0]
        
        # 前後5分間の正常なデータを取得（50000未満のもの）
        cursor.execute("""
            SELECT ask_total, bid_total, price
            FROM order_book_history
            WHERE timestamp != ?
            AND timestamp BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
            AND ask_total < 50000 AND bid_total < 50000
            ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?))
            LIMIT 5
        """, (timestamp, timestamp, timestamp, timestamp))
        
        nearby_data = cursor.fetchall()
        
        if nearby_data:
            # 周辺データの平均値を計算
            avg_ask = sum(row[0] for row in nearby_data) / len(nearby_data)
            avg_bid = sum(row[1] for row in nearby_data) / len(nearby_data)
            avg_price = sum(row[2] for row in nearby_data) / len(nearby_data)
            
            print(f"\n{timestamp}を修正:")
            print(f"  修正前: Ask={abnormal_row[1]:.0f}, Bid={abnormal_row[2]:.0f}")
            print(f"  修正後: Ask={avg_ask:.0f}, Bid={avg_bid:.0f}")
            
            # データベースを更新
            cursor.execute("""
                UPDATE order_book_history
                SET ask_total = ?, bid_total = ?, price = ?
                WHERE timestamp = ?
            """, (avg_ask, avg_bid, avg_price, timestamp))
    
    conn.commit()
    print(f"\n{len(abnormal_rows)}件のデータを修正しました")
    
    # 修正後の確認
    print("\n[修正後の確認]")
    print("=" * 60)
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
        AND (ask_total > 20000 OR bid_total > 20000)
        ORDER BY timestamp
    """)
    
    remaining = cursor.fetchall()
    if remaining:
        print(f"まだ高い値が残っています: {len(remaining)}件")
        for row in remaining[:5]:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    else:
        print("すべての異常値が修正されました")
    
    conn.close()

def verify_data():
    """修正後のデータを確認"""
    conn = sqlite3.connect('btc_usdt_order_book.db')
    cursor = conn.cursor()
    
    print("\n[8/17 13時台のデータ（修正後）]")
    print("=" * 60)
    
    # 13:00-13:10のデータを表示
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp BETWEEN '2025-08-17T13:00:00' AND '2025-08-17T13:10:00'
        ORDER BY timestamp
    """)
    
    data = cursor.fetchall()
    for row in data[:10]:  # 最初の10件を表示
        print(f"{row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    
    # 統計情報
    cursor.execute("""
        SELECT 
            AVG(ask_total) as avg_ask,
            AVG(bid_total) as avg_bid,
            MAX(ask_total) as max_ask,
            MAX(bid_total) as max_bid,
            MIN(ask_total) as min_ask,
            MIN(bid_total) as min_bid
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
    """)
    
    stats = cursor.fetchone()
    print(f"\n[13時台の統計]")
    print(f"Ask平均: {stats[0]:.0f}, Bid平均: {stats[1]:.0f}")
    print(f"Ask最大: {stats[2]:.0f}, Bid最大: {stats[3]:.0f}")
    print(f"Ask最小: {stats[4]:.0f}, Bid最小: {stats[5]:.0f}")
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("テストデータのクリーンアップ")
    print("=" * 60)
    
    # テストデータの修正
    find_and_fix_test_data()
    
    # 修正後の確認
    verify_data()
    
    print("\n" + "=" * 60)
    print("クリーンアップ完了")
    print("=" * 60)