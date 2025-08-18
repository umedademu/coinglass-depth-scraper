#!/usr/bin/env python3
"""5分足データの検証スクリプト"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# データ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
count = cursor.fetchone()[0]
print(f"\norder_book_5minテーブルのデータ件数: {count}")

# 最新10件のデータを確認
print("\n最新10件のデータ:")
cursor.execute("""
    SELECT timestamp, ask_total, bid_total, price 
    FROM order_book_5min 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]} | ask:{row[1]:8.0f} | bid:{row[2]:8.0f} | price:{row[3]:8.0f}")

# 最古10件のデータを確認
print("\n最古10件のデータ:")
cursor.execute("""
    SELECT timestamp, ask_total, bid_total, price 
    FROM order_book_5min 
    ORDER BY timestamp ASC 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]} | ask:{row[1]:8.0f} | bid:{row[2]:8.0f} | price:{row[3]:8.0f}")

# タイムスタンプフォーマットに問題がないか確認
print("\nタイムスタンプ形式の確認:")
cursor.execute("""
    SELECT timestamp FROM order_book_5min 
    WHERE timestamp LIKE '%:00:00%' 
    LIMIT 5
""")
problematic = cursor.fetchall()
if problematic:
    print(f"問題のあるタイムスタンプが見つかりました: {len(problematic)}件")
    for row in problematic[:5]:
        print(f"  {row[0]}")
else:
    print("タイムスタンプ形式に問題はありません")

conn.close()