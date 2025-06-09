@echo off
echo matplotlib をインストールしています...
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

REM matplotlibをインストール
echo インストール中... しばらくお待ちください（数分かかることがあります）
pip install matplotlib==3.7.1

echo.
echo インストールが完了しました！
echo.
pause