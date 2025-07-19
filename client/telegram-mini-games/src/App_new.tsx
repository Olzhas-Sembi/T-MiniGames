import { useState, useEffect } from 'react';
import { FaGamepad, FaDice, FaCubes, FaHandRock, FaNewspaper, FaPlay, FaUsers } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './index.css';

// Импорт компонентов
import DiceGame from './games/dice/DiceGame';
import CardsGame from './games/cards/CardsGame';
import RockPaperScissors from './games/rps/RockPaperScissors';
import { NewsAggregator } from './components/NewsAggregator';
import { LiveGameSelection } from './components/LiveGameSelection';
import { GameLobbyEnhanced } from './components/GameLobbyEnhanced';
import TelegramService from './services/telegramService';
import type { Room } from './services/gameAPI';

type PageType = 'menu' | 'dice' | 'cards' | 'rps' | 'news' | 'live-games' | 'lobby' | 'playing';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('menu');
  const [playerName, setPlayerName] = useState('Игрок');
  const [currentRoom, setCurrentRoom] = useState<Room | null>(null);
  const [playerId, setPlayerId] = useState('');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  // Инициализация Telegram WebApp
  useEffect(() => {
    TelegramService.init();
    
    // Получаем данные пользователя из Telegram
    const username = TelegramService.getUsername();
    setPlayerName(username);
    
    // Генерируем playerId
    const generatedPlayerId = 'player_' + Math.random().toString(36).substr(2, 9);
    setPlayerId(generatedPlayerId);
    
    // Инициализируем WebSocket
    const wsUrl = `ws://localhost:8000/ws/${generatedPlayerId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWebsocket(ws);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWebsocket(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Очистка при размонтировании
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, []);

  // Функция возврата в главное меню
  const returnToMenu = () => {
    setCurrentPage('menu');
    setCurrentRoom(null);
  };

  // Обработчик входа в лобби
  const handleJoinLobby = (room: Room) => {
    setCurrentRoom(room);
    setCurrentPage('lobby');
  };

  // Обработчик начала игры
  const handleStartGame = () => {
    setCurrentPage('playing');
  };

  // Рендер страниц
  const renderPage = () => {
    switch (currentPage) {
      case 'live-games':
        return (
          <LiveGameSelection 
            onBack={returnToMenu} 
            onRoomCreated={handleJoinLobby}
            onRoomJoined={handleJoinLobby}
          />
        );
      case 'lobby':
        return currentRoom ? (
          <GameLobbyEnhanced
            room={currentRoom}
            onBack={returnToMenu}
            onGameStart={handleStartGame}
            playerName={playerName}
            playerId={playerId}
          />
        ) : null;
      case 'playing':
        return (
          <DiceGame
            onBack={returnToMenu}
            playerName={playerName}
            playerId={playerId}
            roomData={currentRoom}
            websocket={websocket}
          />
        );
      case 'dice':
        return (
          <DiceGame 
            onBack={returnToMenu} 
            playerName={playerName}
            playerId={playerId}
            roomData={currentRoom}
            websocket={websocket}
          />
        );
      case 'cards':
        return <CardsGame onBack={returnToMenu} playerName={playerName} />;
      case 'rps':
        return <RockPaperScissors onBack={returnToMenu} playerName={playerName} />;
      case 'news':
        return <NewsAggregator onBack={returnToMenu} />;
      default:
        return renderMenu();
    }
  };

  // Рендер главного меню с современным дизайном
  const renderMenu = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Анимированный фон */}
      <div className="absolute inset-0">
        {/* Плавающие элементы */}
        <motion.div
          animate={{
            y: [0, -20, 0],
            rotate: [0, 5, 0],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute top-20 left-10 w-32 h-32 bg-gradient-to-r from-blue-400/30 to-cyan-400/30 rounded-full blur-xl"
        />
        <motion.div
          animate={{
            y: [0, 25, 0],
            rotate: [0, -8, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
          className="absolute top-1/3 right-20 w-48 h-48 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-2xl"
        />
        <motion.div
          animate={{
            y: [0, -15, 0],
            x: [0, 10, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
          className="absolute bottom-1/4 left-1/4 w-40 h-40 bg-gradient-to-r from-emerald-400/25 to-teal-400/25 rounded-full blur-xl"
        />
        
        {/* Звезды */}
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 0] }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              delay: Math.random() * 5
            }}
            className="absolute w-1 h-1 bg-white rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="pt-8 pb-4"
        >
          <div className="container mx-auto px-4 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.8, type: "spring", stiffness: 100 }}
              className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-2xl mb-6 shadow-2xl"
            >
              <FaGamepad className="text-3xl text-white" />
            </motion.div>
            
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-white via-purple-200 to-cyan-200 bg-clip-text text-transparent mb-4"
            >
              Mini Games
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto"
            >
              Коллекция увлекательных мини-игр для Telegram
            </motion.p>
          </div>
        </motion.header>

        {/* Player Name Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="container mx-auto px-4 mb-8"
        >
          <div className="max-w-md mx-auto">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <label className="block text-white/90 font-medium mb-3 text-sm">
                Ваше имя:
              </label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/20 backdrop-blur-sm text-white placeholder-white/60 border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300"
                placeholder="Введите ваше имя"
                maxLength={20}
              />
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 container mx-auto px-4 pb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
            
            {/* Live Games Section */}
            <motion.section
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.8 }}
              className="space-y-6"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <h2 className="text-2xl font-bold text-white">LIVE Игры</h2>
              </div>
              
              <p className="text-gray-300 mb-6">
                Играйте онлайн с реальными игроками в режиме реального времени
              </p>

              <motion.button
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setCurrentPage('live-games')}
                className="w-full bg-gradient-to-r from-red-500 to-pink-500 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-2xl hover:shadow-red-500/25 transition-all duration-300 border border-red-400/30"
              >
                <div className="flex items-center justify-center gap-3">
                  <FaPlay className="text-xl" />
                  <span>Живые матчи</span>
                  <div className="bg-white/20 px-2 py-1 rounded-full text-sm">
                    🔴 LIVE
                  </div>
                </div>
              </motion.button>
            </motion.section>

            {/* News Section */}
            <motion.section
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 1.0 }}
              className="space-y-6"
            >
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <FaNewspaper className="text-blue-400" />
                Новости
              </h2>
              
              <p className="text-gray-300 mb-6">
                Последние новости из проверенных источников
              </p>

              <motion.button
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setCurrentPage('news')}
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-2xl hover:shadow-blue-500/25 transition-all duration-300 border border-blue-400/30"
              >
                <div className="flex items-center justify-center gap-3">
                  <FaNewspaper className="text-xl" />
                  <span>Актуальные новости</span>
                </div>
              </motion.button>
            </motion.section>
          </div>

          {/* Games Grid */}
          <motion.section
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1.2 }}
            className="mt-16"
          >
            <h2 className="text-3xl font-bold text-white text-center mb-8">
              Игры
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {/* Dice Game */}
              <motion.button
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentPage('dice')}
                className="group bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-md rounded-3xl p-8 border border-purple-300/30 hover:border-purple-300/60 transition-all duration-300 shadow-2xl hover:shadow-purple-500/20"
              >
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <FaDice className="text-2xl text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Кубики</h3>
                  <p className="text-gray-300 text-sm mb-4">
                    Бросьте два кубика и наберите максимальную сумму
                  </p>
                  <div className="flex items-center justify-center gap-2 text-sm text-purple-300">
                    <FaUsers className="text-xs" />
                    <span>2-4 игрока</span>
                  </div>
                </div>
              </motion.button>

              {/* Cards Game */}
              <motion.button
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentPage('cards')}
                className="group bg-gradient-to-br from-emerald-500/20 to-teal-500/20 backdrop-blur-md rounded-3xl p-8 border border-emerald-300/30 hover:border-emerald-300/60 transition-all duration-300 shadow-2xl hover:shadow-emerald-500/20"
              >
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <FaCubes className="text-2xl text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Карты 21</h3>
                  <p className="text-gray-300 text-sm mb-4">
                    Наберите 21 очко, не превышая лимит
                  </p>
                  <div className="flex items-center justify-center gap-2 text-sm text-emerald-300">
                    <FaUsers className="text-xs" />
                    <span>2-4 игрока</span>
                  </div>
                </div>
              </motion.button>

              {/* Rock Paper Scissors */}
              <motion.button
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentPage('rps')}
                className="group bg-gradient-to-br from-orange-500/20 to-red-500/20 backdrop-blur-md rounded-3xl p-8 border border-orange-300/30 hover:border-orange-300/60 transition-all duration-300 shadow-2xl hover:shadow-orange-500/20"
              >
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <FaHandRock className="text-2xl text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Камень-Ножницы-Бумага</h3>
                  <p className="text-gray-300 text-sm mb-4">
                    Классическая игра для 2 игроков
                  </p>
                  <div className="flex items-center justify-center gap-2 text-sm text-orange-300">
                    <FaUsers className="text-xs" />
                    <span>2 игрока</span>
                  </div>
                </div>
              </motion.button>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      {renderPage()}
    </div>
  );
}

export default App;
