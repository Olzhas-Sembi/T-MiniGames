import pytest
from server.games.rps_game import RPSGame
from server.models import Player

@pytest.fixture
def players():
    return [
        Player(id="1", telegram_id="tg1", username="Alice", balance=1000),
        Player(id="2", telegram_id="tg2", username="Bob", balance=1000),
        Player(id="3", telegram_id="tg3", username="Carol", balance=1000),
        Player(id="4", telegram_id="tg4", username="Dave", balance=1000),
    ]

def test_rps_two_players_win(players):
    game = RPSGame("room1", players[:2], bet_amount=100)
    game.player_choice("1", "rock")
    game.player_choice("2", "scissors")
    result = game.finish_game(["1", "2"])
    assert result["result"] == "win"
    assert result["winners"] == ["1"]

def test_rps_two_players_tie(players):
    game = RPSGame("room2", players[:2], bet_amount=100)
    game.player_choice("1", "rock")
    game.player_choice("2", "rock")
    result = game.finish_game(["1", "2"])
    assert result["result"] == "tie"

def test_rps_three_players_complex_tie(players):
    game = RPSGame("room3", players[:3], bet_amount=100)
    game.player_choice("1", "rock")
    game.player_choice("2", "scissors")
    game.player_choice("3", "paper")
    result = game.finish_game(["1", "2", "3"])
    assert result["result"] == "complex_tie"

def test_rps_four_players_win(players):
    game = RPSGame("room4", players[:4], bet_amount=100)
    game.player_choice("1", "rock")
    game.player_choice("2", "scissors")
    game.player_choice("3", "scissors")
    game.player_choice("4", "scissors")
    result = game.finish_game(["1", "2", "3", "4"])
    assert result["result"] == "win"
    assert result["winners"] == ["1"]

def test_rps_timeout(players):
    game = RPSGame("room5", players[:3], bet_amount=100)
    game.player_choice("1", "rock")
    # Игрок 2 не делает выбор (timeout)
    game.player_choice("3", "scissors")
    result = game.finish_game(["1", "2", "3"])
    # Побеждает "rock"
    assert result["result"] == "win"
    assert result["winners"] == ["1"] 