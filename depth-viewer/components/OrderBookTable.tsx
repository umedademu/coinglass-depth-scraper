import { OrderBookData } from '@/lib/supabase'

interface OrderBookTableProps {
  data: OrderBookData[]
  limit?: number
}

export default function OrderBookTable({ data, limit = 100 }: OrderBookTableProps) {
  const displayData = data.slice(-limit).reverse()

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

  if (displayData.length === 0) {
    return (
      <div style={{
        padding: '2rem',
        backgroundColor: '#1e1e1e',
        borderRadius: '8px',
        textAlign: 'center',
        color: '#999'
      }}>
        データがありません
      </div>
    )
  }

  return (
    <div style={{
      backgroundColor: '#1e1e1e',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '1rem 1.5rem',
        backgroundColor: '#2a2a2a',
        borderBottom: '1px solid #444'
      }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
          板情報データ（最新{displayData.length}件）
        </h3>
      </div>
      
      <div style={{ 
        overflowX: 'auto',
        maxHeight: '600px',
        overflowY: 'auto'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.9rem'
        }}>
          <thead>
            <tr style={{
              backgroundColor: '#2a2a2a',
              position: 'sticky',
              top: 0,
              zIndex: 10
            }}>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: '2px solid #444',
                color: '#999',
                fontWeight: 'normal'
              }}>
                時刻
              </th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                borderBottom: '2px solid #444',
                color: '#999',
                fontWeight: 'normal'
              }}>
                売り板総量 (BTC)
              </th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                borderBottom: '2px solid #444',
                color: '#999',
                fontWeight: 'normal'
              }}>
                買い板総量 (BTC)
              </th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                borderBottom: '2px solid #444',
                color: '#999',
                fontWeight: 'normal'
              }}>
                価格 ($)
              </th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                borderBottom: '2px solid #444',
                color: '#999',
                fontWeight: 'normal'
              }}>
                買い/売り比率
              </th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, index) => {
              const ratio = row.bid_total / row.ask_total
              return (
                <tr key={row.id} style={{
                  borderBottom: '1px solid #333',
                  backgroundColor: index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                }}>
                  <td style={{
                    padding: '0.75rem',
                    color: '#ccc',
                    fontSize: '0.85rem'
                  }}>
                    {formatDate(row.timestamp)}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: '#f87171'
                  }}>
                    {row.ask_total.toLocaleString()}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: '#4ade80'
                  }}>
                    {row.bid_total.toLocaleString()}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: '#fff',
                    fontWeight: 'bold'
                  }}>
                    ${row.price.toLocaleString()}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: ratio > 1 ? '#4ade80' : '#f87171',
                    fontWeight: 'bold'
                  }}>
                    {ratio.toFixed(2)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}