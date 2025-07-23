from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = Field("sqlite:///./test_minigames.db", env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field("", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBAPP_URL: str = Field("", env="TELEGRAM_WEBAPP_URL")
    TELEGRAM_WEBHOOK_SECRET: str = Field("", env="TELEGRAM_WEBHOOK_SECRET")
    TELEGRAM_WEBHOOK_URL: str = Field("", env="TELEGRAM_WEBHOOK_URL")
    TELEGRAM_PAYMENT_PROVIDER_TOKEN: str = Field("", env="TELEGRAM_PAYMENT_PROVIDER_TOKEN")

    # WebApp
    SECRET_KEY: str = Field("your-secret-key-here", env="SECRET_KEY")

    # API
    NEWS_API_KEY: str = Field("", env="NEWS_API_KEY")

    # TON
    TON_WALLET_ADDRESS: str = Field("", env="TON_WALLET_ADDRESS")
    TON_WALLET_SEED: str = Field("", env="TON_WALLET_SEED")
    TON_API_KEY: str = Field("", env="TON_API_KEY")
    TON_TESTNET: bool = Field(True, env="TON_TESTNET")
    TON_MANIFEST_URL: str = Field("https://your-domain.com/tonconnect-manifest.json", env="TON_MANIFEST_URL")

    # Платежная система
    STARS_TO_TON_RATE: float = Field(0.001, env="STARS_TO_TON_RATE")
    MIN_WITHDRAWAL_STARS: int = Field(1000, env="MIN_WITHDRAWAL_STARS")
    MAX_WITHDRAWAL_STARS: int = Field(100000, env="MAX_WITHDRAWAL_STARS")

    # NFT
    NFT_IMAGE_BASE_URL: str = Field("https://your-cdn.com/nft/", env="NFT_IMAGE_BASE_URL")
    DEFAULT_CASE_PRICE: int = Field(100, env="DEFAULT_CASE_PRICE")

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        "http://localhost:8081",
        "https://t-mini-games.vercel.app/",
        "https://t.me"
    ]

    class Config:
        env_file = ".env"


settings = Settings()
