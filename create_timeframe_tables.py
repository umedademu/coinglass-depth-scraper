"""
時間足専用テーブルを手動で作成するスクリプト
アプリケーションを再起動せずにテーブルを作成できます
"""

import sqlite3
import os
from datetime import datetime

# AppDataフォルダのパスを取得
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, 'btc_usdt_order_book.db')

print(f"\n=== 時間足専用テーブルの作成 ===")
print(f"DBパス: {db_path}\n")

if not os.path.exists(db_path):
    print("DBファイルが見つかりません。")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 時間足専用テーブルの作成
timeframe_tables = [
    ('order_book_5min', '5分足'),
    ('order_book_15min', '15分足'),
    ('order_book_30min', '30分足'),
    ('order_book_1hour', '1時間足'),
    ('order_book_2hour', '2時間足'),
    ('order_book_4hour', '4時間足'),
    ('order_book_daily', '日足')
]

print("テーブル作成を開始します...\n")

for table_name, timeframe_name in timeframe_tables:
    try:
        # テーブル作成
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TEXT PRIMARY KEY,
                ask_total REAL NOT NULL,
                bid_total REAL NOT NULL,
                price REAL NOT NULL
            )
        """)
        
        # インデックス作成
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp 
            ON {table_name}(timestamp)
        """)
        
        print(f"[OK] 時間足専用テーブルを作成しました: {table_name} ({timeframe_name})")
        
    except Exception as e:
        print(f"[ERROR] {table_name}の作成に失敗: {e}")

# コミット
conn.commit()

print("\n作成結果を確認中...\n")

# 作成されたテーブルを確認
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE 'order_book%'
    ORDER BY name
""")

tables = cursor.fetchall()

print("【作成されたテーブル】")
print("-" * 50)
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  {table[0]}: {count}件")

conn.close()

print("\n" + "=" * 50)
print("テーブル作成完了！")
print("\n注意: アプリケーションを次回起動すると、")
print("自動的にこれらのテーブルが認識されます。")