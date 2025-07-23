"""
Конфигурация Telegram бота на aiogram
"""
import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные экземпляры
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None


def create_bot() -> Bot:
    """Создание экземпляра бота"""
    settings = Settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
    
    return Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    """Создание диспетчера"""
    storage = MemoryStorage()
    return Dispatcher(storage=storage)


async def setup_bot():
    """Инициализация бота и диспетчера"""
    global bot, dp
    
    bot = create_bot()
    dp = create_dispatcher()
    
    # Импорт и регистрация роутеров
    from .handlers import setup_handlers
    setup_handlers(dp)
    
    logger.info("Telegram бот настроен")
    return bot, dp


async def close_bot():
    """Закрытие сессии бота"""
    global bot, dp
    if bot:
        await bot.session.close()
        logger.info("Telegram бот остановлен")


def get_bot() -> Bot:
    """Получение экземпляра бота"""
    if bot is None:
        raise RuntimeError("Бот не инициализирован. Вызовите setup_bot() сначала")
    return bot


def get_dispatcher() -> Dispatcher:
    """Получение экземпляра диспетчера"""
    if dp is None:
        raise RuntimeError("Диспетчер не инициализирован. Вызовите setup_bot() сначала")
    return dp
