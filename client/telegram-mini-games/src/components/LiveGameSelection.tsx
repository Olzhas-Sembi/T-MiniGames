// Современный редизайн выбора игр: светлый фон, плавные градиенты, стеклянные карточки, крупные иконки, анимации, чистая типографика.
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FaDice, FaCubes, FaHandRock, FaPlus, FaUsers, FaCoins, FaArrowLeft } from 'react-icons/fa';
import type { Room } from '../services/gameAPI';
import { gameAPI } from '../services/gameAPI';
import { gameWebSocket } from '../services/gameWebSocket';

interface LiveGameSelectionProps {
  onBack: () => void;
  onRoomCreated: (room: Room) => void;
  onRoomJoined: (room: Room) => void;
}

export const LiveGameSelection: React.FC<LiveGameSelectionProps> = ({
  onBack,
  onRoomCreated,
  onRoomJoined
}) => {
  const [selectedGame, setSelectedGame] = useState<'dice' | 'cards' | 'rps' | null>(null);
  const [betAmount, setBetAmount] = useState(100);
  const [availableRooms, setAvailableRooms] = useState<Room[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const playerName = 'Игрок_' + Math.random().toString(36).substr(2, 6);
  const playerId = gameWebSocket.getPlayerId();

  useEffect(() => {
    if (selectedGame) {
      loadAvailableRooms();
    }
  }, [selectedGame]);

  const loadAvailableRooms = async () => {
    if (!selectedGame) return;
    
    setIsLoading(true);
    try {
      const rooms = await gameAPI.getAvailableRooms(selectedGame, betAmount);
      setAvailableRooms(rooms);
    } catch (error) {
      console.error('Error loading available rooms:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRoom = async () => {
    if (!selectedGame) return;
    
    setIsCreating(true);
    try {
      const result = await gameAPI.createRoom({
        player_id: playerId,
        telegram_id: 'telegram_' + playerId,
        username: playerName,
        game_type: selectedGame,
        bet_amount: betAmount
      });
      
      onRoomCreated(result.room);
    } catch (error) {
      console.error('Error creating room:', error);
      alert('Ошибка при создании комнаты');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinRoom = async (room: Room) => {
    try {
      const result = await gameAPI.joinRoom({
        player_id: playerId,
        telegram_id: 'telegram_' + playerId,
        username: playerName,
        room_id: room.id
      });
      
      onRoomJoined(result.room);
    } catch (error) {
      console.error('Error joining room:', error);
      alert('Ошибка при присоединении к комнате');
    }
  };

  const getGameInfo = (gameType: string) => {
    switch (gameType) {
      case 'dice':
        return {
          name: 'Кубики',
          icon: FaDice,
          description: 'Бросьте два кубика и наберите максимальную сумму',
          players: '2-4 игрока',
          color: 'from-red-400 to-red-600'
        };
      case 'cards':
        return {
          name: 'Карты 21',
          icon: FaCubes,
          description: 'Наберите 21 очко, не превышая лимит',
          players: '2-4 игрока',
          color: 'from-green-400 to-green-600'
        };
      case 'rps':
        return {
          name: 'Камень-Ножницы-Бумага',
          icon: FaHandRock,
          description: 'Классическая игра на удачу',
          players: '2-4 игрока',
          color: 'from-blue-400 to-blue-600'
        };
      default:
        return {
          name: 'Неизвестная игра',
          icon: FaDice,
          description: '',
          players: '',
          color: 'from-gray-400 to-gray-600'
        };
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const created = new Date(dateString);
    const diffMs = now.getTime() - created.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) return `${diffSec}с назад`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}м назад`;
    return `${Math.floor(diffSec / 3600)}ч назад`;
  };

  if (!selectedGame) {
    // Выбор типа игры
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="min-h-screen bg-gradient-to-br from-[#f8fafc] via-[#e0e7ef] to-[#c7d2fe] p-4"
      >
        {/* Заголовок */}
        <motion.div 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="bg-white/80 backdrop-blur-lg rounded-3xl p-6 mb-8 border border-white/30 shadow-2xl"
        >
          <div className="flex items-center gap-4">
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onBack}
              className="bg-white/60 backdrop-blur-sm p-3 rounded-xl hover:bg-white/80 transition-all duration-300 border border-white/30 shadow-lg"
            >
              <FaArrowLeft className="text-indigo-700 text-xl" />
            </motion.button>
            <div>
              <h1 className="text-3xl font-bold text-indigo-900">Живые игры</h1>
              <p className="text-indigo-400">Выберите игру для онлайн-матча</p>
            </div>
          </div>
        </motion.div>

        {/* Сетка игр */}
        <motion.div 
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {(['dice', 'cards', 'rps'] as const).map((gameType, index) => {
            const gameInfo = getGameInfo(gameType);
            const IconComponent = gameInfo.icon;
            
            return (
              <motion.div 
                key={gameType}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedGame(gameType)}
                className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 text-center cursor-pointer border border-white/30 shadow-2xl hover:shadow-3xl transition-all duration-300 group"
              >
                <motion.div 
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  className={`bg-gradient-to-br ${gameInfo.color} w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl transition-transform duration-300`}
                >
                  <IconComponent className="text-white text-3xl" />
                </motion.div>
                <h3 className="text-2xl font-bold text-indigo-900 mb-4">{gameInfo.name}</h3>
                <p className="text-indigo-600 text-lg mb-6">
                  {gameInfo.description}
                </p>
                <div className="bg-white/60 backdrop-blur-sm px-6 py-3 rounded-xl border border-white/30 shadow-lg">
                  <span className="text-indigo-700 font-semibold">{gameInfo.players}</span>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </motion.div>
    );
  }

  // Экран создания/поиска комнаты
  const gameInfo = getGameInfo(selectedGame);
  const IconComponent = gameInfo.icon;

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gradient-to-br from-[#f8fafc] via-[#e0e7ef] to-[#c7d2fe] p-4"
    >
      {/* Заголовок */}
      <motion.div 
        initial={{y: -30, opacity: 0}} 
        animate={{y: 0, opacity: 1}} 
        transition={{duration: 0.5}}
        className="bg-white/80 backdrop-blur-lg rounded-3xl p-6 mb-8 border border-white/30 shadow-2xl"
      >
        <div className="flex items-center gap-4">
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedGame(null)}
            className="bg-white/60 backdrop-blur-sm p-3 rounded-xl hover:bg-white/80 transition-all duration-300 border border-white/30 shadow-lg"
          >
            <FaArrowLeft className="text-indigo-700 text-xl" />
          </motion.button>
          <div className="flex items-center gap-3">
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={`bg-gradient-to-br ${gameInfo.color} w-12 h-12 rounded-xl flex items-center justify-center shadow-xl`}
            >
              <IconComponent className="text-white text-xl" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold text-indigo-900 tracking-tight">{gameInfo.name}</h1>
              <p className="text-indigo-400">Поиск игроков или создание комнаты</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Настройки ставки */}
      <motion.div 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="bg-white/80 backdrop-blur-lg rounded-3xl p-6 mb-8 border border-white/30 shadow-2xl"
      >
        <h3 className="text-xl font-bold text-indigo-900 mb-4">Настройки игры</h3>
        <div className="flex items-center gap-4">
          <label className="text-indigo-600">Ставка:</label>
          <select 
            value={betAmount} 
            onChange={(e) => setBetAmount(Number(e.target.value))}
            className="bg-white/60 backdrop-blur-sm border border-white/30 rounded-xl px-4 py-2 text-indigo-900 shadow-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value={50}>50 ⭐</option>
            <option value={100}>100 ⭐</option>
            <option value={200}>200 ⭐</option>
            <option value={500}>500 ⭐</option>
          </select>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={loadAvailableRooms}
            className="bg-blue-100/80 backdrop-blur-sm border border-blue-200/50 text-blue-700 px-4 py-2 rounded-xl hover:bg-blue-200/80 transition-all duration-300 shadow-lg"
          >
            Обновить
          </motion.button>
        </div>
      </motion.div>

      {/* Создание новой комнаты */}
      <motion.div 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="bg-white/80 backdrop-blur-lg rounded-3xl p-6 mb-8 border border-white/30 shadow-2xl"
      >
        <div className="text-center">
          <h3 className="text-xl font-bold text-indigo-900 mb-4">Создать новую комнату</h3>
          <p className="text-indigo-600 mb-6">
            Создайте комнату и пригласите друзей или ждите случайных игроков
          </p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCreateRoom}
            disabled={isCreating}
            className="bg-gradient-to-r from-green-500 to-green-600 text-white px-8 py-4 rounded-2xl hover:from-green-600 hover:to-green-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-bold text-lg shadow-xl"
          >
            {isCreating ? (
              <div className="flex items-center gap-3">
                <div className="animate-spin w-6 h-6 border-2 border-white/30 border-t-white rounded-full"></div>
                Создание...
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <FaPlus />
                Создать комнату ({betAmount} ⭐)
              </div>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* Доступные комнаты */}
      <motion.div 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="bg-white/80 backdrop-blur-lg rounded-3xl p-6 border border-white/30 shadow-2xl"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-indigo-900">Доступные комнаты</h3>
          {isLoading && (
            <div className="animate-spin w-6 h-6 border-2 border-indigo-300 border-t-indigo-600 rounded-full"></div>
          )}
        </div>

        {availableRooms.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <p className="text-indigo-400 text-lg">
              Нет доступных комнат для ставки {betAmount} ⭐
            </p>
            <p className="text-indigo-300 text-sm mt-2">
              Создайте новую комнату или измените ставку
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {availableRooms.map((room, index) => (
              <motion.div 
                key={room.id} 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="bg-white/60 backdrop-blur-sm rounded-2xl p-4 border border-white/30 hover:border-white/50 hover:bg-white/80 transition-all duration-300 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <FaUsers className="text-indigo-400" />
                      <span className="text-indigo-900 font-semibold">
                        {room.players.length}/{room.max_players}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FaCoins className="text-yellow-500" />
                      <span className="text-indigo-900">{room.bet_amount} ⭐</span>
                    </div>
                    <div className="text-indigo-400 text-sm">
                      {formatTimeAgo(room.created_at)}
                    </div>
                  </div>
                  
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleJoinRoom(room)}
                    className="bg-blue-100/80 backdrop-blur-sm border border-blue-200/50 text-blue-700 px-6 py-2 rounded-xl hover:bg-blue-200/80 transition-all duration-300 shadow-lg"
                  >
                    Присоединиться
                  </motion.button>
                </div>
                
                <div className="mt-3 flex gap-2">
                  {room.players.map((player) => (
                    <div key={player.id} className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        player.status === 'ready' ? 'bg-green-500' : 'bg-yellow-500'
                      }`}></div>
                      <span className="text-indigo-600 text-sm">{player.username}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};
