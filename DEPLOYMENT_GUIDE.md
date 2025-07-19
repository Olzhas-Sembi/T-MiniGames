# 🚀 Пошаговый гайд по запуску в Telegram

## 📱 **1. Создание бота**

### Создайте бота через @BotFather:
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Название: `Mini Games Live`
4. Username: `minigames_live_bot` (или любой доступный)
5. **СОХРАНИТЕ ТОКЕН** - он понадобится!

### Создайте Mini App:
1. В @BotFather отправьте `/newapp`
2. Выберите созданного бота
3. Название: `Mini Games Live`
4. Описание: `Играйте в кубики, карты и РПС с друзьями!`
5. Фото: загрузите иконку 512x512 PNG
6. URL пока укажите временный: `https://example.com`

## 🌐 **2. Деплой приложения**

### Вариант A: Vercel + Railway (Рекомендуется)

#### **Frontend на Vercel:**
1. Зайдите на [vercel.com](https://vercel.com)
2. Подключите GitHub репозиторий
3. Root Directory: `client/telegram-mini-games`
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Деплой займет 2-3 минуты
7. **Сохраните URL:** `https://your-app.vercel.app`

#### **Backend на Railway:**
1. Зайдите на [railway.app](https://railway.app)
2. Создайте новый проект из GitHub
3. Root Directory: `server`
4. Start Command: `python main.py`
5. Environment Variables:
   - `BOT_TOKEN=ваш_токен_от_BotFather`
   - `WEBAPP_URL=https://your-app.vercel.app`
6. **Сохраните URL:** `https://your-api.railway.app`

### Вариант B: Heroku
1. Создайте аккаунт на [heroku.com](https://heroku.com)
2. Установите Heroku CLI
3. Выполните команды:

```bash
# Создание приложения
heroku create your-minigames-app

# Настройка переменных
heroku config:set BOT_TOKEN=ваш_токен
heroku config:set WEBAPP_URL=https://your-minigames-app.herokuapp.com

# Деплой
git push heroku main
```

## 🔧 **3. Настройка интеграции**

### Обновите переменные в коде:

#### **Frontend** (`src/services/gameAPI.ts`):
```typescript
const API_BASE_URL = 'https://your-api.railway.app'; // Ваш backend URL
```

#### **Backend** (`telegram_bot/bot.py`):
```python
BOT_TOKEN = "ваш_токен_от_BotFather"
WEBAPP_URL = "https://your-app.vercel.app"
API_URL = "https://your-api.railway.app"
```

### Обновите URL в @BotFather:
1. Команда `/editapp`
2. Выберите ваш бот и Mini App
3. Выберите "Edit Web App URL"
4. Укажите: `https://your-app.vercel.app`

## 🤖 **4. Запуск Telegram Bot**

### Локально для тестирования:
```bash
cd telegram_bot
pip install -r requirements.txt
python bot.py
```

### На сервере (Railway/Heroku):
1. Добавьте `telegram_bot/` в ваш репозиторий
2. Обновите `requirements.txt` в server:
```
fastapi==0.115.5
uvicorn==0.32.1
pydantic==2.5.0
python-multipart==0.0.6
websockets==12.0
aiogram==3.13.1
aiohttp==3.10.10
python-dotenv==1.0.1
```

3. Обновите `main.py` для запуска и API и бота:
```python
import asyncio
from telegram_bot.bot import main as bot_main

async def start_services():
    # Запуск API и Telegram бота одновременно
    await asyncio.gather(
        uvicorn.run(app, host="0.0.0.0", port=8000),
        bot_main()
    )
```

## ✅ **5. Тестирование**

### Проверьте все работает:
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Нажмите "🚀 Играть"
4. Должно открыться ваше приложение
5. Попробуйте создать комнату и пригласить друга

### Пример работающей ссылки:
`https://t.me/your_bot?startapp=join_room123`

## 💰 **6. Настройка платежей (Опционально)**

### Telegram Stars:
1. В @BotFather: `/setpayments`
2. Выберите провайдера платежей
3. Добавьте в код обработку платежей
4. Интеграция с Telegram Payments API

### TON Connect:
1. Подключите TON Connect SDK
2. Настройте кошелек для приема платежей
3. Интеграция с TON блокчейном

## 🎉 **Готово!**

Ваше приложение теперь доступно в Telegram как Mini App!

**Возможные проблемы:**
- CORS ошибки: добавьте домены в backend/main.py
- WebSocket не работает: проверьте поддержку WSS
- Стили не загружаются: проверьте build конфигурацию

**Поддержка:**
- Документация Telegram Bot API
- Документация Telegram Mini Apps
- GitHub Issues в репозитории проекта
