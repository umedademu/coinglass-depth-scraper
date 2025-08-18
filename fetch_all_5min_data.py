#!/usr/bin/env python3
"""Supabaseから全5分足データを取得してローカルDBに保存する一時スクリプト"""

import sqlite3
import os
from supabase import create_client, Client
from datetime import datetime
import json

# Supabase設定
SUPABASE_URL = "https://rijqtostuemonbfcntck.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpanF0b3N0dWVtb25iZmNudGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM1MDE3MjEsImV4cCI6MjA2OTA3NzcyMX0.2Dui1ybcc-ZlP4N5nbsEFPJzOXnKPjUzB0adWD6eQ58"

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ローカルDB接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# order_book_5minテーブルが存在することを確認
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='order_book_5min'
""")
if not cursor.fetchone():
    print("エラー: order_book_5minテーブルが存在しません")
    conn.close()
    exit(1)

# 現在のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
local_count = cursor.fetchone()[0]
print(f"現在のローカルDB件数: {local_count}")

# Supabaseから全データを取得（バッチで処理）
batch_size = 1000
offset = 0
total_inserted = 0
total_updated = 0

print("Supabaseから全5分足データを取得中...")

while True:
    # バッチでデータ取得
    response = supabase.table('order_book_5min')\
        .select('*')\
        .order('timestamp', desc=False)\
        .limit(batch_size)\
        .offset(offset)\
        .execute()
    
    data = response.data
    
    if not data:
        break
    
    print(f"取得: {offset} - {offset + len(data)} 件")
    
    # データをローカルDBに保存
    for row in data:
        # UPSERT操作（既存データは更新、新規データは挿入）
        cursor.execute("""
            INSERT OR REPLACE INTO order_book_5min (
                timestamp, bid_0_5, bid_1, bid_2, bid_3, bid_5, bid_7, bid_10,
                ask_0_5, ask_1, ask_2, ask_3, ask_5, ask_7, ask_10,
                bid_total, ask_total, price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['timestamp'],
            row.get('bid_0_5', 0), row.get('bid_1', 0), row.get('bid_2', 0),
            row.get('bid_3', 0), row.get('bid_5', 0), row.get('bid_7', 0), row.get('bid_10', 0),
            row.get('ask_0_5', 0), row.get('ask_1', 0), row.get('ask_2', 0),
            row.get('ask_3', 0), row.get('ask_5', 0), row.get('ask_7', 0), row.get('ask_10', 0),
            row.get('bid_total', 0), row.get('ask_total', 0), row.get('price', 0)
        ))
    
    # コミット
    conn.commit()
    
    offset += batch_size
    
    # 次のバッチがない場合は終了
    if len(data) < batch_size:
        break

# 最終的なデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
final_count = cursor.fetchone()[0]
print(f"\n最終的なローカルDB件数: {final_count}")

# 最新のタイムスタンプを確認
cursor.execute("SELECT MAX(timestamp) FROM order_book_5min")
latest_timestamp = cursor.fetchone()[0]
print(f"最新タイムスタンプ: {latest_timestamp}")

# 最古のタイムスタンプを確認
cursor.execute("SELECT MIN(timestamp) FROM order_book_5min")
oldest_timestamp = cursor.fetchone()[0]
print(f"最古タイムスタンプ: {oldest_timestamp}")

conn.close()
print("\n完了: Supabaseから全5分足データを取得しました")