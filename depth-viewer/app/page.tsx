'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { fetchTimeframeData, OrderBookData, TimeframeKey, supabase, timeframes } from '@/lib/supabase'
import { interpolateMissingData, InterpolatedOrderBookData, detectMissingSlots } from '@/lib/dataInterpolation'
import MarketInfo from '@/components/MarketInfo'
import TimeframeSelector from '@/components/TimeframeSelector'
import UnifiedChart, { UnifiedChartRef } from '@/components/UnifiedChart'
import LoadingScreen from '@/components/LoadingScreen'
import ErrorScreen from '@/components/ErrorScreen'

// データキャッシュの型定義
interface CacheEntry {
  data: InterpolatedOrderBookData[]
  timestamp: number
  oldestTimestamp?: string  // 最古のタイムスタンプを追加
  isLoadingMore?: boolean    // 追加データ読み込み中フラグ
  hasMore?: boolean         // さらにデータがあるかのフラグ
  stats?: {
    originalCount: number
    interpolatedCount: number
    totalCount: number
    interpolationRate: number
  }
}

// localStorage のキー
const LOCALSTORAGE_TIMEFRAME_KEY = 'depth-viewer-timeframe'

// 接続状態の型定義
type ConnectionStatus = 'connected' | 'connecting' | 'disconnected'

// データ最大保持数
const MAX_DATA_POINTS = 5000

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [timeframeLoading, setTimeframeLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<InterpolatedOrderBookData[]>([])
  const [latestData, setLatestData] = useState<OrderBookData | null>(null)
  const [hoveredData, setHoveredData] = useState<InterpolatedOrderBookData | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  
  // リアルタイム関連の状態
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const channelRef = useRef<any>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const chartRef = useRef<UnifiedChartRef>(null) // Chartコンポーネントへの参照
  
  // localStorageから初期値を取得（useEffect内で実行）
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeKey>('1hour')
  
  // レスポンシブデザインの対応
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    // localStorageから設定を復元
    const saved = localStorage.getItem(LOCALSTORAGE_TIMEFRAME_KEY)
    if (saved && ['5min', '15min', '30min', '1hour', '2hour', '4hour', '1day'].includes(saved)) {
      setSelectedTimeframe(saved as TimeframeKey)
    }
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // データキャッシュ（メモリ内）
  const [dataCache, setDataCache] = useState<Record<TimeframeKey, CacheEntry | null>>({
    '5min': null,
    '15min': null,
    '30min': null,
    '1hour': null,
    '2hour': null,
    '4hour': null,
    '1day': null
  })

  // 時間足データを取得する関数
  const loadTimeframeData = useCallback(async (timeframe: TimeframeKey) => {
    console.log(`=== 第5段階：タイムフレーム切り替え（${timeframe}） ===`)
    
    // キャッシュチェック
    const cached = dataCache[timeframe]
    if (cached && cached.data.length > 0) {
      console.log(`✅ キャッシュからデータを読み込み（${cached.data.length}件）`)
      setData(cached.data)
      
      // 最新データを更新
      const realData = cached.data.filter(d => !d.isInterpolated)
      if (realData.length > 0) {
        setLatestData(realData[realData.length - 1])
      }
      
      // キャッシュの統計情報を表示
      if (cached.stats) {
        console.log(`📊 補完統計（キャッシュ）:`)
        console.log(`  - 実データ数: ${cached.stats.originalCount}件`)
        console.log(`  - 補間データ数: ${cached.stats.interpolatedCount}件`)
        console.log(`  - 合計データ数: ${cached.stats.totalCount}件`)
        console.log(`  - 補間率: ${cached.stats.interpolationRate.toFixed(1)}%`)
      }
      
      return
    }
    
    setTimeframeLoading(true)
    
    try {
      // データを取得
      console.log(`📊 ${timeframe}データを取得中...`)
      const orderBookData = await fetchTimeframeData(timeframe, 1000)
      
      console.log(`✅ ${orderBookData.length}件のデータを取得しました`)
      
      if (orderBookData.length > 0) {
        // データ欠損の検出
        detectMissingSlots(orderBookData, timeframe)
        
        // データの補完処理
        const { interpolatedData, stats } = interpolateMissingData(orderBookData, timeframe)
        
        // 最古のタイムスタンプを取得
        const oldestTimestamp = orderBookData[0].timestamp
        
        // キャッシュに保存
        const cacheEntry: CacheEntry = {
          data: interpolatedData,
          timestamp: Date.now(),
          oldestTimestamp,
          hasMore: orderBookData.length === 1000, // 1000件取得できた場合はまだデータがある可能性
          stats
        }
        
        setDataCache(prev => ({
          ...prev,
          [timeframe]: cacheEntry
        }))
        
        setData(interpolatedData)
        
        // 最新の実データを取得
        const realData = interpolatedData.filter(d => !d.isInterpolated)
        if (realData.length > 0) {
          setLatestData(realData[realData.length - 1])
        }
        
        // デバッグ情報
        if (interpolatedData.length > 0) {
          console.log('最新データ:', {
            timestamp: interpolatedData[interpolatedData.length - 1].timestamp,
            price: interpolatedData[interpolatedData.length - 1].price,
            isInterpolated: interpolatedData[interpolatedData.length - 1].isInterpolated
          })
          
          console.log('最古データ:', {
            timestamp: interpolatedData[0].timestamp,
            price: interpolatedData[0].price,
            isInterpolated: interpolatedData[0].isInterpolated
          })
        }
      } else {
        setData([])
        setLatestData(null)
      }
      
    } catch (err) {
      console.error('❌ データ取得エラー:', err)
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
    } finally {
      setTimeframeLoading(false)
    }
  }, [dataCache])

  // 過去データを追加取得する関数（第7段階：無限スクロール）
  const loadOlderData = useCallback(async (): Promise<InterpolatedOrderBookData[]> => {
    console.log('=== 第7段階：過去データ取得 ===')
    
    const cache = dataCache[selectedTimeframe]
    if (!cache || !cache.oldestTimestamp || cache.isLoadingMore || !cache.hasMore) {
      console.log('過去データ取得をスキップ（条件不足）')
      return []
    }
    
    // ローディング中フラグを立てる
    setDataCache(prev => ({
      ...prev,
      [selectedTimeframe]: {
        ...prev[selectedTimeframe]!,
        isLoadingMore: true
      }
    }))
    
    try {
      // 追加で1000件取得
      console.log(`📊 ${selectedTimeframe}の過去データを取得中...`)
      console.log(`  最古タイムスタンプ: ${cache.oldestTimestamp}`)
      
      const olderData = await fetchTimeframeData(selectedTimeframe, 1000, cache.oldestTimestamp)
      
      console.log(`✅ ${olderData.length}件の過去データを取得しました`)
      
      if (olderData.length > 0) {
        // データ補完処理
        const { interpolatedData, stats } = interpolateMissingData(olderData, selectedTimeframe)
        
        // 新しい最古のタイムスタンプ
        const newOldestTimestamp = olderData[0].timestamp
        
        // 既存データと結合（古いデータを前に）
        let combinedData = [...interpolatedData, ...cache.data]
        
        // メモリ管理：5000件を超えた場合は新しいデータから削除
        if (combinedData.length > MAX_DATA_POINTS) {
          console.log(`⚠️ データ数が${MAX_DATA_POINTS}件を超えたため、新しいデータを削除します`)
          combinedData = combinedData.slice(0, MAX_DATA_POINTS)
        }
        
        // キャッシュを更新
        setDataCache(prev => ({
          ...prev,
          [selectedTimeframe]: {
            data: combinedData,
            timestamp: Date.now(),
            oldestTimestamp: newOldestTimestamp,
            hasMore: olderData.length === 1000, // 1000件取得できた場合はまだデータがある
            isLoadingMore: false,
            stats: {
              originalCount: (cache.stats?.originalCount || 0) + stats.originalCount,
              interpolatedCount: (cache.stats?.interpolatedCount || 0) + stats.interpolatedCount,
              totalCount: combinedData.length,
              interpolationRate: ((cache.stats?.interpolatedCount || 0) + stats.interpolatedCount) / combinedData.length * 100
            }
          }
        }))
        
        // 表示データも更新
        setData(combinedData)
        
        console.log(`📊 データ統合完了:`)
        console.log(`  - 追加データ: ${interpolatedData.length}件`)
        console.log(`  - 合計データ: ${combinedData.length}件`)
        console.log(`  - 新しい最古タイムスタンプ: ${newOldestTimestamp}`)
        
        return interpolatedData
      } else {
        // もうデータがない
        setDataCache(prev => ({
          ...prev,
          [selectedTimeframe]: {
            ...prev[selectedTimeframe]!,
            hasMore: false,
            isLoadingMore: false
          }
        }))
        
        console.log('これ以上過去のデータはありません')
        return []
      }
    } catch (err) {
      console.error('❌ 過去データ取得エラー:', err)
      
      // エラー時はローディングフラグを解除
      setDataCache(prev => ({
        ...prev,
        [selectedTimeframe]: {
          ...prev[selectedTimeframe]!,
          isLoadingMore: false
        }
      }))
      
      return []
    }
  }, [selectedTimeframe, dataCache])

  // リアルタイムデータ処理
  const handleRealtimeData = useCallback((newData: OrderBookData) => {
    console.log('📡 リアルタイムデータ受信:', {
      timestamp: newData.timestamp,
      price: newData.price,
      ask: newData.ask_total,
      bid: newData.bid_total
    })
    
    // Chart.jsインスタンスに直接データを追加（ズーム状態を維持）
    if (chartRef.current) {
      const interpolatedNewData: InterpolatedOrderBookData = {
        ...newData,
        isInterpolated: false
      }
      chartRef.current.addRealtimeData(interpolatedNewData)
    }
    
    // 最新データを更新（表示用）
    setLatestData(newData)
    
    // データ配列も更新（他のコンポーネント用）
    setData(prevData => {
      const interpolatedNewData: InterpolatedOrderBookData = {
        ...newData,
        isInterpolated: false
      }
      
      let updatedData = [...prevData, interpolatedNewData]
      
      // メモリ管理：最大保持数を超えた場合は古いデータを削除
      if (updatedData.length > MAX_DATA_POINTS) {
        console.log(`⚠️ データ数が${MAX_DATA_POINTS}件を超えたため、古いデータを削除します`)
        updatedData = updatedData.slice(updatedData.length - MAX_DATA_POINTS)
      }
      
      return updatedData
    })
    
    // キャッシュも更新
    setDataCache(prev => {
      const currentCache = prev[selectedTimeframe]
      if (currentCache) {
        const interpolatedNewData: InterpolatedOrderBookData = {
          ...newData,
          isInterpolated: false
        }
        
        let updatedCacheData = [...currentCache.data, interpolatedNewData]
        
        // キャッシュでもメモリ管理
        if (updatedCacheData.length > MAX_DATA_POINTS) {
          updatedCacheData = updatedCacheData.slice(updatedCacheData.length - MAX_DATA_POINTS)
        }
        
        return {
          ...prev,
          [selectedTimeframe]: {
            ...currentCache,
            data: updatedCacheData,
            timestamp: Date.now()
          }
        }
      }
      return prev
    })
  }, [selectedTimeframe])

  // Realtime購読の設定
  const setupRealtimeSubscription = useCallback((timeframe: TimeframeKey) => {
    // 既存のチャンネルをクリーンアップ
    if (channelRef.current) {
      supabase.removeChannel(channelRef.current)
      channelRef.current = null
    }
    
    // テーブル名を取得
    const table = timeframes.find(tf => tf.key === timeframe)?.table
    if (!table) {
      console.error(`❌ 無効なタイムフレーム: ${timeframe}`)
      return
    }
    
    console.log(`🔌 WebSocket接続を設定中... (${table})`)
    setConnectionStatus('connecting')
    
    // Realtimeチャンネルを作成
    const channel = supabase
      .channel(`${table}-changes`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: table,
          filter: 'group_id=eq.default-group'
        },
        (payload) => {
          handleRealtimeData(payload.new as OrderBookData)
        }
      )
      .subscribe((status) => {
        console.log(`📡 Realtime状態: ${status}`)
        
        if (status === 'SUBSCRIBED') {
          setConnectionStatus('connected')
          console.log('✅ WebSocket接続が確立されました')
          
          // 再接続タイマーをクリア
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
            reconnectTimeoutRef.current = null
          }
        } else if (status === 'CLOSED' || status === 'CHANNEL_ERROR') {
          setConnectionStatus('disconnected')
          console.log('❌ WebSocket接続が切断されました')
          
          // 自動再接続（5秒後）
          if (!reconnectTimeoutRef.current) {
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log('🔄 再接続を試みています...')
              setupRealtimeSubscription(timeframe)
            }, 5000)
          }
        }
      })
    
    channelRef.current = channel
  }, [handleRealtimeData])

  // タイムフレーム変更時の処理
  const handleTimeframeChange = useCallback((timeframe: TimeframeKey) => {
    console.log(`📊 タイムフレーム変更: ${selectedTimeframe} → ${timeframe}`)
    setSelectedTimeframe(timeframe)
    
    // localStorageに保存
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCALSTORAGE_TIMEFRAME_KEY, timeframe)
    }
    
    // データを読み込み
    loadTimeframeData(timeframe)
    
    // Realtime購読を再設定
    setupRealtimeSubscription(timeframe)
  }, [selectedTimeframe, loadTimeframeData, setupRealtimeSubscription])

  // 初期データ読み込み
  useEffect(() => {
    async function loadInitialData() {
      console.log('=== 第6段階：リアルタイム更新（ズーム状態維持版） ===')
      
      try {
        await loadTimeframeData(selectedTimeframe)
        setLoading(false)
        
        // Realtime購読を開始
        setupRealtimeSubscription(selectedTimeframe)
      } catch (err) {
        console.error('❌ 初期データ取得エラー:', err)
        setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
        setLoading(false)
      }
    }

    loadInitialData()
  }, [])
  
  // クリーンアップ処理
  useEffect(() => {
    return () => {
      // チャンネルをクリーンアップ
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
      }
      
      // 再接続タイマーをクリア
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }
  }, [])

  if (loading) {
    return <LoadingScreen />
  }

  if (error) {
    return (
      <ErrorScreen 
        error={error}
        onRetry={() => {
          setError(null)
          setLoading(true)
          loadTimeframeData(selectedTimeframe).then(() => {
            setLoading(false)
          }).catch(err => {
            setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
            setLoading(false)
          })
        }}
      />
    )
  }

  return (
    <main style={{ 
      height: isMobile ? '100vh' : 'auto',
      minHeight: isMobile ? 'unset' : '100vh',
      padding: isMobile ? '0' : '32px', 
      position: 'relative',
      overflow: isMobile ? 'hidden' : 'visible',
      display: isMobile ? 'flex' : 'block',
      flexDirection: isMobile ? 'column' : undefined,
      width: isMobile ? '100vw' : 'auto',
      maxWidth: isMobile ? '100vw' : undefined,
      margin: 0
    }}>
      
      {/* メインコンテンツ */}
      <div style={{ 
        position: 'relative', 
        zIndex: 10, 
        flex: isMobile ? 1 : undefined,
        display: isMobile ? 'flex' : 'block',
        flexDirection: isMobile ? 'column' : undefined,
        minHeight: 0
      }}>
        {/* タイムフレーム選択とマーケット情報 */}
        <div className="glass-card fade-in" style={{ 
          padding: isMobile ? '4px' : '24px', 
          marginBottom: isMobile ? '4px' : '24px',
          flexShrink: 0,
          borderRadius: isMobile ? 0 : undefined,
          margin: isMobile ? 0 : undefined,
          width: isMobile ? '100vw' : 'auto',
          maxWidth: isMobile ? '100vw' : undefined
        }}>
          <div style={{
            display: isMobile ? 'block' : 'flex',
            gap: isMobile ? '0' : '24px',
            alignItems: 'flex-start'
          }}>
            {/* タイムフレーム選択 */}
            <div style={{
              width: isMobile ? '100%' : 'auto',
              marginBottom: isMobile ? '4px' : '0'
            }}>
              <TimeframeSelector 
                selectedTimeframe={selectedTimeframe}
                onTimeframeChange={handleTimeframeChange}
                loading={timeframeLoading}
                isMobile={isMobile}
              />
            </div>
            
            {/* 市場情報と接続状態 */}
            <div style={{
              width: isMobile ? '100%' : 'auto',
              flex: isMobile ? 'none' : '1',
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}>
              <MarketInfo 
                latestData={latestData}
                hoveredData={hoveredData}
                compact={true}
                isMobile={isMobile}
              />
              {/* 接続状態インジケーター */}
              <div className={`
                status-indicator 
                ${connectionStatus === 'connected' ? 'status-connected' : 
                  connectionStatus === 'connecting' ? 'status-connecting' : 
                  'status-disconnected'}
              `} style={{ flexShrink: 0 }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'currentColor', display: 'inline-block' }} />
                <span style={{ fontSize: '10px' }}>
                  {connectionStatus === 'connected' ? '接続' :
                   connectionStatus === 'connecting' ? '接続中' : '切断'}
                </span>
              </div>
            </div>
          </div>
        </div>
      
        {/* チャートコンテナ */}
        <div className="chart-container slide-up" style={{ 
          marginBottom: isMobile ? 0 : '24px',
          flex: isMobile ? 1 : undefined,
          minHeight: 0,
          display: isMobile ? 'flex' : 'block',
          borderRadius: isMobile ? 0 : undefined,
          padding: isMobile ? 0 : undefined,
          border: isMobile ? 'none' : undefined,
          width: isMobile ? '100vw' : 'auto',
          maxWidth: isMobile ? '100vw' : undefined
        }}>
          <UnifiedChart 
            ref={chartRef} 
            data={data} 
            onLoadOlderData={loadOlderData}
            isLoadingMore={dataCache[selectedTimeframe]?.isLoadingMore || false}
            onHoverData={setHoveredData}
            isMobile={isMobile}
          />
        </div>
      
        {/* データ統計情報 - モバイルでは非表示 */}
        {!isMobile && (
        <div className="glass-card fade-in" style={{ padding: '24px' }}>
          <h3 className="gradient-text" style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>データ統計</h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            <div className="data-card">
              <span className="metric-label">表示データ数</span>
              <span className="metric-value" style={{ fontSize: '20px' }}>{data.length.toLocaleString()}</span>
            </div>
            
            <div className="data-card">
              <span className="metric-label">タイムフレーム</span>
              <span className="metric-value" style={{ fontSize: '20px' }}>{selectedTimeframe}</span>
            </div>
            
            {dataCache[selectedTimeframe]?.stats && (
              <div className="data-card">
                <span className="metric-label">データ品質</span>
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>
                    実データ: {dataCache[selectedTimeframe]?.stats.originalCount}件
                  </div>
                  <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>
                    補間: {dataCache[selectedTimeframe]?.stats.interpolatedCount}件
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: '500', color: '#fbbf24' }}>
                    補間率: {dataCache[selectedTimeframe]?.stats.interpolationRate.toFixed(1)}%
                  </div>
                </div>
              </div>
            )}
            
            {data.length > 0 && (
              <div className="data-card">
                <span className="metric-label">データ期間</span>
                <div className="font-mono" style={{ fontSize: '14px', color: '#d1d5db' }}>
                  {new Date(data[0].timestamp).toLocaleString('ja-JP', { 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                  <span style={{ color: '#6b7280', margin: '0 4px' }}>～</span>
                  {new Date(data[data.length - 1].timestamp).toLocaleString('ja-JP', { 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            )}
            
            <div className="data-card">
              <span className="metric-label">リアルタイム更新</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: connectionStatus === 'connected' ? '#10b981' : '#ef4444',
                  display: 'inline-block',
                  animation: connectionStatus === 'connected' ? 'pulse 2s infinite' : 'none'
                }} />
                <span style={{ fontSize: '14px', fontWeight: '500' }}>
                  {connectionStatus === 'connected' ? '有効' : connectionStatus === 'connecting' ? '接続中...' : '無効'}
                </span>
              </div>
            </div>
            
            {latestData && (
              <div className="data-card">
                <span className="metric-label">最終更新</span>
                <span className="font-mono" style={{ fontSize: '14px', color: '#d1d5db' }}>
                  {new Date(latestData.timestamp).toLocaleString('ja-JP', { 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                  })}
                </span>
              </div>
            )}
          </div>
          
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '12px', color: '#9ca3af' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span>マウスホイール: ズーム</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                <span>ドラッグ: パン（移動）</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
                <span>最大{MAX_DATA_POINTS.toLocaleString()}件保持</span>
              </div>
            </div>
          </div>
        </div>
        )}
      </div>
    </main>
  )
}