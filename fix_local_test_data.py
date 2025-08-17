#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ローカルDBのテストデータを正常な値に戻す
"""

import sqlite3
import os

def fix_local_data():
    """ローカルDBのテストデータを修正"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[異常な値を検索]")
    print("=" * 60)
    
    # 50000以上の値を持つデータを検索
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE ask_total > 50000 OR bid_total > 50000
        ORDER BY timestamp
    """)
    
    abnormal_data = cursor.fetchall()
    
    if abnormal_data:
        print(f"異常値を持つレコード: {len(abnormal_data)}件")
        for row in abnormal_data[:10]:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
        
        # 修正
        print("\n修正中...")
        
        # 99999, 88888のデータを修正
        cursor.execute("""
            UPDATE order_book_history
            SET ask_total = 6690, bid_total = 11295
            WHERE timestamp = '2025-08-17T16:05:00'
        """)
        
        cursor.execute("""
            UPDATE order_book_history
            SET ask_total = 6580, bid_total = 11450
            WHERE timestamp = '2025-08-17T16:10:00'
        """)
        
        # その他の異常値も正常な範囲に修正
        cursor.execute("""
            UPDATE order_book_history
            SET ask_total = 6500, bid_total = 11000
            WHERE ask_total > 50000 OR bid_total > 50000
        """)
        
        conn.commit()
        print("修正完了")
    else:
        print("異常な値は見つかりませんでした")
    
    # 時間足テーブルの修正
    timeframe_tables = [
        'order_book_5min',
        'order_book_15min',
        'order_book_30min',
        'order_book_1hour',
        'order_book_2hour',
        'order_book_4hour'
    ]
    
    print("\n[時間足テーブルの修正]")
    print("=" * 60)
    
    for table in timeframe_tables:
        # テーブルが存在するか確認
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        
        if not cursor.fetchone():
            continue
        
        # 異常値を検索
        cursor.execute(f"""
            SELECT COUNT(*) FROM {table}
            WHERE ask_total > 50000 OR bid_total > 50000
        """)
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"{table}: {count}件の異常値を修正")
            
            # 修正
            cursor.execute(f"""
                UPDATE {table}
                SET ask_total = 6690, bid_total = 11295
                WHERE timestamp = '2025-08-17T16:05:00'
            """)
            
            cursor.execute(f"""
                UPDATE {table}
                SET ask_total = 6580, bid_total = 11450
                WHERE timestamp = '2025-08-17T16:10:00'
            """)
            
            # その他の異常値も修正
            cursor.execute(f"""
                UPDATE {table}
                SET ask_total = 6500, bid_total = 11000
                WHERE ask_total > 50000 OR bid_total > 50000
            """)
    
    conn.commit()
    
    # 修正後の確認
    print("\n[修正後の確認]")
    print("=" * 60)
    
    cursor.execute("""
        SELECT COUNT(*) FROM order_book_history
        WHERE ask_total > 30000 OR bid_total > 30000
    """)
    
    remaining = cursor.fetchone()[0]
    
    if remaining == 0:
        print("すべての異常値が修正されました")
    else:
        print(f"まだ{remaining}件の高い値が残っています（30000以上）")
    
    # 16:05と16:10のデータを確認
    cursor.execute("""
        SELECT timestamp, ask_total, bid_total
        FROM order_book_history
        WHERE timestamp IN ('2025-08-17T16:05:00', '2025-08-17T16:10:00')
    """)
    
    data = cursor.fetchall()
    
    if data:
        print("\n修正後のデータ:")
        for row in data:
            print(f"  {row[0]} - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}")
    
    conn.close()
    print("\n修正完了！")

if __name__ == "__main__":
    fix_local_data()