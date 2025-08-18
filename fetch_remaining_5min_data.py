#!/usr/bin/env python3
"""Supabaseから残りの5分足データを取得してローカルDBに保存する一時スクリプト"""

import sqlite3
import os
from supabase import create_client, Client

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

# 現在のデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
local_count = cursor.fetchone()[0]
print(f"現在のローカルDB件数: {local_count}")

# Supabaseから残りのデータを取得（既に500件取得済みなので、500から開始）
batch_size = 500
offset = 500  # 既に500件取得済み
total_inserted = 0

print(f"Supabaseから残りの5分足データを取得中（offset={offset}から）...")

while offset < 6672:  # 総件数は6672件
    # バッチでデータ取得
    print(f"取得中: {offset} - {offset + batch_size} 件")
    
    try:
        response = supabase.table('order_book_5min')\
            .select('*')\
            .order('timestamp', desc=False)\
            .limit(batch_size)\
            .offset(offset)\
            .execute()
        
        data = response.data
        
        if not data:
            print("これ以上データがありません")
            break
        
        # データをローカルDBに保存
        for row in data:
            # タイムスタンプの処理
            timestamp = row['timestamp'].replace('+00', '').replace(' ', 'T')
            
            # UPSERT操作
            cursor.execute("""
                INSERT OR REPLACE INTO order_book_5min (
                    timestamp, ask_total, bid_total, price
                ) VALUES (?, ?, ?, ?)
            """, (
                timestamp,
                float(row.get('ask_total', 0)),
                float(row.get('bid_total', 0)),
                float(row.get('price', 0))
            ))
            total_inserted += 1
        
        # コミット
        conn.commit()
        print(f"  {len(data)}件を保存しました（累計: {total_inserted + 500}件）")
        
        offset += batch_size
        
        # 次のバッチがない場合は終了
        if len(data) < batch_size:
            break
            
    except Exception as e:
        print(f"エラー発生: {e}")
        break

# 最終的なデータ件数を確認
cursor.execute("SELECT COUNT(*) FROM order_book_5min")
final_count = cursor.fetchone()[0]
print(f"\n最終的なローカルDB件数: {final_count}")
print(f"新規追加された件数: {final_count - local_count}")

# 最新のタイムスタンプを確認
cursor.execute("SELECT MAX(timestamp) FROM order_book_5min")
latest_timestamp = cursor.fetchone()[0]
print(f"最新タイムスタンプ: {latest_timestamp}")

# 最古のタイムスタンプを確認
cursor.execute("SELECT MIN(timestamp) FROM order_book_5min")
oldest_timestamp = cursor.fetchone()[0]
print(f"最古タイムスタンプ: {oldest_timestamp}")

conn.close()
print("\n完了: Supabaseから5分足データを取得しました")