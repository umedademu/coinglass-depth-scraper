import React from 'react'

interface ErrorScreenProps {
  error: Error | string
  onRetry?: () => void
}

export default function ErrorScreen({ error, onRetry }: ErrorScreenProps) {
  const errorMessage = typeof error === 'string' ? error : error.message
  
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
      justifyContent: 'center',
      padding: '32px'
    }}>
      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', maxWidth: '600px', width: '100%' }}>
        {/* Error icon with animation */}
        <div style={{ position: 'relative', marginBottom: '32px' }}>
          <div style={{ 
            width: '80px', 
            height: '80px', 
            borderRadius: '50%', 
            backgroundColor: 'rgba(239, 68, 68, 0.2)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            animation: 'pulse 2s infinite' 
          }}>
            <div style={{ 
              width: '64px', 
              height: '64px', 
              borderRadius: '50%', 
              backgroundColor: 'rgba(239, 68, 68, 0.3)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center' 
            }}>
              <svg style={{ width: '32px', height: '32px', color: '#f87171' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M5.07 19H19a2 2 0 001.75-2.96L13.07 4.05a2 2 0 00-3.5 0L2.88 16.04A2 2 0 004.63 19z" />
              </svg>
            </div>
          </div>
          <div style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            width: '80px', 
            height: '80px', 
            borderRadius: '50%', 
            border: '2px solid rgba(239, 68, 68, 0.5)', 
            animation: 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite' 
          }} />
        </div>
      
        {/* Error title */}
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px', color: '#f87171' }}>
          エラーが発生しました
        </h2>
        
        {/* Error message */}
        <div className="glass-card" style={{ padding: '24px', marginBottom: '24px', width: '100%', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <svg style={{ width: '20px', height: '20px', color: '#f87171', marginTop: '2px', flexShrink: 0 }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p style={{ color: '#fca5a5', wordBreak: 'break-word' }}>
              {errorMessage}
            </p>
          </div>
        </div>
      
        {/* Troubleshooting hints */}
        <div className="glass-card" style={{ padding: '24px', marginBottom: '32px', width: '100%' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            トラブルシューティング
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '12px' }}>
              <span style={{ width: '6px', height: '6px', backgroundColor: '#9ca3af', borderRadius: '50%', marginTop: '8px', flexShrink: 0 }} />
              <span style={{ color: '#d1d5db' }}>インターネット接続を確認してください</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '12px' }}>
              <span style={{ width: '6px', height: '6px', backgroundColor: '#9ca3af', borderRadius: '50%', marginTop: '8px', flexShrink: 0 }} />
              <span style={{ color: '#d1d5db' }}>しばらく待ってから再試行してください</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '12px' }}>
              <span style={{ width: '6px', height: '6px', backgroundColor: '#9ca3af', borderRadius: '50%', marginTop: '8px', flexShrink: 0 }} />
              <span style={{ color: '#d1d5db' }}>問題が続く場合は、ページを再読み込みしてください</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <span style={{ width: '6px', height: '6px', backgroundColor: '#9ca3af', borderRadius: '50%', marginTop: '8px', flexShrink: 0 }} />
              <span style={{ color: '#d1d5db' }}>Supabaseサービスのステータスを確認してください</span>
            </li>
          </ul>
        </div>
      
        {/* Retry button */}
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn-primary"
            style={{ position: 'relative', overflow: 'hidden' }}
          >
            <span style={{ position: 'relative', zIndex: 10, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              再試行
            </span>
          </button>
        )}
        
        <style jsx>{`
          @keyframes ping {
            75%, 100% {
              transform: scale(2);
              opacity: 0;
            }
          }
        `}</style>
      </div>
    </div>
  )
}