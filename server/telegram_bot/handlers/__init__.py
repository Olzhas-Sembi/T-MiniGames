"""
Регистрация всех обработчиков
"""
from aiogram import Dispatcher

from .commands import commands_router
from .payments import payments_router


def setup_handlers(dp: Dispatcher):
    """
    Регистрация всех роутеров
    """
    # Важно: роутер платежей должен быть зарегистрирован первым
    # для корректной обработки pre_checkout_query
    dp.include_router(payments_router)
    dp.include_router(commands_router)
