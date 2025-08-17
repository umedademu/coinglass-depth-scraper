#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
現在のデータベース状態を確認
"""

import sqlite3
import os
from datetime import datetime

def check_current_state():
    """現在のデータベース状態を確認"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[ASK値が10000を超えるデータの数]")
    print("=" * 60)
    
    # ASK値が10000を超えるデータを日付別に集計
    cursor.execute("""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as count,
            MAX(ask_total) as max_ask,
            MIN(ask_total) as min_ask
        FROM order_book_history
        WHERE ask_total > 10000
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 10
    """)
    
    data = cursor.fetchall()
    
    if data:
        print("日付別の10000超えASK値:")
        for row in data:
            print(f"  {row[0]}: {row[1]}件 (最大: {row[2]:.0f}, 最小: {row[3]:.0f})")
    else:
        print("ASK値が10000を超えるデータはありません")
    
    # 全体の統計
    cursor.execute("""
        SELECT 
            COUNT(*) as total_over_10k,
            AVG(ask_total) as avg_ask,
            MAX(ask_total) as max_ask
        FROM order_book_history
        WHERE ask_total > 10000
    """)
    
    stats = cursor.fetchone()
    
    if stats[0] and stats[0] > 0:
        print(f"\n全体で10000超え: {stats[0]}件")
        print(f"平均ASK値: {stats[1]:.0f}")
        print(f"最大ASK値: {stats[2]:.0f}")
    
    # 2025-08-17の12-13時台のデータを確認
    print("\n[2025-08-17の12-13時台のデータ]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp LIKE '2025-08-17T12:%' OR timestamp LIKE '2025-08-17T13:%'
        ORDER BY timestamp
        LIMIT 30
    """)
    
    data_12_13 = cursor.fetchall()
    
    if data_12_13:
        print(f"12-13時台のデータ: {len(data_12_13)}件（最初の30件）")
        for row in data_12_13[:15]:  # 最初の15件表示
            dt = datetime.fromisoformat(row[0])
            flag = " ⚠️ 要修正" if row[1] > 10000 else ""
            print(f"  {dt.strftime('%H:%M')} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}{flag}")
    
    conn.close()

if __name__ == "__main__":
    check_current_state()