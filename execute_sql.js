const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, 'depth-viewer', '.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function executeSQLFile() {
  console.log('Starting SQL execution...');
  console.log('Supabase URL:', supabaseUrl);
  console.log('');
  
  try {
    // Read the SQL file
    const sqlFile = fs.readFileSync(path.join(__dirname, 'create_timeframe_tables.sql'), 'utf8');
    
    console.log('Executing complete SQL file...');
    
    // Execute the entire SQL file as one statement
    const { data, error } = await supabase.rpc('exec_sql', { sql: sqlFile });
    
    if (error) {
      console.error('❌ Error executing SQL:', error.message);
      console.error('Error details:', error);
      return;
    }
    
    console.log('✅ SQL execution completed successfully!\n');
    
    // Verify table creation by checking each table
    console.log('Verifying table creation...\n');
    
    const tables = ['order_book_15min', 'order_book_30min', 'order_book_2hour', 'order_book_4hour', 'order_book_daily'];
    
    for (const table of tables) {
      try {
        const { count, error } = await supabase
          .from(table)
          .select('*', { count: 'exact', head: true });
        
        if (error) {
          console.log(`❌ Table ${table}: ${error.message}`);
        } else {
          console.log(`✅ Table ${table}: Created successfully (${count || 0} rows)`);
        }
      } catch (err) {
        console.log(`❌ Table ${table}: ${err.message}`);
      }
    }
    
    // Also verify using information_schema
    console.log('\nVerifying table existence in schema...\n');
    
    for (const table of tables) {
      try {
        const { data: tableInfo, error: tableError } = await supabase
          .from('information_schema.tables')
          .select('table_name')
          .eq('table_name', table);
        
        if (tableError) {
          console.log(`❌ Schema check for ${table}: ${tableError.message}`);
        } else if (tableInfo && tableInfo.length > 0) {
          console.log(`✅ Schema check for ${table}: Table exists`);
        } else {
          console.log(`❌ Schema check for ${table}: Table not found`);
        }
      } catch (err) {
        console.log(`❌ Schema check for ${table}: ${err.message}`);
      }
    }
    
  } catch (error) {
    console.error('Error reading SQL file:', error.message);
  }
}

executeSQLFile();