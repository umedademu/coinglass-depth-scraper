"""
テストで更新した特定のタイムスタンプのデータを確認
"""

import sqlite3
import os

appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, 'btc_usdt_order_book.db')

print(f"\n=== 特定タイムスタンプの確認 ===")
print(f"DBパス: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テストで更新したタイムスタンプを確認
test_timestamps = [
    ('2025-08-17T13:45:00', '50,000 / 60,000'),
    ('2025-08-17T13:50:00', '88,888 / 99,999'),
]

print("【テストデータの状態】")
print("-" * 80)

for ts, expected in test_timestamps:
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total, price
        FROM order_book_history
        WHERE timestamp = ?
    """, (ts,))
    
    result = cursor.fetchone()
    if result:
        timestamp, ask, bid, price = result
        print(f"{timestamp}:")
        print(f"  実際の値: Ask={ask:,} / Bid={bid:,}")
        print(f"  期待値:   Ask={expected}")
        if ask >= 50000 or bid >= 60000:
            print(f"  [OK] 更新成功！")
        else:
            print(f"  [NG] 更新されていない")
    else:
        print(f"{ts}: データなし")
    print()

# 13:45～13:50の範囲のデータを全て表示
print("\n【13:45～13:50の全データ】")
print("-" * 80)
cursor.execute("""
    SELECT timestamp, ask_total, bid_total, price
    FROM order_book_history
    WHERE timestamp >= '2025-08-17T13:45:00' 
    AND timestamp <= '2025-08-17T13:50:00'
    ORDER BY timestamp
""")

for row in cursor.fetchall():
    timestamp, ask, bid, price = row
    marker = ""
    if ask >= 50000:
        marker = " <- BIG VALUE!"
    print(f"{timestamp}: Ask={ask:>8,.0f} / Bid={bid:>8,.0f}{marker}")

conn.close()