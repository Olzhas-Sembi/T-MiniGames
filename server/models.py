from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class GameType(str, Enum):
    DICE = "dice"
    CARDS = "cards"
    RPS = "rps"

class RoomStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class PlayerStatus(str, Enum):
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    DISCONNECTED = "disconnected"

class Player(BaseModel):
    id: str
    telegram_id: str
    username: str
    balance: int
    status: PlayerStatus = PlayerStatus.WAITING
    bet_amount: int = 0
    is_creator: bool = False

class Room(BaseModel):
    id: str
    game_type: GameType
    status: RoomStatus = RoomStatus.WAITING
    players: List[Player] = []
    max_players: int = 4
    min_players: int = 2
    bet_amount: int
    pot: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    timer_seconds: int = 60
    game_seed: Optional[str] = None
    game_state: Dict[str, Any] = {}
    winner_ids: List[str] = []
    
    def can_join(self) -> bool:
        return (
            self.status == RoomStatus.WAITING and 
            len(self.players) < self.max_players
        )
    
    def can_start(self) -> bool:
        ready_players = [p for p in self.players if p.status == PlayerStatus.READY]
        return len(ready_players) >= self.min_players
    
    def get_invite_link(self) -> str:
        return f"https://t.me/your_bot?startapp=join_{self.id}"

class GameAction(BaseModel):
    player_id: str
    room_id: str
    action_type: str
    data: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

class DiceResult(BaseModel):
    player_id: str
    dice1: int
    dice2: int
    total: int

class CardGameState(BaseModel):
    deck: List[Dict[str, Any]]
    player_hands: Dict[str, List[Dict[str, Any]]]
    current_player_index: int
    turn_timer: int = 15

class RoomJoinRequest(BaseModel):
    player_id: str
    telegram_id: str
    username: str
    room_id: str

class CreateRoomRequest(BaseModel):
    player_id: str
    telegram_id: str
    username: str
    game_type: GameType
    bet_amount: int

class PlayerActionRequest(BaseModel):
    player_id: str
    room_id: str
    action: str
    data: Optional[Dict[str, Any]] = None

class RoomUpdate(BaseModel):
    type: str  # "room_update", "game_start", "game_action", "game_end"
    room: Room
    action_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
