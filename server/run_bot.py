"""
Запуск Telegram бота в режиме polling для разработки
"""
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загружаем переменные окружения
load_dotenv()

from telegram_bot.webhook import run_polling

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("🚀 Запуск Telegram бота в режиме polling...")
    print("📋 Убедитесь что установлены переменные окружения:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Установлен' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Не установлен'}")
    print(f"   TELEGRAM_PAYMENT_PROVIDER_TOKEN: {'✅ Установлен' if os.getenv('TELEGRAM_PAYMENT_PROVIDER_TOKEN') else '❌ Не установлен'}")
    print()
    print("🛑 Для остановки нажмите Ctrl+C")
    print()
    
    try:
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        print("\n✅ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска бота: {e}")
