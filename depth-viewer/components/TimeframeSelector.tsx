'use client'

import { useState, useEffect } from 'react'

export type Timeframe = '5min' | '15min' | '1hour' | '4hour' | '1day'

interface TimeframeSelectorProps {
  onTimeframeChange: (timeframe: Timeframe) => void
  initialTimeframe?: Timeframe
}

export default function TimeframeSelector({ 
  onTimeframeChange, 
  initialTimeframe = '1hour' 
}: TimeframeSelectorProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>(initialTimeframe)

  // LocalStorageから初期値を読み込み
  useEffect(() => {
    const stored = localStorage.getItem('selectedTimeframe')
    if (stored && isValidTimeframe(stored)) {
      setSelectedTimeframe(stored as Timeframe)
      onTimeframeChange(stored as Timeframe)
    }
  }, [])

  const isValidTimeframe = (value: string): boolean => {
    return ['5min', '15min', '1hour', '4hour', '1day'].includes(value)
  }

  const handleTimeframeChange = (timeframe: Timeframe) => {
    setSelectedTimeframe(timeframe)
    localStorage.setItem('selectedTimeframe', timeframe)
    onTimeframeChange(timeframe)
  }

  const timeframes: { value: Timeframe; label: string }[] = [
    { value: '5min', label: '5分足' },
    { value: '15min', label: '15分足' },
    { value: '1hour', label: '1時間足' },
    { value: '4hour', label: '4時間足' },
    { value: '1day', label: '1日足' }
  ]

  return (
    <div style={{
      display: 'flex',
      gap: '0.5rem',
      padding: '1rem',
      backgroundColor: '#2a2a2a',
      borderRadius: '8px',
      marginBottom: '1.5rem',
      alignItems: 'center'
    }}>
      <span style={{ 
        color: '#888', 
        fontSize: '0.875rem',
        marginRight: '0.5rem'
      }}>
        時間足:
      </span>
      {timeframes.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => handleTimeframeChange(value)}
          style={{
            padding: '0.5rem 1rem',
            fontSize: '0.875rem',
            backgroundColor: selectedTimeframe === value ? '#4ade80' : '#333',
            color: selectedTimeframe === value ? '#000' : '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            fontWeight: selectedTimeframe === value ? 'bold' : 'normal'
          }}
        >
          {label}
        </button>
      ))}
    </div>
  )
}