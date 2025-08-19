import { OrderBookData, TimeframeKey } from './supabase'

// 補間されたデータを識別するための拡張インターフェース
export interface InterpolatedOrderBookData extends OrderBookData {
  isInterpolated?: boolean
}

// 各時間足の間隔（ミリ秒）
const timeframeIntervals: Record<TimeframeKey, number> = {
  '5min': 5 * 60 * 1000,
  '15min': 15 * 60 * 1000,
  '30min': 30 * 60 * 1000,
  '1hour': 60 * 60 * 1000,
  '2hour': 2 * 60 * 60 * 1000,
  '4hour': 4 * 60 * 60 * 1000,
  '1day': 24 * 60 * 60 * 1000,
}

// データ欠損をチェックして補完する関数
export function interpolateMissingData(
  data: OrderBookData[],
  timeframe: TimeframeKey
): {
  interpolatedData: InterpolatedOrderBookData[]
  stats: {
    originalCount: number
    interpolatedCount: number
    totalCount: number
    interpolationRate: number
  }
} {
  if (data.length === 0) {
    return {
      interpolatedData: [],
      stats: {
        originalCount: 0,
        interpolatedCount: 0,
        totalCount: 0,
        interpolationRate: 0
      }
    }
  }

  // データを時系列順にソート
  const sortedData = [...data].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  const interval = timeframeIntervals[timeframe]
  const result: InterpolatedOrderBookData[] = []
  let interpolatedCount = 0

  // 最初のデータを追加
  result.push({ ...sortedData[0], isInterpolated: false })

  // データ間の欠損をチェックして補間
  for (let i = 1; i < sortedData.length; i++) {
    const prevData = sortedData[i - 1]
    const currData = sortedData[i]
    
    const prevTime = new Date(prevData.timestamp).getTime()
    const currTime = new Date(currData.timestamp).getTime()
    
    const timeDiff = currTime - prevTime
    const expectedSlots = Math.floor(timeDiff / interval)
    
    // 欠損がある場合（2スロット以上の間隔）
    if (expectedSlots > 1) {
      // 欠損スロットを補間
      for (let j = 1; j < expectedSlots; j++) {
        const interpolationRatio = j / expectedSlots
        const interpolatedTime = new Date(prevTime + (interval * j))
        
        // 線形補間
        const interpolatedData: InterpolatedOrderBookData = {
          id: -1, // 補間データのIDは-1とする
          timestamp: interpolatedTime.toISOString(),
          ask_total: prevData.ask_total + (currData.ask_total - prevData.ask_total) * interpolationRatio,
          bid_total: prevData.bid_total + (currData.bid_total - prevData.bid_total) * interpolationRatio,
          price: prevData.price + (currData.price - prevData.price) * interpolationRatio,
          group_id: 'default-group',
          isInterpolated: true
        }
        
        result.push(interpolatedData)
        interpolatedCount++
      }
    }
    
    // 現在のデータを追加
    result.push({ ...currData, isInterpolated: false })
  }

  const stats = {
    originalCount: sortedData.length,
    interpolatedCount: interpolatedCount,
    totalCount: result.length,
    interpolationRate: (interpolatedCount / result.length) * 100
  }

  // デバッグ情報をコンソールに出力
  console.log(`📊 補完統計 (${timeframe}):`)
  console.log(`  - 実データ数: ${stats.originalCount}件`)
  console.log(`  - 補間データ数: ${stats.interpolatedCount}件`)
  console.log(`  - 合計データ数: ${stats.totalCount}件`)
  console.log(`  - 補間率: ${stats.interpolationRate.toFixed(1)}%`)

  return { interpolatedData: result, stats }
}

// 時間足の間隔に基づいて期待されるタイムスタンプを生成
export function generateExpectedTimestamps(
  startTime: Date,
  endTime: Date,
  timeframe: TimeframeKey
): Date[] {
  const interval = timeframeIntervals[timeframe]
  const timestamps: Date[] = []
  
  // 開始時刻を時間足の間隔に丸める
  let currentTime = new Date(Math.floor(startTime.getTime() / interval) * interval)
  
  while (currentTime <= endTime) {
    timestamps.push(new Date(currentTime))
    currentTime = new Date(currentTime.getTime() + interval)
  }
  
  return timestamps
}

// データの欠損箇所を検出する関数
export function detectMissingSlots(
  data: OrderBookData[],
  timeframe: TimeframeKey
): {
  missingRanges: Array<{ start: Date; end: Date; count: number }>
  totalMissing: number
} {
  if (data.length < 2) {
    return { missingRanges: [], totalMissing: 0 }
  }

  const sortedData = [...data].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  const interval = timeframeIntervals[timeframe]
  const missingRanges: Array<{ start: Date; end: Date; count: number }> = []
  let totalMissing = 0

  for (let i = 1; i < sortedData.length; i++) {
    const prevTime = new Date(sortedData[i - 1].timestamp)
    const currTime = new Date(sortedData[i].timestamp)
    
    const timeDiff = currTime.getTime() - prevTime.getTime()
    const expectedSlots = Math.floor(timeDiff / interval)
    
    if (expectedSlots > 1) {
      const missingCount = expectedSlots - 1
      missingRanges.push({
        start: new Date(prevTime.getTime() + interval),
        end: new Date(currTime.getTime() - interval),
        count: missingCount
      })
      totalMissing += missingCount
    }
  }

  if (missingRanges.length > 0) {
    console.log(`⚠️ データ欠損検出 (${timeframe}):`)
    console.log(`  - 欠損箇所数: ${missingRanges.length}箇所`)
    console.log(`  - 総欠損スロット数: ${totalMissing}件`)
    missingRanges.slice(0, 5).forEach((range, i) => {
      console.log(`  - 欠損 ${i + 1}: ${range.start.toLocaleString('ja-JP')} ～ ${range.end.toLocaleString('ja-JP')} (${range.count}件)`)
    })
    if (missingRanges.length > 5) {
      console.log(`  ... 他 ${missingRanges.length - 5} 箇所`)
    }
  }

  return { missingRanges, totalMissing }
}