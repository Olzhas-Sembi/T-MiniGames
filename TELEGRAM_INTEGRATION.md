# 🤖 Telegram Bot Integration с aiogram

Интеграция Telegram бота с платежами и Mini App для T-MiniGames.

## 📦 Установка и настройка

### 1. Установка зависимостей

```bash
cd server
pip install aiogram==3.13.0
```

### 2. Создание бота в Telegram

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Введите имя бота: `T-MiniGames Bot`
4. Введите username: `your_minigames_bot`
5. Получите `BOT_TOKEN`

### 3. Настройка платежей

1. У @BotFather выберите ваш бот
2. `Bot Settings` → `Payments`
3. Выберите провайдера (например, Stripe Test)
4. Получите `PAYMENT_PROVIDER_TOKEN`

### 4. Настройка Mini App

1. У @BotFather: `Bot Settings` → `Menu Button`
2. Установите URL: `https://your-domain.com`
3. `Bot Settings` → `Domain` → добавьте ваш домен

### 5. Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_PAYMENT_PROVIDER_TOKEN=your_payment_provider_token_here
TELEGRAM_WEBAPP_URL=https://your-domain.com
```

## 🚀 Запуск

### Режим polling (для разработки)

```bash
cd server
python run_bot.py
```

### Режим webhook (для продакшена)

1. Установите `TELEGRAM_WEBHOOK_URL` в `.env`
2. Запустите FastAPI сервер
3. Webhook автоматически установится при старте

```bash
cd server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🏗️ Архитектура

### Компоненты

```
server/
├── telegram_bot/
│   ├── __init__.py
│   ├── bot_config.py          # Конфигурация aiogram
│   ├── webhook.py             # Webhook обработчик
│   ├── run_bot.py             # Запуск в polling режиме
│   └── handlers/
│       ├── __init__.py        # Регистрация роутеров
│       ├── commands.py        # Команды (/start, /help)
│       └── payments.py        # Платежи (pre_checkout, successful_payment)
```

### Поток данных

```
User → Telegram → Bot API → FastAPI Webhook → aiogram → Обработчики
```

## 💳 Платежи

### Пакеты звёзд

- 100 ⭐ - $2.00
- 500 ⭐ - $8.00  
- 1000 ⭐ - $15.00
- 5000 ⭐ - $60.00

### Обработка платежей

1. **Пользователь**: нажимает "Купить звёзды"
2. **Бот**: отправляет `sendInvoice`
3. **Telegram**: показывает форму оплаты
4. **Система**: получает `pre_checkout_query` → проверяет → подтверждает
5. **Пользователь**: оплачивает
6. **Система**: получает `successful_payment` → зачисляет звёзды

### Код обработки

```python
@payments_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    # Проверки перед оплатой
    await pre_checkout_query.answer(ok=True)

@payments_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    # Зачисление звёзд пользователю
    payment = message.successful_payment
    # Обработка...
```

## 🌐 Mini App Integration

### Frontend (React)

```typescript
import { telegramWebApp } from '../services/telegramWebApp';

// Инициализация
const { isAvailable, user, initData } = useTelegramWebApp();

// Отправка данных боту
telegramWebApp.sendData({
  action: 'buy_stars',
  package: { stars: 100, price: 200 }
});

// Главная кнопка
telegramWebApp.setMainButton('Купить звёзды', () => {
  // Обработка
});
```

### Проверка пользователя на сервере

```python
from aiogram.utils.web_app import check_webapp_signature

def verify_telegram_user(init_data: str) -> bool:
    return check_webapp_signature(
        token=settings.TELEGRAM_BOT_TOKEN,
        init_data=init_data
    )
```

## 🎮 Команды бота

- `/start` - Главное меню с кнопкой Mini App
- `/help` - Справка
- `/profile` - Профиль пользователя
- `/balance` - Баланс звёзд

## 🔧 Настройки webhook

```python
# Установка webhook
await bot.set_webhook(
    url="https://your-domain.com/webhook/telegram",
    secret_token="your-secret-token"
)

# Обработка в FastAPI
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    # Проверка secret_token
    # Обработка Update
    return {"ok": True}
```

## 🛠️ Разработка

### Добавление новых команд

1. Создайте обработчик в `handlers/commands.py`:

```python
@commands_router.message(Command("newcommand"))
async def cmd_new_command(message: Message):
    await message.answer("Новая команда!")
```

### Добавление новых типов платежей

1. Расширьте `handlers/payments.py`
2. Добавьте новые `LabeledPrice` пакеты
3. Обновите логику в `process_successful_payment`

### Тестирование

```bash
# Тестирование команд
python -m pytest server/tests/test_telegram_bot.py

# Локальный запуск
python server/run_bot.py
```

## 📱 Telegram WebApp API

### Основные методы

```javascript
// Инициализация
window.Telegram.WebApp.ready();
window.Telegram.WebApp.expand();

// Получение пользователя
const user = window.Telegram.WebApp.initDataUnsafe.user;

// Главная кнопка
window.Telegram.WebApp.MainButton.setText("Купить");
window.Telegram.WebApp.MainButton.show();

// Вибрация
window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');

// Закрытие приложения
window.Telegram.WebApp.close();
```

## 🔒 Безопасность

### Проверка подписи

```python
import hmac
import hashlib
from urllib.parse import unquote

def verify_webapp_data(init_data: str, bot_token: str) -> bool:
    try:
        parsed_data = dict(param.split('=') for param in init_data.split('&'))
        hash_value = parsed_data.pop('hash', '')
        
        secret_key = hmac.new(
            "WebAppData".encode(), 
            bot_token.encode(), 
            hashlib.sha256
        ).digest()
        
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        calculated_hash = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == hash_value
    except:
        return False
```

## 🚨 Troubleshooting

### Проблемы с webhook

1. Проверьте SSL сертификат
2. Убедитесь что webhook URL доступен
3. Проверьте secret_token

### Проблемы с платежами

1. Проверьте PAYMENT_PROVIDER_TOKEN
2. Убедитесь что тестовые платежи включены
3. Проверьте валюту (USD)

### Проблемы с Mini App

1. Проверьте домен в настройках бота
2. Убедитесь что HTTPS включен
3. Проверьте CORS настройки

## 📊 Мониторинг

### Логирование

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Бот запущен")
```

### Метрики

- Количество активных пользователей
- Количество успешных платежей
- Ошибки webhook
- Время ответа обработчиков

## 🔄 CI/CD

### GitHub Actions

```yaml
name: Deploy Bot
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: |
          # Deploy script
          docker-compose up -d
```

## 📚 Ресурсы

- [aiogram документация](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Telegram Payments API](https://core.telegram.org/bots/payments)
