import os
import sqlite3
from datetime import datetime

# APPDATAパスの確認
appdata = os.environ.get('APPDATA')
print(f'APPDATA: {appdata}')

db_dir = os.path.join(appdata, 'Coinglass Scraper')
print(f'DB Directory: {db_dir}')
print(f'Directory exists: {os.path.exists(db_dir)}')

if not os.path.exists(db_dir):
    print(f"Creating directory: {db_dir}")
    os.makedirs(db_dir, exist_ok=True)

db_path = os.path.join(db_dir, 'btc_usdt_order_book.db')
print(f'DB Path: {db_path}')
print(f'DB exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    # バックアップ作成
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(db_dir, f'btc_usdt_order_book_UTC_backup_{timestamp}.db')
    shutil.copy2(db_path, backup_path)
    print(f'\nBackup created: {backup_path}')
    
    # DBの中身を確認
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル一覧
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'\nTables: {[t[0] for t in tables]}')
    
    # 5分足データの最新10件を確認
    cursor.execute("SELECT timestamp FROM order_book_5min ORDER BY timestamp DESC LIMIT 10")
    rows = cursor.fetchall()
    print(f'\nLatest 5min timestamps:')
    for row in rows[:3]:
        print(f'  {row[0]}')
    
    conn.close()
else:
    print("\nDB file not found. The app may not have been run yet.")