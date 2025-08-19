'use client'

import { useEffect, useState, useCallback } from 'react'
import { fetchTimeframeData, OrderBookData, TimeframeKey } from '@/lib/supabase'
import { interpolateMissingData, InterpolatedOrderBookData, detectMissingSlots } from '@/lib/dataInterpolation'
import MarketInfo from '@/components/MarketInfo'
import TimeframeSelector from '@/components/TimeframeSelector'
import UnifiedChart from '@/components/UnifiedChart'

// データキャッシュの型定義
interface CacheEntry {
  data: InterpolatedOrderBookData[]
  timestamp: number
  stats?: {
    originalCount: number
    interpolatedCount: number
    totalCount: number
    interpolationRate: number
  }
}

// localStorage のキー
const LOCALSTORAGE_TIMEFRAME_KEY = 'depth-viewer-timeframe'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [timeframeLoading, setTimeframeLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<InterpolatedOrderBookData[]>([])
  const [latestData, setLatestData] = useState<OrderBookData | null>(null)
  
  // localStorageから初期値を取得
  const getInitialTimeframe = (): TimeframeKey => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(LOCALSTORAGE_TIMEFRAME_KEY)
      if (saved && ['5min', '15min', '30min', '1hour', '2hour', '4hour', '1day'].includes(saved)) {
        return saved as TimeframeKey
      }
    }
    return '1hour' // デフォルト
  }
  
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeKey>(getInitialTimeframe)
  
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
        
        // キャッシュに保存
        const cacheEntry: CacheEntry = {
          data: interpolatedData,
          timestamp: Date.now(),
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
  }, [selectedTimeframe, loadTimeframeData])

  // 初期データ読み込み
  useEffect(() => {
    async function loadInitialData() {
      console.log('=== 第5段階：タイムフレーム切り替え（遅延読み込み版） ===')
      
      try {
        await loadTimeframeData(selectedTimeframe)
        setLoading(false)
      } catch (err) {
        console.error('❌ 初期データ取得エラー:', err)
        setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
        setLoading(false)
      }
    }

    loadInitialData()
  }, [])

  if (loading) {
    return (
      <main style={{ 
        padding: '2rem',
        minHeight: '100vh',
        backgroundColor: '#0a0a0a'
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh'
        }}>
          <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
            ⏳ データを読み込み中...
          </div>
          <div style={{ color: '#999' }}>
            1時間足データ（最新1000件）を取得しています
          </div>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main style={{ 
        padding: '2rem',
        minHeight: '100vh',
        backgroundColor: '#0a0a0a'
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh'
        }}>
          <div style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#f87171' }}>
            ❌ エラーが発生しました
          </div>
          <div style={{ color: '#999' }}>
            {error}
          </div>
        </div>
      </main>
    )
  }

  return (
    <main style={{ 
      padding: '2rem',
      minHeight: '100vh',
      backgroundColor: '#0a0a0a'
    }}>
      <h1 style={{ 
        marginBottom: '2rem',
        fontSize: '2rem',
        fontWeight: 'bold'
      }}>
        Depth Viewer - 第5段階：タイムフレーム切り替え
      </h1>
      
      {/* UI配置の最適化: 市場情報 → タイムフレーム選択 → グラフ の順序 */}
      
      {/* 市場情報の表示（最上部） */}
      <MarketInfo latestData={latestData} />
      
      {/* タイムフレーム選択（その下） */}
      <TimeframeSelector 
        selectedTimeframe={selectedTimeframe}
        onTimeframeChange={handleTimeframeChange}
        loading={timeframeLoading}
      />
      
      {/* 統合グラフの表示（その下） */}
      <UnifiedChart data={data} />
      
      {/* データ統計情報 */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: '#1e1e1e',
        borderRadius: '8px',
        color: '#999',
        fontSize: '0.9rem'
      }}>
        <div>📊 表示データ数: {data.length}件</div>
        <div>⏱️ タイムフレーム: {selectedTimeframe}</div>
        {dataCache[selectedTimeframe]?.stats && (
          <>
            <div>📊 補完後: {dataCache[selectedTimeframe]?.stats.totalCount}件（実データ: {dataCache[selectedTimeframe]?.stats.originalCount}件, 補間: {dataCache[selectedTimeframe]?.stats.interpolatedCount}件, 補間率: {dataCache[selectedTimeframe]?.stats.interpolationRate.toFixed(1)}%）</div>
          </>
        )}
        {data.length > 0 && (
          <>
            <div>🕐 データ期間: {new Date(data[0].timestamp).toLocaleString('ja-JP')} ～ {new Date(data[data.length - 1].timestamp).toLocaleString('ja-JP')}</div>
            <div>🖱️ マウスホイール: ズーム | ドラッグ: パン（移動）</div>
          </>
        )}
      </div>
    </main>
  )
}