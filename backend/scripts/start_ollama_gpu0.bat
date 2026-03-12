@echo off
REM ==============================================================================
REM Ollama 服務啟動腳本 (GPU 0 專用)
REM ==============================================================================
REM 功能: 在 GPU 0 (RTX 3090) 上啟動 Ollama 服務
REM 原理: 透過環境變數 CUDA_VISIBLE_DEVICES=0 限制 Ollama 只使用 GPU 0
REM 用途: 確保 GPU 資源隔離，讓 GPU 1 可供 Embedding/Reranker 模型使用
REM ==============================================================================

echo ========================================
echo   啟動 Ollama 服務 (GPU 0 - RTX 3090)
echo ========================================
echo.

REM 檢查 Ollama 是否已經在運行
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] Ollama 服務已在運行中！
    echo [INFO] 請先執行 stop_ollama.bat 停止服務
    echo.
    pause
    exit /b 1
)

REM 啟動 Ollama 服務
echo [INFO] 正在啟動 Ollama 服務...
echo [INFO] 環境變數設定: CUDA_VISIBLE_DEVICES=0
echo [INFO] Ollama 將只使用 GPU 0 (RTX 3090)
echo.

REM 在新進程中設定環境變數並啟動 Ollama（不影響當前 session）
start "Ollama GPU 0" cmd /c "set CUDA_VISIBLE_DEVICES=0 && "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve"

REM 等待服務啟動
timeout /t 3 /nobreak >NUL

echo.
echo [SUCCESS] Ollama 服務已啟動
echo.
echo ========================================
echo   驗證步驟
echo ========================================
echo 1. 執行命令: nvidia-smi
echo 2. 確認 Ollama 只出現在 GPU 0
echo 3. 啟動應用程式載入 Embedding/Reranker 到 GPU 1
echo.
echo 如需停止服務，請執行: stop_ollama.bat
echo ========================================
echo.
pause

