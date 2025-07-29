#!/usr/bin/env python3
"""
時間足グルーピングのテストスクリプト
作成日: 2025/07/29

このスクリプトは、時刻ベースのグルーピングロジックが
1分間隔と5分間隔の両方のデータで正しく動作することを確認します。
"""

from datetime import datetime, timedelta

def test_time_grouping(data_interval_minutes, timeframe_minutes):
    """
    時刻ベースグルーピングのテスト
    
    Args:
        data_interval_minutes: データの間隔（分）
        timeframe_minutes: 時間足の間隔（分）
    """
    print(f"\n=== テスト: {data_interval_minutes}分間隔データ → {timeframe_minutes}分足 ===")
    
    # テストデータの生成（24時間分）
    start_time = datetime(2025, 7, 29, 0, 0, 0)
    test_data = []
    
    for i in range(0, 24 * 60, data_interval_minutes):
        timestamp = start_time + timedelta(minutes=i)
        test_data.append(timestamp)
    
    print(f"生成されたデータ数: {len(test_data)}個")
    print(f"データ範囲: {test_data[0]} ～ {test_data[-1]}")
    
    # グループ化
    time_groups = {}
    
    for time_obj in test_data:
        # 時間帯を決定（本番コードと同じロジック）
        if timeframe_minutes < 60:  # 分足の場合
            group_minute = (time_obj.minute // timeframe_minutes) * timeframe_minutes
            group_key = time_obj.replace(minute=group_minute, second=0, microsecond=0)
        elif timeframe_minutes == 60:  # 1時間足の場合
            group_key = time_obj.replace(minute=0, second=0, microsecond=0)
        elif timeframe_minutes < 1440:  # 時間足の場合（2時間、4時間）
            hours_interval = timeframe_minutes // 60
            group_hour = (time_obj.hour // hours_interval) * hours_interval
            group_key = time_obj.replace(hour=group_hour, minute=0, second=0, microsecond=0)
        else:  # 日足の場合
            group_key = time_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if group_key not in time_groups:
            time_groups[group_key] = []
        time_groups[group_key].append(time_obj)
    
    # 結果の表示
    print(f"\nグループ数: {len(time_groups)}個")
    print("各グループの詳細:")
    
    sorted_groups = sorted(time_groups.keys())
    for i, group_key in enumerate(sorted_groups[:5]):  # 最初の5グループのみ表示
        group_data = time_groups[group_key]
        print(f"  グループ{i+1}: {group_key} - データ数: {len(group_data)}個")
        if len(group_data) <= 3:
            for data in group_data:
                print(f"    - {data}")
        else:
            print(f"    - {group_data[0]} ～ {group_data[-1]}")
    
    if len(sorted_groups) > 5:
        print(f"  ... 他 {len(sorted_groups) - 5} グループ")
    
    # 期待される結果との比較
    expected_groups = 24 * 60 // timeframe_minutes
    print(f"\n期待されるグループ数: {expected_groups}個")
    print(f"実際のグループ数: {len(time_groups)}個")
    print(f"判定: {'OK - 正しい' if len(time_groups) == expected_groups else 'NG - 誤り'}")
    
    return len(time_groups) == expected_groups


def main():
    """メイン関数"""
    print("時間足グルーピングロジックのテスト")
    print("=" * 50)
    
    # テストケース
    test_cases = [
        # (データ間隔（分）, 時間足（分）)
        (1, 60),    # 1分間隔データ → 1時間足（24グループ期待）
        (5, 60),    # 5分間隔データ → 1時間足（24グループ期待）
        (1, 240),   # 1分間隔データ → 4時間足（6グループ期待）
        (5, 240),   # 5分間隔データ → 4時間足（6グループ期待）
        (1, 1440),  # 1分間隔データ → 日足（1グループ期待）
        (5, 1440),  # 5分間隔データ → 日足（1グループ期待）
    ]
    
    results = []
    for data_interval, timeframe in test_cases:
        result = test_time_grouping(data_interval, timeframe)
        results.append(result)
    
    # 総合結果
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    print(f"成功: {sum(results)}/{len(results)}")
    print(f"総合判定: {'OK - すべて成功' if all(results) else 'NG - 一部失敗'}")


if __name__ == "__main__":
    main()