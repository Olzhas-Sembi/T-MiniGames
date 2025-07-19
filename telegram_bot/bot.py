import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import aiohttp
import os
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-domain.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# URL вашего фронтенда
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.vercel.app")
API_URL = os.getenv("API_URL", "https://your-api.railway.app")

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class GameBot:
    def __init__(self):
        self.bot = bot
        
    async def get_user_balance(self, telegram_id: str) -> int:
        """Получить баланс пользователя из API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/api/player/{telegram_id}/balance") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("balance", 1000)
                    return 1000  # Стартовый баланс
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 1000

    async def create_user_if_not_exists(self, user: types.User) -> None:
        """Создать пользователя в системе если его нет"""
        try:
            async with aiohttp.ClientSession() as session:
                user_data = {
                    "telegram_id": str(user.id),
                    "username": user.username or f"user_{user.id}",
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
                async with session.post(f"{API_URL}/api/player/create", json=user_data) as resp:
                    if resp.status in [200, 201]:
                        logger.info(f"User {user.id} created/updated successfully")
                    else:
                        logger.warning(f"Failed to create user {user.id}: {resp.status}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")

game_bot = GameBot()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    await game_bot.create_user_if_not_exists(message.from_user)
    
    # Проверяем, есть ли параметр для присоединения к комнате
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("join_"):
        room_id = args[1].replace("join_", "")
        webapp_url = f"{WEBAPP_URL}?room_id={room_id}"
        welcome_text = f"🎮 Вас пригласили в игру!\n\nПрисоединяйтесь к комнате: `{room_id}`"
    else:
        webapp_url = WEBAPP_URL
        welcome_text = "🎮 Добро пожаловать в Mini Games Live!"

    # Создаем клавиатуру с кнопкой для открытия Web App
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Играть", 
            web_app=WebAppInfo(url=webapp_url)
        )],
        [InlineKeyboardButton(
            text="💰 Мой баланс", 
            callback_data="balance"
        )],
        [InlineKeyboardButton(
            text="📋 Правила игр", 
            callback_data="rules"
        )]
    ])

    await message.answer(
        f"{welcome_text}\n\n"
        "🎲 **Доступные игры:**\n"
        "• Кубики - бросайте и выигрывайте!\n"
        "• Карты 21 - классическая игра\n"
        "• Камень-Ножницы-Бумага - для всех возрастов\n\n"
        "💫 Играйте с друзьями в реальном времени!\n"
        "⭐ Зарабатывайте звёзды и побеждайте!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("balance"))
async def balance_command(message: types.Message):
    """Показать баланс пользователя"""
    await game_bot.create_user_if_not_exists(message.from_user)
    balance = await game_bot.get_user_balance(str(message.from_user.id))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Играть", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await message.answer(
        f"💰 **Ваш баланс:** {balance} ⭐\n\n"
        "Зарабатывайте больше звёзд, побеждая в играх!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Показать помощь"""
    help_text = """
🎮 **Mini Games Live - Помощь**

**Доступные команды:**
• /start - Начать игру
• /balance - Показать баланс
• /help - Эта справка

**Как играть:**
1. Нажмите "🚀 Играть" чтобы открыть приложение
2. Выберите "🔴 LIVE Игры" для игры с друзьями
3. Создайте комнату или присоединитесь к существующей
4. Пригласите друзей через ссылку
5. Играйте и выигрывайте звёзды!

**Правила игр:**
🎲 **Кубики** - у кого больше сумма, тот победил
🃏 **Карты 21** - наберите 21 или ближе к 21
✂️ **РПС** - камень-ножницы-бумага для нескольких игроков

**Поддержка:** @your_support_username
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Играть", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "balance")
async def balance_callback(callback_query: types.CallbackQuery):
    """Обработчик кнопки баланса"""
    await game_bot.create_user_if_not_exists(callback_query.from_user)
    balance = await game_bot.get_user_balance(str(callback_query.from_user.id))
    
    await callback_query.answer(f"Ваш баланс: {balance} ⭐")

@dp.callback_query(lambda c: c.data == "rules")
async def rules_callback(callback_query: types.CallbackQuery):
    """Обработчик кнопки правил"""
    rules_text = """
🎲 **Кубики:**
Каждый игрок бросает 2 кубика. У кого больше сумма - тот победил. При ничьей автоматический переброс.

🃏 **Карты 21:**
Цель - набрать 21 очко или ближе к 21, не превысив. Туз = 1 или 11. Ходы по очереди, 15 секунд на ход.

✂️ **Камень-Ножницы-Бумага:**
Все игроки одновременно выбирают. Камень бьёт ножницы, ножницы - бумагу, бумага - камень.

💰 **Призы:**
Победитель забирает весь банк. При ничьей ставки возвращаются.
    """
    
    await callback_query.answer(rules_text, show_alert=True)

async def webhook_handler(request):
    """Обработчик webhook от Telegram"""
    try:
        update = types.Update.model_validate(await request.json())
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)

async def setup_webhook():
    """Настройка webhook"""
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

async def main():
    """Главная функция"""
    # Настройка webhook
    await setup_webhook()
    
    # Создание web приложения
    app = web.Application()
    
    # Обработчик webhook
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    # Здоровье сервера
    async def health(request):
        return web.json_response({"status": "ok", "bot": "running"})
    
    app.router.add_get("/health", health)
    
    # Информация о боте
    async def bot_info(request):
        try:
            me = await bot.get_me()
            return web.json_response({
                "bot_username": me.username,
                "bot_name": me.first_name,
                "webhook_url": WEBHOOK_URL,
                "webapp_url": WEBAPP_URL
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    app.router.add_get("/bot/info", bot_info)
    
    logger.info("Bot server starting...")
    return app

if __name__ == "__main__":
    # Запуск в режиме polling для разработки
    async def dev_mode():
        logger.info("Starting bot in development mode (polling)")
        await bot.delete_webhook()
        await dp.start_polling(bot)
    
    if os.getenv("DEV_MODE", "true") == "true":
        asyncio.run(dev_mode())
    else:
        # Запуск webhook сервера для продакшена
        app = asyncio.run(main())
        web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
