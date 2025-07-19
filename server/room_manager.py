import asyncio
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from server.models import Room, Player, GameType, RoomStatus, PlayerStatus, DiceResult, CardGameState
from server.games.dice_game import DiceGame
import logging

logger = logging.getLogger(__name__)

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player_connections: Dict[str, WebSocket] = {}
        self.player_to_room: Dict[str, str] = {}
        self.game_engines: Dict[str, DiceGame] = {}  # room_id -> game_engine
        self.matchmaker_queue: Dict[GameType, List[str]] = {
            GameType.DICE: [],
            GameType.CARDS: [],
            GameType.RPS: []
        }
        
    async def create_room(self, creator_id: str, telegram_id: str, username: str, 
                         game_type: GameType, bet_amount: int) -> Room:
        """Создает новую комнату-лобби"""
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
    
    async def join_room(self, player_id: str, telegram_id: str, username: str, 
                       room_id: str) -> Optional[Room]:
        """Присоединение игрока к комнате"""
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
        """Игрок подтверждает готовность (оплачивает ставку)"""
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
        """Запускает игру в комнате"""
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
        """Обрабатывает действия игрока в игре кубики согласно ТЗ"""
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
        """Инициализация игры в карты 21"""
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        
        # Создаем колоду
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        
        for suit in suits:
            for rank in ranks:
                value = 11 if rank == 'A' else (10 if rank in ['J', 'Q', 'K'] else int(rank))
                deck.append({
                    'suit': suit,
                    'rank': rank,
                    'value': value
                })
        
        # Перемешиваем колоду с использованием seed
        seed_hash = hashlib.sha256(room.game_seed.encode()).hexdigest()
        deck_indices = list(range(len(deck)))
        
        # Простой алгоритм перемешивания на основе seed
        for i in range(len(deck_indices)):
            swap_seed = hashlib.sha256(f"{seed_hash}_{i}".encode()).hexdigest()
            j = int(swap_seed[:8], 16) % len(deck_indices)
            deck_indices[i], deck_indices[j] = deck_indices[j], deck_indices[i]
        
        shuffled_deck = [deck[i] for i in deck_indices]
        
        # Раздаем по 2 карты каждому игроку
        player_hands = {}
        card_index = 0
        
        for player in ready_players:
            player_hands[player.id] = [
                shuffled_deck[card_index],
                shuffled_deck[card_index + 1]
            ]
            card_index += 2
        
        card_game_state = CardGameState(
            deck=shuffled_deck[card_index:],  # Оставшиеся карты
            player_hands=player_hands,
            current_player_index=0
        )
        
        room.game_state["cards"] = card_game_state.dict()
        
        await self._broadcast_room_update(room_id, "cards_dealt", {
            "your_hand": "will_be_sent_privately",  # Карты отправляются приватно каждому
            "players_count": len(ready_players)
        })
        
        # Отправляем карты каждому игроку приватно
        for player in ready_players:
            if player.id in self.player_connections:
                await self._send_private_message(player.id, {
                    "type": "your_cards",
                    "hand": player_hands[player.id],
                    "total": self._calculate_hand_value(player_hands[player.id])
                })
        
        # Начинаем первый ход
        await self._start_card_turn(room_id)
    
    def _calculate_hand_value(self, hand: List[Dict]) -> int:
        """Подсчитывает стоимость руки в карты 21"""
        total = 0
        aces = 0
        
        for card in hand:
            if card['rank'] == 'A':
                aces += 1
                total += 11
            else:
                total += card['value']
        
        # Корректируем тузы
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    async def _start_card_turn(self, room_id: str):
        """Начинает ход текущего игрока в картах"""
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        card_state = room.game_state["cards"]
        
        current_player = ready_players[card_state["current_player_index"]]
        
        await self._broadcast_room_update(room_id, "player_turn", {
            "current_player": current_player.username,
            "current_player_id": current_player.id,
            "timer": 15
        })
        
        # Запускаем таймер хода
        asyncio.create_task(self._card_turn_timer(room_id, current_player.id))
    
    async def _card_turn_timer(self, room_id: str, player_id: str):
        """Таймер хода игрока в картах"""
        await asyncio.sleep(15)
        
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.status == RoomStatus.PLAYING:
                # Автоматически "стоп" если игрок не ответил
                await self.handle_card_action(player_id, "stop")
    
    async def handle_card_action(self, player_id: str, action: str):
        """Обрабатывает действие игрока в картах (взять/стоп)"""
        room_id = self.player_to_room.get(player_id)
        if not room_id or room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        if room.status != RoomStatus.PLAYING:
            return
        
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        card_state = room.game_state["cards"]
        current_player = ready_players[card_state["current_player_index"]]
        
        if current_player.id != player_id:
            return  # Не ход этого игрока
        
        if action == "hit":
            # Берем карту
            if card_state["deck"]:
                new_card = card_state["deck"].pop(0)
                card_state["player_hands"][player_id].append(new_card)
                
                hand_value = self._calculate_hand_value(card_state["player_hands"][player_id])
                
                # Отправляем новую карту игроку
                await self._send_private_message(player_id, {
                    "type": "card_drawn",
                    "card": new_card,
                    "hand": card_state["player_hands"][player_id],
                    "total": hand_value
                })
                
                # Проверяем перебор
                if hand_value > 21:
                    await self._broadcast_room_update(room_id, "player_bust", {
                        "player": current_player.username,
                        "total": hand_value
                    })
                    # Переходим к следующему игроку
                    await self._next_card_player(room_id)
                else:
                    # Игрок может продолжать
                    await self._start_card_turn(room_id)
        
        elif action == "stop":
            # Игрок останавливается
            hand_value = self._calculate_hand_value(card_state["player_hands"][player_id])
            await self._broadcast_room_update(room_id, "player_stop", {
                "player": current_player.username,
                "total": hand_value
            })
            await self._next_card_player(room_id)
    
    async def _next_card_player(self, room_id: str):
        """Переход к следующему игроку в картах или завершение игры"""
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        card_state = room.game_state["cards"]
        
        card_state["current_player_index"] += 1
        
        if card_state["current_player_index"] >= len(ready_players):
            # Все игроки сделали ходы, определяем победителя
            await self._finish_cards_game(room_id)
        else:
            # Переход к следующему игроку
            await self._start_card_turn(room_id)
    
    async def _finish_cards_game(self, room_id: str):
        """Завершение игры в карты и определение победителя"""
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        card_state = room.game_state["cards"]
        
        # Подсчитываем результаты всех игроков
        results = []
        for player in ready_players:
            hand_value = self._calculate_hand_value(card_state["player_hands"][player.id])
            if hand_value <= 21:  # Только не перебравшие
                results.append({
                    "player_id": player.id,
                    "player_name": player.username,
                    "total": hand_value,
                    "hand": card_state["player_hands"][player.id]
                })
        
        if not results:
            # Все перебрали - никто не выиграл, возвращаем ставки
            for player in ready_players:
                player.balance += room.bet_amount
            
            await self._broadcast_room_update(room_id, "game_finished", {
                "result": "all_bust",
                "message": "Все игроки перебрали, ставки возвращены"
            })
        else:
            # Находим победителей (ближайшие к 21)
            max_total = max(r["total"] for r in results)
            winners = [r for r in results if r["total"] == max_total]
            
            # Распределяем выигрыш
            winner_prize = room.pot // len(winners)
            room.winner_ids = [w["player_id"] for w in winners]
            
            for winner in winners:
                for player in ready_players:
                    if player.id == winner["player_id"]:
                        player.balance += winner_prize
            
            await self._broadcast_room_update(room_id, "game_finished", {
                "results": results,
                "winners": room.winner_ids,
                "prize_per_winner": winner_prize,
                "seed": room.game_seed
            })
        
        room.status = RoomStatus.FINISHED
        room.finished_at = datetime.now()
    
    async def _init_rps_game(self, room_id: str):
        """Инициализация игры камень-ножницы-бумага"""
        room = self.rooms[room_id]
        room.game_state["rps"] = {
            "choices": {},
            "timer": 10
        }
        
        await self._broadcast_room_update(room_id, "rps_started", {
            "message": "Выберите: камень, ножницы или бумага",
            "timer": 10
        })
        
        # Запускаем таймер выбора
        asyncio.create_task(self._rps_choice_timer(room_id))
    
    async def _rps_choice_timer(self, room_id: str):
        """Таймер выбора в RPS"""
        await asyncio.sleep(10)
        
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.status == RoomStatus.PLAYING:
                await self._finish_rps_game(room_id)
    
    async def handle_rps_choice(self, player_id: str, choice: str):
        """Обрабатывает выбор игрока в RPS"""
        room_id = self.player_to_room.get(player_id)
        if not room_id or room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        if room.status != RoomStatus.PLAYING:
            return
        
        if choice not in ["rock", "paper", "scissors"]:
            return
        
        room.game_state["rps"]["choices"][player_id] = choice
        
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        
        # Проверяем, все ли сделали выбор
        if len(room.game_state["rps"]["choices"]) >= len(ready_players):
            await self._finish_rps_game(room_id)
        else:
            await self._broadcast_room_update(room_id, "rps_choice_made", {
                "choices_count": len(room.game_state["rps"]["choices"]),
                "total_players": len(ready_players)
            })
    
    async def _finish_rps_game(self, room_id: str):
        """Завершение игры RPS и определение победителя"""
        room = self.rooms[room_id]
        ready_players = [p for p in room.players if p.status == PlayerStatus.READY]
        choices = room.game_state["rps"]["choices"]
        
        # Если не все сделали выбор, они автоматически проигрывают
        for player in ready_players:
            if player.id not in choices:
                choices[player.id] = "timeout"
        
        # Логика определения победителя в RPS
        valid_choices = {pid: choice for pid, choice in choices.items() if choice != "timeout"}
        
        if len(set(valid_choices.values())) == 1:
            # Все выбрали одинаково - ничья
            for player in ready_players:
                player.balance += room.bet_amount  # Возвращаем ставки
            
            await self._broadcast_room_update(room_id, "game_finished", {
                "result": "tie",
                "choices": choices,
                "message": "Ничья! Ставки возвращены"
            })
        else:
            # Определяем победителей по правилам RPS
            winners = self._determine_rps_winners(valid_choices)
            
            if not winners:
                # Сложная ничья, возвращаем ставки
                for player in ready_players:
                    player.balance += room.bet_amount
                
                await self._broadcast_room_update(room_id, "game_finished", {
                    "result": "complex_tie",
                    "choices": choices,
                    "message": "Сложная ничья! Ставки возвращены"
                })
            else:
                # Есть победители
                winner_prize = room.pot // len(winners)
                room.winner_ids = winners
                
                for winner_id in winners:
                    for player in ready_players:
                        if player.id == winner_id:
                            player.balance += winner_prize
                
                await self._broadcast_room_update(room_id, "game_finished", {
                    "result": "win",
                    "choices": choices,
                    "winners": room.winner_ids,
                    "prize_per_winner": winner_prize
                })
        
        room.status = RoomStatus.FINISHED
        room.finished_at = datetime.now()
    
    def _determine_rps_winners(self, choices: Dict[str, str]) -> List[str]:
        """Определяет победителей в RPS"""
        if not choices:
            return []
        
        choice_counts = {}
        for choice in choices.values():
            choice_counts[choice] = choice_counts.get(choice, 0) + 1
        
        unique_choices = list(choice_counts.keys())
        
        if len(unique_choices) == 3:
            # Все три варианта - ничья
            return []
        elif len(unique_choices) == 2:
            # Два варианта - есть победитель
            c1, c2 = unique_choices
            winning_choice = self._rps_winner(c1, c2)
            return [pid for pid, choice in choices.items() if choice == winning_choice]
        else:
            # Один вариант - ничья (обработано выше)
            return []
    
    def _rps_winner(self, choice1: str, choice2: str) -> str:
        """Определяет победителя между двумя выборами RPS"""
        rules = {
            ("rock", "scissors"): "rock",
            ("scissors", "paper"): "scissors", 
            ("paper", "rock"): "paper"
        }
        
        return rules.get((choice1, choice2), rules.get((choice2, choice1), choice1))
    
    async def _room_timer(self, room_id: str):
        """Таймер ожидания в комнате"""
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
        """Подключает игрока через WebSocket"""
        self.player_connections[player_id] = websocket
    
    async def disconnect_player(self, player_id: str):
        """Отключает игрока"""
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
        """Отправляет обновление всем игрокам в комнате"""
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
