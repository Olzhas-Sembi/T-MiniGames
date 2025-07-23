"""
Обработка Telegram платежей
"""
from aiogram import Router, F
from aiogram.types import (
    Message, 
    PreCheckoutQuery, 
    LabeledPrice,
    CallbackQuery
)
from aiogram.exceptions import TelegramBadRequest

import logging
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..bot_config import get_bot
from config import Settings

logger = logging.getLogger(__name__)

# Роутер для платежей
payments_router = Router()

settings = Settings()


async def send_payment_invoice(
    chat_id: int, 
    stars: int, 
    price_cents: int
) -> bool:
    """
    Отправка инвойса для оплаты звёзд
    
    Args:
        chat_id: ID чата
        stars: Количество звёзд
        price_cents: Цена в центах (USD)
    """
    try:
        bot = get_bot()
        
        if not settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN:
            logger.error("TELEGRAM_PAYMENT_PROVIDER_TOKEN не установлен")
            return False
        
        # Создаем список цен
        prices = [LabeledPrice(label=f"{stars} звёзд", amount=price_cents)]
        
        # Отправляем инвойс
        await bot.send_invoice(
            chat_id=chat_id,
            title=f"Покупка {stars} звёзд",
            description=f"Пополнение баланса на {stars} звёзд для игр T-MiniGames",
            payload=f"stars_{stars}_{chat_id}",  # Полезная нагрузка для идентификации
            provider_token=settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN,
            currency="USD",
            prices=prices,
            start_parameter="purchase-stars",
            is_flexible=False,
            # Дополнительные параметры
            photo_url="https://your-domain.com/star-icon.png",  # Иконка звезды
            photo_size=512,
            photo_width=512,
            photo_height=512,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False
        )
        
        logger.info(f"Инвойс отправлен пользователю {chat_id} на сумму {price_cents/100}$ за {stars} звёзд")
        return True
        
    except TelegramBadRequest as e:
        logger.error(f"Ошибка отправки инвойса: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке инвойса: {e}")
        return False


@payments_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """
    Обработка пре-чекаут запроса
    Здесь можно провести дополнительные проверки перед оплатой
    """
    try:
        # Парсим payload
        payload = pre_checkout_query.invoice_payload
        logger.info(f"Pre-checkout query от {pre_checkout_query.from_user.id}, payload: {payload}")
        
        # Проверяем payload
        if not payload.startswith("stars_"):
            await pre_checkout_query.answer(
                ok=False,
                error_message="Некорректные данные платежа"
            )
            return
        
        # Можно добавить дополнительные проверки:
        # - Проверка лимитов пользователя
        # - Проверка блокировки аккаунта
        # - Валидация данных
        
        # Подтверждаем платеж
        await pre_checkout_query.answer(ok=True)
        logger.info(f"Pre-checkout одобрен для пользователя {pre_checkout_query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в pre_checkout_query: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Внутренняя ошибка сервера"
        )


@payments_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """
    Обработка успешного платежа
    """
    try:
        payment = message.successful_payment
        user_id = message.from_user.id
        
        # Парсим payload
        payload = payment.invoice_payload
        logger.info(f"Успешный платеж от {user_id}: {payload}")
        
        if not payload.startswith("stars_"):
            logger.error(f"Некорректный payload: {payload}")
            return
        
        # Извлекаем данные из payload
        try:
            _, stars_str, user_id_str = payload.split("_")
            stars = int(stars_str)
            expected_user_id = int(user_id_str)
        except (ValueError, IndexError):
            logger.error(f"Ошибка парсинга payload: {payload}")
            return
        
        # Проверяем соответствие пользователя
        if user_id != expected_user_id:
            logger.error(f"Несоответствие пользователя: {user_id} != {expected_user_id}")
            return
        
        # Получаем данные платежа
        amount_cents = payment.total_amount
        currency = payment.currency
        provider_payment_charge_id = payment.provider_payment_charge_id
        telegram_payment_charge_id = payment.telegram_payment_charge_id
        
        logger.info(f"""
Обработка платежа:
- Пользователь: {user_id}
- Звёзды: {stars}
- Сумма: {amount_cents/100} {currency}
- Provider ID: {provider_payment_charge_id}
- Telegram ID: {telegram_payment_charge_id}
""")
        
        # TODO: Записать в базу данных
        # await add_stars_to_user(user_id, stars)
        # await save_payment_record(user_id, stars, amount_cents, provider_payment_charge_id)
        
        # Отправляем подтверждение пользователю
        success_text = f"""
✅ <b>Платеж успешен!</b>

💰 Получено: ⭐ {stars} звёзд
💳 Сумма: ${amount_cents/100:.2f}
🆔 ID транзакции: {telegram_payment_charge_id[:8]}...

Звёзды зачислены на ваш баланс!
Теперь вы можете играть в игры 🎮
"""
        
        await message.answer(success_text)
        
        # Логируем успешную транзакцию
        logger.info(f"Платеж успешно обработан для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки успешного платежа: {e}")
        # Уведомляем администратора о проблеме
        await message.answer(
            "❌ Произошла ошибка при обработке платежа. "
            "Обратитесь в поддержку с ID транзакции."
        )


# Дополнительные утилиты для работы с платежами

async def create_custom_invoice(
    chat_id: int,
    title: str,
    description: str,
    prices: List[LabeledPrice],
    payload: str,
    **kwargs
) -> bool:
    """
    Создание кастомного инвойса
    """
    try:
        bot = get_bot()
        
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN,
            currency="USD",
            prices=prices,
            **kwargs
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка создания кастомного инвойса: {e}")
        return False


def get_stars_packages() -> List[tuple]:
    """
    Получить доступные пакеты звёзд
    Возвращает список кортежей (звёзды, цена_в_центах, описание)
    """
    return [
        (100, 200, "Стартовый пакет"),
        (500, 800, "Популярный выбор"),
        (1000, 1500, "Выгодно"),
        (2500, 3500, "Для профи"),
        (5000, 6000, "Максимум")
    ]


def calculate_bonus_stars(stars: int) -> int:
    """
    Рассчитать бонусные звёзды за покупку
    """
    if stars >= 5000:
        return int(stars * 0.2)  # 20% бонус
    elif stars >= 1000:
        return int(stars * 0.1)  # 10% бонус
    elif stars >= 500:
        return int(stars * 0.05)  # 5% бонус
    return 0
