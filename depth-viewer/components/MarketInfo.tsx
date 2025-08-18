import { OrderBookData } from '@/lib/supabase'

interface MarketInfoProps {
  latestData: OrderBookData | null
}

export default function MarketInfo({ latestData }: MarketInfoProps) {
  if (!latestData) {
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

  const ratio = latestData.bid_total / latestData.ask_total
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

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
            ${latestData.price.toLocaleString()}
          </div>
        </div>

        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            売り板総量
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f87171' }}>
            {latestData.ask_total.toLocaleString()} BTC
          </div>
        </div>

        <div>
          <div style={{ color: '#999', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            買い板総量
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4ade80' }}>
            {latestData.bid_total.toLocaleString()} BTC
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
        最終更新: {formatDate(latestData.timestamp)}
      </div>
    </div>
  )
}