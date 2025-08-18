$appDataPath = [System.Environment]::GetFolderPath('ApplicationData')
$dbPath = Join-Path $appDataPath "Coinglass Scraper\btc_usdt_order_book.db"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $appDataPath "Coinglass Scraper\btc_usdt_order_book_backup_$timestamp.db"

if (Test-Path $dbPath) {
    Copy-Item -Path $dbPath -Destination $backupPath -Force
    Write-Host "Backup created: $backupPath"
    
    # List all DB files
    Get-ChildItem (Join-Path $appDataPath "Coinglass Scraper\*.db") | 
        Select-Object Name, Length, LastWriteTime |
        Format-Table -AutoSize
} else {
    Write-Host "Database file not found: $dbPath"
}