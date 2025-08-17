"""
ローカルDBの実際の値を確認するスクリプト
"""

import sqlite3
import os
from datetime import datetime, timedelta

# DBファイルのパスを設定（カレントディレクトリ）
db_path = 'btc_usdt_order_book.db'

print(f"\n=== ローカルDBの確認 ===")
print(f"DBパス: {db_path}\n")

if not os.path.exists(db_path):
    print("DBファイルが見つかりません")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 最新20件のデータを取得
print("【最新20件のデータ】")
print("-" * 80)
print(f"{'タイムスタンプ':<25} {'Ask':>10} {'Bid':>10} {'Price':>10}")
print("-" * 80)

cursor.execute("""
    SELECT timestamp, ask_total, bid_total, price
    FROM order_book_history
    ORDER BY timestamp DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    timestamp, ask, bid, price = row
    print(f"{timestamp:<25} {ask:>10,} {bid:>10,} {price:>10,}")

# 特定のタイムスタンプのデータを確認
print("\n【テストデータの確認】")
print("-" * 80)
test_timestamps = [
    '2025-08-17T13:45:00',
    '2025-08-17T13:50:00',
    '2025-08-17T13:40:00',
    '2025-08-17T13:35:00'
]

for ts in test_timestamps:
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_history
        WHERE timestamp = ?
    """, (ts,))
    
    result = cursor.fetchone()
    if result:
        timestamp, ask, bid, price = result
        expected = ""
        if '13:45' in ts:
            expected = " <- 50,000 / 60,000 になるはず"
        elif '13:50' in ts:
            expected = " <- 88,888 / 99,999 になるはず"
        print(f"{timestamp}: Ask={ask:,} / Bid={bid:,}{expected}")
    else:
        print(f"{ts}: データなし")

# 最大値と最小値を確認
print("\n【Ask/Bidの範囲】")
print("-" * 80)
cursor.execute("""
    SELECT 
        MIN(ask_total) as min_ask,
        MAX(ask_total) as max_ask,
        MIN(bid_total) as min_bid,
        MAX(bid_total) as max_bid
    FROM order_book_history
    WHERE timestamp >= datetime('now', '-1 hour')
""")

result = cursor.fetchone()
if result:
    min_ask, max_ask, min_bid, max_bid = result
    print(f"過去1時間のAsk: {min_ask:,} ～ {max_ask:,}")
    print(f"過去1時間のBid: {min_bid:,} ～ {max_bid:,}")

conn.close()
print("\n" + "=" * 80)