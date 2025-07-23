"""
Webhook обработчик для Telegram бота
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .bot_config import setup_bot, close_bot, get_bot, get_dispatcher
from config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    # Запуск
    logger.info("Запуск Telegram бота...")
    bot, dp = await setup_bot()
    
    # Устанавливаем webhook
    if settings.TELEGRAM_WEBHOOK_URL:
        try:
            await bot.set_webhook(
                url=settings.TELEGRAM_WEBHOOK_URL,
                secret_token=settings.TELEGRAM_WEBHOOK_SECRET
            )
            logger.info(f"Webhook установлен: {settings.TELEGRAM_WEBHOOK_URL}")
        except TelegramBadRequest as e:
            logger.error(f"Ошибка установки webhook: {e}")
    
    yield
    
    # Завершение
    logger.info("Остановка Telegram бота...")
    await close_bot()


def create_webhook_app() -> FastAPI:
    """
    Создание FastAPI приложения для webhook
    """
    app = FastAPI(
        title="Telegram Bot Webhook",
        lifespan=lifespan
    )
    
    @app.post("/webhook/telegram")
    async def telegram_webhook(request: Request):
        """
        Обработчик webhook от Telegram
        """
        try:
            # Проверяем secret token
            secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
                logger.warning(f"Неверный secret token: {secret_token}")
                raise HTTPException(status_code=403, detail="Forbidden")
            
            # Получаем данные
            data = await request.json()
            
            # Создаем Update объект
            update = Update(**data)
            
            # Получаем диспетчер и обрабатываем обновление
            dp = get_dispatcher()
            await dp.feed_update(bot=get_bot(), update=update)
            
            return {"ok": True}
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    @app.get("/webhook/health")
    async def health_check():
        """
        Проверка здоровья webhook
        """
        return {"status": "ok", "bot": "running"}
    
    return app


async def run_polling():
    """
    Запуск бота в режиме polling (для разработки)
    """
    logger.info("Запуск бота в режиме polling...")
    
    bot, dp = await setup_bot()
    
    try:
        # Удаляем webhook если есть
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удален, запуск polling...")
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await close_bot()


if __name__ == "__main__":
    # Запуск в режиме polling для тестирования
    asyncio.run(run_polling())
