"""
Интегрированная игра Rock-Paper-Scissors с базой данных
"""
import hashlib
import time
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..database_sqlite import get_db, User, GameRoom, GameParticipation, Transaction

class DatabaseRPSGame:
    """
    Игра Rock-Paper-Scissors с полной интеграцией базы данных
    """
    
    def __init__(self, room_id: str, db: Session):
        self.room_id = room_id
        self.db = db
        self.room = db.query(GameRoom).filter(GameRoom.id == room_id).first()
        if not self.room:
            raise ValueError(f"Room {room_id} not found")
        
        self.choices = ["rock", "paper", "scissors"]
        self.winning_rules = {
            "rock": "scissors",
            "paper": "rock", 
            "scissors": "paper"
        }
    
    def play_round(self, player_choices: Dict[str, str]) -> dict:
        """
        Сыграть раунд RPS
        Args:
            player_choices: {telegram_id: choice}
        """
        if self.room.status != "in_progress":
            raise ValueError("Game is not in progress")
        
        # Получить всех участников
        participants = self.db.query(GameParticipation).filter(
            GameParticipation.room_id == self.room_id,
            GameParticipation.bet_paid == True
        ).all()
        
        if not participants:
            raise ValueError("No participants found")
        
        # Проверить что все сделали выбор
        participant_telegram_ids = set()
        for p in participants:
            user = self.db.query(User).filter(User.id == p.user_id).first()
            participant_telegram_ids.add(user.telegram_id)
        
        if not all(tid in player_choices for tid in participant_telegram_ids):
            missing = participant_telegram_ids - set(player_choices.keys())
            raise ValueError(f"Missing choices from players: {missing}")
        
        # Обработать результаты
        results = {}
        for participation in participants:
            user = self.db.query(User).filter(User.id == participation.user_id).first()
            choice = player_choices[user.telegram_id]
            
            if choice not in self.choices:
                raise ValueError(f"Invalid choice: {choice}")
            
            results[str(participation.user_id)] = {
                "user_id": str(participation.user_id),
                "username": user.username,
                "telegram_id": user.telegram_id,
                "choice": choice
            }
        
        # Определить победителей
        winners = self._determine_winners(results)
        
        # Завершить игру
        if winners:
            if len(winners) == 1:
                winner_user_id = winners[0]
                winner_user = self.db.query(User).filter(User.id == winner_user_id).first()
                self._finish_game([winner_user.telegram_id], results)
            else:
                # Ничья между несколькими игроками
                winner_telegram_ids = []
                for winner_id in winners:
                    winner_user = self.db.query(User).filter(User.id == winner_id).first()
                    winner_telegram_ids.append(winner_user.telegram_id)
                self._finish_game(winner_telegram_ids, results)
        else:
            # Полная ничья - все играют заново или возврат ставок
            self._finish_game_full_draw(results)
        
        return {
            "results": list(results.values()),
            "winners": winners,
            "prize_per_winner": self.room.prize_pool // len(winners) if winners else 0
        }
    
    def _determine_winners(self, results: Dict) -> List[str]:
        """Определить победителей в RPS"""
        choices_made = set(result["choice"] for result in results.values())
        
        # Если все выборы одинаковые - ничья
        if len(choices_made) == 1:
            return []
        
        # Если все три выбора - ничья
        if len(choices_made) == 3:
            return []
        
        # Два разных выбора - определить победителя
        if len(choices_made) == 2:
            choices_list = list(choices_made)
            choice1, choice2 = choices_list[0], choices_list[1]
            
            # Определить какой выбор побеждает
            if self.winning_rules[choice1] == choice2:
                winning_choice = choice1
            else:
                winning_choice = choice2
            
            # Найти всех игроков с выигрышным выбором
            winners = [
                user_id for user_id, result in results.items()
                if result["choice"] == winning_choice
            ]
            return winners
        
        return []
    
    def _finish_game(self, winner_telegram_ids: List[str], results: dict):
        """Завершить игру с победителями"""
        prize_per_winner = self.room.prize_pool // len(winner_telegram_ids) if winner_telegram_ids else 0
        
        winner_user_ids = set()
        for telegram_id in winner_telegram_ids:
            user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
            winner_user_ids.add(str(user.id))
        
        for user_id, result in results.items():
            participation = self.db.query(GameParticipation).filter(
                GameParticipation.room_id == self.room_id,
                GameParticipation.user_id == user_id
            ).first()
            
            user = self.db.query(User).filter(User.id == user_id).first()
            user.total_games += 1
            
            participation.game_result = result
            
            if user_id in winner_user_ids:
                participation.status = "won" if len(winner_user_ids) == 1 else "draw_won"
                participation.prize_won = prize_per_winner
                user.wins += 1
                user.stars_balance += prize_per_winner
                
                # Транзакция выигрыша
                transaction = Transaction(
                    user_id=user.id,
                    type="game_win",
                    amount=prize_per_winner,
                    game_room_id=self.room_id,
                    description=f"Won RPS game with {result['choice']}"
                )
                self.db.add(transaction)
            else:
                participation.status = "lost"
                participation.prize_won = 0
        
        # Обновить комнату
        self.room.status = "finished"
        self.room.finished_at = datetime.utcnow()
        self.room.game_state = {"final_results": results}
        self.room.winner_ids = list(winner_user_ids)
        
        self.db.commit()
    
    def _finish_game_full_draw(self, results: dict):
        """Завершить игру с полной ничьей - возврат ставок"""
        for user_id, result in results.items():
            participation = self.db.query(GameParticipation).filter(
                GameParticipation.room_id == self.room_id,
                GameParticipation.user_id == user_id
            ).first()
            
            user = self.db.query(User).filter(User.id == user_id).first()
            user.total_games += 1
            
            participation.game_result = result
            participation.status = "draw"
            participation.prize_won = self.room.bet_amount  # Возврат ставки
            
            # Возврат ставки
            user.stars_balance += self.room.bet_amount
            
            # Транзакция возврата
            transaction = Transaction(
                user_id=user.id,
                type="game_refund",
                amount=self.room.bet_amount,
                game_room_id=self.room_id,
                description="RPS game full draw - bet refunded"
            )
            self.db.add(transaction)
        
        # Обновить комнату
        self.room.status = "finished"
        self.room.finished_at = datetime.utcnow()
        self.room.game_state = {"final_results": results, "full_draw": True}
        self.room.winner_ids = []
        
        self.db.commit()

# API endpoint для RPS
from fastapi import APIRouter, HTTPException, Depends

rps_router = APIRouter(prefix="/api/rps", tags=["rps"])

@rps_router.post("/play/{room_id}")
async def play_rps_game(
    room_id: str, 
    player_choices: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Сыграть в RPS
    Body: {"player1_telegram_id": "rock", "player2_telegram_id": "paper"}
    """
    try:
        game = DatabaseRPSGame(room_id, db)
        results = game.play_round(player_choices)
        return {
            "success": True,
            "game_type": "rps",
            "room_id": room_id,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rps_router.get("/room/{room_id}/status") 
async def get_rps_room_status(room_id: str, db: Session = Depends(get_db)):
    """Получить статус RPS комнаты"""
    room = db.query(GameRoom).filter(
        GameRoom.id == room_id,
        GameRoom.game_type == "rps"
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="RPS room not found")
    
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
            "status": p.status,
            "bet_paid": p.bet_paid,
            "game_result": p.game_result
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
