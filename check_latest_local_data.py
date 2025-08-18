import os
import sqlite3
from datetime import datetime

# APPDATAパスの確認
appdata = os.environ.get('APPDATA')
db_dir = os.path.join(appdata, 'CoinglassScraper')
db_path = os.path.join(db_dir, 'btc_usdt_order_book.db')

print(f'Database path: {db_path}')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 5分足の最新データを確認
    print("\n=== 5分足データ (order_book_5min) ===")
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_5min
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        # タイムスタンプにUTC情報が含まれているか確認
        ts_str = row[0]
        print(f"  {ts_str} | Ask: {row[1]:,.2f} | Bid: {row[2]:,.2f} | Price: {row[3]:,.0f}")
        
        # タイムゾーン情報の有無を確認
        if '+' in ts_str or 'Z' in ts_str:
            print(f"    -> UTC timezone info: YES")
        else:
            print(f"    -> UTC timezone info: NO")
    
    # 1分足の最新データも確認（比較用）
    print("\n=== 1分足データ (order_book_1min) ===")
    cursor.execute("""
        SELECT timestamp
        FROM order_book_1min
        ORDER BY timestamp DESC
        LIMIT 3
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        ts_str = row[0]
        print(f"  {ts_str}")
        if '+' in ts_str or 'Z' in ts_str:
            print(f"    -> UTC timezone info: YES")
        else:
            print(f"    -> UTC timezone info: NO")
    
    conn.close()
else:
    print("Database not found!")