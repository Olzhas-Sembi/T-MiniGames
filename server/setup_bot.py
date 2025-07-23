"""
Скрипт для автоматической настройки Menu Button через Bot API
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_menu_button():
    """Настройка Menu Button для Mini App"""
    try:
        from aiogram import Bot
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        webapp_url = os.getenv("TELEGRAM_WEBAPP_URL", "https://t-mini-games.vercel.app/")
        
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN не установлен")
            return False
        
        print(f"🔑 Настройка Menu Button для: {webapp_url}")
        
        bot = Bot(token=bot_token)
        
        # Настраиваем Menu Button
        menu_button = MenuButtonWebApp(
            text="🎮 Играть",
            web_app=WebAppInfo(url=webapp_url)
        )
        
        await bot.set_chat_menu_button(menu_button=menu_button)
        print("✅ Menu Button настроен!")
        
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"📱 Бот: @{me.username}")
        print(f"🌐 WebApp URL: {webapp_url}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки Menu Button: {e}")
        return False

async def set_bot_commands():
    """Настройка команд бота"""
    try:
        from aiogram import Bot
        from aiogram.types import BotCommand
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        bot = Bot(token=bot_token)
        
        commands = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="help", description="❓ Помощь"),
            BotCommand(command="profile", description="👤 Мой профиль"),
            BotCommand(command="balance", description="💰 Баланс звёзд"),
        ]
        
        await bot.set_my_commands(commands)
        print("✅ Команды бота настроены!")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки команд: {e}")
        return False

async def main():
    print("🤖 Настройка Telegram Bot для Mini App")
    print("=" * 50)
    
    # Настройка Menu Button
    menu_ok = await setup_menu_button()
    
    # Настройка команд
    commands_ok = await set_bot_commands()
    
    print("\n📋 Результаты:")
    print(f"Menu Button: {'✅' if menu_ok else '❌'}")
    print(f"Commands: {'✅' if commands_ok else '❌'}")
    
    if menu_ok:
        print("\n🎉 Готово! Теперь:")
        print("1. Найдите своего бота в Telegram")
        print("2. Нажмите на кнопку меню (три полоски) → '🎮 Играть'")
        print("3. Или отправьте /start")
    else:
        print("\n❌ Исправьте ошибки и повторите")

if __name__ == "__main__":
    asyncio.run(main())
