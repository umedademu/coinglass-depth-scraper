'use client'

import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
  ChartData
} from 'chart.js'
import { OrderBookData } from '@/lib/supabase'
import { InterpolatedOrderBookData } from '@/lib/dataInterpolation'
import { useMemo, useState, useRef, useEffect, useCallback } from 'react'

// Chart.jsの必要なコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// chartjs-plugin-zoomの動的インポート（SSR対応）
if (typeof window !== 'undefined') {
  import('chartjs-plugin-zoom').then((zoomPlugin) => {
    ChartJS.register(zoomPlugin.default)
  })
}

interface UnifiedChartProps {
  data: InterpolatedOrderBookData[]
}

export default function UnifiedChart({ data }: UnifiedChartProps) {
  const [isZoomed, setIsZoomed] = useState(false)
  const chartRef = useRef<any>(null)

  // データを時系列順にソート（メモ化）
  const sortedData = useMemo(() => {
    if (data.length === 0) return []
    return [...data].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  }, [data])

  // 動的スケール更新関数（Chart.jsインスタンスを直接操作）
  const updateDynamicScale = useCallback((chart: any) => {
    if (!chart || !sortedData.length) return

    // 表示範囲の取得
    const xScale = chart.scales.x
    const min = Math.max(0, Math.floor(xScale.min))
    const max = Math.min(sortedData.length - 1, Math.ceil(xScale.max))
    const visibleData = sortedData.slice(min, max + 1)

    if (visibleData.length === 0) return

    // 新しいスケール値の計算
    const askValues = visibleData.map(d => d.ask_total)
    const bidValues = visibleData.map(d => d.bid_total)
    const priceValues = visibleData.map(d => d.price)

    const minAsk = Math.min(...askValues)
    const maxAsk = Math.max(...askValues)
    const minBid = Math.min(...bidValues)
    const maxBid = Math.max(...bidValues)
    const minPrice = Math.min(...priceValues)
    const maxPrice = Math.max(...priceValues)

    // 共通スケールの計算
    const askRange = maxAsk - minAsk
    const bidRange = maxBid - minBid
    const maxRange = Math.max(askRange, bidRange) || 1
    const priceRange = maxPrice - minPrice || 1

    // データセットの直接更新（再レンダリングを避ける）
    const normalizedAskData = sortedData.map(d => {
      const normalizedValue = ((d.ask_total - minAsk) / maxRange) * 30
      return 100 - normalizedValue
    })

    const normalizedBidData = sortedData.map(d => {
      return ((d.bid_total - minBid) / maxRange) * 30
    })

    const normalizedPriceData = sortedData.map(d => {
      return ((d.price - minPrice) / priceRange) * 40 + 30
    })

    // データを直接更新
    chart.data.datasets[0].data = normalizedAskData
    chart.data.datasets[1].data = normalizedBidData
    chart.data.datasets[2].data = normalizedPriceData

    // Y軸ラベルの動的更新
    chart.options.scales.y.ticks.callback = function(value: any) {
      const numValue = Number(value)
      
      // 70-100の範囲（売り板） - 反転表示
      if (numValue >= 70 && numValue <= 100) {
        const actualValue = minAsk + ((100 - numValue) / 30) * maxRange
        if (actualValue > maxAsk) return ''
        return Math.round(actualValue).toLocaleString()
      }
      
      // 0-30の範囲（買い板）
      if (numValue >= 0 && numValue <= 30) {
        const actualValue = minBid + (numValue / 30) * maxRange
        if (actualValue > maxBid) return ''
        return Math.round(actualValue).toLocaleString()
      }
      
      return ''
    }

    // 価格Y軸の更新
    chart.options.scales.y2.ticks.callback = function(value: any) {
      const numValue = Number(value)
      
      // 30-70の範囲（価格）のみ表示
      if (numValue >= 30 && numValue <= 70) {
        const actualValue = minPrice + ((numValue - 30) / 40) * priceRange
        return `$${Math.round(actualValue).toLocaleString()}`
      }
      
      return ''
    }

    // アニメーションなし更新
    chart.update('none')
  }, [sortedData])

  // ズームリセット関数
  const handleResetZoom = () => {
    if (chartRef.current) {
      chartRef.current.resetZoom()
      setIsZoomed(false)
    }
  }

  // データの正規化と準備
  const { chartData, chartOptions } = useMemo(() => {
    if (sortedData.length === 0) {
      return {
        chartData: { labels: [], datasets: [] },
        chartOptions: {}
      }
    }

    // タイムスタンプを時刻形式に変換
    const timestamps = sortedData.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleTimeString('ja-JP', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })
    })

    // 最小値・最大値の計算（共通スケール用）
    const askValues = sortedData.map(d => d.ask_total)
    const bidValues = sortedData.map(d => d.bid_total)
    const priceValues = sortedData.map(d => d.price)

    const minAsk = Math.min(...askValues)
    const maxAsk = Math.max(...askValues)
    const minBid = Math.min(...bidValues)
    const maxBid = Math.max(...bidValues)
    const minPrice = Math.min(...priceValues)
    const maxPrice = Math.max(...priceValues)

    // 共通スケールの計算
    const askRange = maxAsk - minAsk
    const bidRange = maxBid - minBid
    const maxRange = Math.max(askRange, bidRange) || 1

    // データの正規化（垂直分離用）
    const normalizedAskData = sortedData.map(d => {
      // ASK（売り板）: 70-100の範囲（上部30%）、反転表示、共通スケール使用
      const normalizedValue = ((d.ask_total - minAsk) / maxRange) * 30
      return 100 - normalizedValue // 反転表示
    })

    const normalizedBidData = sortedData.map(d => {
      // BID（買い板）: 0-30の範囲（下部30%）、共通スケール使用
      return ((d.bid_total - minBid) / maxRange) * 30
    })

    const normalizedPriceData = sortedData.map(d => {
      // 価格: 30-70の範囲（中央40%）
      const priceRange = maxPrice - minPrice || 1
      return ((d.price - minPrice) / priceRange) * 40 + 30
    })

    // Chart.jsデータ構造
    const chartData: ChartData<'line'> = {
      labels: timestamps,
      datasets: [
        {
          label: '売り板',
          data: normalizedAskData,
          borderColor: 'rgb(248, 113, 113)',
          backgroundColor: 'rgba(248, 113, 113, 0.3)',
          fill: {
            target: { value: 100 },
            above: 'rgba(248, 113, 113, 0.3)'
          },
          yAxisID: 'y',
          tension: 0.1,
          pointRadius: 0 // マーカーを非表示
        },
        {
          label: '買い板',
          data: normalizedBidData,
          borderColor: 'rgb(74, 222, 128)',
          backgroundColor: 'rgba(74, 222, 128, 0.3)',
          fill: {
            target: { value: 0 },
            below: 'rgba(74, 222, 128, 0.3)'
          },
          yAxisID: 'y',
          tension: 0.1,
          pointRadius: 0 // マーカーを非表示
        },
        {
          label: '価格',
          data: normalizedPriceData,
          borderColor: '#ff9500',
          borderWidth: 3,
          backgroundColor: 'transparent',
          fill: false,
          yAxisID: 'y2', // 右側のY軸を使用
          tension: 0.1,
          pointRadius: 0 // マーカーを非表示
        }
      ]
    }

    // Chart.jsオプション
    const chartOptions: ChartOptions<'line'> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false // 凡例を非表示
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              const datasetIndex = context.datasetIndex
              const dataIndex = context.dataIndex
              const rawData = sortedData[dataIndex]
              
              let label = ''
              
              if (datasetIndex === 0) { // 売り板
                label = `売り板: ${rawData.ask_total.toLocaleString()} BTC`
              } else if (datasetIndex === 1) { // 買い板
                label = `買い板: ${rawData.bid_total.toLocaleString()} BTC`
              } else { // 価格
                label = `価格: $${rawData.price.toLocaleString()}`
              }
              
              // 補間データの識別表示
              if (rawData.isInterpolated) {
                label += ' (データ欠損・補間値)'
              }
              
              return label
            },
            afterBody: function(tooltipItems) {
              if (tooltipItems.length > 0) {
                const dataIndex = tooltipItems[0].dataIndex
                const rawData = sortedData[dataIndex]
                
                // 補間データの場合、説明を追加
                if (rawData.isInterpolated) {
                  return ['', '※ 前後の値から線形補間で推定']
                }
              }
              return []
            }
          }
        },
        zoom: {
          pan: {
            enabled: true,
            mode: 'x',
            onPanComplete: ({ chart }: any) => {
              updateDynamicScale(chart)
              setIsZoomed(true)
            }
          },
          zoom: {
            wheel: {
              enabled: true,
              speed: 0.1
            },
            mode: 'x',
            onZoomComplete: ({ chart }: any) => {
              updateDynamicScale(chart)
              setIsZoomed(true)
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#999',
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: { // 左側Y軸（ASK/BID用）
          position: 'left',
          min: 0,
          max: 100,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#999',
            callback: function(value: any) {
              const numValue = Number(value)
              
              // 70-100の範囲（売り板） - 反転表示
              if (numValue >= 70 && numValue <= 100) {
                const actualValue = minAsk + ((100 - numValue) / 30) * maxRange
                // 実データ最大値を超える場合は表示しない
                if (actualValue > maxAsk) return ''
                return Math.round(actualValue).toLocaleString() // 数字のみ
              }
              
              // 0-30の範囲（買い板）
              if (numValue >= 0 && numValue <= 30) {
                const actualValue = minBid + (numValue / 30) * maxRange
                // 実データ最大値を超える場合は表示しない
                if (actualValue > maxBid) return ''
                return Math.round(actualValue).toLocaleString() // 数字のみ
              }
              
              // 中央部分は表示しない
              return ''
            }
          }
        },
        y2: { // 右側Y軸（価格用）
          position: 'right',
          min: 0,
          max: 100,
          grid: {
            display: false // 右側Y軸のグリッドは非表示
          },
          ticks: {
            color: '#999',
            callback: function(value: any) {
              const numValue = Number(value)
              
              // 30-70の範囲（価格）のみ表示
              if (numValue >= 30 && numValue <= 70) {
                const actualValue = minPrice + ((numValue - 30) / 40) * (maxPrice - minPrice)
                return `$${Math.round(actualValue).toLocaleString()}` // 価格のみ$付き
              }
              
              return ''
            }
          }
        }
      }
    }

    return { chartData, chartOptions }
  }, [sortedData, updateDynamicScale])

  return (
    <div style={{
      marginTop: '2rem',
      padding: '1.5rem',
      backgroundColor: '#1e1e1e',
      borderRadius: '8px',
      height: '850px', // コンテナの高さ（パディング込み）
      position: 'relative'
    }}>
      {/* ズームリセットボタン */}
      {isZoomed && (
        <button
          onClick={handleResetZoom}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#4B5563',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 10,
            fontSize: '0.875rem',
            fontWeight: '500'
          }}
        >
          ズームリセット
        </button>
      )}
      
      <div style={{
        height: '800px', // グラフの高さ800px固定
        position: 'relative'
      }}>
        {data.length > 0 ? (
          <Line 
            ref={chartRef}
            data={chartData} 
            options={chartOptions} 
          />
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#999'
          }}>
            データがありません
          </div>
        )}
      </div>
    </div>
  )
}