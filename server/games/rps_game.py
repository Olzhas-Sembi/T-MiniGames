import hashlib
from typing import Dict, List
from server.models import Player

class RPSGame:
    """
    Логика игры 'Камень, ножницы, бумага' для 2-4 игроков.
    - Каждый игрок делает скрытый выбор (rock/paper/scissors)
    - После выбора всех или по таймеру — раскрытие ходов
    - Определение победителя(ей) или ничьи (в т.ч. сложной)
    - Поддержка сложной ничьей (кольцевая ситуация)
    """
    def __init__(self, room_id: str, players: List[Player], bet_amount: int = 100):
        """
        Инициализация игры RPS.
        Args:
            room_id (str): ID комнаты
            players (List[Player]): список игроков
            bet_amount (int): ставка на игрока
        """
        self.room_id = room_id
        self.players = {p.id: p for p in players}
        self.bet_amount = bet_amount
        self.choices: Dict[str, str] = {}  # player_id -> choice
        self.finished = False
        self.winners: List[str] = []

    def player_choice(self, player_id: str, choice: str) -> bool:
        """
        Регистрирует выбор игрока (rock/paper/scissors).
        Args:
            player_id (str): ID игрока
            choice (str): выбор игрока
        Returns:
            bool: True если выбор принят
        """
        if self.finished:
            return False
        if player_id not in self.players:
            return False
        if choice not in ["rock", "paper", "scissors"]:
            return False
        if player_id in self.choices:
            return False
        self.choices[player_id] = choice
        return True

    def all_players_chosen(self) -> bool:
        """
        Проверяет, сделали ли все игроки выбор.
        Returns:
            bool: True если все игроки выбрали
        """
        return len(self.choices) >= len(self.players)

    def choices_count(self) -> int:
        return len(self.choices)

    def finish_game(self, expected_player_ids: List[str]) -> Dict:
        """
        Завершает игру, определяет победителей или ничью.
        Args:
            expected_player_ids (List[str]): список ID игроков, которые должны были сделать выбор
        Returns:
            Dict: результат игры (тип исхода, выборы, победители)
        """
        # Автоматически проставляем timeout для невыбравших
        for pid in expected_player_ids:
            if pid not in self.choices:
                self.choices[pid] = "timeout"
        valid_choices = {pid: ch for pid, ch in self.choices.items() if ch != "timeout"}
        # Все выбрали одинаково — ничья
        if len(set(valid_choices.values())) == 1:
            self.finished = True
            return {"result": "tie", "choices": self.choices}
        # Кольцевая ничья (все три варианта выбраны)
        if len(set(valid_choices.values())) == 3:
            self.finished = True
            return {"result": "complex_tie", "choices": self.choices}
        # Определяем победителей
        winners = self._determine_winners(valid_choices)
        if not winners:
            self.finished = True
            return {"result": "complex_tie", "choices": self.choices}
        self.finished = True
        self.winners = winners
        return {"result": "win", "choices": self.choices, "winners": winners}

    def _determine_winners(self, choices: Dict[str, str]) -> List[str]:
        """
        Определяет победителей среди сделавших выбор.
        Args:
            choices (Dict[str, str]): выборы игроков
        Returns:
            List[str]: список ID победителей
        """
        # Если два варианта — определяем, кто выиграл
        unique = list(set(choices.values()))
        if len(unique) == 2:
            c1, c2 = unique
            win = self._rps_winner(c1, c2)
            return [pid for pid, ch in choices.items() if ch == win]
        # Если один вариант — ничья (обработано выше)
        return []

    def _rps_winner(self, c1: str, c2: str) -> str:
        """
        Определяет победителя между двумя вариантами (rock/paper/scissors).
        Args:
            c1 (str): первый выбор
            c2 (str): второй выбор
        Returns:
            str: выигравший вариант
        """
        rules = {
            ("rock", "scissors"): "rock",
            ("scissors", "paper"): "scissors",
            ("paper", "rock"): "paper"
        }
        return rules.get((c1, c2), rules.get((c2, c1), c1)) 