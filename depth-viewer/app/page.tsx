'use client'

import { useEffect, useState } from 'react'
import { fetchTimeframeData, timeframes, OrderBookData } from '@/lib/supabase'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function testConnection() {
      console.log('=== Supabase Connection Test Started ===')
      
      try {
        // 接続成功メッセージ
        console.log('✅ Supabase connected successfully')
        console.log('Fetching data from all timeframe tables...\n')

        // 各時間足テーブルからデータを取得
        for (const timeframe of timeframes) {
          console.log(`\n📊 ${timeframe.label} (${timeframe.table}):`)
          console.log('----------------------------------------')
          
          const data = await fetchTimeframeData(timeframe.key, 10)
          
          if (data.length > 0) {
            console.log(`✓ Found ${data.length} records`)
            console.log('Latest 3 records:')
            
            // 最新3件のデータを表示
            data.slice(0, 3).forEach((record, index) => {
              console.log(`  ${index + 1}. Timestamp: ${record.timestamp}`)
              console.log(`     Ask Total: ${record.ask_total.toLocaleString()} BTC`)
              console.log(`     Bid Total: ${record.bid_total.toLocaleString()} BTC`)
              console.log(`     Price: $${record.price.toLocaleString()}`)
              console.log(`     Ratio: ${(record.bid_total / record.ask_total).toFixed(2)}`)
            })
          } else {
            console.log('⚠️ No data found in this table')
          }
        }

        console.log('\n=== Connection Test Completed Successfully ===')
        setLoading(false)
      } catch (err) {
        console.error('❌ Connection failed:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
        setLoading(false)
      }
    }

    testConnection()
  }, [])

  return (
    <main style={{ padding: '2rem' }}>
      <h1 style={{ marginBottom: '2rem' }}>Depth Viewer - 第1段階：Supabase接続確認</h1>
      
      <div style={{ 
        padding: '1.5rem',
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        marginBottom: '1rem'
      }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>接続状態</h2>
        {loading && <p>⏳ Supabaseに接続中...</p>}
        {!loading && !error && (
          <p style={{ color: '#4ade80' }}>✅ 接続成功！コンソールを確認してください（F12）</p>
        )}
        {error && (
          <p style={{ color: '#f87171' }}>❌ エラー: {error}</p>
        )}
      </div>

      <div style={{ 
        padding: '1.5rem',
        backgroundColor: '#1e1e1e',
        borderRadius: '8px',
        fontFamily: 'monospace',
        fontSize: '0.9rem'
      }}>
        <h3 style={{ marginBottom: '0.5rem' }}>確認手順：</h3>
        <ol style={{ marginLeft: '1.5rem', lineHeight: '1.8' }}>
          <li>F12キーで開発者コンソールを開く</li>
          <li>「Console」タブを選択</li>
          <li>以下が表示されることを確認：
            <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
              <li>&quot;Supabase connected successfully&quot;</li>
              <li>各時間足テーブルからのデータ</li>
              <li>エラーが表示されていないこと</li>
            </ul>
          </li>
        </ol>
      </div>
    </main>
  )
}