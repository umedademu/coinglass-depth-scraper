'use client'

import { useEffect, useState } from 'react'
import { supabase, OrderBookData } from '../lib/supabase'
import dynamic from 'next/dynamic'

// Chart.jsはSSRと互換性がないため、動的インポートを使用
const OrderBookChart = dynamic(() => import('../components/OrderBookChart'), {
  ssr: false,
  loading: () => <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>グラフを読み込み中...</div>
})

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<OrderBookData[]>([])
  const [chartData, setChartData] = useState<OrderBookData[]>([]) // グラフ用データ（300件）
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      console.log('Fetching data from Supabase...')
      
      // テーブル表示用：最新100件のデータを取得
      const { data: tableData, error: tableError } = await supabase
        .from('order_book_shared')
        .select('*')
        .eq('group_id', 'default-group')
        .order('timestamp', { ascending: false })
        .limit(100)

      // グラフ表示用：最新300件のデータを取得
      const { data: graphData, error: graphError } = await supabase
        .from('order_book_shared')
        .select('*')
        .eq('group_id', 'default-group')
        .order('timestamp', { ascending: false })
        .limit(300)

      if (tableError || graphError) {
        console.error('Error fetching data:', tableError || graphError)
        setError((tableError || graphError)?.message || 'Error fetching data')
      } else {
        console.log('✅ Data fetched successfully:', tableData?.length, 'table records,', graphData?.length, 'graph records')
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
        <h1 style={{ fontSize: '2rem', marginBottom: '2rem', textAlign: 'center' }}>
          Depth Viewer - BTC-USDT Order Book
        </h1>
        
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