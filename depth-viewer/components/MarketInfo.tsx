import React from 'react'
import { OrderBookData } from '@/lib/supabase'
import { InterpolatedOrderBookData } from '@/lib/dataInterpolation'

interface MarketInfoProps {
  latestData: OrderBookData | null
  hoveredData?: InterpolatedOrderBookData | null
  compact?: boolean
  isMobile?: boolean
}

const MarketInfo = React.memo(function MarketInfo({ latestData, hoveredData, compact = false, isMobile = false }: MarketInfoProps) {
  const displayData = hoveredData || latestData
  
  if (!displayData) {
    return (
      <div className="glass-card" style={{ padding: '24px', marginBottom: '16px', animation: 'pulse 2s infinite' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="loading-spinner" style={{ width: '20px', height: '20px' }} />
          <span style={{ color: '#9ca3af' }}>データを読み込み中...</span>
        </div>
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

  const getPriceChangeIcon = () => {
    if (!latestData || !hoveredData) return null
    const diff = hoveredData.price - latestData.price
    if (Math.abs(diff) < 0.01) return null
    return diff > 0 ? '↑' : '↓'
  }

  const getRatioStatus = (ratio: number) => {
    if (ratio > 1.5) return { color: 'text-green-400', bg: 'bg-green-500/20', label: 'Bullish' }
    if (ratio < 0.7) return { color: 'text-red-400', bg: 'bg-red-500/20', label: 'Bearish' }
    return { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'Neutral' }
  }

  const ratioStatus = getRatioStatus(ratio)

  // コンパクトモード
  if (compact) {
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: isMobile ? '8px' : '16px', alignItems: 'center' }}>
        <div className="data-card" style={{ padding: isMobile ? '4px' : undefined }}>
          <span className="metric-label" style={{ fontSize: isMobile ? '10px' : undefined }}>価格</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span className="metric-value" style={{ fontSize: isMobile ? '14px' : '20px' }}>
              ${displayData.price.toLocaleString()}
            </span>
            {getPriceChangeIcon() && (
              <span style={{ 
                fontSize: isMobile ? '12px' : '18px', 
                color: getPriceChangeIcon() === '↑' ? '#10b981' : '#ef4444' 
              }}>
                {getPriceChangeIcon()}
              </span>
            )}
          </div>
        </div>
        
        <div className="data-card" style={{ padding: isMobile ? '4px' : undefined }}>
          <span className="metric-label" style={{ fontSize: isMobile ? '10px' : undefined }}>売り板</span>
          <span style={{ fontSize: isMobile ? '14px' : '20px', fontWeight: 'bold', color: '#ef4444' }}>
            {displayData.ask_total.toLocaleString()}
          </span>
        </div>
        
        <div className="data-card" style={{ padding: isMobile ? '4px' : undefined }}>
          <span className="metric-label" style={{ fontSize: isMobile ? '10px' : undefined }}>買い板</span>
          <span style={{ fontSize: isMobile ? '14px' : '20px', fontWeight: 'bold', color: '#10b981' }}>
            {displayData.bid_total.toLocaleString()}
          </span>
        </div>
        
        <div className="data-card" style={{ padding: isMobile ? '4px' : undefined }}>
          <span className="metric-label" style={{ fontSize: isMobile ? '10px' : undefined }}>比率</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: isMobile ? '14px' : '20px', fontWeight: 'bold', color: ratioStatus.color.replace('text-', '#').replace('green-400', '10b981').replace('red-400', 'ef4444').replace('yellow-400', 'fbbf24') }}>
              {ratio.toFixed(2)}
            </span>
            {!isMobile && (
            <span style={{
              padding: '2px 8px',
              borderRadius: '9999px',
              fontSize: '12px',
              fontWeight: '500',
              backgroundColor: ratioStatus.bg.replace('bg-', 'rgba(').replace('green-500/20', '16, 185, 129, 0.2)').replace('red-500/20', '239, 68, 68, 0.2)').replace('yellow-500/20', '245, 158, 11, 0.2)'),
              color: ratioStatus.color.replace('text-', '#').replace('green-400', '10b981').replace('red-400', 'ef4444').replace('yellow-400', 'fbbf24')
            }}>
              {ratioStatus.label}
            </span>
            )}
          </div>
        </div>
        
        {!isMobile && (
        <div className="data-card">
          <span className="metric-label">更新時刻</span>
          <span className="font-mono" style={{ fontSize: '18px', color: '#d1d5db' }}>
            {formatDate(displayData.timestamp)}
          </span>
        </div>
        )}
        
        {hoveredData?.isInterpolated && (
          <div style={{
            padding: '4px 12px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(245, 158, 11, 0.2)',
            border: '1px solid rgba(245, 158, 11, 0.5)'
          }}>
            <span style={{ fontSize: '12px', fontWeight: '500', color: '#fbbf24' }}>補間データ</span>
          </div>
        )}
      </div>
    )
  }

  // 通常モード
  return (
    <div className="glass-card fade-in" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <h2 className="gradient-text" style={{ fontSize: '20px', fontWeight: 'bold' }}>市場情報</h2>
        <div className={`status-indicator ${hoveredData ? 'status-connecting' : 'status-connected'}`}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'currentColor', display: 'inline-block', animation: 'pulse 2s infinite' }} />
          <span>{hoveredData ? 'ホバー中' : 'ライブ'}</span>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="data-card" style={{ transition: 'transform 0.3s', cursor: 'pointer' }}>
          <div className="metric-label" style={{ marginBottom: '8px' }}>最新価格</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <div className="metric-value">
              ${displayData.price.toLocaleString()}
            </div>
            {getPriceChangeIcon() && (
              <span style={{ fontSize: '20px', color: getPriceChangeIcon() === '↑' ? '#10b981' : '#ef4444', animation: 'pulse 2s infinite' }}>
                {getPriceChangeIcon()}
              </span>
            )}
          </div>
        </div>

        <div className="data-card" style={{ transition: 'transform 0.3s', cursor: 'pointer' }}>
          <div className="metric-label" style={{ marginBottom: '8px' }}>売り板総量</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
              {displayData.ask_total.toLocaleString()}
            </span>
            <span style={{ fontSize: '14px', color: '#9ca3af' }}>BTC</span>
          </div>
        </div>

        <div className="data-card" style={{ transition: 'transform 0.3s', cursor: 'pointer' }}>
          <div className="metric-label" style={{ marginBottom: '8px' }}>買い板総量</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
              {displayData.bid_total.toLocaleString()}
            </span>
            <span style={{ fontSize: '14px', color: '#9ca3af' }}>BTC</span>
          </div>
        </div>

        <div className="data-card" style={{ transition: 'transform 0.3s', cursor: 'pointer' }}>
          <div className="metric-label" style={{ marginBottom: '8px' }}>買い/売り比率</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: ratioStatus.color.replace('text-', '#').replace('green-400', '10b981').replace('red-400', 'ef4444').replace('yellow-400', 'fbbf24') }}>
              {ratio.toFixed(2)}
            </div>
            <div style={{
              display: 'inline-flex',
              width: 'fit-content',
              padding: '4px 8px',
              borderRadius: '9999px',
              fontSize: '12px',
              fontWeight: '500',
              backgroundColor: ratioStatus.bg.replace('bg-', 'rgba(').replace('green-500/20', '16, 185, 129, 0.2)').replace('red-500/20', '239, 68, 68, 0.2)').replace('yellow-500/20', '245, 158, 11, 0.2)'),
              color: ratioStatus.color.replace('text-', '#').replace('green-400', '10b981').replace('red-400', 'ef4444').replace('yellow-400', 'fbbf24')
            }}>
              {ratioStatus.label}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#9ca3af' }}>
          <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-mono">{formatDate(displayData.timestamp)}</span>
        </div>
        {hoveredData?.isInterpolated && (
          <div style={{
            padding: '4px 12px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(245, 158, 11, 0.2)',
            border: '1px solid rgba(245, 158, 11, 0.5)'
          }}>
            <span style={{ fontSize: '12px', fontWeight: '500', color: '#fbbf24' }}>補間データ</span>
          </div>
        )}
      </div>
    </div>
  )
})

export default MarketInfo