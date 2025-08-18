'use client'

import { useEffect, useState } from 'react'
import { fetchTimeframeData, OrderBookData } from '@/lib/supabase'
import MarketInfo from '@/components/MarketInfo'
import UnifiedChart from '@/components/UnifiedChart'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<OrderBookData[]>([])
  const [latestData, setLatestData] = useState<OrderBookData | null>(null)

  useEffect(() => {
    async function loadData() {
      console.log('=== 第4段階：グラフ基本操作とUI整理 ===')
      
      try {
        // デフォルト時間足（1時間足）から最新1000件のデータを取得
        console.log('📊 1時間足データを取得中...')
        const orderBookData = await fetchTimeframeData('1hour', 1000)
        
        console.log(`✅ ${orderBookData.length}件のデータを取得しました`)
        
        if (orderBookData.length > 0) {
          setData(orderBookData)
          setLatestData(orderBookData[orderBookData.length - 1])
          
          // デバッグ情報をコンソールに出力
          console.log('最新データ:', {
            timestamp: orderBookData[orderBookData.length - 1].timestamp,
            price: orderBookData[orderBookData.length - 1].price,
            ask_total: orderBookData[orderBookData.length - 1].ask_total,
            bid_total: orderBookData[orderBookData.length - 1].bid_total,
            ratio: orderBookData[orderBookData.length - 1].bid_total / 
                   orderBookData[orderBookData.length - 1].ask_total
          })
          
          console.log('最古データ:', {
            timestamp: orderBookData[0].timestamp,
            price: orderBookData[0].price
          })
        }
        
        setLoading(false)
      } catch (err) {
        console.error('❌ データ取得エラー:', err)
        setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
        setLoading(false)
      }
    }

    loadData()
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
        Depth Viewer - 第4段階：グラフ基本操作とUI整理
      </h1>
      
      {/* 市場情報の表示 */}
      <MarketInfo latestData={latestData} />
      
      {/* 統合グラフの表示（ズーム・パン機能付き） */}
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
        <div>📊 取得データ数: {data.length}件</div>
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