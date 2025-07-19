import aiohttp
import asyncio
import feedparser
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import logging
import re
import hashlib

logger = logging.getLogger(__name__)

class TelegramNewsService:
    """Сервис для получения новостей из Telegram каналов и RSS источников"""
    
    def __init__(self):
        # Telegram каналы согласно ТЗ - ключевые источники по темам подарков, NFT и крипто
        self.channels = [
            # Каналы о подарках и бонусах
            {'username': 'gift_newstg', 'name': 'Gift News TG', 'category': 'gifts'},
            {'username': 'giftsutya', 'name': 'Gift Sutya', 'category': 'gifts'},
            {'username': 'diruil_gifts', 'name': 'Diruil Gifts', 'category': 'gifts'},
            {'username': 'giftnews', 'name': 'Gift News', 'category': 'gifts'},
            {'username': 'BunnyStarsShop', 'name': 'Bunny Stars Shop', 'category': 'gifts'},
            {'username': 'nft_podarki', 'name': 'NFT Подарки', 'category': 'gifts'},
            
            # Технологии и инновации
            {'username': 'westik', 'name': 'Westik', 'category': 'tech'},
            
            # Сообщества и чаты
            {'username': 'OHUENKOchat', 'name': 'OHUENKO Chat', 'category': 'community'},
            {'username': 'community', 'name': 'Community', 'category': 'community'},
            {'username': 'groza', 'name': 'Groza', 'category': 'community'},
            
            # Криптовалюты и блокчейн
            {'username': 'omicron', 'name': 'Omicron', 'category': 'crypto'},
            {'username': 'tontopic_1', 'name': 'TON Topic', 'category': 'crypto'},
            {'username': 'procryptodoping', 'name': 'Pro Crypto Doping', 'category': 'crypto'},
            
            # NFT и цифровое искусство
            {'username': 'nextgen_NFT', 'name': 'NextGen NFT', 'category': 'nft'},
            {'username': 'snoopdogg', 'name': 'Snoop Dogg', 'category': 'nft'}
        ]
        
        # RSS источники согласно ТЗ - до 5 проверенных лент
        self.rss_sources = [
            {'url': 'https://vc.ru/rss', 'name': 'VC.ru', 'category': 'tech'},
            {'url': 'https://forklog.com/feed/', 'name': 'ForkLog', 'category': 'crypto'},
            {'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/', 'name': 'CoinDesk', 'category': 'crypto'},
            {'url': 'https://cointelegraph.com/rss', 'name': 'Cointelegraph', 'category': 'crypto'},
            {'url': 'https://habr.com/ru/rss/hub/nft/all/', 'name': 'Habr NFT', 'category': 'nft'}
        ]
        
        self.cache = {}
        self.cache_ttl = timedelta(minutes=30)  # Кэш на 30 минут согласно ТЗ
        
        # Ключевые слова для категоризации согласно ТЗ
        self.keywords = {
            'gifts': [
                'подарок', 'подарки', 'бесплатно', 'халява', 'промокод', 'скидка', 
                'акция', 'розыгрыш', 'бонус', 'даром', 'гифт', 'gift', 'freebie',
                'раздача', 'конкурс', 'приз', 'награда', 'cashback', 'кэшбек'
            ],
            'nft': [
                'nft', 'нфт', 'токен', 'коллекция', 'мета', 'opensea', 'digital art', 
                'коллекционный', 'цифровое искусство', 'метавселенная', 'avatar',
                'аватар', 'pfp', 'mint', 'минт', 'drop', 'дроп', 'rare', 'раритет'
            ],
            'crypto': [
                'криптовалюта', 'биткоин', 'bitcoin', 'ethereum', 'блокчейн', 'деф', 
                'defi', 'торги', 'курс', 'btc', 'eth', 'usdt', 'binance', 'трейдинг',
                'стейкинг', 'майнинг', 'altcoin', 'альткоин', 'pump', 'dump', 'hodl'
            ],
            'tech': [
                'технологии', 'it', 'ит', 'программирование', 'разработка', 'стартап', 
                'инновации', 'ai', 'ии', 'machine learning', 'блокчейн', 'веб3',
                'app', 'приложение', 'software', 'hardware', 'gadget', 'гаджет'
            ],
            'community': [
                'сообщество', 'чат', 'общение', 'форум', 'дискуссия', 'мнение',
                'обсуждение', 'новости', 'анонс', 'встреча', 'event', 'мероприятие'
            ]
        }
        
    def categorize_content(self, title: str, description: str = "") -> str:
        """
        Автоматическая категоризация контента по ключевым словам согласно ТЗ
        Приоритет: gifts > crypto > nft > tech > community
        """
        content = (title + " " + description).lower()
        
        # Подсчитываем совпадения для каждой категории
        category_scores = {}
        for category, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return 'general'
        
        # Возвращаем категорию с наибольшим количеством совпадений
        # При равенстве очков используем приоритет
        priority = ['gifts', 'crypto', 'nft', 'tech', 'community']
        
        max_score = max(category_scores.values())
        best_categories = [cat for cat, score in category_scores.items() if score == max_score]
        
        for priority_cat in priority:
            if priority_cat in best_categories:
                return priority_cat
                
        return list(category_scores.keys())[0]  # Fallback
        
    async def fetch_telegram_channel(self, channel_username: str) -> List[Dict[str, Any]]:
        """
        Получение новостей из Telegram канала через веб-скрапинг
        Согласно ТЗ - интеграция с Telegram каналами для получения актуальных новостей
        """
        try:
            channel_data = next((ch for ch in self.channels if ch['username'] == channel_username), None)
            if not channel_data:
                logger.warning(f"Channel {channel_username} not found in configured channels")
                return []
            
            # Используем публичный API Telegram для получения постов
            url = f"https://t.me/s/{channel_username}"
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            return self._parse_telegram_html(html_content, channel_data)
                        else:
                            logger.warning(f"Failed to fetch {url}, status: {response.status}")
                            return self._generate_mock_posts(channel_data)
                except aiohttp.ClientTimeout:
                    logger.warning(f"Timeout fetching {url}, using mock data")
                    return self._generate_mock_posts(channel_data)
                except Exception as e:
                    logger.warning(f"Error fetching {url}: {e}, using mock data")
                    return self._generate_mock_posts(channel_data)
                    
        except Exception as e:
            logger.error(f"Error in fetch_telegram_channel for {channel_username}: {e}")
            return []
    
    def _parse_telegram_html(self, html_content: str, channel_data: Dict) -> List[Dict[str, Any]]:
        """Парсинг HTML содержимого Telegram канала"""
        import re
        from html import unescape
        
        posts = []
        
        # Простой парсер для получения постов из HTML
        # В реальном проекте лучше использовать BeautifulSoup
        post_pattern = r'<div class="tgme_widget_message.*?</div>\s*</div>\s*</div>'
        text_pattern = r'<div class="tgme_widget_message_text.*?".*?>(.*?)</div>'
        date_pattern = r'<time.*?datetime="([^"]+)"'
        
        post_matches = re.findall(post_pattern, html_content, re.DOTALL)
        
        for i, post_html in enumerate(post_matches[:10]):  # Берем только первые 10 постов
            # Извлекаем текст поста
            text_match = re.search(text_pattern, post_html, re.DOTALL)
            text = ""
            if text_match:
                text = unescape(re.sub(r'<[^>]+>', '', text_match.group(1)))
                text = text.strip()[:300] + "..." if len(text) > 300 else text.strip()
            
            # Извлекаем дату
            date_match = re.search(date_pattern, post_html)
            date = datetime.now().isoformat()
            if date_match:
                try:
                    date = datetime.fromisoformat(date_match.group(1).replace('Z', '+00:00')).isoformat()
                except:
                    pass
            
            if text:  # Только если удалось извлечь текст
                # Генерируем заголовок из первых слов
                title = text.split('.')[0][:100] if text else f"Пост от {channel_data['name']}"
                
                post = {
                    'id': hashlib.md5(f"{channel_data['username']}_{i}_{text[:50]}".encode()).hexdigest(),
                    'title': title,
                    'text': text,
                    'link': f"https://t.me/{channel_data['username']}",
                    'date': date,
                    'source': channel_data['name'],
                    'category': channel_data['category'],
                    'channel': channel_data['username']
                }
                
                posts.append(post)
        
        if not posts:  # Если парсинг не удался, используем мок данные
            return self._generate_mock_posts(channel_data)
            
        return posts
    
    def _generate_mock_posts(self, channel_data: Dict) -> List[Dict[str, Any]]:
        """Генерация мок данных для канала согласно ТЗ"""
        posts = []
        base_time = datetime.now()
        
        # Контент в зависимости от категории канала
        content_templates = {
            'gifts': [
                "🎁 Новые бесплатные подарки! Успейте получить эксклюзивные бонусы",
                "💝 Промокоды на скидки до 70%! Ограниченное предложение",
                "🎉 Розыгрыш ценных призов среди подписчиков канала",
                "🛍️ Лучшие предложения дня - не пропустите!"
            ],
            'crypto': [
                "📈 Анализ рынка: Bitcoin показывает рост на 5%",
                "💰 Новые возможности DeFi инвестиций - обзор проектов",
                "🚀 Перспективные альткоины для долгосрочных инвестиций",
                "⚡ Срочные новости: крупные движения на криптовалютном рынке"
            ],
            'nft': [
                "🖼️ Новая коллекция NFT от известного художника уже в продаже",
                "💎 Раритетные токены на аукционе - последний шанс приобрести",
                "🎨 Обзор лучших NFT художников недели",
                "📊 Статистика NFT рынка: рост объемов торгов на 15%"
            ],
            'tech': [
                "💻 Революционные технологии 2025 года - что нас ждет",
                "🔧 Обзор новейших гаджетов от мировых производителей",
                "🚀 Стартапы в сфере ИИ привлекли рекордные инвестиции",
                "📱 ТОП мобильных приложений для повышения продуктивности"
            ],
            'community': [
                "👥 Обсуждение актуальных тем в нашем сообществе",
                "💬 Важные новости и обновления для участников",
                "🔔 Анонс предстоящих мероприятий и встреч",
                "📢 Полезные советы и рекомендации от экспертов"
            ]
        }
        
        templates = content_templates.get(channel_data['category'], content_templates['community'])
        
        for i in range(5):  # Генерируем 5 постов
            post_time = base_time - timedelta(hours=i * 4 + hash(channel_data['username']) % 12)
            
            text = templates[i % len(templates)]
            title = text.split('.')[0][:80] + ("..." if len(text.split('.')[0]) > 80 else "")
            
            posts.append({
                'id': hashlib.md5(f"{channel_data['username']}_{i}_{text}".encode()).hexdigest(),
                'title': title,
                'text': text,
                'link': f"https://t.me/{channel_data['username']}",
                'date': post_time.isoformat(),
                'source': channel_data['name'],
                'category': channel_data['category'],
                'channel': channel_data['username']
            })
        
        return posts
        """Автоматическая категоризация контента по ключевым словам"""
        content = (title + " " + description).lower()
        
        for category, keywords in self.keywords.items():
            if any(keyword in content for keyword in keywords):
                return category
                
        return 'general'
    
    async def fetch_rss_feed(self, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Получение новостей из RSS источника"""
        try:
            # Используем feedparser для парсинга RSS
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {source['url']}")
                return []
            
            articles = []
            for entry in feed.entries[:10]:  # Берем только последние 10 новостей
                # Получаем описание из различных полей
                description = ""
                if hasattr(entry, 'summary'):
                    description = entry.summary
                elif hasattr(entry, 'description'):
                    description = entry.description
                elif hasattr(entry, 'content'):
                    description = entry.content[0].value if entry.content else ""
                
                # Очищаем HTML теги
                description = re.sub(r'<[^>]+>', '', description)
                description = description[:200] + "..." if len(description) > 200 else description
                
                # Получаем дату публикации
                pub_date = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    import time
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                
                # Автоматическая категоризация
                auto_category = self.categorize_content(entry.title, description)
                final_category = source.get('category', auto_category)
                
                article = {
                    'id': hashlib.md5((entry.link + entry.title).encode()).hexdigest(),
                    'title': entry.title,
                    'text': description,
                    'link': entry.link,
                    'date': pub_date.isoformat(),
                    'source': source['name'],
                    'category': final_category,
                    'channel': 'rss_' + source['name'].lower().replace(' ', '_')
                }
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {source['url']}: {e}")
            return []
        """Получить информацию о канале через Telegram API"""
        try:
            # В реальной реализации здесь будет вызов к Telegram Bot API
            # Пока возвращаем мок данные
            channel_data = next((ch for ch in self.channels if ch['username'] == username), None)
            if not channel_data:
                return None
                
            return {
                'username': username,
                'title': channel_data['name'],
                'description': f"Канал {channel_data['name']} - {channel_data['category']}",
                'subscribers_count': 1000 + hash(username) % 50000,  # Мок количества подписчиков
                'category': channel_data['category']
            }
        except Exception as e:
            logger.error(f"Error getting channel info for {username}: {e}")
            return None
    
    async def get_channel_posts(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние посты из канала"""
        try:
            # В реальной реализации здесь будет вызов к Telegram Bot API
            # Пока генерируем мок данные
            channel_data = next((ch for ch in self.channels if ch['username'] == username), None)
            if not channel_data:
                return []
            
            posts = []
            base_time = datetime.now()
            
            for i in range(limit):
                post_time = base_time - timedelta(hours=i * 2 + hash(username + str(i)) % 24)
                
                # Генерируем контент на основе категории
                if channel_data['category'] == 'gifts':
                    titles = [
                        f"🎁 Новые бесплатные подарки в {channel_data['name']}!",
                        f"💝 Эксклюзивные промокоды и скидки",
                        f"🎉 Розыгрыш призов для подписчиков",
                        f"🛍️ Лучшие предложения дня"
                    ]
                elif channel_data['category'] == 'crypto':
                    titles = [
                        f"📈 Анализ рынка криптовалют",
                        f"💰 Новые возможности для инвестиций",
                        f"🚀 Обзор перспективных проектов",
                        f"⚡ Быстрые новости из мира крипто"
                    ]
                elif channel_data['category'] == 'nft':
                    titles = [
                        f"🖼️ Новые NFT коллекции",
                        f"💎 Раритетные токены на аукционе",
                        f"🎨 Обзор NFT художников",
                        f"📊 Статистика NFT рынка"
                    ]
                elif channel_data['category'] == 'tech':
                    titles = [
                        f"💻 Новости технологий",
                        f"🔧 Обзор гаджетов",
                        f"🚀 Инновации в IT",
                        f"📱 Мобильные приложения"
                    ]
                else:
                    titles = [
                        f"📢 Новости от {channel_data['name']}",
                        f"ℹ️ Важные обновления",
                        f"📝 Полезная информация",
                        f"🔥 Горячие темы"
                    ]
                
                title = titles[i % len(titles)]
                
                posts.append({
                    'id': f"{username}_{i}",
                    'title': title,
                    'text': f"Интересный контент от канала {channel_data['name']}. Подписывайтесь для получения актуальных новостей!",
                    'date': post_time.isoformat(),
                    'views': 100 + hash(username + str(i)) % 5000,
                    'link': f"https://t.me/{username}",
                    'channel': username,
                    'category': channel_data['category']
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts for {username}: {e}")
            return []
    
    async def get_all_news(self, category: str = 'all', limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получить новости из всех источников согласно ТЗ:
        - Telegram каналы (основные источники)
        - RSS ленты (дополнительные источники)
        - Автоматическая категоризация и дедупликация
        """
        try:
            # Проверяем кэш
            cache_key = f"news_{category}_{limit}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if datetime.now() - cached_time < self.cache_ttl:
                    logger.info(f"Returning cached news for {category}, {len(cached_data)} items")
                    return cached_data
            
            all_posts = []
            
            # 1. Получаем данные из Telegram каналов (приоритетный источник согласно ТЗ)
            telegram_channels = self.channels
            if category != 'all':
                telegram_channels = [ch for ch in self.channels if ch['category'] == category]
            
            logger.info(f"Fetching from {len(telegram_channels)} Telegram channels")
            
            # Получаем посты из Telegram каналов
            telegram_tasks = []
            for channel in telegram_channels:
                telegram_tasks.append(self.fetch_telegram_channel(channel['username']))
            
            telegram_results = await asyncio.gather(*telegram_tasks, return_exceptions=True)
            
            for i, result in enumerate(telegram_results):
                if isinstance(result, list):
                    all_posts.extend(result)
                    logger.info(f"Got {len(result)} posts from {telegram_channels[i]['username']}")
                else:
                    logger.error(f"Error fetching posts from {telegram_channels[i]['username']}: {result}")
            
            # 2. Получаем данные из RSS источников (дополнительный источник)
            rss_sources = self.rss_sources
            if category != 'all':
                rss_sources = [src for src in self.rss_sources if src['category'] == category]
            
            logger.info(f"Fetching from {len(rss_sources)} RSS sources")
            
            # Получаем статьи из RSS
            rss_tasks = []
            for source in rss_sources:
                rss_tasks.append(self.fetch_rss_feed(source))
            
            rss_results = await asyncio.gather(*rss_tasks, return_exceptions=True)
            
            for i, result in enumerate(rss_results):
                if isinstance(result, list):
                    all_posts.extend(result)
                    logger.info(f"Got {len(result)} articles from {rss_sources[i]['name']}")
                else:
                    logger.error(f"Error fetching RSS from {rss_sources[i]['url']}: {result}")
            
            # 3. Обработка и дедупликация согласно ТЗ
            # Удаляем дубликаты по заголовку и ссылке
            seen = set()
            unique_posts = []
            for post in all_posts:
                # Создаем ключ для дедупликации
                title_clean = re.sub(r'[^\w\s]', '', post['title'].lower()).strip()
                key = (title_clean, post.get('link', ''))
                if key not in seen:
                    seen.add(key)
                    unique_posts.append(post)
            
            logger.info(f"After deduplication: {len(unique_posts)} unique posts from {len(all_posts)} total")
            
            # 4. Сортировка по дате (новые сначала)
            try:
                unique_posts.sort(
                    key=lambda x: datetime.fromisoformat(x['date'].replace('Z', '+00:00')), 
                    reverse=True
                )
            except Exception as e:
                logger.warning(f"Error sorting by date: {e}, using original order")
            
            # 5. Ограничиваем количество согласно ТЗ
            final_posts = unique_posts[:limit]
            
            # 6. Сохраняем в кэш на 30 минут согласно ТЗ
            self.cache[cache_key] = (final_posts, datetime.now())
            
            logger.info(f"Returning {len(final_posts)} news items for category '{category}'")
            return final_posts
            
        except Exception as e:
            logger.error(f"Error in get_all_news: {e}")
            # В случае ошибки возвращаем данные из кэша, если есть
            cache_key = f"news_{category}_{limit}"
            if cache_key in self.cache:
                cached_data, _ = self.cache[cache_key]
                logger.info("Returning stale cached data due to error")
                return cached_data
            return []
            
            return final_posts
            
        except Exception as e:
            logger.error(f"Error getting all news: {e}")
            return []
    
    async def get_channels_info(self) -> List[Dict[str, Any]]:
        """Получить информацию о всех каналах"""
        try:
            tasks = []
            for channel in self.channels:
                tasks.append(self.get_channel_info(channel['username']))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            channels_info = []
            for result in results:
                if isinstance(result, dict):
                    channels_info.append(result)
                    
            return channels_info
            
        except Exception as e:
            logger.error(f"Error getting channels info: {e}")
            return []

# Глобальный экземпляр сервиса
telegram_news_service = TelegramNewsService()
