import React from 'react'
import { timeframes, TimeframeKey } from '@/lib/supabase'

interface TimeframeSelectorProps {
  selectedTimeframe: TimeframeKey
  onTimeframeChange: (timeframe: TimeframeKey) => void
  loading?: boolean
}

const TimeframeSelector = React.memo(function TimeframeSelector({ 
  selectedTimeframe, 
  onTimeframeChange,
  loading = false 
}: TimeframeSelectorProps) {
  return (
    <div>
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        flexWrap: 'wrap',
        justifyContent: 'center'
      }}>
        {timeframes.map((tf) => (
          <button
            key={tf.key}
            onClick={() => onTimeframeChange(tf.key)}
            disabled={loading}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              border: '1px solid',
              borderColor: selectedTimeframe === tf.key ? '#ff9500' : '#444',
              backgroundColor: selectedTimeframe === tf.key ? '#ff950020' : 'transparent',
              color: selectedTimeframe === tf.key ? '#ff9500' : '#999',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.95rem',
              fontWeight: selectedTimeframe === tf.key ? '600' : '400',
              transition: 'all 0.2s ease',
              opacity: loading ? 0.6 : 1
            }}
          >
            {tf.label}
          </button>
        ))}
      </div>
      {loading && (
        <div style={{
          textAlign: 'center',
          marginTop: '0.5rem',
          color: '#999',
          fontSize: '0.875rem'
        }}>
          データを読み込み中...
        </div>
      )}
    </div>
  )
})

export default TimeframeSelector