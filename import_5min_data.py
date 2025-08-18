#!/usr/bin/env python3
"""Supabaseから取得した5分足データをローカルDBに保存"""

import sqlite3
import os
import json

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# ローカルDB接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 現在のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
before_count = cursor.fetchone()[0]
print(f"インポート前のローカルDB件数: {before_count}")

# JSONファイルからデータを読み込んで保存
json_file = 'supabase_data_batch1.json'

if os.path.exists(json_file):
    print(f"\n処理中: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    imported = 0
    for row in data:
        # タイムスタンプの処理（+00を削除してUTC形式に）
        timestamp = row['timestamp'].replace('+00', '').replace(' ', 'T')
        
        # UPSERT操作
        cursor.execute("""
            INSERT OR REPLACE INTO order_book_5min (
                timestamp, ask_total, bid_total, price
            ) VALUES (?, ?, ?, ?)
        """, (
            timestamp,
            float(row['ask_total']),
            float(row['bid_total']),
            float(row['price'])
        ))
        imported += 1
    
    conn.commit()
    print(f"  {imported}件をインポートしました")

# 最終的なデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
after_count = cursor.fetchone()[0]
print(f"\n最終的なローカルDB件数: {after_count}")
print(f"追加された件数: {after_count - before_count}")

# 最新のタイムスタンプを確認
cursor.execute("SELECT MAX(timestamp) FROM order_book_5min")
latest_timestamp = cursor.fetchone()[0]
print(f"最新タイムスタンプ: {latest_timestamp}")

# 最古のタイムスタンプを確認
cursor.execute("SELECT MIN(timestamp) FROM order_book_5min")
oldest_timestamp = cursor.fetchone()[0]
print(f"最古タイムスタンプ: {oldest_timestamp}")

conn.close()
print("\n完了: データをローカルDBにインポートしました")

# 残りのデータ取得が必要な件数を表示
total_in_supabase = 6672
print(f"\nSupabase上の総件数: {total_in_supabase}")
print(f"残り取得が必要な件数: {total_in_supabase - after_count}")