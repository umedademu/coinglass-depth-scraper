@echo off
echo Price Analyzer を起動しています...
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

REM アプリケーションを実行
echo 価格要素の分析を開始します...
python price_analyzer.py

pause