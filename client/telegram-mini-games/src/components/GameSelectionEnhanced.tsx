import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaTrophy, FaSearch, FaFilter, FaSortAmountDown, FaSortAmountUp } from 'react-icons/fa';
import { GameCard } from './GameCard';

interface Game {
  id: string;
  name: string;
  description: string;
  icon: string;
  difficulty: 'Легко' | 'Средне' | 'Сложно';
  color: string;
  players?: string;
  category?: string;
}

interface GameSelectionProps {
  games: Game[];
  onGameSelect: (gameId: string) => void;
  userScore: number;
}

const GameSelectionEnhanced: React.FC<GameSelectionProps> = ({ games, onGameSelect, userScore }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'difficulty'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Фильтрация и сортировка игр
  const filteredAndSortedGames = useMemo(() => {
    let filtered = games.filter(game => 
      game.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      game.description.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter(game => game.difficulty === selectedDifficulty);
    }

    // Сортировка
    filtered.sort((a, b) => {
      if (sortBy === 'name') {
        const comparison = a.name.localeCompare(b.name, 'ru');
        return sortOrder === 'asc' ? comparison : -comparison;
      } else {
        const difficultyOrder = { 'Легко': 1, 'Средне': 2, 'Сложно': 3 };
        const comparison = difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        return sortOrder === 'asc' ? comparison : -comparison;
      }
    });

    return filtered;
  }, [games, searchTerm, selectedDifficulty, sortBy, sortOrder]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="max-w-6xl mx-auto px-4 py-8"
    >
      {/* Заголовок с анимацией */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="text-center mb-12"
      >
        <motion.h2
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-4xl font-bold text-white mb-4 drop-shadow-lg"
        >
          🎮 Выберите игру
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-white/80 text-lg max-w-2xl mx-auto"
        >
          Коллекция классических мини-игр с современным дизайном. Играйте, получайте удовольствие и устанавливайте рекорды!
        </motion.p>
      </motion.div>

      {/* Статистика пользователя */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-effect rounded-3xl p-6 mb-8 border border-white/20"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.div
              whileHover={{ scale: 1.1, rotate: 5 }}
              className="bg-gradient-to-r from-yellow-400 to-orange-500 p-4 rounded-2xl"
            >
              <FaTrophy className="text-white text-2xl" />
            </motion.div>
            <div>
              <h3 className="text-white text-xl font-bold">Ваш счет</h3>
              <motion.p
                key={userScore}
                initial={{ scale: 1.2, color: '#fbbf24' }}
                animate={{ scale: 1, color: '#d1d5db' }}
                className="text-white/80"
              >
                {userScore.toLocaleString()} очков
              </motion.p>
            </div>
          </div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="text-right"
          >
            <p className="text-white/60 text-sm">Игр доступно</p>
            <p className="text-white text-2xl font-bold">{games.length}</p>
          </motion.div>
        </div>
      </motion.div>

      {/* Панель фильтров и поиска */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-effect rounded-3xl p-6 mb-8 border border-white/20"
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Поиск */}
          <div className="relative">
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50" />
            <input
              type="text"
              placeholder="Поиск игр..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-white/10 text-white placeholder-white/50 rounded-xl border border-white/20 focus:border-blue-400 focus:outline-none transition-colors"
            />
          </div>

          {/* Фильтр по сложности */}
          <div className="relative">
            <FaFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50" />
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-white/10 text-white rounded-xl border border-white/20 focus:border-blue-400 focus:outline-none transition-colors appearance-none"
            >
              <option value="all" className="bg-gray-800">Все уровни</option>
              <option value="Легко" className="bg-gray-800">😊 Легко</option>
              <option value="Средне" className="bg-gray-800">😐 Средне</option>
              <option value="Сложно" className="bg-gray-800">😓 Сложно</option>
            </select>
          </div>

          {/* Сортировка */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'difficulty')}
              className="w-full pl-4 pr-4 py-3 bg-white/10 text-white rounded-xl border border-white/20 focus:border-blue-400 focus:outline-none transition-colors appearance-none"
            >
              <option value="name" className="bg-gray-800">По названию</option>
              <option value="difficulty" className="bg-gray-800">По сложности</option>
            </select>
          </div>

          {/* Порядок сортировки */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="flex items-center justify-center gap-2 py-3 px-4 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30 hover:bg-blue-500/30 transition-colors"
          >
            {sortOrder === 'asc' ? <FaSortAmountUp /> : <FaSortAmountDown />}
            {sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'}
          </motion.button>
        </div>

        {/* Результаты поиска */}
        {searchTerm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 pt-4 border-t border-white/20"
          >
            <p className="text-white/80">
              Найдено игр: <span className="font-bold text-blue-400">{filteredAndSortedGames.length}</span>
              {searchTerm && ` по запросу "${searchTerm}"`}
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Сетка игр */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${searchTerm}-${selectedDifficulty}-${sortBy}-${sortOrder}`}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          {filteredAndSortedGames.length > 0 ? (
            filteredAndSortedGames.map((game, index) => (
              <motion.div key={game.id} variants={itemVariants}>
                <GameCard
                  game={game}
                  onClick={() => onGameSelect(game.id)}
                  index={index}
                />
              </motion.div>
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="col-span-full flex flex-col items-center justify-center py-16"
            >
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-2xl font-bold text-white mb-2">Игры не найдены</h3>
              <p className="text-white/60 text-center max-w-md">
                Попробуйте изменить параметры поиска или фильтры
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setSearchTerm('');
                  setSelectedDifficulty('all');
                }}
                className="mt-4 px-6 py-3 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30 hover:bg-blue-500/30 transition-colors"
              >
                Сбросить фильтры
              </motion.button>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Статистика внизу */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-12 text-center"
      >
        <div className="inline-flex items-center gap-4 glass-effect rounded-2xl px-6 py-4 border border-white/20">
          <div className="flex items-center gap-2">
            <span className="text-green-400">😊</span>
            <span className="text-white/80">{games.filter(g => g.difficulty === 'Легко').length} легких</span>
          </div>
          <div className="w-px h-6 bg-white/20"></div>
          <div className="flex items-center gap-2">
            <span className="text-yellow-400">😐</span>
            <span className="text-white/80">{games.filter(g => g.difficulty === 'Средне').length} средних</span>
          </div>
          <div className="w-px h-6 bg-white/20"></div>
          <div className="flex items-center gap-2">
            <span className="text-red-400">😓</span>
            <span className="text-white/80">{games.filter(g => g.difficulty === 'Сложно').length} сложных</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default GameSelectionEnhanced;
