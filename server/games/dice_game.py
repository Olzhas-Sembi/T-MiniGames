import hashlib
import uuid
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from server.models import Player, DiceResult

class DiceGame:
    """
    Честная реализация игры в кубики (Dice) для 2-4 игроков.
    - Каждый игрок бросает два кубика, победитель — наибольшая сумма.
    - При полной ничьей — переброс с новым seed/nonce.
    - Публикация seed/nonce для проверки честности.
    - Призовой фонд делится между победителями.
    """
    
    def __init__(self, room_id: str, players: List[Player], bet_amount: int = 100):
        """
        Инициализация игры Dice.
        Args:
            room_id (str): ID комнаты
            players (List[Player]): список игроков
            bet_amount (int): ставка на игрока
        """
        self.room_id = room_id
        self.players = {p.id: p for p in players}
        self.bet_amount = bet_amount
        self.prize_pool = bet_amount * len(players)
        self.game_seed = self._generate_seed()
        self.nonce = self._generate_nonce()
        self.player_actions: Dict[str, bool] = {p.id: False for p in players}
        self.results: Dict[str, DiceResult] = {}
        self.game_started = False
        self.game_finished = False
        self.winners: List[str] = []
        self.round_number = 1
        self.created_at = datetime.now()
        
    def _generate_seed(self) -> str:
        """Генерирует криптографически стойкий seed для игры"""
        timestamp = str(int(time.time() * 1000000))  # микросекунды для уникальности
        room_hash = hashlib.sha256(self.room_id.encode()).hexdigest()[:8]
        random_component = uuid.uuid4().hex[:8]
        return f"{timestamp}-{room_hash}-{random_component}"
    
    def _generate_nonce(self) -> str:
        """Генерирует nonce для дополнительной случайности"""
        return uuid.uuid4().hex[:16]
    
    def _generate_dice_for_player(self, player_id: str, round_num: int = 1) -> Tuple[int, int]:
        """
        Генерирует детерминированные значения кубиков для игрока согласно ТЗ
        Использует единый seed для всех игроков для обеспечения честности
        """
        # Создаем уникальную строку для хеширования
        hash_input = f"{self.game_seed}-{self.nonce}-{player_id}-round{round_num}".encode('utf-8')
        
        # Получаем SHA-256 хеш
        digest = hashlib.sha256(hash_input).hexdigest()
        
        # Преобразуем первые байты в значения кубиков (1-6)
        die1 = int(digest[:2], 16) % 6 + 1
        die2 = int(digest[2:4], 16) % 6 + 1
        
        return die1, die2
    
    def player_roll_action(self, player_id: str) -> Dict:
        """
        Обрабатывает бросок кубиков игрока.
        Args:
            player_id (str): ID игрока
        Returns:
            Dict: результат броска и состояние игры
        """
        if self.game_finished or player_id not in self.players:
            return {"success": False, "error": "Invalid game state or player"}
        
        if self.player_actions.get(player_id, False):
            return {"success": False, "error": "Player already rolled"}
        
        # Генерируем кубики для игрока
        dice1, dice2 = self._generate_dice_for_player(player_id, self.round_number)
        total = dice1 + dice2
        
        # Сохраняем результат
        player = self.players[player_id]
        self.results[player_id] = DiceResult(
            player_id=player_id,
            player_name=player.username,
            dice1=dice1,
            dice2=dice2,
            total=total
        )
        
        # Отмечаем что игрок сделал ход
        self.player_actions[player_id] = True
        
        # Проверяем завершение раунда
        all_rolled = all(self.player_actions.values())
        
        return {
            "success": True,
            "result": {
                "dice1": dice1,
                "dice2": dice2,
                "total": total
            },
            "all_players_rolled": all_rolled,
            "game_state": self.get_game_state()
        }
    
    def check_round_completion(self) -> Dict:
        """
        Проверяет завершение раунда и определяет победителей.
        Returns:
            Dict: информация о завершении, победителях, призах, seed/nonce
        """
        if not all(self.player_actions.values()):
            return {"completed": False}
        
        # Находим максимальную сумму
        max_total = max(result.total for result in self.results.values())
        
        # Находим всех игроков с максимальной суммой
        winners = [
            player_id for player_id, result in self.results.items() 
            if result.total == max_total
        ]
        
        # Проверяем ничью согласно ТЗ
        if len(winners) > 1:
            # Проверяем полную ничью (все игроки имеют одинаковую сумму)
            all_totals = [result.total for result in self.results.values()]
            if len(set(all_totals)) == 1:
                # Полная ничья - переброс
                return {
                    "completed": True,
                    "tie": True,
                    "winners": [],
                    "message": "Полная ничья! Автоматический переброс..."
                }
        
        # Определяем победителей
        self.winners = winners
        self.game_finished = True
        
        # Распределяем призовой фонд
        prize_per_winner = self.prize_pool // len(winners) if winners else 0
        
        return {
            "completed": True,
            "tie": False,
            "winners": winners,
            "prize_per_winner": prize_per_winner,
            "total_prize": self.prize_pool,
            "results": {pid: result.__dict__ for pid, result in self.results.items()},
            "seed": self.game_seed,  # Публикуем seed для проверки честности
            "nonce": self.nonce      # Публикуем nonce для проверки честности
        }
    
    def prepare_reroll(self) -> None:
        """
        Подготавливает переброс при полной ничьей (новый nonce, очистка результатов).
        """
        self.round_number += 1
        self.player_actions = {pid: False for pid in self.players.keys()}
        self.results.clear()
        # Генерируем новый nonce для переброса
        self.nonce = self._generate_nonce()
    
    def get_game_state(self) -> Dict:
        """
        Возвращает текущее состояние игры (для клиента/серверных уведомлений).
        Returns:
            Dict: состояние игры
        """
        return {
            "room_id": self.room_id,
            "round_number": self.round_number,
            "player_actions": self.player_actions,
            "results": {pid: result.__dict__ for pid, result in self.results.items()},
            "winners": self.winners,
            "game_finished": self.game_finished,
            "all_players_rolled": all(self.player_actions.values()),
            "prize_pool": self.prize_pool,
            "bet_amount": self.bet_amount
        }
    
    def verify_result(self, player_id: str, expected_dice1: int, expected_dice2: int) -> bool:
        """
        Проверяет честность результата броска по публичному seed/nonce.
        Args:
            player_id (str): ID игрока
            expected_dice1 (int): ожидаемый результат кубика 1
            expected_dice2 (int): ожидаемый результат кубика 2
        Returns:
            bool: True если результат честный
        """
        actual_dice1, actual_dice2 = self._generate_dice_for_player(player_id, self.round_number)
        return actual_dice1 == expected_dice1 and actual_dice2 == expected_dice2
        """
        Обрабатывает действие игрока "бросить кубики"
        Возвращает True если все игроки сделали ход
        """
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not in game")
            
        if self.game_finished:
            raise ValueError("Game already finished")
            
        if self.player_actions[player_id]:
            raise ValueError(f"Player {player_id} already rolled")
        
        # Фиксируем действие игрока
        self.player_actions[player_id] = True
        
        # Проверяем, все ли игроки сделали ход
        all_rolled = all(self.player_actions.values())
        
        if all_rolled and not self.game_finished:
            self._process_round()
            
        return all_rolled
    
    def _process_round(self):
        """Обрабатывает раунд игры после того, как все игроки бросили кубики"""
        # Генерируем результаты для всех игроков
        round_results = {}
        
        for player_id in self.players.keys():
            die1, die2 = self._generate_dice_for_player(player_id, self.round_number)
            total = die1 + die2
            
            round_results[player_id] = DiceResult(
                player_id=player_id,
                dice1=die1,
                dice2=die2,
                total=total
            )
        
        self.results = round_results
        
        # Определяем победителей
        max_total = max(result.total for result in round_results.values())
        potential_winners = [
            player_id for player_id, result in round_results.items() 
            if result.total == max_total
        ]
        
        # Проверяем на ничью между всеми игроками
        if len(potential_winners) == len(self.players):
            # Ничья между всеми - переброс
            self._prepare_reroll()
        else:
            # Есть победители
            self.winners = potential_winners
            self.game_finished = True
    
    def _prepare_reroll(self):
        """Подготавливает переброс в случае ничьей между всеми игроками"""
        self.round_number += 1
        self.game_seed = self._generate_seed()  # Новый seed для честности
        self.player_actions = {p_id: False for p_id in self.players.keys()}
        self.results = {}
    
    def get_game_state(self) -> Dict:
        """Возвращает текущее состояние игры"""
        return {
            "room_id": self.room_id,
            "game_seed_hash": hashlib.sha256(self.game_seed.encode()).hexdigest()[:16],  # Для верификации
            "round_number": self.round_number,
            "player_actions": self.player_actions,
            "results": {pid: {
                "dice1": result.dice1,
                "dice2": result.dice2, 
                "total": result.total
            } for pid, result in self.results.items()},
            "winners": self.winners,
            "game_finished": self.game_finished,
            "all_players_rolled": all(self.player_actions.values()),
            "created_at": self.created_at.isoformat()
        }
    
    def can_player_roll(self, player_id: str) -> bool:
        """Проверяет, может ли игрок сделать ход"""
        return (
            player_id in self.players and 
            not self.player_actions[player_id] and 
            not self.game_finished
        )
    
    def get_waiting_players(self) -> List[str]:
        """Возвращает список игроков, которые ещё не сделали ход"""
        return [
            pid for pid, rolled in self.player_actions.items() 
            if not rolled
        ]
    
    def calculate_pot_distribution(self, bet_amount: int) -> Dict[str, int]:
        """Рассчитывает распределение банка между победителями"""
        if not self.game_finished or not self.winners:
            return {}
            
        total_pot = bet_amount * len(self.players)
        winnings_per_player = total_pot // len(self.winners)
        
        return {winner_id: winnings_per_player for winner_id in self.winners}

    def verify_game_integrity(self) -> bool:
        """
        Верифицирует честность игры - пересчитывает результаты 
        и сравнивает с сохранёнными
        """
        if not self.results:
            return True
            
        for player_id, saved_result in self.results.items():
            die1, die2 = self._generate_dice_for_player(player_id, self.round_number)
            if die1 != saved_result.dice1 or die2 != saved_result.dice2:
                return False
                
        return True
