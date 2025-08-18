import os
import sqlite3
from datetime import datetime, timezone

# APPDATAパスの確認
appdata = os.environ.get('APPDATA')
db_dir = os.path.join(appdata, 'CoinglassScraper')
db_path = os.path.join(db_dir, 'btc_usdt_order_book.db')

print(f'Database path: {db_path}')

if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

# データベースに接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 全テーブルを取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'Found tables: {[t[0] for t in tables]}')

# 各テーブルのタイムスタンプを更新
for table_name, in tables:
    print(f'\nProcessing table: {table_name}')
    
    # 現在のデータを取得
    cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT 5")
    sample_rows = cursor.fetchall()
    
    if not sample_rows:
        print(f"  No data in {table_name}")
        continue
    
    print(f"  Sample timestamps before migration:")
    for row in sample_rows[:3]:
        print(f"    {row[0]}")
    
    # 変換が必要なレコード数をカウント
    cursor.execute(f"""
        SELECT COUNT(*) FROM {table_name}
        WHERE timestamp NOT LIKE '%+%' AND timestamp NOT LIKE '%Z'
    """)
    need_update_count = cursor.fetchone()[0]
    
    if need_update_count == 0:
        print(f"  All timestamps already have timezone info")
        continue
    
    print(f"  Found {need_update_count} records without timezone info")
    
    # 全レコードを取得して更新
    cursor.execute(f"SELECT timestamp FROM {table_name} WHERE timestamp NOT LIKE '%+%' AND timestamp NOT LIKE '%Z'")
    rows_to_update = cursor.fetchall()
    
    updated_count = 0
    for timestamp_str, in rows_to_update:
        try:
            # タイムスタンプをパース
            dt = datetime.fromisoformat(timestamp_str)
            
            # UTC情報を追加
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            # 新しいタイムスタンプ文字列
            new_timestamp_str = dt.isoformat()
            
            # データベースを更新
            cursor.execute(f"""
                UPDATE {table_name}
                SET timestamp = ?
                WHERE timestamp = ?
            """, (new_timestamp_str, timestamp_str))
            
            updated_count += 1
            
            if updated_count % 100 == 0:
                print(f"    Updated {updated_count}/{need_update_count} records...")
                
        except Exception as e:
            print(f"    Error updating timestamp '{timestamp_str}': {e}")
    
    # コミット
    conn.commit()
    print(f"  Updated {updated_count} records in {table_name}")
    
    # 更新後のサンプル確認
    cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT 5")
    sample_rows = cursor.fetchall()
    print(f"  Sample timestamps after migration:")
    for row in sample_rows[:3]:
        print(f"    {row[0]}")

print("\nMigration completed!")

# 接続を閉じる
conn.close()