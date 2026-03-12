@echo off
REM ==============================================================================
REM Ollama 服務停止腳本
REM ==============================================================================
REM 功能: 停止當前運行的 Ollama 服務
REM 用途: 在重新啟動 Ollama 服務前使用，確保釋放 GPU 資源
REM ==============================================================================

echo ========================================
echo   停止 Ollama 服務
echo ========================================
echo.

REM 檢查 Ollama 是否正在運行
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] 發現 Ollama 進程，正在停止...
    taskkill /F /IM ollama.exe >NUL 2>&1
    
    REM 等待進程完全終止
    timeout /t 2 /nobreak >NUL
    
    echo [SUCCESS] Ollama 服務已停止
    echo.
    echo 請使用 nvidia-smi 確認 GPU 已釋放
) else (
    echo [INFO] Ollama 服務未運行
)

echo.
echo ========================================
pause

