"""
API endpoints для игр с интеграцией базы данных
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import json
import uuid
from datetime import datetime, timedelta

from .database_sqlite import get_db, User, GameRoom, GameParticipation, Transaction
from .config import settings

router = APIRouter(prefix="/api/games", tags=["games"])

@router.post("/create-room")
async def create_game_room(
    game_type: str,
    bet_amount: int,
    max_players: int,
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """Создать игровую комнату"""
    # Найти пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверить баланс
    if user.stars_balance < bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Создать комнату
    room_id = str(uuid.uuid4())[:8]
    room = GameRoom(
        id=room_id,
        game_type=game_type,
        status="waiting",
        min_players=1,
        max_players=max_players,
        bet_amount=bet_amount,
        creator_id=user.id,
        current_players=1,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        prize_pool=bet_amount
    )
    
    db.add(room)
    
    # Создать участие создателя
    participation = GameParticipation(
        room_id=room_id,
        user_id=user.id
    )
    
    db.add(participation)
    db.commit()
    
    return {
        "room_id": room_id,
        "game_type": game_type,
        "bet_amount": bet_amount,
        "max_players": max_players,
        "status": "waiting"
    }

@router.post("/join-room/{room_id}")
async def join_game_room(
    room_id: str,
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """Присоединиться к игровой комнате"""
    # Найти пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Найти комнату
    room = db.query(GameRoom).filter(GameRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="Room is not accepting players")
    
    if room.current_players >= room.max_players:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Проверить баланс
    if user.stars_balance < room.bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Проверить, не участвует ли уже
    existing = db.query(GameParticipation).filter(
        GameParticipation.room_id == room_id,
        GameParticipation.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already in this room")
    
    # Добавить участие
    participation = GameParticipation(
        room_id=room_id,
        user_id=user.id
    )
    
    db.add(participation)
    
    # Обновить комнату
    room.current_players += 1
    room.prize_pool += room.bet_amount
    
    db.commit()
    
    return {
        "message": "Joined room successfully",
        "room_id": room_id,
        "current_players": room.current_players,
        "max_players": room.max_players
    }

@router.post("/start-game/{room_id}")
async def start_game(
    room_id: str,
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """Начать игру (только создатель может)"""
    # Найти пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Найти комнату
    room = db.query(GameRoom).filter(GameRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Only room creator can start the game")
    
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="Game already started or finished")
    
    # Получить всех участников
    participants = db.query(GameParticipation).filter(
        GameParticipation.room_id == room_id
    ).all()
    
    # Списать ставки у всех участников
    for participation in participants:
        participant_user = db.query(User).filter(User.id == participation.user_id).first()
        if participant_user.stars_balance < room.bet_amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Player {participant_user.username} has insufficient balance"
            )
        
        # Списать ставку
        participant_user.stars_balance -= room.bet_amount
        
        # Создать транзакцию
        transaction = Transaction(
            user_id=participant_user.id,
            type="game_bet",
            amount=-room.bet_amount,
            room_id=room_id,
            description=f"Bet for {room.game_type} game"
        )
        db.add(transaction)
    
    # Обновить статус комнаты
    room.status = "in_progress"
    
    db.commit()
    
    return {
        "message": "Game started successfully",
        "room_id": room_id,
        "participants": len(participants),
        "prize_pool": room.prize_pool
    }

@router.post("/finish-game/{room_id}")
async def finish_game(
    room_id: str,
    winner_telegram_id: Optional[str],
    game_results: dict,
    db: Session = Depends(get_db)
):
    """Завершить игру и распределить призы"""
    # Найти комнату
    room = db.query(GameRoom).filter(GameRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game is not in progress")
    
    # Найти победителя (если есть)
    winner = None
    if winner_telegram_id:
        winner = db.query(User).filter(User.telegram_id == winner_telegram_id).first()
        if not winner:
            raise HTTPException(status_code=404, detail="Winner not found")
    
    # Получить всех участников
    participants = db.query(GameParticipation).filter(
        GameParticipation.room_id == room_id
    ).all()
    
    # Обновить статистику участников
    for participation in participants:
        participant_user = db.query(User).filter(User.id == participation.user_id).first()
        participant_user.total_games += 1
        
        # Сохранить результат игры
        participation.game_result = game_results.get(str(participation.user_id), {})
        
        # Если это победитель
        if winner and participation.user_id == winner.id:
            participation.status = "won"
            participation.prize_won = room.prize_pool
            participant_user.wins += 1
            participant_user.stars_balance += room.prize_pool
            
            # Создать транзакцию выигрыша
            transaction = Transaction(
                user_id=winner.id,
                type="game_win",
                amount=room.prize_pool,
                game_room_id=room_id,
                description=f"Won {room.game_type} game"
            )
            db.add(transaction)
        else:
            participation.status = "lost"
            participation.prize_won = 0
    
    # Обновить комнату
    room.status = "finished"
    room.finished_at = datetime.utcnow()
    room.game_state = game_results
    if winner:
        room.winner_ids = [str(winner.id)]
    
    db.commit()
    
    return {
        "message": "Game finished successfully",
        "room_id": room_id,
        "winner": winner.telegram_id if winner else None,
        "prize_pool": room.prize_pool
    }

@router.get("/rooms")
async def get_available_rooms(db: Session = Depends(get_db)):
    """Получить доступные игровые комнаты"""
    rooms = db.query(GameRoom).filter(
        GameRoom.status == "waiting",
        GameRoom.expires_at > datetime.utcnow()
    ).all()
    
    result = []
    for room in rooms:
        creator = db.query(User).filter(User.id == room.creator_id).first()
        result.append({
            "id": room.id,
            "game_type": room.game_type,
            "bet_amount": room.bet_amount,
            "current_players": room.current_players,
            "max_players": room.max_players,
            "creator": creator.username if creator else "Unknown",
            "created_at": room.created_at.isoformat()
        })
    
    return {"rooms": result}

@router.get("/user-stats/{telegram_id}")
async def get_user_stats(telegram_id: str, db: Session = Depends(get_db)):
    """Получить статистику пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Последние игры
    recent_games = db.query(GameParticipation).join(GameRoom).filter(
        GameParticipation.user_id == user.id
    ).order_by(GameParticipation.joined_at.desc()).limit(10).all()
    
    games_history = []
    for participation in recent_games:
        room = db.query(GameRoom).filter(GameRoom.id == participation.room_id).first()
        games_history.append({
            "game_type": room.game_type,
            "bet_amount": room.bet_amount,
            "status": participation.status,
            "prize_won": participation.prize_won or 0,
            "played_at": participation.joined_at.isoformat()
        })
    
    return {
        "user": {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "stars_balance": user.stars_balance,
            "total_games": user.total_games,
            "wins": user.wins,
            "win_rate": (user.wins / user.total_games * 100) if user.total_games > 0 else 0
        },
        "recent_games": games_history
    }
