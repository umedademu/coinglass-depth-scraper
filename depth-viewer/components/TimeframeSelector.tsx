import React from 'react'
import { timeframes, TimeframeKey } from '@/lib/supabase'

interface TimeframeSelectorProps {
  selectedTimeframe: TimeframeKey
  onTimeframeChange: (timeframe: TimeframeKey) => void
  loading?: boolean
  isMobile?: boolean
}

const TimeframeSelector = React.memo(function TimeframeSelector({ 
  selectedTimeframe, 
  onTimeframeChange,
  loading = false,
  isMobile = false 
}: TimeframeSelectorProps) {
  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: isMobile ? '4px' : '8px', justifyContent: 'center', alignItems: 'center' }}>
        {timeframes.map((tf) => (
          <button
            key={tf.key}
            onClick={() => onTimeframeChange(tf.key)}
            disabled={loading}
            className={selectedTimeframe === tf.key ? 'timeframe-btn active' : 'timeframe-btn'}
            style={{
              opacity: loading ? 0.6 : 1,
              cursor: loading ? 'not-allowed' : 'pointer',
              position: 'relative',
              fontSize: isMobile ? '11px' : undefined,
              padding: isMobile ? '4px 8px' : undefined,
              minWidth: isMobile ? 'unset' : undefined
            }}
          >
            <span style={{ position: 'relative', zIndex: 10, fontSize: isMobile ? '11px' : undefined }}>{tf.label}</span>
            {selectedTimeframe === tf.key && (
              <span style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '8px',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
                animation: 'pulse 2s infinite'
              }} />
            )}
          </button>
        ))}
      </div>
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '16px', gap: '8px' }}>
          <div className="loading-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
          <span style={{ color: '#9ca3af', fontSize: '14px', animation: 'pulse 2s infinite' }}>データを読み込み中...</span>
        </div>
      )}
    </div>
  )
})

export default TimeframeSelector