// Современный агрегатор новостей согласно ТЗ
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaArrowLeft, FaSync, FaExternalLinkAlt, FaTelegram, FaRss, FaClock, FaEye } from 'react-icons/fa';

interface NewsItem {
  id: string;
  title: string;
  description: string;
  link: string;
  pubDate: string;
  source: string;
  category: string;
  channel: string;
}

interface NewsAggregatorProps {
  onBack: () => void;
}

export const NewsAggregator: React.FC<NewsAggregatorProps> = ({ onBack }) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [newsStats, setNewsStats] = useState<{telegram_channels: number, rss_feeds: number}>({
    telegram_channels: 0,
    rss_feeds: 0
  });

  // Категории согласно ТЗ: основные темы - подарки, NFT, крипто
  const categories = [
    { id: 'all', name: '📢 Все', description: 'Все новости' },
    { id: 'gifts', name: '🎁 Подарки', description: 'Бесплатные подарки и розыгрыши' },
    { id: 'crypto', name: '💰 Криптовалюта', description: 'Новости крипторынка' },
    { id: 'nft', name: '🖼️ NFT', description: 'NFT коллекции и маркетплейсы' },
    { id: 'tech', name: '💻 Технологии', description: 'IT новости и инновации' },
    { id: 'general', name: '📰 Общие', description: 'Остальные новости' }
  ];

  const fetchNews = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_BASE_URL = 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/news?category=${selectedCategory}&limit=50`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        const transformedNews: NewsItem[] = data.data.map((item: any) => ({
          id: item.id,
          title: item.title,
          description: item.text,
          link: item.link,
          pubDate: item.date,
          source: item.source,
          category: item.category,
          channel: item.channel
        }));
        
        setNews(transformedNews);
        setNewsStats(data.sources || { telegram_channels: 0, rss_feeds: 0 });
        setLastUpdate(new Date());
      } else {
        throw new Error('Failed to fetch news');
      }
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Ошибка загрузки новостей. Проверьте подключение к серверу.');
      
      // Fallback к моковым данным
      const mockNews: NewsItem[] = [
        {
          id: 'mock_1',
          title: '🎁 Новые подарки в Telegram Stars',
          description: 'Актуальные бесплатные подарки и промокоды для пользователей Telegram',
          link: 'https://t.me/gift_newstg',
          pubDate: new Date().toISOString(),
          source: 'Gift News TG',
          category: 'gifts',
          channel: 'gift_newstg'
        },
        {
          id: 'mock_2',
          title: '💰 Обзор рынка криптовалют',
          description: 'Анализ последних тенденций на крипторынке и перспективы роста',
          link: 'https://forklog.com',
          pubDate: new Date(Date.now() - 3600000).toISOString(),
          source: 'ForkLog',
          category: 'crypto',
          channel: 'rss_forklog'
        }
      ];
      setNews(mockNews);
    } finally {
      setLoading(false);
    }
  };

  const refreshNews = async () => {
    try {
      const API_BASE_URL = 'http://localhost:8000';
      await fetch(`${API_BASE_URL}/api/news/refresh`, { method: 'POST' });
      await fetchNews();
    } catch (err) {
      console.error('Error refreshing news:', err);
      await fetchNews();
    }
  };

  useEffect(() => {
    fetchNews();
  }, [selectedCategory]);

  const filteredNews = selectedCategory === 'all' 
    ? news 
    : news.filter(item => item.category === selectedCategory);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Только что';
    if (diffInHours < 24) return `${diffInHours} ч. назад`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} д. назад`;
    
    return date.toLocaleDateString('ru-RU');
  };

  const getSourceIcon = (channel: string) => {
    if (channel.startsWith('rss_')) return <FaRss className="text-orange-500" />;
    return <FaTelegram className="text-blue-500" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Заголовок */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200"
              >
                <FaArrowLeft />
                <span className="font-medium">Назад</span>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">📰 Агрегатор новостей</h1>
                <p className="text-sm text-gray-500">
                  Последние новости из {newsStats.telegram_channels} Telegram каналов и {newsStats.rss_feeds} RSS источников
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="text-xs text-gray-500 flex items-center gap-1">
                <FaClock />
                Обновлено: {lastUpdate.toLocaleTimeString('ru-RU')}
              </div>
              <button
                onClick={refreshNews}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-200 disabled:opacity-50"
              >
                <FaSync className={loading ? 'animate-spin' : ''} />
                Обновить
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Фильтры категорий */}
        <div className="flex flex-wrap gap-3 mb-8">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-6 py-3 rounded-2xl font-medium transition-all duration-200 ${
                selectedCategory === category.id
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg scale-105'
                  : 'bg-white/80 text-gray-700 hover:bg-white hover:shadow-md hover:scale-105 border border-gray-200'
              }`}
            >
              {category.name}
            </button>
          ))}
        </div>

        {/* Статистика */}
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-800">📊 Статистика новостей</h3>
              <p className="text-gray-600">
                Найдено новостей: <span className="font-semibold text-blue-600">{filteredNews.length}</span>
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <FaTelegram className="text-blue-500" />
                {newsStats.telegram_channels} каналов
              </div>
              <div className="flex items-center gap-1">
                <FaRss className="text-orange-500" />
                {newsStats.rss_feeds} RSS лент
              </div>
            </div>
          </div>
        </div>

        {/* Состояния загрузки и ошибок */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/80 rounded-2xl shadow-lg">
              <FaSync className="animate-spin text-blue-500" />
              <span className="text-gray-700 font-medium">Загружаем новости...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 mb-8">
            <div className="flex items-center gap-3">
              <div className="text-red-500 text-xl">⚠️</div>
              <div>
                <h3 className="font-semibold text-red-800">Ошибка загрузки</h3>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Сетка новостей */}
        <AnimatePresence>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredNews.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                className="group bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-300"
              >
                {/* Заголовок статьи */}
                <div className="flex items-start justify-between mb-4">
                  <h3 className="font-bold text-gray-800 group-hover:text-blue-600 transition-colors line-clamp-2 flex-1">
                    {item.title}
                  </h3>
                  <div className="ml-3 flex items-center gap-1">
                    {getSourceIcon(item.channel)}
                  </div>
                </div>

                {/* Описание */}
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                  {item.description}
                </p>

                {/* Метаинформация */}
                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{item.source}</span>
                    <span>•</span>
                    <span>{formatDate(item.pubDate)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <FaEye />
                    <span>{Math.floor(Math.random() * 1000) + 100}</span>
                  </div>
                </div>

                {/* Кнопка перехода */}
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 w-full justify-center px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-200 font-medium group-hover:scale-105"
                >
                  <span>Читать полностью</span>
                  <FaExternalLinkAlt className="text-sm" />
                </a>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>

        {/* Пустое состояние */}
        {!loading && filteredNews.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Новости не найдены</h3>
            <p className="text-gray-500 mb-6">
              Попробуйте выбрать другую категорию или обновить ленту
            </p>
            <button
              onClick={() => setSelectedCategory('all')}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-200"
            >
              Показать все новости
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
