'use client'

import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  Filler
} from 'chart.js'
import { OrderBookData } from '../lib/supabase'

// Chart.jsの必要なコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface OrderBookChartProps {
  data: OrderBookData[]
}

export default function OrderBookChart({ data }: OrderBookChartProps) {
  // データを時系列順に並び替え（古い順）
  const sortedData = [...data].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  // タイムスタンプをそのまま表示（変換なし）
  const labels = sortedData.map(item => {
    // ISO形式のタイムスタンプから時刻部分を直接抽出
    // 例: "2025-08-17T02:40:00" -> "02:40"
    const timePart = item.timestamp.split('T')[1]
    if (timePart) {
      return timePart.substring(0, 5) // HH:MM形式
    }
    return ''
  })

  // データ配列を作成
  const askData = sortedData.map(item => item.ask_total)
  const bidData = sortedData.map(item => item.bid_total)

  // 縦軸スケールの統一計算（仕様書に従って）
  const askMin = Math.min(...askData)
  const askMax = Math.max(...askData)
  const bidMin = Math.min(...bidData)
  const bidMax = Math.max(...bidData)
  
  const askRange = askMax - askMin
  const bidRange = bidMax - bidMin
  
  // より大きい変動幅を共通幅として採用
  const commonRange = Math.max(askRange, bidRange, 1.0)
  
  // 各グラフの表示範囲を設定（自身の最小値から共通幅分）
  const askYMin = askMin
  const askYMax = askMin + commonRange
  const bidYMin = bidMin
  const bidYMax = bidMin + commonRange

  // 売り板データ（赤色）
  const askChartData = {
    labels,
    datasets: [
      {
        label: '売り板総量 (BTC)',
        data: askData,
        borderColor: 'rgb(248, 113, 113)',
        backgroundColor: 'rgba(248, 113, 113, 0.1)',
        fill: true,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 4,
      }
    ]
  }

  // 買い板データ（緑色）
  const bidChartData = {
    labels,
    datasets: [
      {
        label: '買い板総量 (BTC)',
        data: bidData,
        borderColor: 'rgb(74, 222, 128)',
        backgroundColor: 'rgba(74, 222, 128, 0.1)',
        fill: true,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 4,
      }
    ]
  }

  // 売り板グラフのオプション（Y軸反転）
  const askChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 500,
      easing: 'easeInOutQuart'
    },
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#333',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US').format(context.parsed.y);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          display: true
        },
        ticks: {
          color: '#888',
          maxRotation: 45,
          minRotation: 45,
          autoSkip: true,
          maxTicksLimit: 20
        }
      },
      y: {
        min: askYMin,
        max: askYMax,
        reverse: true, // Y軸を反転
        display: true,
        position: 'right',
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          display: true
        },
        ticks: {
          color: '#888',
          callback: function(value) {
            return new Intl.NumberFormat('en-US').format(value as number);
          }
        }
      }
    }
  }

  // 買い板グラフのオプション
  const bidChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 500,
      easing: 'easeInOutQuart'
    },
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#333',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US').format(context.parsed.y);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          display: true
        },
        ticks: {
          color: '#888',
          maxRotation: 45,
          minRotation: 45,
          autoSkip: true,
          maxTicksLimit: 20
        }
      },
      y: {
        min: bidYMin,
        max: bidYMax,
        display: true,
        position: 'right',
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          display: true
        },
        ticks: {
          color: '#888',
          callback: function(value) {
            return new Intl.NumberFormat('en-US').format(value as number);
          }
        }
      }
    }
  }

  return (
    <div style={{ width: '100%' }}>
      {/* 売り板グラフ（上側、独立した枠） */}
      <div style={{
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '2px' // 最小限の隙間
      }}>
        <div style={{ height: '250px' }}>
          <Line data={askChartData} options={askChartOptions} />
        </div>
      </div>

      {/* 買い板グラフ（下側、独立した枠） */}
      <div style={{
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        padding: '1rem'
      }}>
        <div style={{ height: '250px' }}>
          <Line data={bidChartData} options={bidChartOptions} />
        </div>
      </div>
    </div>
  )
}