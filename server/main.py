from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import asyncio
import logging
import os
from typing import Dict, List
from server.models import (
    CreateRoomRequest, RoomJoinRequest, PlayerActionRequest, 
    GameType, Room, Player, RoomUpdate
)
from server.room_manager import RoomManager
from server.telegram_news_service import telegram_news_service
from server.database_sqlite import get_db, User, GameRoom, Transaction, SessionLocal
from server.config import settings
from server.game_api import router as game_router
from server.games.database_dice import dice_router
from server.games.database_rps import rps_router

# Импортируем новые API для платежей и NFT
from server.api.payments import router as payments_router, nft_router
from server.api.nft import router as nft_api_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Mini Games API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
        "https://t-mini-games.vercel.app",
        "https://t-minigames.onrender.com",
        "https://t.me",
        "https://yourusername.github.io"  # ← Добавь это
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем роутеры
app.include_router(payments_router)  # Платежная система
app.include_router(nft_router)       # NFT система
app.include_router(game_router)      # Игровые API
app.include_router(dice_router)      # Кубики
app.include_router(rps_router)       # Камень-ножницы-бумага

# Глобальный менеджер комнат
room_manager = RoomManager()

# Подключение роутеров
app.include_router(game_router)
app.include_router(dice_router)
app.include_router(rps_router)
app.include_router(payments_router)
app.include_router(nft_router)
app.include_router(nft_api_router)

@app.get("/")
async def root():
    return {"message": "Telegram Mini Games API", "status": "running", "database": "connected"}

# Telegram Webhook
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Webhook для Telegram бота
    """
    try:
        # Проверяем secret token если установлен
        if settings.TELEGRAM_WEBHOOK_SECRET:
            secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
                logger.warning(f"Неверный secret token в webhook")
                raise HTTPException(status_code=403, detail="Forbidden")
        
        # Получаем данные обновления
        data = await request.json()
        logger.info(f"Получено обновление от Telegram: {data}")
        
        # TODO: Обработка обновлений через aiogram
        # Пока что просто логируем
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Ошибка обработки Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# API для работы с пользователями
@app.get("/api/users/{telegram_id}")
async def get_user(telegram_id: str, db: Session = Depends(get_db)):
    """Получить информацию о пользователе по Telegram ID"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "stars_balance": user.stars_balance,
        "total_games": user.total_games,
        "wins": user.wins
    }

@app.post("/api/users")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверяем, не существует ли уже пользователь
    existing_user = db.query(User).filter(User.telegram_id == user_data["telegram_id"]).first()
    if existing_user:
        return {"message": "User already exists", "user_id": str(existing_user.id)}
    
    # Создаем нового пользователя
    new_user = User(
        telegram_id=user_data["telegram_id"],
        username=user_data.get("username"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        stars_balance=100  # Стартовый баланс
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully",
        "user_id": str(new_user.id),
        "stars_balance": new_user.stars_balance
    }

@app.post("/api/users/{telegram_id}/add-stars")
async def add_stars(telegram_id: str, amount: int, db: Session = Depends(get_db)):
    """Добавить звезды пользователю (для тестирования)"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.stars_balance += amount
    
    # Создать транзакцию
    transaction = Transaction(
        user_id=user.id,
        type="stars_purchase",
        amount=amount,
        description=f"Added {amount} stars for testing"
    )
    db.add(transaction)
    db.commit()
    
    return {
        "message": f"Added {amount} stars",
        "new_balance": user.stars_balance
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "rooms_count": len(room_manager.rooms)}

# REST API endpoints

@app.post("/api/rooms/create")
async def create_room(request: CreateRoomRequest):
    """
    Создаёт новую игровую комнату (лобби).
    Args:
        request (CreateRoomRequest): параметры создания комнаты
    Returns:
        dict: результат создания, данные комнаты и ссылка-приглашение
    """
    try:
        room = await room_manager.create_room(
            creator_id=request.player_id,
            telegram_id=request.telegram_id,
            username=request.username,
            game_type=request.game_type,
            bet_amount=request.bet_amount
        )
        
        return {
            "success": True,
            "room": room.dict(),
            "invite_link": room.get_invite_link()
        }
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rooms/join")
async def join_room(request: RoomJoinRequest):
    """
    Присоединяет игрока к комнате.
    Args:
        request (RoomJoinRequest): параметры присоединения
    Returns:
        dict: результат, данные комнаты
    """
    try:
        room = await room_manager.join_room(
            player_id=request.player_id,
            telegram_id=request.telegram_id,
            username=request.username,
            room_id=request.room_id
        )
        
        if not room:
            raise HTTPException(status_code=404, detail="Комната не найдена или заполнена")
        
        return {
            "success": True,
            "room": room.dict()
        }
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rooms/available/{game_type}")
async def get_available_rooms(game_type: GameType, max_bet: int = None):
    """
    Получить доступные комнаты для матчмейкинга.
    Args:
        game_type (GameType): тип игры
        max_bet (int, optional): максимальная ставка
    Returns:
        dict: список комнат
    """
    try:
        rooms = room_manager.get_available_rooms(game_type, max_bet)
        return {
            "success": True,
            "rooms": [room.dict() for room in rooms]
        }
    except Exception as e:
        logger.error(f"Error getting available rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rooms/{room_id}")
async def get_room_info(room_id: str):
    """Получить информацию о комнате"""
    if room_id not in room_manager.rooms:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    room = room_manager.rooms[room_id]
    return {
        "success": True,
        "room": room.dict()
    }

@app.post("/api/rooms/{room_id}/ready")
async def ready_player(room_id: str, player_id: str):
    """Игрок подтверждает готовность (оплачивает ставку)"""
    try:
        room = await room_manager.ready_player(player_id)
        if not room:
            raise HTTPException(status_code=400, detail="Ошибка подтверждения готовности")
        
        return {
            "success": True,
            "room": room.dict()
        }
    except Exception as e:
        logger.error(f"Error setting player ready: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint для реального времени
@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    """
    WebSocket endpoint для реального времени (игровые события, обновления).
    Args:
        websocket (WebSocket): соединение
        player_id (str): ID игрока
    """
    await websocket.accept()
    await room_manager.connect_player(player_id, websocket)
    
    try:
        logger.info(f"Player {player_id} connected via WebSocket")
        
        while True:
            # Получаем сообщения от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action_type = message.get("action")
            
            if action_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            elif action_type == "dice_action":
                # Действие в игре кубики
                room_id = room_manager.player_to_room.get(player_id)
                if room_id:
                    dice_action = message.get("dice_action", "roll")  # "roll"
                    await room_manager.handle_dice_action(player_id, room_id, dice_action)
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "data": {"message": "Player not in any room"}
                    }))
            
            elif action_type == "rps_choice":
                # Выбор в камень-ножницы-бумага
                choice = message.get("choice")  # "rock", "paper", "scissors"
                await room_manager.handle_rps_choice(player_id, choice)
            
            elif action_type == "ready":
                # Игрок готов (оплачивает ставку)
                await room_manager.ready_player(player_id)
            
            else:
                logger.warning(f"Unknown action from player {player_id}: {action_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected")
        await room_manager.disconnect_player(player_id)
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id}: {e}")
        await room_manager.disconnect_player(player_id)

# Дополнительные endpoints для статистики и отладки

@app.get("/api/debug/rooms")
async def debug_rooms():
    """Отладочный endpoint для просмотра всех комнат"""
    return {
        "rooms": {room_id: room.dict() for room_id, room in room_manager.rooms.items()},
        "matchmaker_queue": {
            game_type.value: queue for game_type, queue in room_manager.matchmaker_queue.items()
        },
        "active_connections": len(room_manager.player_connections)
    }

@app.get("/api/player/{player_id}/status")
async def get_player_status(player_id: str):
    """Получить статус игрока"""
    room_id = room_manager.player_to_room.get(player_id)
    is_connected = player_id in room_manager.player_connections
    
    return {
        "player_id": player_id,
        "current_room": room_id,
        "is_connected": is_connected,
        "room_info": room_manager.rooms.get(room_id, {}).dict() if room_id else None
    }

# Telegram Integration Endpoints

@app.post("/api/player/create")
async def create_or_update_player(request: dict):
    """Создать или обновить игрока из Telegram"""
    telegram_id = request.get("telegram_id")
    username = request.get("username", f"user_{telegram_id}")
    
    # Здесь можно добавить логику сохранения в базу данных
    # Пока просто возвращаем успех
    return {
        "telegram_id": telegram_id,
        "username": username,
        "balance": 1000,  # Стартовый баланс
        "status": "created"
    }

@app.get("/api/player/{telegram_id}/balance")
async def get_player_balance(telegram_id: str):
    """Получить баланс игрока по Telegram ID"""
    # TODO: Интеграция с базой данных
    return {
        "telegram_id": telegram_id,
        "balance": 1000  # Пока заглушка
    }

@app.post("/api/player/{telegram_id}/balance/add")
async def add_balance(telegram_id: str, request: dict):
    """Добавить баланс игроку (для пополнения через Telegram Stars)"""
    amount = request.get("amount", 0)
    
    # TODO: Проверка платежа через Telegram
    # TODO: Обновление баланса в базе данных
    
    return {
        "telegram_id": telegram_id,
        "added": amount,
        "new_balance": 1000 + amount
    }

@app.get("/api/rooms/{room_id}/invite")
async def get_room_invite_info(room_id: str):
    """Получить информацию о комнате для приглашения"""
    room = room_manager.rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room_id": room_id,
        "game_type": room.game_type,
        "bet_amount": room.bet_amount,
        "players_count": len(room.players),
        "max_players": room.max_players,
        "can_join": room.can_join(),
        "creator": room.players[0].username if room.players else "Unknown"
    }

# News API Endpoints

@app.get("/api/news")
async def get_news(category: str = "all", limit: int = 50):
    """
    Получить новости из всех источников (Telegram + RSS).
    Args:
        category (str): категория новостей
        limit (int): лимит записей
    Returns:
        dict: новости, источники, категория
    """
    try:
        news = await telegram_news_service.get_all_news(category=category, limit=limit)
        return {
            "status": "success",
            "data": news,
            "total": len(news),
            "category": category,
            "sources": {
                "telegram_channels": len(telegram_news_service.channels),
                "rss_feeds": len(telegram_news_service.rss_sources)
            }
        }
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@app.get("/api/news/sources")
async def get_news_sources():
    """Получить список всех источников новостей"""
    try:
        return {
            "status": "success",
            "data": {
                "telegram_channels": telegram_news_service.channels,
                "rss_sources": telegram_news_service.rss_sources
            }
        }
    except Exception as e:
        logger.error(f"Error getting news sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sources")

@app.post("/api/news/refresh")
async def refresh_news_cache():
    """Принудительное обновление кэша новостей"""
    try:
        # Очищаем кэш
        telegram_news_service.cache.clear()
        
        # Получаем свежие новости
        fresh_news = await telegram_news_service.get_all_news(category="all", limit=50)
        
        return {
            "status": "success",
            "message": "Cache refreshed successfully",
            "articles_fetched": len(fresh_news)
        }
    except Exception as e:
        logger.error(f"Error refreshing news cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh cache")

@app.get("/api/news/channels")
async def get_channels():
    """Получить информацию о всех Telegram каналах"""
    try:
        channels = await telegram_news_service.get_channels_info()
        return {
            "status": "success",
            "data": channels,
            "total": len(channels)
        }
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch channels")

@app.get("/api/news/channel/{username}")
async def get_channel_posts(username: str, limit: int = 20):
    """Получить посты конкретного канала"""
    try:
        posts = await telegram_news_service.get_channel_posts(username, limit=limit)
        channel_info = await telegram_news_service.get_channel_info(username)
        
        if not channel_info:
            raise HTTPException(status_code=404, detail="Channel not found")
            
        return {
            "status": "success",
            "channel": channel_info,
            "posts": posts,
            "total": len(posts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch channel posts")

@app.get("/api/news/categories")
async def get_news_categories():
    """Получить список категорий новостей согласно ТЗ"""
    categories = [
        {"id": "all", "name": "Все", "icon": "📢", "description": "Все новости из всех источников"},
        {"id": "gifts", "name": "Подарки", "icon": "🎁", "description": "Бесплатные подарки, промокоды и розыгрыши"},
        {"id": "crypto", "name": "Криптовалюта", "icon": "💰", "description": "Новости крипторынка и блокчейн проектов"},
        {"id": "nft", "name": "NFT", "icon": "🖼️", "description": "NFT коллекции, аукционы и цифровое искусство"},
        {"id": "tech", "name": "Технологии", "icon": "💻", "description": "IT новости, стартапы и инновации"},
        {"id": "general", "name": "Общие", "icon": "📰", "description": "Остальные новости"}
    ]
    
    return {
        "status": "success",
        "data": categories
    }

# Dependency для получения сессии

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/user/balance")
def get_user_balance(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    return {"success": True, "balance": user.stars_balance}

@app.get("/api/user/transactions")
def get_user_transactions(user_id: str, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).limit(20).all()
    return {"success": True, "transactions": [
        {
            "id": str(tx.id),
            "type": tx.type,
            "amount": tx.amount,
            "status": tx.status if hasattr(tx, 'status') else None,
            "created_at": tx.created_at.isoformat(),
            "description": tx.description
        } for tx in txs
    ]}

@app.post("/api/user/deposit/ton")
def deposit_ton(user_id: str, amount: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    tx = Transaction(user_id=user_id, type="deposit_ton", amount=amount, status="pending")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    # Здесь должна быть логика генерации TON-адреса и ожидания платежа
    return {"success": True, "transaction_id": str(tx.id)}

@app.post("/api/user/deposit/telegram")
def deposit_telegram(user_id: str, amount: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    tx = Transaction(user_id=user_id, type="deposit_telegram", amount=amount, status="pending")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    # Здесь должна быть логика генерации Telegram Invoice через бота
    return {"success": True, "transaction_id": str(tx.id)}

@app.post("/api/user/withdraw/ton")
def withdraw_ton(user_id: str, amount: int, ton_address: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    if user.stars_balance < amount:
        return {"success": False, "error": "Insufficient balance"}
    tx = Transaction(user_id=user_id, type="withdraw_ton", amount=-amount, status="pending", description=f"Withdraw to {ton_address}")
    db.add(tx)
    user.stars_balance -= amount
    db.commit()
    db.refresh(tx)
    # Здесь должна быть логика отправки TON через TonAPI
    return {"success": True, "transaction_id": str(tx.id)}

@app.post("/api/webhook/ton")
def ton_webhook(user_id: str, amount: int, tx_hash: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.ton_transaction_hash == tx_hash, Transaction.status == "pending").first()
    if not tx:
        return {"success": False, "error": "Transaction not found"}
    tx.status = "success"
    user = db.query(User).filter(User.id == user_id).first()
    user.stars_balance += amount
    db.commit()
    return {"success": True}

@app.post("/api/webhook/telegram_payment")
def telegram_payment_webhook(user_id: str, amount: int, payment_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.telegram_payment_id == payment_id, Transaction.status == "pending").first()
    if not tx:
        return {"success": False, "error": "Transaction not found"}
    tx.status = "success"
    user = db.query(User).filter(User.id == user_id).first()
    user.stars_balance += amount
    db.commit()
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
