import os
import typing
import warnings
from dotenv import load_dotenv

load_dotenv()


class Settings:
    VERSION: str = "0.1.0"
    APP_TITLE: str = "lightmo"
    PROJECT_NAME: str = "lightmo"
    APP_DESCRIPTION: str = "lightmo project"

    CORS_ORIGINS: typing.List = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    API_KEY: typing.Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    BASE_URL: typing.Optional[str] = os.getenv("DASHSCOPE_BASE_URL")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen-turbo")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "6"))

    RAG_ENABLE_QUERY_REWRITE: bool = os.getenv("RAG_ENABLE_QUERY_REWRITE", "true").lower() == "true"
    RAG_ENABLE_RERANK: bool = os.getenv("RAG_ENABLE_RERANK", "true").lower() == "true"
    RAG_ENABLE_HYBRID_SEARCH: bool = os.getenv("RAG_ENABLE_HYBRID_SEARCH", "true").lower() == "true"
    RAG_ENABLE_CONTEXT_COMPRESS: bool = os.getenv("RAG_ENABLE_CONTEXT_COMPRESS", "false").lower() == "true"

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", str(30)))
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

    def __init__(self):
        if not self.SECRET_KEY:
            raise RuntimeError("SECRET_KEY 环境变量未设置，禁止使用空密钥启动服务")
        if self.SECRET_KEY == "change-me-in-production":
            warnings.warn("SECRET_KEY 使用了默认值，请立即更换为安全的随机密钥", stacklevel=2)

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "lightmo")

    @property
    def TORTOISE_ORM(self) -> dict:
        return {
            "connections": {
                "postgres": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.DB_HOST,
                        "port": self.DB_PORT,
                        "user": self.DB_USER,
                        "password": self.DB_PASSWORD,
                        "database": self.DB_NAME,
                    },
                },
            },
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": "postgres",
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


settings = Settings()
