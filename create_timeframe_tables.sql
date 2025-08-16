-- Create multiple timeframe tables for order book data
-- Each table has the same structure as order_book_1hour

-- 15分足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_15min (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 30分足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_30min (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 2時間足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_2hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 4時間足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_4hour (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- 日足テーブルの作成
CREATE TABLE IF NOT EXISTS order_book_daily (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- インデックスの作成 (15分足)
CREATE INDEX IF NOT EXISTS idx_15min_timestamp ON order_book_15min(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_15min_group_id ON order_book_15min(group_id);

-- インデックスの作成 (30分足)
CREATE INDEX IF NOT EXISTS idx_30min_timestamp ON order_book_30min(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_30min_group_id ON order_book_30min(group_id);

-- インデックスの作成 (2時間足)
CREATE INDEX IF NOT EXISTS idx_2hour_timestamp ON order_book_2hour(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_2hour_group_id ON order_book_2hour(group_id);

-- インデックスの作成 (4時間足)
CREATE INDEX IF NOT EXISTS idx_4hour_timestamp ON order_book_4hour(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_4hour_group_id ON order_book_4hour(group_id);

-- インデックスの作成 (日足)
CREATE INDEX IF NOT EXISTS idx_daily_timestamp ON order_book_daily(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_daily_group_id ON order_book_daily(group_id);

-- テーブル権限の設定 (15分足)
GRANT ALL ON order_book_15min TO anon;
GRANT ALL ON order_book_15min TO authenticated;

-- テーブル権限の設定 (30分足)
GRANT ALL ON order_book_30min TO anon;
GRANT ALL ON order_book_30min TO authenticated;

-- テーブル権限の設定 (2時間足)
GRANT ALL ON order_book_2hour TO anon;
GRANT ALL ON order_book_2hour TO authenticated;

-- テーブル権限の設定 (4時間足)
GRANT ALL ON order_book_4hour TO anon;
GRANT ALL ON order_book_4hour TO authenticated;

-- テーブル権限の設定 (日足)
GRANT ALL ON order_book_daily TO anon;
GRANT ALL ON order_book_daily TO authenticated;