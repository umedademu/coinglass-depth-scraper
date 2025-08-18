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
import { useMemo } from 'react'

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

interface UnifiedChartProps {
  data: OrderBookData[]
}

export default function UnifiedChart({ data }: UnifiedChartProps) {
  // データの正規化と準備
  const { chartData, chartOptions } = useMemo(() => {
    if (data.length === 0) {
      return {
        chartData: { labels: [], datasets: [] },
        chartOptions: {}
      }
    }

    // データを時系列順（古い→新しい）にソート
    const sortedData = [...data].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

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
          tension: 0.1
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
          tension: 0.1
        },
        {
          label: '価格',
          data: normalizedPriceData,
          borderColor: '#ff9500',
          borderWidth: 3,
          backgroundColor: 'transparent',
          fill: false,
          yAxisID: 'y',
          tension: 0.1
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
              
              if (datasetIndex === 0) { // 売り板
                return `売り板: ${rawData.ask_total.toLocaleString()} BTC`
              } else if (datasetIndex === 1) { // 買い板
                return `買い板: ${rawData.bid_total.toLocaleString()} BTC`
              } else { // 価格
                return `価格: $${rawData.price.toLocaleString()}`
              }
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
        y: {
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
              
              // 30-70の範囲（価格）
              if (numValue > 30 && numValue < 70) {
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
  }, [data])

  return (
    <div style={{
      marginTop: '2rem',
      padding: '1.5rem',
      backgroundColor: '#1e1e1e',
      borderRadius: '8px',
      height: '850px' // コンテナの高さ（パディング込み）
    }}>
      <div style={{
        height: '800px', // グラフの高さ800px固定
        position: 'relative'
      }}>
        {data.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
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