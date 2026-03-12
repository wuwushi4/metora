"""
統一配置管理模組
從專案根目錄的 .env 檔案讀取所有環境變數
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 計算專案根目錄的 .env 路徑 (相對於此檔案)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class RateLimitLevel(str, Enum):
    """
    速率限制級別
    
    用於標記 API 端點的速率限制策略
    """
    NONE = "none"           # 不限制（白名單，如健康檢查）
    DEFAULT = "default"     # 一般限制（預設值）
    SENSITIVE = "sensitive" # 敏感操作（登入、註冊、修改密碼等）
    STRICT = "strict"       # 嚴格限制（未來擴展用）


class Settings(BaseSettings):
    """
    應用配置類別

    ⚠️ 重要提醒:
    1. 此類別使用 Pydantic Settings 從 .env 檔案讀取配置
    2. .env 中的所有參數都必須在此類別中定義對應的屬性
    3. 新增參數的標準流程:
       步驟 1: 在 .env 新增參數 (例如: NEW_PARAM=value)
       步驟 2: 在此類別新增對應屬性 (例如: NEW_PARAM: str = "default")
    4. 參數定義規則:
       - 必填參數: 不給預設值 (例如: DB_USER: str)
       - 可選參數: 給預設值 (例如: LOG_LEVEL: str = "INFO")
       - Pydantic 會自動進行類型轉換和驗證
    5. 如果只在 .env 新增而未在此定義,該參數會被忽略且無法使用

    參考文件: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    # ===========================================
    # 服務器設定
    # ===========================================
    ENVIRONMENT: str = "development"  # development | production
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8002
    SERVER_RELOAD: bool = True
    CORS_ALLOW_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"

    # ===========================================
    # Redis 設定
    # ===========================================
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Redis 聊天快取 TTL（小時）
    REDIS_CHAT_CACHE_TTL_HOURS: int = 2

    # ===========================================
    # PostgreSQL 資料庫設定
    # ===========================================
    DB_DRIVER: str = "postgresql+psycopg"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_CONNECT_TIMEOUT: int = 5        # 連線超時（秒）
    DB_COMMAND_TIMEOUT: int = 30       # SQL 執行超時（秒）

    # ===========================================
    # JWT 認證設定
    # ===========================================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===========================================
    # 使用者註冊設定
    # ===========================================
    ALLOW_PUBLIC_REGISTRATION: bool = False  # B2B 系統預設關閉公開註冊

    # ===========================================
    # Cookie 安全設定
    # ===========================================
    COOKIE_SECURE: bool = False  # 生產環境應設為 True (需 HTTPS)
    COOKIE_SAMESITE: str = "lax"  # lax | strict | none
    COOKIE_HTTPONLY: bool = True
    COOKIE_DOMAIN: str | None = None  # 可選，跨子域共享時設定

    # ===========================================
    # 速率限制設定（按級別配置）
    # ===========================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 500       # 一般 API 每分鐘限制
    RATE_LIMIT_SENSITIVE: int = 10      # 敏感 API 每分鐘限制
    RATE_LIMIT_STRICT: int = 5          # 嚴格限制 API 每分鐘限制（未來擴展）

    # ===========================================
    # 上傳文件配置
    # ===========================================
    UPLOAD_FILES_ROOT: str
    UPLOAD_MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_ALLOWED_EXTENSIONS: str = "json,pdf,txt,md"

    # 遞迴文字分塊設定
    RECURSIVE_TEXT_CHUNK_SIZE: int = 1000
    RECURSIVE_TEXT_CHUNK_OVERLAP: int = 200

    # ===========================================
    # 聊天附件上傳配置
    # ===========================================
    CHAT_FILE_UPLOAD_ENABLED: bool = True
    CHAT_MAX_FILES_PER_MESSAGE: int = 5

    # 圖片配置
    CHAT_IMAGE_MAX_SIZE: int = 10485760  # 10MB
    CHAT_IMAGE_ALLOWED_FORMATS: str = "jpg,jpeg,png,gif,webp,bmp"
    CHAT_IMAGE_COMPRESS_ENABLED: bool = True
    CHAT_IMAGE_MAX_WIDTH: int = 1920
    CHAT_IMAGE_MAX_HEIGHT: int = 1080
    CHAT_IMAGE_QUALITY: int = 85

    # PDF 配置
    CHAT_PDF_ENABLED: bool = False
    CHAT_PDF_MAX_SIZE: int = 52428800  # 50MB
    CHAT_PDF_MAX_PAGES: int = 10
    CHAT_PDF_RENDER_DPI: int = 300  # PDF 渲染解析度

    # 檔案儲存
    CHAT_FILES_STORAGE_PATH: str

    # ===========================================
    # 模型存放路徑
    # ===========================================
    HUGGINGFACE_CACHE_DIR: str

    # ===========================================
    # LLM 提供商設定
    # ===========================================
    LLM_PROVIDER: str = "ollama"

    # Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:12b"
    OLLAMA_MAX_TOKENS: int = 2048
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_TIMEOUT: float = 30.0
    OLLAMA_KEEP_ALIVE: str = "5m"
    OLLAMA_TOP_P: float = 0.6  # Top-p 採樣參數（核採樣）
    OLLAMA_TOP_K: int = 40  # Top-k 採樣參數

    # vLLM 配置
    VLLM_BASE_URL: str = "http://localhost:8001"
    VLLM_MODEL: str = "Qwen3-VL-8B-Instruct-AWQ-4bit"
    VLLM_MAX_TOKENS: int = 4096
    VLLM_TEMPERATURE: float = 0.7
    VLLM_TIMEOUT: float = 60.0
    VLLM_TOP_P: float = 0.95
    VLLM_TOP_K: int = 20

    # OpenAI 原生配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: float = 60.0
    OPENAI_TOP_P: float = 1.0
    OPENAI_ORGANIZATION: str = ""

    # Azure OpenAI 配置
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_MAX_TOKENS: int = 4096
    AZURE_OPENAI_TEMPERATURE: float = 0.7
    AZURE_OPENAI_TIMEOUT: float = 60.0
    AZURE_OPENAI_TOP_P: float = 1.0

    # Google Gemini 配置
    GOOGLE_API_KEY: str = ""
    GOOGLE_GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_GEMINI_MAX_TOKENS: int = 4096
    GOOGLE_GEMINI_TEMPERATURE: float = 0.7
    GOOGLE_GEMINI_TIMEOUT: float = 60.0
    GOOGLE_GEMINI_TOP_P: float = 1.0
    GOOGLE_GEMINI_TOP_K: int = 40

    # ===========================================
    # Sandbox 配置（Agent 程式碼執行環境）
    # ===========================================
    SANDBOX_ENABLED: bool = False
    SANDBOX_IMAGE: str = "metora-sandbox:latest"
    SANDBOX_TIMEOUT: int = 60               # 預設執行超時（秒）
    SANDBOX_MEMORY_LIMIT: str = "512m"      # 記憶體限制
    SANDBOX_CPU_LIMIT: float = 1.0          # CPU 限制（核數）
    SANDBOX_NETWORK_ENABLED: bool = False   # 是否允許網路存取
    SANDBOX_NETWORK_NAME: str = ""          # Docker network 名稱（啟用網路時使用）
    SANDBOX_MAX_OUTPUT_SIZE: int = 1048576  # 最大輸出大小（1MB）
    SANDBOX_MAX_ITERATIONS: int = 8         # Agent 最大工具調用迭代次數

    # ===========================================
    # Graph 配置
    # ===========================================
    # Graph 整體對話記憶輪數（用於 LLM 最終回應）
    GRAPH_MEMORY_TURNS: int = 5

    # 查詢重構使用的上下文輪數（用於意圖判別和查詢重構）
    QUERY_REWRITE_CONTEXT_TURNS: int = 3

    # Graph 執行超時時間（秒,預設 4 分鐘）
    # 包含多個節點執行,建議設為 HTTP 超時的 3-4 倍
    GRAPH_EXECUTION_TIMEOUT: float = 240.0

    # ===========================================
    # RAG 系統設定
    # ===========================================
    # 嵌入模型配置
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_DEVICE: str = "cuda"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_MODEL_POOL_SIZE: int = Field(
        default=1,
        description="Embedding 模型池大小（建議 2-4，適用於併發 < 100 的企業場景）"
    )

    # 重排序配置
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"
    RERANKER_DEVICE: str = "cuda"
    RERANKER_USE_FP16: bool = True
    RERANKER_BATCH_SIZE: int = 32
    RERANKER_MAX_LENGTH: int = 512
    RERANKER_MODEL_POOL_SIZE: int = Field(
        default=1,
        description="Reranker 模型池大小（建議 2-4，適用於併發 < 100 的企業場景）"
    )

    # 分數正規化配置
    RERANKER_SCORE_NORMALIZATION: bool = Field(
        default=True,
        description="是否對 Reranker 分數進行正規化 (Sigmoid 轉換)"
    )
    RRF_SCORE_NORMALIZATION: bool = Field(
        default=True,
        description="是否對 RRF 分數進行正規化 (Sigmoid 轉換)"
    )
    RRF_SIGMOID_SCALE: float = Field(
        default=1000.0,
        description="RRF Sigmoid 轉換的縮放因子"
    )
    RRF_SIGMOID_SHIFT: float = Field(
        default=0.012,
        description="RRF Sigmoid 轉換的平移因子 (中心點)"
    )

    # 向量資料庫配置
    VECTOR_STORE_PROVIDER: str = "chroma"  # chroma | pgvector
    VECTOR_STORE_DIR: str  # ChromaDB 持久化目錄（VECTOR_STORE_PROVIDER=chroma 時使用）
    VECTOR_DISTANCE_METRIC: str = "cosine"  # cosine | l2 | ip (推薦: cosine 適合文本語義相似度)
    VECTOR_SEARCH_SCORE_THRESHOLD: float = 0.6  # 向量檢索相關性閾值 (0.0-1.0)

    # PGVector 專用配置（VECTOR_STORE_PROVIDER=pgvector 時使用）
    PGVECTOR_TABLE_PREFIX: str = "vector_"  # PGVector 資料表前綴
    PGVECTOR_EMBEDDING_DIM: int = 1024  # 向量維度（需與 Embedding 模型輸出維度一致）

    # 檢索結果數量配置
    RAG_RETRIEVER_TOP_K: int = 3

    # ===========================================
    # 訊息反饋設定
    # ===========================================
    # 問題標籤列表（用於使用者反饋）
    FEEDBACK_ISSUE_TAGS: list[str] = [
        "回答不準確",
        "內容太簡短",
        "格式錯誤",
        "檢索結果不相關",
        "語氣不恰當"
    ]

    # ===========================================
    # Pydantic 設定
    # ===========================================
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),  # 從專案根目錄讀取 (使用絕對路徑)
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ===========================================
    # 計算屬性
    # ===========================================
    @computed_field
    @property
    def is_production(self) -> bool:
        """判斷是否為生產環境"""
        return self.ENVIRONMENT == "production"
    
    @computed_field
    @property
    def is_development(self) -> bool:
        """判斷是否為開發環境"""
        return self.ENVIRONMENT == "development"
    
    # SQL 日誌控制
    SHOW_SQL: bool = False  # 是否顯示 SQL 查詢日誌
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """動態組合資料庫連線字串"""
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @computed_field
    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """將 CORS origins 轉換為列表"""
        if self.CORS_ALLOW_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",")]

    @computed_field
    @property
    def UPLOAD_ALLOWED_EXTENSIONS_LIST(self) -> list[str]:
        """將允許的副檔名轉換為列表"""
        return [ext.strip() for ext in self.UPLOAD_ALLOWED_EXTENSIONS.split(",")]

    @computed_field
    @property
    def CHAT_IMAGE_ALLOWED_FORMATS_LIST(self) -> list[str]:
        """將聊天圖片允許的格式轉換為列表"""
        return [fmt.strip().lower() for fmt in self.CHAT_IMAGE_ALLOWED_FORMATS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    取得設定單例
    使用 lru_cache 確保只建立一次實例
    """
    return Settings()


# 便捷別名
settings = get_settings()
