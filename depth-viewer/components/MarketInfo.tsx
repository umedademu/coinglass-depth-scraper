import React from 'react'
import { OrderBookData } from '@/lib/supabase'
import { InterpolatedOrderBookData } from '@/lib/dataInterpolation'

interface MarketInfoProps {
  latestData: OrderBookData | null
  hoveredData?: InterpolatedOrderBookData | null
  compact?: boolean
}

const MarketInfo = React.memo(function MarketInfo({ latestData, hoveredData, compact = false }: MarketInfoProps) {
  const displayData = hoveredData || latestData
  
  if (!displayData) {
    return (
      <div style={{
        padding: '1.5rem',
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#999' }}>データを読み込み中...</div>
      </div>
    )
  }

  const ratio = displayData.bid_total / displayData.ask_total
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    const year = (date.getFullYear() % 100).toString().padStart(2, '0')
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${year}/${month}/${day} ${hours}:${minutes}`
  }

  // コンパクトモード
  if (compact) {
    return (
      <div style={{
        display: 'flex',
        gap: '1.5rem',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#999', fontSize: '0.9rem' }}>価格:</span>
          <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#fff' }}>
            ${displayData.price.toLocaleString()}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#999', fontSize: '0.9rem' }}>売り:</span>
          <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#f87171' }}>
            {displayData.ask_total.toLocaleString()}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#999', fontSize: '0.9rem' }}>買い:</span>
          <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#4ade80' }}>
            {displayData.bid_total.toLocaleString()}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#999', fontSize: '0.9rem' }}>比率:</span>
          <span style={{ 
            fontSize: '1.1rem', 
            fontWeight: '600', 
            color: ratio > 1 ? '#4ade80' : '#f87171' 
          }}>
            {ratio.toFixed(2)}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#999', fontSize: '0.9rem' }}>日時:</span>
          <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#fff' }}>
            {formatDate(displayData.timestamp)}
          </span>
        </div>
      </div>
    )
  }

  // 通常モード
  return (
    <div style={{
      padding: '1.5rem',
      backgroundColor: '#2a2a2a',
      borderRadius: '8px',
      marginBottom: '1rem'
    }}>
      <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>現在の市場情報</h2>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            最新価格
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>
            ${displayData.price.toLocaleString()}
          </div>
        </div>

        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            売り板総量
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f87171' }}>
            {displayData.ask_total.toLocaleString()} BTC
          </div>
        </div>

        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            買い板総量
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4ade80' }}>
            {displayData.bid_total.toLocaleString()} BTC
          </div>
        </div>

        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            買い/売り比率
          </div>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: ratio > 1 ? '#4ade80' : '#f87171' 
          }}>
            {ratio.toFixed(2)}
          </div>
        </div>
      </div>

      <div style={{ 
        marginTop: '1rem', 
        paddingTop: '1rem', 
        borderTop: '1px solid #444',
        color: '#999',
        fontSize: '0.9rem'
      }}>
        日時: {formatDate(displayData.timestamp)}
      </div>
    </div>
  )
})

export default MarketInfo