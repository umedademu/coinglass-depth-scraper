@echo off
echo ========================================
echo Coinglass Scraper インストーラービルド
echo ========================================
echo.

REM EXEファイルの存在確認
if not exist "dist\CoinglassScraper.exe" (
    echo エラー: dist\CoinglassScraper.exe が見つかりません。
    echo 先に build_exe.bat を実行してEXEをビルドしてください。
    pause
    exit /b 1
)

REM アイコンファイルの存在確認
if not exist "icon.ico" (
    echo エラー: icon.ico が見つかりません。
    pause
    exit /b 1
)

REM 出力フォルダを作成
if not exist "installer_output" (
    mkdir installer_output
)

REM Inno Setupのパスを設定（通常のインストール場所）
set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

REM 64ビット版の場所も確認
if not exist %ISCC_PATH% (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

REM Inno Setupがインストールされているか確認
if not exist %ISCC_PATH% (
    echo.
    echo エラー: Inno Setup が見つかりません。
    echo.
    echo Inno Setup をダウンロードしてインストールしてください：
    echo https://jrsoftware.org/isdl.php
    echo.
    echo インストール後、このバッチファイルを再実行してください。
    echo.
    pause
    exit /b 1
)

echo.
echo Inno Setup を検出しました。
echo インストーラーをビルド中...
echo.

REM インストーラーをビルド
%ISCC_PATH% installer.iss

REM ビルド結果を確認
echo.
if exist "installer_output\CoinglassScraperSetup_*.exe" (
    echo ========================================
    echo インストーラービルド成功！
    echo ========================================
    echo.
    echo インストーラーの場所: installer_output\
    echo.
    dir /b installer_output\*.exe
) else (
    echo ========================================
    echo インストーラービルド失敗
    echo ========================================
    echo エラーが発生しました。ログを確認してください。
)

echo.
pause