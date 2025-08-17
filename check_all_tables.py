"""
DBの全テーブルと最新データを確認
"""

import sqlite3
from datetime import datetime

import os
appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
db_path = os.path.join(appdata_dir, 'btc_usdt_order_book.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 全テーブルを取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"\n=== データベース内のテーブル一覧 ===")
for table in tables:
    table_name = table[0]
    print(f"\n【{table_name}】")
    
    # 各テーブルの最新5件を取得
    try:
        cursor.execute(f"""
            SELECT * FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        if rows:
            # カラム名を取得
            column_names = [description[0] for description in cursor.description]
            print(f"カラム: {', '.join(column_names)}")
            print("-" * 80)
            
            for row in rows:
                # timestampとask_total、bid_totalを中心に表示
                print(f"{row}")
                
            # 最新と最古のタイムスタンプを確認
            cursor.execute(f"""
                SELECT 
                    MIN(timestamp) as oldest,
                    MAX(timestamp) as newest,
                    COUNT(*) as count
                FROM {table_name}
            """)
            result = cursor.fetchone()
            print(f"\n最古: {result[0]}")
            print(f"最新: {result[1]}")
            print(f"件数: {result[2]}")
        else:
            print("データなし")
    except Exception as e:
        print(f"エラー: {e}")

conn.close()