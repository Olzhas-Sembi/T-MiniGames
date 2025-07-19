from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import logging
from typing import Dict, List
from models import (
    CreateRoomRequest, RoomJoinRequest, PlayerActionRequest, 
    GameType, Room, Player, RoomUpdate
)
from room_manager import RoomManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Mini Games API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный менеджер комнат
room_manager = RoomManager()

@app.get("/")
async def root():
    return {"message": "Telegram Mini Games API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "rooms_count": len(room_manager.rooms)}

# REST API endpoints

@app.post("/api/rooms/create")
async def create_room(request: CreateRoomRequest):
    """Создает новую комнату-лобби"""
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
    """Присоединение к комнате"""
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
    """Получить доступные комнаты для матчмейкинга"""
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
            
            elif action_type == "card_action":
                # Действие в игре карты 21
                card_action = message.get("card_action")  # "hit" или "stop"
                await room_manager.handle_card_action(player_id, card_action)
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
