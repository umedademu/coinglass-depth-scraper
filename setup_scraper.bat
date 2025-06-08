@echo off
echo Coinglass Scraper セットアップを開始します...
echo.

REM Pythonがインストールされているか確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません。
    echo Pythonをインストールしてから再度実行してください。
    pause
    exit /b 1
)

echo Pythonが検出されました。
echo.

REM 仮想環境を作成
if not exist "venv" (
    echo 仮想環境を作成しています...
    python -m venv venv
    echo 仮想環境を作成しました。
) else (
    echo 仮想環境は既に存在します。
)

echo.

REM 仮想環境をアクティベート
echo 仮想環境をアクティベートしています...
call venv\Scripts\activate.bat

REM 必要なパッケージをインストール
echo 必要なパッケージをインストールしています...
pip install --upgrade pip
pip install -r requirements_scraper.txt

echo.
echo セットアップが完了しました！
echo run_scraper.bat を実行してアプリケーションを起動してください。
echo.
pause