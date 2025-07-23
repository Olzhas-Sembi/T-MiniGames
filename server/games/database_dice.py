"""
Интегрированная игра в кости с базой данных
"""
import hashlib
import uuid
import time
import random
from typing import Dict, List, Optional
from datetime import datetime
import requests
from sqlalchemy.orm import Session

from ..database_sqlite import get_db, User, GameRoom, GameParticipation, Transaction

class DatabaseDiceGame:
    """
    Игра в кости с полной интеграцией базы данных
    """
    
    def __init__(self, room_id: str, db: Session):
        self.room_id = room_id
        self.db = db
        self.room = db.query(GameRoom).filter(GameRoom.id == room_id).first()
        if not self.room:
            raise ValueError(f"Room {room_id} not found")
    
    def play_round(self) -> dict:
        """Сыграть раунд игры в кости"""
        if self.room.status != "in_progress":
            raise ValueError("Game is not in progress")
        
        # Получить всех участников
        participants = self.db.query(GameParticipation).filter(
            GameParticipation.room_id == self.room_id
        ).all()
        
        if not participants:
            raise ValueError("No participants found")
        
        # Генерировать честные результаты
        seed = self._generate_seed()
        results = {}
        
        for i, participation in enumerate(participants):
            user = self.db.query(User).filter(User.id == participation.user_id).first()
            
            # Генерировать кубики на основе seed + user_id
            dice1, dice2 = self._generate_fair_dice(seed, str(participation.user_id), i)
            total = dice1 + dice2
            
            results[str(participation.user_id)] = {
                "user_id": str(participation.user_id),
                "username": user.username,
                "telegram_id": user.telegram_id,
                "dice1": dice1,
                "dice2": dice2,
                "total": total
            }
        
        # Определить победителя
        max_score = max(result["total"] for result in results.values())
        winners = [
            user_id for user_id, result in results.items() 
            if result["total"] == max_score
        ]
        
        # Завершить игру через API
        if len(winners) == 1:
            winner_user_id = winners[0]
            winner_user = self.db.query(User).filter(User.id == winner_user_id).first()
            self._finish_game(winner_user.telegram_id, results)
        else:
            # Ничья - разделить призовой фонд
            self._finish_game_draw(winners, results)
        
        return {
            "results": list(results.values()),
            "winners": winners,
            "seed": seed,
            "prize_per_winner": self.room.prize_pool // len(winners) if winners else 0
        }
    
    def _generate_seed(self) -> str:
        """Генерировать честный seed"""
        timestamp = str(int(time.time() * 1000))
        room_data = f"{self.room_id}{timestamp}"
        return hashlib.sha256(room_data.encode()).hexdigest()
    
    def _generate_fair_dice(self, seed: str, user_id: str, nonce: int) -> tuple:
        """Генерировать честные кубики"""
        # Создать уникальный hash для каждого игрока
        combined = f"{seed}{user_id}{nonce}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        
        # Использовать первые байты для генерации чисел 1-6
        dice1 = (hash_bytes[0] % 6) + 1
        dice2 = (hash_bytes[1] % 6) + 1
        
        return dice1, dice2
    
    def _finish_game(self, winner_telegram_id: str, results: dict):
        """Завершить игру с одним победителем"""
        # Обновить участников
        for user_id, result in results.items():
            participation = self.db.query(GameParticipation).filter(
                GameParticipation.room_id == self.room_id,
                GameParticipation.user_id == user_id
            ).first()
            
            user = self.db.query(User).filter(User.id == user_id).first()
            user.total_games += 1
            
            participation.game_result = result
            
            # Если победитель
            winner_user = self.db.query(User).filter(
                User.telegram_id == winner_telegram_id
            ).first()
            
            if user.id == winner_user.id:
                participation.prize_won = self.room.prize_pool
                user.wins += 1
                user.stars_balance += self.room.prize_pool
                
                # Транзакция выигрыша
                transaction = Transaction(
                    user_id=user.id,
                    type="game_win",
                    amount=self.room.prize_pool,
                    room_id=self.room_id,
                    description=f"Won dice game - rolled {result['total']}"
                )
                self.db.add(transaction)
            else:
                participation.status = "lost"
                participation.prize_won = 0
        
        # Обновить комнату
        self.room.status = "finished"
        self.room.finished_at = datetime.utcnow()
        self.room.game_state = {"final_results": results}
        self.room.winner_ids = [str(winner_user.id)]
        
        self.db.commit()
    
    def _finish_game_draw(self, winner_ids: List[str], results: dict):
        """Завершить игру с ничьей"""
        prize_per_winner = self.room.prize_pool // len(winner_ids)
        
        for user_id, result in results.items():
            participation = self.db.query(GameParticipation).filter(
                GameParticipation.room_id == self.room_id,
                GameParticipation.user_id == user_id
            ).first()
            
            user = self.db.query(User).filter(User.id == user_id).first()
            user.total_games += 1
            
            participation.game_result = result
            
            if user_id in winner_ids:
                participation.status = "draw_won"
                participation.prize_won = prize_per_winner
                user.wins += 1
                user.stars_balance += prize_per_winner
                
                # Транзакция выигрыша
                transaction = Transaction(
                    user_id=user.id,
                    type="game_win",
                    amount=prize_per_winner,
                    room_id=self.room_id,
                    description=f"Draw in dice game - rolled {result['total']}"
                )
                self.db.add(transaction)
            else:
                participation.status = "lost"
                participation.prize_won = 0
        
        # Обновить комнату
        self.room.status = "finished"
        self.room.finished_at = datetime.utcnow()
        self.room.game_state = {"final_results": results, "draw": True}
        self.room.winner_ids = winner_ids
        
        self.db.commit()

# API endpoint для игры в кости
from fastapi import APIRouter, HTTPException, Depends

dice_router = APIRouter(prefix="/api/dice", tags=["dice"])

@dice_router.post("/play/{room_id}")
async def play_dice_game(room_id: str, db: Session = Depends(get_db)):
    """Сыграть в кости"""
    try:
        game = DatabaseDiceGame(room_id, db)
        results = game.play_round()
        return {
            "success": True,
            "game_type": "dice",
            "room_id": room_id,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@dice_router.get("/room/{room_id}/status")
async def get_dice_room_status(room_id: str, db: Session = Depends(get_db)):
    """Получить статус игровой комнаты"""
    room = db.query(GameRoom).filter(
        GameRoom.id == room_id,
        GameRoom.game_type == "dice"
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Dice room not found")
    
    participants = db.query(GameParticipation).filter(
        GameParticipation.room_id == room_id
    ).all()
    
    participants_data = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        participants_data.append({
            "user_id": str(p.user_id),
            "username": user.username,
            "telegram_id": user.telegram_id,
            "player_data": p.player_data
        })
    
    return {
        "room_id": room_id,
        "status": room.status,
        "bet_amount": room.bet_amount,
        "prize_pool": room.prize_pool,
        "current_players": room.current_players,
        "max_players": room.max_players,
        "participants": participants_data,
        "game_state": room.game_state,
        "started_at": room.started_at.isoformat() if room.started_at else None,
        "finished_at": room.finished_at.isoformat() if room.finished_at else None
    }
