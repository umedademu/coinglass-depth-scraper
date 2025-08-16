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

-- テーブル権限の設定（必要に応じて）
GRANT ALL ON order_book_1hour TO anon;
GRANT ALL ON order_book_1hour TO authenticated;