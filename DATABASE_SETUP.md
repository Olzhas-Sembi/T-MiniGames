# Настройка базы данных для Telegram Mini Games

## Вариант 1: Использование Docker (рекомендуется)

### 1. Установите Docker
Скачайте и установите Docker Desktop с официального сайта.

### 2. Запустите PostgreSQL через Docker
```bash
# Из корневой папки проекта
docker-compose up -d
```

Это запустит:
- PostgreSQL на порту 5432 
- pgAdmin на порту 8080 (admin@admin.com / admin)

### 3. Инициализируйте базу данных
```bash
cd server
python init_db.py
```

## Вариант 2: Локальная установка PostgreSQL

### 1. Установите PostgreSQL
- Windows: Скачайте с https://www.postgresql.org/download/windows/
- Создайте базу данных `minigames_db`
- Пользователь: `postgres`, пароль: `password`

### 2. Настройте подключение
Отредактируйте файл `server/.env`:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/minigames_db
```

### 3. Инициализируйте базу данных
```bash
cd server
python init_db.py
```

## Проверка подключения

После настройки выполните:
```bash
cd server
python -c "from database import engine; print('✅ Подключение к БД работает!')"
```

## Структура базы данных

Созданные таблицы:
- `users` - Пользователи Telegram
- `game_rooms` - Игровые комнаты
- `game_participations` - Участие в играх
- `transactions` - Транзакции звезд
- `nfts` - NFT предметы
- `news_items` - Новости
- `roulette_giveaways` - Розыгрыши рулетки

## Следующие шаги

1. ✅ База данных настроена
2. Интеграция с FastAPI сервером
3. Добавление недостающих игр
4. Настройка Telegram Bot
5. Интеграция платежей

## Полезные команды

```bash
# Просмотр таблиц
psql -h localhost -U postgres -d minigames_db -c "\dt"

# Подключение к pgAdmin
# http://localhost:8080 (admin@admin.com / admin)
```
