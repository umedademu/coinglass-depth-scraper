@echo off
echo Coinglass Scraper をデバッグモードで起動しています...
echo （コンソールウィンドウが表示されます）
echo.

REM 仮想環境をアクティベート
if exist "venv" (
    call venv\Scripts\activate.bat
) else (
    echo エラー: 仮想環境が見つかりません。
    echo 先に setup_scraper.bat を実行してください。
    pause
    exit /b 1
)

REM アプリケーションを実行（デバッグモード）
echo アプリケーションを起動しています...
python coinglass_scraper.py

pause