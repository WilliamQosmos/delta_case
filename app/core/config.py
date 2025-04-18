import secrets
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore", case_sensitive=True)
    PROJECT_NAME: str = "Delivery Service API"
    API_V1_STR: str = ""
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # CORS
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl | Literal["*"]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)

    # База данных
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: str
    MYSQL_DATABASE: str
    SQLALCHEMY_DATABASE_URI: str | None = None

    @model_validator(mode="after")
    def _assemble_db_connection(self) -> Self:
        if isinstance(self.SQLALCHEMY_DATABASE_URI, str):
            return self
        self.SQLALCHEMY_DATABASE_URI = f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        return self

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # RabbitMQ
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_VHOST: str = "/"

    # Currency API
    CURRENCY_API_URL: str = "https://www.cbr-xml-daily.ru/daily_json.js"
    CURRENCY_CACHE_TTL: int = 3600  # 1 час

    # Сессия
    SESSION_COOKIE_NAME: str = "delivery_session"
    SESSION_COOKIE_MAX_AGE: int = 60 * 60 * 24 * 30  # 30 дней


settings = Settings()
