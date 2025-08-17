'use client'

import { useEffect, useState, useRef } from 'react'
import { supabase, OrderBookData } from '../lib/supabase'
import dynamic from 'next/dynamic'
import { RealtimeChannel } from '@supabase/supabase-js'

// Chart.jsはSSRと互換性がないため、動的インポートを使用
const OrderBookChart = dynamic(() => import('../components/OrderBookChart'), {
  ssr: false,
  loading: () => <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>グラフを読み込み中...</div>
})

// タイムフレームの定義
type Timeframe = '5min' | '15min' | '30min' | '1hour' | '2hour' | '4hour' | 'daily'

// 接続状態の定義
type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error'

interface TimeframeConfig {
  label: string
  table: string
  interval: string
}

const timeframeConfigs: Record<Timeframe, TimeframeConfig> = {
  '5min': { label: '5分足', table: 'order_book_shared', interval: '5分' },
  '15min': { label: '15分足', table: 'order_book_15min', interval: '15分' },
  '30min': { label: '30分足', table: 'order_book_30min', interval: '30分' },
  '1hour': { label: '1時間足', table: 'order_book_1hour', interval: '1時間' },
  '2hour': { label: '2時間足', table: 'order_book_2hour', interval: '2時間' },
  '4hour': { label: '4時間足', table: 'order_book_4hour', interval: '4時間' },
  'daily': { label: '日足', table: 'order_book_daily', interval: '1日' }
}

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<OrderBookData[]>([])
  const [chartData, setChartData] = useState<OrderBookData[]>([]) // グラフ用データ（300件）
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('5min')
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const [showUpdateNotification, setShowUpdateNotification] = useState(false)
  const channelRef = useRef<RealtimeChannel | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  // 初回マウント時にlocalStorageから設定を復元
  useEffect(() => {
    const saved = localStorage.getItem('selectedTimeframe')
    if (saved && saved in timeframeConfigs) {
      setSelectedTimeframe(saved as Timeframe)
    }
  }, [])

  // 新規データをリストに追加する関数（メモリリーク対策付き）
  const handleNewData = (newRecord: OrderBookData) => {
    console.log(`[Realtime] New data received for ${selectedTimeframe}:`, newRecord)
    
    // データ更新通知を表示
    setShowUpdateNotification(true)
    setTimeout(() => setShowUpdateNotification(false), 3000)
    
    // データを更新（最新データを先頭に追加）
    setData(prevData => {
      const updated = [newRecord, ...prevData]
      // メモリリーク対策：100件を超えたら古いデータを削除
      return updated.slice(0, 100)
    })
    
    // グラフデータを更新
    setChartData(prevChartData => {
      const updated = [newRecord, ...prevChartData]
      // メモリリーク対策：300件を超えたら古いデータを削除
      return updated.slice(0, 300)
    })
    
    setLastUpdate(new Date())
  }

  // 再接続処理
  const setupRealtimeConnection = () => {
    // 既存のチャンネルをクリーンアップ
    if (channelRef.current) {
      console.log('[Realtime] Cleaning up previous channel')
      supabase.removeChannel(channelRef.current)
      channelRef.current = null
    }

    const config = timeframeConfigs[selectedTimeframe]
    const channelName = `realtime-${config.table}-default-group`
    
    console.log(`[Realtime] Setting up subscription for ${config.label}`)
    setConnectionStatus('connecting')
    
    // 新しいチャンネルを作成
    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: config.table,
          filter: 'group_id=eq.default-group'
        },
        (payload) => {
          handleNewData(payload.new as OrderBookData)
          // 接続成功時は再接続カウンターをリセット
          reconnectAttemptsRef.current = 0
        }
      )
      .subscribe((status) => {
        console.log(`[Realtime] Subscription status: ${status}`)
        if (status === 'SUBSCRIBED') {
          setConnectionStatus('connected')
          reconnectAttemptsRef.current = 0
          console.log(`[Realtime] Successfully subscribed to ${config.label}`)
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          setConnectionStatus('error')
          console.error(`[Realtime] Connection error: ${status}`)
          
          // 自動再接続を試みる
          scheduleReconnect()
        } else if (status === 'CLOSED') {
          setConnectionStatus('disconnected')
          console.log('[Realtime] Channel closed')
        }
      })

    channelRef.current = channel
  }

  // 再接続をスケジュール
  const scheduleReconnect = () => {
    // 既存の再接続タイマーをクリア
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    // 再接続の試行回数に応じて待機時間を増やす（指数バックオフ）
    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
    reconnectAttemptsRef.current++
    
    console.log(`[Realtime] Scheduling reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)
    
    reconnectTimeoutRef.current = setTimeout(() => {
      console.log('[Realtime] Attempting to reconnect...')
      setupRealtimeConnection()
    }, delay)
  }

  // タイムフレーム変更時にデータを再取得
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log(`Fetching ${selectedTimeframe} data from Supabase...`)
        const config = timeframeConfigs[selectedTimeframe]
        
        // テーブル表示用：最新100件のデータを取得
        const { data: tableData, error: tableError } = await supabase
          .from(config.table)
          .select('*')
          .eq('group_id', 'default-group')
          .order('timestamp', { ascending: false })
          .limit(100)

        // グラフ表示用：最新300件のデータを取得
        const { data: graphData, error: graphError } = await supabase
          .from(config.table)
          .select('*')
          .eq('group_id', 'default-group')
          .order('timestamp', { ascending: false })
          .limit(300)

        if (tableError || graphError) {
          console.error('Error fetching data:', tableError || graphError)
          setError((tableError || graphError)?.message || 'Error fetching data')
        } else {
          console.log(`✅ ${config.label} data fetched successfully:`, tableData?.length, 'table records,', graphData?.length, 'graph records')
          setData(tableData || [])
          setChartData(graphData || [])
          setLastUpdate(new Date())
        }
      } catch (err) {
        console.error('Unexpected error:', err)
        setError('Unexpected error occurred')
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
    localStorage.setItem('selectedTimeframe', selectedTimeframe)
  }, [selectedTimeframe])

  // Realtime購読の設定
  useEffect(() => {
    setupRealtimeConnection()

    // クリーンアップ関数
    return () => {
      // 再接続タイマーをクリア
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      
      // チャンネルをクリーンアップ
      if (channelRef.current) {
        console.log('[Realtime] Cleaning up channel on unmount')
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
        setConnectionStatus('disconnected')
      }
    }
  }, [selectedTimeframe]) // selectedTimeframeが変更されたら再購読

  // ネットワーク接続の監視
  useEffect(() => {
    const handleOnline = () => {
      console.log('[Network] Connection restored')
      if (connectionStatus === 'error' || connectionStatus === 'disconnected') {
        console.log('[Network] Attempting to reconnect...')
        setupRealtimeConnection()
      }
    }

    const handleOffline = () => {
      console.log('[Network] Connection lost')
      setConnectionStatus('disconnected')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [connectionStatus])

  // 最新のデータ（最初の1件）
  const latestData = data[0]
  
  // 買い/売り比率の計算
  const bidAskRatio = latestData 
    ? (latestData.bid_total / latestData.ask_total).toFixed(2)
    : '0.00'

  // タイムスタンプをそのまま表示（変換なし）
  const formatTimestamp = (timestamp: string) => {
    // ISO形式のタイムスタンプを直接パースして表示
    // 例: "2025-08-17T02:40:00+00:00" -> "2025/08/17 02:40:00"
    const cleanTimestamp = timestamp
      .replace('T', ' ')
      .split('.')[0]  // ミリ秒を除去
      .split('+')[0]  // タイムゾーン情報を除去
      .split('Z')[0]  // Z（UTC）を除去
    const [datePart, timePart] = cleanTimestamp.split(' ')
    const formattedDate = datePart.replace(/-/g, '/')
    return `${formattedDate} ${timePart}`
  }

  // 価格のフォーマット
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price)
  }

  // BTCのフォーマット
  const formatBTC = (btc: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(btc) + ' BTC'
  }

  return (
    <main style={{
      minHeight: '100vh',
      backgroundColor: '#1a1a1a',
      color: '#ffffff',
      fontFamily: 'system-ui, sans-serif',
      padding: '2rem'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ position: 'relative', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', textAlign: 'center' }}>
            Depth Viewer v0.800
          </h1>
          
          {/* 接続状態インジケーター */}
          <div style={{
            position: 'absolute',
            top: '0.5rem',
            right: '0',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#2a2a2a',
            borderRadius: '6px',
            fontSize: '0.875rem'
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: connectionStatus === 'connected' ? '#4ade80' : 
                             connectionStatus === 'connecting' ? '#fbbf24' :
                             connectionStatus === 'error' ? '#f87171' : '#666',
              animation: connectionStatus === 'connecting' ? 'pulse 1.5s infinite' : 'none'
            }} />
            <span style={{ color: '#888' }}>
              {connectionStatus === 'connected' ? '接続中' :
               connectionStatus === 'connecting' ? '接続中...' :
               connectionStatus === 'error' ? 'エラー' : '切断'}
            </span>
          </div>

          {/* データ更新通知 */}
          {showUpdateNotification && (
            <div style={{
              position: 'absolute',
              top: '3rem',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#3b82f6',
              color: '#fff',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              animation: 'slideDown 0.3s ease-out',
              zIndex: 10
            }}>
              データが更新されました
            </div>
          )}
        </div>

        {/* CSS アニメーション */}
        <style jsx>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }
        `}</style>
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: '#888' }}>Loading data...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: '#f87171', marginBottom: '1rem' }}>
              ❌ Error loading data
            </p>
            <p style={{ color: '#888' }}>{error}</p>
          </div>
        ) : (
          <>
            {/* 現在の情報 */}
            {latestData && (
              <div style={{
                backgroundColor: '#2a2a2a',
                borderRadius: '8px',
                padding: '1.5rem',
                marginBottom: '2rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem'
              }}>
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                    最新価格
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4ade80' }}>
                    {formatPrice(latestData.price)}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                    売り板総量
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f87171' }}>
                    {formatBTC(latestData.ask_total)}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                    買い板総量
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4ade80' }}>
                    {formatBTC(latestData.bid_total)}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                    買い/売り比率
                  </p>
                  <p style={{ 
                    fontSize: '1.5rem', 
                    fontWeight: 'bold',
                    color: parseFloat(bidAskRatio) >= 1 ? '#4ade80' : '#f87171'
                  }}>
                    {bidAskRatio}
                  </p>
                </div>
              </div>
            )}

            {/* タイムフレーム選択 */}
            <div style={{
              backgroundColor: '#2a2a2a',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '2rem',
              display: 'flex',
              gap: '0.5rem',
              flexWrap: 'wrap',
              justifyContent: 'center'
            }}>
              {Object.entries(timeframeConfigs).map(([key, config]) => (
                <button
                  key={key}
                  onClick={() => setSelectedTimeframe(key as Timeframe)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    borderRadius: '6px',
                    border: 'none',
                    backgroundColor: selectedTimeframe === key ? '#3b82f6' : '#404040',
                    color: '#ffffff',
                    fontSize: '0.875rem',
                    fontWeight: selectedTimeframe === key ? 'bold' : 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    opacity: loading ? 0.5 : 1
                  }}
                  disabled={loading}
                >
                  {config.label}
                </button>
              ))}
            </div>

            {/* グラフ表示 */}
            {chartData.length > 0 && (
              <div style={{ marginTop: '2rem', marginBottom: '2rem' }}>
                <OrderBookChart data={chartData} />
              </div>
            )}

            {/* 最終更新時刻 */}
            {lastUpdate && (
              <div style={{ 
                textAlign: 'right', 
                marginBottom: '1rem',
                color: '#888',
                fontSize: '0.875rem'
              }}>
                最終更新: {formatTimestamp(lastUpdate.toISOString())}
              </div>
            )}

            {/* データテーブル */}
            <div style={{
              backgroundColor: '#2a2a2a',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse'
                }}>
                  <thead>
                    <tr style={{ backgroundColor: '#333' }}>
                      <th style={{ 
                        padding: '1rem',
                        textAlign: 'left',
                        fontSize: '0.875rem',
                        color: '#888',
                        borderBottom: '1px solid #444'
                      }}>
                        時刻
                      </th>
                      <th style={{ 
                        padding: '1rem',
                        textAlign: 'right',
                        fontSize: '0.875rem',
                        color: '#888',
                        borderBottom: '1px solid #444'
                      }}>
                        売り板 (BTC)
                      </th>
                      <th style={{ 
                        padding: '1rem',
                        textAlign: 'right',
                        fontSize: '0.875rem',
                        color: '#888',
                        borderBottom: '1px solid #444'
                      }}>
                        買い板 (BTC)
                      </th>
                      <th style={{ 
                        padding: '1rem',
                        textAlign: 'right',
                        fontSize: '0.875rem',
                        color: '#888',
                        borderBottom: '1px solid #444'
                      }}>
                        価格 (USD)
                      </th>
                      <th style={{ 
                        padding: '1rem',
                        textAlign: 'right',
                        fontSize: '0.875rem',
                        color: '#888',
                        borderBottom: '1px solid #444'
                      }}>
                        買い/売り比率
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((record, index) => {
                      const ratio = (record.bid_total / record.ask_total).toFixed(2)
                      return (
                        <tr key={record.id} style={{
                          backgroundColor: index % 2 === 0 ? 'transparent' : '#252525',
                          transition: 'background-color 0.2s'
                        }}>
                          <td style={{ 
                            padding: '0.75rem 1rem',
                            fontSize: '0.875rem',
                            borderBottom: '1px solid #333'
                          }}>
                            {formatTimestamp(record.timestamp)}
                          </td>
                          <td style={{ 
                            padding: '0.75rem 1rem',
                            textAlign: 'right',
                            fontSize: '0.875rem',
                            color: '#f87171',
                            borderBottom: '1px solid #333'
                          }}>
                            {record.ask_total.toLocaleString()}
                          </td>
                          <td style={{ 
                            padding: '0.75rem 1rem',
                            textAlign: 'right',
                            fontSize: '0.875rem',
                            color: '#4ade80',
                            borderBottom: '1px solid #333'
                          }}>
                            {record.bid_total.toLocaleString()}
                          </td>
                          <td style={{ 
                            padding: '0.75rem 1rem',
                            textAlign: 'right',
                            fontSize: '0.875rem',
                            borderBottom: '1px solid #333'
                          }}>
                            {formatPrice(record.price)}
                          </td>
                          <td style={{ 
                            padding: '0.75rem 1rem',
                            textAlign: 'right',
                            fontSize: '0.875rem',
                            color: parseFloat(ratio) >= 1 ? '#4ade80' : '#f87171',
                            fontWeight: 'bold',
                            borderBottom: '1px solid #333'
                          }}>
                            {ratio}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ 
              textAlign: 'center', 
              marginTop: '2rem',
              color: '#888',
              fontSize: '0.875rem'
            }}>
              最新{data.length}件のデータを表示中
            </div>
          </>
        )}
      </div>
    </main>
  )
}