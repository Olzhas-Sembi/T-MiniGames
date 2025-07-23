#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных NFT системы
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from server.database_sqlite import engine, User, NFTItem, Case, CaseItem
from uuid import uuid4

# Создаем сессию
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def create_test_nft_data():
    """Создает тестовые данные для NFT системы"""
    
    # Создаем NFT предметы
    nft_items = [
        # Аватары
        {
            "id": str(uuid4()),
            "name": "Космонавт",
            "description": "Редкий аватар космонавта",
            "image_url": "https://via.placeholder.com/200x200/4338ca/ffffff?text=Космонавт",
            "rarity": "rare",
            "nft_type": "avatar",
            "stars_value": 500
        },
        {
            "id": str(uuid4()),
            "name": "Киберпанк",
            "description": "Эпический аватар в стиле киберпанк",
            "image_url": "https://via.placeholder.com/200x200/7c3aed/ffffff?text=Киберпанк",
            "rarity": "epic",
            "nft_type": "avatar",
            "stars_value": 1000
        },
        {
            "id": str(uuid4()),
            "name": "Золотой Робот",
            "description": "Легендарный золотой робот",
            "image_url": "https://via.placeholder.com/200x200/f59e0b/ffffff?text=Золотой+Робот",
            "rarity": "legendary",
            "nft_type": "avatar",
            "stars_value": 2500
        },
        
        # Карты
        {
            "id": str(uuid4()),
            "name": "Огненная Карта",
            "description": "Обычная карта с огненным эффектом",
            "image_url": "https://via.placeholder.com/200x200/ef4444/ffffff?text=Огонь",
            "rarity": "common",
            "nft_type": "card",
            "stars_value": 100
        },
        {
            "id": str(uuid4()),
            "name": "Ледяная Карта",
            "description": "Необычная карта с ледяным эффектом",
            "image_url": "https://via.placeholder.com/200x200/3b82f6/ffffff?text=Лед",
            "rarity": "uncommon",
            "nft_type": "card",
            "stars_value": 250
        },
        {
            "id": str(uuid4()),
            "name": "Молниеносная Карта",
            "description": "Редкая карта с электрическим эффектом",
            "image_url": "https://via.placeholder.com/200x200/a855f7/ffffff?text=Молния",
            "rarity": "rare",
            "nft_type": "card",
            "stars_value": 750
        },
        
        # Стикеры
        {
            "id": str(uuid4()),
            "name": "Смайлик",
            "description": "Обычный веселый смайлик",
            "image_url": "https://via.placeholder.com/200x200/22c55e/ffffff?text=😊",
            "rarity": "common",
            "nft_type": "sticker",
            "stars_value": 50
        },
        {
            "id": str(uuid4()),
            "name": "Крутой Череп",
            "description": "Эпический стикер черепа",
            "image_url": "https://via.placeholder.com/200x200/6b7280/ffffff?text=💀",
            "rarity": "epic",
            "nft_type": "sticker",
            "stars_value": 800
        },
        
        # Рамки
        {
            "id": str(uuid4()),
            "name": "Простая Рамка",
            "description": "Обычная рамка для профиля",
            "image_url": "https://via.placeholder.com/200x200/94a3b8/ffffff?text=Рамка",
            "rarity": "common",
            "nft_type": "frame",
            "stars_value": 150
        },
        {
            "id": str(uuid4()),
            "name": "Золотая Рамка",
            "description": "Легендарная золотая рамка",
            "image_url": "https://via.placeholder.com/200x200/fbbf24/ffffff?text=Золото",
            "rarity": "legendary",
            "nft_type": "frame",
            "stars_value": 3000
        }
    ]
    
    # Добавляем NFT предметы в базу
    for item_data in nft_items:
        nft_item = NFTItem(**item_data)
        db.add(nft_item)
    
    # Создаем кейсы
    cases = [
        {
            "id": str(uuid4()),
            "name": "Стартовый Кейс",
            "description": "Идеальный кейс для новичков с базовыми предметами",
            "image_url": "https://via.placeholder.com/300x300/3b82f6/ffffff?text=Стартовый+Кейс",
            "price_stars": 200,
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "Премиум Кейс",
            "description": "Кейс с редкими и эпическими предметами",
            "image_url": "https://via.placeholder.com/300x300/7c3aed/ffffff?text=Премиум+Кейс",
            "price_stars": 500,
            "is_active": True
        },
        {
            "id": str(uuid4()),
            "name": "Легендарный Кейс",
            "description": "Самые редкие и ценные NFT предметы",
            "image_url": "https://via.placeholder.com/300x300/f59e0b/ffffff?text=Легендарный+Кейс",
            "price_stars": 1000,
            "is_active": True
        }
    ]
    
    # Добавляем кейсы в базу
    case_objects = []
    for case_data in cases:
        case = Case(**case_data)
        db.add(case)
        case_objects.append(case)
    
    # Сохраняем изменения чтобы получить ID
    db.commit()
    
    # Создаем связи кейсов с предметами
    case_items = [
        # Стартовый кейс - обычные и необычные предметы
        {"case_id": case_objects[0].id, "nft_item_id": nft_items[3]["id"], "drop_chance": 30.0, "min_value": 90, "max_value": 110},  # Огненная карта
        {"case_id": case_objects[0].id, "nft_item_id": nft_items[4]["id"], "drop_chance": 25.0, "min_value": 200, "max_value": 300},  # Ледяная карта
        {"case_id": case_objects[0].id, "nft_item_id": nft_items[6]["id"], "drop_chance": 25.0, "min_value": 40, "max_value": 60},  # Смайлик
        {"case_id": case_objects[0].id, "nft_item_id": nft_items[8]["id"], "drop_chance": 20.0, "min_value": 120, "max_value": 180},  # Простая рамка
        
        # Премиум кейс - редкие и эпические
        {"case_id": case_objects[1].id, "nft_item_id": nft_items[0]["id"], "drop_chance": 25.0, "min_value": 450, "max_value": 550},  # Космонавт
        {"case_id": case_objects[1].id, "nft_item_id": nft_items[1]["id"], "drop_chance": 15.0, "min_value": 900, "max_value": 1100},  # Киберпанк
        {"case_id": case_objects[1].id, "nft_item_id": nft_items[5]["id"], "drop_chance": 30.0, "min_value": 650, "max_value": 850},  # Молниеносная карта
        {"case_id": case_objects[1].id, "nft_item_id": nft_items[7]["id"], "drop_chance": 20.0, "min_value": 700, "max_value": 900},  # Крутой череп
        {"case_id": case_objects[1].id, "nft_item_id": nft_items[4]["id"], "drop_chance": 10.0, "min_value": 200, "max_value": 300},  # Ледяная карта
        
        # Легендарный кейс - эпические и легендарные
        {"case_id": case_objects[2].id, "nft_item_id": nft_items[2]["id"], "drop_chance": 10.0, "min_value": 2000, "max_value": 3000},  # Золотой робот
        {"case_id": case_objects[2].id, "nft_item_id": nft_items[9]["id"], "drop_chance": 15.0, "min_value": 2500, "max_value": 3500},  # Золотая рамка
        {"case_id": case_objects[2].id, "nft_item_id": nft_items[1]["id"], "drop_chance": 25.0, "min_value": 900, "max_value": 1100},  # Киберпанк
        {"case_id": case_objects[2].id, "nft_item_id": nft_items[7]["id"], "drop_chance": 30.0, "min_value": 700, "max_value": 900},  # Крутой череп
        {"case_id": case_objects[2].id, "nft_item_id": nft_items[0]["id"], "drop_chance": 20.0, "min_value": 450, "max_value": 550},  # Космонавт
    ]
    
    # Добавляем связи кейсов с предметами
    for item_data in case_items:
        case_item = CaseItem(**item_data)
        db.add(case_item)
    
    # Создаем тестового пользователя
    test_user = User(
        telegram_id="123456789",
        username="test_user",
        first_name="Test",
        stars_balance=2000,  # Начальный баланс для тестирования
        total_games=0,
        wins=0
    )
    
    # Проверяем, не существует ли уже такой пользователь
    existing_user = db.query(User).filter(User.telegram_id == "123456789").first()
    if not existing_user:
        db.add(test_user)
    
    # Сохраняем все изменения
    db.commit()
    print("✅ Тестовые данные NFT системы созданы успешно!")
    print(f"📦 Создано {len(nft_items)} NFT предметов")
    print(f"🎁 Создано {len(cases)} кейсов")
    print(f"🔗 Создано {len(case_items)} связей кейс-предмет")
    print("👤 Создан тестовый пользователь с балансом 2000 звезд")

def cleanup_test_data():
    """Удаляет тестовые данные"""
    db.query(CaseItem).delete()
    db.query(Case).delete()
    db.query(NFTItem).delete()
    # Не удаляем тестового пользователя, только обнуляем баланс
    test_user = db.query(User).filter(User.telegram_id == "123456789").first()
    if test_user:
        test_user.stars_balance = 0
    db.commit()
    print("🧹 Тестовые данные очищены")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        create_test_nft_data()
    
    db.close()
