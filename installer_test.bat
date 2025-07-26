@echo off
echo ========================================
echo インストーラービルド テスト
echo ========================================
echo.

echo 必要ファイルの確認中...
echo.

if exist "dist\CoinglassScraper.exe" (
    echo [OK] dist\CoinglassScraper.exe
) else (
    echo [NG] dist\CoinglassScraper.exe が見つかりません
)

if exist "icon.ico" (
    echo [OK] icon.ico
) else (
    echo [NG] icon.ico が見つかりません
)

if exist "README.md" (
    echo [OK] README.md
) else (
    echo [NG] README.md が見つかりません
)

if exist "TRAY_README.md" (
    echo [OK] TRAY_README.md
) else (
    echo [NG] TRAY_README.md が見つかりません
)

if exist "installer.iss" (
    echo [OK] installer.iss
) else (
    echo [NG] installer.iss が見つかりません
)

echo.
echo ========================================
echo Inno Setup の確認
echo ========================================
echo.

set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC_PATH% (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if exist %ISCC_PATH% (
    echo [OK] Inno Setup が見つかりました
    echo パス: %ISCC_PATH%
) else (
    echo [NG] Inno Setup がインストールされていません
    echo.
    echo ダウンロードURL:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo 推奨: innosetup-6.x.x.exe (通常版)
)

echo.
pause