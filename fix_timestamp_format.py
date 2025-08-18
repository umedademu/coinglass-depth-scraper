#!/usr/bin/env python3
"""タイムスタンプ形式を修正するスクリプト"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 問題のあるタイムスタンプを確認
print("修正前の確認:")
cursor.execute("""
    SELECT COUNT(*) FROM order_book_5min 
    WHERE timestamp LIKE '%:00:00%'
""")
problematic_count = cursor.fetchone()[0]
print(f"問題のあるタイムスタンプ: {problematic_count}件")

if problematic_count > 0:
    # タイムスタンプを修正（最後の:00を削除）
    cursor.execute("""
        UPDATE order_book_5min 
        SET timestamp = SUBSTR(timestamp, 1, LENGTH(timestamp) - 3)
        WHERE timestamp LIKE '%:00:00%'
    """)
    
    conn.commit()
    print(f"{problematic_count}件のタイムスタンプを修正しました")

# 修正後の確認
print("\n修正後の確認:")
cursor.execute("""
    SELECT COUNT(*) FROM order_book_5min 
    WHERE timestamp LIKE '%:00:00%'
""")
remaining = cursor.fetchone()[0]
print(f"残っている問題のあるタイムスタンプ: {remaining}件")

# 最新10件のデータを確認
print("\n修正後の最新10件:")
cursor.execute("""
    SELECT timestamp, ask_total, bid_total, price 
    FROM order_book_5min 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]} | ask:{row[1]:8.0f} | bid:{row[2]:8.0f} | price:{row[3]:8.0f}")

conn.close()
print("\n完了: タイムスタンプ形式を修正しました")