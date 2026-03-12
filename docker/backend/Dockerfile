# ============================================
# 多階段建置 - 後端 FastAPI 應用
# ============================================

# ============================================
# Stage 1: Base Image (基礎映像)
# ============================================
FROM python:3.11-slim AS base

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Stage 2: Dependencies (依賴安裝)
# ============================================
FROM base AS dependencies

# 安裝 uv (快速的 Python 套件管理器)
RUN pip install uv

# 複製依賴定義檔案 (在專案根目錄)
COPY pyproject.toml uv.lock* ./

# 使用 uv 安裝依賴
# uv sync 會在專案目錄創建 .venv,所以直接使用
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen

# ============================================
# Stage 3: Production (生產環境)
# ============================================
FROM base AS production

# 從 dependencies stage 複製虛擬環境
COPY --from=dependencies /opt/venv /opt/venv

# 啟用虛擬環境
ENV PATH="/opt/venv/bin:$PATH"

# 複製後端程式碼
COPY backend/ /app/

# 建立必要的目錄
RUN mkdir -p /app/uploaded_files/chat_files \
    /app/vector_stores \
    /app/models/huggingface/hub \
    /app/logs

# 設定權限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 8002

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 啟動命令
# 使用 python -m 方式啟動,確保可以找到模組
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8002", \
     "--reload"]
