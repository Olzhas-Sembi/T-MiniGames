"""
Обработчики команд Telegram бота
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from typing import Any
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# Создаем роутер для команд
commands_router = Router()


class UserStates(StatesGroup):
    """Состояния пользователя"""
    waiting_for_amount = State()


@commands_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    user = message.from_user
    
    # Получаем URL из конфигурации
    from config import Settings
    settings = Settings()
    webapp_url = settings.TELEGRAM_WEBAPP_URL or "https://t-mini-games.vercel.app/"
    
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Играть сейчас", web_app={
                "url": webapp_url
            })],
            [InlineKeyboardButton(text="💰 Купить звёзды", callback_data="buy_stars")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="📊 Рейтинг", callback_data="leaderboard")]
        ]
    )
    
    welcome_text = f"""
🎮 <b>Добро пожаловать в T-MiniGames!</b>

Привет, {user.first_name}! 👋

🎲 Играй в увлекательные мини-игры
⭐ Зарабатывай звёзды  
🏆 Соревнуйся с друзьями
💎 Собирай уникальные NFT

<b>Нажми "🎮 Играть сейчас" чтобы открыть игры!</b>
"""
    
    await message.answer(welcome_text, reply_markup=keyboard)
    await state.clear()


@commands_router.callback_query(F.data == "buy_stars")
async def process_buy_stars(callback: CallbackQuery, state: FSMContext):
    """Обработка покупки звёзд"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 100 звёзд - $2", callback_data="buy:100:200")],
            [InlineKeyboardButton(text="⭐ 500 звёзд - $8", callback_data="buy:500:800")],
            [InlineKeyboardButton(text="⭐ 1000 звёзд - $15", callback_data="buy:1000:1500")],
            [InlineKeyboardButton(text="⭐ 5000 звёзд - $60", callback_data="buy:5000:6000")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    
    text = """
💰 <b>Покупка звёзд</b>

Выберите количество звёзд для покупки:

⭐ Звёзды используются для:
• Участия в играх
• Покупки NFT кейсов
• Турниров и событий
"""
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@commands_router.callback_query(F.data.startswith("buy:"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    """Обработка платежа"""
    try:
        _, stars_str, price_str = callback.data.split(":")
        stars = int(stars_str)
        price_cents = int(price_str)  # Цена в центах
        
        # Сохраняем данные для обработки платежа
        await state.update_data({
            "stars": stars,
            "price_cents": price_cents
        })
        
        # Показываем информацию о платеже
        text = f"""
💳 <b>Подтверждение покупки</b>

Вы покупаете: ⭐ {stars} звёзд
Цена: ${price_cents/100:.2f}

Нажмите "Оплатить" для продолжения.
"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", callback_data="confirm_payment")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="buy_stars")]
            ]
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка обработки платежа: {e}")
        await callback.answer("Ошибка обработки платежа", show_alert=True)


@commands_router.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    """Отправка инвойса для оплаты"""
    from .payments import send_payment_invoice
    
    data = await state.get_data()
    stars = data.get("stars", 100)
    price_cents = data.get("price_cents", 200)
    
    success = await send_payment_invoice(
        chat_id=callback.message.chat.id,
        stars=stars,
        price_cents=price_cents
    )
    
    if success:
        await callback.answer("Инвойс отправлен!")
    else:
        await callback.answer("Ошибка отправки инвойса", show_alert=True)


@commands_router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль пользователя"""
    user = callback.from_user
    
    # TODO: Получить данные из базы данных
    text = f"""
👤 <b>Профиль</b>

🆔 ID: {user.id}
👤 Имя: {user.first_name}
⭐ Звёзды: 0
🏆 Рейтинг: 1500
🎮 Игр сыграно: 0
🏅 Побед: 0
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@commands_router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Показать таблицу лидеров"""
    text = """
📊 <b>Таблица лидеров</b>

🥇 1. Player1 - 2500 ⭐
🥈 2. Player2 - 2200 ⭐  
🥉 3. Player3 - 1900 ⭐
4. Player4 - 1750 ⭐
5. Player5 - 1600 ⭐

Ваша позиция: #42
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@commands_router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await cmd_start(callback.message, state)
    await callback.answer()


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = """
🆘 <b>Помощь</b>

Доступные команды:
/start - Главное меню
/help - Эта справка
/profile - Ваш профиль
/balance - Баланс звёзд

🎮 <b>Как играть:</b>
1. Нажми "Открыть игры" в главном меню
2. Выбери игру (Кости, Камень-ножницы-бумага)
3. Делай ставки звёздами
4. Выигрывай и поднимайся в рейтинге!

💰 <b>Покупка звёзд:</b>
Нажми "Купить звёзды" в меню для пополнения баланса.

❓ Вопросы? Напиши @support_bot
"""
    
    await message.answer(help_text)


@commands_router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile"""
    # Перенаправляем на callback обработчик
    from aiogram.types import CallbackQuery
    fake_callback = CallbackQuery(
        id="fake",
        from_user=message.from_user,
        chat_instance="fake",
        message=message,
        data="profile"
    )
    await show_profile(fake_callback)


@commands_router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Команда /balance"""
    # TODO: Получить реальный баланс из БД
    balance = 0
    
    text = f"""
💰 <b>Ваш баланс</b>

⭐ Звёзды: {balance}

Для пополнения баланса используйте /start → "Купить звёзды"
"""
    
    await message.answer(text)
