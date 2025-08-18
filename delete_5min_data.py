#!/usr/bin/env python3
"""5分足データを削除するスクリプト"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 削除前のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
before_count = cursor.fetchone()[0]
print(f"削除前: order_book_5min に {before_count} 件のデータがあります")

if before_count > 0:
    # 最新のタイムスタンプを確認
    cursor.execute("SELECT MAX(timestamp) FROM order_book_5min")
    latest_timestamp = cursor.fetchone()[0]
    print(f"削除前の最新タイムスタンプ: {latest_timestamp}")

# データを削除
cursor.execute("DELETE FROM order_book_5min")
conn.commit()

# 削除後のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
after_count = cursor.fetchone()[0]
print(f"削除後: order_book_5min に {after_count} 件のデータがあります")

conn.close()
print("完了: order_book_5minテーブルのデータを削除しました")