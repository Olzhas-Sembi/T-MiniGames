from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class GameType(str, Enum):
    """
    Перечисление поддерживаемых типов игр.
    DICE — игра в кубики, RPS — камень-ножницы-бумага.
    """
    DICE = "dice"
    CARDS = "cards"
    RPS = "rps"

class RoomStatus(str, Enum):
    """
    Перечисление статусов игровой комнаты.
    WAITING — ожидание игроков, PLAYING — игра идёт, FINISHED — завершена, CANCELLED — отменена.
    """
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class PlayerStatus(str, Enum):
    """
    Перечисление статусов игрока в комнате.
    WAITING — ожидает, READY — подтвердил ставку, PLAYING — играет, DISCONNECTED — отключён.
    """
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    DISCONNECTED = "disconnected"

class Player(BaseModel):
    """
    Модель игрока в системе.
    Attributes:
        id (str): внутренний ID игрока
        telegram_id (str): Telegram ID
        username (str): имя пользователя
        balance (int): баланс звёзд
        status (PlayerStatus): статус в комнате
        bet_amount (int): ставка
        is_creator (bool): создатель комнаты
    """
    id: str
    telegram_id: str
    username: str
    balance: int
    status: PlayerStatus = PlayerStatus.WAITING
    bet_amount: int = 0
    is_creator: bool = False

class Room(BaseModel):
    """
    Модель игровой комнаты.
    Attributes:
        id (str): ID комнаты
        game_type (GameType): тип игры
        status (RoomStatus): статус комнаты
        players (List[Player]): список игроков
        max_players (int): максимум игроков
        min_players (int): минимум игроков
        bet_amount (int): ставка
        pot (int): банк
        created_at (datetime): время создания
        started_at (Optional[datetime]): время старта
        finished_at (Optional[datetime]): время завершения
        timer_seconds (int): таймер ожидания
        game_seed (Optional[str]): seed для честности
        game_state (Dict): состояние игры
        winner_ids (List[str]): победители
    """
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
    """
    Результат броска кубиков для одного игрока.
    Attributes:
        player_id (str): ID игрока
        dice1 (int): результат первого кубика
        dice2 (int): результат второго кубика
        total (int): сумма
    """
    player_id: str
    dice1: int
    dice2: int
    total: int

class RoomJoinRequest(BaseModel):
    """
    Запрос на присоединение к комнате.
    Attributes:
        player_id (str): ID игрока
        telegram_id (str): Telegram ID
        username (str): имя пользователя
        room_id (str): ID комнаты
    """
    player_id: str
    telegram_id: str
    username: str
    room_id: str

class CreateRoomRequest(BaseModel):
    """
    Запрос на создание комнаты.
    Attributes:
        player_id (str): ID игрока
        telegram_id (str): Telegram ID
        username (str): имя пользователя
        game_type (GameType): тип игры
        bet_amount (int): ставка
    """
    player_id: str
    telegram_id: str
    username: str
    game_type: GameType
    bet_amount: int

class PlayerActionRequest(BaseModel):
    """
    Запрос на действие игрока в игре.
    Attributes:
        player_id (str): ID игрока
        room_id (str): ID комнаты
        action (str): действие
        data (Optional[Dict]): дополнительные данные
    """
    player_id: str
    room_id: str
    action: str
    data: Optional[Dict[str, Any]] = None

class RoomUpdate(BaseModel):
    """
    Обновление состояния комнаты для клиента.
    Attributes:
        type (str): тип обновления
        room (Room): объект комнаты
        action_data (Optional[Dict]): данные действия
        message (Optional[str]): сообщение
    """
    type: str  # "room_update", "game_start", "game_action", "game_end"
    room: Room
    action_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
