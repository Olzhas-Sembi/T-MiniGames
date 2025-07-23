"""
Конфигурация приложения
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./test_minigames.db"  # Временно используем SQLite для тестирования
    )
    
    # Redis (для кэширования и очередей)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBAPP_URL: str = os.getenv("TELEGRAM_WEBAPP_URL", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    # WebApp
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # API Keys
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # TON Integration
    TON_WALLET_ADDRESS: str = os.getenv("TON_WALLET_ADDRESS", "")
    TON_WALLET_SEED: str = os.getenv("TON_WALLET_SEED", "")
    TON_API_KEY: str = os.getenv("TON_API_KEY", "")
    TON_TESTNET: bool = os.getenv("TON_TESTNET", "true").lower() == "true"
    TON_MANIFEST_URL: str = os.getenv("TON_MANIFEST_URL", "https://your-domain.com/tonconnect-manifest.json")
    
    # Платежная система
    STARS_TO_TON_RATE: float = float(os.getenv("STARS_TO_TON_RATE", "0.001"))  # 1000 звезд = 1 TON
    MIN_WITHDRAWAL_STARS: int = int(os.getenv("MIN_WITHDRAWAL_STARS", "1000"))
    MAX_WITHDRAWAL_STARS: int = int(os.getenv("MAX_WITHDRAWAL_STARS", "100000"))
    
    # NFT система
    NFT_IMAGE_BASE_URL: str = os.getenv("NFT_IMAGE_BASE_URL", "https://your-cdn.com/nft/")
    DEFAULT_CASE_PRICE: int = int(os.getenv("DEFAULT_CASE_PRICE", "100"))
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "http://localhost:5174",
        "https://your-domain.com",
        "https://t.me"
    ]
    
    class Config:
        env_file = ".env"


# Создаем единственный экземпляр настроек
settings = Settings()
