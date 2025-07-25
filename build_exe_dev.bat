@echo off
echo ========================================
echo Coinglass Scraper EXEビルド（開発モード）
echo ========================================
echo.
echo このモードは起動が速く、デバッグに適しています。
echo 配布には build_exe.bat を使用してください。
echo.

REM 仮想環境をアクティベート
if exist "venv" (
    echo 仮想環境をアクティベートしています...
    call venv\Scripts\activate.bat
) else (
    echo エラー: 仮想環境が見つかりません。
    echo 先に setup_scraper.bat を実行してください。
    pause
    exit /b 1
)

REM PyInstallerがインストールされているか確認
echo.
echo PyInstallerの確認中...
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstallerがインストールされていません。
    echo インストール中...
    pip install pyinstaller==6.3.0
)

REM 古いビルドファイルをクリーンアップ
echo.
echo 古いビルドファイルをクリーンアップしています...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM EXEをビルド（フォルダ形式）
echo.
echo EXEファイルをビルド中（フォルダ形式）...
echo.

pyinstaller --onedir --windowed --name CoinglassScraperDev coinglass_scraper.py

REM ビルド結果を確認
echo.
if exist "dist\CoinglassScraperDev\CoinglassScraperDev.exe" (
    echo ========================================
    echo ビルド成功！
    echo ========================================
    echo.
    echo EXEファイルの場所: dist\CoinglassScraperDev\CoinglassScraperDev.exe
    echo.
    echo フォルダ全体が必要です: dist\CoinglassScraperDev\
) else (
    echo ========================================
    echo ビルド失敗
    echo ========================================
    echo エラーが発生しました。ログを確認してください。
)

echo.
pause