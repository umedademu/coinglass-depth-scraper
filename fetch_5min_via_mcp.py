#!/usr/bin/env python3
"""Supabase MCPツール経由で取得したデータをローカルDBに保存"""

import sqlite3
import os
import json
from datetime import datetime

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# JSONファイルからデータを読み込む関数
def load_data_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# ローカルDB接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 現在のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
before_count = cursor.fetchone()[0]
print(f"現在のローカルDB件数: {before_count}")

# データファイルのリスト（MCPツールで取得したデータを保存）
data_files = [
    'order_book_5min_batch1.json',
    'order_book_5min_batch2.json',
    'order_book_5min_batch3.json',
    'order_book_5min_batch4.json',
    'order_book_5min_batch5.json',
    'order_book_5min_batch6.json',
    'order_book_5min_batch7.json'
]

total_inserted = 0

for data_file in data_files:
    if os.path.exists(data_file):
        print(f"\n処理中: {data_file}")
        data = load_data_from_json(data_file)
        
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
            total_inserted += 1
        
        conn.commit()
        print(f"  {len(data)}件を処理しました")

# 最終的なデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
after_count = cursor.fetchone()[0]
print(f"\n最終的なローカルDB件数: {after_count}")
print(f"追加/更新された件数: {after_count - before_count}")

# 最新のタイムスタンプを確認
cursor.execute("SELECT MAX(timestamp) FROM order_book_5min")
latest_timestamp = cursor.fetchone()[0]
print(f"最新タイムスタンプ: {latest_timestamp}")

# 最古のタイムスタンプを確認
cursor.execute("SELECT MIN(timestamp) FROM order_book_5min")
oldest_timestamp = cursor.fetchone()[0]
print(f"最古タイムスタンプ: {oldest_timestamp}")

conn.close()
print("\n完了: データをローカルDBに保存しました")