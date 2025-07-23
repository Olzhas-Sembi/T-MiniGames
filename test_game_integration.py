# #!/usr/bin/env python3
# """
# Тестирование интеграции игр с базой данных
# "    # Бросок костей
#     dice_data = {"dice_count": 2}
#     respons    # Ходы игроков
#     choice1_data = {"choice": "rock"}
#     response = requests.post(f"{BASE_URL}/api/rps/play/{room_id}?telegram_id={telegram_id1}", json=choice1_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка хода игрока 1: {response.text}")
#         return False
    
#     choice2_data = {"choice": "scissors"}
#     response = requests.post(f"{BASE_URL}/api/rps/play/{room_id}?telegram_id={telegram_id2}", json=choice2_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка хода игрока 2: {response.text}")
#         return False
    
#     result = response.json()
#     print(f"✂️ Результат RPS: {result['message']}")st(f"{BASE_URL}/api/dice/play/{room_id}?telegram_id={telegram_id1}", json=dice_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка броска костей: {response.text}")
#         return False
    
#     roll_result = response.json()
#     print(f"🎲 Результат броска игрока 1: {roll_result['results']}, Сумма: {roll_result['total']}")
    
#     # Бросок костей второго игрока
#     response = requests.post(f"{BASE_URL}/api/dice/play/{room_id}?telegram_id={telegram_id2}", json=dice_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка броска костей игрока 2: {response.text}")
#         return False
    
#     roll_result2 = response.json()
#     print(f"🎲 Результат броска игрока 2: {roll_result2['results']}, Сумма: {roll_result2['total']}")s
# import json
# import time

# # Базовый URL API
# BASE_URL = "http://localhost:8000"

# def test_user_creation():
#     """Тест создания пользователя"""
#     print("🧪 Тестирование создания пользователя...")
    
#     user_data = {
#         "telegram_id": 123456789,
#         "username": "test_player",
#         "first_name": "Test",
#         "last_name": "Player"
#     }
    
#     response = requests.post(f"{BASE_URL}/api/users", json=user_data)
#     if response.status_code == 200:
#         user = response.json()
#         print(f"✅ Пользователь создан: {user_data['username']} (ID: {user['user_id']})")
#         return {"id": user['user_id'], "username": user_data['username'], "telegram_id": user_data['telegram_id']}
#     else:
#         print(f"❌ Ошибка создания пользователя: {response.text}")
#         return None

# def test_add_stars(telegram_id):
#     """Тест добавления звезд пользователю"""
#     print(f"💰 Добавление звезд пользователю {telegram_id}...")
    
#     response = requests.post(f"{BASE_URL}/api/users/{telegram_id}/add-stars?amount=100")
#     if response.status_code == 200:
#         result = response.json()
#         print(f"✅ Добавлено 100 звезд. Новый баланс: {result['new_balance']}")
#         return True
#     else:
#         print(f"❌ Ошибка добавления звезд: {response.text}")
#         return False

# def test_dice_game(telegram_id1, telegram_id2):
#     """Тест игры в кости"""
#     print("🎲 Тестирование игры в кости...")
    
#     # Создание комнаты
#     response = requests.post(f"{BASE_URL}/api/games/create-room?game_type=dice&bet_amount=10&max_players=2&telegram_id={telegram_id1}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка создания комнаты: {response.text}")
#         return False
    
#     room = response.json()
#     room_id = room["room_id"]
#     print(f"✅ Комната создана: {room_id}")
    
#     # Присоединение второго игрока
#     response = requests.post(f"{BASE_URL}/api/games/join-room/{room_id}?telegram_id={telegram_id2}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка присоединения к комнате: {response.text}")
#         return False
    
#     print("✅ Второй игрок присоединился")
    
#     # Запуск игры
#     response = requests.post(f"{BASE_URL}/api/games/start-game/{room_id}?telegram_id={telegram_id1}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка запуска игры: {response.text}")
#         return False
    
#     print("✅ Игра запущена")
    
#     # Бросок костей
#     dice_data = {"dice_count": 2}
#     response = requests.post(f"{BASE_URL}/api/dice/{room_id}/roll?telegram_id={telegram_id1}", json=dice_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка броска костей: {response.text}")
#         return False
    
#     roll_result = response.json()
#     print(f"🎲 Результат броска игрока 1: {roll_result['results']}, Сумма: {roll_result['total']}")
    
#     # Бросок костей второго игрока
#     response = requests.post(f"{BASE_URL}/api/dice/{room_id}/roll?telegram_id={telegram_id2}", json=dice_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка броска костей игрока 2: {response.text}")
#         return False
    
#     roll_result2 = response.json()
#     print(f"🎲 Результат броска игрока 2: {roll_result2['results']}, Сумма: {roll_result2['total']}")
    
#     return True

# def test_rps_game(telegram_id1, telegram_id2):
#     """Тест игры в камень-ножницы-бумага"""
#     print("✂️ Тестирование игры камень-ножницы-бумага...")
    
#     # Создание комнаты
#     response = requests.post(f"{BASE_URL}/api/games/create-room?game_type=rps&bet_amount=5&max_players=2&telegram_id={telegram_id1}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка создания комнаты RPS: {response.text}")
#         return False
    
#     room = response.json()
#     room_id = room["room_id"]
#     print(f"✅ RPS комната создана: {room_id}")
    
#     # Присоединение второго игрока
#     response = requests.post(f"{BASE_URL}/api/games/join-room/{room_id}?telegram_id={telegram_id2}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка присоединения к RPS комнате: {response.text}")
#         return False
    
#     print("✅ Второй игрок присоединился")
    
#     # Запуск игры
#     response = requests.post(f"{BASE_URL}/api/games/start-game/{room_id}?telegram_id={telegram_id1}")
#     if response.status_code != 200:
#         print(f"❌ Ошибка запуска RPS игры: {response.text}")
#         return False
    
#     print("✅ RPS игра запущена")
    
#     # Ходы игроков
#     choice1_data = {"choice": "rock"}
#     response = requests.post(f"{BASE_URL}/api/rps/{room_id}/play?telegram_id={telegram_id1}", json=choice1_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка хода игрока 1: {response.text}")
#         return False
    
#     choice2_data = {"choice": "scissors"}
#     response = requests.post(f"{BASE_URL}/api/rps/{room_id}/play?telegram_id={telegram_id2}", json=choice2_data)
#     if response.status_code != 200:
#         print(f"❌ Ошибка хода игрока 2: {response.text}")
#         return False
    
#     result = response.json()
#     print(f"✂️ Результат RPS: {result['message']}")
    
#     return True

# def test_user_stats(telegram_id):
#     """Получение статистики пользователя"""
#     print(f"📊 Получение статистики пользователя {telegram_id}...")
    
#     response = requests.get(f"{BASE_URL}/api/users/{telegram_id}")
#     if response.status_code == 200:
#         user = response.json()
#         print(f"✅ Баланс: {user['stars_balance']} звезд")
#         print(f"   Игр сыграно: {user['total_games']}")
#         print(f"   Игр выиграно: {user['wins']}")
#         return True
#     else:
#         print(f"❌ Ошибка получения статистики: {response.text}")
#         return False

# def main():
#     """Основная функция тестирования"""
#     print("🚀 Запуск тестирования интеграции игр с БД")
#     print("=" * 50)
    
#     # Создание пользователей
#     user1 = test_user_creation()
#     if not user1:
#         return
    
#     # Создание второго пользователя для игр
#     user_data2 = {
#         "telegram_id": 987654321,
#         "username": "test_player2",
#         "first_name": "Test2",
#         "last_name": "Player2"
#     }
    
#     response = requests.post(f"{BASE_URL}/api/users", json=user_data2)
#     if response.status_code != 200:
#         print(f"❌ Ошибка создания второго пользователя: {response.text}")
#         return
    
#     user2 = response.json()
#     print(f"✅ Второй пользователь создан: {user_data2['username']} (ID: {user2['user_id']})")
    
#     # Добавление звезд обоим пользователям
#     if not test_add_stars(user1["telegram_id"]):
#         return
#     if not test_add_stars(user_data2["telegram_id"]):
#         return
    
#     # Тест игры в кости
#     if not test_dice_game(user1["telegram_id"], user_data2["telegram_id"]):
#         return
    
#     # Тест RPS игры
#     test_rps_game(user1["telegram_id"], user_data2["telegram_id"])
    
#     # Статистика обоих пользователей
#     test_user_stats(user1["telegram_id"])
#     test_user_stats(user_data2["telegram_id"])
    
#     print("=" * 50)
#     print("🎉 Тестирование завершено!")

# if __name__ == "__main__":
#     main()
