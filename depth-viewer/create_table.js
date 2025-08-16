const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function createOrderBook1HourTable() {
  console.log('Connecting to Supabase...');
  console.log('URL:', supabaseUrl);
  
  const createTableSQL = `
-- 1時間足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_1hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_1hour_timestamp ON order_book_1hour(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_1hour_group_id ON order_book_1hour(group_id);
  `.trim();

  try {
    console.log('Creating order_book_1hour table...');
    
    // SQL実行
    const { data, error } = await supabase.rpc('exec_sql', { 
      sql: createTableSQL 
    });
    
    if (error) {
      console.error('Error creating table:', error);
      return;
    }
    
    console.log('Table creation successful!');
    
    // テーブル存在確認
    const { data: tables, error: tableError } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_name', 'order_book_1hour');
    
    if (tableError) {
      console.error('Error checking table existence:', tableError);
    } else {
      console.log('Table check result:', tables);
    }
    
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

createOrderBook1HourTable();