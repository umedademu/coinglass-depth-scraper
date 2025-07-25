@echo off
echo ========================================
echo Coinglass Scraper EXEビルド
echo ========================================
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
if exist "CoinglassScraper.exe" del /q "CoinglassScraper.exe"

REM EXEをビルド
echo.
echo EXEファイルをビルド中...
echo これには数分かかる場合があります。
echo.

pyinstaller coinglass_scraper.spec

REM ビルド結果を確認
echo.
if exist "dist\CoinglassScraper.exe" (
    echo ========================================
    echo ビルド成功！
    echo ========================================
    echo.
    echo EXEファイルの場所: dist\CoinglassScraper.exe
    echo.
    echo EXEファイルをプロジェクトルートにコピーしています...
    copy "dist\CoinglassScraper.exe" "CoinglassScraper.exe"
    echo.
    echo 完了しました！
    echo CoinglassScraper.exe を実行してアプリケーションを起動できます。
) else (
    echo ========================================
    echo ビルド失敗
    echo ========================================
    echo エラーが発生しました。ログを確認してください。
)

echo.
pause