#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第4段階：Realtime同期の修正テスト
Realtimeイベントが適切な時間足テーブルに保存されるかを確認
"""

import sqlite3
import os
from datetime import datetime, timedelta

def check_realtime_sync():
    """Realtime同期の状態を確認"""
    
    # AppDataフォルダのパスを取得
    appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
    db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
    
    print(f"データベースパス: {db_path}")
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("第4段階テスト：Realtime同期の修正")
    print("=" * 60)
    
    # 各時間足テーブルの最新データを確認
    tables = [
        ('order_book_5min', '5分足', 'order_book_shared'),
        ('order_book_15min', '15分足', 'order_book_15min'),
        ('order_book_30min', '30分足', 'order_book_30min'),
        ('order_book_1hour', '1時間足', 'order_book_1hour'),
        ('order_book_2hour', '2時間足', 'order_book_2hour'),
        ('order_book_4hour', '4時間足', 'order_book_4hour'),
        ('order_book_daily', '日足', 'order_book_daily')
    ]
    
    print("\n[各時間足テーブルの最新データ]")
    print("-" * 60)
    
    current_time = datetime.now()
    
    for local_table, timeframe_name, supabase_table in tables:
        # テーブルが存在するか確認
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (local_table,))
        
        if not cursor.fetchone():
            print(f"\n{timeframe_name} ({local_table}): テーブルが存在しません")
            continue
        
        # 最新5件のデータを取得
        cursor.execute(f"""
            SELECT timestamp, ask_total, bid_total, price
            FROM {local_table}
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        latest_data = cursor.fetchall()
        
        print(f"\n{timeframe_name} ({local_table}):")
        print(f"  Supabaseテーブル: {supabase_table}")
        
        if latest_data:
            print(f"  最新データ（上位5件）:")
            for row in latest_data:
                dt = datetime.fromisoformat(row[0])
                age = current_time - dt
                age_str = f"{int(age.total_seconds() / 60)}分前"
                print(f"    {dt.strftime('%Y-%m-%d %H:%M')} ({age_str}) - Ask: {row[1]:.0f}, Bid: {row[2]:.0f}, Price: ${row[3]:.2f}")
        else:
            print(f"  データなし")
    
    # 1分足DBへの混入チェック
    print("\n[1分足DBへの混入チェック]")
    print("-" * 60)
    
    # 5分足データが1分足DBに混入していないか確認
    # 最近1時間のデータで、5分の倍数のタイムスタンプを確認
    one_hour_ago = (current_time - timedelta(hours=1)).isoformat()
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN CAST(strftime('%M', timestamp) AS INTEGER) % 5 = 0 THEN 1 ELSE 0 END) as five_min_count
        FROM order_book_history
        WHERE timestamp >= ?
    """, (one_hour_ago,))
    
    result = cursor.fetchone()
    if result and result[0] > 0:
        total_count = result[0]
        five_min_count = result[1] if result[1] else 0
        percentage = (five_min_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"過去1時間のデータ: 総数 {total_count}件")
        print(f"5分の倍数のタイムスタンプ: {five_min_count}件 ({percentage:.1f}%)")
        
        if percentage > 25:  # 25%以上は異常
            print("⚠️ 警告: 5分足データが1分足DBに混入している可能性があります")
        else:
            print("✓ 正常: 1分足DBへの混入は少ないです")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("確認ポイント:")
    print("=" * 60)
    print("1. アプリケーション起動中のRealtime同期ログを確認:")
    print("   - '[Realtime同期] order_book_shared から X件のデータをorder_book_5minに保存開始'")
    print("   - '[Realtime同期] 5分足: 新規X件, 更新X件をorder_book_5minに保存'")
    print("")
    print("2. Supabaseでテストデータを更新:")
    print("   - 大きな値（例: 99999）を設定")
    print("   - Realtime同期で該当する時間足テーブルが更新される")
    print("   - 1分足DB（order_book_history）には保存されない")
    print("")
    print("3. 各時間足テーブルが独立して更新される:")
    print("   - 5分足の更新が15分足に影響しない")
    print("   - 各テーブルが適切なタイミングでのみ更新される")

def test_table_mapping():
    """テーブルマッピングのテスト"""
    print("\n" + "=" * 60)
    print("テーブルマッピングテスト")
    print("=" * 60)
    
    # マッピングの確認
    table_mapping = {
        'order_book_shared': 'order_book_5min',
        'order_book_15min': 'order_book_15min',
        'order_book_30min': 'order_book_30min',
        'order_book_1hour': 'order_book_1hour',
        'order_book_2hour': 'order_book_2hour',
        'order_book_4hour': 'order_book_4hour',
        'order_book_daily': 'order_book_daily'
    }
    
    print("\n[Supabase → ローカルテーブルマッピング]")
    for supabase_table, local_table in table_mapping.items():
        print(f"  {supabase_table:20} → {local_table}")
    
    print("\n[テストケース]")
    test_cases = [
        ('order_book_shared', 'order_book_5min', True),
        ('order_book_15min', 'order_book_15min', True),
        ('unknown_table', None, False),
        ('order_book_1min', None, False),  # 1分足はSupabaseには存在しない
    ]
    
    for supabase_table, expected_local, should_process in test_cases:
        local_table = table_mapping.get(supabase_table)
        status = "✓" if (local_table == expected_local) else "✗"
        process_msg = "処理される" if should_process else "スキップ"
        print(f"  {status} {supabase_table:20} → {local_table or 'None':20} ({process_msg})")

if __name__ == "__main__":
    # Realtime同期の確認
    check_realtime_sync()
    
    # テーブルマッピングのテスト
    test_table_mapping()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)