import os
import shutil
from datetime import datetime

appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'Coinglass Scraper')
db_path = os.path.join(appdata_dir, 'btc_usdt_order_book.db')

if os.path.exists(db_path):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(appdata_dir, f'btc_usdt_order_book_backup_{timestamp}.db')
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # List all DB files
    print("\nAll DB files in directory:")
    for file in os.listdir(appdata_dir):
        if file.endswith('.db'):
            full_path = os.path.join(appdata_dir, file)
            size = os.path.getsize(full_path) / (1024 * 1024)  # MB
            print(f"  {file}: {size:.2f} MB")
else:
    print(f"Database file not found: {db_path}")
    print(f"Looking for DB files in current directory...")
    for file in os.listdir('.'):
        if file.endswith('.db'):
            print(f"  Found: {file}")