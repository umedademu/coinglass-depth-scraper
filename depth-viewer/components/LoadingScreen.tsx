import React from 'react'

export default function LoadingScreen() {
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
      color: '#fff'
    }}>
      {/* スピナー */}
      <div style={{
        width: '50px',
        height: '50px',
        border: '3px solid #333',
        borderTop: '3px solid #ff9500',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: '2rem'
      }} />
      
      {/* メインメッセージ */}
      <h2 style={{
        fontSize: '1.5rem',
        fontWeight: '600',
        marginBottom: '0.5rem',
        textAlign: 'center'
      }}>
        データを読み込み中...
      </h2>
      
      {/* サブメッセージ */}
      <p style={{
        fontSize: '0.9rem',
        color: '#999',
        textAlign: 'center'
      }}>
        BTCーUSDT板情報を取得しています
      </p>
      
      {/* CSS アニメーション */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}