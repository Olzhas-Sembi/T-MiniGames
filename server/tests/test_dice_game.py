import pytest
from server.games.dice_game import DiceGame
from server.models import Player

@pytest.fixture
def players():
    return [
        Player(id="1", telegram_id="tg1", username="Alice", balance=1000),
        Player(id="2", telegram_id="tg2", username="Bob", balance=1000),
        Player(id="3", telegram_id="tg3", username="Carol", balance=1000),
        Player(id="4", telegram_id="tg4", username="Dave", balance=1000),
    ]

def test_dice_roll_and_winner(players):
    game = DiceGame("room1", players[:2], bet_amount=100)
    # Оба игрока бросают кубики
    for p in players[:2]:
        result = game.player_roll_action(p.id)
        assert result["success"]
        assert 1 <= result["result"]["dice1"] <= 6
        assert 1 <= result["result"]["dice2"] <= 6
    # Проверяем завершение раунда
    round_result = game.check_round_completion()
    assert round_result["completed"]
    assert "winners" in round_result
    assert round_result["prize_per_winner"] > 0

def test_dice_tie_and_reroll(players):
    # Принудительно делаем одинаковый seed/nonce для полной ничьей
    game = DiceGame("room2", players[:3], bet_amount=50)
    # Мокаем броски: вручную выставляем одинаковые суммы
    for p in players[:3]:
        game.player_actions[p.id] = True
        game.results[p.id] = type("Fake", (), {"total": 7})()  # все по 7
    res = game.check_round_completion()
    assert res["tie"]
    game.prepare_reroll()
    assert game.round_number == 2
    assert not game.results

def test_dice_verify_result(players):
    game = DiceGame("room3", players[:2], bet_amount=100)
    p = players[0]
    result = game.player_roll_action(p.id)
    dice1 = result["result"]["dice1"]
    dice2 = result["result"]["dice2"]
    assert game.verify_result(p.id, dice1, dice2) 