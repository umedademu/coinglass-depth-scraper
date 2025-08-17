#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ASK値が10000を超える外れ値を修正
"""

import sqlite3
import os
from datetime import datetime

def fix_ask_outliers():
    """ASK値が10000を超える外れ値を修正"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[ASK値が10000を超える外れ値を検索]")
    print("=" * 60)
    
    # ASK値が10000を超えるデータを検索
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE ask_total > 10000
        ORDER BY timestamp
    """)
    
    outliers = cursor.fetchall()
    
    if outliers:
        print(f"ASK値が10000を超えるレコード: {len(outliers)}件\n")
        for row in outliers[:20]:  # 最初の20件表示
            dt = datetime.fromisoformat(row[0])
            print(f"{dt.strftime('%m/%d %H:%M')} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
        
        print(f"\n外れ値を修正しています...")
        
        fixed_count = 0
        for row in outliers:
            timestamp = row[0]
            
            # 前後20件の正常なデータ（ASK < 10000）を取得
            cursor.execute("""
                SELECT ask_total, bid_total, price
                FROM order_book_history
                WHERE timestamp != ?
                AND ask_total < 10000
                ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?))
                LIMIT 20
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
                
                fixed_count += 1
                
                if fixed_count <= 10:  # 最初の10件は詳細表示
                    print(f"  {timestamp}: Ask {row[1]:.0f} → {avg_ask:.0f}")
        
        conn.commit()
        print(f"\n{fixed_count}件のデータを修正しました")
    else:
        print("ASK値が10000を超える外れ値は見つかりませんでした")
    
    # 12-13時台のデータを確認
    print("\n[12-13時台のデータを確認（修正後）]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE 
            (timestamp LIKE '%-12:%' OR timestamp LIKE '%-13:%')
            AND timestamp LIKE '2025-08-17%'
        ORDER BY timestamp
        LIMIT 30
    """)
    
    data_12_13 = cursor.fetchall()
    
    if data_12_13:
        print(f"12-13時台のデータ:")
        for row in data_12_13:
            dt = datetime.fromisoformat(row[0])
            flag = " ⚠️" if row[1] > 10000 else ""
            print(f"{dt.strftime('%H:%M')} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}{flag}")
    
    # 修正後の統計
    print("\n[修正後の統計]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(ask_total) as avg_ask,
            AVG(bid_total) as avg_bid,
            MAX(ask_total) as max_ask,
            MAX(bid_total) as max_bid,
            COUNT(CASE WHEN ask_total > 10000 THEN 1 END) as outliers_remaining
        FROM order_book_history
    """)
    
    stats = cursor.fetchone()
    print(f"総レコード数: {stats[0]}")
    print(f"Ask平均: {stats[1]:.0f}, Bid平均: {stats[2]:.0f}")
    print(f"Ask最大: {stats[3]:.0f}, Bid最大: {stats[4]:.0f}")
    print(f"残っている外れ値（Ask > 10000）: {stats[5]}件")
    
    # ASK値の分布を確認
    print("\n[ASK値の分布]")
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN ask_total < 5000 THEN 1 END) as under_5k,
            COUNT(CASE WHEN ask_total >= 5000 AND ask_total < 7500 THEN 1 END) as '5k_to_7.5k',
            COUNT(CASE WHEN ask_total >= 7500 AND ask_total < 10000 THEN 1 END) as '7.5k_to_10k',
            COUNT(CASE WHEN ask_total >= 10000 THEN 1 END) as over_10k
        FROM order_book_history
    """)
    
    dist = cursor.fetchone()
    print(f"  < 5,000: {dist[0]}件")
    print(f"  5,000 - 7,500: {dist[1]}件")
    print(f"  7,500 - 10,000: {dist[2]}件")
    print(f"  > 10,000: {dist[3]}件")
    
    conn.close()
    print("\n修正完了！")

if __name__ == "__main__":
    fix_ask_outliers()