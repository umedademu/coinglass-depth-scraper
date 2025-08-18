import sqlite3

# データベースに接続
conn = sqlite3.connect(r'C:\Users\USER\AppData\Roaming\CoinglassScraper\btc_usdt_order_book.db')
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=== ローカルDB内のテーブル一覧 ===")
for table in tables:
    table_name = table[0]
    # 各テーブルのレコード数も確認
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"- {table_name}: {count}件")

# 1分足テーブルが存在するか確認
if 'order_book_1min' in [t[0] for t in tables]:
    print("\n✓ order_book_1min テーブルが存在します")
else:
    print("\n✗ order_book_1min テーブルは存在しません")

conn.close()