import asyncio
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from server.models import Room, Player, GameType, RoomStatus, PlayerStatus, DiceResult
from server.games.dice_game import DiceGame
from server.games.rps_game import RPSGame
import logging

logger = logging.getLogger(__name__)

class RoomManager:
    """
    Менеджер игровых комнат и матчмейкинга для мини-игр (Dice, RPS).
    Управляет созданием комнат, присоединением игроков, запуском игр, обработкой действий и рассылкой событий через WebSocket.
    """
    def __init__(self):
        # Словарь всех активных комнат: room_id -> Room
        self.rooms: Dict[str, Room] = {}
        # Активные WebSocket-подключения: player_id -> WebSocket
        self.player_connections: Dict[str, WebSocket] = {}
        # Соответствие игрока и комнаты: player_id -> room_id
        self.player_to_room: Dict[str, str] = {}
        # Игровые движки по комнатам: room_id -> DiceGame/RPSGame
        self.game_engines: Dict[str, object] = {}
        # Очереди матчмейкера по типу игры
        self.matchmaker_queue: Dict[GameType, List[str]] = {
            GameType.DICE: [],
            GameType.CARDS: [],
            GameType.RPS: []
        }
        
    async def create_room(self, creator_id: str, telegram_id: str, username: str, game_type: GameType, bet_amount: int) -> Room:
        """
        Создаёт новую игровую комнату (лобби) с указанным типом игры и ставкой.
        Добавляет создателя в комнату, помещает комнату в матчмейкер, запускает таймер ожидания.
        Args:
            creator_id (str): ID игрока-создателя
            telegram_id (str): Telegram ID
            username (str): Имя пользователя
            game_type (GameType): Тип игры (DICE, RPS)
            bet_amount (int): Ставка в звёздах
        Returns:
            Room: созданная комната
        """
        room_id = str(uuid.uuid4())[:8]
        
        creator = Player(
            id=creator_id,
            telegram_id=telegram_id,
            username=username,
            balance=1000,  # TODO: получать из базы данных
            is_creator=True,
            bet_amount=bet_amount
        )
        
        room = Room(
            id=room_id,
            game_type=game_type,
            players=[creator],
            bet_amount=bet_amount,
            created_at=datetime.now()
        )
        
        self.rooms[room_id] = room
        self.player_to_room[creator_id] = room_id
        
        # Добавляем комнату в матчмейкер
        self.matchmaker_queue[game_type].append(room_id)
        
        logger.info(f"Created room {room_id} for game {game_type} with bet {bet_amount}")
        
        # Запускаем таймер комнаты
        asyncio.create_task(self._room_timer(room_id))
        
        return room
    
    async def join_room(self, player_id: str, telegram_id: str, username: str, room_id: str) -> Optional[Room]:
        """
        Присоединяет игрока к существующей комнате, если есть свободные места.
        Args:
            player_id (str): ID игрока
            telegram_id (str): Telegram ID
            username (str): Имя пользователя
            room_id (str): ID комнаты
        Returns:
            Optional[Room]: объект комнаты или None, если не удалось присоединиться
        """
        if room_id not in self.rooms:
            return None
            
        room = self.rooms[room_id]
        
        if not room.can_join():
            return None
            
        # Проверяем, что игрок не уже в комнате
        if any(p.id == player_id for p in room.players):
            return room
            
        player = Player(
            id=player_id,
            telegram_id=telegram_id,
            username=username,
            balance=1000,  # TODO: получать из базы данных
            bet_amount=room.bet_amount
        )
        
        room.players.append(player)
        self.player_to_room[player_id] = room_id
        
        logger.info(f"Player {username} joined room {room_id}")
        
        # Уведомляем всех в комнате
        await self._broadcast_room_update(room_id, "player_joined", {
            "player": player.dict(),
            "players_count": len(room.players)
        })
        
        return room
    
    async def ready_player(self, player_id: str) -> Optional[Room]:
        """
        Подтверждает готовность игрока (блокирует ставку, меняет статус).
        Если достаточно готовых игроков — запускает игру.
        Args:
            player_id (str): ID игрока
        Returns:
            Optional[Room]: объект комнаты или None, если ошибка
        """
        room_id = self.player_to_room.get(player_id)
        if not room_id or room_id not in self.rooms:
            return None
            
        room = self.rooms[room_id]
        
        # Находим игрока и меняем его статус
        for player in room.players:
            if player.id == player_id:
                if player.balance >= room.bet_amount:
                    player.status = PlayerStatus.READY
                    player.balance -= room.bet_amount  # Блокируем ставку
                    room.pot += room.bet_amount
                    
                    logger.info(f"Player {player.username} is ready in room {room_id}")
                    break
                else:
                    return None  # Недостаточно средств
        
        # Проверяем, можно ли начинать игру
        if room.can_start():
            await self._start_game(room_id)
        else:
            await self._broadcast_room_update(room_id, "player_ready", {
                "player_id": player_id,
                "ready_count": len([p for p in room.players if p.status == PlayerStatus.READY])
            })
        
        return room
    
    async def _start_game(self, room_id: str):
        """
        Запускает игру в комнате: инициализирует игровой движок по типу игры, переводит комнату в статус PLAYING.
        Args:
            room_id (str): ID комнаты
        """
        room = self.rooms[room_id]
        room.status = RoomStatus.PLAYING
        room.started_at = datetime.now()
        
        # Убираем комнату из матчмейкера
        if room_id in self.matchmaker_queue[room.game_type]:
            self.matchmaker_queue[room.game_type].remove(room_id)
        
        # Инициализируем состояние игры в зависимости от типа
        if room.game_type == GameType.DICE:
            await self._init_dice_game(room_id)
        elif room.game_type == GameType.CARDS:
            await self._init_cards_game(room_id)
        elif room.game_type == GameType.RPS:
            await self._init_rps_game(room_id)
        
        logger.info(f"Game started in room {room_id}")
        
        await self._broadcast_room_update(room_id, "game_started", {
            "game_type": room.game_type,
            "players": [p.dict() for p in room.players if p.status == PlayerStatus.READY]
        })
    
    async def _init_dice_game(self, room_id: str):
        """Инициализация игры в кубики согласно ТЗ"""
        room = self.rooms[room_id]
        
        # Создаем игровой движок для кубиков
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        dice_game = DiceGame(room_id, ready_players, room.bet_amount)
        self.game_engines[room_id] = dice_game
        
        # Устанавливаем seed в комнате для совместимости
        room.game_seed = dice_game.game_seed
        
        # Обновляем статус игроков
        for player in ready_players:
            player.status = PlayerStatus.PLAYING
        
        # Отправляем игрокам начальное состояние согласно ТЗ
        await self._broadcast_room_update(room_id, "game_start", {
            "game_state": dice_game.get_game_state(),
            "players": [{"id": p.id, "name": p.username} for p in ready_players],
            "message": "Игра в кубики началась! Бросьте кубики и наберите наибольшую сумму!"
        })
    
    async def handle_dice_action(self, player_id: str, room_id: str, action: str):
        """
        Обрабатывает действие игрока в игре Dice (например, бросок кубиков).
        Args:
            player_id (str): ID игрока
            room_id (str): ID комнаты
            action (str): действие ("roll")
        """
        if room_id not in self.game_engines:
            raise ValueError(f"No dice game found for room {room_id}")
            
        dice_game = self.game_engines[room_id]
        
        if action == "roll":
            try:
                # Игрок бросает кубики
                result = dice_game.player_roll_action(player_id)
                
                if not result["success"]:
                    # Отправляем ошибку игроку
                    if player_id in self.player_connections:
                        await self._send_to_player(player_id, "error", {"message": result["error"]})
                    return
                
                # Отправляем результат броска игроку
                await self._send_to_player(player_id, "dice_roll_result", {
                    "result": result["result"],
                    "game_state": result["game_state"],
                    "all_players_rolled": result["all_players_rolled"]
                })
                
                # Если все игроки сделали ход - проверяем завершение раунда
                if result["all_players_rolled"]:
                    await self._finish_dice_round(room_id)
                    
            except Exception as e:
                logger.error(f"Error in dice action: {e}")
                if player_id in self.player_connections:
                    await self._send_to_player(player_id, "error", {"message": str(e)})
    
    async def _finish_dice_round(self, room_id: str):
        """Завершает раунд игры в кубики согласно ТЗ"""
        dice_game = self.game_engines[room_id]
        room = self.rooms[room_id]
        
        # Проверяем завершение раунда
        completion_result = dice_game.check_round_completion()
        
        if completion_result.get("tie", False):
            # Ничья - переброс согласно ТЗ
            await self._broadcast_room_update(room_id, "tie_detected", {
                "message": completion_result.get("message", "Ничья! Переброс..."),
                "countdown": 10  # 10 секунд до переброса
            })
            
            # Подготавливаем переброс
            dice_game.prepare_reroll()
            
            # Через 10 секунд автоматически начинаем новый раунд
            await asyncio.sleep(10)
            await self._broadcast_room_update(room_id, "game_start", {
                "game_state": dice_game.get_game_state(),
                "message": "Переброс! Бросайте кубики снова!"
            })
            
        else:
            # Есть победители
            winners = completion_result["winners"]
            prize_per_winner = completion_result["prize_per_winner"]
            
            # Обновляем балансы игроков (выплачиваем выигрыш)
            for player in room.players:
                if player.id in winners:
                    player.balance += prize_per_winner
                    logger.info(f"Player {player.id} won {prize_per_winner} stars")
            
            # Отправляем результаты всем игрокам
            await self._broadcast_room_update(room_id, "game_results", {
                "winners": winners,
                "prize_per_winner": prize_per_winner,
                "total_prize": completion_result["total_prize"],
                "results": completion_result["results"],
                "game_state": dice_game.get_game_state(),
                "seed": completion_result["seed"],      # Публикуем seed для проверки честности
                "nonce": completion_result["nonce"]     # Публикуем nonce для проверки честности
            })
            
            # Помечаем комнату как завершенную
            room.status = RoomStatus.FINISHED
            room.finished_at = datetime.now()
            
            # Через 10 секунд удаляем комнату
            await asyncio.sleep(10)
            await self._cleanup_room(room_id)
    
    def _get_player_name(self, player_id: str) -> str:
        """Получает имя игрока по ID"""
        for room in self.rooms.values():
            for player in room.players:
                if player.id == player_id:
                    return player.username
        return "Unknown"
    
    async def _init_cards_game(self, room_id: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def handle_card_action(self, player_id: str, action: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def _start_card_turn(self, room_id: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def _card_turn_timer(self, room_id: str, player_id: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def _next_card_player(self, room_id: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def _finish_cards_game(self, room_id: str):
        """
        # Удалено: логика игры 'Карты 21' больше не поддерживается в этом проекте.
        """
        pass

    async def _init_rps_game(self, room_id: str):
        """
        Инициализация игры камень-ножницы-бумага через отдельный движок RPSGame
        """
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        rps_game = RPSGame(room_id, ready_players, room.bet_amount)
        self.game_engines[room_id] = rps_game
        for player in ready_players:
            player.status = PlayerStatus.PLAYING
        await self._broadcast_room_update(room_id, "rps_started", {
            "message": "Выберите: камень, ножницы или бумага",
            "timer": 15
        })
        asyncio.create_task(self._rps_choice_timer(room_id))

    async def _rps_choice_timer(self, room_id: str):
        """
        Таймер выбора в RPS (15 секунд)
        """
        await asyncio.sleep(15)
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.status == RoomStatus.PLAYING:
                await self._finish_rps_game(room_id)

    async def handle_rps_choice(self, player_id: str, choice: str):
        """
        Обрабатывает выбор игрока в RPS через движок RPSGame
        Args:
            player_id (str): ID игрока
            choice (str): выбор ("rock", "paper", "scissors")
        """
        room_id = self.player_to_room.get(player_id)
        if not room_id or room_id not in self.rooms:
            return
        room = self.rooms[room_id]
        if room.status != RoomStatus.PLAYING:
            return
        if room_id not in self.game_engines or not isinstance(self.game_engines[room_id], RPSGame):
            return
        rps_game: RPSGame = self.game_engines[room_id]
        rps_game.player_choice(player_id, choice)
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        if rps_game.all_players_chosen():
            await self._finish_rps_game(room_id)
        else:
            await self._broadcast_room_update(room_id, "rps_choice_made", {
                "choices_count": rps_game.choices_count(),
                "total_players": len(ready_players)
            })

    async def _finish_rps_game(self, room_id: str):
        """
        Завершение игры RPS через движок RPSGame
        """
        if room_id not in self.game_engines or not isinstance(self.game_engines[room_id], RPSGame):
            return
        rps_game: RPSGame = self.game_engines[room_id]
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        result = rps_game.finish_game([p.id for p in ready_players])
        if result["result"] == "tie":
            for player in ready_players:
                player.balance += room.bet_amount
            await self._broadcast_room_update(room_id, "game_finished", {
                "result": "tie",
                "choices": result["choices"],
                "message": "Ничья! Ставки возвращены"
            })
        elif result["result"] == "complex_tie":
            for player in ready_players:
                player.balance += room.bet_amount
            await self._broadcast_room_update(room_id, "game_finished", {
                "result": "complex_tie",
                "choices": result["choices"],
                "message": "Сложная ничья! Ставки возвращены"
            })
        else:
            winner_prize = room.pot // len(result["winners"])
            room.winner_ids = result["winners"]
            for winner_id in result["winners"]:
                for player in ready_players:
                    if player.id == winner_id:
                        player.balance += winner_prize
            await self._broadcast_room_update(room_id, "game_finished", {
                "result": "win",
                "choices": result["choices"],
                "winners": room.winner_ids,
                "prize_per_winner": winner_prize
            })
        room.status = RoomStatus.FINISHED
        room.finished_at = datetime.now()
    
    async def _room_timer(self, room_id: str):
        """
        Таймер ожидания заполнения комнаты (лобби). Если не набралось игроков — отменяет комнату.
        Args:
            room_id (str): ID комнаты
        """
        await asyncio.sleep(60)  # 60 секунд ожидания
        
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        if room.status != RoomStatus.WAITING:
            return
        
        # Проверяем, достаточно ли игроков для начала
        if room.can_start():
            await self._start_game(room_id)
        else:
            # Отменяем комнату, возвращаем ставки
            await self._cancel_room(room_id)
    
    async def _cancel_room(self, room_id: str):
        """Отменяет комнату и возвращает ставки"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        room.status = RoomStatus.CANCELLED
        
        # Возвращаем заблокированные ставки
        for player in room.players:
            if player.status == PlayerStatus.READY:
                player.balance += room.bet_amount
        
        await self._broadcast_room_update(room_id, "room_cancelled", {
            "message": "Комната отменена из-за недостатка игроков. Ставки возвращены."
        })
        
        # Убираем комнату из матчмейкера
        if room_id in self.matchmaker_queue[room.game_type]:
            self.matchmaker_queue[room.game_type].remove(room_id)
        
        # Удаляем комнату через некоторое время
        asyncio.create_task(self._cleanup_room(room_id, delay=10))
    
    async def _cleanup_room(self, room_id: str, delay: int = 0):
        """Очищает комнату после завершения"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        if room_id in self.rooms:
            room = self.rooms[room_id]
            
            # Удаляем игроков из отслеживания
            for player in room.players:
                if player.id in self.player_to_room:
                    del self.player_to_room[player.id]
            
            del self.rooms[room_id]
            logger.info(f"Room {room_id} cleaned up")
    
    async def connect_player(self, player_id: str, websocket: WebSocket):
        """
        Регистрирует WebSocket-подключение игрока.
        Args:
            player_id (str): ID игрока
            websocket (WebSocket): WebSocket-соединение
        """
        self.player_connections[player_id] = websocket
    
    async def disconnect_player(self, player_id: str):
        """
        Отключает игрока, обновляет статус и рассылку.
        Args:
            player_id (str): ID игрока
        """
        if player_id in self.player_connections:
            del self.player_connections[player_id]
        
        # Обновляем статус игрока в комнате
        room_id = self.player_to_room.get(player_id)
        if room_id and room_id in self.rooms:
            room = self.rooms[room_id]
            for player in room.players:
                if player.id == player_id:
                    player.status = PlayerStatus.DISCONNECTED
                    break
            
            await self._broadcast_room_update(room_id, "player_disconnected", {
                "player_id": player_id
            })
    
    async def _broadcast_room_update(self, room_id: str, update_type: str, data: Dict):
        """
        Рассылает обновление состояния комнаты всем игрокам через WebSocket.
        Args:
            room_id (str): ID комнаты
            update_type (str): тип события ("game_started", "game_results" и т.д.)
            data (Dict): полезные данные события
        """
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        message = {
            "type": update_type,
            "room_id": room_id,
            "data": data,
            "room": room.dict()
        }
        
        for player in room.players:
            if player.id in self.player_connections:
                try:
                    await self.player_connections[player.id].send_text(json.dumps(message))
                except:
                    # Соединение разорвано
                    await self.disconnect_player(player.id)
    
    async def _send_private_message(self, player_id: str, message: Dict):
        """Отправляет приватное сообщение игроку"""
        if player_id in self.player_connections:
            try:
                await self.player_connections[player_id].send_text(json.dumps(message))
            except:
                await self.disconnect_player(player_id)
    
    async def _send_to_player(self, player_id: str, message_type: str, data: Dict):
        """Отправляет сообщение конкретному игроку"""
        message = {
            "type": message_type,
            "data": data
        }
        await self._send_private_message(player_id, message)
    
    def get_available_rooms(self, game_type: GameType, max_bet: int = None) -> List[Room]:
        """Возвращает доступные комнаты для матчмейкинга"""
        available = []
        
        for room_id in self.matchmaker_queue.get(game_type, []):
            if room_id in self.rooms:
                room = self.rooms[room_id]
                if room.can_join() and (max_bet is None or room.bet_amount <= max_bet):
                    available.append(room)
        
        return available
