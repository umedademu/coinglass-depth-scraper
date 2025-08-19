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
      backgroundColor: '#0a0a0a',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      padding: '2rem'
    }}>
      {/* エラーアイコン */}
      <div style={{
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        backgroundColor: '#dc2626',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '2rem'
      }}>
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M12 9v4m0 4h.01M5.07 19H19a2 2 0 001.75-2.96L13.07 4.05a2 2 0 00-3.5 0L2.88 16.04A2 2 0 004.63 19z" />
        </svg>
      </div>
      
      {/* エラータイトル */}
      <h2 style={{
        fontSize: '1.5rem',
        fontWeight: '600',
        marginBottom: '1rem',
        textAlign: 'center'
      }}>
        エラーが発生しました
      </h2>
      
      {/* エラーメッセージ */}
      <div style={{
        backgroundColor: '#1a1a1a',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        maxWidth: '500px',
        width: '100%'
      }}>
        <p style={{
          fontSize: '0.9rem',
          color: '#f87171',
          margin: 0,
          wordBreak: 'break-word'
        }}>
          {errorMessage}
        </p>
      </div>
      
      {/* トラブルシューティングヒント */}
      <div style={{
        backgroundColor: '#1a1a1a',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        maxWidth: '500px',
        width: '100%'
      }}>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '0.75rem',
          color: '#ff9500'
        }}>
          トラブルシューティング
        </h3>
        <ul style={{
          margin: 0,
          paddingLeft: '1.5rem',
          fontSize: '0.9rem',
          color: '#999'
        }}>
          <li style={{ marginBottom: '0.5rem' }}>
            インターネット接続を確認してください
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            しばらく待ってから再試行してください
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            問題が続く場合は、ページを再読み込みしてください
          </li>
          <li>
            Supabaseサービスのステータスを確認してください
          </li>
        </ul>
      </div>
      
      {/* 再試行ボタン */}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '0.75rem 2rem',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: '#ff9500',
            color: '#fff',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#e68600'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#ff9500'
          }}
        >
          再試行
        </button>
      )}
    </div>
  )
}