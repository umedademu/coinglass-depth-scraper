const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: './depth-viewer/.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Define individual table creation SQL statements
const tableDefinitions = {
  'order_book_15min': `
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
  `,
  'order_book_30min': `
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
  `,
  'order_book_2hour': `
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
  `,
  'order_book_4hour': `
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
  `,
  'order_book_daily': `
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
  `
};

async function createTimeframeTables() {
  console.log('Starting timeframe tables creation...');
  console.log('Supabase URL:', supabaseUrl);
  console.log('');

  // Since exec_sql is not available, let's try to use the direct client approach
  // This might not work for CREATE TABLE statements, but let's try
  
  const results = {};
  
  for (const [tableName, sql] of Object.entries(tableDefinitions)) {
    console.log(`Creating table: ${tableName}`);
    
    try {
      // Try direct SQL execution (this might not work with anon key)
      const response = await fetch(`${supabaseUrl}/rest/v1/rpc/exec`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': supabaseAnonKey,
          'Authorization': `Bearer ${supabaseAnonKey}`
        },
        body: JSON.stringify({ sql: sql.trim() })
      });
      
      if (response.ok) {
        console.log(`✅ ${tableName}: Created successfully`);
        results[tableName] = 'success';
      } else {
        const errorText = await response.text();
        console.log(`❌ ${tableName}: ${response.status} - ${errorText}`);
        results[tableName] = `error: ${response.status}`;
      }
    } catch (err) {
      console.log(`❌ ${tableName}: Exception - ${err.message}`);
      results[tableName] = `exception: ${err.message}`;
    }
  }
  
  console.log('\nVerifying table creation...\n');
  
  // Try to verify tables exist by attempting to query them
  const tables = ['order_book_15min', 'order_book_30min', 'order_book_2hour', 'order_book_4hour', 'order_book_daily'];
  
  for (const table of tables) {
    try {
      const { count, error } = await supabase
        .from(table)
        .select('*', { count: 'exact', head: true });
      
      if (error) {
        if (error.message.includes('does not exist') || error.message.includes('relation') || error.code === 'PGRST106') {
          console.log(`❌ Table ${table}: Does not exist`);
        } else {
          console.log(`❌ Table ${table}: ${error.message}`);
        }
      } else {
        console.log(`✅ Table ${table}: Exists and accessible (${count || 0} rows)`);
      }
    } catch (err) {
      console.log(`❌ Table ${table}: ${err.message}`);
    }
  }
  
  console.log('\nSummary:');
  console.log(results);
}

createTimeframeTables();