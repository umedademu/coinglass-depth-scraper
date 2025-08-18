#!/usr/bin/env python3
"""残っている問題のあるタイムスタンプを確認"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 問題のあるタイムスタンプを詳しく確認
print("残っている問題のあるタイムスタンプのサンプル:")
cursor.execute("""
    SELECT timestamp FROM order_book_5min 
    WHERE timestamp LIKE '%:00:00%'
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 異なるパターンを確認
print("\n00:00で終わるタイムスタンプ:")
cursor.execute("""
    SELECT timestamp FROM order_book_5min 
    WHERE timestamp LIKE '%00:00'
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()