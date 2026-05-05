import os
import typing
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings:
    VERSION: str = "0.1.0"
    APP_TITLE: str = "lightmo"
    PROJECT_NAME: str = "lightmo"
    APP_DESCRIPTION: str = "lightmo project"

    CORS_ORIGINS: typing.List = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    API_KEY: typing.Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    BASE_URL: typing.Optional[str] = os.getenv("DASHSCOPE_BASE_URL")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen-turbo")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))

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
