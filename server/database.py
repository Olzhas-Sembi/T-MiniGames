"""
Настройка базы данных PostgreSQL для Telegram Mini Games
Согласно ТЗ: система звезд, NFT, игровые комнаты, транзакции
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
    pool_recycle=300,
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

# Модели согласно ТЗ

class User(Base):
    """Пользователи системы с интеграцией Telegram"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Баланс звезд - основная валюта согласно ТЗ
    stars_balance = Column(Integer, default=0, nullable=False)
    
    # Статистика игрока
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Связи
    transactions = relationship("Transaction", back_populates="user")
    nfts = relationship("NFT", back_populates="owner")
    game_participations = relationship("GameParticipation", back_populates="user")

class GameRoom(Base):
    """Игровые комнаты - основа 'живого лобби' согласно ТЗ"""
    __tablename__ = "game_rooms"
    
    id = Column(String, primary_key=True)  # Короткий ID для пользователей
    game_type = Column(String, nullable=False)  # dice, cards, rps, lotto, case_battle, roulette
    status = Column(String, default="waiting")  # waiting, playing, finished, cancelled
    
    # Настройки комнаты
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=4)
    bet_amount = Column(Integer, nullable=False)  # Ставка в звездах
    
    # Создатель и игроки
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_players = Column(Integer, default=0)
    
    # Время жизни комнаты (60 секунд согласно ТЗ)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Игровое состояние (JSON для гибкости)
    game_state = Column(JSON, default=dict)
    game_seed = Column(String, nullable=True)  # Для честности
    nonce = Column(String, nullable=True)
    
    # Призовой фонд
    prize_pool = Column(Integer, default=0)
    winner_ids = Column(JSON, default=list)  # Список ID победителей
    
    # Связи
    creator = relationship("User")
    participations = relationship("GameParticipation", back_populates="room")

class GameParticipation(Base):
    """Участие игроков в комнатах"""
    __tablename__ = "game_participations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String, ForeignKey("game_rooms.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Статус участника
    status = Column(String, default="joined")  # joined, ready, playing, finished
    bet_paid = Column(Boolean, default=False)
    
    # Результаты игры (специфично для каждой игры)
    game_result = Column(JSON, default=dict)
    prize_won = Column(Integer, default=0)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="game_participations")
    room = relationship("GameRoom", back_populates="participations")

class Transaction(Base):
    """Все транзакции звезд согласно ТЗ"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Тип транзакции
    type = Column(String, nullable=False)  # deposit_telegram, deposit_ton, bet, win, refund
    amount = Column(Integer, nullable=False)  # Может быть отрицательным для расходов
    
    # Внешние данные
    telegram_payment_id = Column(String, nullable=True)
    ton_transaction_hash = Column(String, nullable=True)
    
    # Связанная игра (если применимо)
    game_room_id = Column(String, ForeignKey("game_rooms.id"), nullable=True)
    
    # Метаданные
    description = Column(String, nullable=True)
    transaction_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="transactions")

class NFT(Base):
    """NFT предметы согласно ТЗ (Case Battle, награды)"""
    __tablename__ = "nfts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Характеристики NFT
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    rarity = Column(String, nullable=False)  # common, rare, epic, legendary
    
    # Экономика
    estimated_value = Column(Integer, default=0)  # В звездах
    
    # Происхождение
    source_type = Column(String, nullable=False)  # case_opening, prize, gift
    source_game_id = Column(String, nullable=True)
    
    # TON блокчейн данные (опционально)
    ton_address = Column(String, nullable=True)
    ton_collection = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    owner = relationship("User", back_populates="nfts")

class NewsItem(Base):
    """Новости для агрегатора согласно ТЗ"""
    __tablename__ = "news_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    url = Column(String, nullable=False, unique=True)
    
    # Категоризация согласно ТЗ
    category = Column(String, nullable=False)  # gifts, nft, crypto, tech
    source = Column(String, nullable=False)  # telegram_channel, rss_feed
    source_name = Column(String, nullable=False)
    
    # Метаданные
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Для фильтрации дубликатов
    content_hash = Column(String, nullable=False, unique=True)

class RouletteGiveaway(Base):
    """Рулетка-розыгрыш согласно ТЗ"""
    __tablename__ = "roulette_giveaways"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Призы
    prize_type = Column(String, nullable=False)  # stars, nft
    prize_value = Column(Integer, nullable=False)
    prize_nft_id = Column(UUID(as_uuid=True), ForeignKey("nfts.id"), nullable=True)
    
    # Механика согласно ТЗ
    target_amount = Column(Integer, nullable=False)  # Целевая сумма
    collected_amount = Column(Integer, default=0)
    min_bet = Column(Integer, nullable=False)
    
    # Статус
    status = Column(String, default="active")  # active, completed, cancelled
    winner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    winner = relationship("User")
    prize_nft = relationship("NFT")

# Функции для работы с БД

def get_db():
    """Получить сессию БД (для dependency injection в FastAPI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Создать все таблицы"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def drop_db():
    """Удалить все таблицы (для разработки)"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")

if __name__ == "__main__":
    # Для тестирования
    init_db()
