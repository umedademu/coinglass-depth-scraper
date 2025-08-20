import React from 'react'

export default function LoadingScreen() {
  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Animated loader */}
        <div style={{ position: 'relative', marginBottom: '32px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', border: '4px solid rgba(255, 255, 255, 0.1)', animation: 'pulse 2s infinite' }} />
          <div style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            width: '80px', 
            height: '80px', 
            borderRadius: '50%', 
            border: '4px solid transparent',
            borderTopColor: '#3b82f6',
            borderRightColor: '#8b5cf6',
            animation: 'spin 1s linear infinite' 
          }} />
          <div style={{ 
            position: 'absolute', 
            top: '8px', 
            left: '8px', 
            width: '64px', 
            height: '64px', 
            borderRadius: '50%', 
            border: '4px solid transparent',
            borderBottomColor: '#ec4899',
            borderLeftColor: '#06b6d4',
            animation: 'spin 1.5s linear infinite reverse' 
          }} />
        </div>
        
        {/* Main message */}
        <h2 className="gradient-text" style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px', animation: 'pulse 2s infinite' }}>
          データを読み込み中...
        </h2>
        
        {/* Sub message */}
        <p style={{ color: '#9ca3af', textAlign: 'center', marginBottom: '32px' }}>
          BTC-USDT板情報を取得しています
        </p>
        
        {/* Loading progress indicator */}
        <div style={{ width: '256px', height: '4px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
          <div className="shimmer" style={{ height: '100%', width: '30%', background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)', borderRadius: '9999px' }} />
        </div>
        
        {/* Loading dots */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '32px' }}>
          <span style={{ width: '8px', height: '8px', backgroundColor: '#60a5fa', borderRadius: '50%', animation: 'bounce 1s infinite', animationDelay: '0s' }} />
          <span style={{ width: '8px', height: '8px', backgroundColor: '#a78bfa', borderRadius: '50%', animation: 'bounce 1s infinite', animationDelay: '0.2s' }} />
          <span style={{ width: '8px', height: '8px', backgroundColor: '#f472b6', borderRadius: '50%', animation: 'bounce 1s infinite', animationDelay: '0.4s' }} />
        </div>
      </div>
      
      <style jsx>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  )
}