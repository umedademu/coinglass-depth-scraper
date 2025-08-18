#!/usr/bin/env python3
"""order_book_5minテーブルの構造を確認"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル構造を確認
cursor.execute("PRAGMA table_info(order_book_5min)")
columns = cursor.fetchall()

print("\norder_book_5minテーブルの構造:")
print("-" * 50)
for col in columns:
    print(f"{col[1]:20} {col[2]:10}")

conn.close()