#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2025-08-17の13時台の3件の外れ値のみを修正
"""

import sqlite3
import os

def fix_specific_outliers():
    """2025-08-17 13時台の特定の外れ値を修正"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[2025-08-17 13時台の外れ値を修正]")
    print("=" * 60)
    
    # 修正対象のタイムスタンプ
    target_timestamps = [
        '2025-08-17T13:05:00',
        '2025-08-17T13:10:00', 
        '2025-08-17T13:15:00'
    ]
    
    for timestamp in target_timestamps:
        # 現在の値を取得
        cursor.execute("""
            SELECT ask_total, bid_total, price
            FROM order_book_history
            WHERE timestamp = ?
        """, (timestamp,))
        
        current = cursor.fetchone()
        if current:
            print(f"\n{timestamp}:")
            print(f"  現在の値: Ask={current[0]:.0f}, Bid={current[1]:.0f}")
            
            # 前後10分間の正常なデータ（ASK < 10000）を取得
            cursor.execute("""
                SELECT ask_total, bid_total, price
                FROM order_book_history
                WHERE timestamp != ?
                AND timestamp BETWEEN datetime(?, '-10 minutes') AND datetime(?, '+10 minutes')
                AND ask_total < 10000
                ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?))
                LIMIT 10
            """, (timestamp, timestamp, timestamp, timestamp))
            
            nearby_data = cursor.fetchall()
            
            if nearby_data:
                # 周辺データの平均値を計算
                avg_ask = sum(d[0] for d in nearby_data) / len(nearby_data)
                avg_bid = sum(d[1] for d in nearby_data) / len(nearby_data)
                avg_price = sum(d[2] for d in nearby_data) / len(nearby_data)
                
                print(f"  周辺{len(nearby_data)}件の平均: Ask={avg_ask:.0f}, Bid={avg_bid:.0f}")
                
                # データベースを更新
                cursor.execute("""
                    UPDATE order_book_history
                    SET ask_total = ?, bid_total = ?, price = ?
                    WHERE timestamp = ?
                """, (avg_ask, avg_bid, avg_price, timestamp))
                
                print(f"  修正完了: Ask={avg_ask:.0f}, Bid={avg_bid:.0f}")
            else:
                print(f"  周辺に正常なデータが見つかりませんでした")
        else:
            print(f"{timestamp} のデータが見つかりません")
    
    conn.commit()
    
    # 修正後の確認
    print("\n[修正後の確認]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T13:%'
        ORDER BY timestamp
        LIMIT 20
    """)
    
    data = cursor.fetchall()
    
    print("13時台のデータ（最初の20件）:")
    for row in data:
        flag = " ✓ 修正済" if row[0] in target_timestamps else ""
        print(f"  {row[0][11:16]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}{flag}")
    
    # 外れ値が残っていないか確認
    cursor.execute("""
        SELECT COUNT(*)
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17%' AND ask_total > 10000
    """)
    
    remaining = cursor.fetchone()[0]
    
    if remaining == 0:
        print("\n✅ 2025-08-17の外れ値はすべて修正されました")
    else:
        print(f"\n⚠️ まだ{remaining}件の外れ値が残っています")
    
    conn.close()
    print("\n処理完了！")

if __name__ == "__main__":
    fix_specific_outliers()