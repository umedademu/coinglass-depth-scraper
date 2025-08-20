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
import { useMemo, useState, useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'

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

// 初期表示件数（TradingView/MT5準拠）
const INITIAL_DISPLAY_COUNT = 120

interface UnifiedChartProps {
  data: InterpolatedOrderBookData[]
  onLoadOlderData?: () => Promise<InterpolatedOrderBookData[]>
  isLoadingMore?: boolean
  onHoverData?: (data: InterpolatedOrderBookData | null) => void
  isMobile?: boolean
}

// 外部から操作可能なメソッドの型定義
export interface UnifiedChartRef {
  addRealtimeData: (newData: InterpolatedOrderBookData) => void
  getChartInstance: () => any
}

const UnifiedChart = forwardRef<UnifiedChartRef, UnifiedChartProps>(({ data, onLoadOlderData, isLoadingMore = false, onHoverData, isMobile = false }, ref) => {
  const [isZoomed, setIsZoomed] = useState(false)
  const [isLoadingOlder, setIsLoadingOlder] = useState(false)
  const [isPrefetching, setIsPrefetching] = useState(false)
  const chartRef = useRef<any>(null)
  const internalDataRef = useRef<InterpolatedOrderBookData[]>([]) // 内部データ参照
  const isLoadingRef = useRef(false) // ローディング中フラグ（重複防止）

  // データを時系列順にソート（メモ化）
  const sortedData = useMemo(() => {
    if (data.length === 0) return []
    const sorted = [...data].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
    internalDataRef.current = sorted // 内部参照を更新
    return sorted
  }, [data])
  
  // 縦線カーソルプラグインの実装
  const crosshairPlugin = useMemo(() => ({
    id: 'crosshair',
    afterDraw: (chart: any) => {
      if (chart.tooltip?._active && chart.tooltip._active.length) {
        const activePoint = chart.tooltip._active[0]
        const ctx = chart.ctx
        const x = activePoint.element.x
        const topY = chart.scales.y.top
        const bottomY = chart.scales.y.bottom

        // 保存現在の描画状態
        ctx.save()
        
        // 縦線の描画のみ（時間軸位置を示す）
        ctx.beginPath()
        ctx.moveTo(x, topY)
        ctx.lineTo(x, bottomY)
        ctx.lineWidth = 1
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
        ctx.setLineDash([3, 3])
        ctx.stroke()
        
        // 描画状態を復元
        ctx.restore()
      }
    }
  }), [])

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
  
  // リアルタイムデータを追加する関数
  const addRealtimeData = useCallback((newData: InterpolatedOrderBookData) => {
    const chart = chartRef.current
    if (!chart) return
    
    // 内部データに追加
    internalDataRef.current = [...internalDataRef.current, newData]
    
    // メモリ管理（最大5000件）
    const MAX_POINTS = 5000
    if (internalDataRef.current.length > MAX_POINTS) {
      internalDataRef.current = internalDataRef.current.slice(-MAX_POINTS)
      
      // ズーム範囲も調整
      if (chart.scales && chart.scales.x) {
        const removedCount = 1
        chart.scales.x.min = Math.max(0, chart.scales.x.min - removedCount)
        chart.scales.x.max = Math.max(0, chart.scales.x.max - removedCount)
      }
    }
    
    // 現在のデータを取得
    const currentData = internalDataRef.current
    
    // 新しいタイムスタンプを追加
    const date = new Date(newData.timestamp)
    const timeLabel = date.toLocaleTimeString('ja-JP', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
    
    // 正規化のための計算
    const askValues = currentData.map(d => d.ask_total)
    const bidValues = currentData.map(d => d.bid_total)
    const priceValues = currentData.map(d => d.price)
    
    const minAsk = Math.min(...askValues)
    const maxAsk = Math.max(...askValues)
    const minBid = Math.min(...bidValues)
    const maxBid = Math.max(...bidValues)
    const minPrice = Math.min(...priceValues)
    const maxPrice = Math.max(...priceValues)
    
    const askRange = maxAsk - minAsk
    const bidRange = maxBid - minBid
    const maxRange = Math.max(askRange, bidRange) || 1
    const priceRange = maxPrice - minPrice || 1
    
    // 新しいデータポイントを正規化
    const normalizedAsk = 100 - ((newData.ask_total - minAsk) / maxRange) * 30
    const normalizedBid = ((newData.bid_total - minBid) / maxRange) * 30
    const normalizedPrice = ((newData.price - minPrice) / priceRange) * 40 + 30
    
    // Chart.jsのデータを直接更新
    chart.data.labels.push(timeLabel)
    chart.data.datasets[0].data.push(normalizedAsk)
    chart.data.datasets[1].data.push(normalizedBid)
    chart.data.datasets[2].data.push(normalizedPrice)
    
    // メモリ管理（グラフ側）
    if (chart.data.labels.length > MAX_POINTS) {
      chart.data.labels.shift()
      chart.data.datasets[0].data.shift()
      chart.data.datasets[1].data.shift()
      chart.data.datasets[2].data.shift()
    }
    
    // 現在ズーム中の場合は動的スケールを更新
    if (isZoomed) {
      updateDynamicScale(chart)
    }
    
    // アニメーションなしで更新（ズーム状態を維持）
    chart.update('none')
  }, [isZoomed, updateDynamicScale])
  
  // 外部から操作可能なメソッドを公開
  useImperativeHandle(ref, () => ({
    addRealtimeData,
    getChartInstance: () => chartRef.current
  }), [addRealtimeData])

  // データの正規化と準備
  const { chartData, chartOptions } = useMemo(() => {
    if (sortedData.length === 0) {
      return {
        chartData: { labels: [], datasets: [] },
        chartOptions: {}
      }
    }

    // タイムスタンプを時刻形式に変換（0:00の場合は日付のみ表示）
    const timestamps = sortedData.map(d => {
      const date = new Date(d.timestamp)
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      
      // 0:00の場合は日付のみ表示（日のみ）
      if (hours === '00' && minutes === '00') {
        const day = date.getDate().toString()
        return day  // 例：「17」
      }
      
      return `${hours}:${minutes}`
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
      layout: {
        padding: isMobile ? 0 : undefined
      },
      plugins: {
        legend: {
          display: false // 凡例を非表示
        },
        tooltip: {
          enabled: false  // ツールチップを完全に無効化
        },
        zoom: {
          pan: {
            enabled: true,
            mode: 'x',
            onPanComplete: async ({ chart }: any) => {
              updateDynamicScale(chart)
              setIsZoomed(true)
              
              // 第7段階：左端到達検知と過去データ取得
              if (onLoadOlderData && !isLoadingRef.current) {
                const xScale = chart.scales.x
                const dataLength = chart.data.labels.length
                
                // 左端到達を検知（最小値が0に近い場合）
                if (xScale.min <= 0) {
                  console.log('🔄 左端に到達！過去データを取得します...')
                  isLoadingRef.current = true
                  setIsLoadingOlder(true)
                  
                  try {
                    // 過去データを取得
                    const newData = await onLoadOlderData()
                    
                    if (newData.length > 0) {
                      console.log(`📊 ${newData.length}件の過去データを取得しました`)
                      
                      // X軸インデックスを調整（重要）
                      const addedCount = newData.length
                      
                      // 現在の表示範囲を保持するため、min/maxを調整
                      if (chart.options.scales?.x) {
                        chart.options.scales.x.min = xScale.min + addedCount
                        chart.options.scales.x.max = xScale.max + addedCount
                      }
                      
                      // 即座に反映（ジャンプを防ぐ）
                      chart.update('none')
                      
                      console.log(`📍 X軸インデックスを調整: min=${xScale.min + addedCount}, max=${xScale.max + addedCount}`)
                    }
                  } catch (error) {
                    console.error('❌ 過去データ取得エラー:', error)
                  } finally {
                    isLoadingRef.current = false
                    setIsLoadingOlder(false)
                  }
                }
                
                // プリフェッチ機能：左端の20%に到達したら先読み開始
                else if (xScale.min < dataLength * 0.2 && !isPrefetching) {
                  console.log('📥 プリフェッチ開始（20%地点）')
                  setIsPrefetching(true)
                  
                  // バックグラウンドで先読み
                  onLoadOlderData().then((newData) => {
                    if (newData.length > 0) {
                      console.log(`✅ プリフェッチ完了: ${newData.length}件`)
                    }
                    setIsPrefetching(false)
                  }).catch((error) => {
                    console.error('❌ プリフェッチエラー:', error)
                    setIsPrefetching(false)
                  })
                }
              }
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
      interaction: {
        mode: 'index',        // 縦軸全体が当たり判定
        intersect: false      // ポイント上でなくてもOK
      },
      onHover: (event: any, activeElements: any) => {
        if (onHoverData) {
          if (activeElements.length > 0) {
            const dataIndex = activeElements[0].index
            onHoverData(sortedData[dataIndex])
          } else {
            onHoverData(null)
          }
        }
      },
      scales: {
        x: {
          // type: 'category'を削除 - 無限スクロール機能との互換性のため
          // 初期表示を最新250件に制限（TradingView/MT5準拠）
          min: Math.max(0, sortedData.length - INITIAL_DISPLAY_COUNT),  // 最新250件の開始位置
          max: sortedData.length - 1,                                    // 最後まで
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#999',
            maxRotation: isMobile ? 0 : 45,
            minRotation: isMobile ? 0 : 45,
            autoSkip: true,  // 重要：自動的にラベルを間引く
            maxTicksLimit: isMobile ? 6 : 20,  // 表示する最大ラベル数
            font: {
              size: isMobile ? 10 : 11
            }
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
            font: {
              size: isMobile ? 10 : 11
            },
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
            font: {
              size: isMobile ? 10 : 11
            },
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
      marginTop: isMobile ? '0' : '2rem',
      padding: isMobile ? '0' : '1.5rem',
      backgroundColor: '#1e1e1e',
      borderRadius: isMobile ? '0' : '8px',
      height: isMobile ? '100%' : '850px', // モバイル時は親の高さに合わせる
      position: 'relative',
      display: isMobile ? 'flex' : 'block',
      flexDirection: isMobile ? 'column' : undefined
    }}>
      {/* ローディングインジケーター（第7段階） */}
      {(isLoadingOlder || isLoadingMore) && !isMobile && (
        <div style={{
          position: 'absolute',
          top: '1rem',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(30, 30, 30, 0.9)',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          zIndex: 11,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            border: '2px solid #4B5563',
            borderTopColor: '#fff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <span style={{ fontSize: '0.875rem', color: '#fff' }}>
            過去データを取得中...
          </span>
        </div>
      )}
      
      {/* プリフェッチインジケーター */}
      {isPrefetching && !isMobile && (
        <div style={{
          position: 'absolute',
          bottom: '1rem',
          left: '1rem',
          backgroundColor: 'rgba(30, 30, 30, 0.7)',
          padding: '0.25rem 0.5rem',
          borderRadius: '4px',
          fontSize: '0.75rem',
          color: '#999'
        }}>
          📥 先読み中...
        </div>
      )}
      
      {/* ズームリセットボタン */}
      {isZoomed && (
        <button
          onClick={handleResetZoom}
          style={{
            position: 'absolute',
            top: isMobile ? '0.5rem' : '1rem',
            right: isMobile ? '0.5rem' : '1rem',
            padding: isMobile ? '0.25rem 0.5rem' : '0.5rem 1rem',
            backgroundColor: '#4B5563',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            zIndex: 10,
            fontSize: isMobile ? '0.75rem' : '0.875rem',
            fontWeight: '500'
          }}
        >
          リセット
        </button>
      )}
      
      {/* スピナーアニメーション用のスタイル */}
      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      
      <div style={{
        height: isMobile ? '100%' : '800px', // モバイル時は親の高さに合わせる
        position: 'relative',
        flex: isMobile ? 1 : undefined,
        minHeight: 0
      }}>
        {data.length > 0 ? (
          <Line 
            ref={chartRef}
            data={chartData} 
            options={chartOptions}
            plugins={[crosshairPlugin]}
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
})

UnifiedChart.displayName = 'UnifiedChart'

export default UnifiedChart