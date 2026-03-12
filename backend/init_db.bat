@echo off
chcp 65001 >nul
echo ====================================
echo   Metora 資料庫初始化腳本
echo ====================================
echo.

echo [1/3] 檢查 Alembic 狀態...
alembic current
echo.

echo [2/3] 執行資料庫遷移 (建立表結構)...
alembic upgrade head
if %errorlevel% neq 0 (
    echo.
    echo ❌ 遷移失敗! 請檢查資料庫連線設定
    pause
    exit /b 1
)
echo ✅ 遷移完成
echo.

echo [3/3] 初始化基礎資料 (管理員帳號、角色)...
python scripts/init_database.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 初始化失敗!
    pause
    exit /b 1
)
echo.

echo ====================================
echo   ✅ 資料庫初始化完成!
echo ====================================
echo.
echo 預設管理員帳號:
echo   使用者名稱: admin
echo   密碼: admin123
echo.
echo 您現在可以啟動後端服務:
echo   python run.py
echo.
pause

