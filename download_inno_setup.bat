@echo off
echo ========================================
echo Inno Setup ダウンローダー
echo ========================================
echo.
echo PowerShellスクリプトを実行します...
echo.

powershell.exe -ExecutionPolicy Bypass -File download_inno_setup.ps1

pause