"""
時間足専用テーブルの作成確認スクリプト
第1段階の実装確認用
"""

import sqlite3
import os

# AppDataフォルダのパスを取得
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, 'btc_usdt_order_book.db')

print(f"\n=== 時間足専用テーブル作成確認 ===")
print(f"DBパス: {db_path}\n")

if not os.path.exists(db_path):
    print("DBファイルが見つかりません。アプリケーションを起動してください。")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# すべてのテーブルを取得
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name
""")

tables = cursor.fetchall()

print("【データベース内のテーブル一覧】")
print("-" * 50)

expected_tables = [
    'order_book_history',  # 既存の1分足テーブル
    'order_book_5min',
    'order_book_15min',
    'order_book_30min',
    'order_book_1hour',
    'order_book_2hour',
    'order_book_4hour',
    'order_book_daily'
]

found_tables = [table[0] for table in tables]

for expected in expected_tables:
    if expected in found_tables:
        print(f"[OK] {expected}")
    else:
        print(f"[NG] {expected} (見つかりません)")

# 各テーブルのスキーマを確認
print("\n【テーブルスキーマの確認】")
print("-" * 50)

for table_name in found_tables:
    if table_name.startswith('order_book'):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n{table_name}:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

# インデックスの確認
print("\n【インデックスの確認】")
print("-" * 50)

cursor.execute("""
    SELECT name, tbl_name FROM sqlite_master 
    WHERE type='index' AND name LIKE 'idx_%'
    ORDER BY tbl_name, name
""")

indexes = cursor.fetchall()
for idx_name, table_name in indexes:
    print(f"  {table_name}: {idx_name}")

# テーブル内のデータ件数を確認
print("\n【各テーブルのデータ件数】")
print("-" * 50)

for table_name in found_tables:
    if table_name.startswith('order_book'):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count}件")

conn.close()

print("\n" + "=" * 50)
print("確認完了！")
print("\n全8テーブルが存在すれば第1段階は成功です。")