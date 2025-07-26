# Inno Setup ダウンロードヘルパースクリプト
# PowerShell 5.0以上が必要

$innoSetupUrl = "https://files.jrsoftware.org/is/6/innosetup-6.3.3.exe"
$outputPath = "$env:USERPROFILE\Downloads\innosetup-6.3.3.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Inno Setup ダウンローダー" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ダウンロード済みかチェック
if (Test-Path $outputPath) {
    Write-Host "✓ 既にダウンロード済みです: $outputPath" -ForegroundColor Green
    Write-Host ""
    $response = Read-Host "インストーラーを実行しますか？ (Y/N)"
    if ($response -eq 'Y' -or $response -eq 'y') {
        Start-Process $outputPath
    }
    exit
}

Write-Host "Inno Setup 6.3.3 をダウンロード中..." -ForegroundColor Yellow
Write-Host "保存先: $outputPath"
Write-Host ""

try {
    # プログレスバーを表示してダウンロード
    $ProgressPreference = 'Continue'
    Invoke-WebRequest -Uri $innoSetupUrl -OutFile $outputPath -UseBasicParsing
    
    Write-Host "✓ ダウンロード完了！" -ForegroundColor Green
    Write-Host ""
    
    # ファイルサイズ確認
    $fileInfo = Get-Item $outputPath
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "ファイルサイズ: $sizeMB MB" -ForegroundColor Gray
    Write-Host ""
    
    $response = Read-Host "インストーラーを実行しますか？ (Y/N)"
    if ($response -eq 'Y' -or $response -eq 'y') {
        Write-Host "インストーラーを起動中..." -ForegroundColor Yellow
        Start-Process $outputPath
    } else {
        Write-Host "ダウンロードのみ完了しました。" -ForegroundColor Green
        Write-Host "手動で実行する場合: $outputPath"
    }
} catch {
    Write-Host "✗ ダウンロードエラー: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "手動でダウンロードしてください:"
    Write-Host $innoSetupUrl -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")