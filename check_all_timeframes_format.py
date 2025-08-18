#!/usr/bin/env python3
"""全時間足のタイムスタンプ形式を確認"""

import sqlite3
import os

# APPDATAフォルダのDBファイルパス
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")

print(f"データベースパス: {db_path}")

# データベース接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 各時間足のテーブル
timeframes = [
    'order_book_history',  # 1分足
    'order_book_5min',
    'order_book_15min',
    'order_book_30min',
    'order_book_1hour',
    'order_book_2hour',
    'order_book_4hour',
    'order_book_daily'
]

print("各時間足のタイムスタンプ形式:\n")
print("-" * 70)

for table in timeframes:
    try:
        # 最新3件のタイムスタンプを取得
        cursor.execute(f"""
            SELECT timestamp FROM {table}
            ORDER BY timestamp DESC
            LIMIT 3
        """)
        rows = cursor.fetchall()
        
        print(f"\n{table}:")
        for row in rows:
            timestamp = row[0]
            # 形式を分析
            if 'T' in timestamp:
                if timestamp.endswith(':00'):
                    if timestamp.count(':') == 3:  # HH:MM:SS形式
                        print(f"  {timestamp} → ISO形式（秒まで）")
                    elif timestamp.count(':') == 2:  # HH:MM形式
                        print(f"  {timestamp} → ISO形式（分まで）")
                else:
                    print(f"  {timestamp} → ISO形式")
            else:
                print(f"  {timestamp} → 不明な形式")
                
    except Exception as e:
        print(f"\n{table}: エラー - {e}")

# 5分足の秒が:00のデータと:00でないデータを比較
print("\n" + "=" * 70)
print("5分足の詳細確認:")
print("-" * 70)

# 秒が00のデータ
cursor.execute("""
    SELECT timestamp FROM order_book_5min 
    WHERE timestamp LIKE '%:00'
    ORDER BY timestamp DESC
    LIMIT 3
""")
print("\n秒が:00で終わるデータ:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 秒が00でないデータ
cursor.execute("""
    SELECT timestamp FROM order_book_5min 
    WHERE timestamp NOT LIKE '%:00'
    ORDER BY timestamp DESC
    LIMIT 3
""")
print("\n秒が:00で終わらないデータ:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()