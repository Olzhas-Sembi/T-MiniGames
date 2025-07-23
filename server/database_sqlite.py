"""
Настройка базы данных SQLite для тестирования Telegram Mini Games
Упрощенная версия для быстрого тестирования
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

# Конфигурация БД
from server.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=True  # Для разработки
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Игровая статистика
    stars_balance = Column(Integer, default=0)  # Баланс звезд
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    game_rooms = relationship("GameRoom", back_populates="creator")
    participations = relationship("GameParticipation", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

# Модель игровой комнаты
class GameRoom(Base):
    __tablename__ = "game_rooms"
    
    id = Column(String, primary_key=True)
    game_type = Column(String, nullable=False)  # dice, rps, cards21, lotto, case_battle, roulette
    status = Column(String, default="waiting")  # waiting, active, finished, cancelled
    
    # Настройки игры
    min_players = Column(Integer, default=1)
    max_players = Column(Integer, default=2)
    current_players = Column(Integer, default=0)
    bet_amount = Column(Integer, nullable=False)
    
    # Создатель и призовой фонд
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    prize_pool = Column(Integer, default=0)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Игровые данные
    game_data = Column(JSON, default=dict)  # Хранение состояния игры
    
    # Связи
    creator = relationship("User", back_populates="game_rooms")
    participations = relationship("GameParticipation", back_populates="room")

# Модель участия в игре
class GameParticipation(Base):
    __tablename__ = "game_participations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("game_rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Результаты
    position = Column(Integer, nullable=True)  # Место в игре (1 = победитель)
    score = Column(Integer, nullable=True)  # Очки/результат
    prize_won = Column(Integer, default=0)  # Выигранные звезды
    
    # Игровые данные участника
    player_data = Column(JSON, default=dict)  # Ходы, выборы и т.д.
    
    # Метаданные
    joined_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # Связи
    room = relationship("GameRoom", back_populates="participations")
    user = relationship("User", back_populates="participations")

# Модель транзакций
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Тип и сумма
    type = Column(String, nullable=False)  # bet, win, purchase, refund, stars_purchase, ton_deposit, ton_withdraw
    amount = Column(Integer, nullable=False)  # Может быть отрицательным для расходов
    description = Column(String, nullable=True)
    
    # Платежные данные
    payment_method = Column(String, nullable=True)  # telegram_stars, ton_connect, internal
    telegram_payment_id = Column(String, nullable=True)
    ton_transaction_hash = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, success, failed
    
    # Связанная игра (если применимо)
    room_id = Column(String, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="transactions")

# Модель NFT предметов
class NFTItem(Base):
    __tablename__ = "nft_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    
    # Характеристики NFT
    rarity = Column(String, nullable=False)  # common, uncommon, rare, epic, legendary
    nft_type = Column(String, nullable=False)  # avatar, card, sticker, frame, gift
    
    # Стоимость
    stars_value = Column(Integer, nullable=False)
    ton_value = Column(Numeric(precision=10, scale=9), nullable=True)
    
    # Настройки
    is_tradeable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Метаданные
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user_nfts = relationship("UserNFT", back_populates="nft_item")

# Модель NFT в инвентаре пользователя
class UserNFT(Base):
    __tablename__ = "user_nfts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    nft_item_id = Column(String, ForeignKey("nft_items.id"), nullable=False)
    
    # Когда и откуда получен
    acquired_at = Column(DateTime, default=datetime.utcnow)
    acquired_from = Column(String, nullable=False)  # case_battle, roulette, purchase, gift
    
    # Статус
    is_equipped = Column(Boolean, default=False)
    
    # Связи
    user = relationship("User")
    nft_item = relationship("NFTItem", back_populates="user_nfts")

# Модель кейсов
class Case(Base):
    __tablename__ = "cases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    
    # Цены
    price_stars = Column(Integer, nullable=False)
    price_ton = Column(Numeric(precision=10, scale=9), nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    case_items = relationship("CaseItem", back_populates="case")

# Модель предметов в кейсах
class CaseItem(Base):
    __tablename__ = "case_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    nft_item_id = Column(String, ForeignKey("nft_items.id"), nullable=False)
    
    # Параметры выпадения
    drop_chance = Column(Numeric(precision=5, scale=4), nullable=False)  # 0.0000 - 1.0000
    min_value = Column(Integer, nullable=False)
    max_value = Column(Integer, nullable=False)
    
    # Связи
    case = relationship("Case", back_populates="case_items")
    nft_item = relationship("NFTItem")

# Модель розыгрышей рулетки
class RouletteDraw(Base):
    __tablename__ = "roulette_draws"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Приз
    prize_nft_id = Column(String, ForeignKey("nft_items.id"), nullable=False)
    
    # Параметры
    target_amount = Column(Integer, nullable=False)  # Целевая сумма
    min_bet = Column(Integer, nullable=False)
    max_bet = Column(Integer, nullable=False)
    current_amount = Column(Integer, default=0)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Результат
    winner_id = Column(String, ForeignKey("users.id"), nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    prize_nft = relationship("NFTItem")
    winner = relationship("User")
    participations = relationship("RouletteParticipation", back_populates="draw")

# Модель участия в розыгрышах
class RouletteParticipation(Base):
    __tablename__ = "roulette_participations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draw_id = Column(String, ForeignKey("roulette_draws.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Ставка
    amount_bet = Column(Integer, nullable=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    draw = relationship("RouletteDraw", back_populates="participations")
    user = relationship("User")
