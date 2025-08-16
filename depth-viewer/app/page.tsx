'use client'

import { useEffect, useState } from 'react'
import { supabase, OrderBookData } from '../lib/supabase'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<OrderBookData[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      console.log('Connecting to Supabase...')
      
      // 最新10件のデータを取得
      const { data, error } = await supabase
        .from('order_book_shared')
        .select('*')
        .eq('group_id', 'default-group')
        .order('timestamp', { ascending: false })
        .limit(10)

      if (error) {
        console.error('Error fetching data:', error)
        setError(error.message)
      } else {
        console.log('✅ Supabase connected successfully')
        console.log('Data retrieved:', data)
        console.log('====================')
        console.log('Latest 10 records:')
        data?.forEach((record, index) => {
          console.log(`${index + 1}. Timestamp: ${record.timestamp}`)
          console.log(`   Ask Total: ${record.ask_total} BTC`)
          console.log(`   Bid Total: ${record.bid_total} BTC`)
          console.log(`   Price: $${record.price}`)
          console.log('---')
        })
        setData(data || [])
      }
    } catch (err) {
      console.error('Unexpected error:', err)
      setError('Unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#1a1a1a',
      color: '#ffffff',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>
        Depth Viewer - Supabase Connection Test
      </h1>
      
      {loading && (
        <p style={{ color: '#888' }}>
          Connecting to Supabase...
        </p>
      )}
      
      {!loading && !error && (
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#4ade80', marginBottom: '1rem' }}>
            ✅ Supabase connected successfully!
          </p>
          <p style={{ color: '#888' }}>
            Retrieved {data.length} records - Check console for details (F12)
          </p>
        </div>
      )}
      
      {error && (
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#f87171', marginBottom: '1rem' }}>
            ❌ Connection Error
          </p>
          <p style={{ color: '#888' }}>
            {error}
          </p>
        </div>
      )}
    </main>
  )
}