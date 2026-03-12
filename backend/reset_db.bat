@echo off
chcp 65001 >nul
echo ====================================
echo   Metora 資料庫重置腳本
echo ====================================
echo.
echo ⚠️  警告: 此操作將清空所有資料!
echo.
set /p confirm="確定要重置資料庫嗎? (輸入 YES 確認): "
if not "%confirm%"=="YES" (
    echo.
    echo ❌ 已取消操作
    pause
    exit /b 0
)
echo.

echo [1/3] 回滾所有遷移...
alembic downgrade base
if %errorlevel% neq 0 (
    echo.
    echo ❌ 回滾失敗!
    pause
    exit /b 1
)
echo ✅ 回滾完成
echo.

echo [2/3] 重新執行遷移...
alembic upgrade head
if %errorlevel% neq 0 (
    echo.
    echo ❌ 遷移失敗!
    pause
    exit /b 1
)
echo ✅ 遷移完成
echo.

echo [3/3] 初始化基礎資料...
python scripts/init_database.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 初始化失敗!
    pause
    exit /b 1
)
echo.

echo ====================================
echo   ✅ 資料庫重置完成!
echo ====================================
echo.
echo 預設管理員帳號:
echo   使用者名稱: admin
echo   密碼: admin123
echo.
pause

