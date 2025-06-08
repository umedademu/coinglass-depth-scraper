@echo off
echo Coinglass ページ分析ツールを起動しています...
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

REM 分析ツールを実行
echo ページ構造を分析しています...
python page_analyzer.py

echo.
echo 分析が完了しました。生成されたファイルを確認してください：
echo - page_analysis_*.png (スクリーンショット)
echo - page_source_*.html (HTMLソース)
echo - page_text_*.txt (ページのテキスト)
echo - page_analysis_*.json (要素の分析結果)
echo.
pause