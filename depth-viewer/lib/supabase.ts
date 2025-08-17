import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export interface OrderBookData {
  id: number
  timestamp: string
  ask_total: number
  bid_total: number
  price: number
  group_id: string
  created_at?: string
}

export const timeframes = [
  { key: '5min', label: '5分足', table: 'order_book_shared' },
  { key: '15min', label: '15分足', table: 'order_book_15min' },
  { key: '30min', label: '30分足', table: 'order_book_30min' },
  { key: '1hour', label: '1時間足', table: 'order_book_1hour' },
  { key: '2hour', label: '2時間足', table: 'order_book_2hour' },
  { key: '4hour', label: '4時間足', table: 'order_book_4hour' },
  { key: '1day', label: '日足', table: 'order_book_daily' },
] as const

export type TimeframeKey = typeof timeframes[number]['key']

export async function fetchTimeframeData(
  timeframe: TimeframeKey,
  limit: number = 10
): Promise<OrderBookData[]> {
  const table = timeframes.find(tf => tf.key === timeframe)?.table
  if (!table) {
    throw new Error(`Invalid timeframe: ${timeframe}`)
  }

  const { data, error } = await supabase
    .from(table)
    .select('*')
    .eq('group_id', 'default-group')
    .order('timestamp', { ascending: false })
    .limit(limit)

  if (error) {
    console.error(`Error fetching data from ${table}:`, error)
    return []
  }

  return data || []
}