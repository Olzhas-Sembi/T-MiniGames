"""
Тестовый скрипт для проверки aiogram интеграции
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_bot_connection():
    """Тест подключения к боту"""
    try:
        from aiogram import Bot
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN не установлен в .env файле")
            return False
        
        print(f"🔑 Токен: {bot_token[:10]}...")
        
        bot = Bot(token=bot_token)
        
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username} ({me.first_name})")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        print(f"🔗 Webhook URL: {webhook_info.url or 'Не установлен'}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")
        return False

async def test_payment_token():
    """Тест токена платежей"""
    payment_token = os.getenv("TELEGRAM_PAYMENT_PROVIDER_TOKEN")
    if payment_token:
        print(f"💳 Payment token: {payment_token[:10]}...")
        return True
    else:
        print("⚠️  TELEGRAM_PAYMENT_PROVIDER_TOKEN не установлен")
        return False

async def main():
    print("🧪 Тестирование Telegram Bot интеграции")
    print("=" * 50)
    
    # Тест подключения
    bot_ok = await test_bot_connection()
    
    # Тест токена платежей
    payment_ok = await test_payment_token()
    
    print("\n📋 Результаты:")
    print(f"Bot API: {'✅' if bot_ok else '❌'}")
    print(f"Payments: {'✅' if payment_ok else '⚠️'}")
    
    if bot_ok:
        print("\n🚀 Готов к запуску! Используйте:")
        print("   python run_bot.py")
    else:
        print("\n❌ Исправьте ошибки перед запуском")
        print("   1. Получите токен у @BotFather")
        print("   2. Добавьте TELEGRAM_BOT_TOKEN в .env")

if __name__ == "__main__":
    asyncio.run(main())
