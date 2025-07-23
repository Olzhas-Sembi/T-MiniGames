"""
Скрипт для инициализации базы данных
"""
from .database import Base, engine
from .config import settings
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Создание всех таблиц в базе данных"""
    try:
        logger.info("Создание таблиц базы данных...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных успешно инициализирована!")
        
        # Вывод информации о созданных таблицах
        table_names = list(Base.metadata.tables.keys())
        logger.info(f"📊 Созданные таблицы: {', '.join(table_names)}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании базы данных: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Инициализация базы данных...")
    print(f"🔗 URL базы данных: {settings.DATABASE_URL}")
    init_db()
